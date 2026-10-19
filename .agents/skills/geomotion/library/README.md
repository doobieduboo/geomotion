# GeoMotion component library

`catalog.json` owns category IDs, folders, planned counts and the inventory status. This catalog is a planning/inventory document, not a scene schema accepted by the current renderer. Entries with an implemented definition and renderer can be previewed; `verified` also requires visual approval.

| Folder | Scope |
|---|---|
| `titles/` | Short titles, emphasis and CTA |
| `callouts/` | Pointer/leader, point and brief text |
| `media-callouts/` | Photo/video container, caption and geographic leader |
| `flags/` | Flagpole and geographic flag-fill components; country textures are separate inputs |
| `time/` | Dates, timeline and timer |
| `counters/` | Animated number and unit |
| `icons/` | Standalone symbols |
| `effects/` | Smoke, fire and animated highlights |
| `vehicles/` | Directional vehicle assets and movement behavior |
| `map-elements/` | Pins, routes, outlines, focus areas and magnifier |

Category boundaries: titles carry short emphasis; explanatory text belongs in VO/subtitles. Callouts connect information to a point, while media callouts contain a real image/video. A standalone symbol is an icon; a moving directional transport asset is a vehicle. Focus/highlight behavior belongs to map-elements; atmospheric animations belong to effects. Use categories as choices, not a checklist for every scene.

## Initial selection

Build only the nine selected components listed in `catalog.json`: Title 01 opening title, question CTA, left/right callouts, landscape/portrait media callouts, a number counter, flagpole and geographic flag fill. Call Out 01L is the received left-callout reference. The other names describe required roles, not verified filenames from the external preview pack; select their actual GIF references before development.

Time, icons, effects, vehicles and map-elements remain folder categories for later needs. They have no initial asset quota. Do not populate every category merely to complete a pack. Country flag textures are interchangeable inputs, not a new component per country. Existing toolkit primitives can support development but do not count as approved catalog assets.

## Files and locations

```text
library/
  catalog.json                 inventory and status
  CATEGORY/
    ASSET-ID.json              reusable definition, added when implemented
scripts/
  COMPONENT_RENDERER.py        shared renderer, added when implemented

External working library:
  manifest.json                local reference paths, hashes and source records
  CATEGORY/ASSET-ID/
    references/               supplied GIF, optional AEP and original media
    aep-inspection.json        inspection report when available
    inspection-frames/         extracted frames when available
    working/                   create only when development starts
    renders/                   create only when verification starts
```

GIFs show appearance and animation; optional AEP files help inspect source controls. Neither automatically becomes editable JSON. Definitions require a working renderer and declared editable parameters. Reuse one renderer across compatible variations instead of creating a new engine per asset. Keep photo/video/flag/sprite inputs separate from JSON.

Reference sources, previews and licensed third-party packages stay outside the reusable repo. Add only reusable code/definitions and assets whose terms allow repository distribution; record their actual source/license. Workspace paths are local and are not an automatic cross-chat storage service.

## Status

- `planned`: no reference or implementation yet.
- `reference_received`: preview/source available; not renderable.
- `implemented`: definition and renderer exist; visual approval pending.
- `verified`: rendered and inspected, editable controls work, provenance recorded.

Planned counts are a starting scope, not completed assets. Do not add empty renderer modules or placeholder definitions to inflate the inventory. Existing low-level toolkit helpers remain documented in [assets.md](../references/assets.md); their presence does not mean all catalog variations exist.

Call Out 01L currently has a supplied GIF/AEP and an inspection report in the external working library. Conversion and renderer implementation have not started.

## Title 01

[Definition](titles/title-01.json) uses the shared `scripts/title_layer.py` renderer. Status: implemented, pending user visual approval. Read [titles.md](../references/titles.md) for editable fields, standalone preview and scene integration. This is a visual reconstruction from a supplied GIF, not an AEP/Lottie conversion.
