# GeoMotion repository instructions

GeoMotion is a topic-agnostic map animation toolkit. Use the current brief and verified project inputs; no story, location, date or duration is built in.

## Read and apply

1. Read [.agents/skills/geomotion/SKILL.md](.agents/skills/geomotion/SKILL.md) and [defaults.json](.agents/skills/geomotion/defaults.json).
2. Inspect the checkout, execution environment and production workspace. Repository access does not attach credentials or restore production files.
3. When asked to use the latest repo in any conversation, fetch and compare the remote revision. Fast-forward a clean checkout; preserve local changes and resolve differences without reset/clean. Read the updated instructions and relevant references from that checkout, not an older installed skill or remembered chat rules. No commit-specific prompt or new conversation is required for repository changes. Environment/network changes are separate.
4. Apply current defaults to the active project's scene/scripts as well as future templates. Preserve approved narration, VO, media and timing unless the change requires updating them. Load the saved active project before revising it; follow [pipeline.md](.agents/skills/geomotion/references/pipeline.md#active-project-save-and-load) for saved state and reuse, and [delivery.md](.agents/skills/geomotion/references/delivery.md) for the retained delivery stage. Verify the affected output at that stage.
5. Use a full-frame flat Esri satellite map by default, retaining geographic overlays, outlines, zoom, pan, rotation and longitude wrap. Automatic supplementary text, media captions and visual source credits are off under the text policy in `defaults.json`; keep provenance and source/license records in the production’s `SOURCES.md`. Geographic names, VO subtitles and explicitly approved/authored opening titles remain available. Explicit user text requests override the default through scene `text_policy`. For map revisions, follow [style.md](.agents/skills/geomotion/references/style.md) for fills/outline appearance, [composition.md](.agents/skills/geomotion/references/composition.md) for persistent layers and phrase timing, [assets.md](.agents/skills/geomotion/references/assets.md) for flags/history, [scene-format.md](.agents/skills/geomotion/references/scene-format.md) for implemented behavior, and [quality.md](.agents/skills/geomotion/references/quality.md) for transition review. Keep story-specific choices in the production.

## Ownership

- `defaults.json` owns production values and media-provider/model policies.
- `AGENTS.md` owns agent delegation and sub-agent model selection.
- `SKILL.md` owns the production workflow and reference routing.
- `references/` owns technical contracts and verification guidance.
- `delivery-target.json` owns the replaceable private hosting binding.
- Scripts implement only the features documented in [capabilities.md](.agents/skills/geomotion/references/capabilities.md).

Explicit user instructions override repository defaults; session/platform instructions retain their priority. Apply established preferences without repeated confirmation. Do not add a competing instruction file, duplicate a preset into templates, or append historical exceptions to multiple documents.

## Short briefs

Topic-only and PDF briefs inherit the [required territory treatment](.agents/skills/geomotion/references/style.md#required-territory-treatment) and [global/contextual framing](.agents/skills/geomotion/references/composition.md#global-context-and-territory-framing). Author these in the scene before production; do not treat a local storyboard as permission to omit them. Explicit user exceptions retain priority.

Treat a short topic/edit brief—including “outline”, “daratan diwarnai” or “bendera”—as sufficient to apply the current production defaults. Load saved project/stage when continuing; choose routine colors, outline roles, glow, terrain tint, geographic flag treatment, reveal/hold, layout and delivery from their owning preset/reference instead of asking the user to repeat them. Keep reusable appearance settings topic-agnostic; actual locations, coordinates, assets and ownership states belong to the production. Ask only for missing information that materially changes the story, scope or result. Explicit requested exceptions override defaults locally. Do not claim a preset automatically researches geography, aligns speech or invents focus cues: author those from the actual project inputs. Keep invocation shortcuts as optional aliases to this same workflow when requested, not another preset or parallel rule system. A fresh conversation inherits repository changes only from a checkout or installed skill containing them; local edits are not remote updates. Verify the revision actually fetched or installed before claiming cross-session availability.

## Agent delegation and model selection

The user authorizes task-scoped sub-agent delegation when useful. The lead agent chooses sub-agent models under this policy without asking the user to select a model for each task. This does not change the main conversation model, grant new external-action permissions, or override platform restrictions.

Optimize for economical work with the approved quality retained. Start with the lead alone; activate a specialist only for a bounded task whose independent contribution justifies its cost. Roles are responsibilities, not an always-running team. The lead may perform every role on a small revision:

| Responsibility | Ownership |
| --- | --- |
| Project stewardship | Load/save the authoritative composition, retained stage, approved inputs and latest usable deliverable. |
| Visual editing | Change only assigned layers/assets/cues; preserve unrelated approved content. |
| Reuse and rendering | Inspect dependencies/cache validity and propose the smallest compatible operation before rendering. |
| Verification | Inspect the affected appearance, timing and joins; reuse applicable existing evidence. |
| Coordination and delivery | Integrate edits, schedule expensive work once, own credentials and publish the verified result. |

Keep one coordinator for the active project record and render scheduling. Give delegated tasks the relevant file paths, brief, approved constraints, output profile and expected result; avoid repeatedly copying the entire conversation. Do not let parallel agents overwrite the same state, render competing full revisions, regenerate the same assets or repeat completed checks. Waiting for a renderer or upload is not a reason to spawn more agents. Follow the [composition-first edit decision](.agents/skills/geomotion/references/pipeline.md#composition-first-edit-decision) before any expensive operation; delegation alone does not provide per-layer caches or eliminate source rendering.

- Keep small edits, simple fixes and documentation work with one agent. Delegate only when an independent implementation, investigation or review materially helps; start with the fewest agents needed.
- Use `gpt-6.1-sol` with `high` reasoning for delegated implementation, renderer changes, outline/flag integration, camera–VO timing fixes and relevant verification.
- Use `gpt-6-astra` with `high` reasoning for difficult diagnosis or design review: projection seams, persistent camera glitches, continuity problems, architectural tradeoffs or approaches that have repeatedly failed. Give it a bounded question and evidence; do not add an Astra review to every routine change.
- Use model overrides only when the delegation tool supports them, and follow its context/fork requirements. Supply the brief, approved constraints, relevant files and expected result explicitly when conversation history is not inherited. If the requested model is unavailable, continue with the current model or another user-authorized available model; report a material limitation without inventing model availability.
- Give each sub-agent a clear scope and file ownership. Parallelize independent work; sequence dependent edits and avoid concurrent changes to the same files. Preserve all existing local changes and approved production inputs.
- The lead agent reviews findings and diffs, integrates changes, performs relevant checks and inspects affected rendered output when visuals change. Model choice or a sub-agent's success report is not verification. Keep source/fact checks distinct from visual and audio checks, and state unavailable playback/listening review honestly.
- The lead agent owns credentials, final publication and the user-facing handoff. Delegate implementation or review without passing secrets or expanding the task's authorized scope. Do not render videos or regenerate speech for policy/documentation-only edits.

## Maintenance

Keep production inputs/outputs, downloaded media, caches and credentials outside the reusable repo. Bundled licensed fonts are dependencies. Preserve factual source dates, geography, allegations and attribution. Update a rule at its owning source, then repair affected links/code/tests. Remove obsolete instructions and unreachable code instead of retaining migration notes or redirects. Preserve supported script entry points. Run checks relevant to the changed behavior; do not generate speech or full videos for documentation-only edits.
