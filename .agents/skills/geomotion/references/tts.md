# Gemini TTS — pinned model

Use **`gemini-3.8-flash-lite-tts`** for new GeoMotion TTS. This exact lowercase API model ID is the user's explicit choice, including for short samples, revisions and final narration. It replaces the old Edge/Ardi default. Read `defaults.json` → `audio.tts` before generation.

Do not substitute another Gemini model, Pro/non-Lite variant, Edge, ElevenLabs or another provider merely because it is newer, recommended by search, present in an example, faster to configure or available after an error. A model/provider change requires an explicit user instruction. Legacy project README files and old default presets naming Edge or generic "choose an available model" do not override this rule. User-supplied recorded VO remains valid when specifically requested.

## Default voice and delivery

Read `defaults.json` → `audio.tts` and `pacing`. The default prebuilt voice is **Charon**, with fast-paced, conversational Indonesian delivery. Charon is a chosen starting voice, not a claim that it has already passed an Indonesian production audition. Reuse an already approved project voice/audio unless the user requests a change; do not replace an approved recording just because the default changed. A new project's first short sample uses Charon and the preset style. Do not randomly cycle through voices or switch when a request fails.

Pass delivery instructions through the model's supported style metadata/prompt controls separately from the verbatim transcript so they are not spoken. Preserve actual script punctuation and wording. Do not copy another provider's numeric `rate` parameter or assume Gemini supports that control. The words-per-minute target is an editorial starting range, not a guaranteed TTS parameter: measure the WAV, listen for clear articulation, names and geographic terms, and relax the pace if understanding suffers. Do not silently speed up audio in post.

Audition only a short representative phrase before spending quota on full narration for an unapproved voice. Keep tone confident and clear with varied intonation and brief natural pauses. Topic-specific sarcasm, urgency or solemnity follows the brief; do not turn every subject into sensational commentary. After approval, cache the voice/style/text/settings and actual WAV; see [retention.md](retention.md) for the complete pacing policy.

## Access and costs

Use the published `geomotion` cloud environment when available. The repository stores configuration, not credentials. Inspect `environment_status` and the current readiness of the `GEMINI_API_KEY` network secret; proxy placeholders are expected. Use the credential normally in the request header to `generativelanguage.googleapis.com`, never print/persist the actual key or send it to a browser, Sites frontend, archive or Git. Use the cloud environment runtime skill for access diagnostics. If a session uses Base Environment, explain that it needs the configured environment; opening the repository alone cannot attach its credentials.

Respect the user's free-quota policy. Confirm the selected model is available under the project's free tier; never enable billing, purchase credits, or switch to paid usage automatically. Having an API key does not prove the project is free-tier. Hosted Gemini does not require a user-operated TTS model server/GPU. API integration is a separate audio production step; the map renderer does not generate speech by itself.

Free service still has model/project request and token limits. Inspect the actual account limits and API errors. Do not describe them as an unlimited API, a guaranteed monthly credit wallet, or a universal rolling reset schedule. For 429/quota exhaustion, report the actual limit and retry/reset guidance if provided; obey Retry-After when present and avoid repeated full narration attempts. Do not evade limits with alternative projects/keys or silently switch the model. For missing/retired/unauthorized models, report the returned cause and wait for an explicit model decision.

## Generation and reuse

Reuse the project-approved voice, style and narration; log the actual requested model ID, voice, settings, text hash and audio sample rate/duration alongside the generated WAV. If a voice has not been approved, audition a short sentence rather than regenerating the whole narration repeatedly. Model pinning alone does not guarantee identical output; preserve approved audio as a file.

Cache approved audio by model ID, voice, text and generation settings. Visual-only edits reuse VO rather than spending quota again. Re-generate only affected narration when appropriate; preserve natural context and joins. Do not accidentally reuse an old Edge reference stem as the new Gemini VO.

Measure the new WAV and rebuild actual phrase timings; do not reuse old provider word times unverified. Follow [quality.md](quality.md) for subtitle/mixing checks, [composition.md](composition.md) for camera alignment and [delivery.md](delivery.md) for the current preview/final stage.

References (verify live before model-specific implementation):
- https://ai.google.dev/gemini-api/docs/speech-generation
- https://ai.google.dev/gemini-api/docs/rate-limits
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/terms
