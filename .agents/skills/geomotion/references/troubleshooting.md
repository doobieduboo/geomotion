# Troubleshooting from observed state

| Symptom | Check / next action |
|---|---|
| Repo opens, but TTS key is missing | Check the session's selected environment and current `environment_status`; a repo cannot attach a different cloud environment. Choose the published configured environment at conversation start if necessary. |
| Key value looks like a placeholder | Network secrets can be proxy-substituted. Check current readiness and use the normal HTTPS header; do not dump secrets or declare failure from the placeholder alone. |
| Key ready, HTTP request fails | Diagnose the actual HTTP/model/quota error and allowed destination. Read [tts.md](tts.md); do not switch model/provider or billing automatically. |
| A new chat follows old rules | Check repo HEAD, installed skill copy and published environment version. Sync safely; opening an old checkout does not fetch new rules automatically. |
| Finished MP4 cannot be edited cleanly | Restore source scenes/assets and separate audio/cues. Burned subtitles and mixed audio are not editable source. See [composition.md](composition.md). |
| A region looks sparse compared with a reference | Compare source period, confidence filters, coordinates and observation/event counts. Do not invent or shift points to match an undated picture. |
| Parallel/coincident outlines | Compare dataset geometries and duplicate region/country/coast layers; deduplicate compatible shared linework rather than hiding with thick glow. |
| Subtitles overlap cards, map labels or CTA | Inspect affected frames, then adjust those cue/element positions within the composition. Preserve horizontal centering and approved timing/text. |
| App file link times out | The message does not prove a bad user connection. Prefer the configured Sites player's compact file/browser download; verify publication and media paths. Do not create a master or third resolution as a workaround. |
| Player still shows an old revision | Check current `media.json`, stage, file existence, revisioned URLs and actual deployed commit/version. Preparation is not deployment. |
| Only 360p appears during editing | Expected. Final options become available only after final is requested, rendered and published. |
| Browser/tool QA unavailable | Report the specific limit; run applicable file/syntax/media checks. Do not claim a browser was tested or a publication succeeded without evidence. |

Read [the knowledge index](README.md) for focused follow-up; project-specific failures and sources stay with the project. Do not copy private credentials, transient errors or conversation transcripts into reusable knowledge.
