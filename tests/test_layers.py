import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
        / ".agents"
        / "skills"
        / "geomotion"
        / "scripts"
    ),
)
from map_assets import clip_flag, flagpole, select_sprite
from PIL import Image
from render_scene import color
from config import DEFAULTS


class GeographicLayers(unittest.TestCase):
    def test_layer_color_follows_preset_without_overriding_authored_color(self):
        with patch.dict(DEFAULTS["palette"], outline="#123456"):
            self.assertEqual(color(None), (18, 52, 86))
            self.assertEqual(color([255, 46, 66]), (255, 46, 66))

    def test_disconnected_islands_and_hole_do_not_fill_sea(self):
        flag = Image.new("RGBA", (2, 2), (255, 0, 0, 255))
        regions = [
            [
                [(2, 2), (20, 2), (20, 20), (2, 20)],
                [(7, 7), (12, 7), (12, 12), (7, 12)],
            ],
            [[(30, 3), (37, 3), (37, 10), (30, 10)]],
        ]
        result = clip_flag(flag, regions, (40, 24))
        self.assertEqual(result.getpixel((3, 3))[3], 255)
        self.assertEqual(result.getpixel((8, 8))[3], 0)
        self.assertEqual(result.getpixel((25, 5))[3], 0)
        self.assertEqual(result.getpixel((33, 5))[3], 255)

    def test_heading_accounts_for_camera_rotation_and_wrap(self):
        atlas = Image.new("RGBA", (32, 8))
        for i, color in enumerate(["red", "green", "blue", "white"]):
            atlas.paste(Image.new("RGBA", (8, 8), color), (i * 8, 0))
        meta = {
            "headings": 4,
            "columns": 4,
            "frame_width": 8,
            "frame_height": 8,
            "anchor": [4, 6],
        }
        a, anchor, index = select_sprite(atlas, meta, 90, 90)
        self.assertEqual(index, 0)
        self.assertEqual(anchor, (4, 6))
        self.assertEqual(a.getpixel((4, 4)), (255, 0, 0, 255))
        self.assertEqual(select_sprite(atlas, meta, 359)[2], 0)

    def test_invalid_atlas_fails_instead_of_inventing_views(self):
        with self.assertRaises(ValueError):
            select_sprite(
                Image.new("RGBA", (4, 4)),
                {
                    "headings": 32,
                    "columns": 8,
                    "frame_width": 64,
                    "frame_height": 64,
                    "anchor": [32, 48],
                },
                90,
            )

    def test_animation_preserves_heading_and_ground_anchor(self):
        atlas = Image.new("RGBA", (32, 8))
        for i, color in enumerate(["red", "yellow", "blue", "white"]):
            atlas.paste(Image.new("RGBA", (8, 8), color), (i * 8, 0))
        meta = dict(headings=2, columns=4, frame_width=8, frame_height=8,
                    anchor=[4, 7], animation_frames=2, animation_fps=4)
        first, anchor, heading = select_sprite(atlas, meta, 180, animation_time_s=0)
        next_frame, next_anchor, next_heading = select_sprite(atlas, meta, 180, animation_time_s=.25)
        self.assertEqual(first.getpixel((4, 4)), (0, 0, 255, 255))
        self.assertEqual(next_frame.getpixel((4, 4)), (255, 255, 255, 255))
        self.assertEqual((anchor, heading), (next_anchor, next_heading))
        self.assertEqual(select_sprite(atlas, meta, 180, animation_time_s=.5)[0].tobytes(), first.tobytes())

    def test_incomplete_animation_atlas_is_rejected(self):
        with self.assertRaises(ValueError):
            select_sprite(Image.new("RGBA", (8, 8)),
                          dict(headings=1, columns=1, frame_width=8, frame_height=8,
                               anchor=[4, 7], animation_frames=2), 0)

    def test_flagpole_ground_stays_pinned_during_flutter(self):
        flag = Image.new("RGBA", (20, 12), "red")
        for t in [0, 0.4, 1]:
            layer = flagpole(flag, (40, 80), t, canvas_size=(120, 100))
            self.assertGreater(layer.getpixel((40, 79))[3], 0)


if __name__ == "__main__":
    unittest.main()
