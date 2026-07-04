"""Apple-centric model building."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.light import ATTR_SUPPORTED_COLOR_MODES, ColorMode
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import entity_registry as er

SUPPORTED_DOMAINS = {"light", "scene"}


@dataclass(slots=True)
class AppleAccessory:
    """Internal Apple Home accessory representation."""

    id: str
    source_entity_id: str
    name: str
    room: str | None
    category: str
    icon: str
    visible: bool = True
    exposure: str = "individual"
    siri_name: str | None = None
    controls: list[str] = field(default_factory=list)
    capabilities: dict[str, Any] = field(default_factory=dict)
    state: str | None = None
    needs_attention: bool = False
    explanation: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        """Serialize accessory for storage and APIs."""
        return {
            "id": self.id,
            "source_entity_id": self.source_entity_id,
            "name": self.name,
            "room": self.room,
            "category": self.category,
            "icon": self.icon,
            "visible": self.visible,
            "exposure": self.exposure,
            "siri_name": self.siri_name or self.name,
            "controls": self.controls,
            "capabilities": self.capabilities,
            "state": self.state,
            "needs_attention": self.needs_attention,
            "explanation": self.explanation,
            "diagnostics": self.diagnostics,
        }


class AppleModelBuilder:
    """Build the runtime's Apple model from Home Assistant state."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    def build_accessory(self, state: State, custom: dict[str, Any] | None = None) -> AppleAccessory | None:
        """Build an Apple accessory from a Home Assistant state."""
        domain = state.domain
        if domain not in SUPPORTED_DOMAINS:
            return None

        custom = custom or {}
        if domain == "light":
            accessory = self._build_light(state)
        else:
            accessory = self._build_scene(state)

        merged = accessory.as_dict()
        merged.update({key: value for key, value in custom.items() if value is not None})
        return AppleAccessory(
            id=merged["id"],
            source_entity_id=merged["source_entity_id"],
            name=merged["name"],
            room=merged.get("room"),
            category=merged["category"],
            icon=merged["icon"],
            visible=merged.get("visible", True),
            exposure=merged.get("exposure", "individual"),
            siri_name=merged.get("siri_name"),
            controls=list(merged.get("controls", [])),
            capabilities=dict(merged.get("capabilities", {})),
            state=merged.get("state"),
            needs_attention=bool(merged.get("needs_attention", False)),
            explanation=dict(merged.get("explanation", {})),
            diagnostics=dict(merged.get("diagnostics", {})),
        )

    def _build_light(self, state: State) -> AppleAccessory:
        attrs = state.attributes
        color_modes = {
            getattr(mode, "value", mode)
            for mode in (attrs.get(ATTR_SUPPORTED_COLOR_MODES) or [])
        }
        features = int(attrs.get(ATTR_SUPPORTED_FEATURES) or 0)
        controls = ["Power"]
        capabilities: dict[str, Any] = {
            "on_off": True,
            "brightness": False,
            "rgb": False,
            "hsv": False,
            "color_temperature": False,
            "effects": False,
            "transitions": features > 0,
            "adaptive_lighting": False,
        }

        if ColorMode.BRIGHTNESS.value in color_modes or ColorMode.HS.value in color_modes or ColorMode.RGB.value in color_modes:
            controls.append("Brightness")
            capabilities["brightness"] = True
        if ColorMode.RGB.value in color_modes or ColorMode.RGBW.value in color_modes or ColorMode.RGBWW.value in color_modes:
            controls.append("RGB")
            capabilities["rgb"] = True
        if ColorMode.HS.value in color_modes:
            controls.append("HSV")
            capabilities["hsv"] = True
        if ColorMode.COLOR_TEMP.value in color_modes or ColorMode.RGBWW.value in color_modes:
            controls.append("Colour Temperature")
            capabilities["color_temperature"] = True
        if attrs.get("effect_list"):
            controls.append("Effects")
            capabilities["effects"] = True

        if state.state in {STATE_UNAVAILABLE, STATE_UNKNOWN}:
            needs_attention = True
        else:
            needs_attention = False

        return AppleAccessory(
            id=state.entity_id,
            source_entity_id=state.entity_id,
            name=self._display_name(state),
            room=self._area_name(state.entity_id),
            category="Light",
            icon="mdi:lightbulb",
            controls=controls,
            capabilities=capabilities,
            state=state.state,
            needs_attention=needs_attention,
            explanation={
                "mapped_as": "Apple Light",
                "reason": "The source accessory is a light and supports Apple Home light controls.",
                "supports": controls,
                "recommendation": "Apple Light",
            },
            diagnostics=self._diagnostics(state),
        )

    def _build_scene(self, state: State) -> AppleAccessory:
        return AppleAccessory(
            id=state.entity_id,
            source_entity_id=state.entity_id,
            name=self._display_name(state),
            room=self._area_name(state.entity_id),
            category="Scene",
            icon="mdi:palette",
            controls=["Activate"],
            capabilities={"activate": True},
            state=state.state,
            explanation={
                "mapped_as": "Apple Scene",
                "reason": "Home Assistant scenes map most naturally to Apple Home scenes.",
                "supports": ["Activate"],
                "recommendation": "Apple Scene",
            },
            diagnostics=self._diagnostics(state),
        )

    def _display_name(self, state: State) -> str:
        return str(state.attributes.get(ATTR_FRIENDLY_NAME) or state.object_id.replace("_", " ").title())

    def _area_name(self, entity_id: str) -> str | None:
        entity_registry = er.async_get(self.hass)
        entity_entry = entity_registry.async_get(entity_id)
        if entity_entry is None or entity_entry.area_id is None:
            return None
        area_registry = ar.async_get(self.hass)
        area = area_registry.async_get_area(entity_entry.area_id)
        return area.name if area else None

    def _diagnostics(self, state: State) -> dict[str, Any]:
        return {
            "entity_id": state.entity_id,
            "domain": state.domain,
            "attributes": dict(state.attributes),
        }
