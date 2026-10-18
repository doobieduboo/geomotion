# GeoMotion: repository instructions

GeoMotion is a topic-agnostic map animation toolkit. Derive every story, place, date, duration and optional layer from the current brief and verified project sources. Do not inherit content from repository history or examples.

## Start here

1. Read [.agents/skills/geomotion/SKILL.md](.agents/skills/geomotion/SKILL.md).
2. Load [.agents/skills/geomotion/defaults.json](.agents/skills/geomotion/defaults.json) for production settings; read only references relevant to the task.
3. Inspect the current checkout/environment and existing project inputs before editing. Repository access, installed skill, cloud environment and API credentials are separate things.

## Working rules

- Apply established defaults without repeated confirmation. Explicit user instructions override repository defaults; higher-priority session/platform instructions still apply.
- Editing stays in the preview stage. Native final export requires the user's final request; never upscale a preview or make a large master by default. See the skill's delivery workflow.
- TTS uses the exact model pinned in `defaults.json` → `audio.tts`. No automatic model/provider substitution, billing activation or paid fallback. Read the TTS reference before generating audio; reuse approved VO for visual-only changes.
- Keep source scenes, media, narration, separate audio stems, subtitles and timing reproducible in the production workspace. Do not put production outputs, caches, secrets or downloaded topic-specific media into this reusable repo. Bundled fonts are licensed dependencies.
- Preserve geographic/date accuracy and actual attribution. Keep factual data separate from illustrative effects; never invent observations or silently treat allegations as findings.
- Verify the changed output, then update the configured private Sites player according to the delivery reference. This standing preference does not authorize YouTube/social publication or a change of audience.
- Do not claim an effect, media library, TTS integration or end-to-end automation exists unless implemented and verified. See [docs/capabilities.md](docs/capabilities.md).

## Repository maintenance

Keep numeric settings in `defaults.json`, task workflow in `SKILL.md`, and technical knowledge in `references/`. Do not add another competing `INSTRUCTIONS.md` or repeat entire workflows in agent metadata. Preserve old reference paths with short redirects when reorganizing. Keep the installer and script entry points compatible; run the checks relevant to the change. Structure and implementation coverage are documented in [docs/architecture.md](docs/architecture.md).
