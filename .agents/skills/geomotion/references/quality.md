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
- Inspect representative frames and all changed/problem areas: boundaries, clipping, title/card/subtitle overlap, geographic anchors, sprite heading and effect scaling. For each affected camera/focus/ownership transition inspect before departure, during travel/reveal, on arrival and during the hold; include actual encoded frames, not just source geometry or a static final pose.
- Check persistent color/flag fills for flicker, blank frames, double fills, sea leakage and unintended changes as focus moves. Colored land should remain saturated with visible terrain detail, clipped internal emission and restrained edge bloom; check for pastel wash, clipped highlights and unintended global basemap tint. Historical flags must retain factual RGB and emblem design under any optional bloom. Check that a single integrated emblem stays at its geographic location and is allowed to leave a partial view. Inspect islands, dateline crossings and the closest zoom for texture seams and duplicate/misaligned boundaries.
- Check that the reference and focus have the same preset thin core width at native output, with a sharp core and restrained additive bloom. The colored focus and its bloom must grow only over the revealed boundary, suppressing the reference core/neutral halo locally without doubled edges or a second white line. Completed segments remain through the intended hold, and island paths never bridge across water. Inspect shared borders as well as individual countries; exact-ring deduplication alone does not certify a complete boundary network.
- Verify VO, subtitle words and named-location camera beats agree, including the final word and audio tail.
- Check arrival against the actual spoken clause, including any authored pre-roll; a readable destination must not arrive late or imply the next claim too early. Check arrow endpoint coordinates, reveal direction and hold. Check archive/icon/figure entrance and exit against the same clause and camera movement.
- Check documentary archives against [assets.md](assets.md): factual support and reuse status are recorded separately, credits match active media, reconstructions are identified, and approved evidence has not been silently removed or replaced.
- Inspect joins for matching camera/layers/effect phase, smooth motion and no black gaps. Check source-to-output offsets rather than assuming concatenation is seamless.
- Measure encoded loudness/true peak after audio-affecting changes. Reuse already verified audio when only pixels changed, checking the assembly retained timing.
- Confirm stage-appropriate media files and one download action; report unavailable browser QA or other material verification limits. A script exit code alone is not visual QA.

Scale verification to the change. Do not repeatedly run expensive full renders or regenerate TTS for documentation/UI edits. Preserve provenance and reproducible settings alongside the production.

For position/size revisions, inspect representative frames or a short affected-range sample before a long render, using the retained delivery profile and a phone-sized view. Judge geographic/narrative anchoring, legibility, relative scale, visual hierarchy, screen balance and entrance/exit timing together. Empty space is not sufficient reason to place an element there; a collision-free bounding box is not visual approval. Preserve approved placements/sizes unless the change affects them. For reused segments, verify the dependency/continuity evidence in [pipeline.md](pipeline.md#revision-reuse) and inspect actual encoded joins without repeating unrelated renders.

Inspect continuous playback when available to assess acceleration, deceleration and transient flicker; frame samples alone cannot establish smooth motion. If playback or listening is unavailable, record that limit and distinguish encoded-frame/source-timing checks from realtime review. Automated collision/layout reports do not certify visual stability, historical correctness or narration meaning.

For executable encoded/layout checks, checkpoint joins and review-bound delivery, use [pipeline.md](pipeline.md). Automated checks do not certify sources, archive reuse or listening quality.
