import io
import json
import math
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".agents/skills/geomotion/scripts"))
from composition import Composer, validate_composition, pixel_box
from config import DEFAULTS
from layout import overlaps, inspect_boxes
from render_scene import main
from timeline import resolve_scene


class CompositionRules(unittest.TestCase):
    def test_panel_avoids_focus_subtitle_and_other_panel(self):
        composer = Composer((360, 640), 24)
        focus = (80, 200, 280, 410)
        reserved = [(20, 460, 340, 530)]
        panels = [
            {
                "id": "photo",
                "kind": "media",
                "size": (150, 110),
                "preferred": (120, 260),
            },
            {
                "id": "info",
                "kind": "callout",
                "size": (70, 35),
                "preferred": (120, 260),
            },
        ]
        positions = composer.step(panels, [focus], reserved)
        for box in positions.values():
            self.assertFalse(overlaps(box, focus))
            self.assertFalse(overlaps(box, reserved[0]))
        self.assertFalse(overlaps(*positions.values()))

    def test_budget_and_no_space_fail_without_discarding_media(self):
        composer = Composer((360, 640), 24)
        panels = [
            {"id": str(i), "kind": "media", "size": (100, 100), "preferred": (10, 10)}
            for i in range(2)
        ]
        with self.assertRaisesRegex(ValueError, "media"):
            composer.step(panels, [])
        with self.assertRaisesRegex(ValueError, "No safe continuous placement"):
            composer.step(panels[:1], [(0, 0, 360, 640)])
        with self.assertRaisesRegex(ValueError, "markers"):
            composer.step([], [], counts={"markers": 7})
        with self.assertRaisesRegex(ValueError, "area budget"):
            Composer((360, 640), 24, {"max_annotation_area_fraction": 0.01}).step(
                panels[:1], []
            )

    def test_large_vehicle_footprint_consumes_area_and_blocks_panel(self):
        composer = Composer((360, 640), 24)
        with self.assertRaisesRegex(ValueError, "area budget"):
            composer.step([], [], footprints=[(0, 0, 360, 600)])
        result = composer.step(
            [
                {
                    "id": "caption",
                    "kind": "callout",
                    "size": (80, 40),
                    "preferred": (20, 20),
                }
            ],
            [],
            footprints=[(10, 10, 130, 100)],
        )
        self.assertFalse(overlaps(result["caption"], (10, 10, 130, 100)))

    def test_tracking_has_bounded_motion_and_replay_matches(self):
        def sequence():
            composer = Composer((360, 640), 24)
            result = []
            for n in range(20):
                result.append(
                    composer.step(
                        [
                            {
                                "id": "photo",
                                "kind": "media",
                                "size": (90, 70),
                                "preferred": (15 + n * 6, 15),
                            }
                        ],
                        [(80, 220, 280, 400)],
                    )
                )
            return result, composer.step_limit

        full, speed = sequence()
        replayed, _ = sequence()
        self.assertEqual(full[10:], replayed[10:])
        self.assertTrue(
            any(full[n]["photo"] != full[n - 1]["photo"] for n in range(1, 20))
        )
        self.assertTrue(
            all(
                math.dist(full[n]["photo"][:2], full[n - 1]["photo"][:2])
                <= speed + 1e-7
                for n in range(1, 20)
            )
        )

    def test_cta_is_centered_above_focus_in_both_profiles(self):
        for size, fps in (((360, 640), 24), ((1080, 1920), 30)):
            composer = Composer(size, fps)
            focus = pixel_box((0.2, 0.45, 0.8, 0.6), size)
            w, h = size[0] * 0.6, size[1] * 0.09
            result = composer.step(
                [
                    {
                        "id": "cta",
                        "kind": "cta",
                        "size": (w, h),
                        "preferred": ((size[0] - w) / 2, focus[1] - composer.gap - h),
                    }
                ],
                [focus],
            )["cta"]
            self.assertAlmostEqual((result[0] + result[2]) / 2, size[0] / 2)
            self.assertLess(result[3], focus[1])

    def test_metadata_validation_and_phrase_clock(self):
        scene = {
            "duration": 2,
            "regions": [{"id": "province", "geojson": "region.json"}],
            "timeline": {"events": [{"id": "phrase", "start": 1, "end": 2}]},
            "focuses": [{"event": "phrase", "region_id": "province"}],
            "cta": {"event": "phrase", "text": "WHY AGAIN?"},
        }
        resolved, _ = resolve_scene(scene)
        validate_composition(resolved)
        self.assertEqual(resolved["cta"]["start"], 1)
        self.assertEqual(resolved["focuses"][0]["end"], 2)
        scene["focuses"][0]["region_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "Unknown focus region"):
            validate_composition(scene)
        scene["focuses"] = []
        scene["cta"] = {"text": "CTA", "anchor_normalized": [0.5, 0.5]}
        with self.assertRaisesRegex(ValueError, "Unsupported CTA fields"):
            validate_composition(scene)
        scene["focuses"] = []
        scene["cta"] = None
        resolve_scene(scene)
        self.assertIn(
            "overlaps",
            inspect_boxes(
                [("callout:a", (0, 0, 20, 20)), ("title:b", (10, 10, 30, 30))],
                (100, 100),
            )[0],
        )


@unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
class RenderComposition(unittest.TestCase):
    def test_real_render_keeps_map_clear_and_segment_replays_same_layout(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            Image.new("RGB", (600, 400), "#d9b05d").save(root / "photo.jpg")
            scene = {
                "duration": 1,
                "text_policy": {"media_captions": True, "extra_annotations": True},
                "camera": [
                    {"time": 0, "center": [0, 0], "zoom": 6},
                    {"time": 1, "center": [1, 0], "zoom": 6},
                ],
                "focuses": [{"start": 0, "end": 1, "bounds": [-0.6, -0.6, 0.6, 0.6]}],
                "callouts": [
                    {
                        "start": 0,
                        "end": 0.5,
                        "position": [0, 0],
                        "image": "photo.jpg",
                        "title": "Foto uji",
                        "lines": ["Arsip untuk tes layout"],
                    }
                ],
                "subtitles": [{"start": 0, "end": 1, "text": "Frasa aktual."}],
                "cta": {"start": 0.55, "end": 1, "text": "KENAPA\nBERULANG?"},
            }
            path = root / "scene.json"
            path.write_text(json.dumps(scene))
            tile = io.BytesIO()
            Image.new("RGB", (256, 256), "#385747").save(tile, "JPEG")

            def render(out, extra=()):
                with patch(
                    "sys.argv",
                    ["render_scene", str(path), "--output", str(out), *extra],
                ), patch(
                    "render_scene.urllib.request.urlopen",
                    side_effect=lambda *a, **k: io.BytesIO(tile.getvalue()),
                ):
                    main()
                return json.loads(out.with_suffix(".layout.json").read_text())

            full = render(root / "preview.mp4")
            part = render(
                root / "part.mp4",
                ["--start-frame", "12", "--end-frame", "24", "--video-only"],
            )
            self.assertFalse(full["errors"])
            frames = full["composition"]["frames"]
            self.assertEqual(part["composition"]["frames"], frames[12:])
            self.assertTrue(any("callout:0" in f["positions"] for f in frames))
            self.assertTrue(any("cta" in f["positions"] for f in frames))
            for frame in frames:
                for box in frame["positions"].values():
                    self.assertFalse(
                        any(overlaps(box, focus) for focus in frame["focuses"])
                    )
            for frame in frames:
                if "cta" in frame["positions"]:
                    box = frame["positions"]["cta"]
                    self.assertAlmostEqual((box[0] + box[2]) / 2, 180)
                    self.assertLess(box[3], frame["focuses"][0][1])


if __name__ == "__main__":
    unittest.main()
