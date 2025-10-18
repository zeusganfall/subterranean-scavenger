# Game Engine Agents

This document outlines the core "agents" or systems that drive the game. Understanding these components is key to modifying or extending the game's functionality.

## Core Components

The game is built around a few key systems that work together. All core game logic is contained within `src/engine_core.py`.

### 1. Map Generation

*   **Description:** This system is responsible for creating the game world. It generates a map composed of rooms and tunnels.
*   **Process:**
    1.  A `GameMap` object is initialized with a set width and height.
    2.  The `generate_map` function creates a series of `Rect` objects (rooms) and carves them into the map.
    3.  Tunnels are carved between rooms to ensure connectivity.
    4.  The `check_map_connectivity` function verifies that all rooms are reachable.
*   **Key Functions:** `generate_map`, `_create_room`, `_create_h_tunnel`, `_create_v_tunnel`

### 2. Content Loader

*   **Description:** This system loads all external game data from JSON files located in the `data/` directory. This includes definitions for items, enemies, and procedural generation settings.
*   **Files:**
    *   `data/content.json`: Contains definitions for items, enemies, recipes, and zones.
    *   `data/procgen.json`: Contains parameters for map generation.
*   **Key Functions:** `load_content`, `load_procgen`, `load_json`

### 3. Combat System

*   **Description:** This system manages turn-based combat between the player and enemies.
*   **Process:**
    1.  Combat is initiated when the player attempts to move onto a tile occupied by an `Enemy`.
    2.  The `run_combat` function is called, which starts a loop that continues until either the player or the enemy is defeated.
    3.  Players can choose to attack or flee.
    4.  Damage is calculated using a simple formula: `damage = attacker_atk - defender_def`.
*   **Key Classes and Functions:** `Player`, `Enemy`, `run_combat`

### 4. Save/Load System

*   **Description:** This system handles the serialization of the game state to a `save.json` file, allowing players to save and resume their progress.
*   **Process:**
    *   `save_game` collects the player's state, enemy data, and the world seed into a JSON object.
    *   `load_game` reads the `save.json` file, re-generates the map using the saved seed, and restores the player and enemy states.
*   **Key Functions:** `save_game`, `load_game`

## Conventions

*   **Single File for Core Logic:** To keep things simple, all core game logic should be kept within `src/engine_core.py`. Avoid creating new Python files in the `src` directory.
*   **Data-Driven Design:** New content (like items or enemies) should be added to `data/content.json` rather than being hardcoded into the game logic.
*   **Testing:** Tests are located in the `tests/` directory. When making changes, ensure that existing tests pass and add new tests for new functionality where appropriate.