# main.py — Entry point: map definition, game loop, and wiring.

import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    BLACK,
)
from tilemap import TileMap, TILE_FLOOR, TILE_WALL
from camera  import Camera
from player  import Player
from enemy   import Enemy
from combat  import resolve_combat
from hud     import draw_hud


# ------------------------------------------------------------------ #
#  Map builder                                                         #
# ------------------------------------------------------------------ #

def _fill_rect(grid: list, col: int, row: int, w: int, h: int, tile: int):
    """Fill a rectangular region of the grid with a tile type."""
    for r in range(row, row + h):
        for c in range(col, col + w):
            if 0 <= r < MAP_HEIGHT and 0 <= c < MAP_WIDTH:
                grid[r][c] = tile


def build_map() -> tuple:
    """
    Build and return a 50×38 tile grid together with the player's
    world-pixel spawn position (top-left of the spawn tile).

    Layout (all tile coords, col × row):
    ┌─────────────────────────────────────────────────────┐
    │  Room A  :  cols  2-14,  rows  2-12  (13×11)        │
    │  Room B  :  cols 18-30,  rows  2-12  (13×11)        │
    │  Room C  :  cols 34-47,  rows  2-12  (14×11)        │
    │  Room D  :  cols  6-20,  rows 18-33  (15×16)        │
    │  Room E  :  cols 28-44,  rows 18-33  (17×16)        │
    │                                                      │
    │  Corridors connect the rooms horizontally and        │
    │  vertically (3 tiles wide).                          │
    └─────────────────────────────────────────────────────┘
    Player spawns near the centre of Room A.
    """
    # Start with all walls
    grid = [[TILE_WALL] * MAP_WIDTH for _ in range(MAP_HEIGHT)]

    def carve(col, row, w, h):
        _fill_rect(grid, col, row, w, h, TILE_FLOOR)

    # ---- Rooms -------------------------------------------------------
    carve( 2,  2, 13, 11)   # Room A  (top-left)      — player spawn
    carve(18,  2, 13, 11)   # Room B  (top-centre)
    carve(34,  2, 14, 11)   # Room C  (top-right)
    carve( 6, 18, 15, 16)   # Room D  (bottom-left)
    carve(28, 18, 17, 16)   # Room E  (bottom-right)

    # ---- Horizontal corridors (3 tiles tall) -------------------------
    carve(15,  6,  3,  3)   # A → B
    carve(31,  6,  3,  3)   # B → C
    carve(21, 24,  7,  3)   # D → E

    # ---- Vertical corridors (3 tiles wide) ---------------------------
    carve( 7, 13,  3,  5)   # A → D
    carve(22, 13,  3,  5)   # B → D
    carve(36, 13,  3,  5)   # C → E

    # ---- Player spawn: centre of Room A ------------------------------
    spawn_tile_col = 2 + 13 // 2   # col 8
    spawn_tile_row = 2 + 11 // 2   # row 7
    spawn_px = (spawn_tile_col * TILE_SIZE, spawn_tile_row * TILE_SIZE)

    return grid, spawn_px


def _tile_px(tile_col: int, tile_row: int) -> tuple:
    """Convert tile coordinates to the world-pixel top-left of that tile."""
    return (tile_col * TILE_SIZE, tile_row * TILE_SIZE)


def spawn_enemies() -> list:
    """
    Create one Enemy per room (excluding Room A where the player starts).

    Each enemy is given two patrol waypoints near the room's extremes so
    it naturally traverses a meaningful portion of its room.

    Returns:
        List of Enemy instances ready to be updated and drawn.
    """
    enemies = []

    # Room B — top-centre (~24, 7)
    b_cx, b_cy = 24 * TILE_SIZE, 7 * TILE_SIZE
    enemies.append(Enemy(b_cx, b_cy, patrol_start=(19, 4), patrol_end=(29, 10)))

    # Room C — top-right (~40, 7)
    c_cx, c_cy = 40 * TILE_SIZE, 7 * TILE_SIZE
    enemies.append(Enemy(c_cx, c_cy, patrol_start=(35, 4), patrol_end=(46, 10)))

    # Room D — bottom-left (~13, 25)
    d_cx, d_cy = 13 * TILE_SIZE, 25 * TILE_SIZE
    enemies.append(Enemy(d_cx, d_cy, patrol_start=(7, 19), patrol_end=(19, 32)))

    # Room E — bottom-right (~36, 25)
    e_cx, e_cy = 36 * TILE_SIZE, 25 * TILE_SIZE
    enemies.append(Enemy(e_cx, e_cy, patrol_start=(29, 19), patrol_end=(43, 32)))

    # Corridor D↔E — near the connecting passage (~24, 25)
    de_cx, de_cy = 24 * TILE_SIZE, 25 * TILE_SIZE
    enemies.append(Enemy(de_cx, de_cy, patrol_start=(22, 24), patrol_end=(26, 26)))

    return enemies


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("RPG Adventure")

    clock = pygame.time.Clock()

    # --- Build world --------------------------------------------------
    map_data, (spawn_x, spawn_y) = build_map()

    tilemap = TileMap(map_data)
    player  = Player(spawn_x, spawn_y)
    enemies = spawn_enemies()
    camera  = Camera(
        map_width_px  = MAP_WIDTH  * TILE_SIZE,
        map_height_px = MAP_HEIGHT * TILE_SIZE,
    )

    # Prime the camera so it doesn't start at (0, 0) on frame 1
    camera.update(player.rect)

    # --- Main loop ----------------------------------------------------
    running = True
    while running:
        # ---- Events --------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Single-press attack (Space or F)
                elif event.key in (pygame.K_SPACE, pygame.K_f):
                    player.try_attack()

        # ---- Update --------------------------------------------------
        keys = pygame.key.get_pressed()
        # handle_input calls update_timers() internally
        player.handle_input(keys, tilemap)
        camera.update(player.rect)

        # Update all enemies
        for enemy in enemies:
            enemy.update(player.rect, tilemap)

        # Resolve combat: player swings, enemies hit player
        dead_enemies = resolve_combat(player, enemies)

        # Safely remove enemies that died this frame
        for dead in dead_enemies:
            if dead in enemies:
                enemies.remove(dead)

        # Check for player death
        if player.is_dead:
            print("Game Over")
            running = False

        # ---- Draw ----------------------------------------------------
        screen.fill(BLACK)
        tilemap.draw(screen, camera.offset)

        # Enemies drawn before player so player renders on top
        for enemy in enemies:
            enemy.draw(screen, camera)

        player.draw(screen, camera)

        # HUD drawn last (screen space — always on top)
        draw_hud(screen, player)

        pygame.display.flip()

        # ---- Timing --------------------------------------------------
        clock.tick(FPS)
        pygame.display.set_caption(
            f"RPG Adventure — FPS: {clock.get_fps():.0f}"
        )

    pygame.quit()


if __name__ == "__main__":
    main()
