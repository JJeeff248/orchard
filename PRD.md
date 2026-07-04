# Orchard

The Apple Home experience Home Assistant deserves.

## Product Requirements Document (PRD)

**Version:** 1.0
**Status:** Draft – Discovery Complete
**Owner:** Chris
**Target Platform:** Home Assistant (HACS Custom Integration)

---

# 1. Executive Summary

Apple Home is one of the best smart home interfaces available.

Home Assistant is one of the best smart home automation platforms available.

Unfortunately, the bridge between them feels like exactly that—a bridge. Entities are translated rather than thoughtfully presented, resulting in switches masquerading as scenes, inconsistent grouping, and an overall experience that doesn't feel native.

Orchard aims to solve this.

Rather than exposing Home Assistant directly to Apple Home, Orchard builds an internal Apple-centric representation of the home and presents it in the most natural, polished and reliable way possible.

The objective is not feature parity.

The objective is **Apple-quality experience**.

---

# 2. Vision

> Build the Apple Home integration that Home Assistant should have shipped.

The runtime should disappear into the background.

Users should eventually forget it exists because everything simply works.

---

# 3. Mission

> Home Assistant is the brain.

> Apple Home is the interface.

> Orchard ensures the interface feels like they were designed together.

---

# 4. Product Goals

## Primary Goals

* Apple-native experience
* Reliable enough to trust indefinitely
* Beautiful configuration
* Opinionated defaults
* Deep customization
* Excellent performance
* Long-term maintainability

---

## Secondary Goals

* Excellent diagnostics
* Clear explanations
* Easy onboarding
* Minimal maintenance

---

# 5. Non Goals

Version 1 will NOT include:

* Matter
* Google Home
* Alexa
* SmartThings
* HomeKit Controller replacement
* Home Assistant automation replacement

Home Assistant remains the automation engine.

---

# 6. Design Principles

## Apple First

Every engineering decision should ask:

> "How would Apple want this represented?"

rather than

> "How do we expose another Home Assistant entity?"

---

## Home Assistant is Source of Truth

Home Assistant owns:

* Devices
* Entities
* States
* Areas
* Automations
* Scripts
* Registries

Orchard owns:

* Presentation
* Mapping
* Synchronization
* Configuration
* UX

---

## Opinionated Defaults

The system should work well immediately.

Every default should be overridable.

---

## Reliability Over Features

The bridge should prioritize stability over shipping new features.

A reliable bridge with fewer features is preferable to an unstable bridge with many.

---

## Transparency

The runtime should always be able to explain why something is represented the way it is.

No hidden magic.

---

# 7. Product Philosophy

Orchard is **not a protocol bridge.**

It is an Apple Home presentation engine.

Instead of translating Home Assistant concepts directly, the runtime builds its own internal Apple model.

This distinction drives the entire architecture.

---

# 8. User Experience Principles

The user should feel like they are configuring Apple Home—not Home Assistant.

Terminology should favour Apple concepts.

Examples:

Instead of:

```
Entity
```

show

```
Accessory
```

Instead of:

```
Domain
```

show

```
Accessory Type
```

Hide Home Assistant terminology unless Advanced Mode is enabled.

---

# 9. Core Architecture

```
                     Home Assistant

              Event Bus
              Entity Registry
              Device Registry
              Area Registry
              State Machine

                      │

                      ▼

         Orchard Core

    ┌────────────────────────────────────┐

    Discovery Engine

    Apple Model Builder

    Mapping Engine

    Synchronization Engine

    Configuration Engine

    Preview Engine

    Health Engine

    Compatibility Layer

    HomeKit Engine

    └────────────────────────────────────┘

                      │

                      ▼

              Apple Home

              Siri
```

---

# 10. Internal Apple Model

Internally the runtime represents the home using Apple concepts.

```
Home

├── Rooms

│     ├── Accessories

│     ├── Scenes

│     ├── Controls

│     └── Automations

├── Siri

├── Presentation

└── Synchronization
```

Home Assistant data feeds this model.

The model is never a mirror of Home Assistant.

---

# 11. Discovery Engine

The runtime continuously monitors:

* New entities
* New devices
* Capability changes
* Area changes
* Entity removal

When a new compatible entity appears:

```
New Apple Home Accessory

Kitchen Pendant

Detected.

[ Add ]

[ Configure ]

[ Ignore ]
```

Ignored entities remain ignored until manually reviewed.

---

# 12. Apple Model Builder

Responsible for determining:

* Accessory type
* Room
* Display name
* Supported capabilities
* Siri representation
* Recommended defaults

This is where opinionated decisions live.

---

# 13. Mapping Engine

Converts Apple Model into HomeKit objects.

Priority:

Native HomeKit

↓

Stable workaround

↓

Graceful fallback

Never use unstable hacks.

---

# 14. Synchronization Engine

## Primary

Event driven.

No polling during normal operation.

Changes propagate immediately.

---

## Secondary

Scheduled reconciliation.

Responsibilities:

* Missed events
* Network interruptions
* Entity rename verification
* Capability verification
* State reconciliation

Default interval:

5–10 minutes

Configurable.

---

# 15. Health Engine

Dashboard showing runtime status.

Example:

```
Connected

128 Accessories

120 Synced

5 Awaiting Review

2 Ignored

1 Needs Attention

Last Sync

1 second ago
```

The runtime should never feel like a black box.

---

# 16. Preview Engine

Every accessory should display:

* Name
* Room
* Icon
* Controls
* Apple representation

Example:

```
Kitchen Pendant

Appears as

Light

Room

Kitchen

Controls

✓ Brightness

✓ RGB

✓ Colour Temperature

✓ Adaptive Lighting
```

Changes update instantly.

---

# 17. Explanation Engine

Every mapping should answer:

```
Why?
```

Example:

```
Kitchen Pendant

Mapped as:

Apple Light

Reason

Supports

• Brightness

• RGB

• Colour Temperature

Recommendation

Apple Light
```

---

# 18. Accessory Configuration

Every accessory supports:

## Identity

Display name

Room

Category

Icon

---

## Exposure

Visible

Hidden

Individual

Grouped

Both

---

## Voice

Preferred Siri name

Future alias support (if technically possible)

---

## Behaviour

Adaptive Lighting

Brightness limits

Colour temperature limits

Transition defaults

Effects

---

## Advanced

Source entity

Entity ID

Diagnostics

HomeKit properties

Debug information

---

# 19. Change Management

## Automatic

Rename

Area rename

Metadata

Capability additions

Friendly name changes

Preserve user customisations.

---

## Review Required

Entity deleted

Capability loss

Domain change

Merge

Split

Mapping conflicts

Notification example:

```
Kitchen Pendant has changed.

Now supports RGB colours.

Recommended:

Enable Colour Controls

[ Review ]

[ Accept ]

[ Ignore ]
```

---

# 20. Reliability Requirements

Highest engineering priority.

Minor platform updates should never require manual intervention.

Supported updates:

Home Assistant patch releases

Home Assistant minor releases

iOS point releases

tvOS

HomePod OS

Major platform changes may require compatibility updates.

---

# 21. Compatibility Layer

Every external dependency passes through adapters.

```
Home Assistant Adapter

↓

Runtime

↓

HomeKit Adapter
```

No business logic directly references external APIs.

---

# 22. Supported Accessories (v1)

Lights

Scenes

Future:

Buttons

Triggers

Fans

Covers

Locks

Climate

Garage Doors

Sensors

TVs

Cameras

---

# 23. Light Support

Support:

On / Off

Brightness

RGB

HSV

Colour Temperature

Effects

Transitions

Adaptive Lighting (where supported)

Capability detection should be automatic.

---

# 24. Scene Support

Highest priority feature.

Goal:

Represent Home Assistant scenes in the most native Apple experience possible.

Decision order:

Native

↓

Stable workaround

↓

Graceful fallback

---

# 25. Performance Requirements

Startup:

<5 seconds

State propagation:

<100ms typical

Configuration save:

Instant

Memory usage:

Low enough to comfortably run on Raspberry Pi hardware.

---

# 26. Security

No cloud dependency.

No telemetry.

No analytics.

Everything remains local.

---

# 27. Technology Decisions

## Runtime

Rust

Reason:

Memory safety

Excellent concurrency

Long-running reliability

Performance

---

## Home Assistant Integration

Python

Native Home Assistant integration layer.

---

## UI

Native Home Assistant frontend.

Use existing HA UI patterns.

Should feel like part of Home Assistant.

---

## Storage

Home Assistant `.storage`

Migration capable

Versioned

Structured

Future export:

YAML

---

## Packaging

HACS

Single install

Single update

No Docker

No additional containers

---

# 28. Testing Strategy

Unit tests

Integration tests

Regression tests

Protocol tests

Compatibility tests

Every bug becomes a permanent regression test.

---

# 29. Release Philosophy

Conservative.

Quality over speed.

Stable over clever.

No feature ships without automated tests.

---

# 30. Future Roadmap

## Phase 1

Runtime

Discovery

Lights

Scenes

Configuration

Health Dashboard

Preview Engine

---

## Phase 2

Buttons

Triggers

Automations

Motion

Presence

---

## Phase 3

Fans

Climate

Locks

Garage

Sensors

Cameras

TVs

---

# 31. Success Metrics

The project is successful when:

* Apple Home feels intentionally designed.
* Users rarely need to open the runtime after setup.
* Minor updates do not break functionality.
* Configuration remains simple despite powerful customization.
* The runtime explains every decision it makes.
* Users forget the bridge exists because everything just works.

---

# 32. Guiding Principles

1. Apple Home is the interface.
2. Home Assistant is the source of truth.
3. Reliability before features.
4. Opinionated defaults with deep customization.
5. Explain every decision.
6. Never expose Home Assistant concepts unless necessary.
7. Prefer native implementations.
8. Stable workarounds over fragile hacks.
9. Build for years, not months.
10. If Apple would do it differently, reconsider the design.
