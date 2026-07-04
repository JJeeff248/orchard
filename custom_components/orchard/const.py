"""Constants for Orchard."""

from __future__ import annotations

DOMAIN = "orchard"
NAME = "Orchard"
TAGLINE = "The Apple Home experience Home Assistant deserves."
VERSION = "0.2.0"

PANEL_URL = "/orchard"
PANEL_TITLE = "Orchard"
# Serve the app icon from the integration API so we can use a custom image
PANEL_ICON = "/api/orchard/icon.png"

STORAGE_KEY = f"{DOMAIN}.store"
STORAGE_VERSION = 1

DEFAULT_RECONCILE_INTERVAL_MINUTES = 5

EVENT_RUNTIME_UPDATED = f"{DOMAIN}_updated"
