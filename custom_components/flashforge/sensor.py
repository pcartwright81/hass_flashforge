"""Add Flashforge sensors."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,  # Added for Disk Space
    PERCENTAGE,
    EntityCategory,
    UnitOfInformation,  # Added for TVOC
    UnitOfLength,  # Added for Filament/Z-Offset
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from flashforge.models import FFMachineInfo

    from .data_update_coordinator import FlashForgeDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FlashforgeSensorEntityDescription(SensorEntityDescription):
    """Sensor entity description with added value fnc."""

    value_fnc: Callable[[FFMachineInfo], str | int | float | None] | None = None
    exists_fn: Callable[[FFMachineInfo], bool] = lambda _: True


SENSORS: tuple[FlashforgeSensorEntityDescription, ...] = (
    # CORE STATUS SENSORS
    FlashforgeSensorEntityDescription(
        key="status",
        translation_key="status",
        icon="mdi:printer-3d",
        value_fnc=lambda info: info.machine_state.value,
    ),
    FlashforgeSensorEntityDescription(
        key="job_percentage",
        translation_key="job_percentage",
        icon="mdi:file-percent",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        # Use print_progress (float 0.0-1.0)
        value_fnc=lambda info: info.print_progress * 100.0,
    ),
    FlashforgeSensorEntityDescription(
        key="file",
        translation_key="file",
        icon="mdi:file-cad",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fnc=lambda info: info.print_file_name,
    ),
    FlashforgeSensorEntityDescription(
        key="current_layer",
        translation_key="current_layer",
        icon="mdi:layers-edit",
        state_class=SensorStateClass.MEASUREMENT,
        value_fnc=lambda info: info.current_print_layer,
    ),
    FlashforgeSensorEntityDescription(
        key="total_layers",
        translation_key="total_layers",
        icon="mdi:layers-triple",
        state_class=SensorStateClass.MEASUREMENT,
        value_fnc=lambda info: info.total_print_layers,
    ),
    FlashforgeSensorEntityDescription(
        key="print_time_remaining",
        translation_key="print_time_remaining",
        icon="mdi:timer-sand",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        value_fnc=lambda info: info.estimated_time,
    ),
    FlashforgeSensorEntityDescription(
        key="print_eta",
        translation_key="print_eta",
        icon="mdi:clock-outline",
        value_fnc=lambda info: info.print_eta,
    ),
    FlashforgeSensorEntityDescription(
        key="print_duration",
        translation_key="print_duration",
        icon="mdi:timer",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        value_fnc=lambda info: info.print_duration,
    ),
    # TEMPERATURE SENSORS
    FlashforgeSensorEntityDescription(
        key="bed_temp",
        translation_key="bed_temp",
        icon="mdi:radiator",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fnc=lambda info: info.print_bed.current if info.print_bed else None,
        exists_fn=lambda info: info.print_bed is not None,
    ),
    FlashforgeSensorEntityDescription(
        key="bed_target_temp",
        translation_key="bed_target_temp",
        icon="mdi:radiator-off",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fnc=lambda info: info.print_bed.set if info.print_bed else None,
        exists_fn=lambda info: info.print_bed is not None,
    ),
    FlashforgeSensorEntityDescription(
        key="extruder_temp",
        translation_key="extruder_temp",
        icon="mdi:printer-3d-nozzle",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fnc=lambda info: info.extruder.current if info.extruder else None,
        exists_fn=lambda info: info.extruder is not None,
    ),
    FlashforgeSensorEntityDescription(
        key="extruder_target_temp",
        translation_key="extruder_target_temp",
        icon="mdi:printer-3d-nozzle-alert",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fnc=lambda info: info.extruder.set if info.extruder else None,
        exists_fn=lambda info: info.extruder is not None,
    ),
    # MISSING DIAGNOSTIC & LIFETIME SENSORS
    FlashforgeSensorEntityDescription(
        key="lifetime_print_time",
        translation_key="lifetime_print_time",
        icon="mdi:history",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fnc=lambda info: info.cumulative_print_time,
    ),
    FlashforgeSensorEntityDescription(
        key="lifetime_filament",
        translation_key="lifetime_filament",
        icon="mdi:tape-measure",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fnc=lambda info: info.cumulative_filament,
    ),
    FlashforgeSensorEntityDescription(
        key="free_disk_space",
        translation_key="free_disk_space",
        icon="mdi:sd-storage",
        native_unit_of_measurement=UnitOfInformation.MEGABYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fnc=lambda info: float(info.free_disk_space),
    ),
    FlashforgeSensorEntityDescription(
        key="firmware_version",
        translation_key="firmware_version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fnc=lambda info: info.firmware_version,
    ),
    FlashforgeSensorEntityDescription(
        key="error_code",
        translation_key="error_code",
        icon="mdi:alert-octagon",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fnc=lambda info: info.error_code,
        exists_fn=lambda info: info.error_code is not None and info.error_code != "",
    ),
    FlashforgeSensorEntityDescription(
        key="tvoc",
        translation_key="tvoc",
        icon="mdi:air-filter",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fnc=lambda info: info.tvoc,
        exists_fn=lambda info: info.tvoc is not None,
    ),
    FlashforgeSensorEntityDescription(
        key="z_offset",
        translation_key="z_offset",
        icon="mdi:axis-z-arrow",
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fnc=lambda info: info.z_axis_compensation,
        exists_fn=lambda info: info.z_axis_compensation is not None,
    ),
    FlashforgeSensorEntityDescription(
        key="mac_address",
        translation_key="mac_address",
        icon="mdi:network-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fnc=lambda info: info.mac_address,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the available FlashForge sensors platform."""
    _LOGGER.debug("async_setup_entry - sensors")
    coordinator: FlashForgeDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    # Pre-check info to filter entities that don't exist (e.g., TVOC on some models)
    info = coordinator.data.get("info")
    entities = [
        FlashForgeSensor(coordinator=coordinator, description=description)
        for description in SENSORS
        # Only add the entity if the info model is None (initial setup)
        # OR if the custom exists_fn returns True for the populated info.
        if info is None or description.exists_fn(info)
    ]

    async_add_entities(entities)


class FlashForgeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a FlashForge sensor."""

    coordinator: FlashForgeDataUpdateCoordinator
    entity_description: FlashforgeSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FlashForgeDataUpdateCoordinator,
        description: FlashforgeSensorEntityDescription,
    ) -> None:
        """Initialize a new Flashforge sensor."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.unique_id}_{description.key}"

        # Note: self._attr_name is automatically set by _attr_has_entity_name = True
        # if translation_key is used. If not, the manual title() attribute naming
        # is used, but for simplicity, we rely on the HA naming system here.
        self._attr_name = f"{description.key.replace('_', ' ').title()}"

    @property
    def native_value(self) -> str | int | float | None:
        """Return sensor state."""
        if self.entity_description.value_fnc is None:
            return None

        info = self.coordinator.data.get("info")

        # Check if FFMachineInfo object exists before calling the value function
        if info is None:
            return None

        return self.entity_description.value_fnc(info)
