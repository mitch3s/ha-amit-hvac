"""Platform for sensor integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONCENTRATION_PARTS_PER_MILLION, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from amit_hvac_control.api.ventilation import VentilationResult

from .api import AmitApi
from .api_helper import AmitApiHelper
from .const import DEVICE_VENTILATION_ID, DOMAIN
from .coordinator import AmitSensorCoordinator


@dataclass(kw_only=True)
class AmitNumberEntityDescription(NumberEntityDescription):
    """Describes Amit sensor entity."""

    device_identifier: str
    exists_fn: Callable[[VentilationResult], bool] = lambda _: True
    value_fn: Callable[[VentilationResult], StateType]


KEY_TARGET_AIR_TEMPERATURE = "target_air_temperature"
KEY_TARGET_CO2 = "target_co2"

NUMBERS = {
    KEY_TARGET_AIR_TEMPERATURE: AmitNumberEntityDescription(
        key=KEY_TARGET_AIR_TEMPERATURE,
        translation_key=KEY_TARGET_AIR_TEMPERATURE,
        device_class=NumberDeviceClass.TEMPERATURE,
        device_identifier=DEVICE_VENTILATION_ID,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=15,
        native_max_value=25,
        value_fn=lambda result: result.air_temp_setpoint,
        exists_fn=lambda result: bool(result.air_temp_setpoint),
    ),
    KEY_TARGET_CO2: AmitNumberEntityDescription(
        key=KEY_TARGET_CO2,
        translation_key=KEY_TARGET_CO2,
        device_identifier=DEVICE_VENTILATION_ID,
        device_class=NumberDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        native_min_value=0,
        native_max_value=1500,
        native_step=100,
        value_fn=lambda result: result.co2_setpoint,
        exists_fn=lambda result: bool(result.co2_setpoint),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up devices."""

    helper: AmitApiHelper = hass.data[DOMAIN][entry.entry_id]
    coordinator = helper.ventilation_coordinator

    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        AmitNumberEntity(helper.api, coordinator, description, entry.entry_id)
        for description in NUMBERS.values()
    )


class AmitNumberEntity(CoordinatorEntity, NumberEntity):
    """Representation of a Number."""

    _attr_has_entity_name = True

    def __init__(
        self,
        api: AmitApi,
        coordinator: AmitSensorCoordinator,
        entity_description: AmitNumberEntityDescription,
        entry_id: str,
    ) -> None:
        """Set up the instance."""
        super().__init__(coordinator)
        self._api = api
        self.entity_description = entity_description
        self._attr_available = False
        self._attr_unique_id = f"{entry_id}-{entity_description.key}"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.entity_description.value_fn(
            self.coordinator.data["ventilation_data"]
        )
        self._attr_available = True
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        key = self.entity_description.key
        if key == KEY_TARGET_AIR_TEMPERATURE:
            await self._async_set_air_temp_setpoint(value)
        elif key == KEY_TARGET_CO2:
            await self._async_set_co2_setpoint(value)
        await self.coordinator.async_request_refresh()

    async def _async_set_air_temp_setpoint(self, value: float):
        """Set air temperature setpoint."""
        async with self._api.create_client() as client:
            await client.ventilation_api.async_set_target_air_temperature(value)

    async def _async_set_co2_setpoint(self, value: float):
        """Set Co2 setpoint."""
        async with self._api.create_client() as client:
            await client.ventilation_api.async_set_target_co2(value)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entity_description.device_identifier)}
        )
