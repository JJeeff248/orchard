"""Apple-centric model building."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.light import (
    ATTR_EFFECT_LIST,
    ATTR_SUPPORTED_COLOR_MODES,
    LightEntityFeature,
    brightness_supported,
    color_supported,
    color_temp_supported,
)
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import entity_registry as er

SUPPORTED_DOMAINS = {"light", "scene", "switch", "sensor", "binary_sensor", "cover", "climate", "lock", "media_player", "vacuum"}


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
        elif domain == "scene":
            accessory = self._build_scene(state)
        elif domain == "switch":
            accessory = self._build_switch(state)
        elif domain == "sensor":
            accessory = self._build_sensor(state)
        elif domain == "binary_sensor":
            accessory = self._build_binary_sensor(state)
        elif domain == "cover":
            accessory = self._build_cover(state)
        elif domain == "climate":
            accessory = self._build_climate(state)
        elif domain == "lock":
            accessory = self._build_lock(state)
        elif domain == "media_player":
            accessory = self._build_media_player(state)
        elif domain == "vacuum":
            accessory = self._build_vacuum(state)
        else:
            accessory = None

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
        color_modes = attrs.get(ATTR_SUPPORTED_COLOR_MODES) or set()
        features = int(attrs.get(ATTR_SUPPORTED_FEATURES) or 0)
        controls = ["Power"]
        capabilities: dict[str, Any] = {
            "on_off": True,
            "brightness": False,
            "rgb": False,
            "hsv": False,
            "color_temperature": False,
            "effects": False,
            "transitions": bool(features & LightEntityFeature.TRANSITION),
            "adaptive_lighting": False,
        }

        if brightness_supported(color_modes):
            controls.append("Brightness")
            capabilities["brightness"] = True
        if color_supported(color_modes):
            controls.append("RGB")
            capabilities["rgb"] = True
        if "hs" in color_modes:
            controls.append("HSV")
            capabilities["hsv"] = True
        if color_temp_supported(color_modes):
            controls.append("Colour Temperature")
            capabilities["color_temperature"] = True
        if attrs.get(ATTR_EFFECT_LIST):
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

    def _build_switch(self, state: State) -> AppleAccessory:
        attrs = state.attributes
        controls = ["Power"]
        capabilities = {"on_off": True}

        if state.state in {STATE_UNAVAILABLE, STATE_UNKNOWN}:
            needs_attention = True
        else:
            needs_attention = False

        return AppleAccessory(
            id=state.entity_id,
            source_entity_id=state.entity_id,
            name=self._display_name(state),
            room=self._area_name(state.entity_id),
            category="Switch",
            icon="mdi:toggle-switch",
            controls=controls,
            capabilities=capabilities,
            state=state.state,
            needs_attention=needs_attention,
            explanation={
                "mapped_as": "Apple Switch",
                "reason": "Home Assistant switches map to simple on/off accessories.",
                "supports": controls,
                "recommendation": "Apple Switch",
            },
            diagnostics=self._diagnostics(state),
        )

    def _build_sensor(self, state: State) -> AppleAccessory:
        return AppleAccessory(
            id=state.entity_id,
            source_entity_id=state.entity_id,
            name=self._display_name(state),
            room=self._area_name(state.entity_id),
            category="Sensor",
            icon="mdi:gauge",
            controls=["Value"],
            capabilities={"sensor": True},
            state=state.state,
            explanation={
                "mapped_as": "Apple Sensor",
                "reason": "Sensors report values and map to read-only accessories.",
                "supports": ["Value"],
                "recommendation": "Apple Sensor",
            },
            diagnostics=self._diagnostics(state),
        )

    def _build_binary_sensor(self, state: State) -> AppleAccessory:
        return AppleAccessory(
            id=state.entity_id,
            source_entity_id=state.entity_id,
            name=self._display_name(state),
            room=self._area_name(state.entity_id),
            category="BinarySensor",
            icon="mdi:checkbox-marked-circle-outline",
            controls=["State"],
            capabilities={"binary_sensor": True},
            state=state.state,
            explanation={
                "mapped_as": "Apple Binary Sensor",
                "reason": "Binary sensors expose boolean states.",
                "supports": ["State"],
                "recommendation": "Apple Binary Sensor",
            },
            diagnostics=self._diagnostics(state),
        )

    def _build_cover(self, state: State) -> AppleAccessory:
        controls = ["Open", "Close", "Stop"]
        capabilities = {"open_close": True, "stop": True}
        return AppleAccessory(
            id=state.entity_id,
            source_entity_id=state.entity_id,
            name=self._display_name(state),
            room=self._area_name(state.entity_id),
            category="Cover",
            icon="mdi:window-open-variant",
            controls=controls,
            capabilities=capabilities,
            state=state.state,
            explanation={
                "mapped_as": "Apple Cover",
                "reason": "Covers can be opened/closed and stopped.",
                "supports": controls,
                "recommendation": "Apple Cover",
            },
            diagnostics=self._diagnostics(state),
        )

    def _build_climate(self, state: State) -> AppleAccessory:
        controls = ["Temperature", "Mode"]
        capabilities = {"temperature": True, "modes": True}
        return AppleAccessory(
            id=state.entity_id,
            source_entity_id=state.entity_id,
            name=self._display_name(state),
            room=self._area_name(state.entity_id),
            category="Thermostat",
            icon="mdi:thermostat",
            controls=controls,
            capabilities=capabilities,
            state=state.state,
            explanation={
                "mapped_as": "Apple Thermostat",
                "reason": "Climate entities provide temperature control and modes.",
                "supports": controls,
                "recommendation": "Apple Thermostat",
            },
            diagnostics=self._diagnostics(state),
        )

    def _build_lock(self, state: State) -> AppleAccessory:
        controls = ["Lock", "Unlock"]
        capabilities = {"lock": True}
        return AppleAccessory(
            id=state.entity_id,
            source_entity_id=state.entity_id,
            name=self._display_name(state),
            room=self._area_name(state.entity_id),
            category="Lock",
            icon="mdi:lock",
            controls=controls,
            capabilities=capabilities,
            state=state.state,
            explanation={
                "mapped_as": "Apple Lock",
                "reason": "Locks expose lock/unlock controls.",
                "supports": controls,
                "recommendation": "Apple Lock",
            },
            diagnostics=self._diagnostics(state),
        )

    def _build_media_player(self, state: State) -> AppleAccessory:
        controls = ["Play", "Pause", "Stop", "Next", "Previous", "Volume"]
        capabilities = {"media_control": True, "volume": True}
        return AppleAccessory(
            id=state.entity_id,
            source_entity_id=state.entity_id,
            name=self._display_name(state),
            room=self._area_name(state.entity_id),
            category="MediaPlayer",
            icon="mdi:cast",
            controls=controls,
            capabilities=capabilities,
            state=state.state,
            explanation={
                "mapped_as": "Apple Media Player",
                "reason": "Media players support play/pause/track controls.",
                "supports": controls,
                "recommendation": "Apple Media Player",
            },
            diagnostics=self._diagnostics(state),
        )

    def _build_vacuum(self, state: State) -> AppleAccessory:
        controls = ["Start", "Stop", "Dock"]
        capabilities = {"vacuum": True}
        return AppleAccessory(
            id=state.entity_id,
            source_entity_id=state.entity_id,
            name=self._display_name(state),
            room=self._area_name(state.entity_id),
            category="Vacuum",
            icon="mdi:robot-vacuum",
            controls=controls,
            capabilities=capabilities,
            state=state.state,
            explanation={
                "mapped_as": "Apple Vacuum",
                "reason": "Vacuums support start/stop/dock commands.",
                "supports": controls,
                "recommendation": "Apple Vacuum",
            },
            diagnostics=self._diagnostics(state),
        )
