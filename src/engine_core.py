import json
import sys
from pathlib import Path

from collections import deque
from enum import Enum, auto
from rng import RNG


class TileType(Enum):
    WALL = auto()
    FLOOR = auto()
    STAIRS_DOWN = auto()

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

class Player:
    def __init__(self, x: int, y: int, hp: int = 100):
        self.x = x
        self.y = y
        self.hp = hp
        self.inventory = []
        self.atk = 5
        self.def_stat = 1

class Enemy:
    def __init__(self, x: int, y: int, enemy_id: str, name: str, hp: int, atk: int, def_stat: int):
        self.x = x
        self.y = y
        self.enemy_id = enemy_id
        self.name = name
        self.hp = hp
        self.atk = atk
        self.def_stat = def_stat

class Engine:
    def __init__(self, rng: RNG, game_map: GameMap, player: Player, enemies: list[Enemy], enemy_types: dict, current_depth: int = 1, deltas=None):
        self.rng = rng
        self.game_map = game_map
        self.player = player
        self.enemies = enemies
        self.enemy_types = enemy_types
        self.seed = rng.seed
        self.current_depth = current_depth
        self.level_seeds = {1: self.seed}
        self.deltas = deltas if deltas is not None else {}

    def move_player(self, dx: int, dy: int):
        dest_x = self.player.x + dx
        dest_y = self.player.y + dy

        for enemy in self.enemies:
            if dest_x == enemy.x and dest_y == enemy.y:
                # Combat initiated
                run_combat(self.player, enemy, self)
                return

        if self.game_map.tiles[dest_y][dest_x] == TileType.FLOOR:
            self.player.x = dest_x
            self.player.y = dest_y

    def descend(self):
        """Descend to the next level of the dungeon."""
        if self.game_map.tiles[self.player.y][self.player.x] != TileType.STAIRS_DOWN:
            print("You can't descend here.")
            return

        self.current_depth += 1
        print(f"You descend deeper into the dungeon, reaching level {self.current_depth}.")

        if self.current_depth not in self.level_seeds:
            # Derive a new seed for the new level
            self.level_seeds[self.current_depth] = self.seed + self.current_depth

        level_seed = self.level_seeds[self.current_depth]
        level_rng = RNG(level_seed)

        # Map parameters (should be centralized later)
        map_width = 80
        map_height = 45
        max_rooms = 30
        min_room_size = 6
        max_room_size = 10

        game_map, rooms, enemies = generate_map(level_rng, map_width, map_height, max_rooms, min_room_size, max_room_size, self.enemy_types)
        self.game_map = game_map

        # Place player
        if rooms:
            first_room = rooms[0]
            self.player.x = (first_room.x1 + first_room.x2) // 2
            self.player.y = (first_room.y1 + first_room.y2) // 2
        else:
            # Failsafe if map gen creates no rooms
            self.player.x = map_width // 2
            self.player.y = map_height // 2

        # Apply deltas for the new level
        level_deltas = self.deltas.get(str(self.current_depth), {})
        killed_enemies_coords = level_deltas.get("killed_enemies", [])

        self.enemies = [e for e in enemies if {"x": e.x, "y": e.y} not in killed_enemies_coords]


def save_game(engine: Engine, filename:str):
    """Saves the game state to a file."""
    enemies_data = [
        {"x": enemy.x, "y": enemy.y, "enemy_id": enemy.enemy_id, "hp": enemy.hp}
        for enemy in engine.enemies
    ]
    data = {
        "seed": engine.seed,
        "level_seeds": engine.level_seeds,
        "current_depth": engine.current_depth,
        "player": {
            "x": engine.player.x,
            "y": engine.player.y,
            "hp": engine.player.hp,
            "inventory": engine.player.inventory,
        },
        "enemies": enemies_data,
        "deltas": engine.deltas,
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

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

def run_combat(player: Player, enemy: Enemy, engine: Engine):
    while player.hp > 0 and enemy.hp > 0:
        print(f"You encounter a {enemy.name}!")
        print(f"Player HP: {player.hp} | {enemy.name} HP: {enemy.hp}")
        action = input("Choose action: (a)ttack, (f)lee> ").lower().strip()

        if action == "a":
            # Player attacks enemy
            player_damage = max(0, player.atk - enemy.def_stat)
            enemy.hp -= player_damage
            print(f"You attack the {enemy.name} for {player_damage} damage.")

            if enemy.hp <= 0:
                print(f"You defeated the {enemy.name}!")
                level_deltas = engine.deltas.setdefault(str(engine.current_depth), {})
                killed_enemies = level_deltas.setdefault("killed_enemies", [])
                killed_enemies.append({"x": enemy.x, "y": enemy.y})
                engine.enemies.remove(enemy)
                break

            # Enemy attacks player
            enemy_damage = max(0, enemy.atk - player.def_stat)
            player.hp -= enemy_damage
            print(f"The {enemy.name} attacks you for {enemy_damage} damage.")

            if player.hp <= 0:
                print("You have been defeated.")
                raise SystemExit()

        elif action == "f":
            print("You flee from the combat.")
            # Basic flee mechanic: 50% chance to succeed
            if engine.rng.randint(0, 1) == 1:
                print("You successfully escaped!")
                break
            else:
                print("You failed to escape!")
                # Enemy gets a free attack
                enemy_damage = max(0, enemy.atk - player.def_stat)
                player.hp -= enemy_damage
                print(f"The {enemy.name} attacks you for {enemy_damage} damage.")
                if player.hp <= 0:
                    print("You have been defeated.")
                    raise SystemExit()
        else:
            print("Invalid action.")


def render_map(game_map: GameMap, player_x: int, player_y: int, enemies: list[Enemy]):
    """Renders the map to the console."""
    for y in range(game_map.height):
        for x in range(game_map.width):
            if x == player_x and y == player_y:
                print("@", end="")
            elif any(enemy.x == x and enemy.y == y for enemy in enemies):
                print("E", end="")
            elif game_map.tiles[y][x] == TileType.STAIRS_DOWN:
                print(">", end="")
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

def _place_enemies(rng: RNG, rooms: list[Rect], enemy_types: dict) -> list[Enemy]:
    enemies = []
    if not rooms or not enemy_types:
        return enemies

    player_start_room = rooms[0]
    player_start_pos = (
        (player_start_room.x1 + player_start_room.x2) // 2,
        (player_start_room.y1 + player_start_room.y2) // 2,
    )

    for room in rooms:
        # Try to place one enemy per room, avoiding the player's start tile.
        for _ in range(5):  # 5 attempts to find a valid spot
            x = rng.randint(room.x1 + 1, room.x2 - 1)
            y = rng.randint(room.y1 + 1, room.y2 - 1)

            if (x, y) == player_start_pos:
                continue

            if any(enemy.x == x and enemy.y == y for enemy in enemies):
                continue

            enemy_id = rng.choice(list(enemy_types.keys()))
            enemy_data = enemy_types[enemy_id]
            enemy = Enemy(
                x=x,
                y=y,
                enemy_id=enemy_id,
                name=enemy_data["name"],
                hp=enemy_data["hp"],
                atk=enemy_data["atk"],
                def_stat=enemy_data["def"],
            )
            enemies.append(enemy)
            break  # Move to the next room after placing one enemy
    return enemies


def generate_map(rng: RNG, width: int, height: int, max_rooms: int, min_room_size: int, max_room_size: int, enemy_types: dict) -> tuple[GameMap, list[Rect], list[Enemy]]:
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
                enemies = _place_enemies(rng, rooms, enemy_types)
                if rooms:
                    last_room = rooms[-1]
                    stair_x = (last_room.x1 + last_room.x2) // 2
                    stair_y = (last_room.y1 + last_room.y2) // 2
                    game_map.tiles[stair_y][stair_x] = TileType.STAIRS_DOWN
                return game_map, rooms, enemies

def load_game(filename: str) -> Engine:
    """Loads a game state from a file."""
    with open(filename, "r") as f:
        data = json.load(f)

    current_depth = data.get("current_depth", 1)
    level_seeds = data.get("level_seeds", {1: data["seed"]})
    # Ensure level_seeds keys are integers
    level_seeds = {int(k): v for k, v in level_seeds.items()}

    level_seed = level_seeds[current_depth]
    rng = RNG(level_seed)

    # Map parameters
    map_width = 80
    map_height = 45
    max_rooms = 30
    min_room_size = 6
    max_room_size = 10

    content = load_content()
    enemy_types = {enemy_data["id"]: enemy_data for enemy_data in content["enemies"]}
    # We generate the map, but will replace the enemies with the loaded state.
    game_map, _, _ = generate_map(rng, map_width, map_height, max_rooms, min_room_size, max_room_size, enemy_types)

    player_data = data["player"]
    player = Player(player_data["x"], player_data["y"], player_data["hp"])
    player.inventory = player_data["inventory"]

    # Load enemies from save file to preserve their state (e.g., HP) on the current level
    enemies_data = data.get("enemies", [])
    enemies = []
    for enemy_data in enemies_data:
        enemy_id = enemy_data["enemy_id"]
        base_enemy_data = enemy_types[enemy_id]
        enemy = Enemy(
            x=enemy_data["x"],
            y=enemy_data["y"],
            enemy_id=enemy_id,
            name=base_enemy_data["name"],
            hp=enemy_data["hp"],
            atk=base_enemy_data["atk"],
            def_stat=base_enemy_data["def"],
        )
        enemies.append(enemy)

    deltas = data.get("deltas", {})

    engine = Engine(rng, game_map, player, enemies, enemy_types, current_depth, deltas)
    engine.seed = data["seed"]  # This is the master seed
    engine.level_seeds = level_seeds
    return engine

def main():
    content = load_content()
    enemy_types = {enemy_data["id"]: enemy_data for enemy_data in content["enemies"]}

    if "--load" in sys.argv:
        engine = load_game("save.json")
        print("Game loaded.")
    else:
        seed = None
        if len(sys.argv) > 1:
            try:
                seed = int(sys.argv[1])
                print(f"Using seed from command line: {seed}")
            except ValueError:
                print(f"Invalid seed: {sys.argv[1]}. Using a random seed.")
        rng = RNG(seed)

        # Map parameters
        map_width = 80
        map_height = 45
        max_rooms = 30
        min_room_size = 6
        max_room_size = 10

        game_map, rooms, enemies = generate_map(rng, map_width, map_height, max_rooms, min_room_size, max_room_size, enemy_types)

        player_x, player_y = 0, 0
        if rooms:
            first_room = rooms[0]
            player_x = (first_room.x1 + first_room.x2) // 2
            player_y = (first_room.y1 + first_room.y2) // 2

        player = Player(player_x, player_y)
        engine = Engine(rng, game_map, player, enemies, enemy_types)

    while True:
        render_map(engine.game_map, engine.player.x, engine.player.y, engine.enemies)

        action = input("> ").lower().strip()

        if action == 'w':
            engine.move_player(0, -1)
        elif action == 's':
            engine.move_player(0, 1)
        elif action == 'a':
            engine.move_player(-1, 0)
        elif action == 'd':
            engine.move_player(1, 0)
        elif action == '>':
            engine.descend()
        elif action == 'p':
            save_game(engine, "save.json")
            print("Game saved.")
        elif action in ["q", "quit"]:
            raise SystemExit()

if __name__ == "__main__":
    main()
