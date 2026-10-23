"""Exercise cross-revision reuse through real scene rendering with offline tiles."""
import io,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];SCRIPTS=ROOT/'.agents/skills/geomotion/scripts'
sys.path.insert(0,str(SCRIPTS))
from config import DEFAULTS
from execution import render
from project_state import atomic_json,digest
from render_scene import main as render_scene


@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
class RevisionReuse(unittest.TestCase):
    def test_late_edit_metadata_and_corrupt_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'scene.json'
            scene={'duration':.5,'camera':[{'time':0,'center':[0,0],'zoom':0}]}
            atomic_json(path,scene);tile=io.BytesIO();Image.new('RGB',(256,256),'#204a60').save(tile,'JPEG')
            calls=[];original_run=subprocess.run
            def offline(command,*args,**kwargs):
                if len(command)>1 and command[1]==str(SCRIPTS/'render_scene.py'):
                    if '--plan-only' not in command:
                        calls.append((int(command[command.index('--start-frame')+1]),int(command[command.index('--end-frame')+1])))
                    with patch('sys.argv',['render_scene',*command[2:]]),patch('render_scene.urllib.request.urlopen',side_effect=lambda *a,**k:io.BytesIO(tile.getvalue())):
                        render_scene()
                    return subprocess.CompletedProcess(command,0)
                return original_run(command,*args,**kwargs)
            with patch.dict(DEFAULTS['execution'],{'checkpoint_seconds':1/6}),patch('execution.worker_limit',return_value=1),patch('execution.subprocess.run',side_effect=offline):
                first=render(path,'preview',root/'a.mp4',root/'a')
                self.assertEqual(first['rendered_segments'],3)
                scene['markers']=[{'start':1/3,'end':.5,'position':[0,0],'label':'New','offset':[0,-80]}];atomic_json(path,scene)
                bad=root/'bad';bad.mkdir();(bad/'checkpoint.json').write_text('{incomplete')
                second=render(path,'preview',root/'b.mp4',root/'b',reuse_from=[bad,root/'a'])
                self.assertEqual(second['reused_segments'],2)
                self.assertEqual(second['rendered_segments'],1)
                self.assertEqual(calls[-1],(8,12))
                scene['metadata']={'note':'Editorial note only'};atomic_json(path,scene)
                third=render(path,'preview',root/'c.mp4',root/'c',reuse_from=[root/'b'])
                self.assertEqual(third['rendered_segments'],0)
                self.assertEqual(third['reused_segments'],3)
                source_hash=digest(root/'b/0-4.mp4')
                (root/'c/0-4.mp4').write_bytes(b'corrupt')
                fourth=render(path,'preview',root/'d.mp4',root/'d',reuse_from=[root/'c'])
                self.assertEqual(fourth['rendered_segments'],1)
                self.assertEqual(fourth['reused_segments'],2)
                self.assertEqual(digest(root/'b/0-4.mp4'),source_hash)
                self.assertEqual(calls[-1],(0,4))
                # A forged sidecar frame range is rejected even when its hash was updated.
                side=root/'d/4-8.layout.json';trace=json.loads(side.read_text());trace['composition']['frames'][0]['frame']=99;atomic_json(side,trace)
                manifest=root/'d/checkpoint.json';record=json.loads(manifest.read_text());record['segments']['4-8']['layout_sha256']=digest(side);atomic_json(manifest,record)
                fifth=render(path,'preview',root/'e.mp4',root/'e',reuse_from=[root/'d'])
                self.assertEqual(fifth['rendered_segments'],1)
                self.assertEqual(calls[-1],(4,8))

if __name__=='__main__':unittest.main()
