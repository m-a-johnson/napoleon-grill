"""Sensor platform for Napoleon Grill."""
from __future__ import annotations
from decimal import Decimal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature,  EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    PROP_DEVICE_NAME,
    PROP_PROBE_ONE_TEMP,
    PROP_PROBE_TWO_TEMP,
    PROP_PROBE_THREE_TEMP,
    PROP_PROBE_FOUR_TEMP,
    PROP_BURNER_LEVEL,
    PROP_RSSI,
    PROP_TANK_WEIGHT,
    PROP_VERSION,
)
from .coordinator import NapoleonGrillCoordinator

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=PROP_PROBE_ONE_TEMP,
        name="Probe 1 Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key=PROP_PROBE_TWO_TEMP,
        name="Probe 2 Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key=PROP_PROBE_THREE_TEMP,
        name="Probe 3 Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key=PROP_PROBE_FOUR_TEMP,
        name="Probe 4 Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(
        key=PROP_BURNER_LEVEL,
        name="Burner Level",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=PROP_RSSI,
        name="WiFi Signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="dBm",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=PROP_TANK_WEIGHT,
        name="Tank Weight",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="g",
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Napoleon Grill sensors."""
    coordinator: NapoleonGrillCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device in coordinator.devices:
        device_data = coordinator.data.get(device.serial_number, {})
        for description in SENSOR_DESCRIPTIONS:
            if description.key in device_data:
                entities.append(
                    NapoleonGrillSensor(coordinator, device.serial_number, description)
                )
    async_add_entities(entities)


class NapoleonGrillSensor(CoordinatorEntity, SensorEntity): # type: ignore[misc]
    """Representation of a Napoleon Grill sensor."""

    def __init__(
        self,
        coordinator: NapoleonGrillCoordinator,
        serial_number: str,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
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
    def native_value(self) -> float | int | str | Decimal | None: # type: ignore[override]
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._serial_number, {}).get(
            self.entity_description.key
        )