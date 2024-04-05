"""Platform for sensor integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from amit_hvac_control.api.ventilation import VentilationResult
from amit_hvac_control.models import VentilationMode

from .api import AmitApi
from .api_helper import AmitApiHelper
from .const import DEVICE_VENTILATION_ID, DOMAIN
from .coordinator import AmitFanCoordinator

ORDERED_NAMED_FAN_SPEEDS = [
    VentilationMode.LOW,
    VentilationMode.MEDIUM,
    VentilationMode.HIGH,
]

PRESET_AUTO = "Auto"


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up devices."""
    helper: AmitApiHelper = hass.data[DOMAIN][entry.entry_id]

    await helper.ventilation_coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            AmitVentilationFanEntity(
                helper.api, helper.ventilation_coordinator, entry.entry_id
            )
        ]
    )


class AmitVentilationFanEntity(CoordinatorEntity, FanEntity):
    """Fan entity."""

    mode = VentilationMode.OFF

    _attr_has_entity_name = True
    _attr_name = None
    _attr_preset_modes = [PRESET_AUTO]
    _attr_supported_features = FanEntityFeature.SET_SPEED | FanEntityFeature.PRESET_MODE
    _attr_is_on = False
    _attr_preset_mode = None

    def __init__(
        self, api: AmitApi, ventilation_coordinator: AmitFanCoordinator, entry_id: str
    ) -> None:
        """Construct climate entity."""
        super().__init__(ventilation_coordinator)
        self.api = api
        self._attr_unique_id = f"{entry_id}-fan"
        self._attr_available = False

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_available = True
        ventilation_data: VentilationResult = self.coordinator.data["ventilation_data"]
        self.mode = ventilation_data.ventilation_speed
        self._attr_is_on = self.mode != VentilationMode.OFF
        self._attr_preset_mode = (
            PRESET_AUTO
            if ventilation_data.ventilation_mode == VentilationMode.AUTO
            else None
        )
        self.async_write_ha_state()

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        if self.mode == VentilationMode.OFF:
            return 0
        return ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, self.mode)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(ORDERED_NAMED_FAN_SPEEDS)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        if percentage == 0:
            mode = VentilationMode.OFF
        else:
            mode = percentage_to_ordered_list_item(ORDERED_NAMED_FAN_SPEEDS, percentage)
        await self.async_set_mode(mode)

    async def async_set_mode(self, mode: VentilationMode):
        """Set ventilation mode."""
        self.mode = mode
        async with self.api.create_client() as client:
            await client.ventilation_api.async_set_ventilation(mode)
        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        if preset_mode == PRESET_AUTO:
            async with self.api.create_client() as client:
                await client.ventilation_api.async_set_ventilation(VentilationMode.AUTO)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the entity on."""
        if preset_mode == PRESET_AUTO:
            await self.async_set_preset_mode(preset_mode)
        elif percentage is not None:
            await self.async_set_percentage(percentage)
        else:
            await self.async_set_mode(VentilationMode.LOW)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        async with self.api.create_client() as client:
            await client.ventilation_api.async_set_ventilation(VentilationMode.OFF)
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, DEVICE_VENTILATION_ID)},
        )
