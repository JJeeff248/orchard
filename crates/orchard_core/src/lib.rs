//! Orchard core model and mapping logic.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum RuntimeError {
    #[error("unsupported domain: {0}")]
    UnsupportedDomain(String),
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceEntity {
    pub entity_id: String,
    pub domain: String,
    pub name: String,
    pub room: Option<String>,
    pub state: Option<String>,
    pub attributes: BTreeMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AppleAccessory {
    pub id: String,
    pub source_entity_id: String,
    pub name: String,
    pub room: Option<String>,
    pub category: AccessoryCategory,
    pub icon: String,
    pub visible: bool,
    pub exposure: Exposure,
    pub siri_name: String,
    pub controls: Vec<String>,
    pub capabilities: BTreeMap<String, bool>,
    pub state: Option<String>,
    pub needs_attention: bool,
    pub explanation: Explanation,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum AccessoryCategory {
    Light,
    Scene,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Exposure {
    Hidden,
    Individual,
    Grouped,
    Both,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Explanation {
    pub mapped_as: String,
    pub reason: String,
    pub supports: Vec<String>,
    pub recommendation: String,
}

pub fn map_entity(entity: &SourceEntity) -> Result<AppleAccessory, RuntimeError> {
    match entity.domain.as_str() {
        "light" => Ok(map_light(entity)),
        "scene" => Ok(map_scene(entity)),
        other => Err(RuntimeError::UnsupportedDomain(other.to_owned())),
    }
}

fn map_light(entity: &SourceEntity) -> AppleAccessory {
    let modes = entity
        .attributes
        .get("supported_color_modes")
        .and_then(|value| value.as_array())
        .map(|items| {
            items
                .iter()
                .filter_map(|item| item.as_str())
                .map(str::to_owned)
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();

    let mut controls = vec!["Power".to_owned()];
    let mut capabilities = BTreeMap::from([
        ("on_off".to_owned(), true),
        ("brightness".to_owned(), false),
        ("rgb".to_owned(), false),
        ("hsv".to_owned(), false),
        ("color_temperature".to_owned(), false),
        ("effects".to_owned(), false),
        ("transitions".to_owned(), false),
        ("adaptive_lighting".to_owned(), false),
    ]);

    if modes.iter().any(|mode| matches!(mode.as_str(), "brightness" | "hs" | "rgb" | "rgbw" | "rgbww")) {
        controls.push("Brightness".to_owned());
        capabilities.insert("brightness".to_owned(), true);
    }
    if modes.iter().any(|mode| matches!(mode.as_str(), "rgb" | "rgbw" | "rgbww")) {
        controls.push("RGB".to_owned());
        capabilities.insert("rgb".to_owned(), true);
    }
    if modes.iter().any(|mode| mode == "hs") {
        controls.push("HSV".to_owned());
        capabilities.insert("hsv".to_owned(), true);
    }
    if modes.iter().any(|mode| matches!(mode.as_str(), "color_temp" | "rgbww")) {
        controls.push("Colour Temperature".to_owned());
        capabilities.insert("color_temperature".to_owned(), true);
    }
    if entity.attributes.get("effect_list").is_some() {
        controls.push("Effects".to_owned());
        capabilities.insert("effects".to_owned(), true);
    }

    AppleAccessory {
        id: entity.entity_id.clone(),
        source_entity_id: entity.entity_id.clone(),
        name: entity.name.clone(),
        room: entity.room.clone(),
        category: AccessoryCategory::Light,
        icon: "mdi:lightbulb".to_owned(),
        visible: true,
        exposure: Exposure::Individual,
        siri_name: entity.name.clone(),
        state: entity.state.clone(),
        needs_attention: matches!(entity.state.as_deref(), Some("unavailable" | "unknown")),
        explanation: Explanation {
            mapped_as: "Apple Light".to_owned(),
            reason: "The source accessory is a light and supports Apple Home light controls.".to_owned(),
            supports: controls.clone(),
            recommendation: "Apple Light".to_owned(),
        },
        controls,
        capabilities,
    }
}

fn map_scene(entity: &SourceEntity) -> AppleAccessory {
    AppleAccessory {
        id: entity.entity_id.clone(),
        source_entity_id: entity.entity_id.clone(),
        name: entity.name.clone(),
        room: entity.room.clone(),
        category: AccessoryCategory::Scene,
        icon: "mdi:palette".to_owned(),
        visible: true,
        exposure: Exposure::Individual,
        siri_name: entity.name.clone(),
        controls: vec!["Activate".to_owned()],
        capabilities: BTreeMap::from([("activate".to_owned(), true)]),
        state: entity.state.clone(),
        needs_attention: false,
        explanation: Explanation {
            mapped_as: "Apple Scene".to_owned(),
            reason: "Home Assistant scenes map most naturally to Apple Home scenes.".to_owned(),
            supports: vec!["Activate".to_owned()],
            recommendation: "Apple Scene".to_owned(),
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pretty_assertions::assert_eq;
    use serde_json::json;

    #[test]
    fn maps_rgb_light_to_apple_light() {
        let entity = SourceEntity {
            entity_id: "light.kitchen_pendant".to_owned(),
            domain: "light".to_owned(),
            name: "Kitchen Pendant".to_owned(),
            room: Some("Kitchen".to_owned()),
            state: Some("on".to_owned()),
            attributes: BTreeMap::from([(
                "supported_color_modes".to_owned(),
                json!(["brightness", "rgb", "color_temp"]),
            )]),
        };

        let accessory = map_entity(&entity).unwrap();

        assert_eq!(accessory.category, AccessoryCategory::Light);
        assert_eq!(accessory.controls, vec!["Power", "Brightness", "RGB", "Colour Temperature"]);
        assert_eq!(accessory.capabilities["rgb"], true);
    }

    #[test]
    fn rejects_unsupported_domains() {
        let entity = SourceEntity {
            entity_id: "sensor.temperature".to_owned(),
            domain: "sensor".to_owned(),
            name: "Temperature".to_owned(),
            room: None,
            state: Some("20".to_owned()),
            attributes: BTreeMap::new(),
        };

        assert_eq!(
            map_entity(&entity).unwrap_err(),
            RuntimeError::UnsupportedDomain("sensor".to_owned())
        );
    }
}

