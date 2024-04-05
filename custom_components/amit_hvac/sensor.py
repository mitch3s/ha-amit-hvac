"""Platform for sensor integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from amit_hvac_control.api.status import DataResult

from .api import AmitApi
from .api_helper import AmitApiHelper
from .const import DEVICE_HEATING_ID, DEVICE_VENTILATION_ID, DOMAIN
from .coordinator import AmitSensorCoordinator


@dataclass(kw_only=True)
class AmitSensorEntityDescription(SensorEntityDescription):
    """Describes Amit sensor entity."""

    device_identifier: str
    exists_fn: Callable[[DataResult], bool] = lambda _: True
    value_fn: Callable[[DataResult], StateType]


SENSORS = {
    "temperature": AmitSensorEntityDescription(
        key="temperature",
        device_identifier=DEVICE_HEATING_ID,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda result: result.temperature,
        exists_fn=lambda result: bool(result.temperature),
    ),
    "air_temperature": AmitSensorEntityDescription(
        key="air_temperature",
        device_identifier=DEVICE_VENTILATION_ID,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda result: result.air_temperature,
        exists_fn=lambda result: bool(result.air_temperature),
    ),
    "co2": AmitSensorEntityDescription(
        key="co2",
        device_identifier=DEVICE_VENTILATION_ID,
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda result: result.co_2,
        exists_fn=lambda result: bool(result.co_2),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up devices."""

    helper: AmitApiHelper = hass.data[DOMAIN][entry.entry_id]
    coordinator = AmitSensorCoordinator(hass, helper.api)

    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        AmitSensorEntity(helper.api, coordinator, description, entry.entry_id)
        for description in SENSORS.values()
    )


class AmitSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        api: AmitApi,
        coordinator: AmitSensorCoordinator,
        entity_description: AmitSensorEntityDescription,
        entry_id: str,
    ) -> None:
        """Set up the instance."""
        super().__init__(coordinator)
        self._api = api
        self.entity_description = entity_description
        self._attr_available = False  # This overrides the default
        self._attr_unique_id = f"{entry_id}-{entity_description.key}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""

        self._attr_available = True
        self._attr_native_value = self.entity_description.value_fn(
            self.coordinator.data
        )

        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entity_description.device_identifier)}
        )
