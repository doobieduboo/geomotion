"""Reproducible render → encoded QA → agent review → existing Sites handoff.

No TTS, implicit approval, fact certification or simulated hosted deployment.
"""

import argparse
import json
import subprocess
import sys
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
    for group in ("regions", "routes", "markers", "callouts", "titles"):
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
    run.add_argument("--mode", choices=("preview", "final"), default="preview")
    run.add_argument("--final-requested", action="store_true")
    run.add_argument("--lock", type=Path)
    run.add_argument(
        "--scope",
        default="visuals",
        help="Comma-separated already-authorized revision domains",
    )
    run.add_argument("--workers", type=int)
    review = sub.add_parser(
        "review", help="Agent records review of actual encoded video/contact sheet"
    )
    review.add_argument("scene", type=Path)
    review.add_argument("--video", type=Path, required=True)
    review.add_argument("--mode", choices=("preview", "final"), default="preview")
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
    prepare.add_argument("--mode", choices=("preview", "final"), default="preview")
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
    if a.command == "approve":
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
        receipt = render(
            a.scene, a.mode, a.output, a.checkpoint, a.workers, a.final_requested
        )
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
        command = [
            sys.executable,
            str(SKILL_ROOT / "scripts/prepare_delivery.py"),
            str(a.video),
            "--stage",
            a.mode,
            "--output",
            str(a.site / hosting["static"]["directory"]),
            "--title",
            a.title,
        ]
        if scene.get("audio"):
            command.append("--narrated")
        if a.credits:
            command += ["--credits", str(a.credits)]
        subprocess.run(command, check=True)
        dist = a.site / hosting["static"]["directory"]
        media = json.loads((dist / "media.json").read_text())
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
                dist / variant["src"],
                mode,
                timeline.duration,
                bool(scene.get("audio")),
                voice_end=voice_end,
            )
            results.append(report)
        if any(not r["automated_pass"] for r in results):
            raise ValueError(
                "Encoded delivery variant QA failed; no publication handoff"
            )
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
