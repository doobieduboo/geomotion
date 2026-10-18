# Camera, narrative and layer composition

Use the current narration/brief and [defaults.json](../defaults.json), not timings from an older clip.

Fast-paced production follows [retention.md](retention.md); align useful visual beats to actual speech rather than forcing constant zooms or cuts.

## Camera and continuity

Establish geographic context before a specific location is spoken; start its focus move with the relevant phrase, not seconds early. A short hook push-in then contextual pullback is an option, not a mandatory sequence. Maintain gentle pan/zoom/rotation during longer holds without distracting from the narrative. End by widening to the relevant geographic context; do not always choose the same country.

Working parts must assemble as one flowing scene. Match boundary poses, movement direction/velocity, zoom, rotation, persistent layers, effect phase and audio placement. Do not insert black gaps or visible stops at clip joins. Narration can cross a visual part boundary. Trim unnecessary silence after the final spoken word while allowing a natural release/fade.

## Geography and evidence

Use compatible country/province geometry and a deduplicated shared-line network; avoid parallel coastlines from differently detailed sources. Fit geographic endpoints when a route needs both visible. Inspect coast/island preservation and projection seams. See [scene-format.md](scene-format.md) for the flat renderer's limits.

Use actual observations/coordinates when claiming a measured distribution. Match source periods rather than altering points to resemble an undated reference image. Distinguish observations from unique events and accumulate repeat detections only with clear description. Keep allegations, established findings and illustrative markers distinct.

## Vehicles, effects and imagery

Vehicles follow meaningful paths, face their direction of travel, remain on appropriate terrain and fade as complete layers including rotor/shadow/trails. Multiple vehicles may have different headings and motion, but do not invent factual deployment counts/positions. Fixed-camera 2.5D sprites support yaw changes, not arbitrary 3D orbits.

Anchor smoke/fire and similar effects geographically. Scale them down during pullbacks and keep the map readable; illustrative effects do not establish measured coverage. Use only relevant layers, not a fixed inventory for every topic. Asset requirements and implementation coverage are separate; see [assets.md](assets.md).

Photographs must relate to the spoken phrase, retain real archival dates/credits, and use clean originals without removing watermarks. Place them in restrained connected image/bubble compositions. Preserve context rather than assigning a generic archive image to an unsupported location/event.

## Production workspace

Keep source scene JSON, project renderer extensions, assets and licenses, approved narration, separate VO/music/SFX, editable subtitle cues, actual phrase timing, render/export settings and revision metadata together. Use relative asset paths in portable source bundles. Raw reference clips may retain geographic labels but must be identified if captions/audio are baked in; do not treat a finished MP4 as editable source. Final export uses the delivery reference.
