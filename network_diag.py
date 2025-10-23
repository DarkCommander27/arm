"""
Network diagnostics module for discovering Android TV devices on the local network.
Provides ping scans, port scanning, and subnet enumeration utilities.
"""

import asyncio
import ipaddress
import logging
import socket
from typing import List, Tuple

_LOGGER = logging.getLogger(__name__)

# Android TV remote port (typically 5555 for adb, but androidtvremote2 uses SSL on port 6466)
ANDROID_TV_PORTS = [5555, 6466, 8080, 9008]


def get_local_ip() -> str:
    """Get the local machine's IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as exc:
        _LOGGER.error("Failed to get local IP: %s", exc)
        return "127.0.0.1"


def get_subnet_ips(num_hosts: int = 254) -> List[str]:
    """
    Generate a list of IPs on the same subnet as the local machine.
    
    Args:
        num_hosts: Number of hosts to scan (default 254 for /24 subnet)
    
    Returns:
        List of IP addresses on the local subnet
    """
    try:
        local_ip = get_local_ip()
        network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
        ips = [str(ip) for ip in list(network.hosts())[:num_hosts]]
        _LOGGER.debug("Generated %d IPs for subnet scan from %s", len(ips), local_ip)
        return ips
    except Exception as exc:
        _LOGGER.error("Failed to generate subnet IPs: %s", exc)
        return []


async def ping_host(host: str, timeout: float = 1.0) -> bool:
    """
    Ping a single host using asyncio (TCP connect as ping).
    
    Args:
        host: IP address or hostname
        timeout: Timeout in seconds
    
    Returns:
        True if host is reachable, False otherwise
    """
    try:
        # Try to connect to a common port (80/443 for SSH/HTTP)
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, 22),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False


async def scan_port(host: str, port: int, timeout: float = 0.5) -> bool:
    """
    Scan a single port on a host.
    
    Args:
        host: IP address or hostname
        port: Port number to scan
        timeout: Timeout in seconds
    
    Returns:
        True if port is open, False otherwise
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        _LOGGER.debug("Port %d open on %s", port, host)
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False


async def scan_ports_on_host(host: str, ports: List[int] = None, timeout: float = 0.5) -> List[int]:
    """
    Scan multiple ports on a single host.
    
    Args:
        host: IP address or hostname
        ports: List of port numbers to scan (default: ANDROID_TV_PORTS)
        timeout: Timeout per port in seconds
    
    Returns:
        List of open ports
    """
    if ports is None:
        ports = ANDROID_TV_PORTS
    
    tasks = [scan_port(host, port, timeout) for port in ports]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    open_ports = [ports[i] for i, result in enumerate(results) if result is True]
    return open_ports


async def network_scan(
    subnet_ips: List[str] = None,
    progress_callback=None,
    timeout: float = 1.0
) -> List[Tuple[str, List[int]]]:
    """
    Scan a subnet for reachable hosts and their open Android TV ports.
    
    Args:
        subnet_ips: List of IPs to scan (default: generate from local subnet)
        progress_callback: Optional callback(current, total) for progress updates
        timeout: Timeout per host in seconds
    
    Returns:
        List of tuples (ip, [open_ports]) for hosts with Android TV ports open
    """
    if subnet_ips is None:
        subnet_ips = get_subnet_ips()
    
    if not subnet_ips:
        _LOGGER.error("No IPs to scan")
        return []
    
    _LOGGER.info("Starting network scan on %d hosts with %d port(s) per host", len(subnet_ips), len(ANDROID_TV_PORTS))
    
    results = []
    total = len(subnet_ips)
    
    # Scan hosts in batches to avoid overwhelming the network
    batch_size = 10
    for batch_num in range(0, len(subnet_ips), batch_size):
        batch = subnet_ips[batch_num:batch_num + batch_size]
        tasks = []
        
        for ip in batch:
            async def scan_single_host(host: str):
                open_ports = await scan_ports_on_host(host, timeout=timeout)
                if open_ports:
                    _LOGGER.info("Found open Android TV ports on %s: %s", host, open_ports)
                    results.append((host, open_ports))
                if progress_callback:
                    progress_callback(batch_num + len(tasks) + 1, total)
                return open_ports
            
            tasks.append(scan_single_host(ip))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    _LOGGER.info("Network scan complete. Found %d hosts with Android TV ports", len(results))
    return results


async def quick_scan(timeout: float = 2.0, max_hosts: int = 50) -> List[str]:
    """
    Quick scan of the local subnet for any reachable hosts with Android TV ports.
    Scans fewer hosts and with shorter timeout for speed.
    
    Args:
        timeout: Timeout per host
        max_hosts: Maximum number of hosts to scan
    
    Returns:
        List of IP addresses with open Android TV ports
    """
    subnet_ips = get_subnet_ips(max_hosts)
    results = await network_scan(subnet_ips, timeout=timeout)
    return [ip for ip, ports in results]
