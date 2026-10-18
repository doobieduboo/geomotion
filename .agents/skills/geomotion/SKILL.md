---
name: geomotion
description: Create and edit topic-agnostic geographic animation and map motion graphics from a user's brief. Compose scenes, verify media, and deliver previews or native compact finals through a reusable player without imposing any topic, country, date or duration.
---

# GeoMotion

Use the current brief and project sources. Examples are structural placeholders, not story defaults. Apply the user's established preferences without asking them to repeat details.

## Load only what this task needs

Always load `defaults.json`. Use [references/README.md](references/README.md) as the knowledge index; do not read every reference on every turn.

| Task | Reference |
|---|---|
| Scene JSON, coordinate/projection behavior | [scene-format.md](references/scene-format.md) |
| Map appearance, typography and placement | [style.md](references/style.md) |
| Camera/narrative timing, part continuity and layer behavior | [composition.md](references/composition.md) |
| New flags, sprites, media or geographic data | [assets.md](references/assets.md) |
| VO generation or access/quota errors | [tts.md](references/tts.md) |
| Audio mixing, subtitle edits and final checks | [quality.md](references/quality.md) |
| Preparing or publishing the media player | [delivery.md](references/delivery.md) plus the Sites skill |
| Environment, stale settings, output or data failures | [troubleshooting.md](references/troubleshooting.md) |

## Production workflow

1. Inspect the environment, applicable instructions, current repo/skill revision and existing project inputs. Resolve package paths against the skill and asset paths against the scene. A repo checkout does not attach its cloud environment or credentials.
2. Translate the brief into content, geography, duration, camera and optional layers. Obtain verified sources/media and record their dates, licenses and limitations in the production's `SOURCES.md`. Ask only for essential missing input.
3. If narration is needed, use `audio.tts` from the preset and follow the TTS reference. Preserve approved wording/voice/audio; do not generate new speech for visual-only edits. Determine actual phrase timings before driving the camera and subtitle cues.
4. Compose a source scene from `templates/scene.json` and actual assets. Keep the map dominant, geographic anchors correct and camera movement aligned with the narrative. Match adjacent parts as one continuous scene. Consult style/composition references only where needed.
5. Implement any missing production step honestly. The generic renderer does not automatically generate TTS, mix stems, burn subtitles/CTA or simulate arbitrary effects. Compose those with verified project scripts or an appropriate supported tool; see [capabilities.md](references/capabilities.md).
6. During editing, render `scripts/render_scene.py SCENE.json --mode preview --output outputs/preview.mp4`. Use the preview profile in `defaults.json`. Inspect the affected frames, geography, subtitle placement/punctuation and VO timing. Preserve project source files, separate stems and editable cues.
7. Prepare the verified preview with `scripts/prepare_delivery.py VIDEO --stage preview --output SITE/dist --title TITLE`, then use the Sites workflow to publish to the configured player. Preparation alone is not publication. Return the verified URL and material limitations.
8. Only after final export is requested, rerender source geometry, original assets/effects and native text at the final profile. Encode compact directly; never upscale preview frames or create a master by default. Recheck the complete output, then prepare `--stage final` and publish to the same player. Keep only the approved delivery qualities and one download action.

## Implementation entry points

- `scripts/render_scene.py`: scene-driven flat Web Mercator renderer, geographic layers, camera, optional supplied audio.
- `scripts/map_assets.py`: polygon flag clipping, fluttering flagpole and multi-angle atlas selection using supplied assets.
- `scripts/prepare_delivery.py`: verify input size/fps, prepare stage-specific files and `media.json`, reuse `templates/player/`; no hosted deployment.
- `defaults.json`: production settings; some fields guide agent composition rather than executable renderer features.
- `delivery-target.json`: this user's replaceable Site binding, not story content or authorization for other audiences.

Install `scripts/requirements.txt`; FFmpeg and bundled fonts must be accessible. This toolkit is a flat map, not a 3D globe or Blender workflow. Rendering requires execution tools. Skill installation and credentials are environment-specific; follow the getting-started/troubleshooting documents when a new session cannot access them.
