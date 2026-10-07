# maps.py — Map layout definitions for all game areas.
#
# Each build_*() function returns a dict describing the full map data:
#   grid          — 2D list[list[int]] of tile types (TILE_FLOOR / TILE_WALL / TILE_EXIT)
#   player_spawn  — (px, py) world-pixel top-left for the player on entry
#   enemy_spawns  — list of (x, y, patrol_start, patrol_end) tuples
#   npc_spawns    — list of (tile_col, tile_row, name, dialogue_lines)
#   item_spawns   — list of (tile_col, tile_row, item_type_str)
#   exit_tiles    — list of {'col': c, 'row': r, 'target': map_id}
#   map_width     — width in tiles
#   map_height    — height in tiles

from settings import (
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    TILE_EXIT,
    MAP_ID_TOWN, MAP_ID_DUNGEON,
)
from tilemap import TILE_FLOOR, TILE_WALL


# ------------------------------------------------------------------ #
#  Internal helpers                                                    #
# ------------------------------------------------------------------ #

def _make_grid(width: int, height: int) -> list:
    """Return a 2D grid completely filled with TILE_WALL."""
    return [[TILE_WALL] * width for _ in range(height)]


def _fill_rect(grid: list, col: int, row: int, w: int, h: int, tile: int, max_col: int, max_row: int):
    """Fill a rectangular region of the grid with a tile type (bounds-checked)."""
    for r in range(row, row + h):
        for c in range(col, col + w):
            if 0 <= r < max_row and 0 <= c < max_col:
                grid[r][c] = tile


# ------------------------------------------------------------------ #
#  Town map                                                            #
# ------------------------------------------------------------------ #

def build_town_map() -> dict:
    """
    Build the 50×38 town / overworld map.

    Layout (tile coords, col × row):
      Room A  :  cols  2-14,  rows  2-12  (13×11) — player spawn
      Room B  :  cols 18-30,  rows  2-12  (13×11)
      Room C  :  cols 34-47,  rows  2-12  (14×11)
      Room D  :  cols  6-20,  rows 18-33  (15×16)
      Room E  :  cols 28-44,  rows 18-33  (17×16)

    Corridors (3 tiles wide/tall) connect the rooms.

    Phase 3 additions:
      - EXIT tile at col=13, row=34  (south of Room D → dungeon)
      - NPC  "Elder" at col=5, row=4
      - Health potions at (col=10, row=4) and (col=22, row=5)
    """
    W, H = MAP_WIDTH, MAP_HEIGHT
    grid = _make_grid(W, H)

    def carve(col, row, w, h):
        _fill_rect(grid, col, row, w, h, TILE_FLOOR, W, H)

    # ---- Rooms -------------------------------------------------------
    carve( 2,  2, 13, 11)   # Room A — player spawn
    carve(18,  2, 13, 11)   # Room B
    carve(34,  2, 14, 11)   # Room C
    carve( 6, 18, 15, 16)   # Room D
    carve(28, 18, 17, 16)   # Room E

    # ---- Horizontal corridors (3 tiles tall) -------------------------
    carve(15,  6,  3,  3)   # A → B
    carve(31,  6,  3,  3)   # B → C
    carve(21, 24,  7,  3)   # D → E

    # ---- Vertical corridors (3 tiles wide) ---------------------------
    carve( 7, 13,  3,  5)   # A → D
    carve(22, 13,  3,  5)   # B → D
    carve(36, 13,  3,  5)   # C → E

    # ---- Exit passage from the bottom of Room D ----------------------
    # Small 3-tile-wide stub going south from row 33 to row 35,
    # then the exit trigger sits at the middle tile (col 13, row 34).
    carve(12, 33, 3, 3)     # stub: cols 12-14, rows 33-35
    grid[34][13] = TILE_EXIT

    # ------------------------------------------------------------------ #
    #  Spawn data                                                          #
    # ------------------------------------------------------------------ #

    # Player spawn — centre of Room A
    spawn_col = 2 + 13 // 2   # col 8
    spawn_row = 2 + 11 // 2   # row 7
    player_spawn = (spawn_col * TILE_SIZE, spawn_row * TILE_SIZE)

    # Enemy spawns — (world_x, world_y, patrol_start_tile, patrol_end_tile)
    # One enemy per major room (excluding Room A) + one in the D↔E corridor.
    enemy_spawns = [
        # Room B — patrol across the room
        (24 * TILE_SIZE, 7 * TILE_SIZE,  (19, 4),  (29, 10)),
        # Room C — patrol across the room
        (40 * TILE_SIZE, 7 * TILE_SIZE,  (35, 4),  (46, 10)),
        # Room D — patrol top-to-bottom
        (13 * TILE_SIZE, 25 * TILE_SIZE, (7,  19), (19, 32)),
        # Room E — patrol top-to-bottom
        (36 * TILE_SIZE, 25 * TILE_SIZE, (29, 19), (43, 32)),
        # Corridor D↔E — short patrol in the passage
        (24 * TILE_SIZE, 25 * TILE_SIZE, (22, 24), (26, 26)),
    ]

    # NPC spawns — (tile_col, tile_row, name, [dialogue_lines])
    npc_spawns = [
        (
            5, 4,
            "Elder",
            [
                "Welcome, wanderer. These lands grow dangerous.",
                "I have heard dark creatures stir beneath the old keep.",
                "Descend through the southern passage if you dare... but be careful.",
            ],
        ),
    ]

    # Item spawns — (tile_col, tile_row, item_type_str)
    item_spawns = [
        (10, 4, 'health_potion'),   # Room A
        (22, 5, 'health_potion'),   # Room B
    ]

    # Exit tiles
    exit_tiles = [
        {'col': 13, 'row': 34, 'target': MAP_ID_DUNGEON},
    ]

    return {
        'grid':         grid,
        'player_spawn': player_spawn,
        'enemy_spawns': enemy_spawns,
        'npc_spawns':   npc_spawns,
        'item_spawns':  item_spawns,
        'exit_tiles':   exit_tiles,
        'map_width':    W,
        'map_height':   H,
    }


# ------------------------------------------------------------------ #
#  Dungeon map                                                         #
# ------------------------------------------------------------------ #

def build_dungeon_map() -> dict:
    """
    Build the 50×38 dungeon map.

    Layout (tile coords):
      Room 1 (entry) : cols  4-14, rows  2-10  (11×9)  — player spawns here
      Room 2         : cols 18-28, rows  2-10  (11×9)
      Room 3         : cols 32-46, rows  2-14  (15×13)
      Room 4         : cols  4-20, rows 16-28  (17×13)
      Room 5         : cols 24-46, rows 18-34  (23×17)

    Narrow corridors (2 tiles wide):
      Room1 → Room2  : col 15-17, rows 5-6
      Room2 → Room3  : col 29-31, rows 5-6
      Room1 → Room4  : col 7-8,  rows 11-15
      Room3 → Room5  : col 35-36, rows 15-17
      Room4 → Room5  : col 21-23, rows 22-23

    Phase 3 additions:
      - EXIT tile at col=8, row=3 (inside Room 1) → back to town
      - 6 enemies spread across rooms 2–5
      - 2 health potions (Room 3 and Room 5)
    """
    W, H = MAP_WIDTH, MAP_HEIGHT
    grid = _make_grid(W, H)

    def carve(col, row, w, h):
        _fill_rect(grid, col, row, w, h, TILE_FLOOR, W, H)

    # ---- Rooms -------------------------------------------------------
    carve( 4,  2, 11,  9)   # Room 1 — entry / player spawn
    carve(18,  2, 11,  9)   # Room 2
    carve(32,  2, 15, 13)   # Room 3
    carve( 4, 16, 17, 13)   # Room 4
    carve(24, 18, 23, 17)   # Room 5

    # ---- Narrow corridors (2 tiles wide) ----------------------------
    carve(15,  5,  3,  2)   # Room1 → Room2  (cols 15-17, rows 5-6)
    carve(29,  5,  3,  2)   # Room2 → Room3  (cols 29-31, rows 5-6)
    carve( 7, 11,  2,  5)   # Room1 → Room4  (cols 7-8,  rows 11-15)
    carve(35, 15,  2,  3)   # Room3 → Room5  (cols 35-36, rows 15-17)
    carve(21, 22,  3,  2)   # Room4 → Room5  (cols 21-23, rows 22-23)

    # ---- EXIT tile — inside Room 1, near the top --------------------
    grid[3][8] = TILE_EXIT

    # ------------------------------------------------------------------ #
    #  Spawn data                                                          #
    # ------------------------------------------------------------------ #

    # Player spawn — centre of Room 1
    spawn_col = 4 + 11 // 2   # col 9
    spawn_row = 2 +  9 // 2   # row 6
    player_spawn = (spawn_col * TILE_SIZE, spawn_row * TILE_SIZE)

    # Enemy spawns — 6 enemies in rooms 2-5 (use dungeon stats in main.py)
    enemy_spawns = [
        # Room 2 — two patrollers
        (20 * TILE_SIZE,  4 * TILE_SIZE, (19,  3), (27,  9)),
        (24 * TILE_SIZE,  7 * TILE_SIZE, (19,  3), (27,  9)),
        # Room 3 — one patrol across the large room
        (38 * TILE_SIZE,  6 * TILE_SIZE, (33,  3), (45, 13)),
        # Room 4 — one patrol
        (10 * TILE_SIZE, 22 * TILE_SIZE, (5,  17), (19, 27)),
        # Room 5 — two patrollers
        (30 * TILE_SIZE, 24 * TILE_SIZE, (25, 19), (45, 33)),
        (40 * TILE_SIZE, 28 * TILE_SIZE, (25, 19), (45, 33)),
    ]

    # No NPCs in the dungeon
    npc_spawns = []

    # Two health potions
    item_spawns = [
        (40,  8, 'health_potion'),   # Room 3
        (36, 28, 'health_potion'),   # Room 5
    ]

    # Exit tile back to town
    exit_tiles = [
        {'col': 8, 'row': 3, 'target': MAP_ID_TOWN},
    ]

    return {
        'grid':         grid,
        'player_spawn': player_spawn,
        'enemy_spawns': enemy_spawns,
        'npc_spawns':   npc_spawns,
        'item_spawns':  item_spawns,
        'exit_tiles':   exit_tiles,
        'map_width':    W,
        'map_height':   H,
    }
