import json
import sys
from pathlib import Path

from rng import RNG


def load_json(path: str):
    with open(Path(path), "r", encoding="utf-8") as f:
        return json.load(f)

def load_content(path="data/content.json"):
    data = load_json(path)
    assert "items" in data and "enemies" in data
    return data

def load_procgen(path="data/procgen.json"):
    data = load_json(path)
    assert "map" in data and "depth_settings" in data
    return data

def generate_map(rng, width, height):
    """Generates a simple map for testing purposes."""
    return [[rng.choice(["wall", "floor"]) for _ in range(width)] for _ in range(height)]

if __name__ == "__main__":
    seed = None
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
            print(f"Using seed from command line: {seed}")
        except ValueError:
            print(f"Invalid seed: {sys.argv[1]}. Using a random seed.")

    rng = RNG(seed)
    print(f"Initialized with seed: {rng.seed}")

    content = load_content()
    procgen = load_procgen()
    print(f"Loaded {len(content['items'])} items, {len(procgen['depth_settings'])} depth profiles.")

    # Generate a map
    width, height = 20, 10
    game_map = generate_map(rng, width, height)
    print(f"Generated a {width}x{height} map.")
