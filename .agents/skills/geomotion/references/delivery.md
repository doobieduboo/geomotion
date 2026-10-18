# Stage-aware media delivery

The user wants one reusable private Sites player, not a newly designed page per clip. Read `../delivery-target.json` for the user's binding; resolve its project ID through Sites before writing. The binding is a delivery preference, not default story content. Preserve audience and use the Sites skill for credentials, source synchronization and deployment. Credentials never belong in the repo. A missing local checkout can be restored from the existing Site; do not create a duplicate. Another user can replace the binding.

## Editing / preview

Composition, camera, VO, subtitle or asset revisions stay at **360×640 / 24fps** until final export is requested. Publish the verified revision into the player with `stage: preview`; the player shows only 360p. Do not pre-render 720p or 1080p, list unavailable quality choices, or silently show the previous final as the current edit. A request to fix the final is a 360p editing pass by default unless the user explicitly asks to re-export final.

## Final

An explicit final request authorizes **1080×1920 / 30fps**, rendered directly from scene geometry, original imagery/assets and native text/subtitle composition. Never upscale a 360p or 720p preview. Directly encode the deliverable as compact H.264/yuv420p, `preset fast`, CRF 26, maxrate 3200k / bufsize 6400k, AAC 128k, `+faststart`. Do not first create a large master and then recompress it. Do not create or publish a master download unless separately requested. Lossy intermediate parts should be minimized; if segmentation is needed for resources, assemble only needed sources once and use the same compact delivery settings at the final encode.

After final exists, the player may offer compact **360p / 720p / 1080p** versions. Derive lower resolutions from the verified final, not new scene renders. Default selection is 1080p. There is exactly one download action following the selected quality. No separate preview/master download buttons, chunked master fetch, exposed technical metadata or placeholders for unavailable qualities.

Lower-quality playback encodes: 360p CRF28 / 650k / AAC80k (24fps), 720p CRF26 / 1800k / AAC128k. Use faststart, preload none, playsinline and native video controls. Keep title, stage, duration, file size, quality selector, one download and credits. Do not fetch the whole file on initial page load or when merely changing metadata. Preserve the current playback position on quality changes. Use revisioned filenames and no-store manifest reads to avoid stale revisions.

## Reuse, verify and publish

`scripts/prepare_delivery.py VIDEO --stage preview|final --output SITE/dist --title TITLE [--narrated] [--credits SOURCES.md]` copies the existing UI template, checks native input resolution/fps, prepares the allowed compact variants and writes `media.json`. It does **not** publish. Call it on the verified, already compact final or the current 360p preview. Review high-motion smoke/texture legibility if bitrate settings need a justified scene-specific adjustment; a precise fixed filesize is not guaranteed.

Before publishing, inspect representative frames and subtitle punctuation/case, horizontal centering, card/label/CTA collisions, audio sync/true peaks, seamless camera transitions, full-file decode and final spoken word/fade. Validate the manifest stage and source dimensions. All listed files must exist. Follow Sites' source and publish workflow; return the same deployed player URL when success is verified. Do not claim the player updates automatically in an unconfigured environment: an agent must run preparation and publish steps each time. In this user's configured workflow, do that after a verified render without making the user repeat the instruction. Do not publish to YouTube or social platforms by this rule.

## Efficiency

Keep editing at 360p, use the existing player/template and manifest rather than redesigning UI, reuse unchanged media/caches, and render only affected parts when appropriate. Upgrade resolution once final is requested. Prefer the cheapest checks that verify the actual risk, with one full decode of a new deliverable. Compact files reduce transfer and storage; they do not guarantee fewer model tokens, and native final rendering still has a compute cost.
