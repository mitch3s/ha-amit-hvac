"""Amit API."""

from homeassistant.config_entries import ConfigEntry

from amit_hvac_control.client import AmitHvacControlClient
from amit_hvac_control.models import Config, VentilationMode


class AmitApi:
    """Amit API."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Construct the API."""
        host = entry.data["host"]
        username = entry.data["username"]
        password = entry.data["password"]
        self.config = Config(host, username, password)

    def create_client(self):
        """Create client."""
        return AmitHvacControlClient(self.config)

    async def async_set_ventilation(self, ventilation_mode: VentilationMode):
        """Set ventilation mode."""
        async with AmitHvacControlClient(self.config) as client:
            return await client.ventilation_api.async_set_ventilation(ventilation_mode)

    async def async_get_data(self):
        """Get data."""
        async with AmitHvacControlClient(self.config) as client:
            return await client.status_api.async_get_overview()

    async def async_get_heating_data(self):
        """Get heating data."""
        async with AmitHvacControlClient(self.config) as client:
            return await client.temperature_api.async_get_data()

    async def async_get_ventilation_data(self):
        """Get ventilation data."""
        async with AmitHvacControlClient(self.config) as client:
            return await client.ventilation_api.async_get_data()
