# Topic-neutral scene composition

The input is a scene description, not a story template. No subject, place, date or duration is built in. `templates/scene.json` uses anonymous points only to illustrate structure; replace them with the actual request.

## Coordinates, paths and time
- Geographic positions are `[longitude, latitude]`, in WGS84 degrees.
- Times are seconds on the scene timeline; duration is explicit and positive.
- All media and GeoJSON paths resolve relative to the scene JSON file.
- Preview is 360×640/24fps; final is 720×1280/30fps.
- Screen offsets, widths and font sizes use a 720-wide design grid and scale to the selected output. The preview renders directly at 360p.

## Top-level fields

| Field | Meaning |
|---|---|
| `duration` | Required scene length in seconds; no topic-specific fixed timeline |
| `camera` | Required keyframes: `time`, `center`, `zoom`, optional `rotation` in degrees; `ease: "linear"` disables easing for that incoming segment |
| `basemap` | `type: "solid"` with RGB `color`, or `type: "satellite"` with optional `saturation` and `brightness`; satellite mode fetches Esri World Imagery tiles |
| `regions` | Optional GeoJSON geometry layers with outline/reveal and optional flag fill |
| `markers` | Optional geographic points, labels and flagpole markers |
| `routes` | Optional animated paths and atlas sprites |
| `callouts` | Optional geographic infographic bubbles, with image and text |
| `audio` | Optional path to an actual audio file; omitted means silent |
| `attribution` | Optional on-video credit when needed by the chosen data/media source |

A visual layer may have `start` and `end` visibility times unless specified below. RGB colors are three integers from 0 to 255. Avoid hidden mandatory decorative layers.

## Regions

`geojson` is a path to a Geometry, Feature or FeatureCollection. Polygon and MultiPolygon are supported. Optional `match` selects features by exact property values. `fill` supplies an optional solid RGB region fill, `color` controls outline, `reveal` controls outline reveal time in seconds, `flag` supplies a flag texture, and `opacity` sets its alpha (0–255).

Flag fill stretches one texture over the selected feature's projected bounding box and masks it to its polygons and holes; it does not deliberately paint the surrounding sea. Separate matched features get separate textures. For one flag across an archipelago, use one MultiPolygon feature. Extreme close-ups may require pre-clipped polygons to keep flag allocation within memory limits. Split geometries crossing a projection seam before rendering.

## Markers

`position`, optional `label`, `color`, `font_size`, screen `offset` for the label, and optional `flag` image. A flag image produces a waving flagpole anchored at the geographic position. Marker semantics come from the user's content; a flag does not automatically mean territorial control.

## Routes

`points` is a sequence of at least two geographic coordinates. Required `start` and `end` define travel time; optional `hide_at` controls when the completed path disappears. Optional `color` and `width` control the path. Optional `atlas`, `atlas_metadata` and `sprite_scale` select an actual multi-angle vehicle asset; otherwise the moving marker is a dot. The view is selected from projected travel direction, incorporating camera rotation. Path progress is evaluated in projected screen distance each frame; use a scene-specific geodesic sampler for exact physical speeds or long-distance trajectories.

## Callouts

`position` anchors the leader line. `title`, `lines` (explicit line breaks as separate strings), optional `image`, `color`, screen `width` and `offset` define a compact bubble. Fit text to the box and inspect the output. This is an optional information layer, not a fixed slide layout.

## Global movement

The camera interpolates the shortest longitude path and wraps satellite tile x coordinates. The flat map is Web Mercator, with supported scene coordinates between latitude −85 and +85 degrees. It does not simulate a globe. Inspect dateline-crossing polygons/routes and adapt projection or split shots when needed. Very wide same-zoom sequences have an explicit memory guard and may need multiple shots.
