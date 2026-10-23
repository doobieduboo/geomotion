import sys,unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.agents/skills/geomotion/scripts'))
from layout import callout_image

class ArchiveDetail(unittest.TestCase):
    def test_detail_preserves_source_pixels_and_original(self):
        source=Image.new('RGBA',(8,6))
        for y in range(6):
            for x in range(8):source.putpixel((x,y),(x*20,y*30,50,255))
        before=source.tobytes();detail=callout_image(source,{'image_crop':[2,1,7,5]})
        self.assertEqual(detail.size,(5,4))
        for y in range(4):
            for x in range(5):self.assertEqual(detail.getpixel((x,y)),source.getpixel((x+2,y+1)))
        self.assertEqual(source.tobytes(),before)
        self.assertIs(callout_image(source,{}),source)

    def test_invalid_detail_does_not_silently_clip_or_pad(self):
        for crop in [[-1,0,3,3],[0,0,9,3],[2,1,2,4],[0,0,2.5,3],[0,0,3]]:
            with self.assertRaises(ValueError):callout_image(Image.new('RGB',(8,6)),{'image_crop':crop})
        with self.assertRaises(ValueError):callout_image(None,{'image_crop':[0,0,3,3]})
