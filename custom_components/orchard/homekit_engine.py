"""Orchard-managed Apple Home bridge."""

from __future__ import annotations

import socket
from typing import Any

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant

HOMEKIT_DOMAIN = "homekit"
ORCHARD_BRIDGE_NAME = "Orchard Bridge"
ORCHARD_BRIDGE_PORT = 21100


class OrchardHomeKitEngine:
    """Manage the HomeKit protocol bridge from Orchard's Apple model."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def async_sync(self, accessories: list[dict[str, Any]]) -> dict[str, Any]:
        """Create or update the Orchard-owned HomeKit bridge."""
        entity_ids = sorted(
            accessory["source_entity_id"]
            for accessory in accessories
            if accessory.get("visible", True) and accessory.get("exposure") != "hidden"
        )

        entry = self._entry()
        if entry is None:
            port = await self._available_port(ORCHARD_BRIDGE_PORT)
            result = await self.hass.config_entries.flow.async_init(
                HOMEKIT_DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=self._entry_data(port, entity_ids),
            )
            return {
                "managed": True,
                "created": result.get("type") == "create_entry",
                "status": result.get("type"),
                "entity_count": len(entity_ids),
                "entities": entity_ids,
            }

        data = dict(entry.data)
        options = dict(entry.options)
        options["filter"] = self._filter(entity_ids)
        options["mode"] = "bridge"
        options["entity_config"] = self._entity_config(accessories)
        self.hass.config_entries.async_update_entry(entry, data=data, options=options)
        await self.hass.config_entries.async_reload(entry.entry_id)
        return self.status(entity_ids)

    def status(self, entity_ids: list[str] | None = None) -> dict[str, Any]:
        """Return Orchard bridge status."""
        entry = self._entry()
        if entry is None:
            return {
                "managed": False,
                "status": "Not Created",
                "entry_id": None,
                "entity_count": 0,
                "entities": [],
            }

        options = entry.options if entry.options else entry.data
        current_entities = entity_ids or options.get("filter", {}).get("include_entities", [])
        runtime_data = getattr(entry, "runtime_data", None)
        homekit = getattr(runtime_data, "homekit", None)
        driver = getattr(homekit, "driver", None)
        driver_state = getattr(driver, "state", None)
        paired = bool(getattr(driver_state, "paired", False))
        pairing_secret = getattr(runtime_data, "pairing_qr_secret", None)

        return {
            "managed": True,
            "status": getattr(entry, "state", "Created").name
            if hasattr(getattr(entry, "state", None), "name")
            else str(getattr(entry, "state", "Created")),
            "entry_id": entry.entry_id,
            "title": entry.title,
            "paired": paired,
            "pin_code": None if paired else getattr(driver_state, "pincode", None),
            "pairing_qr_url": None
            if paired or not pairing_secret
            else f"/api/homekit/pairingqr?{entry.entry_id}-{pairing_secret}",
            "entity_count": len(current_entities),
            "entities": current_entities,
        }

    def _entry(self) -> ConfigEntry | None:
        for entry in self.hass.config_entries.async_entries(HOMEKIT_DOMAIN):
            if entry.data.get("orchard_managed") or entry.data.get(CONF_NAME) == ORCHARD_BRIDGE_NAME:
                return entry
        return None

    def _entry_data(self, port: int, entity_ids: list[str]) -> dict[str, Any]:
        return {
            CONF_NAME: ORCHARD_BRIDGE_NAME,
            CONF_PORT: port,
            "orchard_managed": True,
            "mode": "bridge",
            "exclude_accessory_mode": True,
            "filter": self._filter(entity_ids),
            "entity_config": {},
        }

    def _filter(self, entity_ids: list[str]) -> dict[str, list[str]]:
        return {
            "include_domains": [],
            "include_entities": entity_ids,
            "exclude_domains": [],
            "exclude_entities": [],
        }

    def _entity_config(self, accessories: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        config: dict[str, dict[str, Any]] = {}
        for accessory in accessories:
            entity_id = accessory["source_entity_id"]
            config[entity_id] = {"name": accessory.get("name") or entity_id}
        return config

    async def _available_port(self, preferred: int) -> int:
        port = preferred
        while not await self.hass.async_add_executor_job(self._port_available, port):
            port += 1
        return port

    def _port_available(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("", port))
            except OSError:
                return False
            return True
