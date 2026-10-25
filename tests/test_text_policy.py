"""Public scene loading/rendering must not leak descriptions or source credits."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.agents/skills/geomotion/scripts'))
from text_policy import apply, settings
from project_state import load_project
from render_scene import main, validate
from revision_cache import render_key


class TextPolicy(unittest.TestCase):
    def test_defaults_keep_media_and_geography_but_remove_extra_text(self):
        source = {'attribution': 'Private source record',
                  'callouts': [{'image': 'photo.png', 'title': 'Description', 'lines': ['Credit']},
                               {'title': 'Technical explanation'}],
                  'markers': [{'position': [0, 0], 'label': 'Place'}],
                  'cta': {'text': 'Extra'}, 'subtitles': [{'text': 'Voice'}]}
        scene = apply(source)
        self.assertEqual(scene['attribution'], '')
        self.assertEqual(scene['callouts'], [{'image': 'photo.png'}])
        self.assertNotIn('cta', scene)
        self.assertEqual(scene['markers'], source['markers'])
        self.assertEqual(scene['subtitles'], source['subtitles'])
        self.assertEqual(source['attribution'], 'Private source record')
        self.assertEqual(source['callouts'][0]['title'], 'Description')
        self.assertEqual(apply(scene), scene)

    def test_explicit_caption_and_credit_opt_in_is_boolean_and_independent(self):
        scene = apply({'text_policy': {'media_captions': True, 'source_credits': True},
                       'attribution': 'Publisher', 'callouts': [{'image': 'a.png', 'title': 'Caption'}],
                       'cta': {'text': 'No automatic CTA'}})
        self.assertIn('Publisher', scene['attribution'])
        self.assertIn('Esri', scene['attribution'])
        self.assertEqual(scene['callouts'][0]['title'], 'Caption')
        self.assertNotIn('cta', scene)
        for value in [{'source_credits': 'false'}, {'unknown': True}, []]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                settings({'text_policy': value})

    def test_removed_scene_and_camera_options_fail_instead_of_rendering(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'scene.json'
            path.write_text(json.dumps({'map_board': {'enabled': True}}))
            with self.assertRaisesRegex(ValueError, 'Unsupported generic scene fields'):
                load_project(path)
        with self.assertRaisesRegex(ValueError, 'Unsupported camera fields'):
            validate({'duration': 1, 'camera': [{'time': 0, 'center': [0, 0], 'zoom': 2, 'pitch': 20}]})

    def test_policy_opt_in_changes_video_dependencies(self):
        with tempfile.TemporaryDirectory() as temporary:
            p = Path(temporary) / 'scene.json'
            scene = {'duration': 1, 'camera': [{'time': 0, 'center': [0, 0], 'zoom': 2}]}
            p.write_text(json.dumps(scene));before = render_key(p, 'preview', 0, 24)
            scene['text_policy'] = {'source_credits': True}
            p.write_text(json.dumps(scene))
            self.assertNotEqual(before, render_key(p, 'preview', 0, 24))

    def test_native_still_has_full_map_and_no_automatic_footer_without_ffmpeg(self):
        with tempfile.TemporaryDirectory() as temporary:
            p = Path(temporary);scene = p/'scene.json';out = p/'frame.png'
            scene.write_text(json.dumps({'duration': 1, 'camera': [{'time': 0, 'center': [0, 0], 'zoom': 4}],
                'audio': 'not-generated.wav', 'attribution': 'Do not draw this automatically',
                'export': {'preview': {'width': 180, 'height': 320, 'fps': 2}}}))
            buf = io.BytesIO();Image.new('RGB', (256, 256), (37, 78, 83)).save(buf, format='PNG')
            with patch('sys.argv', ['render_scene', str(scene), '--still', '--start-frame', '1', '--output', str(out)]), \
                 patch('render_scene.shutil.which', return_value=None), \
                 patch('render_scene.subprocess.Popen', side_effect=AssertionError('Still must not encode')), \
                 patch('render_scene.urllib.request.urlopen', side_effect=lambda *a, **k: io.BytesIO(buf.getvalue())):
                main()
            image = Image.open(out)
            self.assertEqual(image.size, (180, 320))
            self.assertEqual(image.getextrema(), ((37, 37), (78, 78), (83, 83)))
            layout = json.loads(out.with_suffix('.layout.json').read_text())
            self.assertEqual(layout['errors'], {})
            self.assertFalse(list(p.glob('*.mp4')))
