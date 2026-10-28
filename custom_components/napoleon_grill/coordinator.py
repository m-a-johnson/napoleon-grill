"""Data update coordinator for Napoleon Grill."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from aiohttp import ClientError
from ayla_iot_unofficial import new_ayla_api, AylaAuthError
from ayla_iot_unofficial.device import Device
from ayla_iot_unofficial.exc import AylaError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_APP_ID,
    CONF_APP_SECRET,
    SCAN_INTERVAL_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

# The library's own HTTP timeout is 5 minutes; cap a whole poll well below that
# so one hung request can't leave the entities stale for minutes.
UPDATE_TIMEOUT_SECONDS = 60


class NapoleonGrillCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching Napoleon Grill data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.entry = entry
        self.api = new_ayla_api(
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
            entry.data[CONF_APP_ID],
            entry.data[CONF_APP_SECRET],
        )
        self.devices: list[Device] = []
        self._auth_lock = asyncio.Lock()
        self._force_sign_in = False

    async def async_ensure_auth(self) -> None:
        """Make sure we hold a usable token, signing in again if we don't.

        ayla-iot-unofficial never refreshes its token. Once the token is expired,
        or within 10 minutes of expiring, every request raises AylaNotAuthedError /
        AylaAuthExpiringError (both AylaError, NOT AylaAuthError) until the caller
        signs in again. check_auth() raises exactly in those cases.
        """
        async with self._auth_lock:
            if not self._force_sign_in:
                try:
                    self.api.check_auth()
                    return
                except AylaError:
                    pass  # missing, expired or expiring token: sign in below
            _LOGGER.debug("Signing in to Ayla Networks")
            await self.api.async_sign_in()
            self._force_sign_in = False

    async def _async_update_data(self) -> dict:
        """Fetch data from Napoleon Grill API."""
        try:
            async with asyncio.timeout(UPDATE_TIMEOUT_SECONDS):
                await self.async_ensure_auth()
                if not self.devices:
                    self.devices = await self.api.async_get_devices()

                data = {}
                for device in self.devices:
                    await device.async_update()
                    data[device.serial_number] = device.property_values
                return data

        except AylaAuthError as err:
            # Ayla rejected the stored credentials during sign-in.
            raise ConfigEntryAuthFailed("Authentication failed") from err
        except (ClientError, TimeoutError) as err:
            # Network trouble says nothing about the token; just retry next poll.
            raise UpdateFailed(f"Cannot reach Ayla Networks: {err}") from err
        except Exception as err:
            # Anything else (e.g. an error body where properties were expected)
            # can mean the token was revoked server-side. Sign in fresh next poll.
            self._force_sign_in = True
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def async_shutdown(self) -> None:
        """Stop polling and close the library's HTTP session."""
        await super().async_shutdown()
        session = self.api.websession
        if session is not None and not session.closed:
            await session.close()
