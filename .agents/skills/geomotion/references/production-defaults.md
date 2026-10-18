# Persistent production defaults

Use `../defaults.json` for every new project unless the user overrides a setting. Keep the skill universal: no default country, topic, dates, narrative, vehicles, photographs, fire effects or fixed duration. Do not ask the user to reconfirm established preferences.

## Typography and composition

- Display/CTA: bundled Montserrat ExtraBold 800. Optional italic emphasis for a brief CTA; do not apply italics to all text. Existing approved compositions keep their font unless a change is requested.
- Subtitles and geographic labels: bundled Open Sans Bold 700. Supporting text/credits: Open Sans Regular 400. Never silently substitute a different font if the bundled files are available.
- Use a 720-wide design grid; scale every font, stroke, offset and graphic with output size. Subtitle starting size 44 design pixels (22 at 360p), dark 4-pixel outline, white text; adjust to fit and inspect on a phone-sized frame.
- Subtitle safe rectangle: x7–93%, y68–77% of frame. Center horizontally at x50%, with the bottom anchor around y77%; do not push subtitles to the screen bottom or shift the text column left. Two lines maximum, usually 3–5 words per cue, breaking by meaning. A long name may need a different grouping. Keep clear of platform controls, credits, labels and cards.
- CTA is optional and follows the brief. Use a short question when appropriate, placed over the map around x10–85%, y43–65%, at most two lines. Never occupy the subtitle band. No automatic hashtags or slogans. Avoid obscuring the geographic focus.
- Map dominates. White text, cyan general boundaries, amber focus, restrained glow. Context can override colors; avoid confusing hazard markers with decorative effects.

## Camera and layers

Follow verified narration word/phrase timings: show geographic context before a named region; start its focus move at the relevant phrase, never several seconds early. A brief hook push-in followed by a quick contextual pullback is an option, not a compulsory sequence. Maintain gentle pan/zoom/rotation during longer holds without distracting from the story. End by widening to the relevant geographic context; do not automatically choose any particular country.

Parts are working units, not visible slide breaks. Match camera position, zoom, rotation, motion direction, persistent layers and effect phase across boundaries. Assemble VO on a continuous master timeline; trim excess silence after the last word while allowing a natural release/fade.

Deduplicate shared boundaries. Use compatible geometry for country/province coastlines; do not stack slightly different outlines. Vehicles follow meaningful paths, face their travel direction, remain on appropriate terrain and fade as a complete layer including rotor, shadow and attached effects. Use region-specific quantities only when the content supports them. Smoke/fire and other illustrative effects remain geographically anchored and scale down during pullbacks; do not imply measured coverage from an illustrative effect.

Photographs are optional, source-verified, relevant to the phrase and dated when archival. Choose clean original media; do not remove watermarks. Keep actual credits/licenses. Use restrained connected bubbles or concise captions rather than unrelated presentation panels.

## Voice, music and subtitles

For Indonesian narration, use Google Gemini TTS with the exact pinned model **`gemini-3.8-flash-lite-tts`**. Read `tts.md` and `defaults.json` → `audio.tts`. No automatic model/provider fallback or paid usage. Reuse the project-approved voice/style and cache approved audio, especially during visual-only edits. Edge/Ardi stems are legacy references, not the current default. Check pronunciation, pauses and actual audio timings; preserve approved wording.

Make VO prominent: target approximately -13 LUFS integrated on the isolated speech program, then mix with final true peak at or below -1.5 dBTP. Treat these as measured targets, not unconditional +3 dB gain; avoid clipping or crushing dynamics. Keep music about 20–26 dB below active voice, ducking with roughly 20 ms attack / 250 ms release where useful. Check intelligibility at low phone volume, master loudness and peaks after encoding. Do not boost the music together with quiet speech.

Subtitles default ON for narrated productions. Derive cues from actual word boundaries/recording and map any silence cuts or delays onto the master timeline. Use phrase-level cues, no bouncing word-by-word karaoke. Preserve exact approved wording AND authored punctuation: commas, periods, question marks and exclamation marks as the sentence requires. Do not put a period after every cue; cues may continue one sentence. Capitalize the first word after . ? ! and preserve proper names/acronyms. Do not capitalize every continued cue or add sensational exclamation marks. Restore punctuation from the approved script rather than relying on raw TTS WordBoundary tokens. Compare the joined cues against that script before rendering; adjust line breaks rather than compressing or inventing speech. Prevent overlaps, screen-edge clipping and CTA collisions. Silence does not need text. Keep the editable cue file beside the project.

## Export and implementation boundary

Preview 360×640 / 24 fps; final 1080×1920 / 30 fps only when requested. Only 360p and compact native 1080p are included in the standard player/export workflow. H.264/yuv420p, AAC and faststart. Inspect representative frames, cue timing, transitions, dimensions, fps, duration, audio and decode before delivery.

The generic renderer reads export dimensions/fps and regular/bold font paths directly from `defaults.json`; a scene can override `export.preview` or `export.final`. The remaining preset fields guide the production workflow. Subtitle composition, speech generation, loudness normalization/ducking, display typography and custom effects require their own implemented/verified composition step; they are not automatically rendered by adding those fields to scene JSON. Do not claim a production feature exists until implemented for that output.

## Compact export and delivery stages

Follow `delivery.md`: editing is 360p only; native final is compact 1080p only when requested. Do not create a master export by default. Update the reusable Sites player after verification, with stage-appropriate qualities and one download action.
