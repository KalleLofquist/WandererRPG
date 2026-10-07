# main.py — Entry point: map definition, game loop, and wiring.

import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    BLACK
)
from tilemap import TileMap, TILE_FLOOR, TILE_WALL
from camera  import Camera
from player  import Player


# ------------------------------------------------------------------ #
#  Map builder                                                         #
# ------------------------------------------------------------------ #

def _fill_rect(grid: list[list[int]], col: int, row: int,
               w: int, h: int, tile: int):
    """Fill a rectangular region of the grid with a tile type."""
    for r in range(row, row + h):
        for c in range(col, col + w):
            if 0 <= r < MAP_HEIGHT and 0 <= c < MAP_WIDTH:
                grid[r][c] = tile


def build_map() -> tuple[list[list[int]], tuple[int, int]]:
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

    # Helper: carve a floor rectangle
    def carve(col, row, w, h):
        _fill_rect(grid, col, row, w, h, TILE_FLOOR)

    # ---- Rooms -------------------------------------------------------
    # Room A  (top-left)
    carve( 2,  2, 13, 11)
    # Room B  (top-centre)
    carve(18,  2, 13, 11)
    # Room C  (top-right)
    carve(34,  2, 14, 11)
    # Room D  (bottom-left / centre)
    carve( 6, 18, 15, 16)
    # Room E  (bottom-right / centre)
    carve(28, 18, 17, 16)

    # ---- Horizontal corridors (3 tiles tall) -------------------------
    # A → B  (row 6–8, cols 15–17)
    carve(15,  6,  3,  3)
    # B → C  (row 6–8, cols 31–33)
    carve(31,  6,  3,  3)
    # D → E  (row 24–26, cols 21–27)
    carve(21, 24,  7,  3)

    # ---- Vertical corridors (3 tiles wide) ---------------------------
    # A → D  (col 7–9, rows 13–17)
    carve( 7, 13,  3,  5)
    # B → D  (col 22–24, rows 13–17)
    carve(22, 13,  3,  5)
    # C → E  (col 36–38, rows 13–17)
    carve(36, 13,  3,  5)

    # ---- Player spawn: centre of Room A ------------------------------
    spawn_tile_col = 2 + 13 // 2   # col 8
    spawn_tile_row = 2 + 11 // 2   # row 7
    spawn_px = (spawn_tile_col * TILE_SIZE,
                spawn_tile_row * TILE_SIZE)

    return grid, spawn_px


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

        # ---- Update --------------------------------------------------
        keys = pygame.key.get_pressed()
        player.handle_input(keys, tilemap)
        camera.update(player.rect)

        # ---- Draw ----------------------------------------------------
        screen.fill(BLACK)
        tilemap.draw(screen, camera.offset)
        player.draw(screen, camera)

        pygame.display.flip()

        # ---- Timing --------------------------------------------------
        clock.tick(FPS)
        pygame.display.set_caption(
            f"RPG Adventure — FPS: {clock.get_fps():.0f}"
        )

    pygame.quit()


if __name__ == "__main__":
    main()
