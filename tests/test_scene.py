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
from render_scene import camera_at, main, validate


class SceneInput(unittest.TestCase):
    def test_camera_short_path_across_antimeridian(self):
        keys = [
            {"time": 0, "center": [179, 0], "zoom": 4, "rotation": 350},
            {"time": 2, "center": [-179, 2], "zoom": 6, "rotation": 10},
        ]
        c = camera_at(keys, 1)
        self.assertEqual(c["center"], [180, 1])
        self.assertEqual(c["zoom"], 5)
        self.assertEqual(c["rotation"], 360)

    def test_scene_requires_explicit_duration_and_camera(self):
        with self.assertRaises(ValueError):
            validate({"camera": [{"time": 0, "center": [0, 0], "zoom": 2}]})
        with self.assertRaises(ValueError):
            validate({"duration": 3})


@unittest.skipUnless(
    shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required"
)
class SceneRender(unittest.TestCase):
    def test_imagery_denial_stops_without_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            scene = d / "scene.json"
            out = d / "preview.mp4"
            scene.write_text(
                json.dumps(
                    {
                        "duration": 0.05,
                        "camera": [{"time": 0, "center": [0, 0], "zoom": 0}],
                    }
                )
            )
            with (
                patch("sys.argv", ["render_scene", str(scene), "--output", str(out)]),
                patch(
                    "render_scene.urllib.request.urlopen",
                    side_effect=OSError("403 Forbidden"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "403 Forbidden"):
                    main()
            self.assertFalse(out.exists())
            self.assertFalse((d / "cache").exists())

    def test_render_composed_scene_without_topic_or_network(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            flag = Image.new("RGBA", (40, 24), "white")
            flag.paste("red", (0, 0, 40, 12))
            flag.save(d / "flag.png")
            atlas = Image.new("RGBA", (64, 16))
            for i, c in enumerate(["red", "green", "blue", "yellow"]):
                atlas.paste(c, (16 * i, 0, 16 * i + 16, 16))
            atlas.save(d / "atlas.png")
            (d / "atlas.json").write_text(
                json.dumps(
                    {
                        "headings": 4,
                        "columns": 4,
                        "frame_width": 16,
                        "frame_height": 16,
                        "anchor": [8, 12],
                    }
                )
            )
            (d / "area.geojson").write_text(
                json.dumps(
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-0.3, -0.3],
                                [0.3, -0.3],
                                [0.3, 0.3],
                                [-0.3, 0.3],
                                [-0.3, -0.3],
                            ]
                        ],
                    }
                )
            )
            scene = {
                "duration": 0.5,
                "basemap": {"type": "satellite", "provider": "esri_world_imagery"},
                "camera": [{"time": 0, "center": [0, 0], "zoom": 8}],
                "regions": [
                    {
                        "geojson": "area.geojson",
                        "flag": "flag.png",
                        "fill": [20, 100, 140],
                        "reveal": 0.1,
                    }
                ],
                "markers": [{"position": [0, 0], "label": "Point", "flag": "flag.png"}],
                "routes": [
                    {
                        "points": [[-0.2, 0], [0.2, 0]],
                        "start": 0,
                        "end": 0.4,
                        "atlas": "atlas.png",
                        "atlas_metadata": "atlas.json",
                    }
                ],
                "callouts": [
                    {
                        "position": [0, 0],
                        "title": "Info",
                        "lines": ["Value"],
                        "image": "flag.png",
                    }
                ],
            }
            (d / "scene.json").write_text(json.dumps(scene))
            out = d / "preview.mp4"
            tile = io.BytesIO()
            Image.new("RGB", (256, 256), (25, 55, 40)).save(tile, format="JPEG")
            with (
                patch(
                    "sys.argv",
                    ["render_scene", str(d / "scene.json"), "--output", str(out)],
                ),
                patch(
                    "render_scene.urllib.request.urlopen",
                    side_effect=lambda *a, **k: io.BytesIO(tile.getvalue()),
                ),
            ):
                main()
            raw = subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "stream=width,height,r_frame_rate",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    str(out),
                ]
            )
            data = json.loads(raw)
            self.assertEqual(data["streams"][0]["width"], 360)
            self.assertEqual(data["streams"][0]["height"], 640)
            self.assertEqual(data["streams"][0]["r_frame_rate"], "24/1")
            self.assertAlmostEqual(float(data["format"]["duration"]), 0.5, places=2)
            self.assertEqual(len(list(d.glob("preview_frame_*.jpg"))), 3)


if __name__ == "__main__":
    unittest.main()
