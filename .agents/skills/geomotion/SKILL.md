---
name: geomotion
description: Create, edit and render topic-agnostic map animation and geographic motion graphics. Compose camera movements, geographic shapes, region fills, borders, labels, routes, markers, flags, images, infographic callouts and 2.5D sprite layers from the user's scene requirements. Use for any topic with a geographic or spatial component, without imposing a narrative, location, country, date or duration.
---

# GeoMotion

A reusable geographic animation skill, independent of subject matter. Start from the user's requested scene and data. Do not inherit a storyline, place, era, country pair, vehicle type or duration from previous examples. A topic is content input, not part of the skill's identity.

Load `defaults.json` as the persistent production preset before composing each new scene. Apply it without asking the user to repeat choices; explicit scene/user overrides take precedence. For any TTS work, read `references/tts.md`; the model is pinned to `gemini-3.8-flash-lite-tts`, without automatic fallback or paid usage. Read `references/delivery.md` for stage-aware compact export and reusable Sites delivery. Read `references/production-defaults.md` for typography, subtitle, audio and continuity requirements. Read `references/style.md` for editable visual defaults, `references/scene-format.md` for scene composition, and `references/assets.md` when additional media are needed. Explicit user instructions override defaults.

## Workflow

1. Inspect the execution environment, available render tools, fonts and applicable network instructions. Resolve package paths relative to this skill; scene assets are relative to the scene file.
2. Translate the request into a scene: required locations/geometry, camera, duration, layers, timing and optional audio. Use only the layers relevant to the request. Do not assume that a map needs borders, flags, vehicles, photographs, dates, a narrative or voice-over. Ask only for essential missing input.
3. Obtain appropriate geographic/media data and retain provenance in a scene-specific `SOURCES.md`. Match dates when temporal accuracy matters. Follow actual source attribution requirements. Do not download unrelated example assets.
4. Compose geographic layers and camera keyframes. Prefer continuous motion and location-attached labels. Add concise connected information bubbles only where useful or requested. Keep the scene legible as the camera moves.
5. Build a scene JSON using `templates/scene.json` as a structural example. Its anonymous coordinates and labels are placeholders, not suggested content. Modify or extend the renderer when the request exceeds the existing primitives; do not present a template as a completed requested scene.
6. Render **360×640 at 24 fps** for iteration. Do not render high resolution while experimenting unless explicitly requested. Use `scripts/render_scene.py SCENE.json --mode preview --output preview.mp4`.
7. For a narrated production, apply phrase-synced subtitles and the audio targets in `references/production-defaults.md` using a verified composition/FFmpeg step. These are production requirements, not built-in JSON overlay primitives. Inspect representative frames and verify actual dimensions, frame rate, duration and audio using ffprobe. Check geographic correctness, projected borders, label clipping, sprite direction and callout readability. Prepare the current 360p revision with `scripts/prepare_delivery.py --stage preview`, then update the configured Sites player following `references/delivery.md` and the Sites skill; give its verified URL. State material limitations.
8. Only when the user requests a final export, render **1080×1920 at 30 fps** using `--mode final`. Encode the native final directly with compact delivery settings from `defaults.json`; do not create a large master first or upscale preview frames. Inspect sync/transitions/collisions/decode again, prepare `--stage final`, and publish compact quality options to the same player. Keep scene data, source files and asset metadata reproducible.

## Tools and composition

- `scripts/render_scene.py`: topic-neutral scene renderer. Camera keyframes, satellite or solid basemap, geographic border reveal/glow, flag-filled polygon regions, routes, location labels, flagpole markers, sprite-atlas route followers, image/info callouts and optional supplied audio. Nothing in the renderer dictates subject matter or timing.
- `scripts/map_assets.py`: reusable polygon flag clipping, flagpole flutter and camera-relative sprite selection.
- `templates/scene.json`: an anonymous structural example. Replace its inputs; it is not a content default.
- Supply actual image, flag, atlas, geometry and audio files only when a scene requires them. The skill does not include a universal media library.

Install Python dependencies with `python -m pip install -r scripts/requirements.txt`. FFmpeg and suitable fonts must be available. Output uses H.264/yuv420p and faststart, with AAC when audio is supplied.

## Visual defaults and limits

Default to a clean map with readable geographic layers. Avoid large presentation headlines and permanent HUD elements. These are style defaults, not mandatory features or restrictions on topics. Layer colors, labels, geometry level and imagery style can change with each request.

Use 2D layers or multi-angle 2.5D sprites without Blender by default. The renderer uses Web Mercator and a rotating flat camera; it does not implement a 3D globe or arbitrary 3D vehicle orbit. High-latitude, projection-seam and very wide multi-stop scenes may need another projection, geometry clipping or multiple shots. Do not promise universal geographic accuracy from one projection.

Procedural explosion/smoke simulation, speech generation and free camera orbits are not implemented primitives. Add suitable licensed assets or an actual implementation before claiming those outputs exist. Keep capability claims separate from future asset specifications.

## New conversations

Open the repository in the new Codex environment so `AGENTS.md` and this skill are accessible, or use the repository's `scripts/install_skill.py` to install on that machine. Invoke `$geomotion` where supported. Installation in one environment does not install it in every ChatGPT/Work session. A session without execution tools cannot promise to render an MP4.
