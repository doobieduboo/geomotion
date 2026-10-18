# GeoMotion repository instructions

GeoMotion is a topic-agnostic map animation toolkit. Use the current brief and verified project inputs; no story, location, date or duration is built in.

## Read and apply

1. Read [.agents/skills/geomotion/SKILL.md](.agents/skills/geomotion/SKILL.md) and [defaults.json](.agents/skills/geomotion/defaults.json).
2. Inspect the checkout, execution environment and production workspace. Repository access does not attach credentials or restore production files.
3. When asked to use the latest repo in any conversation, fetch and compare the remote revision. Fast-forward a clean checkout; preserve local changes and resolve differences without reset/clean. Read the updated instructions and relevant references from that checkout, not an older installed skill or remembered chat rules. No commit-specific prompt or new conversation is required for repository changes. Environment/network changes are separate.
4. Apply current defaults to the active project's scene/scripts as well as future templates. Preserve approved narration, VO, media and timing unless the change requires updating them. Verify the affected preview.

## Ownership

- `defaults.json` owns production values and provider/model policies.
- `SKILL.md` owns the production workflow and reference routing.
- `references/` owns technical contracts and verification guidance.
- `delivery-target.json` owns the replaceable private player binding.
- Scripts implement only the features documented in [capabilities.md](.agents/skills/geomotion/references/capabilities.md).

Explicit user instructions override repository defaults; session/platform instructions retain their priority. Apply established preferences without repeated confirmation. Do not add a competing instruction file, duplicate a preset into templates, or append historical exceptions to multiple documents.

## Maintenance

Keep production inputs/outputs, downloaded media, caches and credentials outside the reusable repo. Bundled licensed fonts are dependencies. Preserve factual source dates, geography, allegations and attribution. Update a rule at its owning source, then repair affected links/code/tests. Remove obsolete instructions and unreachable code instead of retaining migration notes or redirects. Preserve supported script entry points. Run checks relevant to the changed behavior; do not generate speech or full videos for documentation-only edits.
