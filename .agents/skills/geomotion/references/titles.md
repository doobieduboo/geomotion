# Editable title components

Title 01 is a visual reconstruction of the supplied preview: caret/reveal, headline compaction, subtitle-panel reveal and a gentle tilt. The reference ends on a hold, so exit animation is disabled by default. It is not a binary AEP conversion or a claim of identical source keyframes. The source GIF/AEP is not needed at runtime.

## Definition

[library/titles/title-01.json](../library/titles/title-01.json) owns this component's values. It has its own schema (`schema_version: 1`, `type: title`), distinct from a map scene or Lottie document.

- `content`: editable `headline` and `subline`.
- `duration`: local lifetime in seconds.
- `layout`: normalized center, scale and maximum width relative to the canvas width.
- `style`: preset font role, colors, font sizes/condensation, panel spacing/radius, gap and tilt. Font sizes/spacing use the preset design grid. Typography is rendered from the bundled font at output size, not sampled from the GIF.
- `timing`: start/end ranges for enter, compact, subline and tilt; optional `exit_seconds` fades the complete layer. Ranges must fit inside duration. When shortening the lifetime, adjust those ranges too.

`scripts/title_layer.py` validates the definition, applies per-instance overrides without changing the source, and returns a transparent RGBA image from `render_title(config, local_time, canvas_size)`. Times outside the lifetime produce an empty layer. It is screen-anchored; it does not track a geographic coordinate.

## Standalone preview

From the skill root:

```bash
python scripts/render_title.py library/titles/title-01.json --output outputs/title-01.mp4
python scripts/render_title.py library/titles/title-01.json --text "KALIMANTAN" --subtext "HUTAN DAN LAHAN" --output outputs/title-custom.mp4
```

The default preview uses the production preview profile on a neutral background. `--background` accepts a color. The renderer also saves a transparent PNG of the settled title and a JPG poster alongside the MP4. The MP4 is an opaque preview; transparent animation is composed directly through the RGBA renderer, not extracted from this video. `--mode final` uses the final source-render profile only when the user requests final export.

## Scene integration

Add this optional field to a map scene:

```json
{
  "titles": [
    {
      "definition": "library/titles/title-01.json",
      "start": 1.0,
      "overrides": {
        "content": {"headline": "KALIMANTAN", "subline": "HUTAN DAN LAHAN"},
        "layout": {"center": [0.5, 0.43]}
      }
    }
  ]
}
```

`library/` paths resolve against the skill root; other definition paths resolve against the scene. `start` is a nonnegative scene time; animation time is `scene_time - start`. Omit `titles` for an unchanged scene. Multiple instances reuse the renderer. Inspect title/subtitle/map-label collisions and retain the map-documentary text policy; an available title does not mean every scene needs one.

The library catalog records implementation and visual approval separately. Update status only after verifying the actual component; do not mark future title styles as implemented by association.
