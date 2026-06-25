"""Text platform for Napoleon Grill."""
from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    PROP_DEVICE_NAME,
    PROP_PROBE_ONE_NAME,
    PROP_PROBE_TWO_NAME,
    PROP_PROBE_THREE_NAME,
    PROP_PROBE_FOUR_NAME,
    PROP_COOK_PRESET_ONE,
    PROP_COOK_PRESET_TWO,
    PROP_COOK_PRESET_THREE,
    PROP_COOK_PRESET_FOUR,
    PROP_VERSION,
)
from .coordinator import NapoleonGrillCoordinator

PROBE_NAME_PROPS = [
    (PROP_PROBE_ONE_NAME, "Probe 1 Name"),
    (PROP_PROBE_TWO_NAME, "Probe 2 Name"),
    (PROP_PROBE_THREE_NAME, "Probe 3 Name"),
    (PROP_PROBE_FOUR_NAME, "Probe 4 Name"),
]

COOK_PRESET_PROPS = [
    (PROP_COOK_PRESET_ONE, "Probe 1 Cook Preset"),
    (PROP_COOK_PRESET_TWO, "Probe 2 Cook Preset"),
    (PROP_COOK_PRESET_THREE, "Probe 3 Cook Preset"),
    (PROP_COOK_PRESET_FOUR, "Probe 4 Cook Preset"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Napoleon Grill text entities."""
    coordinator: NapoleonGrillCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device in coordinator.devices:
        device_data = coordinator.data.get(device.serial_number, {})
        for prop, name in PROBE_NAME_PROPS + COOK_PRESET_PROPS:
            if prop in device_data:
                entities.append(
                    NapoleonGrillText(coordinator, device.serial_number, prop, name)
                )

    async_add_entities(entities)


class NapoleonGrillText(CoordinatorEntity, TextEntity):  # type: ignore[misc]
    """Text entity for probe names and cook presets."""

    coordinator: NapoleonGrillCoordinator

    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = 32

    def __init__(
        self,
        coordinator: NapoleonGrillCoordinator,
        serial_number: str,
        prop: str,
        name: str,
    ) -> None:
        """Initialize the text entity."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._prop = prop
        self._attr_unique_id = f"{serial_number}_{prop}"
        self._attr_name = name
        device_data = coordinator.data.get(serial_number, {})
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial_number)},
            manufacturer=MANUFACTURER,
            name=device_data.get(PROP_DEVICE_NAME) or f"Napoleon Grill {serial_number}",
            sw_version=device_data.get(PROP_VERSION),
        )

    @property
    def native_value(self) -> str | None:  # type: ignore[override]
        """Return the current text value."""
        value = self.coordinator.data.get(self._serial_number, {}).get(self._prop)
        return value if value else ""

    async def async_set_value(self, value: str) -> None:
        """Set the text value."""
        device = next(
            d for d in self.coordinator.devices
            if d.serial_number == self._serial_number
        )
        await device.async_set_property_value(self._prop, value)
        await self.coordinator.async_request_refresh()