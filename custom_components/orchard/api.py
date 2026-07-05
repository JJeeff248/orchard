"""HTTP API for the Orchard panel."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol
from aiohttp import web
from homeassistant.components.http import KEY_HASS, HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .runtime import OrchardRuntime

PANEL_PATH = Path(__file__).parent / "frontend" / "orchard-panel.js"


def runtime_for(hass: HomeAssistant) -> OrchardRuntime:
    """Return the active runtime."""
    return hass.data[DOMAIN]["runtime"]


def async_register_api(hass: HomeAssistant) -> None:
    """Register panel APIs once."""
    if hass.data[DOMAIN].get("api_registered"):
        return
    hass.http.register_view(FrontendAssetView)
    hass.http.register_view(DashboardView)
    hass.http.register_view(AccessoryView)
    hass.http.register_view(ChangeView)
    hass.http.register_view(UnignoreView)
    hass.http.register_view(ReconcileView)
    hass.http.register_view(BridgeView)
    hass.data[DOMAIN]["api_registered"] = True


class FrontendAssetView(HomeAssistantView):
    """Serve the panel JavaScript."""

    url = f"/api/{DOMAIN}/frontend/orchard-panel.js"
    name = f"api:{DOMAIN}:frontend"
    requires_auth = False

    async def get(self, _request):
        """Return panel source."""
        return web.Response(
            text=PANEL_PATH.read_text(encoding="utf-8"),
            content_type="text/javascript",
        )


class DashboardView(HomeAssistantView):
    """Runtime dashboard endpoint."""

    url = f"/api/{DOMAIN}/dashboard"
    name = f"api:{DOMAIN}:dashboard"

    async def get(self, request):
        """Return current dashboard."""
        return self.json(runtime_for(request.app[KEY_HASS]).dashboard())


class AccessoryView(HomeAssistantView):
    """Accessory configuration endpoint."""

    url = f"/api/{DOMAIN}/accessory/{{entity_id}}"
    name = f"api:{DOMAIN}:accessory"

    async def post(self, request, entity_id: str):
        """Update accessory configuration."""
        hass = request.app[KEY_HASS]
        data = await request.json()
        schema = vol.Schema(
            {
                vol.Optional("name"): cv.string,
                vol.Optional("room"): vol.Any(cv.string, None),
                vol.Optional("category"): cv.string,
                vol.Optional("icon"): cv.string,
                vol.Optional("visible"): cv.boolean,
                vol.Optional("exposure"): vol.In(["hidden", "individual", "grouped", "both"]),
                vol.Optional("siri_name"): cv.string,
                vol.Optional("capabilities"): dict,
            }
        )
        await runtime_for(hass).async_update_accessory(entity_id, schema(data))
        return self.json(runtime_for(hass).dashboard())


class ChangeView(HomeAssistantView):
    """Review action endpoint."""

    url = f"/api/{DOMAIN}/change/{{entity_id}}/{{action}}"
    name = f"api:{DOMAIN}:change"

    async def post(self, request, entity_id: str, action: str):
        """Accept or ignore a review item."""
        runtime = runtime_for(request.app[KEY_HASS])
        if action == "accept":
            await runtime.async_accept_change(entity_id)
        elif action == "ignore":
            await runtime.async_ignore(entity_id)
        elif action == "propose":
            await runtime.async_propose_accessory(entity_id)
        else:
            return self.json_message("Unknown action", status_code=400)
        return self.json(runtime.dashboard())





class ReconcileView(HomeAssistantView):
    """Manual reconciliation endpoint."""

    url = f"/api/{DOMAIN}/reconcile"
    name = f"api:{DOMAIN}:reconcile"

    async def post(self, request):
        """Run reconciliation."""
        runtime = runtime_for(request.app[KEY_HASS])
        await runtime.async_reconcile()
        return self.json(runtime.dashboard())


class BridgeView(HomeAssistantView):
    """Apple Home bridge endpoint."""

    url = f"/api/{DOMAIN}/bridge/sync"
    name = f"api:{DOMAIN}:bridge_sync"

    async def post(self, request):
        """Create or update the Orchard-managed HomeKit bridge."""
        runtime = runtime_for(request.app[KEY_HASS])
        await runtime.async_sync_bridge()
        return self.json(runtime.dashboard())


class UnignoreView(HomeAssistantView):
    """Endpoint to unignore an entity."""

    url = f"/api/{DOMAIN}/ignored/{{entity_id}}/unignore"
    name = f"api:{DOMAIN}:ignored:unignore"

    async def post(self, request, entity_id: str):
        runtime = runtime_for(request.app[KEY_HASS])
        await runtime.async_unignore(entity_id)
        return self.json(runtime.dashboard())
