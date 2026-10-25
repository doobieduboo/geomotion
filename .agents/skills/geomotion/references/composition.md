# Camera, narrative and layer composition

Use the current narration/brief and [defaults.json](../defaults.json), not timings from an older clip.

Fast-paced production follows [retention.md](retention.md); align useful visual beats to actual speech rather than forcing constant zooms or cuts.

## Camera and continuity

Use a full-frame flat Esri satellite map. Geographic overlays, outlines, zoom, pan, rotation and longitude wrap retain their supported behavior. Geographic names remain anchored to the map; subtitles remain in screen space.

### Global context and territory framing

Establish the story on a recognizable global/contextual map before entering local detail. Frame the relevant countries or territories together, with their readable outlined/colored land and geographic labels; then connect the overview to regional action through continuous camera movement. When moving to a different theater or country, reestablish the wider geographic relationship before its detail. Preserve territory layers during these moves under the persistence contract below.

Every shot must retain geographic orientation through the treated territory, relevant labeled places, a recognizable boundary/coastline or a clear visual connection to the established overview. Avoid a sequence composed only of tight satellite-ground textures with tiny city pins and route marks. Fit the active territory or meaningful boundary/context into the framing when the close view would otherwise lose its identity. Regional battle graphics still need this map context; a PDF's city-level storyboard is not an instruction to omit surrounding territory treatment. Follow explicit user framing exceptions when supplied.

Before a full production render, inspect an overview and the tightest representative detail at the retained delivery profile. Confirm that location and highlighted land remain recognizable, action is prominent, and the overview-to-detail relationship reads. Reuse valid existing samples; this is not a reason to render another full video. Appearance values remain owned by `defaults.json` and [style.md](style.md).

Plan arrival against actual recorded phrase timing: the intended place should already be recognizable when it is named or the relevant claim is made. Start travel slightly before that phrase when necessary, while preserving the preceding clause's geographic meaning. Do not reveal the next destination so early that it misrepresents the current narration. Pre-roll and arrival remain authored keyframes, not an automatic speech-alignment feature.

Use smooth acceleration into travel and deceleration into focus. Combine push-in and contextual pullback when they help the route read; do not force a zoom reversal on every phrase. Keep important locations and labels inside the frame, allow time to read on arrival, and avoid sudden jumps, velocity changes or long delayed moves. Gentle drift on a hold is optional when it improves the shot. End by widening to the relevant geographic context; do not always choose the same country.

Working parts must assemble as one flowing scene. Match boundary poses, movement direction/velocity, zoom, rotation, persistent layers, effect phase and audio placement. Do not insert black gaps or visible stops at clip joins. Narration can cross a visual part boundary. Trim unnecessary silence after the final spoken word while allowing a natural release/fade.

## Geography and evidence

Keep thematic fill, focus emphasis and ownership state separate. Define topic-relevant persistent color/flag layers over their intended story interval, independent of which territory the camera currently discusses. A focus change alters outline emphasis without switching those fills off and on. Preserve a completed reference outline outside focus when needed; see the reveal contract in [scene-format.md](scene-format.md).

For an ownership change, choose the verified narrative event and author old/new fill visibility on the shared source clock. Keep unrelated territory layers persistent, and avoid blank frames, accidental double fills or premature changes. Do not change ownership merely because the camera enters/leaves a region. The renderer has no automatic ownership state machine: a bare phrase `event` on a region limits it to that phrase's interval. Persistent layers need explicit lifetimes extending until the next intended state change; world overlays and nested focus cues use explicit source times. Project colors, historical dates and transition timing belong to the production.

Use compatible country/province geometry and a deduplicated shared-line network; avoid parallel coastlines from differently detailed sources. Fit geographic endpoints when a route needs both visible. Inspect coast/island preservation and projection seams. See [scene-format.md](scene-format.md) for the flat renderer's limits.

Routes and arrows must express a specific relationship in the spoken clause. Verify source and destination coordinates and ensure the head reaches the intended land/point rather than a nearby ocean or neighboring territory. Author curved geographic samples when a curved arrow helps. Reveal from source toward destination, hold the completed route long enough to read, and remove/fade it when its meaning ends. Do not present an illustrative relationship as a researched physical journey, invasion or transfer route. The head, trail and glow must share the same timing and geographic transform.

Use actual observations/coordinates when claiming a measured distribution. Match source periods rather than altering points to resemble an undated reference image. Distinguish observations from unique events and accumulate repeat detections only with clear description. Keep allegations, established findings and illustrative markers distinct.

## Vehicles, effects and imagery

Vehicles follow meaningful paths, face their direction of travel, remain on appropriate terrain and fade as complete layers including rotor/shadow/trails. Multiple vehicles may have different headings and motion, but do not invent factual deployment counts/positions. Fixed-camera 2.5D sprites support yaw changes, not arbitrary 3D orbits.

Anchor smoke/fire and similar effects geographically. Scale them down during pullbacks and keep the map readable; illustrative effects do not establish measured coverage. Use only relevant layers, not a fixed inventory for every topic. Asset requirements and implementation coverage are separate; see [assets.md](assets.md).

Photographs must relate to the spoken phrase, retain real archival dates/credits in project `SOURCES.md`, and use clean originals without removing watermarks. Apply the documentary archive and reconstruction contract in [assets.md](assets.md). Place them in restrained connected image/bubble compositions, image-only by default. Add captions/context only when explicitly requested and enabled through root scene `text_policy`; do not promote archive metadata into visual text automatically. Preserve context rather than assigning a generic archive image to an unsupported location/event.

## Production workspace

Keep source scene JSON, project renderer extensions, assets and licenses, approved narration, separate VO/music/SFX, editable subtitle cues, actual phrase timing, render/export settings and revision metadata together. Use relative asset paths in portable source bundles. Raw reference clips may retain geographic labels but must be identified if captions/audio are baked in; do not treat a finished MP4 as editable source. Final export uses the delivery reference.

## Executable composition contract

The generic renderer applies `composition.py` and `scene_layout.py`. Numeric limits, margin, gap, movement speed, stability weight, coverage budget and fallback focus live in `defaults.json` → `composition.layout`. A scene may override those named keys through its `composition` object when the brief justifies the change; never change the preset silently to make a failed render pass.

Declare the geography currently being discussed with `focuses`:

```json
{
  "regions": [{"id": "spoken-region", "geojson": "data/region.geojson"}],
  "focuses": [{"event": "location-phrase", "region_id": "spoken-region"}]
}
```

Alternatively a focus has `bounds: [west, south, east, north]` and source-clock `start`/`end`. Use a region ID **or** bounds, not both. Event IDs resolve through the shared phrase timeline. Region IDs must be unique and reference actual selected Polygon/MultiPolygon geometry. An active focus outside the camera view fails; correct the authored framing/timing. Split antimeridian geometries explicitly. Focus protection uses conservative projected bounding rectangles, including holes/sea inside those rectangles; it does not claim exact land occupancy or render another visible highlight. When no focus is active, the preset central screen reservation protects the camera's composition without inventing a geographic location.

Callouts measure actual text/fonts and keep image ratio, then prefer their geographic anchor plus `offset`. `placement: "auto"` chooses feasible space within margins, outside focus, subtitles, enabled visual credits, visible titles/labels, other panels and map-symbol footprints. Evidence photos are placed before supporting panels; all requested panels must fit. `placement: "manual"` keeps the authored position and still checks constraints. No evidence, text or effect is removed, rewritten or reduced in size to satisfy limits.

Positions are planned from output frame zero for every segment. Tracking is bounded by preset speed and favors stable placement; inactive panels release their positions. This preserves the same positions during checkpoint/resume and avoids abrupt corner switches. If a moving focus blocks every continuous path, rendering fails at the precise frame/output/source time; revise framing, timing or explicit panel size. The planner does not rewrite the camera. Inspect actual motion for readability even when constraints pass.

An explicitly requested `cta` requires `text_policy.extra_annotations: true`. Its object has only authored `text` and source `start`/`end` or `event`. It uses preset display font, CTA color, maximum lines and stroke, with no frame or additional decoration. The preset CTA area supplies text width; vertical placement follows the protected geography rather than covering it. Unsupported CTA style/anchor fields fail instead of being ignored. The planner keeps it horizontally centered, prefers space directly above the protected geography and falls back to other clear vertical space. It never inserts a stock question or country name. A closing pullback remains authored by camera keyframes and the chosen geographic focus; no country or zoom move is generated automatically.

The planner enforces simultaneous callout/media/marker/route/title counts and an annotation area budget. Area is a conservative sum of panel/text and visible symbol rectangles, not an exact union or opacity measurement. Routes use the same path pose for rendering and sprite footprints. Atlas padding counts toward a sprite's footprint; use suitably prepared original assets and scaling. Map symbols may share geographic space with each other, but panels avoid them and they cannot cover subtitle/enabled-credit reservations. Route trails/glow and custom smoke/fire effects still need visual inspection; custom effects must supply their own footprint/coverage checks through the project compositor or adapter. The generic renderer does not implement those effects or silently replace their compositor.

Visible marker labels, titles, enabled callouts/CTA, subtitles and enabled attribution are checked for mutual rectangle collisions. Related icon/label layout remains authored. Title 01 retains its explicit layout; move/re-time it when it obscures protected geography. Title telemetry measures the rendered alpha rectangle, so clipping that occurs inside a title component still needs manual review. Subtitle reservations include actual maximum line/font bounds; the preset subtitle anchor is not misread as the bottom of every glyph.

`.layout.json` records global frame numbers, panel positions and protected focus rectangles. Checkpoint assembly retains this trace. Pipeline contact sheets include authored focus/media/title/CTA boundaries as well as phrase/segment samples. These diagnostics support agent review; they do not verify geography, archival context, visual balance or speech by themselves.
