# GeoMotion workspace

This is a topic-agnostic geographic animation toolkit. Read `.agents/skills/geomotion/SKILL.md`, its style defaults, scene format and asset contracts. Derive all content, locations, countries, time periods, duration and narrative from the current user's request. Do not infer a topic from repository history or anonymous template coordinates.

Compose only relevant layers. A scene can use camera movement, shapes, labels, markers, routes, fills, flags, 2.5D sprites, images, callouts and audio independently. The entry point is `scripts/render_scene.py` inside the skill, driven by scene JSON. No default story or fixed sequence.

Preview 360×640/24fps; final 720×1280/30fps only when requested. Prefer a map-first style, no giant presentation typography or permanent HUD. These defaults are adjustable. No Blender by default.

Keep scene-specific provenance and actual attribution requirements. Keep downloaded media, caches, credentials and exports out of Git. Do not claim unimplemented capabilities or assets that do not exist. No automatic publishing of finished videos.
