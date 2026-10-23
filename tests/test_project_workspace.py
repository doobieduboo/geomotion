import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]/'.agents/skills/geomotion/scripts'
sys.path.insert(0, str(SCRIPTS))
import project_workspace as workspace
from project_state import atomic_json, digest, fingerprint, snapshot
from pipeline import main


class SavedWorkspace(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name);self.scene = self.root/'scene.json'
        atomic_json(self.scene, {'duration': .5, 'camera': [{'time': 0, 'center': [0,0], 'zoom': 0}]})
        self.state = workspace.default_path(self.scene)

    def test_final_stage_survives_save_load_and_needs_explicit_downgrade(self):
        with self.assertRaisesRegex(ValueError, 'final-requested'):
            workspace.save(self.scene, mode='final')
        self.assertFalse(self.state.exists())
        workspace.save(self.scene, mode='final', final_requested=True)
        workspace.save(self.scene)
        loaded = workspace.load(self.state)
        self.assertEqual(loaded['mode'], 'final')
        self.assertEqual(workspace.select_mode(loaded), ('final', True))
        self.assertTrue(loaded['source_available'])
        self.assertEqual(loaded['source_changes'], [])
        with self.assertRaisesRegex(ValueError, 'retained'):
            workspace.save(self.scene, mode='preview')
        self.assertEqual(workspace.read(self.state)['mode'], 'final')
        workspace.save(self.scene, mode='preview', return_to_preview=True)
        self.assertEqual(workspace.read(self.state)['mode'], 'preview')

    def test_old_artifact_is_available_but_stale_after_edit_and_save(self):
        video=self.root/'video.mp4';video.write_bytes(b'fixture artifact identity')
        atomic_json(video.with_suffix('.render.json'), {'sha256':digest(video),
            'fingerprint':fingerprint(snapshot(self.scene),'preview')})
        workspace.save(self.scene, video=video)
        self.assertTrue(workspace.load(self.state)['last_render_current'])
        scene=json.loads(self.scene.read_text());scene['camera'][0]['zoom']=1;atomic_json(self.scene,scene)
        workspace.save(self.scene)
        loaded=workspace.load(self.state)
        self.assertTrue(loaded['last_render_available'])
        self.assertFalse(loaded['last_render_current'])
        previous=self.state.read_bytes()
        with self.assertRaisesRegex(ValueError,'does not match'):
            workspace.save(self.scene,video=video)
        self.assertEqual(self.state.read_bytes(),previous)

    def test_missing_asset_and_checkpoint_history(self):
        asset=self.root/'input.txt';asset.write_text('source')
        scene=json.loads(self.scene.read_text());scene['inputs']={'data':['input.txt']};atomic_json(self.scene,scene)
        workspace.save(self.scene,checkpoint=self.root/'cp-a')
        workspace.save(self.scene,checkpoint=self.root/'cp-b')
        workspace.save(self.scene,checkpoint=self.root/'cp-b')
        self.assertEqual(workspace.read(self.state)['history'],[str(self.root/'cp-a')])
        asset.unlink();loaded=workspace.load(self.state)
        self.assertFalse(loaded['source_available'])
        self.assertFalse(loaded['checkpoint_available'])

    def test_cli_save_load_does_not_render(self):
        for arguments in (['save',str(self.scene)],['load',str(self.state)]):
            output=io.StringIO()
            with patch('sys.argv',['pipeline',*arguments]),patch('pipeline.render',side_effect=AssertionError('no render')),contextlib.redirect_stdout(output):
                main()
            self.assertEqual(json.loads(output.getvalue())['mode'],'preview')

    def test_run_cli_inherits_saved_final_stage_without_another_final_flag(self):
        workspace.save(self.scene,mode='final',final_requested=True)
        output=self.root/'final.mp4'
        def completed(scene,mode,video,checkpoint,workers,authorized,**kwargs):
            self.assertEqual(mode,'final');self.assertTrue(authorized)
            video.write_bytes(b'fixture for source-bound CLI stage routing')
            binding={'sha256':digest(video),'fingerprint':fingerprint(snapshot(scene),mode),'frames':15}
            atomic_json(video.with_suffix('.render.json'),binding)
            return binding
        arguments=['pipeline','run',str(self.scene),'--output',str(output),'--checkpoint',str(self.root/'native-cp')]
        with patch('sys.argv',arguments),patch('pipeline.render',side_effect=completed),patch('pipeline.check',return_value={'automated_pass':True}),patch('pipeline.contact_sheet'),contextlib.redirect_stdout(io.StringIO()):
            main()
        self.assertEqual(workspace.read(self.state)['mode'],'final')
        self.assertTrue(workspace.load(self.state)['last_render_current'])

    def test_interrupted_first_composite_keeps_recovery_paths(self):
        recipe=self.root/'overlay.json';atomic_json(recipe,{'version':1})
        arguments=['pipeline','composite',str(recipe),'--mode','preview','--output',str(self.root/'out.mp4'),'--checkpoint',str(self.root/'overlay-cp')]
        with patch('sys.argv',arguments),patch('compositor.composite',side_effect=RuntimeError('interrupted')):
            with self.assertRaisesRegex(RuntimeError,'interrupted'):main()
        loaded=workspace.load(self.state)
        self.assertEqual(loaded['status'],'composite_interrupted')
        self.assertEqual(loaded['pending_composite']['checkpoint'],str(self.root/'overlay-cp'))
        self.assertEqual(loaded['active_kind'],'composite_pending')
        self.assertFalse(loaded['active_sources_current'])

if __name__=='__main__':unittest.main()
