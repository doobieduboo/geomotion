# Map appearance and typography

Read [defaults.json](../defaults.json) for fonts, palette, design grid, subtitle safe area and CTA area. These values are the canonical preset; use normalized regions as starting positions, then resolve actual collisions in rendered frames.

The map dominates. Use Esri World Imagery as the only basemap; retain its original brightness/color by default. Overlay real geometry and restrained border glow. Labels/pins stay attached to coordinates during camera moves. General and focal borders use different preset colors unless the content needs another palette. Deduplicate overlapping boundary networks; detailed behavior is in [composition.md](composition.md).

Use the bundled display face for short purposeful titles/CTA, bold reading face for geographic labels/subtitles, and regular face for supporting text. Do not substitute fonts silently. Scale typography, strokes, offsets and graphics from the design grid to the output resolution. The internal design-grid width is not a delivery resolution.

Use the preset's map-documentary composition and text policy. Tell the story through geographic focus, moving camera, meaningful map layers and relevant archival imagery. VO and phrase subtitles carry the explanation. Extra text is limited to brief location labels, a key figure, a short evidence/photo caption or an optional CTA; do not repeat a spoken sentence as a separate card above its subtitle.

Do not build presentation slides, paragraph cards, bullet lists, repeated chapter-title screens or a persistent headline. Cards and infographic bubbles are optional: use one only when a specific fact needs it, keep its wording brief and remove it when that phrase ends. Sources, dates and attribution remain accurate and readable; put extended methodology/source notes in delivery credits rather than turning the frame into a report. Required on-video credits must remain visible.

If a shot feels empty, add relevant imagery, geographic action or measured layers when supported by the story; do not fill it with more text. Keep camera motion restrained and information readable. A contextual hold is valid. The toolkit does not invent missing archival assets or facts to make a frame look busy.

CTA is optional: use a concise relevant question when it fits the brief, place it over the map and reserve the subtitle area. No default hashtag/slogan. Subtitle placement follows the preset and [quality.md](quality.md); the safe area is not permission to cover another label/card.

Keep the clean aesthetic while complying with actual source/license attribution. Use minimally intrusive required credit or choose a compatible replacement asset; source records alone do not waive attribution requirements. Flag and multi-angle sprite contracts are in [assets.md](assets.md).
