import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.agents/skills/geomotion/scripts'))
from region_stroke import prepare_stroke, revealed_paths, projected_stroke_copies, stroke_state, validate_focus_strokes, outline_style, paint_outlines
from config import DEFAULTS

class StrokeReveal(unittest.TestCase):
    def test_focus_has_independent_progress_and_completed_core_persists(self):
        r=dict(start=0,reveal=0,stroke_origin=[0,0],focus_strokes=[dict(start=2,end=5,reveal=1,stroke_origin=[2,2])])
        validate_focus_strokes(r)
        self.assertEqual(stroke_state(r,1), (1,(0,0),None))
        self.assertEqual(stroke_state(r,2)[:2], (0,(2,2)))
        self.assertEqual(stroke_state(r,2.5)[0], .5)
        self.assertEqual(stroke_state(r,4.9)[0], 1)
        self.assertEqual(stroke_state(r,5), (1,(0,0),None))

    def test_default_native_sizes_and_automatic_focus_recipe(self):
        scale=DEFAULTS['export']['final']['width']/DEFAULTS['design_width']
        base=outline_style({});focus=outline_style({},dict(start=1,end=3,reveal=1))
        self.assertAlmostEqual(base['stroke_width_design']*scale,2)
        self.assertAlmostEqual(base['glow_radius_design']*scale,2)
        self.assertAlmostEqual(focus['stroke_width_design']*scale,2)
        self.assertAlmostEqual(max(l['radius_design'] for l in focus['glow']['layers'])*scale,16)
        self.assertEqual(focus['color'],[255,46,66])
        self.assertEqual(base['casing_opacity'],0)
        self.assertEqual(stroke_state({'start':0},0)[0],1)
        explicit=outline_style({},dict(start=1,end=3,reveal=1,color=[0,195,255],stroke_width_design=1,glow_radius_design=2,glow_opacity=55))
        self.assertEqual(explicit['color'],[0,195,255])
        self.assertEqual(explicit['stroke_width_design'],1)
        self.assertNotIn('glow_layers',explicit)
        for bad in (0,-1,float('nan')):
            with self.assertRaises(ValueError):outline_style({'stroke_width_design':bad})

    def test_revealed_emphasis_replaces_only_its_reference_without_white_halo(self):
        full=[[(50,100),(400,100)]];partial=[[(50,100),(220,100)]]
        base=outline_style({});focus=outline_style({},dict(start=0,end=3,reveal=1))
        ordinary=paint_outlines((480,200),1.5,[(full,base)],[])
        empty=paint_outlines((480,200),1.5,[(full,base)],[([],focus,1)])
        self.assertEqual(ordinary.tobytes(),empty.tobytes())
        image=paint_outlines((480,200),1.5,[(full,base)],[(partial,focus,1)])
        r,g,b,a=image.getpixel((100,100))
        self.assertGreater(a,240);self.assertGreater(r,220);self.assertLess(g,100)
        self.assertEqual(image.getpixel((350,100)),ordinary.getpixel((350,100)))
        r,g,b,a=image.getpixel((100,105))
        self.assertGreater(a,0);self.assertGreater(r-g,100)
        r,g,b,a=image.getpixel((350,105))
        self.assertGreater(a,0);self.assertLessEqual(r,g)
        # Completed focus stays on the same boundary; no white reference halo
        # remains beside its red core, including a second coincident region.
        finished=paint_outlines((480,200),1.5,[(full,base),(full,base)],[(full,focus,1)])
        r,g,b,a=finished.getpixel((350,105))
        self.assertGreater(r-g,100)

    def test_focus_schedule_cannot_overlap_or_cut_off_reveal(self):
        for cues in [
            [dict(start=0,end=2,reveal=1),dict(start=1,end=3,reveal=1)],
            [dict(start=0,end=1,reveal=2)],
            [dict(start=0,end=1,reveal=0)],
            [dict(start=0,end=1,reveal=.5,glow_opacity=300)],
        ]:
            with self.assertRaises(ValueError):validate_focus_strokes(dict(focus_strokes=cues))

    def test_artificial_geojson_dateline_closure_is_not_a_border(self):
        project=lambda ll:(ll[0]+180,90-ll[1])
        copies=projected_stroke_copies([(179,60),(180,61),(180,70),(179,71)],project,(360,0),(720,640))
        self.assertTrue(copies)
        self.assertTrue(all(len(p)==2 for p in copies))
        self.assertTrue(all(abs(p[-1][1]-p[0][1])==1 for p in copies))

    def test_camera_wrap_seam_never_connects_across_viewport(self):
        # Adjacent points straddle the camera antipode, outside both edges.
        project=lambda ll: (180 + ((ll[0] + 180) % 360 - 180)*2, 200)
        copies=projected_stroke_copies([(179,60),(-179,60)],project,(720,0),(360,640))
        self.assertEqual(copies,[])

    def test_dateline_boundary_stays_connected_in_visible_copy(self):
        project=lambda ll: (180 + ((ll[0]-180+180)%360-180)*2, 200)
        copies=projected_stroke_copies([(179,60),(-179,60)],project,(720,0),(360,640))
        self.assertEqual(len(copies),1)
        self.assertEqual(copies[0],[(178,200),(182,200)])

    def test_distance_not_vertex_count_and_no_early_full_segment(self):
        paths=prepare_stroke([[[(0,0),(1,0),(10,0)]]])
        self.assertEqual(revealed_paths(paths,0),[])
        part=revealed_paths(paths,0.5)
        self.assertAlmostEqual(part[0][-1][0],5)
        self.assertEqual(revealed_paths(paths,1)[0],paths[0][0])
        self.assertEqual(revealed_paths(paths,2),revealed_paths(paths,1))

    def test_islands_are_sequential_without_bridge(self):
        paths=prepare_stroke([[[(0,0),(10,0)]],[[(20,0),(22,0)]]])
        first=revealed_paths(paths,0.5)
        self.assertEqual(len(first),1)
        later=revealed_paths(paths,0.9)
        self.assertEqual(later[0],paths[0][0])
        self.assertEqual(later[1][0],(20,0))
        self.assertLess(later[1][-1][0],22)

    def test_duplicate_reversed_ring_is_drawn_once(self):
        ring=[(0,0),(2,0),(2,2),(0,0)]
        self.assertEqual(len(prepare_stroke([[ring],[list(reversed(ring))]])),1)

    def test_authored_start_preserves_closed_boundary_and_length(self):
        ring=[(0,0),(2,0),(2,2),(0,2),(0,0)]
        original=prepare_stroke([[ring]])
        rotated=prepare_stroke([[ring]],origin=(2,2))
        self.assertEqual(rotated[0][0][0],(2,2))
        self.assertEqual(rotated[0][0][0],rotated[0][0][-1])
        self.assertEqual(set(rotated[0][0]),set(original[0][0]))
        self.assertEqual(rotated[0][2],original[0][2])
        self.assertEqual(len(revealed_paths(rotated,0.1)),1)
