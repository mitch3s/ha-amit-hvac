"""API helper."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import AmitApi
from .coordinator import AmitFanCoordinator


class AmitApiHelper:
    """Amit API data helper class."""

    def __init__(self, hass: HomeAssistant, api: AmitApi, entry: ConfigEntry) -> None:
        """Construct Amit data helper object."""
        self.hass = hass
        self.api = api
        self.entry = entry
        self._ventilation_coordinator = None

    @property
    def ventilation_coordinator(self):
        """Get ventilation coordinator."""
        if self._ventilation_coordinator is None:
            self._ventilation_coordinator = AmitFanCoordinator(
                self.hass, self.api, self.entry
            )
        return self._ventilation_coordinator
