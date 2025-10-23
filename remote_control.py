import asyncio
import logging
from typing import Callable

from androidtvremote2 import (
    AndroidTVRemote,
    CannotConnect,
    ConnectionClosed,
    InvalidAuth,
)
from zeroconf import IPVersion, ServiceStateChange, Zeroconf
from zeroconf._services.info import AsyncServiceInfo
from zeroconf.asyncio import AsyncServiceBrowser, AsyncZeroconf

_LOGGER = logging.getLogger(__name__)


class RemoteControl:
    POWER: str = 'POWER'
    BACK: str = 'BACK'
    HOME: str = 'HOME'
    MENU: str = 'MENU'
    VOLUME_MUTE: str = 'MUTE'
    VOLUME_UP: str = 'VOLUME_UP'
    VOLUME_DOWN: str = 'VOLUME_DOWN'
    DPAD_UP: str = 'DPAD_UP'
    DPAD_DOWN: str = 'DPAD_DOWN'
    DPAD_LEFT: str = 'DPAD_LEFT'
    DPAD_RIGHT: str = 'DPAD_RIGHT'
    DPAD_CENTER: str = 'DPAD_CENTER'
    CHANNEL_UP: str = 'CHANNEL_UP'
    CHANNEL_DOWN: str = 'CHANNEL_DOWN'

    def __init__(self):
        self.found_addresses: list = []
        self.remote: AndroidTVRemote | None = None

    async def find_android_tv(self) -> list:
        """Discover Android TV devices using mDNS.

        Returns a list of IPv4 addresses of discovered devices.
        The method will perform a short browse and return whatever it finds.
        """
        self.found_addresses = []

        # Try a slightly longer default timeout and search multiple service types
        timeout_seconds = 8

        zc = AsyncZeroconf()
        # Primary service for androidtvremote2, fallback to common cast service
        services = ['_androidtvremote2._tcp.local.', '_googlecast._tcp.local.']

        _LOGGER.debug('Starting mDNS discovery for services: %s (timeout=%ds)', services, timeout_seconds)

        # Register browser for all service types
        browsers = [AsyncServiceBrowser(zc.zeroconf, [svc], handlers=[self._async_on_service_state_change]) for svc in services]

        # Wait for responses
        await asyncio.sleep(timeout_seconds)

        # Cancel browsers and close zeroconf
        for b in browsers:
            try:
                await b.async_cancel()
            except Exception:
                # Some versions may not require explicit cancel
                pass

        try:
            await zc.async_close()
        except Exception:
            pass

        _LOGGER.debug('Discovery complete, found addresses: %s', self.found_addresses)
        return self.found_addresses

    async def pair(self, host: str, callback: Callable):
        self.remote = AndroidTVRemote(
            'Android TV Remote demo',
            'keys/cert.pem',
            'keys/key.pem',
            host,
        )

        try:
            # Generate certificate if needed
            if await self.remote.async_generate_cert_if_missing():
                _LOGGER.info('Generated new certificate')
            
            # Start pairing process
            _LOGGER.info('Starting pairing process with %s', host)
            await self.remote.async_start_pairing()
            _LOGGER.info('Pairing started, waiting for code...')
            
            # Get pairing code from user
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    pairing_code, done = callback()
                    if not done:
                        _LOGGER.warning('Pairing cancelled by user')
                        self.remote.disconnect()
                        raise RuntimeError('Pairing cancelled by user')
                    
                    _LOGGER.info('Finishing pairing with code: %s***', pairing_code[:2] if pairing_code else '')
                    await self.remote.async_finish_pairing(pairing_code)
                    _LOGGER.info('Pairing successful')
                    break
                    
                except InvalidAuth as exc:
                    _LOGGER.error('Invalid pairing code (attempt %d/%d): %s', attempt + 1, max_attempts, exc)
                    if attempt == max_attempts - 1:
                        raise
                    continue
                except Exception as exc:
                    _LOGGER.error('Pairing error: %s', exc)
                    raise
            
            # Now try to connect
            _LOGGER.info('Attempting to connect to %s', host)
            max_retries = 3
            for retry in range(max_retries):
                try:
                    await self.remote.async_connect()
                    _LOGGER.info('Successfully connected to %s', host)
                    break
                except InvalidAuth as exc:
                    _LOGGER.error('Auth error, need to pair again (retry %d/%d): %s', retry + 1, max_retries, exc)
                    if retry == max_retries - 1:
                        raise
                    await asyncio.sleep(1)
                except (CannotConnect, ConnectionClosed) as exc:
                    _LOGGER.error('Connection error (retry %d/%d): %s', retry + 1, max_retries, exc)
                    if retry == max_retries - 1:
                        raise
                    await asyncio.sleep(2)
            
            # Start keep-alive
            self.remote.keep_reconnecting()
            
            # Log device info
            _LOGGER.info('Device connected. Info: %s', self.remote.device_info)
            _LOGGER.info('Power state: %s', self.remote.is_on)
            
            # Add callbacks
            self.remote.add_is_on_updated_callback(self._is_on_updated)
            self.remote.add_current_app_updated_callback(self._current_app_updated)
            self.remote.add_volume_info_updated_callback(self._volume_info_updated)
            self.remote.add_is_available_updated_callback(self._is_available_updated)
            
        except Exception as exc:
            _LOGGER.error('Fatal pairing/connection error: %s', exc)
            raise

    def power(self) -> None:
        self.remote.send_key_command(self.POWER)

    def back(self) -> None:
        self.remote.send_key_command(self.BACK)

    def home(self) -> None:
        self.remote.send_key_command(self.HOME)

    def menu(self) -> None:
        self.remote.send_key_command(self.MENU)

    def channel_up(self) -> None:
        self.remote.send_key_command(self.CHANNEL_UP)

    def channel_down(self) -> None:
        self.remote.send_key_command(self.CHANNEL_DOWN)

    def volume_mute(self) -> None:
        self.remote.send_key_command(self.VOLUME_MUTE)

    def volume_up(self) -> None:
        self.remote.send_key_command(self.VOLUME_UP)

    def volume_down(self) -> None:
        self.remote.send_key_command(self.VOLUME_DOWN)

    def dpad_up(self) -> None:
        self.remote.send_key_command(self.DPAD_UP)

    def dpad_down(self) -> None:
        self.remote.send_key_command(self.DPAD_DOWN)

    def dpad_left(self) -> None:
        self.remote.send_key_command(self.DPAD_LEFT)

    def dpad_right(self) -> None:
        self.remote.send_key_command(self.DPAD_RIGHT)

    def dpad_center(self) -> None:
        self.remote.send_key_command(self.DPAD_CENTER)

    def device_info(self) -> dict[str, str] | None:
        return self.remote.device_info

    def disconnect(self):
        self.remote.disconnect()

    async def _pair(self, callback: Callable) -> None:
        """Legacy pairing method - kept for compatibility."""
        _LOGGER.info('Using legacy pairing method')
        await self.remote.async_start_pairing()
        while True:
            pairing_code, done = callback()
            if not done:
                self.remote.disconnect()
                raise RuntimeError('Interrupted by user')

            try:
                return await self.remote.async_finish_pairing(pairing_code)
            except InvalidAuth as exc:
                _LOGGER.error('Invalid pairing code. Error: %s', exc)
                continue
            except ConnectionClosed as exc:
                _LOGGER.error('Connection closed during pairing. Error: %s', exc)
                return await self._pair(callback)

    def _async_on_service_state_change(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        if state_change is not ServiceStateChange.Added:
            return
        asyncio.ensure_future(self._async_display_service_info(zeroconf, service_type, name))

    async def _async_display_service_info(self, zeroconf: Zeroconf, service_type: str, name: str) -> None:
        info = AsyncServiceInfo(service_type, name)
        await info.async_request(zeroconf, 2000)

        if info:
            self.found_addresses.extend(info.parsed_scoped_addresses(IPVersion.V4Only))

    def _is_on_updated(self, is_on: bool) -> None:
        _LOGGER.info('Notified that is_on: %s', is_on)

    def _current_app_updated(self, current_app: str) -> None:
        _LOGGER.info('Notified that current_app: %s', current_app)

    def _volume_info_updated(self, volume_info: dict[str, str | bool]) -> None:
        _LOGGER.info('Notified that volume_info: %s', volume_info)

    def _is_available_updated(self, is_available: bool) -> None:
        _LOGGER.info('Notified that is_available: %s', is_available)
