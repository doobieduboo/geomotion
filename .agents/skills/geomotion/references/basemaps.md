# Satellite basemap

Default: NASA GIBS Blue Marble Shaded Relief and Bathymetry, as used in the earlier satellite-style production. Keep land texture, shaded terrain and ocean bathymetry visible; draw administrative outlines above imagery. Avoid opaque polygon fills that hide the background. Solid vector styling is an explicit creative alternative, not an automatic fallback.

## Public source references

- NASA Worldview: https://github.com/nasa-gibs/worldview — NASA's open-source satellite viewer; its README identifies GIBS as the imagery service. Worldview code uses NASA-1.3, not this toolkit's license. We link it for reference; no Worldview code is vendored.
- NASA GIBS integration examples: https://github.com/nasa-gibs/gibs-web-examples — official examples for mapping clients. Reference only; no third-party code copied.
- Service documentation: https://nasa-gibs.github.io/gibs-api-docs/
- Imagery use guidance: https://www.nasa.gov/nasa-brand-center/images-and-media/

Open-source client code and imagery have separate terms. Record the actual layer, date, provider and relevant media terms in the production SOURCES.md. Do not infer that arbitrary satellite providers or third-party assets are freely licensed because a map client is open-source. Credit this background as “NASA Blue Marble / NASA GIBS”; the renderer inserts this credit when none is supplied. Explicit custom attribution must retain the NASA credit alongside other required credits.

## Implemented source

`scripts/basemap.py` defines the tile URL and supported matrix. Renderer configuration is in `defaults.json` and `templates/scene.json`:

```json
{"basemap":{"type":"satellite","provider":"nasa_gibs_blue_marble","saturation":0.6,"brightness":0.75},"attribution":"NASA Blue Marble / NASA GIBS"}
```

Layer: `BlueMarble_ShadedRelief_Bathymetry`; fixed service date: `2004-07-01`; projection: EPSG:3857; matrix: `GoogleMapsCompatible_Level8`; JPEG tiles, 256 pixels, zoom 0–8. This is a historic background composite, NOT current satellite evidence of fires, smoke, land cover or boundaries. Source those observations and geometries independently. Very close zooms cannot invent detail beyond source resolution.

Final mode requests two more tile zoom levels than preview where available (maximum 8); transforms, borders and type render directly at output resolution. This does not guarantee unlimited detail in the underlying composite.

## Access and failure behavior

- Imagery host: `gibs.earthdata.nasa.gov`; HTTPS, no Gemini key. Do not send TTS credentials to imagery providers.
- Cache: scene directory `cache/nasa-blue-marble-2004-07-01/`, separated from other providers/layers. Reuse valid downloaded tiles. Do not commit cache to the skill repo or include it in a compact raw bundle by default.
- Missing tiles are downloaded before rendering; HTTP/proxy/decode failures stop the satellite render. Report the actual host/status and inspect active network policy. Do not silently switch to a plain background, another provider or a different dated observation.
- If network is blocked, reuse an existing compatible cache or report the blocker. A color-map draft may be made only when explicitly requested and must be labeled accordingly.
- Inspect a representative 360p frame before a full render: satellite texture visible, boundaries aligned, no opaque fill masking terrain, source credit legible, no tile seams. Preview remains 360p; native compact 1080p requires the final request.
