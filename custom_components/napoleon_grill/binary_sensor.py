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
from homeassistant.const import EntityCategory

from .const import (
    DOMAIN,
    MANUFACTURER,
    PROP_DEVICE_NAME,
    PROP_GRILL_MODE,
    PROP_LCD_OFF,
    PROP_VERSION,
)
from .coordinator import NapoleonGrillCoordinator

def ayla_bool(value: object) -> bool | None:
    """Safely convert Ayla API values to bool."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "on", "yes", "active", "running"}:
            return True
        if normalized in {"0", "false", "off", "no", "inactive", "standby"}:
            return False
    return None

BINARY_SENSOR_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=PROP_GRILL_MODE,
        name="Grill Active",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    BinarySensorEntityDescription(
        key=PROP_LCD_OFF,
        name="Display Off",
        entity_registry_enabled_default=False,
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
        device_data = coordinator.data.get(device.serial_number, {})
        for description in BINARY_SENSOR_DESCRIPTIONS:
            if description.key in device_data:
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
        device_data = coordinator.data.get(serial_number, {})
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial_number)},
            manufacturer=MANUFACTURER,
            name=device_data.get(PROP_DEVICE_NAME) or f"Napoleon Grill {serial_number}",
            sw_version=device_data.get(PROP_VERSION),
        )

    @property
    def is_on(self) -> bool | None:  # type: ignore[override]
        """Return true if the binary sensor is on."""
        value = self.coordinator.data.get(self._serial_number, {}).get(
            self.entity_description.key
        )
        return ayla_bool(value)