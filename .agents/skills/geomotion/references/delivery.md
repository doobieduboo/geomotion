# Stage-aware media delivery

The user wants one reusable private Sites player, not a newly designed page per clip. Read `../delivery-target.json` for the user's binding; resolve its project ID through Sites before writing. The binding is a delivery preference, not default story content. Preserve audience and use the Sites skill for credentials, source synchronization and deployment. Credentials never belong in the repo. A missing local checkout can be restored from the existing Site; do not create a duplicate. Another user can replace the binding.

## Editing / preview

Composition, camera, VO, subtitle or asset revisions stay at **360×640 / 24fps** until final export is requested. Publish the verified revision into the player with `stage: preview`; the player shows only 360p. Do not pre-render 720p or 1080p, list unavailable quality choices, or silently show the previous final as the current edit. A request to fix the final is a 360p editing pass by default unless the user explicitly asks to re-export final.

## Final

An explicit final request authorizes **1080×1920 / 30fps**, rendered directly from scene geometry, original imagery/assets and native text/subtitle composition. Never upscale a 360p or 720p preview. Directly encode the deliverable as compact H.264/yuv420p with AAC and faststart using `defaults.json` → `export.final`. Do not first create a large master and then recompress it. Do not create or publish a master download unless separately requested. Lossy intermediate parts should be minimized; if segmentation is needed for resources, assemble only needed sources once and use the same compact delivery settings at the final encode.

After final exists, the player may offer compact **360p / 1080p** versions. Derive lower resolutions from the verified final, not new scene renders. Default selection is 1080p. There is exactly one download action following the selected quality. No separate preview/master download buttons, chunked master fetch, exposed technical metadata or placeholders for unavailable qualities.

Lower-quality playback follows `defaults.json` → `export.preview`. Use faststart, preload none and playsinline. The reusable player uses a transparent, accessible tap target for play/pause without a central play icon. Keep separate bottom controls for play/pause, elapsed/total time, mute and supported fullscreen. Its timeline supports tapping, pointer/touch dragging and keyboard seeking; seeking must not toggle playback, snap back during dragging or lose a requested position before metadata loads. Resume after dragging only if playback was active. Keep native controls as a fallback until custom controls initialize. Keep title, stage, duration, file size, quality selector, one download and credits. Do not fetch the whole file on initial page load or when merely changing metadata; media loading may begin after a playback or seek interaction. Preserve the current playback position and play/pause state on quality changes. Use revisioned filenames and no-store manifest reads to avoid stale revisions.

Check the hosted MP4's response to byte-range requests. On the first seek, the player probes `bytes=0-0`: a `206` response keeps direct playback, while a host returning the whole file with `200` is handled by buffering that response into a local Blob URL. The selected time and play/pause state survive the source change; later seeks reuse the Blob. The first seek on a host without Range support may wait for the compact file to finish downloading. Abort outdated requests and release Blob URLs when changing quality. Report unavailable browser/device QA honestly.

## Reuse, verify and publish

`scripts/prepare_delivery.py VIDEO --stage preview|final --output SITE/dist --title TITLE [--narrated] [--credits SOURCES.md]` preserves an existing UI (installs the template only when missing), checks native input resolution/fps, prepares the allowed compact variants and writes `media.json`. Use `--refresh-player-template` only for an explicitly intended UI replacement. It does **not** publish. The [pipeline](pipeline.md) adds review-bound preparation, encoded-variant QA and exact-commit handoff to native Sites tools. Call it on the verified, already compact final or the current 360p preview. Review high-motion smoke/texture legibility if bitrate settings need a justified scene-specific adjustment; a precise fixed filesize is not guaranteed.

Before publishing, complete the relevant [quality checks](quality.md). Validate the manifest stage and source dimensions. All listed files must exist. Follow Sites' source and publish workflow; return the same deployed player URL when success is verified. Do not claim the player updates automatically in an unconfigured environment: an agent must run preparation and publish steps each time. In this user's configured workflow, do that after a verified render without making the user repeat the instruction. Do not publish to YouTube or social platforms by this rule.

## Efficiency

Keep editing at 360p, use the existing player/template and manifest rather than redesigning UI, reuse unchanged approved media, and render only affected parts when appropriate. Upgrade resolution once final is requested. Prefer the cheapest checks that verify the actual risk, with one full decode of a new deliverable. Compact files reduce transfer and storage; they do not guarantee fewer model tokens, and native final rendering still has a compute cost.

Only two delivery resolutions are enabled: 360p for editing/light playback and compact native 1080p for final. Never render, derive or upload a 720p intermediate or player variant by default. The 720-wide internal design coordinate grid is unrelated to export resolutions and remains valid.

Portable raw/source ZIPs must stay below 20 MB for the user's upload workflow. Preserve editable scenes, narration, stems, subtitle cues, assets and provenance; omit reproducible exports and caches first. Verify archive integrity and actual size. This is a packaging requirement, not a claim that a universal packager exists.
