"""Regression tests for Site staging and fail-safe QA promotion."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "skills" / "geomotion" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from config import DEFAULTS
from delivery_staging import (
    promote_staged_delivery,
    seed_existing_player,
    version_credits,
)
from pipeline import main as pipeline_main
from project_state import atomic_json, digest


class StagingHelpers(unittest.TestCase):
    def test_preserves_existing_custom_player_and_versioned_credits(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            current, stage = root / "site", root / "stage"
            (current / "media").mkdir(parents=True)
            (stage / "media").mkdir(parents=True)
            (current / "index.html").write_text("custom player")
            (current / "app.js").write_text("custom app")
            (current / "media.json").write_text('{"stage":"old"}')
            (current / "media/old.mp4").write_bytes(b"old")
            (current / "credits.md").write_text("old attribution")
            seed_existing_player(current, stage)
            (stage / "media/new.mp4").write_bytes(b"new")
            (stage / "media/new.jpg").write_bytes(b"poster")
            (stage / "credits.md").write_text("new attribution")
            media = {
                "stage": "preview",
                "variants": [{"height": 360, "src": "media/new.mp4"}],
                "poster": "media/new.jpg",
                "credits": "credits.md",
            }
            atomic_json(stage / "media.json", media)
            media = version_credits(stage, media)
            promote_staged_delivery(stage, current, media)
            self.assertEqual((current / "index.html").read_text(), "custom player")
            self.assertEqual((current / "app.js").read_text(), "custom app")
            self.assertEqual((current / "credits.md").read_text(), "old attribution")
            self.assertEqual((current / "media/old.mp4").read_bytes(), b"old")
            self.assertEqual((current / "media/new.mp4").read_bytes(), b"new")
            published = json.loads((current / "media.json").read_text())
            self.assertEqual(published["credits"], media["credits"])
            self.assertEqual(
                (current / published["credits"]).read_text(), "new attribution"
            )
            self.assertFalse((stage / "media.json").exists())

    def test_invalid_staged_asset_does_not_change_active_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            current, stage = root / "site", root / "stage"
            current.mkdir()
            (stage / "media").mkdir(parents=True)
            (current / "media.json").write_text('{"stage":"old"}')
            (stage / "media/new.jpg").write_bytes(b"poster")
            (stage / "media.json").write_text('{"stage":"new"}')
            media = {
                "variants": [{"src": "../outside.mp4"}],
                "poster": "media/new.jpg",
            }
            with self.assertRaisesRegex(ValueError, "Unsafe staged asset"):
                promote_staged_delivery(stage, current, media)
            self.assertEqual((current / "media.json").read_text(), '{"stage":"old"}')


    def test_symlinked_site_media_dir_rejected_before_promotion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            current, stage, external = root / "site", root / "stage", root / "external"
            current.mkdir()
            (stage / "media").mkdir(parents=True)
            external.mkdir()
            (current / "media").symlink_to(external, target_is_directory=True)
            (current / "media.json").write_text('{"stage":"old"}')
            (stage / "media/new.mp4").write_bytes(b"new")
            (stage / "media/new.jpg").write_bytes(b"poster")
            (stage / "media.json").write_text('{"stage":"new"}')
            media = {
                "variants": [{"src": "media/new.mp4"}],
                "poster": "media/new.jpg",
            }
            with self.assertRaisesRegex(ValueError, "Unsafe Site destination"):
                promote_staged_delivery(stage, current, media)
            self.assertEqual((current / "media.json").read_text(), '{"stage":"old"}')
            self.assertEqual(list(external.iterdir()), [])


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required"
)
class PipelinePrepareStaging(unittest.TestCase):
    def setup_project(self, root):
        project = root / "project"
        project.mkdir()
        scene = project / "scene.json"
        scene.write_text(
            json.dumps(
                {
                    "duration": 0.25,
                    "camera": [{"time": 0, "center": [0, 0], "zoom": 0}],
                }
            )
        )
        video = project / "preview.mp4"
        profile = DEFAULTS["export"]["preview"]
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                "-i", f"color=c=black:s={profile['width']}x{profile['height']}:r={profile['fps']}",
                "-t", "0.25", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(video),
            ],
            check=True,
        )
        atomic_json(
            project / "preview.review.json",
            {"sha256": digest(video), "mode": "preview"},
        )
        site = root / "site"
        (site / ".openai").mkdir(parents=True)
        dist = site / "dist"
        (dist / "media").mkdir(parents=True)
        atomic_json(
            site / ".openai/hosting.json",
            {"project_id": "fixture-site", "static": {"directory": "dist"}},
        )
        (dist / "index.html").write_text("custom player")
        (dist / "app.js").write_text("// custom player logic")
        (dist / "media.json").write_text('{"stage":"old"}')
        (dist / "media/old.mp4").write_bytes(b"old video")
        credits = project / "credits.txt"
        credits.write_text("new credits")
        (dist / "credits.md").write_text("old credits")
        evidence = site / ".geomotion-delivery.json"
        evidence.write_text('{"state":"previous"}')
        binding = root / "binding.json"
        atomic_json(
            binding,
            {"project_id": "fixture-site", "audience": "owner-private",
             "url": "https://example.org"},
        )
        args = [
            "pipeline", "prepare", str(scene), "--video", str(video),
            "--site", str(site), "--title", "Staging fixture",
            "--binding", str(binding), "--credits", str(credits),
        ]
        return site, dist, args

    def test_qa_failure_keeps_existing_site_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            site, dist, args = self.setup_project(root)
            before = {
                str(path.relative_to(site)): path.read_bytes()
                for path in site.rglob("*") if path.is_file()
            }
            with (
                patch("pipeline.require_current_video"),
                patch("pipeline.check", return_value={"automated_pass": False}),
                patch("sys.argv", args),
            ):
                with self.assertRaisesRegex(ValueError, "previous Site files preserved"):
                    pipeline_main()
            after = {
                str(path.relative_to(site)): path.read_bytes()
                for path in site.rglob("*") if path.is_file()
            }
            self.assertEqual(before, after)
            self.assertEqual(list(root.glob(".geomotion-site-stage-*")), [])

    def test_qa_success_promotes_media_but_keeps_old_player(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            site, dist, args = self.setup_project(root)
            with (
                patch("pipeline.require_current_video"),
                patch("pipeline.check", return_value={"automated_pass": True}),
                patch("sys.argv", args),
            ):
                pipeline_main()
            media = json.loads((dist / "media.json").read_text())
            self.assertEqual(media["stage"], "preview")
            self.assertEqual([v["height"] for v in media["variants"]], [360])
            self.assertTrue(all((dist / v["src"]).exists() for v in media["variants"]))
            self.assertEqual((dist / "index.html").read_text(), "custom player")
            self.assertEqual((dist / "app.js").read_text(), "// custom player logic")
            self.assertEqual((dist / "credits.md").read_text(), "old credits")
            self.assertEqual((dist / media["credits"]).read_text(), "new credits")
            self.assertEqual((dist / "media/old.mp4").read_bytes(), b"old video")
            evidence = json.loads((site / ".geomotion-delivery.json").read_text())
            self.assertEqual(evidence["state"], "publication_required")
            self.assertIn("dist/media.json", evidence["files"])
            self.assertEqual(list(root.glob(".geomotion-site-stage-*")), [])


if __name__ == "__main__":
    unittest.main()
