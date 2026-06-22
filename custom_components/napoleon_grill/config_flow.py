"""Config flow for Napoleon Grill integration."""
from __future__ import annotations

import logging
from typing import Any

from ayla_iot_unofficial import new_ayla_api, AylaAuthError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_APP_ID, CONF_APP_SECRET

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_APP_ID): str,
        vol.Required(CONF_APP_SECRET): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    api = new_ayla_api(
        data[CONF_EMAIL],
        data[CONF_PASSWORD],
        data[CONF_APP_ID],
        data[CONF_APP_SECRET],
    )

    await api.async_sign_in()
    devices = await api.async_get_devices()

    if not devices:
        raise ValueError("No devices found")

    return {"title": devices[0].name}


class NapoleonGrillConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Napoleon Grill."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except AylaAuthError:
                errors["base"] = "invalid_auth"
            except ValueError:
                errors["base"] = "no_devices"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )