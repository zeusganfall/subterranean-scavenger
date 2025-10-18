import json
import sys
from pathlib import Path

from collections import deque
from enum import Enum, auto
from rng import RNG


class TileType(Enum):
    WALL = auto()
    FLOOR = auto()

class GameMap:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.tiles = [[TileType.WALL for _ in range(width)] for _ in range(height)]

class Rect:
    """A rectangle on the map, used for rooms."""
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

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

def _create_room(game_map: GameMap, room: Rect):
    """Carves out a rectangular room in the map."""
    for x in range(room.x1 + 1, room.x2):
        for y in range(room.y1 + 1, room.y2):
            game_map.tiles[y][x] = TileType.FLOOR

def _create_h_tunnel(game_map: GameMap, x1: int, x2: int, y: int):
    """Carves a horizontal tunnel."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        game_map.tiles[y][x] = TileType.FLOOR

def _create_v_tunnel(game_map: GameMap, y1: int, y2: int, x: int):
    """Carves a vertical tunnel."""
    for y in range(min(y1, y2), max(y1, y2) + 1):
        game_map.tiles[y][x] = TileType.FLOOR

def render_map(game_map: GameMap, player_x: int, player_y: int):
    """Renders the map to the console."""
    for y in range(game_map.height):
        for x in range(game_map.width):
            if x == player_x and y == player_y:
                print("@", end="")
            elif game_map.tiles[y][x] == TileType.WALL:
                print("#", end="")
            else:
                print(".", end="")
        print()

def check_map_connectivity(game_map: GameMap, rooms: list[Rect]) -> bool:
    """Check if all rooms on the map are connected using BFS."""
    if not rooms:
        return True

    start_node = rooms[0]
    start_pos = ((start_node.x1 + start_node.x2) // 2, (start_node.y1 + start_node.y2) // 2)

    q = deque([start_pos])
    visited = {start_pos}

    room_centers = set()
    for room in rooms:
        center = ((room.x1 + room.x2) // 2, (room.y1 + room.y2) // 2)
        room_centers.add(center)

    found_centers = set()
    if start_pos in room_centers:
        found_centers.add(start_pos)

    while q:
        x, y = q.popleft()

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy

            if 0 <= nx < game_map.width and 0 <= ny < game_map.height and \
               (nx, ny) not in visited and game_map.tiles[ny][nx] == TileType.FLOOR:

                visited.add((nx, ny))
                q.append((nx, ny))

                if (nx, ny) in room_centers:
                    found_centers.add((nx, ny))

    return len(found_centers) == len(room_centers)

def generate_map(rng: RNG, width: int, height: int, max_rooms: int, min_room_size: int, max_room_size: int) -> tuple[GameMap, list[Rect]]:
    """Generates a new map with rooms and corridors."""
    while True:
        game_map = GameMap(width, height)
        rooms = []

        for _ in range(max_rooms):
            w = rng.randint(min_room_size, max_room_size)
            h = rng.randint(min_room_size, max_room_size)
            x = rng.randint(0, width - w - 1)
            y = rng.randint(0, height - h - 1)

            new_room = Rect(x, y, w, h)

            # Check for intersections
            if any((new_room.x1 <= room.x2 and new_room.x2 >= room.x1 and \
                    new_room.y1 <= room.y2 and new_room.y2 >= room.y1) for room in rooms):
                continue

            _create_room(game_map, new_room)

            if rooms:
                prev_room = rooms[-1]
                # Center points of the rooms
                prev_center_x = (prev_room.x1 + prev_room.x2) // 2
                prev_center_y = (prev_room.y1 + prev_room.y2) // 2
                new_center_x = (new_room.x1 + new_room.x2) // 2
                new_center_y = (new_room.y1 + new_room.y2) // 2

                if rng.randint(0, 1) == 1:
                    # Horizontal then vertical
                    _create_h_tunnel(game_map, prev_center_x, new_center_x, prev_center_y)
                    _create_v_tunnel(game_map, prev_center_y, new_center_y, new_center_x)
                else:
                    # Vertical then horizontal
                    _create_v_tunnel(game_map, prev_center_y, new_center_y, prev_center_x)
                    _create_h_tunnel(game_map, prev_center_x, new_center_x, new_center_y)

            rooms.append(new_room)

            if check_map_connectivity(game_map, rooms):
                return game_map, rooms

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

    # Map parameters
    map_width = 80
    map_height = 45
    max_rooms = 30
    min_room_size = 6
    max_room_size = 10

    game_map, rooms = generate_map(rng, map_width, map_height, max_rooms, min_room_size, max_room_size)

    player_x, player_y = 0, 0
    if rooms:
        first_room = rooms[0]
        player_x = (first_room.x1 + first_room.x2) // 2
        player_y = (first_room.y1 + first_room.y2) // 2

    print(f"Generated a {map_width}x{map_height} map with seed {rng.seed}.")
    render_map(game_map, player_x, player_y)
