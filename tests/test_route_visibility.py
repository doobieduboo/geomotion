import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.agents/skills/geomotion/scripts'))
from map_assets import route_visibility
from layout import callout_opacity
class RouteVisibility(unittest.TestCase):
 def test_completed_stroke_holds_until_visibility_fade(self):
  route=dict(start=1,end=2,hide_at=4,fade_in=.2,fade_out=.4)
  cue=route_visibility(route,8)
  self.assertEqual(callout_opacity(cue,2.5),1)
  self.assertAlmostEqual(callout_opacity(cue,3.8),.5)
  self.assertEqual(callout_opacity(cue,4),0)
 def test_scene_end_default_and_invalid_visual_envelope(self):
  self.assertEqual(route_visibility(dict(start=1,end=2),8)['end'],8)
  with self.assertRaises(ValueError):route_visibility(dict(start=1,end=2,hide_at=2,fade_out=2),8)
if __name__=='__main__':unittest.main()
