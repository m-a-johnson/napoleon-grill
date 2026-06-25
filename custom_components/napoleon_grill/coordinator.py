"""Data update coordinator for Napoleon Grill."""
from __future__ import annotations

import logging
from datetime import timedelta

from ayla_iot_unofficial import new_ayla_api, AylaAuthError
from ayla_iot_unofficial.device import Device

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

        
    async def _async_update_data(self) -> dict:
        """Fetch data from Napoleon Grill API."""
        try:
            if not self.devices:
                await self.api.async_sign_in()
                self.devices = await self.api.async_get_devices()

            data = {}
            for device in self.devices:
                await device.async_update()
                data[device.serial_number] = device.property_values

            return data

        except AylaAuthError:
            _LOGGER.debug("Auth token expired, re-authenticating")
            try:
                await self.api.async_sign_in()
                self.devices = await self.api.async_get_devices()
                data = {}
                for device in self.devices:
                    await device.async_update()
                    data[device.serial_number] = device.property_values
                return data
            except AylaAuthError as err:
                raise ConfigEntryAuthFailed("Authentication failed") from err
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err