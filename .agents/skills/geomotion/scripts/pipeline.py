"""Reproducible render → encoded QA → agent review → existing Sites handoff.

No TTS, implicit approval, fact certification or simulated hosted deployment.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from config import DEFAULTS, SKILL_ROOT
from execution import render
from project_state import (
    atomic_json,
    snapshot,
    check_lock,
    digest,
    load_project,
    fingerprint,
    differences,
)
from qa import check, contact_sheet
from timeline import resolve_scene
from render_scene import validate
from composition import validate_composition
from delivery_staging import seed_existing_player, version_credits, promote_staged_delivery
import project_workspace as workspace


def checked_scene(path):
    scene, warnings = load_project(path)
    if scene.get("subtitle_cues"):
        if scene.get("subtitles"):
            raise ValueError("Use subtitle_cues or inline subtitles, not both")
        scene["subtitles"] = json.loads(
            (path.parent / scene["subtitle_cues"]).read_text()
        )
    scene, timeline = resolve_scene(scene)
    validate(scene)
    validate_composition(scene)
    for group in ("regions", "routes", "markers", "callouts", "titles", "focuses"):
        for item in scene.get(group, []):
            start, end = item.get("start", 0), item.get("end", timeline.source_duration)
            if not 0 <= start < end <= timeline.source_duration:
                raise ValueError("Layer interval outside source timeline: " + group)
    if (
        scene.get("audio")
        and DEFAULTS["subtitles"]["enabled_with_narration"]
        and not scene.get("subtitles")
    ):
        raise ValueError("Narrated pipeline requires actual phrase subtitle cues")
    return scene, timeline, warnings


def require_current_video(scene_path, video, mode):
    receipt = json.loads(video.with_suffix(".render.json").read_text())
    if receipt["fingerprint"] != fingerprint(snapshot(scene_path), mode) or receipt[
        "sha256"
    ] != digest(video):
        raise ValueError("Video does not match current source/configuration")


def review_path(video):
    return video.with_suffix(".review.json")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    save = sub.add_parser('save', help='Save active workspace state without rendering or copying assets')
    save.add_argument('scene', type=Path)
    save.add_argument('--project', type=Path)
    save.add_argument('--mode', choices=('preview', 'final'))
    save.add_argument('--final-requested', action='store_true')
    save.add_argument('--return-to-preview', action='store_true')
    save.add_argument('--checkpoint', type=Path)
    save.add_argument('--video', type=Path)
    load = sub.add_parser('load', help='Inspect saved paths, source changes and artifact availability')
    load.add_argument('project', type=Path)
    composite = sub.add_parser('composite', help='Add supplied transparent overlays to saved native checkpoints')
    composite.add_argument('recipe', type=Path)
    composite.add_argument('--output', type=Path, required=True)
    composite.add_argument('--checkpoint', type=Path, required=True)
    composite.add_argument('--mode', choices=('preview', 'final'))
    composite.add_argument('--final-requested', action='store_true')
    composite.add_argument('--project', type=Path)
    composite.add_argument('--plan', action='store_true', help='Validate source/bounds and list reused ranges without encoding')
    approve = sub.add_parser(
        "approve", help="Record an existing explicit user approval; never infer it"
    )
    approve.add_argument("scene", type=Path)
    approve.add_argument("--lock", type=Path, required=True)
    approve.add_argument("--approval-note", required=True)
    run = sub.add_parser("run")
    run.add_argument("scene", type=Path)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--checkpoint", type=Path, required=True)
    run.add_argument("--mode", choices=("preview", "final"))
    run.add_argument("--final-requested", action="store_true")
    run.add_argument("--lock", type=Path)
    run.add_argument(
        "--scope",
        default="visuals",
        help="Comma-separated already-authorized revision domains",
    )
    run.add_argument("--workers", type=int)
    run.add_argument('--project', type=Path, help='Workspace state; defaults beside the scene')
    run.add_argument('--return-to-preview', action='store_true')
    run.add_argument('--reuse-from', type=Path, action='append', default=[], help='Additional previous checkpoint directory')
    review = sub.add_parser(
        "review", help="Agent records review of actual encoded video/contact sheet"
    )
    review.add_argument("scene", type=Path)
    review.add_argument("--video", type=Path, required=True)
    review.add_argument("--mode", choices=("preview", "final"))
    review.add_argument("--visual-note", required=True)
    review.add_argument("--fact-note", required=True)
    review.add_argument(
        "--audio-note",
        required=True,
        help="State checks and any listening limitation honestly",
    )
    prepare = sub.add_parser("prepare")
    prepare.add_argument("scene", type=Path)
    prepare.add_argument("--video", type=Path, required=True)
    prepare.add_argument("--mode", choices=("preview", "final"))
    prepare.add_argument("--site", type=Path, required=True)
    prepare.add_argument("--title", required=True)
    prepare.add_argument("--credits", type=Path)
    prepare.add_argument(
        "--binding",
        type=Path,
        default=SKILL_ROOT / DEFAULTS["delivery"]["site_binding"],
    )
    handoff = sub.add_parser(
        "handoff", help="Package exact pushed Site source for native Sites tools"
    )
    handoff.add_argument("--site", type=Path, required=True)
    handoff.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Artifact directory OUTSIDE Site checkout",
    )
    handoff.add_argument(
        "--binding",
        type=Path,
        default=SKILL_ROOT / DEFAULTS["delivery"]["site_binding"],
    )
    record = sub.add_parser("record-publication")
    record.add_argument("--request", type=Path, required=True)
    record.add_argument(
        "--receipt",
        type=Path,
        required=True,
        help="Native Sites terminal deployment response, no credentials",
    )
    a = p.parse_args()
    if hasattr(a, "scene"):
        a.scene = a.scene.resolve()
        if a.command in ('review', 'prepare'):
            a.mode = a.mode or (workspace.read(workspace.default_path(a.scene)) or {}).get('mode', 'preview')
    if a.command == 'save':
        checked_scene(a.scene)
        result = workspace.save(a.scene, a.project, mode=a.mode,
            final_requested=a.final_requested, return_to_preview=a.return_to_preview,
            checkpoint=a.checkpoint, video=a.video)
        print(json.dumps({'project': str(a.project or workspace.default_path(a.scene)),
                          'mode': result['mode'], 'status': result['status']}))
        return
    elif a.command == 'load':
        print(json.dumps(workspace.load(a.project), ensure_ascii=False, indent=2))
        return
    elif a.command == 'composite':
        from compositor import composite as composite_video, plan as composite_plan
        project = a.project or workspace.default_path(a.recipe)
        mode, authorized = workspace.select_mode(workspace.read(project), a.mode, a.final_requested)
        if a.plan:
            receipt = composite_plan(a.recipe, mode=mode)
        else:
            workspace.begin_composite(a.recipe,a.output,a.checkpoint,path=project,
                                      mode=mode,final_requested=authorized)
            try:
                receipt = composite_video(a.recipe, a.output, a.checkpoint,
                                          mode=mode, final_requested=authorized)
            except BaseException:
                workspace.mark_status(project,'composite_interrupted')
                raise
            workspace.save_composite(a.recipe, a.output, a.checkpoint,
                                     path=project, mode=mode, final_requested=authorized)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return
    elif a.command == "approve":
        checked_scene(a.scene)
        if not a.approval_note.strip():
            p.error("An actual user approval reference is required")
        atomic_json(
            a.lock,
            {
                "version": 1,
                "approval_note": a.approval_note,
                "inputs": snapshot(a.scene),
            },
        )
    elif a.command == "run":
        scene, timeline, warnings = checked_scene(a.scene)
        project = a.project or workspace.default_path(a.scene)
        saved = workspace.read(project)
        a.mode, authorized = workspace.select_mode(saved, a.mode,
            a.final_requested, a.return_to_preview)
        reuse = list(a.reuse_from)
        if saved:
            if saved.get('checkpoint'):
                reuse.append(Path(saved['checkpoint']))
            reuse += [Path(v) for v in reversed(saved.get('history', []))]
        changes = []
        if a.lock:
            lock = json.loads(a.lock.read_text())
            current = snapshot(a.scene)
            changes = differences(lock["inputs"], current)
            atomic_json(
                a.output.with_suffix(".revision.json"),
                {"changes": changes, "scope": a.scope.split(",")},
            )
            check_lock(lock, current, set(a.scope.split(",")))
        workspace.save(a.scene, project, mode=a.mode, final_requested=authorized,
            return_to_preview=a.return_to_preview, checkpoint=a.checkpoint, status='rendering')
        try:
            receipt = render(a.scene, a.mode, a.output, a.checkpoint, a.workers,
                             authorized, reuse_from=reuse)
        except BaseException:
            workspace.mark_status(project,'render_interrupted')
            raise
        voice_end = (
            timeline.output_time(scene["subtitles"][-1]["end"])
            if scene.get("subtitles")
            else None
        )
        result = check(
            a.output,
            a.mode,
            timeline.duration,
            bool(scene.get("audio")),
            voice_end=voice_end,
            require_layout=True,
        )
        times = {
            0,
            max(0, timeline.duration / 2),
            max(0, timeline.duration - 1 / DEFAULTS["export"][a.mode]["fps"]),
        }
        for item in scene.get("timeline", {}).get("events", []):
            times.add(timeline.output_time(item["start"]))
        authored = (
            scene.get("focuses", [])
            + scene.get("callouts", [])
            + scene.get("titles", [])
            + ([scene["cta"]] if scene.get("cta") else [])
        )
        for item in authored:
            times.add(timeline.output_time(item.get("start", 0)))
            times.add(
                max(
                    0,
                    timeline.output_time(item.get("end", timeline.source_duration))
                    - 1 / DEFAULTS["export"][a.mode]["fps"],
                )
            )
        # Include both sides of every checkpoint join.
        step = DEFAULTS["execution"]["checkpoint_seconds"]
        for join in range(step, int(timeline.duration) + 1, step):
            if join < timeline.duration:
                times.update((join - 1 / DEFAULTS["export"][a.mode]["fps"], join))
        times = sorted(t for t in times if 0 <= t < timeline.duration)
        contact_sheet(a.output, a.output.with_suffix(".contact.jpg"), times)
        atomic_json(
            a.output.with_suffix(".pipeline.json"),
            {
                "state": "review_required" if result["automated_pass"] else "qa_failed",
                "sha256": receipt["sha256"],
                "changes": changes,
                "archive_warnings": warnings,
            },
        )
        if not result["automated_pass"]:
            raise ValueError(
                "Encoded QA failed; inspect " + str(a.output.with_suffix(".qa.json"))
            )
        workspace.save(a.scene, project, mode=a.mode, final_requested=authorized,
                       checkpoint=a.checkpoint, video=a.output, status='review_required')
    elif a.command == "review":
        checked_scene(a.scene)
        require_current_video(a.scene, a.video, a.mode)
        qa = json.loads(a.video.with_suffix(".qa.json").read_text())
        if qa["sha256"] != digest(a.video) or not qa["automated_pass"]:
            raise ValueError("Current encoded QA must pass before review")
        if not all(s.strip() for s in (a.visual_note, a.fact_note, a.audio_note)):
            raise ValueError("Review notes cannot be empty")
        atomic_json(
            review_path(a.video),
            {
                "sha256": digest(a.video),
                "mode": a.mode,
                "visual_note": a.visual_note,
                "fact_note": a.fact_note,
                "audio_note": a.audio_note,
            },
        )
    elif a.command == "prepare":
        scene, timeline, _ = checked_scene(a.scene)
        require_current_video(a.scene, a.video, a.mode)
        review = json.loads(review_path(a.video).read_text())
        if review["sha256"] != digest(a.video) or review["mode"] != a.mode:
            raise ValueError("Review is stale")
        binding, hosting = bound_site(a.site, a.binding)
        dist = a.site / hosting["static"]["directory"]
        # Stage outside the Site checkout. A failed preparation or QA must not
        # change its currently active player, media or publication evidence.
        with tempfile.TemporaryDirectory(
            prefix=".geomotion-site-stage-", dir=a.site.resolve().parent
        ) as temporary:
            staged = Path(temporary)
            seed_existing_player(dist, staged)
            command = [
                sys.executable,
                str(SKILL_ROOT / "scripts/prepare_delivery.py"),
                str(a.video),
                "--stage",
                a.mode,
                "--output",
                str(staged),
                "--title",
                a.title,
            ]
            if scene.get("audio"):
                command.append("--narrated")
            if a.credits:
                command += ["--credits", str(a.credits)]
            subprocess.run(command, check=True)
            media = json.loads((staged / "media.json").read_text())
            expected = DEFAULTS["delivery"][
                "editing_qualities" if a.mode == "preview" else "final_qualities"
            ]
            if [v["height"] for v in media["variants"]] != expected:
                raise ValueError("Delivery qualities differ from preset")
            results = []
            for variant in media["variants"]:
                mode = (
                    "preview"
                    if variant["height"] == DEFAULTS["export"]["preview"]["width"]
                    else "final"
                )
                voice_end = (
                    timeline.output_time(scene["subtitles"][-1]["end"])
                    if scene.get("subtitles")
                    else None
                )
                report = check(
                    staged / variant["src"],
                    mode,
                    timeline.duration,
                    bool(scene.get("audio")),
                    voice_end=voice_end,
                )
                results.append(report)
            if any(not r["automated_pass"] for r in results):
                raise ValueError(
                    "Encoded delivery variant QA failed; previous Site files preserved"
                )
            # Credits have content-addressed names so the old manifest can
            # safely remain active until the new manifest is installed.
            media = version_credits(staged, media)
            promote_staged_delivery(staged, dist, media)
        evidence = {
            "state": "publication_required",
            "project_id": binding["project_id"],
            "source_video_sha256": digest(a.video),
            "review": review,
            "variant_qa": results,
            "files": {
                str(f.relative_to(a.site)): digest(f)
                for f in dist.rglob("*")
                if f.is_file()
            },
        }
        # Evidence lives outside the Site so media QA logs need not be published.
        atomic_json(a.site / ".geomotion-delivery.json", evidence)
    elif a.command == "handoff":
        binding, hosting = bound_site(a.site, a.binding)
        site = a.site.resolve()
        if a.output.resolve().is_relative_to(site):
            raise ValueError("Handoff artifacts must be outside Site checkout")
        evidence_file = site / ".geomotion-delivery.json"
        evidence = json.loads(evidence_file.read_text())
        if evidence["project_id"] != binding["project_id"]:
            raise ValueError("Prepared delivery binding changed")
        dist = site / hosting["static"]["directory"]
        inventory = {
            str(f.relative_to(site)): digest(f) for f in dist.rglob("*") if f.is_file()
        }
        if inventory != evidence["files"]:
            raise ValueError("Site inventory changed after delivery QA")
        for file, sha in evidence["files"].items():
            if digest(site / file) != sha:
                raise ValueError("Prepared Site file changed after QA: " + file)
        paths = [".openai/hosting.json", hosting["static"]["directory"]]
        status = subprocess.check_output(
            [
                "git",
                "-C",
                str(site),
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--",
                *paths,
            ],
            text=True,
        )
        if status.strip():
            raise ValueError("Commit and push reviewed Site source before handoff")
        head = subprocess.check_output(
            ["git", "-C", str(site), "rev-parse", "HEAD"], text=True
        ).strip()
        upstream = subprocess.check_output(
            ["git", "-C", str(site), "rev-parse", "--abbrev-ref", "@{upstream}"],
            text=True,
        ).strip()
        remote, branch = upstream.split("/", 1)
        remote_sha = subprocess.check_output(
            ["git", "-C", str(site), "ls-remote", remote, "refs/heads/" + branch],
            text=True,
        ).split()[0]
        if head != remote_sha:
            raise ValueError("Site HEAD is not the currently pushed upstream revision")
        a.output.mkdir(parents=True, exist_ok=True)
        archive = a.output / "site-source.tar.gz"
        subprocess.run(
            [
                "git",
                "-C",
                str(site),
                "archive",
                "--format=tar.gz",
                "--output",
                str(archive.resolve()),
                head,
                *paths,
            ],
            check=True,
        )
        atomic_json(
            a.output / "publication-request.json",
            {
                "state": "publication_required",
                "project_id": binding["project_id"],
                "url": binding["url"],
                "audience": binding["audience"],
                "commit_sha": head,
                "archive": str(archive.resolve()),
                "archive_sha256": digest(archive),
                "source_video_sha256": evidence["source_video_sha256"],
            },
        )
    elif a.command == "record-publication":
        request, receipt = json.loads(a.request.read_text()), json.loads(
            a.receipt.read_text()
        )
        # Normalize the native tool's result to these fields; preserve the raw response separately.
        for key in ("project_id", "commit_sha", "url"):
            if receipt.get(key) != request[key]:
                raise ValueError("Publication receipt mismatch: " + key)
        if receipt.get("status") not in (
            "live",
            "published",
            "succeeded",
        ) or not receipt.get("deployment_id"):
            raise ValueError(
                "A terminal successful native deployment receipt is required"
            )
        if receipt.get("audience") != request["audience"]:
            raise ValueError("Publication audience changed")
        atomic_json(
            a.request.with_name("publication.json"),
            {
                **request,
                "state": "published",
                "deployment_id": receipt["deployment_id"],
                "status": receipt["status"],
            },
        )
    print(a.command + ": complete")


def bound_site(site, binding_path):
    binding = json.loads(Path(binding_path).read_text())
    hosting = json.loads((Path(site) / ".openai/hosting.json").read_text())
    if hosting["project_id"] != binding["project_id"]:
        raise ValueError(
            "Existing Site does not match configured project_id; do not create a replacement"
        )
    directory = Path(hosting["static"]["directory"])
    if directory.is_absolute() or ".." in directory.parts:
        raise ValueError("Site static directory must stay inside checkout")
    return binding, hosting


if __name__ == "__main__":
    main()
