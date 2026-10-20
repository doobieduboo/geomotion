import io
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents/skills/geomotion/scripts"
sys.path.insert(0, str(SCRIPTS))
from config import DEFAULTS
from execution import render, worker_limit, exclusive
from project_state import snapshot, check_lock, archive_manifest, atomic_json, digest
from timeline import Timeline, resolve_scene
from render_scene import main as render_main, load_font
from layout import callout_layout, inspect_boxes
from pipeline import (
    checked_scene,
    require_current_video,
    bound_site,
    main as pipeline_main,
)
from qa import check


def write_scene(root, duration=0.5, **extra):
    path = root / "scene.json"
    path.write_text(
        json.dumps(
            {
                "duration": duration,
                "camera": [{"time": 0, "center": [0, 0], "zoom": 0}],
                **extra,
            }
        )
    )
    return path


class Timing(unittest.TestCase):
    def test_cuts_share_clock_and_boundary(self):
        t = Timeline(10, [(2, 4), (7, 8)])
        self.assertEqual(t.duration, 7)
        self.assertEqual([t.source_time(x) for x in (0, 2, 5, 7)], [0, 4, 8, 10])
        self.assertEqual([t.output_time(x) for x in (0, 3, 4, 8, 10)], [0, 2, 2, 5, 7])
        self.assertIn("concat=n=3", t.audio_filter())
        for cuts in ([(4, 5), (3, 4)], [(0, 10)], [(1, float("nan"))]):
            with self.assertRaises(ValueError):
                Timeline(10, cuts)

    def test_phrase_reference_and_bad_clock(self):
        s = {
            "duration": 3,
            "timeline": {"events": [{"id": "phrase", "start": 1, "end": 2}]},
            "camera": [{"event": "phrase", "center": [0, 0], "zoom": 1}],
            "callouts": [{"event": "phrase", "position": [0, 0]}],
        }
        scene, _ = resolve_scene(s)
        self.assertEqual(scene["camera"][0]["time"], 1)
        self.assertEqual(scene["callouts"][0]["end"], 2)
        s["callouts"][0]["start"] = 0
        with self.assertRaises(ValueError):
            resolve_scene(s)
        s["callouts"][0].pop("start")
        s["timeline"]["audio_clock"] = "guess"
        with self.assertRaises(ValueError):
            resolve_scene(s)


class Provenance(unittest.TestCase):
    def test_scope_separates_voice_and_visual(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "voice.bin").write_bytes(b"approved")
            path = write_scene(root, inputs={"voice": ["voice.bin"]})
            lock = {"inputs": snapshot(path)}
            s = json.loads(path.read_text())
            s["camera"][0]["zoom"] = 2
            path.write_text(json.dumps(s))
            self.assertEqual(
                check_lock(lock, snapshot(path), {"visuals"})[0]["domain"], "visuals"
            )
            (root / "voice.bin").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "voice"):
                check_lock(lock, snapshot(path), {"visuals"})

    def test_manifest_context_and_uncertain_reuse_are_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "photo.jpg").write_bytes(b"photo")
            item = {
                "id": "archive",
                "file": "photo.jpg",
                "source_url": "https://example.org/report",
                "credit": "Publisher / photographer",
                "context": "Actual event, location known",
                "publication_date": "2026-01-01",
                "date_basis": "Publisher date; capture date unknown",
                "fact_status": "verified",
                "reuse_status": "unknown",
            }
            path = root / "archives.json"
            atomic_json(path, {"version": 1, "archives": [item]})
            records, warnings = archive_manifest(path)
            self.assertEqual(records["archive"]["sha256"], digest(root / "photo.jpg"))
            self.assertEqual(len(warnings), 1)
            item["sha256"] = "bad"
            atomic_json(path, {"version": 1, "archives": [item]})
            with self.assertRaisesRegex(ValueError, "bytes changed"):
                archive_manifest(path)

    def test_real_font_content_fit_and_image_ratio(self):
        font = load_font(22, True)
        body = load_font(19)
        short = callout_layout("Info", [], font, body, 330, 12)
        long = callout_layout("Information label", [], font, body, 330, 12)
        self.assertLess(short[0], long[0])
        self.assertLess(long[0], 330)
        pic = callout_layout("Info", [], font, body, 330, 12, (600, 400))
        self.assertEqual(pic[2], 204)
        self.assertTrue(
            inspect_boxes(
                [("subtitle", (0, 0, 30, 30)), ("callout", (10, 10, 40, 40))],
                (100, 100),
            )
        )


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required"
)
class NativeExecution(unittest.TestCase):
    def test_checkpoint_resume_corruption_and_exact_join(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_scene(root)
            calls = []
            barrier = threading.Barrier(2)

            def runner(scene, mode, out, start, stop):
                calls.append((start, stop))
                if len(calls) <= 2:
                    barrier.wait(timeout=5)
                proc = subprocess.Popen(
                    [
                        "ffmpeg",
                        "-y",
                        "-v",
                        "error",
                        "-f",
                        "rawvideo",
                        "-pix_fmt",
                        "rgb24",
                        "-s",
                        "360x640",
                        "-r",
                        "24",
                        "-i",
                        "-",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "fast",
                        "-crf",
                        "28",
                        "-pix_fmt",
                        "yuv420p",
                        str(out),
                    ],
                    stdin=subprocess.PIPE,
                )
                for n in range(start, stop):
                    proc.stdin.write(
                        Image.new("RGB", (360, 640), (n * 15, 0, 0)).tobytes()
                    )
                proc.stdin.close()
                self.assertEqual(proc.wait(), 0)
                atomic_json(out.with_suffix(".layout.json"), {"errors": {}})

            with patch.dict(DEFAULTS["execution"], {"checkpoint_seconds": 0.2}), patch(
                "execution.worker_limit", return_value=2
            ):
                receipt = render(
                    path, "preview", root / "out.mp4", root / "cp", 1, runner=runner
                )
                self.assertEqual(receipt["frames"], 12)
                self.assertEqual(receipt["workers"], 2)
                self.assertEqual(len(calls), 3)
                receipt = render(
                    path, "preview", root / "out.mp4", root / "cp", 1, runner=runner
                )
                self.assertEqual(receipt["rendered_segments"], 0)
                self.assertEqual(len(calls), 3)
                (root / "cp/5-10.mp4").write_bytes(b"corrupted")
                render(path, "preview", root / "out.mp4", root / "cp", 1, runner=runner)
                self.assertEqual(calls[-1], (5, 10))
                result = check(root / "out.mp4", "preview", 0.5, require_layout=True)
                self.assertFalse(result["errors"])
                # Decode joined frames to prove order/content across boundaries.
                raw = subprocess.check_output(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-i",
                        str(root / "out.mp4"),
                        "-vf",
                        "scale=1:1",
                        "-f",
                        "rawvideo",
                        "-pix_fmt",
                        "rgb24",
                        "-",
                    ]
                )
                self.assertEqual(len(raw), 36)
                self.assertTrue(all(abs(raw[n * 3] - n * 15) < 8 for n in range(12)))
                s = json.loads(path.read_text())
                s["camera"][0]["zoom"] = 1
                path.write_text(json.dumps(s))
                with self.assertRaisesRegex(ValueError, "input/profile changed"):
                    render(
                        path, "preview", root / "out.mp4", root / "cp", 1, runner=runner
                    )
            with self.assertRaisesRegex(ValueError, "explicit user request"):
                render(path, "final", root / "final.mp4", root / "other")

    def test_interruption_preserves_completed_segments(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_scene(root)

            def runner(scene, mode, out, start, stop):
                if start:
                    raise RuntimeError("interrupted")
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-v",
                        "error",
                        "-f",
                        "lavfi",
                        "-i",
                        "color=c=green:s=360x640:r=24",
                        "-frames:v",
                        str(stop - start),
                        "-c:v",
                        "libx264",
                        "-pix_fmt",
                        "yuv420p",
                        str(out),
                    ],
                    check=True,
                )
                atomic_json(out.with_suffix(".layout.json"), {"errors": {}})

            (root / "out.mp4").write_bytes(b"previous-approved-output")
            with patch.dict(DEFAULTS["execution"], {"checkpoint_seconds": 0.2}):
                with self.assertRaisesRegex(RuntimeError, "interrupted"):
                    render(
                        path, "preview", root / "out.mp4", root / "cp", 1, runner=runner
                    )
            state = json.loads((root / "cp/checkpoint.json").read_text())
            self.assertIn("0-5", state["segments"])
            self.assertEqual(
                (root / "out.mp4").read_bytes(), b"previous-approved-output"
            )

    def test_actual_renderer_source_cut_and_subtitles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=500:duration=1",
                    str(root / "voice.wav"),
                ],
                check=True,
            )
            path = write_scene(
                root,
                1,
                audio="voice.wav",
                timeline={"cuts": [[0.25, 0.75]]},
                subtitles=[{"start": 0, "end": 1, "text": "Actual phrase."}],
            )
            tile = io.BytesIO()
            Image.new("RGB", (256, 256), "green").save(tile, "JPEG")
            with patch(
                "sys.argv",
                ["render_scene", str(path), "--output", str(root / "out.mp4")],
            ), patch(
                "render_scene.urllib.request.urlopen",
                side_effect=lambda *a, **k: io.BytesIO(tile.getvalue()),
            ):
                render_main()
            result = check(root / "out.mp4", "preview", 0.5, False, require_layout=True)
            self.assertEqual(result["frames"], 12)
            self.assertIsNotNone(result["audio"])
            self.assertFalse(
                json.loads((root / "out.layout.json").read_text())["errors"]
            )

    def test_pipeline_rejects_missing_cues_and_stale_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_scene(root, audio="voice.wav")
            with self.assertRaisesRegex(ValueError, "subtitle cues"):
                checked_scene(path)
            path = write_scene(root)
            (root / "video.mp4").write_bytes(b"video")
            atomic_json(
                root / "video.render.json",
                {"fingerprint": "wrong", "sha256": digest(root / "video.mp4")},
            )
            with self.assertRaisesRegex(ValueError, "current source"):
                require_current_video(path, root / "video.mp4", "preview")

    def test_review_delivery_handoff_exact_pushed_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            path = write_scene(project, 0.25)
            tile = io.BytesIO()
            Image.new("RGB", (256, 256), "green").save(tile, "JPEG")

            def runner(scene, mode, out, start, stop):
                argv = [
                    "render_scene",
                    str(scene),
                    "--output",
                    str(out),
                    "--mode",
                    mode,
                    "--start-frame",
                    str(start),
                    "--end-frame",
                    str(stop),
                    "--video-only",
                ]
                with patch("sys.argv", argv), patch(
                    "render_scene.urllib.request.urlopen",
                    side_effect=lambda *a, **k: io.BytesIO(tile.getvalue()),
                ):
                    render_main()

            def run_with_fixture(scene, mode, out, cp, workers, final_requested):
                return render(scene, mode, out, cp, 1, final_requested, runner=runner)

            video = project / "preview.mp4"
            with patch("pipeline.render", side_effect=run_with_fixture), patch(
                "sys.argv",
                [
                    "pipeline",
                    "run",
                    str(path),
                    "--output",
                    str(video),
                    "--checkpoint",
                    str(project / "cp"),
                ],
            ):
                pipeline_main()
            self.assertEqual(
                json.loads(video.with_suffix(".pipeline.json").read_text())["state"],
                "review_required",
            )
            with patch(
                "sys.argv",
                [
                    "pipeline",
                    "review",
                    str(path),
                    "--video",
                    str(video),
                    "--visual-note",
                    "Fixture frame checks",
                    "--fact-note",
                    "Synthetic test only",
                    "--audio-note",
                    "Silent fixture; no listening claim",
                ],
            ):
                pipeline_main()
            site = root / "site"
            (site / ".openai").mkdir(parents=True)
            (site / "dist").mkdir()
            atomic_json(
                site / ".openai/hosting.json",
                {"project_id": "fixture-site", "static": {"directory": "dist"}},
            )
            binding = root / "binding.json"
            atomic_json(
                binding,
                {
                    "project_id": "fixture-site",
                    "audience": "owner-private",
                    "url": "https://example.org",
                },
            )
            (site / "dist/index.html").write_text("CUSTOM PLAYER RETAINED")
            (site / "dist/app.js").write_text("// CUSTOM CONTROLS RETAINED")
            with patch(
                "sys.argv",
                [
                    "pipeline",
                    "prepare",
                    str(path),
                    "--video",
                    str(video),
                    "--site",
                    str(site),
                    "--title",
                    "Fixture",
                    "--binding",
                    str(binding),
                ],
            ):
                pipeline_main()
            self.assertEqual(
                (site / "dist/index.html").read_text(), "CUSTOM PLAYER RETAINED"
            )
            self.assertTrue((site / "dist/media.json").is_file())

            def git(*args):
                return subprocess.check_output(
                    ["git", "-C", str(site), *args],
                    stderr=subprocess.DEVNULL,
                    text=True,
                ).strip()

            subprocess.run(
                ["git", "init", "--bare", str(root / "remote.git")],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            git("init")
            git("config", "user.email", "fixture@example.org")
            git("config", "user.name", "Fixture")
            git("add", ".openai", "dist")
            git("commit", "-m", "Reviewed fixture")
            git("remote", "add", "origin", str(root / "remote.git"))
            git("push", "-u", "origin", "HEAD")
            with patch(
                "sys.argv",
                [
                    "pipeline",
                    "handoff",
                    "--site",
                    str(site),
                    "--output",
                    str(project / "publication"),
                    "--binding",
                    str(binding),
                ],
            ):
                pipeline_main()
            request = project / "publication/publication-request.json"
            data = json.loads(request.read_text())
            self.assertEqual(data["commit_sha"], git("rev-parse", "HEAD"))
            self.assertEqual(data["state"], "publication_required")
            receipt = project / "receipt.json"
            atomic_json(
                receipt, {**data, "status": "live", "deployment_id": "fixture-deploy"}
            )
            with patch(
                "sys.argv",
                [
                    "pipeline",
                    "record-publication",
                    "--request",
                    str(request),
                    "--receipt",
                    str(receipt),
                ],
            ):
                pipeline_main()
            self.assertEqual(
                json.loads((request.parent / "publication.json").read_text())["state"],
                "published",
            )
            (site / "dist/index.html").write_text("CHANGED AFTER QA")
            with patch(
                "sys.argv",
                [
                    "pipeline",
                    "handoff",
                    "--site",
                    str(site),
                    "--output",
                    str(project / "publication"),
                    "--binding",
                    str(binding),
                ],
            ):
                with self.assertRaisesRegex(ValueError, "inventory changed"):
                    pipeline_main()

    def test_archive_selection_is_not_a_layout_only_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("a.jpg", "b.jpg"):
                (root / name).write_bytes(name.encode())
            records = [
                {
                    "id": name,
                    "file": name + ".jpg",
                    "source_url": "https://example.org/" + name,
                    "credit": "Publisher",
                    "publication_date": "2026-01-01",
                    "date_basis": "Publication only",
                    "context": "Fixture",
                    "fact_status": "verified",
                    "reuse_status": "unknown",
                }
                for name in ("a", "b")
            ]
            atomic_json(root / "archives.json", {"version": 1, "archives": records})
            path = write_scene(
                root,
                archive_manifest="archives.json",
                callouts=[{"position": [0, 0], "archive_id": "a"}],
            )
            lock = {"inputs": snapshot(path)}
            scene = json.loads(path.read_text())
            scene["callouts"][0]["offset"] = [10, 20]
            atomic_json(path, scene)
            check_lock(lock, snapshot(path), {"visuals"})
            scene["callouts"][0]["archive_id"] = "b"
            atomic_json(path, scene)
            with self.assertRaisesRegex(ValueError, "archives/active_callouts"):
                check_lock(lock, snapshot(path), {"visuals"})

    def test_final_is_native_and_requires_explicit_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_scene(root, 1 / 30)
            out = root / "final.mp4"
            args = ["render_scene", str(path), "--mode", "final", "--output", str(out)]
            with patch("sys.argv", args), patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit):
                    render_main()
            self.assertFalse(out.exists())
            tile = io.BytesIO()
            Image.new("RGB", (256, 256), "green").save(tile, "JPEG")
            with patch("sys.argv", args + ["--final-requested"]), patch(
                "render_scene.urllib.request.urlopen",
                side_effect=lambda *a, **k: io.BytesIO(tile.getvalue()),
            ):
                render_main()
            report = check(out, "final", 1 / 30, require_layout=True)
            self.assertFalse(report["errors"])
            self.assertEqual(report["frames"], 1)

    def test_qa_flags_encoded_low_voice_and_layout_collision(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "low.mp4"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-v",
                    "error",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=green:s=360x640:r=24",
                    "-f",
                    "lavfi",
                    "-i",
                    "sine=frequency=440:duration=1",
                    "-t",
                    "1",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-c:a",
                    "aac",
                    str(path),
                ],
                check=True,
            )
            atomic_json(
                path.with_suffix(".layout.json"),
                {"errors": {"subtitle: overlaps callout": {}}},
            )
            report = check(path, "preview", 1, True, require_layout=True)
            self.assertIn("subtitle: overlaps callout", report["errors"])
            self.assertTrue(any("loudness" in error for error in report["errors"]))

    def test_worker_bound_and_exclusive_writer(self):
        self.assertGreaterEqual(worker_limit(999), 1)
        self.assertLessEqual(worker_limit(999), DEFAULTS["execution"]["max_workers"])
        with self.assertRaises(ValueError):
            worker_limit(0)
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "lock"
            with exclusive(lock):
                with self.assertRaisesRegex(RuntimeError, "Another process"):
                    with exclusive(lock):
                        pass


if __name__ == "__main__":
    unittest.main()
