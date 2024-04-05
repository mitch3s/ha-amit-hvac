"""Config flow for Amit HVAC integration."""

from __future__ import annotations

import logging
from typing import Any


import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, FlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from amit_hvac_control.client import AmitHvacControlClient
from amit_hvac_control.models import Config

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_input(_hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    host = data["host"]
    username = data["username"]
    password = data["password"]

    config = Config(host, username, password)
    async with AmitHvacControlClient(config) as client:
        if not await client.async_is_valid_auth():
            raise InvalidAuth

    # Return info that you want to store in the config entry.
    return {
        "title": "AMiT Hub",
        "host": host,
        "username": username,
        "password": password,
    }


class AmitHvacConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Amit HVAC."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
