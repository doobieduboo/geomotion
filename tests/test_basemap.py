import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.agents/skills/geomotion/scripts'))
from basemap import tile_url, tile_zoom

class SatelliteSource(unittest.TestCase):
    def test_matrix_order_and_wrapping(self):
        self.assertTrue(tile_url(3,-1,2).endswith('/3/2/7.jpeg'))
        self.assertIn('BlueMarble_ShadedRelief_Bathymetry/default/2004-07-01',tile_url(0,0,0))
        with self.assertRaises(ValueError): tile_url(9,0,0)
        with self.assertRaises(ValueError): tile_url(3,0,8)

    def test_native_final_uses_higher_available_tile_level(self):
        self.assertEqual(tile_zoom(5.7,'preview'),5)
        self.assertEqual(tile_zoom(5.7,'final'),7)
        self.assertEqual(tile_zoom(9,'final'),8)
