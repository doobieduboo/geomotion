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

Dates accept ISO calendar dates or reduced precision `YYYY` / `YYYY-MM` when that is all the catalog establishes. Closed date intervals such as `1860/1865` preserve a catalog range; endpoints must be valid and chronological. Optional `document_date` records an archival document’s creation/issue date without pretending it is a modern scan capture date. Provide at least one known capture/publication/document date and explain its precision in `date_basis`; do not invent a month/day. Optional `sha256` locks original file bytes. Allowed `fact_status`: verified/unverified/rejected. Allowed `reuse_status`: licensed/public_domain/editorial_assessment/unknown/restricted. These are recorded assessments, not a legal or factual certification by software. Unknown/restricted reuse produces a warning and does not silently delete the asset. Active `callouts[].archive_id` resolves its image from the manifest and requires factual review marked verified. A conflicting explicit `image` fails. Manifest metadata remains source evidence in project `SOURCES.md`; it does not automatically generate visible archive descriptions, captions or credits. Explicitly requested captions/credits require root scene `text_policy` overrides and authored wording under [assets.md](assets.md).

Register all additional production dependencies in `inputs`, grouped by `narration`, `voice`, `audio`, `subtitles`, `archives`, `data`, `visuals` or `configuration`; each value is an array of local file paths. The snapshot also collects generic scene assets, audio, cues, archive files, bundled fonts, renderer modules, actual font overrides and the current preset. Unregistered custom assets cannot be protected automatically.

After an **existing explicit user approval**, record it once:

```bash
python scripts/pipeline.py approve PROJECT/scene.json --lock PROJECT/approved.json --approval-note "Reference to the user's actual approval"
```

This records approval; it does not solicit new permission or infer consent. For an authorized visual revision, pass `--lock PROJECT/approved.json --scope visuals`. Changes in VO, subtitle text/timing, archive bytes, data or configuration then fail with a concrete domain diff. For an already authorized change in those domains, include the relevant domains in `--scope`; do not make the user approve the same action again. Timeline changes belong to `subtitles` as well as affected media. A preset/code upgrade changes `configuration`; review that diff explicitly. The snapshot is not overwritten by rendering, and approval is never auto-renewed.

## Active-project save and load

Keep an active production in its existing cloud workspace directory. Save enough state to continue that project across turns, interrupted commands and agent context changes; permanent storage, external backups and cross-project restoration are not required unless requested. Start a new production separately and never assume another conversation has the same workspace or files.

`project_workspace.py` owns the machine-readable `.geomotion-project.json` beside the source. It references the editable scene, existing input hashes, retained stage/authorization, last render receipt, current/previous checkpoint directories and any active compositor recipe/receipt. `pipeline.py run` and `composite` update this one record; do not create a second machine state file for the same generic project. Existing scene/layers and `project_state.py` remain the source/provenance owners. Agent notes may reference this record without duplicating it.

```bash
python scripts/pipeline.py save PROJECT/scene.json
python scripts/pipeline.py load PROJECT/.geomotion-project.json
```

`save` hashes/references existing files without rendering or copying media. Optional `--checkpoint` and `--video` register an existing checkpoint or current-source-bound render receipt; `--project PATH` selects the record explicitly. `load` is read-only: it reports paths, source changes, missing inputs, artifact availability and whether a saved render/composite is current. It never overwrites the edited scene or regenerates missing assets. A current-source receipt is required before a render can be registered as current; an old video may remain available while stale.

For an existing approved final with no workspace record, record the already-given authorization once using `save ... --mode final --final-requested`. Subsequent `run`, `review`, `prepare` and `composite` select the saved stage when `--mode` is omitted. Returning a saved final project to preview requires `--return-to-preview` on `save`/`run`, representing the user's explicit stage change; a small edit does not imply it. A custom production with its own receipt schema needs a compatible adapter, not a fabricated generic `.render.json`.

Save after a usable asset/segment/revision is completed and before handing off ongoing work. Preserve editable scene/layers, original media, approved audio/stems, cues, camera timing, relevant source hashes, segment hashes/frame ranges and verification results. Save new results atomically and retain the previous usable deliverable until its replacement passes checks. Load and inspect this state before generating assets, requesting imagery or starting rendering again. Reuse valid files; recover missing/corrupt work without discarding completed compatible work. Keep production files and any permitted caches outside the toolkit repo. Do not add a large master or permanent backup requirement to implement workspace save/load.

## Composition-first edit decision

Economy means reusing valid work while retaining approved quality. The editable composition, its assets and the saved active-project record remain the source of truth through previews and exports. An MP4 is a derived result, not a replacement project or proof that its visible elements remain separately editable. Do not restart a production from its exported video while the composition is available.

Before spending on rendering, asset generation or publication, load the existing project and compare the requested change with its approved inputs. In the production's existing revision plan or saved state, record the changed layers/assets, affected intervals including dependent tails/neighbors, usable clean bases/checkpoints, operation chosen and any concrete reason a cheaper operation is invalid. Reference these files instead of creating another competing project ledger. This is the agent's decision record, not a new automatic planner CLI or a permission gate.

Choose the first compatible operation below; preserve profile, factual assets, voice and reading quality:

| Requested change and available evidence | Operation |
| --- | --- |
| Discussion, status, rules or non-rendering metadata only | Update the relevant source/notes; no render, VO regeneration or publication of media. |
| Source and saved deliverable are still current | Reuse the verified deliverable; do not rerun a completed export. |
| Appearance/position needs a decision | Produce one representative still or the shortest relevant sample, or reuse a still whose actual dependencies are unchanged. |
| Add/change/remove an independently supplied overlay with a compatible clean native base | Edit its recipe/assets; inspect `composite --plan`, then recomposite only affected GOPs from that clean base. Removing a recipe entry does not remove pixels already baked into the base. |
| Source layers changed and some range dependency keys remain valid | Import verified unaffected chunks; render missing/invalid ranges only. |
| An element is baked into the available base, with no compatible clean layer | Render the necessary intervals from the editable composition; explain the dependency reason before starting. |
| A global change actually invalidates every frame | Full source render is allowed with a recorded reason; resume valid work from that same revision if interrupted. |

An overlay change does not inherently require another basemap render. Conversely, cache files alone do not prove that a changed camera, geometry, baked outline or layout can reuse old pixels. Never falsify cache identity, paint over old elements, silently lower resolution or retain a visual regression just to claim savings. Source rendering and final decoding/compositing/encoding are different costs; cached assets may still require composition into a new MP4.

Keep existing clean bases, transparent graphics, editable text/cues, geographic masks, textures, effect settings and approved audio/stems separate when they already exist. For new independently composed graphics, retain the base and recipe so later revisions can rebuild from the base rather than stack compressed exports. Do not render a second full clean base solely to satisfy this policy; use supported composition steps and justify extra intermediate work by the expected edit need. Honor source-provider cache restrictions: this policy does not authorize a raw Esri tile disk cache.

Current generic support is workspace save/load, source/assets, global layout plans, dependency-aware video chunks and additive PNG/atlas composition. Automatic independent raster caches for every basemap/fill/flag/outline/text/effect layer, real-time AE-style preview and extraction of hidden layers from a flattened MP4 are not implemented. Keep these distinctions explicit in planning and handoffs; do not describe task delegation as implementation of that missing architecture.

After the chosen operation, inspect changed content and joins, run the applicable assembled-file checks once, and atomically save the resulting scene/recipe, dependencies, checkpoints, review and deliverable before handoff. Preserve the previous usable result until its replacement is verified. Do not repeat unchanged source research, TTS, renders, full-file checks or publication merely because another agent took over. Agent roles and model selection are owned by [AGENTS.md](../../../../AGENTS.md).

## Revision reuse

Before rendering a revision, compare it with the saved source and record the affected layers, old/new time ranges and dependencies. Explain the selected render scope briefly. A file or whole-project fingerprint change is not by itself evidence that every frame needs to be rerendered.

- For purely additive overlays, first load a saved compatible native base and use a verified compositor to add transparent native-resolution graphics over the affected range. Retain the clean base, editable overlay recipe/assets, placement/scale and global timing for subsequent revisions; do not repeatedly stack compressed revisions when the base is available. Re-encode only affected independently decodable GOP segments as needed, stream-copy compatible unaffected segments, and preserve approved audio/timestamps. This avoids scene/map rendering and new basemap requests for those reused frames; it does not imply compositing needs no video decoding or encoding. Existing baked-in pixels and their lifetimes remain part of the base.
- Moving, removing or replacing baked-in callouts/text/graphics requires rerendering the affected range from editable sources or a saved clean layer. Painting over the old element or pretending the MP4 has editable layers is not sufficient.
- Camera, timing, ownership, asset or style changes invalidate every range that actually depends on them. Include entrances/exits, fade/reveal tails, interpolation neighbors, persistent state and any downstream automatic-layout tracking. Inspect the dependency reach; a cue's nominal interval alone may be too small. Global changes may require a full render.
- Reuse unaffected native segments only after proving their render dependencies and output profile remain compatible. Verify actual files/hashes, global frame ranges and clock, resolution/fps/codec parameters, layout state and camera/layer/effect continuity at joins. Preserve verified audio by stream copy when compatible with the unchanged timing; otherwise use the approved source mix and check the new encoding.
- Record the old/new source identities, reasons each reused range remains valid, regenerated ranges and assembly/QA results. Never rewrite a stale checkpoint fingerprint or fabricate a new render receipt to force acceptance. A changed revision needs a verified project adapter or implemented dependency-aware reuse; generic identical-input resume is insufficient.

Inspect the changed layout at its actual delivery size and phone viewing scale before an expensive range render. After assembly, review changed ranges and both sides of joins, and run applicable full-file decode/timing/profile checks once. Reuse unaffected factual/audio review evidence where it still applies; bind the new assembled video to its real current source and review.

`revision_cache.py` computes conservative per-range video dependency keys; `execution.py` verifies/imports matching ranges into a new revision checkpoint, then uses its existing worker/assembly path. Saved current/history checkpoints are consulted automatically by `run`; `--reuse-from DIR` adds explicit sources. Only genuine generic-render records carrying dependency keys are eligible across revisions. Legacy checkpoints still resume identical inputs, but are not silently assigned new provenance. A full-render fallback needs a concrete dependency or compatibility reason communicated before starting; do not silently rerender everything for a small edit.

Keys include renderer/font/runtime/video-profile dependencies, actual source-clock/camera poses, layer/asset state and global imagery/geometry/subtitle reservations. Audio and unrelated authoring metadata are excluded from video keys; assembly still binds the full current source and audio. Layout has temporal tracking: this first implementation conservatively retains its prefix, so an earlier annotation may also invalidate later ranges. Camera/geometry/imagery-level/global reservation changes can invalidate more. These are safe bounds, not a claim of mathematically minimal invalidation. Live Esri imagery has no immutable server revision; retained video preserves the imagery already rendered. No raw tile disk cache is added.

Custom `runner` hooks have unknown dependencies and retain identical-input recovery only; use their own verified adapter for cross-revision reuse. Never invent Codex quota savings or repeatedly rerun/poll completed work.

## Additive native compositor

`compositor.py` is the separate owner of additive screen-space PNG/atlas composition. It requires a saved native base video, its matching `.render.json` and original checkpoint segments; verifies base/segment packet identity; encodes only segments intersecting supplied overlays; and stream-copies unaffected video and original audio. It verifies unchanged video packets and exact audio payload/timestamps, including AAC priming/edit-list offsets. Its output proof is `.composite.json`, never a fake scene-render receipt. Clean sources stay independent of derived checkpoints; interruption/corruption recovery uses per-segment overlay dependencies.

```json
{
  "version": 1,
  "base_video": "outputs/native-base.mp4",
  "base_checkpoint": "checkpoints/native-base",
  "overlays": [{
    "image": "media/original-symbol.png",
    "start": 3.0, "end": 6.0,
    "position": [540, 180], "size": [240, 160],
    "fade_in": 0.12, "fade_out": 0.12
  }]
}
```

Paths resolve against the recipe. `position` is the native-pixel top-left corner, not a geographic point or the 720-wide design grid. `size` is optional; images retain their supplied pixel dimensions otherwise. Out-of-frame clipping is rejected. Use exactly one `image` or `atlas`; an atlas also supplies `atlas_metadata` as a local JSON path or metadata object following [scene-format.md](scene-format.md). Atlas anchors are not used for this top-left screen-space placement. `start`/`end` use output seconds; fades apply to the complete supplied overlay. Geographic parenting, arbitrary transform keyframes and removal of baked-in elements remain source-render/asset tasks.

```bash
python scripts/pipeline.py composite PROJECT/overlay.json --output PROJECT/outputs/revised.mp4 --checkpoint PROJECT/checkpoints/overlay --plan
python scripts/pipeline.py composite PROJECT/overlay.json --output PROJECT/outputs/revised.mp4 --checkpoint PROJECT/checkpoints/overlay
```

Both use the saved stage; the first final operation needs actual final authorization as above. `--plan` validates base proof/native bounds and lists affected/copied ranges without encoding or requesting maps. A completed composite is registered in the same workspace record, which reports stale assets/recipes on load. Inspect actual composed frames/joins and apply encoded/audio review before publication. The compositor's technical proof does not certify layout aesthetics, history, listening or native Sites deployment. Direct-MP4 staging/publication still follows the contract below.

## Render and resume

All paths below are examples relative to the installed skill root; keep projects outside the toolkit checkout.

```bash
python scripts/pipeline.py run PROJECT/scene.json --output PROJECT/outputs/preview.mp4 --checkpoint PROJECT/checkpoints/revision-1
```

Optional `--workers N` can lower concurrency. CPU affinity/cgroup quota and currently available host/cgroup memory constrain it further using preset estimates; these are resource estimates, not an OOM guarantee. No resolution, bitrate or provider is lowered to fit resources. Workers render native video-only frame ranges with **global frame numbers**; final assembly stream-copies video and encodes supplied audio once. No full-size master or intermediate upscale is created.

Each completed segment records video/layout hashes, frame count and generic dependency key atomically. Same-checkpoint resume requires an identical whole-source fingerprint and reruns missing/corrupt segments. After input changes, choose a new revision directory; saved history or `--reuse-from` can import eligible ranges under the contract above, checking real H.264/yuv420p bytes, frame counts, layout hash and global frame numbers. New render receipts report `reused_segments` separately from `rendered_segments`; `resumed_segments` includes all ranges reused without rendering. An interrupted segment is not completed work. Exclusive checkpoint locks prevent overlapping writes; changing sources during execution invalidates that attempt's records and blocks assembly. The previous deliverable survives render failure.

Before scheduling missing native segments, the pipeline computes one source-fingerprint-bound `global-layout.json` in the checkpoint directory. This planning pass checks every output frame in order, including source-clock cuts, text/image bounds, map focuses, moving panels and density constraints **without requesting Esri imagery**. Workers reuse the exact per-frame positions/focuses rather than recalculating all earlier frames. A resumed render reuses the plan when its input fingerprint and output profile match; otherwise it rebuilds the plan before rendering. Direct `render_scene.py` calls without an explicit shared plan retain the original deterministic standalone layout behavior. Tampered or stale plans fail closed; a changed plan during rendering prevents assembly.

Each worker fetches Esri imagery into session memory. There is no persistent tile cache, no alternate provider, and workers may request overlapping tiles. Source allocation is checked in bytes for both decoded physical tiles and wrapped mosaics, against `execution.max_tile_buffer_mb` and available host/cgroup memory with worker/reserve headroom. Decoded tiles are released once mosaics own their pixels. `execution.final_max_workers` additionally caps native-final concurrency. A failed memory check still stops rendering; split work or provide adequate resources without silently changing source tile detail, camera, provider or output profile.

Final requires the user's explicit request, represented by `--mode final --final-requested`. Direct `render_scene.py` accepts the same explicit gate and frame-range/video-only flags. The existing final authorization remains valid for subsequent revisions of that active project under [delivery.md](delivery.md); retain it in the work-state record. Never claim adding the flag supplies consent that the user did not give.

## QA and agent review

`run` emits `.render.json`, `.layout.json`, `.qa.json`, `.contact.jpg` and `.pipeline.json` beside the video. It checks native profile/frame count, full decode, presentation timestamp cadence (including segment joins), actual encoded integrated loudness/true peak, and reported callout/subtitle collisions/off-frame bounds. Callouts measure actual fonts with compact padding and preserve image ratio. Subtitle wrapping enforces preset max lines. Visible marker labels, titles, callouts, CTA, subtitles and attribution report mutual rectangle collisions. Focus protection, panel tracking, density budgets and remaining review limits follow the [composition contract](composition.md#executable-composition-contract). Silence, black intervals and optional voice-tail checks are candidates for review, not automatic proof of dead air or a bad fade. Integrated mix measurements do not prove stem ducking or speech intelligibility; inspect stems/listen when tools allow, and state limitations.

The contact sheet samples the opening, middle, ending, event starts, authored focus/media/title/CTA boundaries and both sides of segment joins. Inspect actual frames and relevant motion/audio; a sheet cannot establish smooth animation, factual correctness or listening quality. The agent records what was actually checked, without asking the user for another production approval:

```bash
python scripts/pipeline.py review PROJECT/scene.json --video PROJECT/outputs/preview.mp4 --visual-note "Actual frame/motion checks and limitations" --fact-note "Original source/date/context checks" --audio-note "Encoded measurements, listening checks or limitation"
```

Review is bound to current source/configuration and the encoded video hash. A changed source/video invalidates it. Do not write a successful review merely because automated checks pass.

## Direct MP4 delivery (default)

Direct delivery follows [delivery.md](delivery.md). The bundled `prepare` and `handoff` commands below currently implement the player workflow, not automatic direct-asset publication. A verified project-specific adapter may implement direct staging without adding UI or deriving unrequested qualities. Keep its source and evidence in the production; do not claim it is a generic toolkit feature.

Bind the assembled MP4 and actual review to the current source/overlay recipe, base/segment hashes and reuse audit. Stage the verified file under a revisioned path outside the Site first, verify its encoded bytes/profile, then copy those exact bytes into the configured Site static directory. Preserve the previous usable asset until verification succeeds. Record the direct relative path, file hash, stage/profile, credits and intended URL in project delivery evidence. Keep credentials and local review records out of public source. A player `media.json` update or refreshed player template is not required.

Commit/push the reviewed static asset and required hosting/source files, verify the exact pushed commit, and archive that source with its real hosting manifest/static assets. Use native Sites publication preserving the existing audience. Save its raw response and matching receipt, verify the hosted MP4, and return the literal file URL. Never use an older player's review/delivery record as proof of the new MP4 or fabricate a generic render fingerprint for a custom compositor. Retain verified unchanged-segment/audio evidence and the active direct URL in the saved project state.

## Optional player delivery

```bash
python scripts/pipeline.py prepare PROJECT/scene.json --video PROJECT/outputs/preview.mp4 --site SITE --title "Title from brief"
```

Add `--credits PROJECT/PUBLIC_CREDITS.md` only for explicitly requested, curated public credits. Keep the full project `SOURCES.md` private. The Site's `.openai/hosting.json` must match the current binding. Existing player UI is preserved; direct `prepare_delivery.py --refresh-player-template` is the explicit option to replace it. All encoded variants get QA again, since derived AAC may overshoot. The pipeline prepares files in a temporary directory **outside the Site checkout**, validates every encoded variant there, then promotes the new media and versioned credits before atomically replacing `media.json` last. Failed preparation or variant QA leaves the current player, active manifest, and existing publication evidence unchanged. A process interruption during promotion can leave unreferenced media files, but cannot switch the manifest until its final replacement. This staging guarantee applies to `pipeline.py prepare`; direct `prepare_delivery.py` is a lower-level preparation command. Reports and a local `.geomotion-delivery.json` bind promoted file bytes to the review. Keep the local evidence file out of public Site source.

Commit and push the reviewed Site files using its configured source workflow, then:

```bash
python scripts/pipeline.py handoff --site SITE --output PROJECT/publication
```

Handoff verifies current inventory, clean relevant paths, matching upstream HEAD and binding, then uses `git archive` to package exactly that committed source. The output directory must be outside the Site. `.openai/hosting.json` plus its static directory are included; the archive is deployment source, not a user-facing editable-project download.

**Publication still requires the native Sites tools.** The agent must read the current Site, preserve its actual audience, deploy the exact commit/archive through those tools and verify the terminal response; do not stop at preparation if publication is authorized and tools are available. No new Site, credentials in files, audience change or simulated publish. If tools/access fail, report the concrete blocker. A normalized native receipt with `project_id`, `commit_sha`, `url`, `audience`, successful `status` and `deployment_id` can be recorded with `record-publication --request … --receipt …`; keep the raw native response separately. The CLI validates consistency, not authenticity of a manually invented receipt.

For final player preparation/review use `--mode final` as well. Only an explicitly requested player receives the allowed variants and one download action from the preset; default direct delivery returns the current-stage MP4 file.
