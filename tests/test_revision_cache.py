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
SCRIPTS = ROOT / ".agents/skills/geomotion/scripts"
sys.path.insert(0, str(SCRIPTS))

from config import DEFAULTS
from project_state import snapshot
from revision_cache import render_key, render_keys


class RevisionDependencies(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / "scene.json"
        self.scene = {
            "duration": 4,
            "text_policy": {"extra_annotations": True},
            "camera": [{"time": 0, "center": [0, 0], "zoom": 1}],
            "export": {"preview": {"fps": 4}},
        }
        self.ranges = [(0, 4), (4, 8), (8, 12), (12, 16)]

    def keys(self, state=None):
        self.path.write_text(json.dumps(self.scene))
        return render_keys(self.path, "preview", self.ranges, state=state)

    def image(self, name, color):
        Image.new("RGBA", (24, 24), color).save(self.root / name)

    def test_late_marker_callout_route_preserve_earlier_ranges(self):
        for group, item in (
            ("markers", {"position": [0, 0], "label": "Here"}),
            ("callouts", {"position": [0, 0], "title": "Evidence"}),
            ("routes", {"points": [[0, 0], [1, 1]], "width": 3}),
        ):
            with self.subTest(group=group):
                self.scene.pop("markers", None)
                self.scene.pop("callouts", None)
                self.scene.pop("routes", None)
                before = self.keys()
                self.scene[group] = [{"start": 2, "end": 3, **item}]
                after = self.keys()
                self.assertEqual(before[(0, 4)], after[(0, 4)])
                self.assertEqual(before[(4, 8)], after[(4, 8)])
                self.assertNotEqual(before[(8, 12)], after[(8, 12)])

    def test_past_layout_dependency_is_retained(self):
        self.scene["callouts"] = [{"start": 0, "end": 1, "position": [0, 0], "title": "A"}]
        before = self.keys()
        self.scene["callouts"][0]["title"] = "Changed"
        after = self.keys()
        self.assertNotEqual(before[(12, 16)], after[(12, 16)])

    def test_route_persists_after_end_until_hide_at(self):
        self.scene["routes"] = [{"start": 0, "end": 1, "points": [[0, 0], [1, 1]]}]
        before = self.keys()
        self.scene["routes"][0]["color"] = [255, 0, 0]
        changed = self.keys()
        self.assertNotEqual(before[(12, 16)], changed[(12, 16)])
        self.scene["routes"][0]["hide_at"] = 2
        self.assertNotEqual(changed[(12, 16)], self.keys()[(12, 16)])

    def test_future_assets_do_not_invalidate_prefix_active_assets_do(self):
        self.image("archive.png", "red")
        self.scene["callouts"] = [{"start": 2, "end": 3, "position": [0, 0], "image": "archive.png"}]
        before = self.keys()
        self.image("archive.png", "blue")
        after = self.keys()
        self.assertEqual(before[(0, 4)], after[(0, 4)])
        self.assertNotEqual(before[(8, 12)], after[(8, 12)])

    def test_audio_metadata_registered_input_and_audio_profile_do_not_change_keys(self):
        before = self.keys()
        self.scene.update(audio="voice.wav", metadata={"note": "new"}, inputs={"narration": ["script.txt"]})
        self.scene["timeline"] = {"audio_clock": "output"}
        self.scene["export"]["preview"]["audio_bitrate"] = "200k"
        self.assertEqual(before, self.keys())

    def test_actual_cue_file_contents_and_global_reservation(self):
        before = self.keys()
        cue_path = self.root / "cues.json"
        cue_path.write_text(json.dumps([{"start": 2, "end": 3, "text": "A"}]))
        self.scene["subtitle_cues"] = "cues.json"
        reserved = self.keys()
        self.assertNotEqual(before[(0, 4)], reserved[(0, 4)])
        cue_path.write_text(json.dumps([{"start": 2, "end": 3, "text": "Changed"}]))
        after = self.keys()
        self.assertEqual(reserved[(0, 4)], after[(0, 4)])
        self.assertNotEqual(reserved[(8, 12)], after[(8, 12)])

    def test_cuts_use_actual_source_times(self):
        before = self.keys()
        self.scene["duration"] = 5
        self.scene["timeline"] = {"cuts": [[2, 3]]}
        after = self.keys()
        self.assertEqual(before[(0, 4)], after[(0, 4)])
        self.assertEqual(before[(4, 8)], after[(4, 8)])
        self.assertNotEqual(before[(8, 12)], after[(8, 12)])

    def test_future_camera_interpolation_and_global_imagery_level(self):
        self.scene["camera"].append({"time": 3, "center": [10, 0], "zoom": 1})
        before = self.keys()
        self.scene["camera"][1]["center"] = [20, 0]
        after = self.keys()
        self.assertNotEqual(before[(0, 4)], after[(0, 4)])
        # A future jump in maximum tile level changes even a held early pose.
        self.scene["camera"] = [{"time": 0, "center": [0, 0], "zoom": 1},
                                {"time": 2, "center": [0, 0], "zoom": 1},
                                {"time": 3, "center": [0, 0], "zoom": 1}]
        held = self.keys()
        self.scene["camera"][2]["zoom"] = 2
        self.assertNotEqual(held[(0, 4)], self.keys()[(0, 4)])

    def test_camera_change_after_held_segment_preserves_it(self):
        self.scene["camera"] += [{"time": 2, "center": [0, 0], "zoom": 1},
                                 {"time": 3, "center": [3, 0], "zoom": 1}]
        before = self.keys()
        self.scene["camera"][2]["center"] = [7, 0]
        after = self.keys()
        self.assertEqual(before[(0, 4)], after[(0, 4)])
        self.assertNotEqual(before[(8, 12)], after[(8, 12)])

    def test_world_overlay_asset_and_shared_image_conversion(self):
        self.image("overlay.png", "red")
        self.scene["world_overlays"] = [{"image": "overlay.png", "start": 2, "end": 4}]
        before = self.keys()
        self.image("overlay.png", "blue")
        after = self.keys()
        self.assertEqual(before[(0, 4)], after[(0, 4)])
        self.assertNotEqual(before[(8, 12)], after[(8, 12)])
        self.scene["markers"] = [{"start": 0, "end": 1, "position": [0, 0], "flag": "overlay.png"}]
        shared = self.keys()
        self.scene.pop("world_overlays")
        self.assertNotEqual(shared[(0, 4)], self.keys()[(0, 4)])

    def test_region_geometry_nested_focus_crop_and_archive_resolution(self):
        geometry = self.root / "land.json"
        geometry.write_text(json.dumps({"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}))
        self.scene["regions"] = [{"id": "land", "geojson": "land.json", "focus_strokes": [{"start": 2, "end": 3, "reveal": 1}]}]
        before = self.keys()
        self.scene["regions"][0]["focus_strokes"][0]["color"] = [255, 0, 0]
        changed = self.keys()
        self.assertEqual(before[(0, 4)], changed[(0, 4)])
        self.assertNotEqual(before[(8, 12)], changed[(8, 12)])
        geometry.write_text(geometry.read_text().replace("[1, 1]", "[2, 1]"))
        self.assertNotEqual(changed[(0, 4)], self.keys()[(0, 4)])
        self.image("original.png", "red")
        manifest = {"version": 1, "archives": [{"id": "a", "file": "original.png", "source_url": "https://example.org/a", "credit": "Archive", "context": "Verified object", "fact_status": "verified", "reuse_status": "public_domain", "capture_date": "1900", "date_basis": "Catalog"}]}
        (self.root / "archive.json").write_text(json.dumps(manifest))
        self.scene["archive_manifest"] = "archive.json"
        self.scene["callouts"] = [{"archive_id": "a", "start": 2, "end": 3, "position": [0, 0], "image_crop": [0, 0, 12, 12]}]
        original = self.keys()
        self.scene["callouts"][0]["image_crop"] = [2, 2, 14, 14]
        cropped = self.keys()
        self.assertEqual(original[(0, 4)], cropped[(0, 4)])
        self.assertNotEqual(original[(8, 12)], cropped[(8, 12)])

    def test_renderer_font_profile_and_reduced_default_dependencies(self):
        before = self.keys()
        state = snapshot(self.path)
        self.assertEqual(before, self.keys(state))
        state["configuration"]["render_scene.py"] = "new renderer"
        self.assertNotEqual(before[(0, 4)], self.keys(state)[(0, 4)])
        state = snapshot(self.path)
        state["configuration"]["OpenSans-Regular.ttf"] = "new font"
        self.assertNotEqual(before[(0, 4)], self.keys(state)[(0, 4)])
        self.scene["export"]["preview"]["crf"] = 25
        self.assertNotEqual(before[(0, 4)], self.keys()[(0, 4)])
        with patch.dict(DEFAULTS["execution"], {"max_workers": 123}), patch.dict(DEFAULTS["delivery"], {"format": "player"}):
            same_profile = self.keys()
        self.assertEqual(same_profile, self.keys())

    def test_batch_single_range_paths_and_bad_ranges(self):
        batch = self.keys()
        self.assertEqual(batch[(0, 4)], render_key(self.path, "preview", 0, 4))
        other = self.root / "renamed.json"
        other.write_text(self.path.read_text())
        self.assertEqual(batch, render_keys(other, "preview", self.ranges))
        for interval in ((-1, 4), (0, 17), (4, 4), (0.0, 4)):
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                render_keys(self.path, "preview", [interval])
        self.scene["unknown_renderer"] = {}
        with self.assertRaises(ValueError):
            self.keys()

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required")
    def test_real_renderer_prior_range_survives_late_marker_without_network(self):
        from render_scene import main as render_main
        self.scene["duration"] = 2
        self.scene["camera"][0]["zoom"] = 0
        self.ranges = [(0, 4), (4, 8)]
        before = self.keys()
        tile = io.BytesIO()
        Image.new("RGB", (256, 256), (32, 70, 80)).save(tile, "PNG")

        def render(name):
            output = self.root / name
            with patch("urllib.request.urlopen", side_effect=lambda *a, **k: io.BytesIO(tile.getvalue())), patch.object(sys, "argv", ["render_scene.py", str(self.path), "--output", str(output), "--video-only", "--start-frame", "0", "--end-frame", "4"]):
                render_main()
            return subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(output), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])

        old_pixels = render("old.mp4")
        self.scene["markers"] = [{"start": 1, "end": 2, "position": [0, 0], "label": "Later"}]
        after = self.keys()
        self.assertEqual(before[(0, 4)], after[(0, 4)])
        self.assertNotEqual(before[(4, 8)], after[(4, 8)])
        self.assertEqual(old_pixels, render("revised.mp4"))


if __name__ == "__main__":
    unittest.main()
