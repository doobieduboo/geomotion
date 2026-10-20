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
| Checkpoints, unified timing, archive manifest, revision locks and pipeline | [pipeline.md](references/pipeline.md) |
| Scene JSON, coordinate/projection behavior | [scene-format.md](references/scene-format.md) |
| Satellite source, licensing and download failures | [basemaps.md](references/basemaps.md) |
| Editable title assets and title preview | [titles.md](references/titles.md) |
| Map appearance, typography and placement | [style.md](references/style.md) |
| Fast-paced Shorts delivery and information rhythm | [retention.md](references/retention.md) |
| Camera/narrative timing, part continuity and layer behavior | [composition.md](references/composition.md) |
| Documentary archives, reuse assessment, AI reconstruction, flags, sprites or geographic data | [assets.md](references/assets.md) |
| VO generation or access/quota errors | [tts.md](references/tts.md) |
| Audio mixing, subtitle edits and final checks | [quality.md](references/quality.md) |
| Preparing or publishing the media player | [delivery.md](references/delivery.md) plus the Sites skill |
| Environment, stale settings, output or data failures | [troubleshooting.md](references/troubleshooting.md) |

## Production workflow

1. Inspect the environment, applicable instructions, current repo/skill revision and existing project inputs. When updating an active conversation, sync the checkout safely and reread the current preset/references; do not reuse a stale installed copy. Apply changed rules to the active source scene/scripts while preserving approved content and audio. Resolve package paths against the skill and asset paths against the scene. A repo checkout does not attach its cloud environment or credentials.
2. Translate the brief into content, geography, duration, camera and optional layers. For documentary evidence, follow [assets.md](references/assets.md): prioritize authentic archives, distinguish factual verification from reuse status, and record sources, dates, credits, reuse basis or uncertainty, and limitations in the production's `SOURCES.md`. Missing written permission alone is not an automatic exclusion rule. Ask only for essential missing input.
3. If narration is needed, use `audio.tts` from the preset and follow the TTS reference. Preserve approved wording/voice/audio; do not generate new speech for visual-only edits. Determine actual phrase timings before driving the camera and subtitle cues.
4. Compose a source scene from `templates/scene.json` and actual assets. Use Esri World Imagery as the only basemap; read references/basemaps.md for map creation and Esri use/credit requirements. Other providers and solid vector backgrounds are prohibited; report request failures without fallback. Apply the map-documentary text policy from defaults.json and style.md: imagery/map action carries the scene; VO and phrase subtitles explain it. Do not turn the narration into paragraph cards or bullet slides. Apply the fast-paced editorial preset without sacrificing voice clarity, geographic context or reading time. Keep the map dominant, geographic anchors correct and camera movement aligned with the narrative. Match adjacent parts as one continuous scene. Consult style/composition references only where needed.
5. Implement any missing production step honestly. The generic renderer does not automatically generate TTS, mix stems, generate CTA or simulate arbitrary effects. Compose those with verified project scripts or an appropriate supported tool; see [capabilities.md](references/capabilities.md).
6. For generic scenes, use `scripts/pipeline.py run SCENE.json --output outputs/preview.mp4 --checkpoint CHECKPOINT_DIR`; follow [pipeline.md](references/pipeline.md) for unified timing, manifests, approval locks and interruption recovery. Preserve custom project compositors until an explicit compatible adapter exists. The direct renderer remains available for individual checks. Use the preview profile in `defaults.json`. Inspect the affected frames, geography, subtitle placement/punctuation and VO timing. Preserve project source files, separate stems and editable cues.
7. Record actual agent visual/fact/audio review with `pipeline.py review`, prepare with `pipeline.py prepare`, and use its exact-commit `handoff` plus the native Sites workflow to publish to the configured player. For custom compositors, apply equivalent checks before direct `prepare_delivery.py`. Preparation alone is not publication. Return the verified URL and material limitations.
8. Only after final export is requested, pass `--mode final --final-requested` and rerender source geometry, original assets/effects and native text at the final profile. Encode compact directly; never upscale preview frames or create a master by default. Recheck the complete output, then prepare `--stage final` and publish to the same player. Keep only the approved delivery qualities and one download action.

## Implementation entry points

- `scripts/pipeline.py`: checkpoint render, encoded QA, recorded agent review, existing Site preparation and exact-commit native publication handoff; see [pipeline.md](references/pipeline.md).
- `scripts/render_scene.py`: scene-driven flat Web Mercator renderer, geographic layers, camera, optional supplied audio.
- `scripts/map_assets.py`: polygon flag clipping, fluttering flagpole and multi-angle atlas selection using supplied assets.
- `scripts/prepare_delivery.py`: verify input size/fps, prepare stage-specific files and `media.json`, reuse `templates/player/`; no hosted deployment.
- `defaults.json`: production settings; some fields guide agent composition rather than executable renderer features.
- `delivery-target.json`: this user's replaceable Site binding, not story content or authorization for other audiences.

Install `scripts/requirements.txt`; FFmpeg and bundled fonts must be accessible. This toolkit is a flat map, not a 3D globe or Blender workflow. Rendering requires execution tools. Skill installation and credentials are environment-specific; follow the getting-started/troubleshooting documents when a new session cannot access them.
