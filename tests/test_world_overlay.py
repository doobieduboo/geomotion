import sys,unittest,math
from unittest.mock import patch
from pathlib import Path
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.agents/skills/geomotion/scripts'))
from world_overlay import project_world_overlay
class WorldOverlay(unittest.TestCase):
 def test_empty_overlay_does_not_sample_transparent_canvas(self):
  with patch('PIL.Image.Image.transform',side_effect=AssertionError('empty transform')):
   r=project_world_overlay(Image.new('RGBA',(128,128)),{'center':[0,0],'zoom':1},(128,128),1)
  self.assertIsNone(r.getbbox())
 def test_visible_extent_sampler_matches_full_canvas_with_rotation_and_wrap(self):
  texture=Image.new('RGBA',(256,256));draw=ImageDraw.Draw(texture)
  draw.ellipse((85,30,140,120),fill=(220,35,85,160));draw.rectangle((0,95,12,180),fill=(10,180,255,220));texture=texture.convert('RGBa')
  for camera in [{'center':[0,40],'zoom':1,'rotation':31},{'center':[179,40],'zoom':0,'rotation':-17},{'center':[-40,5],'zoom':3,'rotation':70}]:
   w,h=300,500;side=texture.width;lon,lat=camera['center'];factor=side/(256*2**camera['zoom']*1.5);r=math.radians(camera['rotation']);a,b,d,e=math.cos(r)*factor,math.sin(r)*factor,-math.sin(r)*factor,math.cos(r)*factor;c=((lon+180)/360*side)%side-(a*w+b*h)/2;f=(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*side-(d*w+e*h)/2
   reference=Image.new('RGBA',(w,h))
   for shift in [-side,0,side]:reference.alpha_composite(texture.transform((w,h),Image.Transform.AFFINE,(a,b,c+shift,d,e,f),Image.Resampling.BICUBIC).convert('RGBA'))
   self.assertEqual(reference.tobytes(),project_world_overlay(texture,camera,(w,h),1.5).tobytes())
 def test_camera_center_and_transparency(self):
  im=Image.new('RGBA',(128,128));ImageDraw.Draw(im).rectangle((58,58,70,70),fill=(0,255,0,180))
  r=project_world_overlay(im,{'center':[0,0],'zoom':1},(128,128),1)
  self.assertEqual(r.getpixel((64,64)),(0,255,0,180));self.assertEqual(r.getpixel((0,0))[3],0)
 def test_dateline_wrap_preserves_both_sides(self):
  im=Image.new('RGBA',(128,128),(255,0,0,255));ImageDraw.Draw(im).rectangle((64,0,127,127),fill=(0,0,255,255))
  r=project_world_overlay(im,{'center':[180,0],'zoom':0},(32,32),1)
  self.assertEqual(r.getpixel((2,16)),(0,0,255,255));self.assertEqual(r.getpixel((29,16)),(255,0,0,255))
 def test_requires_square_world_texture(self):
  with self.assertRaises(ValueError):project_world_overlay(Image.new('RGBA',(10,20)),{'center':[0,0],'zoom':1},(32,32),1)
