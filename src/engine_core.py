import json
from pathlib import Path

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

if __name__ == "__main__":
    content = load_content()
    procgen = load_procgen()
    print(f"Loaded {len(content['items'])} items, {len(procgen['depth_settings'])} depth profiles.")
