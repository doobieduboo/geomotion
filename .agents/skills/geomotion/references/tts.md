# Gemini TTS

Read `defaults.json` → `audio.tts` for the exact provider, model, voice, language, style, credential host and cost policy. Use those values for samples, revisions and final narration; do not duplicate model IDs or voice defaults in project prompts. No automatic provider/model/voice fallback or billing activation.

## Generate

1. Inspect the selected environment and current credential readiness through the cloud environment runtime skill. A repository checkout does not attach its environment. Proxy placeholders do not prove that a secret is missing.
2. Use the configured key in the supported API request header to the configured host. Never print/persist the key or send it to the player, frontend, archive or another provider.
3. Respect the configured free-quota policy. An API key alone does not establish billing status; use existing account evidence and authorization rather than repeatedly asking the same question. Never enable billing or purchase credits automatically.
4. Check the pinned model's current request schema. Pass supported style instructions separately from the verbatim transcript. A speaking-rate target is editorial guidance, not a guaranteed API parameter.
5. For a new unapproved voice, generate one short representative sample using the preset. Check names, articulation, tone and pace before the full narration. Preserve an already approved project voice/recording unless the user requests replacement.
6. Save the actual model ID, voice, style/settings, transcript hash, sample rate and duration alongside the WAV. Replacing speech requires new phrase/subtitle/camera timing based on the recording.

## Reuse and errors

Cache approved audio by actual model, voice, text and generation settings. Visual-only revisions reuse it. Regenerate only affected narration when feasible, preserving natural joins. Never relabel audio made by another model or assume identical text yields identical timing.

For quota errors, report the actual limit and retry guidance; respect Retry-After. Do not evade limits through other keys/projects or retry full narration repeatedly. For unavailable/unauthorized models, report the returned cause without choosing another model. Free quotas and reset behavior depend on the current account/model; they are not an unlimited service or a guaranteed monthly wallet.

Follow [retention.md](retention.md) for delivery rhythm, [quality.md](quality.md) for mixing/subtitles and [composition.md](composition.md) for camera alignment. API generation is a separate production step; the map renderer does not synthesize speech.

Verify current primary documentation before model-specific implementation:
- https://ai.google.dev/gemini-api/docs/speech-generation
- https://ai.google.dev/gemini-api/docs/rate-limits
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/terms
