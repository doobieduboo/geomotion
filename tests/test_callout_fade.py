import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.agents/skills/geomotion/scripts'))
from PIL import Image
from layout import callout_opacity,fade_callout
class CalloutFade(unittest.TestCase):
 def test_source_time_layer_alpha_preserves_all_elements_and_original(self):
  layer=Image.new('RGBA',(3,1));layer.putdata([(255,0,0,255),(0,255,0,210),(0,0,255,240)])
  cue=dict(start=7,end=8.3,fade_in=.2,fade_out=.2)
  self.assertEqual(fade_callout(layer,cue,7).getchannel('A').getextrema(),(0,0))
  halfway=fade_callout(layer,cue,7.1)
  for original,actual in zip(layer.getdata(),halfway.getdata()):
   self.assertEqual(original[:3],actual[:3]);self.assertLessEqual(abs(actual[3]-original[3]/2),1)
  self.assertEqual(layer.getpixel((0,0))[3],255)
  self.assertIs(fade_callout(layer,cue,7.5),layer)
  self.assertEqual(callout_opacity(cue,8.3),0)
  self.assertAlmostEqual(callout_opacity(cue,8.2),.5)
 def test_omitted_fades_keep_visibility_and_bad_envelopes_fail(self):
  self.assertEqual(callout_opacity(dict(start=1,end=2),1),1)
  for cue in [dict(start=1,end=2,fade_in=-.1),dict(start=1,end=2,fade_in=.6,fade_out=.6)]:
   with self.assertRaises(ValueError):callout_opacity(cue,1.5)
if __name__=='__main__':unittest.main()
