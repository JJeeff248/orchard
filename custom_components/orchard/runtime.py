"""Runtime coordinator for Orchard."""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, EVENT_STATE_CHANGED
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.event import (
    async_track_time_interval,
)

from .const import DEFAULT_RECONCILE_INTERVAL_MINUTES, EVENT_RUNTIME_UPDATED
from .homekit_engine import OrchardHomeKitEngine
from .model import SUPPORTED_DOMAINS, AppleModelBuilder
from .storage import OrchardStorage


class OrchardRuntime:
    """Coordinate discovery, model building, sync health, and persistence."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.storage = OrchardStorage(hass)
        self.builder = AppleModelBuilder(hass)
        self.homekit = OrchardHomeKitEngine(hass)
        self._unsubscribers: list[Callable[[], None]] = []
        self.last_sync: str | None = None

    async def async_start(self) -> None:
        """Start runtime services."""
        await self.storage.async_load()
        await self.async_reconcile()

        interval = int(
            self.entry.data.get(
                "reconcile_interval",
                DEFAULT_RECONCILE_INTERVAL_MINUTES,
            )
        )
        self._unsubscribers.append(
            async_track_time_interval(
                self.hass,
                self._scheduled_reconcile,
                timedelta(minutes=interval),
            )
        )
        self._unsubscribers.append(self.hass.bus.async_listen(EVENT_STATE_CHANGED, self._state_changed))
        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, self._started)

    async def async_stop(self) -> None:
        """Stop runtime listeners."""
        while self._unsubscribers:
            self._unsubscribers.pop()()

    @callback
    def _started(self, _event: Event) -> None:
        self.hass.async_create_task(self.async_reconcile())

    @callback
    def _scheduled_reconcile(self, _now: Any) -> None:
        self.hass.async_create_task(self.async_reconcile())

    @callback
    def _state_changed(self, event: Event) -> None:
        entity_id = event.data["entity_id"]
        if entity_id.split(".", 1)[0] not in SUPPORTED_DOMAINS:
            return
        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None:
            self.hass.async_create_task(self.async_mark_removed(entity_id))
            return
        self.hass.async_create_task(self.async_sync_state(new_state, old_state))

    async def async_review_entity(self, entity_id: str) -> None:
        """Add a newly compatible entity to review."""
        if entity_id in self.storage.data.accessories or entity_id in self.storage.data.ignored:
            return
        state = self.hass.states.get(entity_id)
        if state is None:
            return
        accessory = self.builder.build_accessory(state)
        if accessory is None:
            return
        self.storage.data.changes[entity_id] = {
            "kind": "new_accessory",
            "message": f"{accessory.name} was detected.",
            "recommended": "Add",
            "accessory": accessory.as_dict(),
        }
        await self._save_and_signal()

    async def async_sync_state(self, new_state: State, old_state: State | None = None) -> None:
        """Synchronize an entity state into the Apple model."""
        existing = self.storage.data.accessories.get(new_state.entity_id)
        if existing is None:
            if self.entry.data.get("auto_discover", True):
                await self.async_review_entity(new_state.entity_id)
            return

        accessory = self.builder.build_accessory(new_state, existing)
        if accessory is None:
            await self.async_mark_removed(new_state.entity_id)
            return

        if old_state and self._capabilities_changed(old_state, new_state):
            self.storage.data.changes[new_state.entity_id] = {
                "kind": "capability_change",
                "message": f"{accessory.name} has changed capabilities.",
                "recommended": "Review mapping",
                "accessory": accessory.as_dict(),
            }

        self.storage.data.accessories[new_state.entity_id] = accessory.as_dict()
        await self._save_and_signal()

    async def async_reconcile(self) -> None:
        """Rebuild the model and repair missed events."""
        seen: set[str] = set()
        for state in self.hass.states.async_all():
            if state.domain not in SUPPORTED_DOMAINS:
                continue
            seen.add(state.entity_id)
            if state.entity_id in self.storage.data.ignored:
                continue
            if state.entity_id in self.storage.data.accessories:
                accessory = self.builder.build_accessory(
                    state,
                    self.storage.data.accessories[state.entity_id],
                )
                if accessory is not None:
                    self.storage.data.accessories[state.entity_id] = accessory.as_dict()
            elif self.entry.data.get("auto_discover", True):
                await self.async_review_entity(state.entity_id)

        for entity_id in list(self.storage.data.accessories):
            if entity_id not in seen:
                await self.async_mark_removed(entity_id, save=False)

        from homeassistant.util import dt as dt_util

        self.last_sync = dt_util.utcnow().isoformat()
        await self._save_and_signal()

    async def async_accept_change(self, entity_id: str) -> None:
        """Accept a pending review item."""
        change = self.storage.data.changes.pop(entity_id, None)
        if not change:
            return
        accessory = change.get("accessory")
        if accessory:
            self.storage.data.accessories[entity_id] = accessory
            self.storage.data.ignored.pop(entity_id, None)
            await self.async_sync_bridge(save=False)
        await self._save_and_signal()

    async def async_ignore(self, entity_id: str) -> None:
        """Ignore an accessory until manually reviewed."""
        self.storage.data.changes.pop(entity_id, None)
        self.storage.data.accessories.pop(entity_id, None)
        self.storage.data.ignored[entity_id] = {
            "entity_id": entity_id,
            "reason": "Ignored by user",
        }
        await self.async_sync_bridge(save=False)
        await self._save_and_signal()

    async def async_unignore(self, entity_id: str) -> None:
        """Remove an entity from the ignored list and queue it for review."""
        self.storage.data.ignored.pop(entity_id, None)
        # Re-add to review so it shows up in the panel
        await self.async_review_entity(entity_id)
        await self._save_and_signal()

    async def async_update_accessory(self, entity_id: str, updates: dict[str, Any]) -> None:
        """Update user-facing accessory configuration."""
        accessory = self.storage.data.accessories.get(entity_id)
        if accessory is None:
            change = self.storage.data.changes.get(entity_id)
            accessory = dict(change.get("accessory", {})) if change else {}
        if not accessory:
            return

        allowed = {
            "name",
            "room",
            "category",
            "icon",
            "visible",
            "exposure",
            "siri_name",
            "capabilities",
        }
        for key in allowed:
            if key in updates:
                accessory[key] = updates[key]
        self.storage.data.accessories[entity_id] = accessory
        self.storage.data.changes.pop(entity_id, None)
        await self.async_sync_bridge(save=False)
        await self._save_and_signal()

    async def async_sync_bridge(self, save: bool = True) -> dict[str, Any]:
        """Synchronize accepted accessories to the Orchard-managed Apple Home bridge."""
        result = await self.homekit.async_sync(list(self.storage.data.accessories.values()))
        self.storage.data.settings["homekit_bridge"] = result
        if save:
            await self._save_and_signal()
        return result

    async def async_mark_removed(self, entity_id: str, save: bool = True) -> None:
        """Mark a removed entity as needing review."""
        accessory = self.storage.data.accessories.get(entity_id)
        if accessory:
            self.storage.data.changes[entity_id] = {
                "kind": "removed",
                "message": f"{accessory['name']} is no longer available.",
                "recommended": "Remove accessory",
                "accessory": {**accessory, "needs_attention": True},
            }
        if save:
            await self._save_and_signal()

    def dashboard(self) -> dict[str, Any]:
        """Return health dashboard state."""
        accessories = list(self.storage.data.accessories.values())
        awaiting = list(self.storage.data.changes.values())

        # Enrich ignored items with friendly name and area where possible
        ignored: list[dict[str, Any]] = []
        for ent_id, info in self.storage.data.ignored.items():
            name = None
            room = None
            state = self.hass.states.get(ent_id)
            if state is not None:
                name = str(
                    state.attributes.get("friendly_name")
                    or state.object_id.replace("_", " ").title()
                )
            # try to get area from entity registry
            try:
                from homeassistant.helpers import entity_registry as er

                entity_registry = er.async_get(self.hass)
                entry = entity_registry.async_get(ent_id)
                if entry and entry.area_id:
                    from homeassistant.helpers import area_registry as ar

                    area_registry = ar.async_get(self.hass)
                    area = area_registry.async_get_area(entry.area_id)
                    room = area.name if area else None
            except Exception:
                room = None

            ignored.append(
                {
                    "entity_id": ent_id,
                    "source_entity_id": ent_id,
                    "name": name or ent_id,
                    "room": room,
                    "reason": info.get("reason"),
                }
            )

        needs_attention = [a for a in accessories if a.get("needs_attention")]
        homekit_status = self.homekit.status()
        return {
            "status": "Connected",
            "accessory_count": len(accessories),
            "synced_count": len([a for a in accessories if not a.get("needs_attention")]),
            "awaiting_review_count": len(awaiting),
            "ignored_count": len(ignored),
            "needs_attention_count": len(needs_attention),
            "last_sync": self.last_sync,
            "accessories": accessories,
            "changes": awaiting,
            "ignored": ignored,
            "homekit_bridge": self.storage.data.settings.get(
                "homekit_bridge", homekit_status
            ),
        }

    def _capabilities_changed(self, old_state: State, new_state: State) -> bool:
        return old_state.attributes.get("supported_color_modes") != new_state.attributes.get(
            "supported_color_modes"
        )

    async def _save_and_signal(self) -> None:
        await self.storage.async_save()
        self.hass.bus.async_fire(EVENT_RUNTIME_UPDATED, self.dashboard())
