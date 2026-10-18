# GeoMotion workspace

This is a topic-agnostic geographic animation toolkit. Read `.agents/skills/geomotion/SKILL.md`, its style defaults, scene format and asset contracts. Derive all content, locations, countries, time periods, duration and narrative from the current user's request. Do not infer a topic from repository history or anonymous template coordinates.

Compose only relevant layers. A scene can use camera movement, shapes, labels, markers, routes, fills, flags, 2.5D sprites, images, callouts and audio independently. The entry point is `scripts/render_scene.py` inside the skill, driven by scene JSON. No default story or fixed sequence.

Preview 360×640/24fps; final 1080×1920/30fps only when requested. Prefer a map-first style, no giant presentation typography or permanent HUD. These defaults are adjustable. No Blender by default.

Keep scene-specific provenance and actual attribution requirements. Keep downloaded media, caches, credentials and exports out of Git. Do not claim unimplemented capabilities or assets that do not exist. After a verified render, update the configured private Sites media player using `references/delivery.md`; this is an established user preference. No publishing to YouTube or social platforms without explicit instruction.

Load `.agents/skills/geomotion/defaults.json` and `references/production-defaults.md` in every new conversation. Preserve these production preferences without repeated questions. Subtitles default on for narrated productions; keep their safe area free of CTA and image cards. Renderer directly reads export and regular/bold font defaults; additional production settings require explicit composition/audio steps.

Editing stays 360p/24fps and the player lists only 360p. Explicit final export uses native 1080p/30fps with compact encoding directly; no master deliverable. Final player may offer compact 360p/1080p with one download action. Read delivery-target.json and reuse the existing player across topics.
