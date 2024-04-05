"""Platform for sensor integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_OFF,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from amit_hvac_control.api.status import DataResult
from amit_hvac_control.api.ventilation import VentilationResult
from amit_hvac_control.models import HeatingMode, Season, VentilationMode

from .api import AmitApi
from .api_helper import AmitApiHelper
from .const import DEVICE_HEATING_ID, DEVICE_VENTILATION_ID, DOMAIN
from .coordinator import AmitFanCoordinator

FAN_MODE_MAP = {
    FAN_OFF: VentilationMode.OFF,
    FAN_LOW: VentilationMode.LOW,
    FAN_MEDIUM: VentilationMode.MEDIUM,
    FAN_HIGH: VentilationMode.HIGH,
    FAN_AUTO: VentilationMode.AUTO,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up devices."""

    helper: AmitApiHelper = hass.data[DOMAIN][entry.entry_id]

    ventilation_coordinator = helper.ventilation_coordinator
    api = helper.api

    await ventilation_coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            AmitHeatingClimateEntity(api, entry.entry_id),
            AmitVentilationClimateEntity(api, ventilation_coordinator, entry.entry_id),
        ]
    )


class AmitHeatingClimateEntity(ClimateEntity):
    """Amit Heating Climate entity. Used to control heating."""

    _enable_turn_on_off_backwards_compatibility = False
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF, HVACMode.AUTO]
    _attr_hvac_mode = HVACMode.OFF
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, api: AmitApi, entry_id: str) -> None:
        """Construct climate entity."""
        self.api = api
        self._attr_unique_id = f"{entry_id}-heating"

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            mode = HeatingMode.MINIMAL
        elif hvac_mode == HVACMode.AUTO:
            mode = HeatingMode.SCHEDULED
        else:
            mode = HeatingMode.COMFORT

        async with self.api.create_client() as client:
            await client.temperature_api.async_set_heading_mode(mode)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        new_temp = kwargs["temperature"]

        async with self.api.create_client() as client:
            if self.hvac_mode == HVACMode.OFF:
                await client.temperature_api.async_set_minimal_temperature(new_temp)
            else:
                await client.temperature_api.async_set_temperature(new_temp)

    async def async_turn_on(self) -> None:
        """Turn the entity on."""
        async with self.api.create_client() as client:
            await client.temperature_api.async_set_heading_mode(HeatingMode.COMFORT)

    async def async_turn_off(self) -> None:
        """Turn the entity off."""
        async with self.api.create_client() as client:
            await client.temperature_api.async_set_heading_mode(HeatingMode.MINIMAL)

    async def async_update(self) -> None:
        """Update state of entity."""
        heating_data = await self.api.async_get_heating_data()

        heating_mode = heating_data.heating_mode
        match heating_mode:
            case HeatingMode.SCHEDULED:
                self.hvac_mode = HVACMode.AUTO
            case HeatingMode.COMFORT:
                self.hvac_mode = HVACMode.HEAT
            case HeatingMode.MINIMAL:
                self.hvac_mode = HVACMode.OFF

        self._attr_current_temperature = heating_data.actual_temperature
        self._attr_target_temperature = heating_data.set_temperature

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, DEVICE_HEATING_ID)},
        )


class AmitVentilationClimateEntity(CoordinatorEntity, ClimateEntity):
    """Amit Ventilation climate entity. Used to control (heated) fan."""

    _enable_turn_on_off_backwards_compatibility = False
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_hvac_mode = HVACMode.OFF
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_has_entity_name = True
    _attr_fan_modes = [FAN_OFF, FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO]
    _attr_fan_mode = FAN_OFF
    _attr_hvac_action = None
    _attr_name = None

    def __init__(
        self, api: AmitApi, ventilation_coordinator: AmitFanCoordinator, entry_id: str
    ) -> None:
        """Construct climate entity."""
        super().__init__(ventilation_coordinator)
        self.api = api
        self._attr_unique_id = f"{entry_id}-ventilation"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        ventilation_data: VentilationResult = self.coordinator.data["ventilation_data"]
        overview_data: DataResult = self.coordinator.data["overview_data"]
        fan_map = {v: k for k, v in FAN_MODE_MAP.items()}

        self._attr_current_temperature = ventilation_data.air_temp_current
        self._attr_target_temperature = ventilation_data.air_temp_setpoint
        self._attr_fan_mode = fan_map[ventilation_data.ventilation_mode]
        self._attr_hvac_mode = (
            HVACMode.HEAT if overview_data.season == Season.WINTER else HVACMode.OFF
        )

        # if ventilation_data.is_heating:
        #     self._attr_hvac_action = HVACAction.HEATING
        # elif ventilation_data.ventilation_mode != VentilationMode.OFF:
        #     self._attr_hvac_action = HVACAction.FAN
        # else:
        #     self._attr_hvac_action = HVACAction.OFF

        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        target_season = Season.WINTER if hvac_mode == HVACMode.HEAT else Season.SUMMER

        async with self.api.create_client() as client:
            await client.temperature_api.async_set_season(target_season)
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        mode = FAN_MODE_MAP[fan_mode]

        async with self.api.create_client() as client:
            await client.ventilation_api.async_set_ventilation(mode)
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        new_temp = kwargs["temperature"]

        async with self.api.create_client() as client:
            await client.ventilation_api.async_set_target_air_temperature(new_temp)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Switch off."""
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_turn_on(self) -> None:
        """Switch on."""
        await self.async_set_hvac_mode(HVACMode.HEAT)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, DEVICE_VENTILATION_ID)},
        )
