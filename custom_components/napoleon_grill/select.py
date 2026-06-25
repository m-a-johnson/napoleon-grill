"""Select platform for Napoleon Grill."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    BRIGHTNESS_OPTIONS,
    DOMAIN,
    MANUFACTURER,
    PROP_BRIGHTNESS_LEVEL,
    PROP_DEVICE_NAME,
    PROP_VERSION,
)
from .coordinator import NapoleonGrillCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Napoleon Grill select entities."""
    coordinator: NapoleonGrillCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device in coordinator.devices:
        device_data = coordinator.data.get(device.serial_number, {})
        if PROP_BRIGHTNESS_LEVEL in device_data:
            entities.append(
                NapoleonGrillBrightnessSelect(coordinator, device.serial_number)
            )

    async_add_entities(entities)


class NapoleonGrillBrightnessSelect(CoordinatorEntity, SelectEntity):  # type: ignore[misc]
    """Select entity for LED brightness control."""

    _attr_options = list(BRIGHTNESS_OPTIONS.keys())
    coordinator: NapoleonGrillCoordinator
    def __init__(
        self,
        coordinator: NapoleonGrillCoordinator,
        serial_number: str,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._attr_unique_id = f"{serial_number}_{PROP_BRIGHTNESS_LEVEL}"
        self._attr_name = "LED Brightness"
        device_data = coordinator.data.get(serial_number, {})
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial_number)},
            manufacturer=MANUFACTURER,
            name=device_data.get(PROP_DEVICE_NAME) or f"Napoleon Grill {serial_number}",
            sw_version=device_data.get(PROP_VERSION),
        )

    @property
    def current_option(self) -> str | None:  # type: ignore[override]
        """Return the current brightness option."""
        value = self.coordinator.data.get(self._serial_number, {}).get(
            PROP_BRIGHTNESS_LEVEL
        )
        reverse_map = {v: k for k, v in BRIGHTNESS_OPTIONS.items()}
        return reverse_map.get(value)

    async def async_select_option(self, option: str) -> None:
        """Change the brightness setting."""
        value = BRIGHTNESS_OPTIONS[option]
        device = next(
            d for d in self.coordinator.devices
            if d.serial_number == self._serial_number
        )
        await device.async_set_property_value(PROP_BRIGHTNESS_LEVEL, value)
        await self.coordinator.async_request_refresh()