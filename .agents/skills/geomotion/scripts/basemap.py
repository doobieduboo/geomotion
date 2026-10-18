"""Esri World Imagery only. Imagery access remains subject to Esri terms."""

from config import DEFAULTS

PROVIDER = DEFAULTS["basemap"]["provider"]
SERVICE = (
    "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer"
)
MAX_ZOOM = 23
ATTRIBUTION = DEFAULTS["basemap"]["attribution"]


def validate_basemap(config):
    if config.get("type") != "satellite" or config.get("provider") != PROVIDER:
        raise ValueError(
            "Only Esri World Imagery satellite basemaps are supported; no provider or solid-map fallback"
        )


def tile_zoom(camera_zoom, mode):
    return max(0, min(MAX_ZOOM, int(camera_zoom) + (2 if mode == "final" else 0)))


def tile_url(z, x, y):
    if not 0 <= z <= MAX_ZOOM or not 0 <= y < 2**z:
        raise ValueError("Esri World Imagery tile outside supported matrix")
    return f"{SERVICE}/tile/{z}/{y}/{x % (2**z)}"
