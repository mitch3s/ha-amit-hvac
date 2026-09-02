"""Data Coordinator for Amit entities."""

from datetime import timedelta
import logging

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from amit_hvac_control.api.parsing import UnexpectedResponseException
from amit_hvac_control.client import AuthenticationException

from .api import AmitApi

_LOGGER = logging.getLogger(__name__)


class AmitSensorCoordinator(DataUpdateCoordinator):
    """Amit sensor coordinator."""

    def __init__(
        self, hass: HomeAssistant, amit_api: AmitApi, config_entry: ConfigEntry
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="sensor",
            update_interval=timedelta(seconds=30),
        )
        self.amit_api = amit_api

    async def _async_update_data(self):
        """Get data from API."""
        try:
            return await self.amit_api.async_get_data()
        except AuthenticationException as err:
            raise ConfigEntryAuthFailed(err) from err
        except (ClientError, TimeoutError, UnexpectedResponseException) as err:
            raise UpdateFailed(err) from err


class AmitFanCoordinator(DataUpdateCoordinator):
    """Amit fan coordinator."""

    def __init__(
        self, hass: HomeAssistant, amit_api: AmitApi, config_entry: ConfigEntry
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="ventilation",
            update_interval=timedelta(seconds=30),
        )
        self.amit_api = amit_api

    async def _async_update_data(self):
        """Get data from API."""
        try:
            _LOGGER.debug("Start loading ventilation data...")
            ventilation_data = await self.amit_api.async_get_ventilation_data()
            overview_data = await self.amit_api.async_get_data()
            _LOGGER.debug("Ventilation data loaded")
        except AuthenticationException as err:
            raise ConfigEntryAuthFailed(err) from err
        except (ClientError, TimeoutError, UnexpectedResponseException) as err:
            raise UpdateFailed(err) from err
        return {"ventilation_data": ventilation_data, "overview_data": overview_data}
