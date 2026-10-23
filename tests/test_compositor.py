"""Real native-size preview fixtures; no imagery/network or production renders."""
import json
from fractions import Fraction
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / ".agents/skills/geomotion/scripts"
sys.path.insert(0, str(SCRIPTS))
from compositor import composite, plan, _audio_packets, _video_packets
from config import DEFAULTS
from project_state import atomic_json, digest


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class NativeComposite(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.cp = self.root / "base-checkpoint"
        self.cp.mkdir()
        cfg = DEFAULTS["export"]["preview"]
        segments = {}
        for start, color in ((0, "blue"), (12, "green")):
            key = f"{start}-{start+12}"
            path = self.cp / f"{key}.mp4"
            self.runff("-f", "lavfi", "-i", f"color={color}:s=360x640:r=24:d=0.5", "-an", "-c:v", "libx264", "-preset", cfg["preset"], "-crf", str(cfg["crf"]), "-maxrate", cfg["maxrate"], "-bufsize", cfg["bufsize"], "-pix_fmt", "yuv420p", str(path))
            segments[key] = {"sha256": digest(path), "frames": 12}
        atomic_json(self.cp / "checkpoint.json", {"version": 1, "fingerprint": "fixture-native-v1", "segments": segments})
        (self.cp / "concat.txt").write_text("file '0-12.mp4'\nduration 0.5\nfile '12-24.mp4'\nduration 0.5\n")
        self.base = self.root / "base.mp4"
        self.runff("-f", "concat", "-safe", "1", "-i", str(self.cp / "concat.txt"), "-itsoffset", "0.125", "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", str(self.base))
        self.bind_receipt()
        overlay = Image.new("RGBA", (40, 30), (255, 0, 0, 255))
        for x in range(20, 40):
            for y in range(30):
                overlay.putpixel((x, y), (255, 0, 0, 0))
        overlay.save(self.root / "overlay.png")
        self.recipe = self.root / "recipe.json"
        self.data = {"version": 1, "base_video": "base.mp4", "base_checkpoint": "base-checkpoint", "overlays": [{"image": "overlay.png", "start": .125, "end": .375, "position": [50, 60]}]}
        self.save()
        self.output = self.root / "result.mp4"
        self.checkpoint = self.root / "composite"

    def tearDown(self):
        self.temporary.cleanup()

    def runff(self, *args):
        subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)

    def save(self):
        atomic_json(self.recipe, self.data)

    def bind_receipt(self):
        atomic_json(self.base.with_suffix(".render.json"), {"fingerprint": "fixture-native-v1", "sha256": digest(self.base), "frames": 24})

    def render(self):
        return composite(self.recipe, self.output, self.checkpoint, mode="preview")

    def frame(self, n):
        raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(self.output), "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
        return Image.frombytes("RGB", (360, 640), raw)

    def test_overlay_native_pixels_tail_audio_and_partial_resume(self):
        inspection = plan(self.recipe, "preview")
        self.assertEqual(inspection["composited_ranges"], [[0, 12]])
        report = self.render()
        self.assertEqual(report["copied_ranges"], [[12, 24]])
        self.assertEqual(report["frames"], 24)
        self.assertEqual(_audio_packets(self.base), _audio_packets(self.output))
        self.assertEqual([p for p in _video_packets(self.base, 24) if p[0] >= 12], [p for p in _video_packets(self.output, 24) if p[0] >= 12])
        frame = self.frame(5)
        self.assertGreater(frame.getpixel((55, 65))[0], 220)
        self.assertGreater(frame.getpixel((80, 65))[2], 220)  # PNG transparency
        self.assertGreater(frame.getpixel((45, 65))[2], 220)  # exact placement
        self.assertGreater(self.frame(1).getpixel((55, 65))[2], 220)
        first_hash = digest(self.checkpoint / "0-12.mp4")
        clean_tail = digest(self.cp / "12-24.mp4")
        with (self.checkpoint / "12-24.mp4").open("r+b") as stream:
            stream.write(b"corrupt")
        self.assertEqual(digest(self.cp / "12-24.mp4"), clean_tail)
        self.render()  # Recover only the damaged derived chunk.
        self.assertEqual(digest(self.checkpoint / "12-24.mp4"), clean_tail)
        self.data["overlays"].append({"image": "overlay.png", "start": .625, "end": .875, "position": [80, 90]})
        self.save()
        report = self.render()
        self.assertEqual(report["resumed_ranges"], [[0, 12]])
        self.assertEqual(digest(self.checkpoint / "0-12.mp4"), first_hash)
        self.assertFalse(self.output.with_suffix(".render.json").exists())
        self.assertTrue(self.output.with_suffix(".composite.json").exists())

    def test_pipeline_composite_uses_one_workspace_and_reports_stale_assets(self):
        import contextlib,io
        import project_workspace as workspace
        from pipeline import main
        arguments=['pipeline','composite',str(self.recipe),'--mode','preview','--output',str(self.output),'--checkpoint',str(self.checkpoint)]
        with patch('sys.argv',arguments),contextlib.redirect_stdout(io.StringIO()):
            main()
        state=workspace.default_path(self.recipe)
        loaded=workspace.load(state)
        self.assertEqual(loaded['active_kind'],'composite')
        self.assertTrue(loaded['composite_available'])
        self.assertTrue(loaded['active_sources_current'])
        Image.new('RGBA',(40,30),'yellow').save(self.root/'overlay.png')
        loaded=workspace.load(state)
        self.assertTrue(loaded['composite_available'])
        self.assertFalse(loaded['active_sources_current'])

    def test_bad_receipt_packet_binding_bounds_and_final_gate(self):
        with self.assertRaisesRegex(ValueError, "explicit user request"):
            composite(self.recipe, self.output, self.checkpoint)
        receipt = self.base.with_suffix(".render.json")
        record = json.loads(receipt.read_text())
        record["sha256"] = "bad"
        atomic_json(receipt, record)
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.render()
        self.bind_receipt()
        manifest_path = self.cp / "checkpoint.json"
        manifest = json.loads(manifest_path.read_text())
        original = (self.cp / "0-12.mp4").read_bytes()
        (self.cp / "0-12.mp4").write_bytes((self.cp / "12-24.mp4").read_bytes())
        manifest["segments"]["0-12"]["sha256"] = digest(self.cp / "0-12.mp4")
        atomic_json(manifest_path, manifest)
        with self.assertRaisesRegex(ValueError, "do not correspond"):
            self.render()
        (self.cp / "0-12.mp4").write_bytes(original)
        manifest["segments"]["0-12"]["sha256"] = digest(self.cp / "0-12.mp4")
        atomic_json(manifest_path, manifest)
        for position in ([-1, 60], [350, 60]):
            self.data["overlays"][0]["position"] = position
            self.save()
            with self.assertRaisesRegex(ValueError, "clipping"):
                self.render()
        self.assertFalse(self.output.exists())

    def test_original_negative_audio_priming_timestamps(self):
        replacement = self.root / "primed.mp4"
        self.runff("-i", str(self.base), "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", str(replacement))
        replacement.replace(self.base)
        self.bind_receipt()
        self.assertLess(float(Fraction(_audio_packets(self.base)[0]["pts"])), 0)
        self.render()
        self.assertEqual(_audio_packets(self.base), _audio_packets(self.output))

    def test_no_audio_atlas_fade_and_failure_keeps_previous_video(self):
        silent = self.root / "silent.mp4"
        self.runff("-i", str(self.base), "-map", "0:v", "-c", "copy", str(silent))
        silent.replace(self.base)
        self.bind_receipt()
        atlas = Image.new("RGBA", (40, 20), "red")
        atlas.paste(Image.new("RGBA", (20, 20), "yellow"), (20, 0))
        atlas.save(self.root / "atlas.png")
        self.data["overlays"] = [{"atlas": "atlas.png", "atlas_metadata": {"headings": 1, "columns": 2, "frame_width": 20, "frame_height": 20, "anchor": [10, 20], "animation_frames": 2, "animation_fps": 24}, "start": 0, "end": .5, "fade_in": .125, "fade_out": .125, "position": [100, 100], "size": [40, 40]}]
        self.save()
        report = self.render()
        self.assertEqual(report["audio_packet_count"], 0)
        self.assertGreater(self.frame(0).getpixel((110, 110))[2], 220)
        red, green, blue = self.frame(5).getpixel((110, 110))
        self.assertGreater(min(red, green), 200)
        self.assertLess(blue, 30)
        old = self.output.read_bytes()
        self.data["overlays"][0]["position"] = [120, 100]
        self.save()
        with patch("compositor._encode", side_effect=RuntimeError("encoding failed")):
            with self.assertRaisesRegex(RuntimeError, "encoding failed"):
                self.render()
        self.assertEqual(self.output.read_bytes(), old)


if __name__ == "__main__":
    unittest.main()
