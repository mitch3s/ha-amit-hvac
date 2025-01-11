"""Data Coordinator for Amit entities."""

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import AmitApi

_LOGGER = logging.getLogger(__name__)


class AmitSensorCoordinator(DataUpdateCoordinator):
    """Amit sensor coordinator."""

    def __init__(self, hass: HomeAssistant, amit_api: AmitApi) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="sensor",
            update_interval=timedelta(seconds=30),
        )
        self.amit_api = amit_api

    async def _async_update_data(self):
        """Get data from API."""
        return await self.amit_api.async_get_data()


class AmitFanCoordinator(DataUpdateCoordinator):
    """Amit fan coordinator."""

    def __init__(self, hass: HomeAssistant, amit_api: AmitApi) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="ventilation",
            update_interval=timedelta(seconds=30),
        )
        self.amit_api = amit_api

    async def _async_update_data(self):
        """Get data from API."""
        _LOGGER.debug("Start loading ventilation data...")
        ventilation_data = await self.amit_api.async_get_ventilation_data()
        overview_data = await self.amit_api.async_get_data()
        _LOGGER.debug("Ventilation data loaded")
        return {"ventilation_data": ventilation_data, "overview_data": overview_data}
