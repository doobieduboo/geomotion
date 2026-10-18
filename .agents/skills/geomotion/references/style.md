# Map appearance and typography

Read [defaults.json](../defaults.json) for fonts, palette, design grid, subtitle safe area and CTA area. These values are the canonical preset; use normalized regions as starting positions, then resolve actual collisions in rendered frames.

The map dominates. Use Esri World Imagery as the only basemap; retain its original brightness/color by default. Overlay real geometry and restrained border glow. Labels/pins stay attached to coordinates during camera moves. General and focal borders use different preset colors unless the content needs another palette. Deduplicate overlapping boundary networks; detailed behavior is in [composition.md](composition.md).

Use the bundled display face for short purposeful titles/CTA, bold reading face for geographic labels/subtitles, and regular face for supporting text. Do not substitute fonts silently. Scale typography, strokes, offsets and graphics from the design grid to the output resolution. The internal design-grid width is not a delivery resolution.

Avoid presentation paragraphs, giant unrelated headlines, permanent date chips, compasses, scale bars and decorative source footers. Put useful dates/details inside concise connected infographic bubbles. A relevant photograph may have a short caption/date and required credit. Preserve legibility and geographic context; do not make the video a sequence of slides.

CTA is optional: use a concise relevant question when it fits the brief, place it over the map and reserve the subtitle area. No default hashtag/slogan. Subtitle placement follows the preset and [quality.md](quality.md); the safe area is not permission to cover another label/card.

Keep the clean aesthetic while complying with actual source/license attribution. Use minimally intrusive required credit or choose a compatible replacement asset; source records alone do not waive attribution requirements. Flag and multi-angle sprite contracts are in [assets.md](assets.md).
