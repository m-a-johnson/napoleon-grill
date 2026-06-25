"""Number platform for Napoleon Grill."""
from __future__ import annotations

import json

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    PROP_DEVICE_NAME,
    PROP_TARGET_TEMP_ONE,
    PROP_TARGET_TEMP_TWO,
    PROP_TARGET_TEMP_THREE,
    PROP_TARGET_TEMP_FOUR,
    PROP_VERSION,
    TRGT_TMP_NOT_SET,
)
from .coordinator import NapoleonGrillCoordinator

PROBE_TARGET_PROPS = [
    (PROP_TARGET_TEMP_ONE, "Probe 1"),
    (PROP_TARGET_TEMP_TWO, "Probe 2"),
    (PROP_TARGET_TEMP_THREE, "Probe 3"),
    (PROP_TARGET_TEMP_FOUR, "Probe 4"),
]


def parse_target_temp(value: str | None) -> list[float]:
    """Parse target temp JSON blob and return list of values, filtering out sentinel."""
    if not value:
        return []
    try:
        data = json.loads(value) if isinstance(value, str) else value
        pts = data.get("ptr", [])
        return [p for p in pts if p != TRGT_TMP_NOT_SET]
    except (json.JSONDecodeError, AttributeError):
        return []


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Napoleon Grill number entities."""
    coordinator: NapoleonGrillCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device in coordinator.devices:
        device_data = coordinator.data.get(device.serial_number, {})
        for prop, probe_name in PROBE_TARGET_PROPS:
            if prop in device_data:
                entities.append(
                    NapoleonGrillTargetTemp(
                        coordinator, device.serial_number, prop, f"{probe_name} Target Low", 0
                    )
                )
                entities.append(
                    NapoleonGrillTargetTemp(
                        coordinator, device.serial_number, prop, f"{probe_name} Target High", 1
                    )
                )

    async_add_entities(entities)


class NapoleonGrillTargetTemp(CoordinatorEntity, NumberEntity):  # type: ignore[misc]
    """Number entity for probe target temperature."""

    coordinator: NapoleonGrillCoordinator

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0.0
    _attr_native_max_value = 400.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: NapoleonGrillCoordinator,
        serial_number: str,
        prop: str,
        name: str,
        index: int,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._prop = prop
        self._index = index
        self._attr_unique_id = f"{serial_number}_{prop}_{index}"
        self._attr_name = name
        device_data = coordinator.data.get(serial_number, {})
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial_number)},
            manufacturer=MANUFACTURER,
            name=device_data.get(PROP_DEVICE_NAME) or f"Napoleon Grill {serial_number}",
            sw_version=device_data.get(PROP_VERSION),
        )

    @property
    def native_value(self) -> float | None:  # type: ignore[override]
        """Return the current target temperature."""
        value = self.coordinator.data.get(self._serial_number, {}).get(self._prop)
        pts = parse_target_temp(value)
        if not pts:
            return None
        if self._index == 0:
            return pts[0]
        if len(pts) > 1:
            return pts[1]
        return pts[0]

    async def async_set_native_value(self, value: float) -> None:
        """Set the target temperature."""
        current = self.coordinator.data.get(self._serial_number, {}).get(self._prop)
        pts = parse_target_temp(current)

        if self._index == 0:
            low = value
            high = pts[1] if len(pts) > 1 else value
        else:
            low = pts[0] if pts else value
            high = value

        if low == high:
            new_value = json.dumps({"ptr": [low]})
        else:
            new_value = json.dumps({"ptr": [low, high]})

        device = next(
            d for d in self.coordinator.devices
            if d.serial_number == self._serial_number
        )
        await device.async_set_property_value(self._prop, new_value)
        await self.coordinator.async_request_refresh()