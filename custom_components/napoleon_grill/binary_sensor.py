"""Binary sensor platform for Napoleon Grill."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    PROP_GRILL_MODE,
    PROP_LCD_OFF,
    PROP_VERSION,
)
from .coordinator import NapoleonGrillCoordinator

BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=PROP_GRILL_MODE,
        name="Grill Active",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key=PROP_LCD_OFF,
        name="Display Off",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Napoleon Grill binary sensors."""
    coordinator: NapoleonGrillCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device in coordinator.devices:
        for description in BINARY_SENSOR_DESCRIPTIONS:
            entities.append(
                NapoleonGrillBinarySensor(
                    coordinator, device.serial_number, description
                )
            )

    async_add_entities(entities)


class NapoleonGrillBinarySensor(CoordinatorEntity, BinarySensorEntity):  # type: ignore[misc]
    """Representation of a Napoleon Grill binary sensor."""

    def __init__(
        self,
        coordinator: NapoleonGrillCoordinator,
        serial_number: str,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._serial_number = serial_number
        self._attr_unique_id = f"{serial_number}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial_number)},
            manufacturer=MANUFACTURER,
            name=f"Napoleon Grill {serial_number}",
            sw_version=coordinator.data.get(serial_number, {}).get(PROP_VERSION),
        )

    @property
    def is_on(self) -> bool | None:  # type: ignore[override]
        """Return true if the binary sensor is on."""
        value = self.coordinator.data.get(self._serial_number, {}).get(
            self.entity_description.key
        )
        if value is None:
            return None
        return bool(value)