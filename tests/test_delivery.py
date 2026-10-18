"""Check the delivery stage boundary with real encoded inputs."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/skills/geomotion/scripts"
sys.path.insert(0, str(SCRIPTS))
from config import DEFAULTS


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required"
)
class DeliveryStages(unittest.TestCase):
    def make_video(self, path, stage):
        profile = DEFAULTS["export"][stage]
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                f"color=c=black:s={profile['width']}x{profile['height']}:r={profile['fps']}",
                "-t",
                "0.1",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(path),
            ],
            check=True,
        )

    def prepare(self, source, stage, output):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "prepare_delivery.py"),
                str(source),
                "--stage",
                stage,
                "--output",
                str(output),
                "--title",
                "Stage check",
            ],
            capture_output=True,
            text=True,
        )

    def test_stage_qualities_and_default_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for stage in ("preview", "final"):
                with self.subTest(stage=stage):
                    source = root / f"{stage}.mp4"
                    self.make_video(source, stage)
                    out = root / stage
                    result = self.prepare(source, stage, out)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    manifest = json.loads((out / "media.json").read_text())
                    self.assertEqual(
                        [v["height"] for v in manifest["variants"]],
                        [360] if stage == "preview" else [360, 1080],
                    )
                    self.assertEqual(
                        manifest["defaultQuality"], 360 if stage == "preview" else 1080
                    )
                    self.assertTrue(
                        all((out / v["src"]).is_file() for v in manifest["variants"])
                    )

    def test_preview_cannot_be_delivered_as_native_final(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "preview.mp4"
            self.make_video(source, "preview")
            result = self.prepare(source, "final", root / "site")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Never upscale", result.stderr)
            self.assertFalse((root / "site/media.json").exists())
