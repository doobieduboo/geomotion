---
name: geomotion
description: Create and edit topic-agnostic geographic animation and map motion graphics from a user's brief. Save active projects, reuse valid renders, and deliver compact previews or native finals as direct MP4 links without imposing any topic, country, date or duration.
---

# GeoMotion

Use the current brief and project sources. Examples are structural placeholders, not story defaults. Apply the user's established preferences without asking them to repeat details.

A short brief such as “outline”, “daratan diwarnai” or “bendera” uses the current defaults for routine appearance and delivery. Inherit the matching thin reference/focus outline roles, additive bloom, terrain-preserving color tint and factual geographic flag treatment from the preset and relevant reference. Author locations/timing from actual story inputs, choose a contrasting focus alternative when needed, and ask only for missing information that materially changes the result. Do not copy a second style preset into every scene or require a detailed invocation checklist; shortcuts, when requested, route into this same workflow. Keep locations, coordinates, assets and ownership states in the production. Fresh conversations need the updated checkout or installed skill; a local change alone is not a remote update.

## Load only what this task needs

Always load `defaults.json`. Use [references/README.md](references/README.md) as the knowledge index; do not read every reference on every turn.

| Task | Reference |
|---|---|
| Active-project save/load, revision reuse, checkpoints, timing, manifests and pipeline | [pipeline.md](references/pipeline.md) |
| Scene JSON, coordinate/projection behavior | [scene-format.md](references/scene-format.md) |
| Satellite source, licensing and download failures | [basemaps.md](references/basemaps.md) |
| Editable title assets and title preview | [titles.md](references/titles.md) |
| Topic-only terrain tints, additive outline bloom, typography and placement | [style.md](references/style.md) |
| Fast-paced Shorts delivery and information rhythm | [retention.md](references/retention.md) |
| Phrase-aligned camera arrival, persistent fills, ownership changes, routes and continuity | [composition.md](references/composition.md) |
| Historical geography, integrated geographic flags/emblems, archives, reuse and sprites | [assets.md](references/assets.md) |
| VO generation or access/quota errors | [tts.md](references/tts.md) |
| Audio mixing, subtitle edits and final checks | [quality.md](references/quality.md) |
| Publishing direct MP4s or an explicitly requested player | [delivery.md](references/delivery.md) plus the Sites skill |
| Environment, stale settings, output or data failures | [troubleshooting.md](references/troubleshooting.md) |

## Production workflow

For new topics and supplied storyboards, apply [required territory treatment](references/style.md#required-territory-treatment) and [global/contextual framing](references/composition.md#global-context-and-territory-framing) as part of scene authoring. Inspect a contextual overview and the tightest detail before full rendering. The preset styles authored geometry; it does not discover or create territory polygons from a topic automatically.

1. Inspect the environment, applicable instructions, current repo/skill revision and existing project inputs. Load the active production's saved state, approved delivery stage, assets and completed renders before planning another render; follow the save/load and revision-reuse workflow in [pipeline.md](references/pipeline.md#active-project-save-and-load). When updating an active conversation, sync the checkout safely and reread changed preset/references; do not reuse a stale installed copy. Apply changed rules to the active source scene/scripts while preserving approved content and audio. Resolve package paths against the skill and asset paths against the scene. A repo checkout does not attach its cloud environment or credentials.
2. Translate the brief into content, geography, duration, camera and optional layers. For documentary evidence, follow [assets.md](references/assets.md): prioritize authentic archives, distinguish factual verification from reuse status, and record sources, dates, credits, reuse basis or uncertainty, and limitations in the production's `SOURCES.md`. Missing written permission alone is not an automatic exclusion rule. Ask only for essential missing input.
3. If narration is needed, use `audio.tts` from the preset and follow the TTS reference. Preserve approved wording/voice/audio; do not generate new speech for visual-only edits. Determine actual phrase timings before driving the camera and subtitle cues.
4. Compose a source scene from `templates/scene.json` and actual assets. Use Esri World Imagery as the only basemap; read references/basemaps.md for map creation and Esri use/credit requirements. Other providers and solid vector backgrounds are prohibited; report request failures without fallback. Apply the map-documentary text policy from defaults.json and style.md: imagery/map action carries the scene; VO and phrase subtitles explain it. Do not turn the narration into paragraph cards or bullet slides. Apply the fast-paced editorial preset without sacrificing voice clarity, geographic context or reading time. Keep the map dominant, geographic anchors correct and camera movement aligned with the narrative. Match adjacent parts as one continuous scene. For generic scenes declare phrase-timed `focuses`, use automatic panel placement and the preset density/coverage limits, and supply optional CTA wording explicitly; follow the executable contract in [composition.md](references/composition.md#executable-composition-contract). Do not hide evidence or alter camera/content to bypass failed composition checks. Consult style references where needed.
5. Implement any missing production step honestly. The generic renderer does not automatically generate TTS, mix stems, author CTA wording or simulate arbitrary effects. Compose those with verified project scripts or an appropriate supported tool; see [capabilities.md](references/capabilities.md).
6. Keep the editable composition as the authoritative project and treat exported MP4s as derived deliverables. Load its saved state first, then follow the [composition-first edit decision](references/pipeline.md#composition-first-edit-decision): determine affected layers/time ranges, inspect existing cache/clean-base evidence and choose the smallest supported operation before rendering. Inspect position, scale and narrative meaning in representative frames or a short affected-range sample at the retained delivery profile; reuse an already approved sample while its dependencies remain unchanged. For generic initial previews, use `scripts/pipeline.py run SCENE.json --output outputs/preview.mp4 --checkpoint CHECKPOINT_DIR`; follow [pipeline.md](references/pipeline.md) for revision reuse, timing, manifests, locks and interruption recovery. Preserve custom project compositors until an explicit compatible adapter exists. The direct renderer remains available for individual range checks. Use the preview profile before final is requested; after final, retain the final profile under [delivery.md](references/delivery.md). Preserve project sources, separate stems, editable cues and usable completed segments. Do not start a full render merely because a scene file changed, and do not invoke rendering or asset generation for a discussion, status request or rules-only edit.
7. Record actual visual/fact/audio review bound to the current inputs and encoded bytes. Deliver a direct MP4 by default under [delivery.md](references/delivery.md) and the direct-delivery contract in [pipeline.md](references/pipeline.md#direct-mp4-delivery-default), using the configured hosting and native Sites publication workflow. The bundled `pipeline.py prepare`/`handoff` path prepares a player; use it only when a player is requested. Custom compositors/direct delivery need equivalent verified staging and exact-commit provenance, not invented generic pipeline receipts. Preparation alone is not publication. Return the verified MP4 URL and material limitations.
8. Final export requires an explicit user request; that authorization persists for subsequent revisions of the same active production unless the user changes stage. Pass `--mode final --final-requested` for final scene rendering. Render newly required frames from source geometry, original assets/effects and native text, retaining verified unchanged native segments when compatible. For additive revisions prefer compositing over a saved compatible native base. Encode compact; never upscale preview frames or create a master by default. Verify and publish the current-stage MP4 on the same hosting, returning its direct file URL. Derive extra qualities or prepare a player only when requested.

## Implementation entry points

- `scripts/pipeline.py`: save/load workspace, revision reuse, additive native composition, checkpoint render/QA/review and Site handoff; see [pipeline.md](references/pipeline.md).
- `scripts/project_workspace.py` owns the single workspace record; `project_state.py` owns source hashes/approval; `revision_cache.py` owns conservative range dependencies; `execution.py` owns generic segment reuse/render/assembly; `compositor.py` owns additive native overlays. Keep these responsibilities separate.
- `scripts/render_scene.py`: scene-driven flat Web Mercator renderer, geographic layers, camera, optional supplied audio.
- `scripts/effects.py`: shared terrain-preserving land tint and linear-light additive bloom; `region_stroke.py` owns reference/focus reveal geometry and matching thin cores.
- `scripts/map_assets.py`: polygon flag clipping, fluttering flagpole and multi-angle atlas selection using supplied assets.
- `scripts/prepare_delivery.py`: verify input size/fps, prepare stage-specific files and `media.json`, reuse `templates/player/`; no hosted deployment.
- `defaults.json`: production settings; some fields guide agent composition rather than executable renderer features.
- `delivery-target.json`: this user's replaceable Site binding, not story content or authorization for other audiences.

Install `scripts/requirements.txt`; FFmpeg and bundled fonts must be accessible. This toolkit is a flat map, not a 3D globe or Blender workflow. Rendering requires execution tools. Skill installation and credentials are environment-specific; follow the getting-started/troubleshooting documents when a new session cannot access them.
