# Map appearance and typography

Read [defaults.json](../defaults.json) for fonts, palette, design grid, subtitle safe area and CTA area. These values are the canonical preset; use normalized regions as starting positions, then resolve actual collisions in rendered frames.

The map dominates. Use Esri World Imagery as the only basemap, with its preset original brightness and saturation. Add solid color or flag fills only to territories relevant to the brief; leave other land and the ocean as original imagery. Use a sharp, saturated multiply tint for ordinary colored land, retaining satellite terrain and detail instead of washing it into a pastel alpha overlay. Its subtle emission is clipped to the land mask, with a restrained colored halo outside the edge; neither effect changes unrelated territory or recolors the global basemap. Default fill blend, opacity and emission settings live in `defaults.json.region_fill`; supplied world overlays retain their authored RGB and alpha. Judge the combined result when layers overlap rather than stacking fills until the map is opaque. Geographic flag/emblem preparation is owned by [assets.md](assets.md), and layer persistence by [composition.md](composition.md).

## Required territory treatment

Topic-relevant territory outlines and land fills are the default visual foundation, including for a topic-only or PDF brief. Author geographic polygons with the preset reference border and a saturated terrain-preserving color fill; do not wait for a separate request for outlines or land coloring. A verified, period-appropriate flag may replace the color fill when requested or justified by the story. Leave unrelated land and the ocean as original imagery. Use the existing appearance values in `defaults.json`, not a copied project preset.

Select the geographic unit from the actual story: countries, historical territories or a verified regional area. City pins, route lines and schematic battle arrows supplement this territory treatment; they do not replace it. Verify historical geometry or identify modern boundaries as orientation only; never present a schematic encirclement or modern national border as a factual historical front. If suitable geometry is unavailable, report that specific gap before an expensive render. Explicit user exceptions override this default locally. Follow [global/contextual framing](composition.md#global-context-and-territory-framing) when composing the camera.

## Outlines and emphasis

Use two roles on the same geographic boundary, with equal thin core widths. The ordinary reference border uses the preset white with a compact neutral halo and is complete from region entry by default. Phrase-specific emphasis grows along that border with a saturated colored core and multilayer bloom. All numeric values live in `defaults.json.region_outline`; widths/radii are design pixels and multiply by output width / design width, independently of camera zoom. Do not copy numeric preset values into scenes, templates or reference examples.

The renderer automatically inherits `focus_preset` for an authored `focus_strokes` cue; a cue containing only its timing/reveal already receives the standard focus appearance. No copying a glow recipe into every scene is required. Default focus is red; author a listed yellow/blue `focus_color_alternatives` color when it contrasts better with the actual fill/basemap. Routine color selection does not need another user brief. Explicit scene overrides remain possible for a requested exception. Apply a requested preset revision to the active source while preserving approved content and timing; a preset update does not edit a baked MP4 by itself.

Use linear-light additive multilayer bloom for the approved deep-glow-like appearance. This is a renderer effect, not an After Effects plugin or a claim of plugin parity. Keep the core sharp while compact and wider low-gain halos provide depth. Adjust halo radius/opacity/gain independently of the core; do not thicken the line to make glow stronger. Avoid white focus glow that reads as another border. The reference remains on unrevealed portions while emphasis grows. On revealed portions, replace its core and locally suppress its neutral halo before drawing the colored focus, including coincident neighboring edges. This keeps one visible boundary rather than stacked full outlines. No dark casing is enabled by default; an explicit casing is coincident contrast edging, never a displaced geographic border.

Color/flag fills persist through camera and focus changes until the authored ownership or narrative state changes; time ownership transitions to the actual VO phrase. A flag may receive restrained bloom using its factual source colors, with its single emblem fixed geographically; never recolor a historical flag to match the focus hue.

Reveal the boundary from one authored point by path distance. Glow follows only the part already drawn, and completed portions remain through the intended hold. Disconnected islands reveal sequentially without lines across water. A traveling stroke with an erasing tail requires an explicit request and a verified implementation; it is not the default. See [scene-format.md](scene-format.md) for cue lifetime and reveal behavior.

Use compatible, deduplicated boundary geometry to avoid doubled coastlines/shared edges and inspect seams during camera movement. These are authored data and review requirements, not a guarantee that arbitrary input boundaries are automatically repaired.

## Type and placement

Use the bundled display face for short purposeful titles/CTA, bold reading face for geographic labels/subtitles, and regular face for supporting text. Do not substitute fonts silently. Scale typography, strokes, offsets and graphics from the design grid to the output resolution. The internal design-grid width is not a delivery resolution.

Use the preset's map-documentary composition and text policy. Tell the story through geographic focus, moving camera, meaningful map layers and relevant archival imagery. VO and phrase subtitles carry the explanation. Extra text is limited to brief location labels, a key figure, a short evidence/photo caption or an optional CTA; do not repeat a spoken sentence as a separate card above its subtitle.

Do not build presentation slides, paragraph cards, bullet lists, repeated chapter-title screens or a persistent headline. Cards and infographic bubbles are optional: use one only when a specific fact needs it, keep its wording brief and remove it when that phrase ends. Sources, dates and attribution remain accurate and readable; put extended methodology/source notes in delivery credits rather than turning the frame into a report. Required on-video credits must remain visible.

If a shot feels empty, add relevant imagery, geographic action or measured layers when supported by the story; do not fill it with more text. Keep camera motion restrained and information readable. A contextual hold is valid. The toolkit does not invent missing archival assets or facts to make a frame look busy.

CTA is optional: use a concise relevant question when it fits the brief, place it over the map and reserve the subtitle area. No default hashtag/slogan. Subtitle placement follows the preset and [quality.md](quality.md); the safe area is not permission to cover another label/card.

Keep the clean aesthetic while complying with actual source/license attribution. Use minimally intrusive required credit or choose a compatible replacement asset; source records alone do not waive attribution requirements. Flag and multi-angle sprite contracts are in [assets.md](assets.md).
