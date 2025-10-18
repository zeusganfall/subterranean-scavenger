import unittest
import sys
from pathlib import Path

# Add src to path to allow for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from rng import RNG
from engine_core import generate_map

class TestRNG(unittest.TestCase):
    def test_deterministic_map_generation(self):
        seed = 12345
        rng1 = RNG(seed)
        rng2 = RNG(seed)

        map1, _, _ = generate_map(rng1, 20, 10, 5, 3, 5, {})
        map2, _, _ = generate_map(rng2, 20, 10, 5, 3, 5, {})

        self.assertEqual(map1.tiles, map2.tiles, "Maps generated with the same seed should be identical")

if __name__ == '__main__':
    unittest.main()