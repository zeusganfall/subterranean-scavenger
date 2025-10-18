import unittest
import os
import sys
from pathlib import Path

# Add src to path to allow for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from engine_core import Engine, Player, GameMap, RNG, save_game, load_game, generate_map

class TestSaveLoad(unittest.TestCase):
    def setUp(self):
        self.save_file = "test_save.json"
        self.seed = 12345
        self.rng = RNG(self.seed)
        self.game_map, rooms = generate_map(self.rng, 80, 45, 30, 6, 10)
        self.player = Player(10, 10)
        self.engine = Engine(self.rng, self.game_map, self.player)

    def tearDown(self):
        if os.path.exists(self.save_file):
            os.remove(self.save_file)

    def test_save_and_load_game(self):
        # Move player and save game
        self.engine.move_player(1, 0)
        save_game(self.engine, self.save_file)

        # Load game
        loaded_engine = load_game(self.save_file)

        # Assert that the loaded state is correct
        self.assertEqual(self.engine.seed, loaded_engine.seed)
        self.assertEqual(self.engine.player.x, loaded_engine.player.x)
        self.assertEqual(self.engine.player.y, loaded_engine.player.y)
        self.assertEqual(self.engine.player.hp, loaded_engine.player.hp)
        self.assertEqual(self.engine.player.inventory, loaded_engine.player.inventory)
        self.assertEqual(self.engine.game_map.tiles, loaded_engine.game_map.tiles)

if __name__ == '__main__':
    unittest.main()