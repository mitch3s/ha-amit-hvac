"""The Amit HVAC integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers import device_registry as dr

from .api import AmitApi
from .api_helper import AmitApiHelper
from .const import (
    DEVICE_HEATING_ID,
    DEVICE_HEATING_NAME,
    DEVICE_VENTILATION_ID,
    DEVICE_VENTILATION_NAME,
    DOMAIN,
    MANUFACTURER,
    PLC_ID,
    PLC_MODEL,
    PLC_NAME,
)

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.FAN,
    Platform.NUMBER,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Amit HVAC from a config entry."""

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, PLC_ID)},
        manufacturer=MANUFACTURER,
        name=PLC_NAME,
        model=PLC_MODEL,
    )
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, DEVICE_HEATING_ID)},
        name=DEVICE_HEATING_NAME,
        manufacturer=MANUFACTURER,
        via_device=(DOMAIN, PLC_ID),
        entry_type=DeviceEntryType.SERVICE,
    )
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, DEVICE_VENTILATION_ID)},
        name=DEVICE_VENTILATION_NAME,
        manufacturer=MANUFACTURER,
        via_device=(DOMAIN, PLC_ID),
        entry_type=DeviceEntryType.SERVICE,
    )

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = AmitApiHelper(hass, AmitApi(entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
