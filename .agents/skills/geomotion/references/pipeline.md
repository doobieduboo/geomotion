# Reproducible production pipeline

`scripts/pipeline.py` orchestrates the **generic scene renderer**. Its contracts also expose reusable Python APIs for custom project renderers. Never replace an approved custom compositor with the generic renderer merely to use this command: unsupported top-level fields fail explicitly. Existing project-specific smoke, fire, camera ramps and other effects still require their compositor. Integration needs an explicit adapter, registered dependencies and equivalent QA; it is not automatic migration.

Production values remain in `defaults.json`; `execution`, `layout`, `composition.layout` and `qa` own execution limits, layout and technical tolerances. Encoding, voices, provider, fonts and audio targets are unchanged.

## One clock

`duration` is the length of the **original recording/source timeline**. Camera keyframes, layer intervals, phrase events and subtitle cues all use source seconds. Only output playback time changes after cuts:

```json
{
  "timeline": {
    "cuts": [[2.4, 2.8]],
    "audio_clock": "source",
    "events": [{"id": "spoken-location", "start": 4.0, "end": 5.2}]
  },
  "camera": [{"time": 0, "center": [0, 0], "zoom": 5},
             {"event": "spoken-location", "center": [1, 1], "zoom": 6}],
  "markers": [{"event": "spoken-location", "position": [1, 1], "label": "Location"}],
  "subtitles": [{"event": "spoken-location", "text": "Actual recorded phrase."}]
}
```

This is a fragment, not a complete scene. Event IDs must be unique; use an event reference **or** absolute timing on an item. Camera events resolve to phrase start; other layers resolve to start/end. Subtitle cues must be ordered, nonoverlapping, punctuated actual speech. Alternatively `subtitle_cues` points to a JSON array of the same cue objects. Narrated pipeline scenes require cues; alignment is not invented automatically.

`Timeline.source_time(output_seconds)` drives every rendered frame, including resumed segments. `output_time(source_seconds)` maps cue/event positions into playback; times inside a cut collapse to its join. Cuts must be explicit, ordered and nonoverlapping; the toolkit never detects silence and deletes it without editorial assessment. Source-clock audio is cut once with `atrim`/`concat`. Set `audio_clock: "output"` when the supplied approved mix already contains those edits, preventing a second cut. Keep original VO/stems separately. Updating cuts requires reviewing subtitle/camera/layer continuity. This implementation preserves source-clock animation across cuts; a cut through a moving camera can produce a jump and must be authored accordingly.

## Archive manifest and revision locks

`archive_manifest` points to a version-1 JSON file. Its `archives` array contains:

```json
{
  "version": 1,
  "archives": [{
    "id": "source-photo",
    "file": "media/photo.jpg",
    "source_url": "https://example.org/original-report",
    "credit": "Publisher / photographer",
    "publication_date": "2026-01-01",
    "date_basis": "Publication date only; capture day unknown",
    "context": "Actual event and location established from the original report",
    "fact_status": "verified",
    "reuse_status": "unknown",
    "reuse_basis": "Assessment and any uncertainty recorded here",
    "limitations": "What this image does not establish"
  }]
}
```

Dates are ISO calendar dates. Record only known capture/publication dates, distinguishing them in `date_basis`. Optional `sha256` locks original file bytes. Allowed `fact_status`: verified/unverified/rejected. Allowed `reuse_status`: licensed/public_domain/editorial_assessment/unknown/restricted. These are recorded assessments, not a legal or factual certification by software. Unknown/restricted reuse produces a warning and does not silently delete the asset. Active `callouts[].archive_id` resolves its image from the manifest and requires factual review marked verified. A conflicting explicit `image` fails. Caption and visible/delivery credits remain authored and must be checked under [assets.md](assets.md).

Register all additional production dependencies in `inputs`, grouped by `narration`, `voice`, `audio`, `subtitles`, `archives`, `data`, `visuals` or `configuration`; each value is an array of local file paths. The snapshot also collects generic scene assets, audio, cues, archive files, bundled fonts, renderer modules, actual font overrides and the current preset. Unregistered custom assets cannot be protected automatically.

After an **existing explicit user approval**, record it once:

```bash
python scripts/pipeline.py approve PROJECT/scene.json --lock PROJECT/approved.json --approval-note "Reference to the user's actual approval"
```

This records approval; it does not solicit new permission or infer consent. For an authorized visual revision, pass `--lock PROJECT/approved.json --scope visuals`. Changes in VO, subtitle text/timing, archive bytes, data or configuration then fail with a concrete domain diff. For an already authorized change in those domains, include the relevant domains in `--scope`; do not make the user approve the same action again. Timeline changes belong to `subtitles` as well as affected media. A preset/code upgrade changes `configuration`; review that diff explicitly. The snapshot is not overwritten by rendering, and approval is never auto-renewed.

## Render and resume

All paths below are examples relative to the installed skill root; keep projects outside the toolkit checkout.

```bash
python scripts/pipeline.py run PROJECT/scene.json --output PROJECT/outputs/preview.mp4 --checkpoint PROJECT/checkpoints/revision-1
```

Optional `--workers N` can lower concurrency. CPU affinity/cgroup quota and currently available host/cgroup memory constrain it further using preset estimates; these are resource estimates, not an OOM guarantee. No resolution, bitrate or provider is lowered to fit resources. Workers render native video-only frame ranges with **global frame numbers**; final assembly stream-copies video and encodes supplied audio once. No full-size master or intermediate upscale is created.

Each completed segment records a hash, layout hash and frame count atomically. Resume reruns only missing/corrupted segments; it checks dimensions/fps/decoded frame count before reuse. An interrupted segment is never a completed checkpoint. An exclusive lock prevents two processes writing the same checkpoint. Source/config/profile fingerprints must match exactly; after input changes, use a new revision directory. This is interruption recovery, not automatic partial invalidation across edits. The previous deliverable survives render failure.

Each worker fetches Esri imagery into session memory. There is no persistent tile cache, no alternate provider, and workers may request overlapping tiles. The conservative memory estimate includes duplicated mosaics. Huge mosaics can still fail the renderer's size guard; split the authored shots without changing evidence or visual configuration silently.

Final requires the user's explicit request, represented by `--mode final --final-requested`. Direct `render_scene.py` accepts the same explicit gate and frame-range/video-only flags. Never claim adding the flag supplies consent that the user did not give.

## QA and agent review

`run` emits `.render.json`, `.layout.json`, `.qa.json`, `.contact.jpg` and `.pipeline.json` beside the video. It checks native profile/frame count, full decode, presentation timestamp cadence (including segment joins), actual encoded integrated loudness/true peak, and reported callout/subtitle collisions/off-frame bounds. Callouts measure actual fonts with compact padding and preserve image ratio. Subtitle wrapping enforces preset max lines. Visible marker labels, titles, callouts, CTA, subtitles and attribution report mutual rectangle collisions. Focus protection, panel tracking, density budgets and remaining review limits follow the [composition contract](composition.md#executable-composition-contract). Silence, black intervals and optional voice-tail checks are candidates for review, not automatic proof of dead air or a bad fade. Integrated mix measurements do not prove stem ducking or speech intelligibility; inspect stems/listen when tools allow, and state limitations.

The contact sheet samples the opening, middle, ending, event starts, authored focus/media/title/CTA boundaries and both sides of segment joins. Inspect actual frames and relevant motion/audio; a sheet cannot establish smooth animation, factual correctness or listening quality. The agent records what was actually checked, without asking the user for another production approval:

```bash
python scripts/pipeline.py review PROJECT/scene.json --video PROJECT/outputs/preview.mp4 --visual-note "Actual frame/motion checks and limitations" --fact-note "Original source/date/context checks" --audio-note "Encoded measurements, listening checks or limitation"
```

Review is bound to current source/configuration and the encoded video hash. A changed source/video invalidates it. Do not write a successful review merely because automated checks pass.

## Existing Site delivery

```bash
python scripts/pipeline.py prepare PROJECT/scene.json --video PROJECT/outputs/preview.mp4 --site SITE --title "Title from brief" --credits PROJECT/SOURCES.md
```

The Site's `.openai/hosting.json` must match the current binding. Existing player UI is preserved; direct `prepare_delivery.py --refresh-player-template` is the explicit option to replace it. All encoded variants get QA again, since derived AAC may overshoot. The pipeline prepares files in a temporary directory **outside the Site checkout**, validates every encoded variant there, then promotes the new media and versioned credits before atomically replacing `media.json` last. Failed preparation or variant QA leaves the current player, active manifest, and existing publication evidence unchanged. A process interruption during promotion can leave unreferenced media files, but cannot switch the manifest until its final replacement. This staging guarantee applies to `pipeline.py prepare`; direct `prepare_delivery.py` is a lower-level preparation command. Reports and a local `.geomotion-delivery.json` bind promoted file bytes to the review. Keep the local evidence file out of public Site source.

Commit and push the reviewed Site files using its configured source workflow, then:

```bash
python scripts/pipeline.py handoff --site SITE --output PROJECT/publication
```

Handoff verifies current inventory, clean relevant paths, matching upstream HEAD and binding, then uses `git archive` to package exactly that committed source. The output directory must be outside the Site. `.openai/hosting.json` plus its static directory are included; the archive is deployment source, not a user-facing editable-project download.

**Publication still requires the native Sites tools.** The agent must read the current Site, preserve its actual audience, deploy the exact commit/archive through those tools and verify the terminal response; do not stop at preparation if publication is authorized and tools are available. No new Site, credentials in files, audience change or simulated publish. If tools/access fail, report the concrete blocker. A normalized native receipt with `project_id`, `commit_sha`, `url`, `audience`, successful `status` and `deployment_id` can be recorded with `record-publication --request … --receipt …`; keep the raw native response separately. The CLI validates consistency, not authenticity of a manually invented receipt.

For final preparation/review use `--mode final` as well. The same Site receives the allowed preview/final variants and one download action from the existing delivery preset.
