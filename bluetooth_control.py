"""
Bluetooth HID Controller for Android TV Remote Control.

This module implements a Bluetooth HID (Human Interface Device) profile
to make the application appear as a generic remote control to Android TV.
"""

import asyncio
import logging
import struct
import time
from typing import Dict, List, Optional, Callable, Any
from enum import IntEnum

try:
    import bleak
    from bleak import BleakClient, BleakScanner
    from bleak.backends.characteristic import BleakGATTCharacteristic
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    bleak = None
    BleakClient = None
    BleakScanner = None
    BleakGATTCharacteristic = None

_LOGGER = logging.getLogger(__name__)

# HID Report Descriptor for Consumer Control (Media Keys)
HID_CONSUMER_REPORT_DESC = bytes([
    0x05, 0x0C,        # Usage Page (Consumer Devices)
    0x09, 0x01,        # Usage (Consumer Control)
    0xA1, 0x01,        # Collection (Application)
    0x85, 0x01,        #   Report ID (1)
    0x19, 0x00,        #   Usage Minimum (0)
    0x2A, 0xFF, 0x02,  #   Usage Maximum (767)
    0x15, 0x00,        #   Logical Minimum (0)
    0x26, 0xFF, 0x02,  #   Logical Maximum (767)
    0x95, 0x01,        #   Report Count (1)
    0x75, 0x10,        #   Report Size (16)
    0x81, 0x00,        #   Input (Data,Array,Abs)
    0xC0,              # End Collection
])

# Standard Consumer Control Usage Codes for Android TV
class ConsumerControlCodes(IntEnum):
    """Standard HID Consumer Control codes for remote control functions."""
    POWER = 0x30
    HOME = 0x223
    BACK = 0x224
    MENU = 0x40
    VOLUME_UP = 0xE9
    VOLUME_DOWN = 0xEA
    VOLUME_MUTE = 0xE2
    CHANNEL_UP = 0x9C
    CHANNEL_DOWN = 0x9D
    PLAY_PAUSE = 0xCD
    STOP = 0xB7
    FAST_FORWARD = 0xB3
    REWIND = 0xB4
    RECORD = 0xB2
    # Navigation (using generic codes)
    UP = 0x42
    DOWN = 0x43
    LEFT = 0x44
    RIGHT = 0x45
    SELECT = 0x41
    # Pairing/Bluetooth control
    PAIR = 0x225  # Bluetooth pairing button

# HID Service and Characteristic UUIDs
HID_SERVICE_UUID = "00001812-0000-1000-8000-00805f9b34fb"
HID_INFORMATION_UUID = "00002a4a-0000-1000-8000-00805f9b34fb"
HID_REPORT_MAP_UUID = "00002a4b-0000-1000-8000-00805f9b34fb"
HID_CONTROL_POINT_UUID = "00002a4c-0000-1000-8000-00805f9b34fb"
HID_REPORT_UUID = "00002a4d-0000-1000-8000-00805f9b34fb"

class BluetoothRemoteController:
    """
    Bluetooth HID controller for Android TV remote control functionality.
    
    This class implements a Bluetooth Low Energy (BLE) HID device that
    appears as a generic remote control to Android TV systems.
    """
    
    def __init__(self):
        if not BLUETOOTH_AVAILABLE:
            raise ImportError("Bluetooth functionality requires 'bleak' library. Install with: pip install bleak")
        
        self.client: Optional[BleakClient] = None
        self.is_connected = False
        self.device_address: Optional[str] = None
        self.device_name: Optional[str] = None
        self.hid_report_char: Optional[BleakGATTCharacteristic] = None
        
        # Callback for connection status updates
        self.connection_callback: Optional[Callable[[bool, str], None]] = None
        
    def set_connection_callback(self, callback: Callable[[bool, str], None]):
        """Set callback for connection status updates."""
        self.connection_callback = callback
        
    def _notify_connection_status(self, connected: bool, message: str = ""):
        """Notify connection status change."""
        if self.connection_callback:
            self.connection_callback(connected, message)
    
    async def discover_android_tv_devices(self, timeout: float = 15.0, retry_count: int = 3) -> List[Dict[str, str]]:
        """
        Discover Bluetooth-enabled Android TV devices with improved reliability.
        
        Args:
            timeout: Discovery timeout per attempt in seconds
            max_attempts: Maximum number of discovery attempts
            
        Returns:
            List of dictionaries containing device info
        """
        if not BLUETOOTH_AVAILABLE:
            return []
        
        _LOGGER.info(f"Starting enhanced Bluetooth device discovery ({max_attempts} attempts, {timeout}s each)...")
        all_devices = {}  # Use dict to deduplicate by address
        
        for attempt in range(max_attempts):
            _LOGGER.info(f"Discovery attempt {attempt + 1}/{max_attempts}")
            
            try:
                # Use longer timeout and more aggressive scanning
                discovered = await BleakScanner.discover(
                    timeout=timeout,
                    return_adv=True  # Get advertisement data if available
                )
                
                attempt_count = 0
                for device_key, (device, adv_data) in discovered.items():
                    if isinstance(device_key, tuple):
                        device = device_key[0] if device_key else device
                    
                    # Get device info with enhanced data
                    device_info = {
                        'address': device.address,
                        'name': device.name or 'Unknown Device',
                        'rssi': getattr(device, 'rssi', getattr(adv_data, 'rssi', None)),
                        'manufacturer_data': getattr(adv_data, 'manufacturer_data', {}),
                        'service_uuids': getattr(adv_data, 'service_uuids', []),
                        'local_name': getattr(adv_data, 'local_name', device.name),
                        'tx_power': getattr(adv_data, 'tx_power', None),
                        'discovery_attempt': attempt + 1
                    }
                    
                    # Only include devices with names or strong signals
                    if device.name or (device_info['rssi'] and device_info['rssi'] > -80):
                        all_devices[device.address] = device_info
                        attempt_count += 1
                
                _LOGGER.info(f"Attempt {attempt + 1}: Found {attempt_count} devices")
                
                # If we found devices and this isn't the first attempt, add delay before next
                if attempt_count > 0 and attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                    
            except Exception as exc:
                _LOGGER.warning(f"Discovery attempt {attempt + 1} failed: {exc}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)  # Brief delay before retry
        
        # Convert to list and sort by likelihood and signal strength
        devices = list(all_devices.values())
        devices = self._sort_and_filter_devices(devices)
        
        _LOGGER.info(f"Enhanced discovery complete. Found {len(devices)} total devices")
        for device in devices[:5]:  # Log top 5
            _LOGGER.info(f"  {device['name']} ({device['address']}) RSSI: {device['rssi']}")
        
        return devices
    
    def _sort_and_filter_devices(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort and filter devices by relevance and signal strength."""
        # Separate Android TV devices from others
        tv_devices = []
        other_devices = []
        
        for device in devices:
            if self._is_likely_android_tv_enhanced(device):
                tv_devices.append(device)
            else:
                other_devices.append(device)
        
        # Sort Android TV devices by signal strength (best first)
        tv_devices.sort(key=lambda d: d.get('rssi', -100), reverse=True)
        
        # Sort other devices by signal strength, but lower priority
        other_devices.sort(key=lambda d: d.get('rssi', -100), reverse=True)
        
        # Return TV devices first, then others, but limit total results
        return tv_devices + other_devices[:20]  # Top 20 total
    
    def _is_likely_android_tv_enhanced(self, device: Dict[str, Any]) -> bool:
        """Enhanced Android TV detection using multiple indicators."""
        name = (device.get('name') or device.get('local_name', '')).lower()
        
        # Strong indicators (definitely Android TV)
        strong_indicators = [
            'android tv', 'google tv', 'chromecast', 'nvidia shield',
            'mi box', 'fire tv', 'smart tv', 'tv box', 'sony bravia',
            'philips tv', 'samsung tv', 'lg tv'
        ]
        
        # Weak indicators (might be Android TV)
        weak_indicators = [
            'tv', 'roku', 'streaming', 'media', 'cast', 'player'
        ]
        
        # Check manufacturer data for known TV manufacturers
        manufacturer_data = device.get('manufacturer_data', {})
        tv_manufacturers = [0x00E0, 0x004C, 0x0006]  # Sony, Apple, Microsoft (example IDs)
        
        # Check service UUIDs for media/HID services
        service_uuids = device.get('service_uuids', [])
        media_services = ['1812', '180F', '1800']  # HID, Battery, Generic Access
        
        # Strong match
        if any(indicator in name for indicator in strong_indicators):
            return True
        
        # Weak match with good signal
        if any(indicator in name for indicator in weak_indicators):
            rssi = device.get('rssi', -100)
            if rssi > -70:  # Strong signal suggests nearby device
                return True
        
        # Check manufacturer or services
        if any(mfg_id in manufacturer_data for mfg_id in tv_manufacturers):
            return True
        
        if any(service in str(service_uuids) for service in media_services):
            return True
        
        return False

    def _is_likely_android_tv(self, device) -> bool:
        """Check if a device is likely an Android TV (legacy method)."""
        if not device.name:
            return False
        
        return self._is_likely_android_tv_enhanced({
            'name': device.name,
            'rssi': getattr(device, 'rssi', None)
        })
    
    async def connect(self, device_address: str, max_attempts: int = 3) -> bool:
        """
        Connect to a Bluetooth device with retry logic.
        
        Args:
            device_address: Bluetooth MAC address of the device
            max_attempts: Maximum connection attempts
            
        Returns:
            True if connection successful, False otherwise
        """
        if not BLUETOOTH_AVAILABLE:
            _LOGGER.error("Bluetooth not available")
            return False
        
        _LOGGER.info(f"Attempting to connect to {device_address} (max {max_attempts} attempts)")
        
        for attempt in range(max_attempts):
            try:
                _LOGGER.info(f"Connection attempt {attempt + 1}/{max_attempts}")
                self._notify_connection_status(False, f"Connecting... (attempt {attempt + 1})")
                
                self.client = BleakClient(device_address)
                
                # Set connection timeout
                connection_timeout = 15.0 + (attempt * 5)  # Longer timeout for later attempts
                _LOGGER.debug(f"Using connection timeout: {connection_timeout}s")
                
                await asyncio.wait_for(self.client.connect(), timeout=connection_timeout)
                
                if not self.client.is_connected:
                    _LOGGER.warning(f"Connection attempt {attempt + 1} failed - not connected after connect()")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2)  # Wait before retry
                    continue
                
                _LOGGER.info("Connected successfully, discovering services...")
                
                # Discover services with timeout
                try:
                    services = await asyncio.wait_for(self.client.get_services(), timeout=10.0)
                    self.hid_report_char = None
                    
                    # Look for HID service and report characteristic
                    for service in services:
                        _LOGGER.debug(f"Found service: {service.uuid}")
                        if str(service.uuid).lower() == HID_SERVICE_UUID.lower():
                            _LOGGER.info("Found HID service")
                            for char in service.characteristics:
                                if str(char.uuid).lower() == HID_REPORT_UUID.lower():
                                    self.hid_report_char = char
                                    _LOGGER.info("Found HID report characteristic")
                                    break
                    
                    if not self.hid_report_char:
                        _LOGGER.warning("HID report characteristic not found, using generic approach")
                    
                    self.device_address = device_address
                    self.is_connected = True
                    
                    # Get device info
                    device_info = await self._get_device_info()
                    self.device_name = device_info.get('name', 'Unknown Device')
                    
                    _LOGGER.info(f"Successfully connected to {self.device_name}")
                    self._notify_connection_status(True, f"Connected to {self.device_name}")
                    
                    return True
                    
                except asyncio.TimeoutError:
                    _LOGGER.warning(f"Service discovery timeout on attempt {attempt + 1}")
                    await self.disconnect()
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(3)
                    continue
                    
            except asyncio.TimeoutError:
                _LOGGER.warning(f"Connection timeout on attempt {attempt + 1}")
                if self.client:
                    try:
                        await self.client.disconnect()
                    except:
                        pass
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                continue
                
            except Exception as exc:
                _LOGGER.error(f"Connection attempt {attempt + 1} failed: {exc}")
                if self.client:
                    try:
                        await self.client.disconnect()
                    except:
                        pass
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2)
                continue
        
        # All attempts failed
        _LOGGER.error(f"All {max_attempts} connection attempts failed")
        self._notify_connection_status(False, f"Connection failed after {max_attempts} attempts")
        await self.disconnect()
        return False
    
    async def disconnect(self):
        """Disconnect from the current device."""
        if self.client and self.client.is_connected:
            try:
                await self.client.disconnect()
                _LOGGER.info("Disconnected from Bluetooth device")
            except Exception as exc:
                _LOGGER.error(f"Error during disconnect: {exc}")
        
        self.client = None
        self.is_connected = False
        self.device_address = None
        self.device_name = None
        self.hid_report_char = None
        self._notify_connection_status(False, "Disconnected")
    
    async def _get_device_info(self) -> Dict[str, str]:
        """Get device information."""
        info = {}
        
        if not self.client:
            return info
        
        try:
            # Try to read device name
            for service in await self.client.get_services():
                for char in service.characteristics:
                    if "device_name" in str(char.uuid).lower():
                        try:
                            name_bytes = await self.client.read_gatt_char(char.uuid)
                            info['name'] = name_bytes.decode('utf-8')
                        except:
                            pass
                        break
        except Exception as exc:
            _LOGGER.debug(f"Could not read device info: {exc}")
        
        return info
    
    async def send_key_command(self, key_code: str) -> bool:
        """
        Send a key command to the connected Android TV.
        
        Args:
            key_code: Key code constant (e.g., 'POWER', 'HOME', etc.)
            
        Returns:
            True if command sent successfully, False otherwise
        """
        if not self.is_connected or not self.client:
            _LOGGER.warning("Not connected to any device")
            return False
        
        # Map key codes to consumer control codes
        key_mapping = {
            'POWER': ConsumerControlCodes.POWER,
            'HOME': ConsumerControlCodes.HOME,
            'BACK': ConsumerControlCodes.BACK,
            'MENU': ConsumerControlCodes.MENU,
            'VOLUME_UP': ConsumerControlCodes.VOLUME_UP,
            'VOLUME_DOWN': ConsumerControlCodes.VOLUME_DOWN,
            'MUTE': ConsumerControlCodes.VOLUME_MUTE,
            'CHANNEL_UP': ConsumerControlCodes.CHANNEL_UP,
            'CHANNEL_DOWN': ConsumerControlCodes.CHANNEL_DOWN,
            'DPAD_UP': ConsumerControlCodes.UP,
            'DPAD_DOWN': ConsumerControlCodes.DOWN,
            'DPAD_LEFT': ConsumerControlCodes.LEFT,
            'DPAD_RIGHT': ConsumerControlCodes.RIGHT,
            'DPAD_CENTER': ConsumerControlCodes.SELECT,
            'PLAY_PAUSE': ConsumerControlCodes.PLAY_PAUSE,
            'STOP': ConsumerControlCodes.STOP,
            'FAST_FORWARD': ConsumerControlCodes.FAST_FORWARD,
            'REWIND': ConsumerControlCodes.REWIND,
            'PAIR': ConsumerControlCodes.PAIR,
        }
        
        consumer_code = key_mapping.get(key_code)
        if consumer_code is None:
            _LOGGER.warning(f"Unknown key code: {key_code}")
            return False
        
        try:
            # Send HID report
            success = await self._send_consumer_report(consumer_code)
            if success:
                _LOGGER.info(f"Sent key command: {key_code}")
            else:
                _LOGGER.warning(f"Failed to send key command: {key_code}")
            
            return success
            
        except Exception as exc:
            _LOGGER.error(f"Error sending key command {key_code}: {exc}")
            return False
    
    async def _send_consumer_report(self, usage_code: int) -> bool:
        """
        Send a consumer control report.
        
        Args:
            usage_code: HID usage code to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create HID report: Report ID + Usage Code (little endian)
            report = struct.pack('<BH', 0x01, usage_code)
            
            if self.hid_report_char:
                # Use HID report characteristic if available
                await self.client.write_gatt_char(self.hid_report_char, report)
            else:
                # Try to find a writable characteristic
                success = await self._try_generic_write(report)
                if not success:
                    _LOGGER.warning("Could not find suitable characteristic to write HID report")
                    return False
            
            # Send key release (usage code 0) after a short delay
            await asyncio.sleep(0.1)
            release_report = struct.pack('<BH', 0x01, 0x00)
            
            if self.hid_report_char:
                await self.client.write_gatt_char(self.hid_report_char, release_report)
            else:
                await self._try_generic_write(release_report)
            
            return True
            
        except Exception as exc:
            _LOGGER.error(f"Failed to send consumer report: {exc}")
            return False
    
    async def _try_generic_write(self, data: bytes) -> bool:
        """Try to write data to any writable characteristic."""
        try:
            services = await self.client.get_services()
            
            for service in services:
                for char in service.characteristics:
                    if 'write' in [prop.lower() for prop in char.properties]:
                        try:
                            await self.client.write_gatt_char(char.uuid, data)
                            _LOGGER.debug(f"Successfully wrote to characteristic {char.uuid}")
                            return True
                        except Exception:
                            continue
            
            return False
            
        except Exception as exc:
            _LOGGER.error(f"Generic write failed: {exc}")
            return False

    # Convenience methods for common remote control functions
    async def power(self) -> bool:
        """Send power button command."""
        return await self.send_key_command('POWER')
    
    async def home(self) -> bool:
        """Send home button command."""
        return await self.send_key_command('HOME')
    
    async def back(self) -> bool:
        """Send back button command."""
        return await self.send_key_command('BACK')
    
    async def menu(self) -> bool:
        """Send menu button command."""
        return await self.send_key_command('MENU')
    
    async def volume_up(self) -> bool:
        """Send volume up command."""
        return await self.send_key_command('VOLUME_UP')
    
    async def volume_down(self) -> bool:
        """Send volume down command."""
        return await self.send_key_command('VOLUME_DOWN')
    
    async def volume_mute(self) -> bool:
        """Send mute command."""
        return await self.send_key_command('MUTE')
    
    async def channel_up(self) -> bool:
        """Send channel up command."""
        return await self.send_key_command('CHANNEL_UP')
    
    async def channel_down(self) -> bool:
        """Send channel down command."""
        return await self.send_key_command('CHANNEL_DOWN')
    
    async def dpad_up(self) -> bool:
        """Send D-pad up command."""
        return await self.send_key_command('DPAD_UP')
    
    async def dpad_down(self) -> bool:
        """Send D-pad down command."""
        return await self.send_key_command('DPAD_DOWN')
    
    async def dpad_left(self) -> bool:
        """Send D-pad left command."""
        return await self.send_key_command('DPAD_LEFT')
    
    async def dpad_right(self) -> bool:
        """Send D-pad right command."""
        return await self.send_key_command('DPAD_RIGHT')
    
    async def dpad_center(self) -> bool:
        """Send D-pad center/OK command."""
        return await self.send_key_command('DPAD_CENTER')

    async def pair(self) -> bool:
        """
        Put the connected Android TV into pairing mode.
        
        Sends a PAIR HID report (usage code 0x0225) to the Android TV, which
        activates pairing mode on the TV, making it discoverable to other
        Bluetooth devices like phones, tablets, etc.
        
        Returns:
            True if the pairing mode command was sent successfully, False otherwise
        """
        _LOGGER.info("BluetoothRemoteController.pair() called")
        try:
            result = await self.send_key_command('PAIR')
            _LOGGER.debug("pair() result: %s", result)
            return result
        except Exception as exc:
            _LOGGER.exception("Exception in pair(): %s", exc)
            return False

    def get_device_info(self) -> Optional[Dict[str, str]]:
        """Get information about the connected device."""
        if not self.is_connected:
            return None
        
        return {
            'name': self.device_name or 'Unknown Device',
            'address': self.device_address or '',
            'type': 'Bluetooth HID',
            'manufacturer': 'Bluetooth Device'
        }


class BluetoothDeviceManager:
    """Manager for Bluetooth device connections and pairing."""
    
    def __init__(self):
        self.controller = BluetoothRemoteController()
        self.discovered_devices: List[Dict[str, str]] = []
        
    async def discover_devices(self, timeout: float = 20.0, max_attempts: int = 3) -> List[Dict[str, str]]:
        """Discover nearby Bluetooth devices with enhanced reliability."""
        self.discovered_devices = await self.controller.discover_android_tv_devices(timeout, max_attempts)
        return self.discovered_devices
    
    async def connect_to_device(self, device_address: str, max_attempts: int = 3) -> bool:
        """Connect to a specific device with retry logic."""
        return await self.controller.connect(device_address, max_attempts)
    
    async def disconnect(self):
        """Disconnect from current device."""
        await self.controller.disconnect()
    
    def is_connected(self) -> bool:
        """Check if connected to a device."""
        return self.controller.is_connected
    
    def get_connected_device_info(self) -> Optional[Dict[str, str]]:
        """Get info about connected device."""
        return self.controller.get_device_info()