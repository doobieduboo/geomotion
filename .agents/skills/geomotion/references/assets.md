# Asset contract and inventory

## Reusable component inventory

The [library catalog](../library/catalog.json) owns the ten category folders and item status. Read [library/README.md](../library/README.md) for file layout, reference intake and the distinction between a supplied preview and a verified component. Keep original GIF/AEP/media in the external working library; do not mistake inspection JSON for a renderable asset.

## Map data
Use real coordinates, country/admin polygons, coastline/island geometry, and licensed imagery. Record the source version and historical applicability. GeoJSON is WGS84 lon/lat. Preserve Polygon holes and MultiPolygon parts. For long-distance scenes, unwrap longitudes or use a globe-aware projection to avoid antimeridian jumps.

For historical stories, verify the period-specific country/empire name, flag and emblem, capital, administrative seat and territorial extent before labeling or filling them. A modern outline used only for orientation must be recorded as such; do not silently equate it with an empire's historical borders. Distinguish treaty, ratification, transfer and payment dates, and keep archive captions consistent with the actual document date. These facts remain project inputs, not reusable story defaults.

## Geographic flag fills and emblems

Prepare one intended flag composition per territory, clipped to verified land geometry with holes and disconnected islands preserved. Transparent sea and the intended land alpha retain the original imagery. Preserve the factual RGB of the period-specific flag and emblem; the ordinary colored-land multiply tint must not recolor a historical flag. Choose explicitly whether one composition spans the territory or distinct regions have separate textures; never accidentally tile the full flag or repeat its emblem across polygon parts.

For a stable flag/emblem through camera pan, zoom, rotation and longitude wrap, supply a geographically prepared `world_overlays` texture as documented in [scene-format.md](scene-format.md). Bake the single emblem into the flag at a fixed geographic location. Both must undergo the same transform; do not recenter, duplicate or detach the emblem to keep it visible in a partial view. A restrained optional bloom may use the texture’s own colors and projected alpha; it must not replace those colors with the outline/focus hue. If its geographic position leaves the frame, it may leave the frame. Review mask edges, transparency, islands, dateline splits and raster resolution at the closest intended zoom. Keep the fill visible through subsequent camera/focus changes until an authored narrative or ownership transition, aligned with the actual VO.

Ordinary `regions[].flag` uses screen-bounding-box texture fitting; it is not equivalent to a fixed geographic world texture during rotation or seam crossings. Select the supported method that meets the shot's stability requirements, prepare masks externally, and register textures, geometry and generation scripts in the production inputs. The renderer samples supplied overlays; it does not create historical masks or integrated emblems automatically.

## Documentary archives and reconstruction

For map documentaries, prioritize authentic photographs, footage and primary records as visual evidence. Match each archive to the spoken claim. A press conference documents a statement; it does not by itself prove the alleged event. A response photograph does not establish an agency, deployment location or date beyond what its source supports. Do not replace relevant archives with generated imagery merely because reuse terms are not stated.

Keep factual verification separate from the reuse assessment. In the production's `SOURCES.md`, record the original publisher/creator, source URL, publication and capture dates separately when known, place, supported claim, verification limits, and visible credit. Record reuse status accurately: explicit license, permission, public-domain basis, documented editorial-exception rationale, or terms not found. Never invent a license or mark uncertain use as cleared.

Written permission is not a universal prerequisite for documentary research or every editorial use. Missing public reuse terms alone must not trigger automatic exclusion, a permission request, or deletion of an approved archive. Evaluate the intended use: applicable law, a relevant reporting/criticism/quotation exception where supportable, the amount and resolution needed, commentary/context, attribution, and known publisher restrictions. Source credit, public availability and a public-interest subject do not independently guarantee lawful reuse. Do not assume government, NGO or news photographs are public domain, or that only commercial photo libraries have protected material.

Use archives to support the documentary's specific reporting rather than as an unrelated image collection or substitute for the original publication. Preserve existing attribution and required notices. Seek clean originals; do not remove watermarks or evade paywalls/access restrictions. If a concrete restriction or material unresolved issue prevents the intended use, explain the specific issue and a suitable alternative before changing the evidence presentation. Preserve originals and provenance locally; do not silently remove approved archives, change periods/locations, or describe an unverified replacement as equivalent evidence. Routine source uncertainty is documented, not turned into a blanket production approval gate.

Generated or AI-assisted reconstructions are explanatory material, never archival proof. Identify them clearly as reconstruction in the presentation and source record; do not imply original camera capture. Preserve verified geography, chronology and factual details. Do not invent identifiable participants, actions, damage, deployment or fire extent. Retain the authentic source separately and document substantive alterations; matching a real image's style does not authenticate a reconstruction. Ordinary crop, exposure and placement adjustments must preserve evidentiary meaning. Illustrative fire, smoke and vehicle effects do not establish observed coverage or actual positions.

## Asset families
| Family | Files / metadata |
|---|---|
| Country fill | ISO country code, flag PNG/SVG, country GeoJSON, license |
| Flagpole | Flag texture, pole/ground anchor, flutter frames or procedural deformation, shadow |
| Vehicle | RGBA atlas, 16–32 headings, frame size, ground anchor, heading order, view elevation, source/license |
| Tank | Hull atlas, optional separate turret atlas and muzzle flash |
| Aircraft | Heading atlas, engine trail, optional rotor/propeller frames, shadow |
| Ship | Heading atlas, wake, shadow |
| Land transport | Heading atlas, wheels/dust where useful |
| Effects | RGBA frame sequence, fps, lifetime, anchor, blend mode, color-space assumptions |
| Infographic | Real photo/image, verified caption/date, source/license; bubble is drawn procedurally |
| Audio | Licensed/original score and SFX, levels, timing |

A flag fill and a flagpole marker are separate layer types. A marker’s meaning comes from the brief; it must not silently assert sovereignty or territorial control. Texture extent and repetition follow the geographic flag contract above; see [scene-format.md](scene-format.md) for the implemented mapping.

## Sprite atlas schema

```json
{
  "image": "tank.png",
  "columns": 8,
  "headings": 32,
  "frame_width": 192,
  "frame_height": 192,
  "anchor": [96, 132],
  "heading_zero": "north",
  "heading_order": "clockwise",
  "view_elevation_deg": 55,
  "license": "record the actual license"
}
```

Each atlas row continues the clockwise heading sequence. Relative heading = world heading minus camera heading. Only use the 32-view claim after checking 32 distinct correct views. A fixed-camera top-down atlas supports yaw changes, not arbitrary pitch/orbit. Use screen-scaled sprites and a geographic ground anchor to avoid sliding.

Optional `animation_frames` and `animation_fps` provide a looping supplied frame sequence per heading. Store all frames for heading0 first, then heading1, in row-major order. The first frame is also the idle frame after arrival. For a single fixed-view animated icon use `headings: 1`; do not label that as a multi-angle atlas. See the route timing contract in scene-format.md.

## Utilities
`map_assets.py` implements:
- `clip_flag`: projected polygons → flag-filled RGBA region with polygon holes.
- `flagpole`: procedural waving flag at a ground anchor.
- `select_sprite`: camera-relative heading → atlas frame and anchor.

These helpers accept actual input assets; they do not download a complete vehicle library. Verify view order, licensing and scale before scene integration.
