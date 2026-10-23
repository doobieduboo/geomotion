import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.agents/skills/geomotion/scripts'))
from tile_memory import check_tile_memory
from execution import worker_limit

class TileMemory(unittest.TestCase):
    def test_wide_native_world_fits_measured_budget(self):
        value=check_tile_memory({6:(-18,90,0,63)},4096,available=7*1024**3)
        self.assertGreater(value,2*1024**3)
        self.assertLess(value,3*1024**3)

    def test_refuses_low_memory_or_excessive_mosaic(self):
        with self.assertRaises(ValueError):check_tile_memory({6:(-18,90,0,63)},4096,available=3*1024**3)
        with self.assertRaises(ValueError):check_tile_memory({6:(-40,150,0,100)},4096,available=32*1024**3)

    def test_final_worker_cap_applies_even_when_more_requested(self):
        self.assertEqual(worker_limit(2,'final'),1)
