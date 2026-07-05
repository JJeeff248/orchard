"""Services for Orchard."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .runtime import OrchardRuntime


def _runtime(hass: HomeAssistant) -> OrchardRuntime:
    return hass.data[DOMAIN]["runtime"]


def async_register_services(hass: HomeAssistant) -> None:
    """Register integration services."""
    if hass.data[DOMAIN].get("services_registered"):
        return

    async def reconcile(_call: ServiceCall) -> None:
        await _runtime(hass).async_reconcile()

    async def accept_change(call: ServiceCall) -> None:
        await _runtime(hass).async_accept_change(call.data["entity_id"])

    async def ignore(call: ServiceCall) -> None:
        await _runtime(hass).async_ignore(call.data["entity_id"])

    async def unignore(call: ServiceCall) -> None:
        await _runtime(hass).async_unignore(call.data["entity_id"])

    async def propose_accessory(call: ServiceCall) -> None:
        await _runtime(hass).async_propose_accessory(call.data["entity_id"])

    async def sync_bridge(_call: ServiceCall) -> None:
        await _runtime(hass).async_sync_bridge()

    hass.services.async_register(DOMAIN, "reconcile", reconcile)
    hass.services.async_register(DOMAIN, "sync_bridge", sync_bridge)
    hass.services.async_register(
        DOMAIN,
        "accept_change",
        accept_change,
        schema=vol.Schema({vol.Required("entity_id"): cv.entity_id}),
    )
    hass.services.async_register(
        DOMAIN,
        "ignore",
        ignore,
        schema=vol.Schema({vol.Required("entity_id"): cv.entity_id}),
    )
    hass.services.async_register(
        DOMAIN,
        "unignore",
        unignore,
        schema=vol.Schema({vol.Required("entity_id"): cv.entity_id}),
    )
    hass.services.async_register(
        DOMAIN,
        "propose_accessory",
        propose_accessory,
        schema=vol.Schema({vol.Required("entity_id"): cv.entity_id}),
    )
    hass.data[DOMAIN]["services_registered"] = True
