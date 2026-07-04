"""Orchard integration."""

from __future__ import annotations

from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .api import async_register_api
from .const import DOMAIN, PANEL_ICON, PANEL_TITLE, PANEL_URL
from .runtime import OrchardRuntime
from .services import async_register_services

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Set up integration services."""
    hass.data.setdefault(DOMAIN, {})
    async_register_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Orchard from a config entry."""
    runtime = OrchardRuntime(hass, entry)
    await runtime.async_start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime
    hass.data[DOMAIN]["runtime"] = runtime

    async_register_api(hass)
    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        frontend_url_path=PANEL_URL.strip("/"),
        config={
            "_panel_custom": {
                "name": "orchard-panel",
                "js_url": f"/api/{DOMAIN}/frontend/orchard-panel.js",
            }
        },
        require_admin=True,
        update=True,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Orchard."""
    runtime: OrchardRuntime | None = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if runtime is not None:
        await runtime.async_stop()
    if hass.data.get(DOMAIN, {}).get("runtime") is runtime:
        hass.data[DOMAIN].pop("runtime", None)
    frontend.async_remove_panel(hass, PANEL_URL.strip("/"), warn_if_unknown=False)
    return True
