"""Global layout planning regression tests with mocked satellite imagery."""

import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "skills" / "geomotion" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from config import DEFAULTS
from execution import render, worker_limit
from project_state import fingerprint, snapshot
from render_scene import main as render_main


def make_scene(root):
    scene = root / "scene.json"
    scene.write_text(json.dumps({
        "duration": 0.5,
        "text_policy": {"extra_annotations": True},
        "camera": [
            {"time": 0, "center": [0, 0], "zoom": 0},
            {"time": 0.5, "center": [4, 0], "zoom": 0},
        ],
        "callouts": [{
            "start": 0, "end": 0.5, "position": [0, 0],
            "title": "Example", "lines": ["Shared placement"],
            "offset": [-100, -300],
        }],
    }))
    return scene


def run_renderer(scene, destination, *flags, imagery=None):
    with patch("sys.argv", [
        "render_scene", str(scene), "--output", str(destination), *flags,
    ]):
        with patch(
            "render_scene.urllib.request.urlopen",
            side_effect=imagery if imagery is not None else AssertionError("Planner requested imagery"),
        ):
            render_main()


def fake_tile():
    buf = io.BytesIO()
    Image.new("RGB", (256, 256), (37, 78, 83)).save(buf, format="JPEG")
    return buf.getvalue()


class GlobalPlan(unittest.TestCase):
    def test_plan_is_network_free_and_profile_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene = make_scene(root)
            plan = root / "global-layout.json"
            fp = fingerprint(snapshot(scene), "preview")
            run_renderer(scene, plan, "--plan-only", "--plan-fingerprint", fp)
            data = json.loads(plan.read_text())
            self.assertEqual(data["fingerprint"], fp)
            self.assertEqual(data["profile"], {
                "mode": "preview", "width": 360, "height": 640, "fps": 24,
            })
            self.assertEqual(len(data["plans"]), 12)
            self.assertTrue(all("callout:0" in f["positions"] for f in data["plans"]))
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                run_renderer(scene, root / "stale.json", "--plan-only",
                             "--plan-fingerprint", "stale")


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required"
)
class GlobalPlanRender(unittest.TestCase):
    def test_worker_layout_and_pixels_equal_legacy_full_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene = make_scene(root)
            fp = fingerprint(snapshot(scene), "preview")
            plan = root / "global-layout.json"
            run_renderer(scene, plan, "--plan-only", "--plan-fingerprint", fp)
            tile = fake_tile()
            imagery = lambda *a, **kw: io.BytesIO(tile)
            legacy = root / "legacy.mp4"
            shared = root / "shared.mp4"
            segment = ["--start-frame", "5", "--end-frame", "12", "--video-only"]
            run_renderer(scene, legacy, *segment, imagery=imagery)
            run_renderer(scene, shared, *segment, "--layout-plan", str(plan),
                         "--plan-fingerprint", fp, imagery=imagery)
            one = json.loads(legacy.with_suffix(".layout.json").read_text())
            two = json.loads(shared.with_suffix(".layout.json").read_text())
            self.assertEqual(one["composition"], two["composition"])
            self.assertEqual(one["errors"], two["errors"])
            def raw_frames(file):
                return subprocess.check_output([
                    "ffmpeg", "-v", "error", "-i", str(file),
                    "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
                ])
            self.assertEqual(raw_frames(legacy), raw_frames(shared))

    def test_pipeline_plans_once_and_reuses_it_after_segment_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scene = make_scene(root)
            checkpoint = root / "cp"
            output = root / "output.mp4"
            tile = fake_tile()
            actual_run = subprocess.run
            planning_calls = []

            def simulate_render_command(command, **kwargs):
                if len(command) > 1 and str(command[1]).endswith("render_scene.py"):
                    if "--plan-only" in command:
                        planning_calls.append("plan")
                    with (
                        patch("sys.argv", ["render_scene", *command[2:]]),
                        patch("render_scene.urllib.request.urlopen",
                              side_effect=lambda *a, **kw: io.BytesIO(tile)),
                    ):
                        render_main()
                    return subprocess.CompletedProcess(command, 0)
                return actual_run(command, **kwargs)

            with (
                patch.dict(DEFAULTS["execution"], {"checkpoint_seconds": 0.2}),
                patch("execution.worker_limit", return_value=1),
                patch("execution.subprocess.run", side_effect=simulate_render_command),
            ):
                first = render(scene, "preview", output, checkpoint)
                self.assertEqual(planning_calls, ["plan"])
                self.assertEqual(first["rendered_segments"], 3)
                global_plan = checkpoint / "global-layout.json"
                self.assertTrue(global_plan.is_file())
                # Resume should reuse the existing fingerprint-matched global plan.
                (checkpoint / "5-10.mp4").write_bytes(b"corrupted")
                second = render(scene, "preview", output, checkpoint)
                self.assertEqual(planning_calls, ["plan"])
                self.assertEqual(second["rendered_segments"], 1)
                self.assertEqual(second["resumed_segments"], 2)
                # An altered global plan must be regenerated before another
                # missing segment is rendered, even with unchanged input files.
                global_plan.write_text('{"version":1,"plans":[]}')
                (checkpoint / "0-5.mp4").write_bytes(b"corrupted")
                third = render(scene, "preview", output, checkpoint)
                self.assertEqual(planning_calls, ["plan", "plan"])
                self.assertEqual(third["rendered_segments"], 1)
                self.assertEqual(
                    len(json.loads(output.with_suffix(".layout.json").read_text())
                        ["composition"]["frames"]),
                    12,
                )


if __name__ == "__main__":
    unittest.main()
