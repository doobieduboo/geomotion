---
name: geomotion
description: Create or revise geographic motion graphics and vertical map videos with satellite cameras, glowing borders, flag-filled territories, flagpole markers, routes, image callouts, and multi-angle 2.5D sprites. Use for GeoLayers-style map animation without Blender, including global travel and historical stories.
---

# GeoMotion

Make the video, not only a storyboard. Read `references/style.md` first. This skill captures an established user's visual preferences; explicit new user instructions override these defaults.

## Workflow

1. Check Python, Pillow, NumPy, FFmpeg and available fonts. Inspect applicable environment/network instructions before downloads. Resolve paths relative to this skill, never a previous chat's workspace.
2. Determine the geography, dates, duration and story from the request. Continue with reasonable defaults for routine choices. Ask only for essential missing facts. Read `references/assets.md` when flags, sprites, archival images or effects are needed.
3. Verify geographic coordinates, political boundaries for the depicted date, image identity and routes. Modern data is not historical boundary evidence. Keep source, license and accuracy notes in `SOURCES.md`; display credits where a provider's license requires them. Do not remove required attribution merely for visual cleanliness; choose a compatible source or integrate the minimum required credit unobtrusively.
4. Design a continuous map camera and world-anchored layers. Prefer concise location labels and connected infographic bubbles. No slide deck layout, giant editorial headlines, persistent date HUD, compass, scale bar or explanatory footer by default. See `references/style.md`.
5. Render a lightweight **360×640, 24 fps preview** first. Do not render a 720p video while experimenting unless requested. The working renderer is `scripts/render_demo.py`; use it as an editable reference, not a generic scene engine. It currently contains the Jakarta–Rengasdengklok example. Change its coordinates, camera, routes and callouts explicitly for other stories.
6. Inspect representative frames, ensure labels stay on screen, verify the actual output's duration/resolution/fps/audio with ffprobe, and link the exported MP4. Use H.264, yuv420p, AAC and faststart. State unresolved limitations plainly.
7. Render **720×1280, 30 fps** only when the user requests the final export. Preserve source/config/assets for reproducibility.

## Working commands

From this skill directory:

```bash
python -m pip install -r scripts/requirements.txt
python scripts/render_demo.py --mode preview --output preview.mp4
# Only for a requested final export:
python scripts/render_demo.py --mode final --output final.mp4
```

A quick excerpt check uses `--start 11 --duration 1`. The reference timeline is 15 seconds; this flag selects a portion of that timeline, not a retiming tool. The first run downloads third-party demo inputs and map tiles. Inspect their source/license notes before publication; the repository's code license does not cover external assets.

## Capability boundaries

- The reference renderer implements satellite camera movement, modern provincial borders with glow, routes, moving car icon, geographic pins and connected image/info bubbles.
- `scripts/map_assets.py` provides flag clipping, animated flagpole markers and multi-angle sprite selection. Integrate these utilities into a scene before claiming a corresponding video exists.
- Worldwide map coordinates and tiled imagery are supported by the projection pattern. A true 3D globe transition is **not implemented** by this flat-map reference. Use a suitable globe renderer when specifically requested; never call a 2D pan a 3D globe flight.
- The reference has synthesized music and no voice-over. Do not claim narration was generated unless an actual audio track exists.
- No Blender by default. Use multi-angle 2D sprite sheets for a 2.5D look. A free camera orbit needs suitable views; screen rotation of one flat icon is not a multi-angle vehicle.
- This skill is not an asset library. Do not claim country flags, vehicle atlases or explosion sequences have been created when only their specifications exist.

## New conversations

Open this repository in the new Codex session so `.agents/skills/geomotion` and `AGENTS.md` are available, or install the skill on that Codex machine using `scripts/install_skill.py` at the repository root. Invoke `$geomotion` when supported. Installing it in one environment does not install it in all ChatGPT/Work sessions. Plain chat without execution tools can discuss or prepare code but cannot promise an MP4 render.
