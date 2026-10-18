import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.agents/skills/geomotion/scripts'))
from basemap import tile_url, tile_zoom, validate_basemap

class SatelliteSource(unittest.TestCase):
    def test_matrix_order_and_wrapping(self):
        self.assertTrue(tile_url(3,-1,2).endswith('/tile/3/2/7'))
        self.assertIn('services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer',tile_url(0,0,0))
        with self.assertRaises(ValueError): tile_url(24,0,0)
        with self.assertRaises(ValueError): tile_url(3,0,8)

    def test_native_final_uses_higher_available_tile_level(self):
        self.assertEqual(tile_zoom(5.7,'preview'),5)
        self.assertEqual(tile_zoom(5.7,'final'),7)
        self.assertEqual(tile_zoom(24,'final'),23)

    def test_only_esri_is_permitted(self):
        validate_basemap({'type':'satellite','provider':'esri_world_imagery'})
        for config in ({'type':'solid'},{'type':'satellite','provider':'other'},{}):
            with self.assertRaises(ValueError):validate_basemap(config)
