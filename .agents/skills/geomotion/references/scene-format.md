# Topic-neutral scene composition

The input is a scene description, not a story template. No subject, place, date or duration is built in. `templates/scene.json` uses anonymous points only to illustrate structure; replace them with the actual request.

## Coordinates, paths and time
- Geographic positions are `[longitude, latitude]`, in WGS84 degrees.
- Times are source seconds; duration is explicit, positive and finite. Optional timeline cuts change playback time consistently; see [pipeline.md](pipeline.md).
- All media and GeoJSON paths resolve relative to the scene JSON file.
- Preview is 360×640/24fps; final is 1080×1920/30fps.
- Screen offsets, widths and font sizes use a 720-wide design grid and scale to the selected output. The preview renders directly at 360p.

## Top-level fields

| Field | Meaning |
|---|---|
| `export` | Optional explicit mode overrides; omitted uses `defaults.json`. Standard delivery is preview 360p or final 1080p |
| `duration` | Required original source timeline length; no topic-specific fixed duration |
| `timeline` | Explicit silence cuts, source/output audio clock and shared phrase events; [contract](pipeline.md) |
| `subtitles` / `subtitle_cues` | Inline or JSON-file actual phrase cues, source-timed; use one form |
| `archive_manifest` | Version-1 provenance manifest; callouts may reference `archive_id` |
| `inputs` | Additional local dependency paths by approval domain |
| `metadata` | Optional informational project metadata; no renderer behavior |
| `focuses` | Source/event-timed protected geographic bounds or region IDs; [composition contract](composition.md#executable-composition-contract) |
| `composition` | Explicit overrides of preset layout limits, spacing and tracking |
| `cta` | Optional authored text and source interval/event; centered clear placement above focus |
| `camera` | Required keyframes: `time`, `center`, `zoom`, optional `rotation` in degrees; `ease: "linear"` disables easing for that incoming segment |
| `basemap` | Esri World Imagery only: `type: "satellite"`, `provider: "esri_world_imagery"`; optional `saturation` and `brightness` inherited from the preset. Other providers and solid backgrounds are rejected. See [basemaps.md](basemaps.md) |
| `regions` | Optional GeoJSON geometry layers with outline/reveal and optional flag fill |
| `markers` | Optional geographic points, labels and flagpole markers |
| `routes` | Optional animated paths and atlas sprites |
| `callouts` | Optional geographic infographic bubbles, with image and text |
| `titles` | Editable title layers: `definition`, optional scene `start` and `overrides`; see [titles.md](titles.md) |
| `audio` | Optional path to an actual audio file; omitted means silent |
| `attribution` | Additional on-video source credit; required Esri credit is always retained |

A visual layer may have `start` and `end` visibility times unless specified below. RGB colors are three integers from 0 to 255. Avoid hidden mandatory decorative layers.

## Regions

`geojson` is a path to a Geometry, Feature or FeatureCollection. Polygon and MultiPolygon are supported. Optional `match` selects features by exact property values. `fill` supplies an optional solid RGB region fill, `color` controls the reference outline (neutral/light by default), `reveal` controls persistent reference-stroke reveal in seconds (preset default0 means already complete), `flag` supplies a flag texture, and `opacity` sets its alpha (0–255). Omitted fill opacity comes from `defaults.json.region_fill.solid_opacity` or `.flag_opacity`; flag texture alpha is multiplied by this mask opacity. Ordinary color fills inherit `fill_blend: "terrain_tint"` from the preset: a saturated multiply tint preserving the satellite terrain, rather than a pastel normal-alpha wash. Explicit `fill_blend: "normal"` selects ordinary alpha composition. A `flag` always preserves its supplied RGB with normal composition; the color-tint blend does not recolor it. Prefer one intended fill per territory rather than unintentionally stacking solid and flag layers.

Optional `fill_glow` is a boolean or mapping, inheriting `defaults.json.region_fill.glow` when omitted. `false` disables emission; a mapping may override `enabled`, nonnegative `inside_gain`, `strength` and `flag_strength`, and `layers` containing finite nonnegative `radius_design` and `gain`. A layer list may contain up to four entries, including an empty list to omit outside halos. Omitted mapping fields inherit the preset; an authored `layers` list replaces that list. Emission uses linear-light additive composition: restrained terrain-modulated light stays inside the land mask, while same-color blurred layers extend outside it without tinting the rest of the basemap. Flag emission keeps the source texture colors and uses the preset flag-strength factor. These settings affect the existing layer lifetime and do not create ownership or speech alignment.

For each region layer, the loader combines all selected features into one polygon collection. Flag fill stretches one texture over that collection's current projected screen bounding box and masks it to the polygons and holes; separate matched features do not automatically receive separate textures. Use distinct region layers when independent texture extents are intended. This screen-bounds fitting is not a geographically fixed flag texture under rotation or dateline crossings. Use supplied geographic world overlays for stable integrated flags/emblems. Extreme close-ups may require pre-clipped polygons to keep flag allocation within memory limits. Split geometries crossing a projection seam before rendering.

Region/overlay visibility and focus emphasis are independent. Author explicit layer lifetimes for persistent fills and successive ownership states; the renderer does not infer these from the camera. A region's bare `event` reference resolves both visibility bounds to that phrase, not to an indefinite ownership state. See [composition.md](composition.md) for timing and [assets.md](assets.md) for historical flag preparation.

## Markers

`position`, optional `label`, `color`, `font_size`, screen `offset` for the label, and optional `flag` image. A flag image produces a waving flagpole anchored at the geographic position. Marker semantics come from the user's content; a flag does not automatically mean territorial control.

## Routes

`points` is a sequence of at least two geographic coordinates. Required `start` and `end` define travel time; optional `hide_at` controls when the completed path disappears. Optional `color` and `width` control the path. Optional `atlas`, `atlas_metadata` and `sprite_scale` select an actual multi-angle vehicle asset; otherwise the moving marker is a dot. Optional `fade_in` / `fade_out` are nonnegative source-clock seconds, constrained to the visibility lifetime from `start` through `hide_at` (or scene end), independently of motion `end`. They fade the complete trail, casing, head/sprite and associated glow together; the completed stroke stays intact during its hold, with no traveling tail. The view is selected from projected travel direction, incorporating camera rotation. Path progress is evaluated in projected screen distance each frame; use a scene-specific geodesic sampler for exact physical speeds or long-distance trajectories.

Routes may set `arrow: true` to use a leading triangular arrowhead instead of a moving dot/sprite. `head_length`, `head_width` and optional `casing_width` are design pixels; `casing_color` defaults to dark charcoal. The head follows the current revealed path tangent, grows from the initial point, and remains at the geographic destination after `end`; the entire completed stroke persists until `hide_at`. Supply a sampled geographic curve in `points` for curved arrows.

Supplied sprite atlas metadata may additionally set `animation_frames` and `animation_fps` (positive values; default one static frame). Cells are heading-major, with each heading's animation frames contiguous in row-major grid order. Animation starts at route `start`, loops while traveling, and returns to the first/idle frame at `end`; the ground anchor stays unchanged. One heading denotes a fixed-view billboard, not a multi-angle model. For a stationary looping effect, supply two identical route points and keep `end` at the visibility end.

## Callouts

`position` anchors the leader line. `title`, `lines` (explicit line breaks as separate strings), optional `image`, `color`, screen `width` and preferred `offset` define a compact bubble. `placement` is `auto` by default; `manual` checks the authored position without relocation. Width is a maximum for text-only bubbles: actual font measurement determines compact bounds and wrapping. Padding comes from the preset. Image panels use that width and preserve the original image ratio; oversized panels fail rather than crop silently. Inspect placement and subtitle collisions. This is an optional information layer, not a fixed slide layout. Optional `fade_in` and `fade_out` are nonnegative source-clock seconds whose sum must fit the callout lifetime. Smoothstep opacity applies to the complete panel, original image, caption and leader together. The full rectangle remains reserved during fades; omitted fields preserve abrupt full visibility.

Image callouts may set `image_crop: [left, top, right, bottom]` as integer pixel bounds in the original source image. The rectangle must be nonempty and wholly inside that image; invalid bounds fail instead of padding or clipping silently. Layout and rendering use the same cropped aspect ratio. This is an exact source-pixel detail view, not regenerated imagery; preserve the source file/provenance, caption an excerpt as such, and retain full-document context when the brief requires it. `show_leader: false` omits only that callout's geographic connector; the panel, placement checks and whole-layer fades remain active. Two simultaneous image views require an explicit scene media-budget override if they exceed the preset.

## Global movement

The camera interpolates the shortest longitude path and wraps satellite tile x coordinates. The flat map is Web Mercator, with supported scene coordinates between latitude −85 and +85 degrees. It does not simulate a globe. Inspect dateline-crossing polygons/routes and adapt projection or split shots when needed. Very wide same-zoom sequences have an explicit memory guard and may need multiple shots.

Region strokes unwrap connected vertices before drawing visible periodic copies; the camera wrap seam never becomes a connecting line. Satellite sampling uses one tile level selected from the complete scene's maximum camera zoom (plus the final-mode detail offset), including all checkpoint chunks, to avoid imagery-level changes during camera ramps.

Unknown top-level fields are rejected by the generic loader. Do not pass custom production fields and assume their effects were rendered. For resumable native export, review/approval contracts and pipeline commands, see [pipeline.md](pipeline.md).

An authored outline reveal grows by cumulative Mercator path length from one starting point, drawing the largest boundary first and disconnected rings sequentially without connecting across water. Its glow is generated from the revealed stroke. The reference border is already complete by default; a focus reveal replaces its corresponding portions rather than adding another full border. Completed portions remain for the layer/cue interval; no traveling/fading tail is applied. Duplicate rings are removed; union adjacent source polygons before rendering when shared internal boundaries are unwanted.

`stroke_origin: [longitude, latitude]` optionally rotates the main closed boundary to its nearest vertex without changing topology, length or geographic position. Reveal eases at its ends; core and all bloom layers share that revealed path. Width, glow, color and antialias values come from `defaults.json.region_outline`; the focus role automatically inherits its nested `focus_preset`. Width is output-scaled design pixels, independent of camera zoom. A region or focus cue can explicitly override positive `stroke_width_design`; reference regions may override `casing_width_design`, `casing_opacity` and `casing_color`. Casing is disabled by default and, when explicitly enabled, is coincident contrast edging rather than a displaced boundary. Use `reveal: 0` for a completed reference border.

Optional `focus_strokes` on a region supplies ordered, nonoverlapping source-time cues with `start`, `end`, positive `reveal` duration and optional `color` (RGB for core and bloom), `stroke_width_design`, `stroke_origin`, `glow` and `glow_fade_out`. Reveal must finish within its cue. The independent reference border remains visible on unrevealed portions; focus core/casing and glow grow only along the revealed path. The reference core and neutral halo are suppressed locally beneath that path, including coincident neighboring boundaries, so there is one visible border. Completed focus geometry stays until the cue ends; the reference role remains outside that cue. `glow_fade_out` fades the emphasis halo near cue end while retaining its completed core, not an erasing tail. Country fills and world overlays do not change with focus cues. A later cue explicitly restarts only the emphasis; disconnected islands remain sequential without bridges.

Exact ring deduplication is not a general shared-border topology repair. Compatible geometry and preprocessing remain required to avoid overlapping national/admin boundaries. A traveling stroke with an erasing tail is not a supported switch on these region cues; if explicitly requested it needs an implemented and verified extension.

Reference and focus inherit the shared `defaults.json.region_outline.glow` recipe. Optional `focus_strokes[].glow` is a boolean or mapping with `enabled`, nonnegative `strength`, and up to four `layers` of finite nonnegative `radius_design`/`gain`; omitted mapping fields inherit the shared recipe and an authored `layers` list replaces that list. `false` disables this additive bloom; the compact alpha-composited halo is controlled separately by the compatibility halo fields. All radii use output-scaled design pixels and gains scale linear-light emission. Bloom is composited beneath the sharp core and follows only the revealed focus path; no white core or extra border is inserted. Reference regions have no separate per-region `glow` override contract.

Explicit compatibility fields remain supported on focus cues: `glow_layers` selects one to four same-color halos, each with `radius_design`, optional `opacity` (0–255) and positive `gain`; `glow_radius_design`/`glow_opacity` select the single-halo recipe, with optional `glow_spread_design` for halo dilation. These authored recipes disable inherited additive bloom to avoid stacking two recipes. Prefer the inherited preset or the new `glow` mapping for new cues; use only one glow recipe per cue.

Focus cues may set `casing_opacity` (0–255), overriding `defaults.json.region_outline.casing_opacity`. This changes opacity only, not the one core boundary or width. Ordinary reference outlines use the preset casing opacity.

See [style.md](style.md#outlines-and-emphasis) for both roles and native-size interpretation. A cue with only `start`, `end` and `reveal` automatically uses the focus color, core width and glow from the preset; the reference uses the ordinary outline preset. Nested focus cues require absolute source times, not `event` references. This is automatic style inheritance, not automatic speech alignment or focus-cue creation.

## Geographic world overlays

`world_overlays` is an ordered array of supplied transparent PNG layers (`image`, optional source-clock `start`/`end`). Each square PNG covers the complete EPSG:3857 world: west/east -180/+180, north/south +85.0511/-85.0511. The renderer samples it with the same pan/zoom/rotation as Esri and wraps longitude; transparent ocean pixels preserve the basemap. This is a supplied thematic overlay, never a satellite-provider fallback. Author and verify country/polygon masks and attribution externally, register source data and generation scripts in `inputs`, and use sufficient source raster resolution for intended views. Default region outlines draw above these overlays.

Markers may set `show_dot: false` for a label-only geographic marker when a supplied emblem already identifies that point; labels keep their existing geographic anchor and screen offset. Flagpole markers are unaffected.

World overlays optionally specify `fill_kind: "flag"` (default) or `"color"`, and `fill_blend: "normal"` (default) or `"terrain_tint"`. Defaults preserve the authored texture RGB and alpha; historical flag textures must keep normal composition and factual source colors. A color overlay may explicitly select the terrain-preserving multiply tint. Optional `glow` is a boolean or mapping using the region `fill_glow` contract and shared fill defaults. It operates on the projected texture alpha/colors, respects the supplied land/sea mask and fade envelope, and scales flag emission by the preset flag-strength factor. Existing authored texture colors are not automatically retinted.

World overlays optionally specify nonnegative `fade_in` and `fade_out` durations in source seconds. Smooth opacity envelopes affect the supplied layer only, retaining its intrinsic alpha. Zero/omitted durations preserve immediate visibility; no basemap fade or outline traveling tail is introduced.

Precompose the flag and its single emblem into the same geographic texture for fixed placement; an emblem outside the current view is not recentered. Intrinsic PNG alpha controls terrain visibility. These overlays are sampled as supplied without automatic polygon clipping, historical-mask creation or ownership logic, so verify their masks and seam continuity before rendering. Overlay lifetimes use explicit source times; `event` references are not resolved for this group. Scope fills to topic-relevant territory while keeping the remaining world transparent.

The sampler caches the immutable premultiplied texture's alpha extent and limits each wrapped transform to its affected viewport rectangle, including bicubic filter support. Empty/offscreen portions skip sampling; the source texture, resolution and geographic transform are unchanged. Create a new texture object if its pixels change rather than mutating a cached source during rendering.
