# Source policy

GeoMotion is topic-agnostic. No narrative, historical event, country dataset, image collection or soundtrack is loaded automatically. Each production supplies its own geometry, images, flags, sprites and audio as needed.

Create a scene-specific SOURCES.md recording:
- Input file, creator/provider, URL, version/date and actual license.
- What the data supports, including temporal or geographic accuracy limitations.
- Required attribution and where it appears in the distributed result.
- Whether a route, effect, boundary or marker is factual, reconstructed or illustrative.

The optional satellite basemap uses Esri World Imagery. Its credits and use requirements depend on the contributed imagery and location. Service: https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer . Review the provider terms before distributing output. Use the scene's `attribution` field when on-video credit is required, or choose another compatible source.

The repository's MIT license applies to its code, not to external media. Source research is scene-specific. A missing scene credit or source file is not permission to omit required attribution.

## Bundled fonts

Open Sans (Regular/Bold) and Montserrat (ExtraBold) are bundled as static instances generated from Google Fonts variable fonts. Each family's SIL Open Font License 1.1 is included in the skill's `fonts/` directory. Sources: https://github.com/google/fonts/tree/main/ofl/opensans and https://github.com/google/fonts/tree/main/ofl/montserrat . Code's MIT license does not replace font licenses.
