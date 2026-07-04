"""Versioned storage for Orchard."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION


@dataclass(slots=True)
class RuntimeStore:
    """Persisted runtime configuration and review state."""

    accessories: dict[str, dict[str, Any]] = field(default_factory=dict)
    ignored: dict[str, dict[str, Any]] = field(default_factory=dict)
    changes: dict[str, dict[str, Any]] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RuntimeStore:
        """Create a runtime store from raw data."""
        if not data:
            return cls()
        return cls(
            accessories=dict(data.get("accessories", {})),
            ignored=dict(data.get("ignored", {})),
            changes=dict(data.get("changes", {})),
            settings=dict(data.get("settings", {})),
        )

    def as_dict(self) -> dict[str, Any]:
        """Serialize the runtime store."""
        return {
            "accessories": self.accessories,
            "ignored": self.ignored,
            "changes": self.changes,
            "settings": self.settings,
        }


class OrchardStorage:
    """Storage adapter around Home Assistant .storage."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data = RuntimeStore()

    async def async_load(self) -> RuntimeStore:
        """Load stored data."""
        self.data = RuntimeStore.from_dict(await self._store.async_load())
        return self.data

    async def async_save(self) -> None:
        """Persist current data."""
        await self._store.async_save(self.data.as_dict())

