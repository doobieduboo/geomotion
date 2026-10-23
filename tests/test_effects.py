import sys
import unittest
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.agents/skills/geomotion/scripts'))
from effects import paint_land, _paint_land, glow_settings, composite_emission
from region_stroke import outline_style, paint_outlines
from render_scene import validate


class GeographicEffects(unittest.TestCase):
    def test_visible_window_preserves_pixels_at_output_scales_and_frame_edges(self):
        random=np.random.default_rng(8)
        base=Image.fromarray(random.integers(10,200,(160,120,3),dtype=np.uint8)).convert('RGBA')
        for box in ((40,60,55,85),(0,0,15,20),(105,140,119,159)):
            layer=Image.new('RGBA',base.size)
            ImageDraw.Draw(layer).rectangle(box,fill=(255,24,40,180))
            for scale in (.5,1.5,2.25):
                for kind,blend in (('flag','normal'),('color','terrain_tint')):
                    with self.subTest(box=box,scale=scale,kind=kind):
                        full=_paint_land(base,layer,scale,kind=kind,blend=blend)
                        window=paint_land(base,layer,scale,kind=kind,blend=blend)
                        self.assertEqual(full.tobytes(),window.tobytes())

    def test_tint_preserves_terrain_and_does_not_color_the_ocean(self):
        terrain=Image.new('RGBA',(100,80),(50,50,50,255))
        ImageDraw.Draw(terrain).rectangle((50,0,99,79),fill=(150,150,150,255))
        layer=Image.new('RGBA',terrain.size)
        ImageDraw.Draw(layer).rectangle((20,20,80,60),fill=(255,24,40,230))
        result=paint_land(terrain,layer,1.5,blend='terrain_tint',kind='color',glow=False)
        self.assertEqual(result.getpixel((10,10)),terrain.getpixel((10,10)))
        dark,light=result.getpixel((30,40)),result.getpixel((70,40))
        self.assertGreater(light[0],dark[0]*2)
        self.assertGreater(dark[0],dark[1]*3)
        self.assertGreater(light[0],light[2]*3)

    def test_only_colored_emission_can_fall_outside_the_land_mask(self):
        base=Image.new('RGBA',(256,256),(30,50,70,255))
        layer=Image.new('RGBA',base.size)
        ImageDraw.Draw(layer).rectangle((110,100,145,155),fill=(255,24,40,230))
        result=paint_land(base,layer,1.5,blend='terrain_tint',kind='color')
        self.assertEqual(result.getpixel((5,5)),base.getpixel((5,5)))
        near=result.getpixel((108,125));old=base.getpixel((108,125))
        self.assertGreater(near[0],old[0])
        self.assertGreater(near[0]-old[0],near[1]-old[1])

    def test_flag_rgb_is_preserved_without_tinting(self):
        base=Image.new('RGBA',(40,20),(80,80,80,255))
        flag=Image.new('RGBA',base.size,(0,64,255,255))
        ImageDraw.Draw(flag).rectangle((0,0,19,19),fill=(255,24,40,255))
        result=paint_land(base,flag,1.5,kind='flag',glow=False)
        self.assertEqual(result.tobytes(),flag.tobytes())
        with self.assertRaises(ValueError):
            paint_land(base,flag,1.5,kind='flag',blend='terrain_tint')

    def test_addition_is_linear_light_and_preserves_alpha(self):
        base=Image.new('RGBA',(2,2),(64,64,64,197))
        result=composite_emission(base,np.full((2,2,3),.1,dtype=np.float32))
        self.assertGreater(result.getpixel((0,0))[0],100)
        self.assertLess(result.getpixel((0,0))[0],140)
        self.assertEqual(result.getpixel((0,0))[3],197)
        self.assertIs(composite_emission(base,np.zeros((2,2,3))),base)

    def test_focus_bloom_follows_the_revealed_front_without_neutral_double_glow(self):
        full=[[(20,60),(280,60)]];partial=[[(20,60),(130,60)]]
        ref=outline_style({});focus=outline_style({},dict(start=0,end=2,reveal=1))
        _,light=paint_outlines((300,120),1.5,[(full,ref)],[(partial,focus,1)],return_emission=True)
        # Far inside the completed span, red emission replaces the white one;
        # well beyond the reveal front, the ordinary neutral border remains.
        self.assertGreater(light[64,70,0],light[64,70,1]*4)
        self.assertAlmostEqual(float(light[64,230,0]),float(light[64,230,1]),delta=.02)
        _,empty=paint_outlines((300,120),1.5,[],[([],focus,1)],return_emission=True)
        self.assertFalse(np.any(empty))

    def test_malformed_effects_fail_before_imagery_work(self):
        for bad in ({'inside_gain':float('nan')},{'layers':[{'radius_design':-1,'gain':1}]}, {'layers':[{'radius_design':1,'gain':float('inf')}]},'red'):
            with self.assertRaises(ValueError):glow_settings(bad,land=True)
        with self.assertRaises(ValueError):
            validate({'duration':1,'camera':[{'time':0,'center':[0,0],'zoom':1}],
                      'world_overlays':[{'image':'unused.png','fill_kind':'flag','fill_blend':'terrain_tint'}]})


if __name__=='__main__':unittest.main()
