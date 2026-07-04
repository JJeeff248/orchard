"""Config flow for Orchard."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    DEFAULT_RECONCILE_INTERVAL_MINUTES,
    DOMAIN,
    NAME,
)


class OrchardConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle an Orchard config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Create the runtime entry."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    "reconcile_interval": user_input["reconcile_interval"],
                    "auto_discover": user_input["auto_discover"],
                },
            )

        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default=NAME): str,
                vol.Optional(
                    "reconcile_interval",
                    default=DEFAULT_RECONCILE_INTERVAL_MINUTES,
                ): vol.All(int, vol.Range(min=1, max=60)),
                vol.Optional("auto_discover", default=True): bool,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

