# Satellite basemap

Default: NASA GIBS Blue Marble Shaded Relief and Bathymetry, as used in the earlier satellite-style production. Keep land texture, shaded terrain and ocean bathymetry visible; draw administrative outlines above imagery. Avoid opaque polygon fills that hide the background. Solid vector styling is an explicit creative alternative, not an automatic fallback.

## Esri World Imagery — requested visual reference

The user-selected visual reference is Esri World Imagery. Use these exact links when identifying the layer or checking its current service terms:

- [ArcGIS item overview](https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9#overview)
- [Open the layer in ArcGIS Map Viewer](https://www.arcgis.com/apps/mapviewer/index.html?layers=10df2279f9684e4a9f6a7f08febac2a9)
- [Service metadata](https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer?f=pjson)
- [Item metadata, credits and license information](https://www.arcgis.com/sharing/rest/content/items/10df2279f9684e4a9f6a7f08febac2a9?f=pjson)
- [Esri terms summary](https://goto.arcgis.com/termsofuse/viewsummary) and [terms of use](https://goto.arcgis.com/termsofuse/viewtermsofuse)
- [World Imagery (for Export)](https://www.arcgis.com/home/item.html?id=226d23f076da478bba4589e7eae95952), the separately documented layer for supported offline export workflows.

Esri World Imagery is a satellite/aerial imagery service, not an open-source imagery dataset. Open-source mapping clients may use the service subject to its terms; their code license does not grant rights to the imagery. Do not assume that public viewing or an HTTP 200 authorizes arbitrary tile downloads, redistribution, offline caching or commercial video export. Check the applicable account/service terms for the actual production workflow and retain required attribution.

The item metadata checked on 2026-10-18 credits Esri, Vantor, Earthstar Geographics and the GIS User Community. Actual contributors vary with location and scale; use the service's current imagery citations for the scene, not this list as a permanent exhaustive credit. Record the item/service, access date, relevant imagery date and citations in the production SOURCES.md and place required credits in the delivered output. The overview explicitly distinguishes this viewing layer from the layer intended for offline exports.

Implementation status: these links document the user's preferred Esri appearance; the bundled renderer still implements NASA Blue Marble only. Do not set an Esri provider in scene JSON and claim it works, silently substitute NASA for an explicitly requested Esri shot, or treat this documentation update as an implemented Esri integration. Integrating an authorized Esri workflow is separate renderer work. NASA remains the executable default until that integration is implemented and verified.

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
