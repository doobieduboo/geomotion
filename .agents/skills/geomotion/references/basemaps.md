# Esri World Imagery — single basemap

Esri World Imagery is the only permitted basemap. Do not use another provider or a plain vector background, including when access fails.

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

## Implemented source and rendering

The renderer implements this exact service through `scripts/basemap.py`. The scene inherits the basemap preset; do not duplicate provider settings in templates. Other provider/type values raise an error before rendering. Brightness and saturation follow the preset, preserving source color by default.

Service tiles use Web Mercator, 256px JPEG, levels 0–23; availability and detail vary by location/scale. Final mode requests two higher tile levels where supported and renders geometry/text at native final size. No preview upscaling. Initial editing uses 360p; an explicit final request establishes the retained 1080p stage for that production under [delivery.md](delivery.md).

Draw geographic outlines above the imagery; avoid opaque region fills masking terrain. Imagery is a background composite with different capture dates, not live evidence of fires or smoke. Source current observations independently.

## Access, terms and failure behavior

- Host: `services.arcgisonline.com`; metadata/item host: `www.arcgis.com`. Do not send Gemini secrets to these hosts.
- Tiles are held in session memory for rendering; no persistent offline tile cache or raw tile distribution is implemented. The source-buffer byte budget and available-memory check are documented in [pipeline.md](pipeline.md); final concurrency and numeric memory limits live in the execution preset. Service metadata reports `exportTilesAllowed: false`. A temporary client request does not itself establish rights to a particular published video; apply the current Esri terms to the actual account and workflow.
- Save/load does not automatically add a raw-tile disk cache. Reuse compatible previously rendered video/map-containing segments before requesting the same basemap again; follow [revision reuse](pipeline.md#revision-reuse). A reusable clean map layer must actually exist with its camera/profile/provenance; do not claim the current renderer saves one automatically. Any future tile-cache implementation must follow the applicable service terms and retain attribution.
- For offline workflows, follow the linked Esri export documentation/layer under the applicable rights. Do not change the service URL automatically or assume access is interchangeable.
- HTTP, proxy, auth and image-decode errors stop rendering and identify the failing URL. Report the actual blocker. No fallback to another provider or a solid background.
- Default contributor credit is inserted in the video; add accurate location/scale-specific citations when required. Preserve attribution in final exports and browser delivery. Never remove credits to clean up the design.
- Inspect a representative preview frame: textured land/sea, aligned boundaries, original source brightness, no missing tiles/seams, and legible credit. Keep caches and downloaded production media out of this reusable repo.
