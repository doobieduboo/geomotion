"""Behavior checks for editable title layers and scene-relative timing."""

import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/skills/geomotion/scripts"
sys.path.insert(0, str(SCRIPTS))
from config import SKILL_ROOT
from title_layer import render_title, title_config


class EditableTitles(unittest.TestCase):
    def setUp(self):
        self.definition = json.loads(
            (SKILL_ROOT / "library/titles/title-01.json").read_text()
        )

    def test_transparent_lifetime_and_optional_exit(self):
        config = title_config(self.definition, {"timing": {"exit_seconds": 0.5}})
        self.assertIsNone(render_title(config, 0, (360, 640)).getbbox())
        self.assertIsNone(render_title(config, -1, (360, 640)).getbbox())
        self.assertIsNotNone(render_title(config, 4, (360, 640)).getbbox())
        self.assertIsNone(
            render_title(config, config["duration"], (360, 640)).getbbox()
        )
        alpha = render_title(config, config["duration"] - 0.1, (360, 640)).getchannel(
            "A"
        )
        self.assertLessEqual(alpha.getextrema()[1], 52)

    def test_text_replacement_is_editable_and_does_not_mutate_source(self):
        config = title_config(
            self.definition,
            {"content": {"headline": "KALIMANTAN", "subline": "HUTAN DAN LAHAN"}},
        )
        self.assertEqual(self.definition["content"]["headline"], "TRENDY")
        frame = render_title(config, 4, (360, 640))
        bounds = frame.getbbox()
        self.assertIsNotNone(bounds)
        self.assertGreaterEqual(bounds[0], 0)
        self.assertLessEqual(bounds[2], 360)
        original = render_title(title_config(self.definition), 4, (360, 640))
        self.assertNotEqual(frame.tobytes(), original.tobytes())

    def test_invalid_timeline_is_rejected(self):
        with self.assertRaises(ValueError):
            title_config(self.definition, {"timing": {"enter": [2, 1]}})
        with self.assertRaises(ValueError):
            title_config(self.definition, {"content": {"headline": ""}})
