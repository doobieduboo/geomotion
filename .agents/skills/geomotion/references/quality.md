# Audio, subtitle and output verification

Use numeric targets from [defaults.json](../defaults.json); this page describes how to apply and check them. Generate speech under [tts.md](tts.md), and use [delivery.md](delivery.md) for stage/export rules.

## Mixing and subtitles

Keep approved VO/music/SFX as separate stems. Measure isolated speech loudness, mix with the preset music offset/ducking, then check encoded deliverable true peak and intelligibility at low phone volume. Loudness targets are measured outcomes, not an unconditional gain boost. Avoid clipping/crushing dynamics or raising music together with quiet speech.

Subtitles default on for narrated productions. Build phrase-level cues from actual recording/word boundaries, including any silence cuts, delays and cross-part offsets. Re-align when VO changes. Preserve the exact approved script and punctuation; capitalize after sentence-ending punctuation and retain proper names/acronyms. A cue can continue a sentence: do not add a period or capitalize merely because a new cue starts. Do not add sensational exclamation marks or bouncing word-by-word karaoke.

Use the preset line count, font role, word-group range and centered safe area. Break at natural phrase boundaries, adapting long names for fit. Resolve label/card/CTA collisions by inspecting the actual frames; move only affected elements/cues when appropriate. Silence needs no caption. Keep the editable ASS/SRT and cue/timing metadata.

For fast-paced edits, also inspect opening clarity, voice articulation, visual information beats and reading time using [retention.md](retention.md).

## Before delivery

- Verify dimensions, frame rate, duration and audio presence with ffprobe; decode a new assembled deliverable to the end.
- Check that the scene reads as a map documentary: no paragraph/bullet slides, no duplicate narration cards, and no persistent headline crowding the map.
- Inspect representative frames and all changed/problem areas: boundaries, clipping, title/card/subtitle overlap, geographic anchors, sprite heading and effect scaling.
- Verify VO, subtitle words and named-location camera beats agree, including the final word and audio tail.
- Check documentary archives against [assets.md](assets.md): factual support and reuse status are recorded separately, credits match active media, reconstructions are identified, and approved evidence has not been silently removed or replaced.
- Inspect joins for matching camera/layers/effect phase, smooth motion and no black gaps. Check source-to-output offsets rather than assuming concatenation is seamless.
- Measure encoded loudness/true peak after audio-affecting changes. Reuse already verified audio when only pixels changed, checking the assembly retained timing.
- Confirm stage-appropriate media files and one download action; report unavailable browser QA or other material verification limits. A script exit code alone is not visual QA.

Scale verification to the change. Do not repeatedly run expensive full renders or regenerate TTS for documentation/UI edits. Preserve provenance and reproducible settings alongside the production.
