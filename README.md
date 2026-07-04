# Orchard

The Apple Home experience Home Assistant deserves.

Orchard is a HACS custom integration that builds an Apple-first presentation model on top of Home Assistant lights and scenes.

It discovers compatible entities, explains each mapping, keeps a versioned `.storage` configuration, exposes a Home Assistant panel, and provides service/API controls for review and reconciliation.

## Status

This is an early runtime implementation for the PRD in `PRD.md`. It includes:

- Config flow setup
- Event-driven discovery for lights and scenes
- Scheduled reconciliation
- Versioned Home Assistant storage
- Accessory review, ignore, and configuration
- Health dashboard
- Preview and explanation views
- Services for reconcile, accept, and ignore
- Rust model crate scaffold for long-term runtime core work

## Install

Copy this repository into:

```text
config/custom_components/orchard
```

Or install as a custom HACS repository, then restart Home Assistant.

## Use

1. Go to **Settings > Devices & services > Add integration**.
2. Add **Orchard**.
3. Open **Orchard** in the sidebar.
4. Review detected lights and scenes.
5. Save any names, rooms, Siri names, or exposure choices.

## Services

- `orchard.reconcile`
- `orchard.accept_change`
- `orchard.ignore`
