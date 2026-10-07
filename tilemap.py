# tilemap.py — Tile map rendering, wall-query logic, and theme switching.

import pygame
from settings import (
    TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT,
    WALL_COLOR, FLOOR_COLOR,
    DUNGEON_WALL_COLOR, DUNGEON_FLOOR_COLOR,
    TILE_EXIT,
)

# ---- Tile type constants -----------------------------------------------
TILE_FLOOR = 0
TILE_WALL  = 1
# TILE_EXIT  = 2  (imported from settings, re-exported below for convenience)

# ---- Active theme colors (module-level, changed by set_*_theme()) ------
_current_wall_color  = WALL_COLOR
_current_floor_color = FLOOR_COLOR

# Pre-compute border shades from the base constants (updated with the theme)
def _wall_border():
    return tuple(max(0, c - 20) for c in _current_wall_color)

def _floor_border():
    return tuple(max(0, c - 15) for c in _current_floor_color)


# ---- Theme switching ---------------------------------------------------

def set_town_theme() -> None:
    """Switch tile colors back to the overworld (town) palette."""
    global _current_wall_color, _current_floor_color
    _current_wall_color  = WALL_COLOR
    _current_floor_color = FLOOR_COLOR


def set_dungeon_theme() -> None:
    """Switch tile colors to the underground (dungeon) palette."""
    global _current_wall_color, _current_floor_color
    _current_wall_color  = DUNGEON_WALL_COLOR
    _current_floor_color = DUNGEON_FLOOR_COLOR


# ---- TileMap class -----------------------------------------------------

class TileMap:
    """Holds tile data and draws the visible portion of the map."""

    def __init__(self, data: list):
        """
        Args:
            data: 2-D list [row][col] of tile type integers.
                  Row 0 is the top of the map.
        """
        self._data   = data
        self._height = len(data)
        self._width  = len(data[0]) if self._height > 0 else 0

    # ------------------------------------------------------------------ #
    #  Properties                                                          #
    # ------------------------------------------------------------------ #

    @property
    def width(self) -> int:
        """Map width in tiles."""
        return self._width

    @property
    def height(self) -> int:
        """Map height in tiles."""
        return self._height

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def is_wall(self, tile_x: int, tile_y: int) -> bool:
        """
        Return True if the tile at (tile_x, tile_y) blocks movement.

        Out-of-bounds coords are treated as walls.
        TILE_EXIT (value 2) is walkable — returns False.
        """
        if tile_x < 0 or tile_y < 0 or tile_x >= self._width or tile_y >= self._height:
            return True
        tile = self._data[tile_y][tile_x]
        # TILE_WALL (1) blocks; everything else (FLOOR=0, EXIT=2) is walkable
        return tile == TILE_WALL

    def get_tile(self, tile_x: int, tile_y: int) -> int:
        """Return the tile type at (tile_x, tile_y), or TILE_WALL if out of bounds."""
        if tile_x < 0 or tile_y < 0 or tile_x >= self._width or tile_y >= self._height:
            return TILE_WALL
        return self._data[tile_y][tile_x]

    def draw(self, surface: pygame.Surface, camera_offset: tuple):
        """
        Draw only the tiles currently visible on screen (plus a 1-tile margin).

        Uses the module-level theme colors set by set_town_theme() /
        set_dungeon_theme().

        Args:
            surface:       The pygame surface to draw onto.
            camera_offset: (offset_x, offset_y) — world-pixel position of the
                           screen's top-left corner (from Camera.offset).
        """
        off_x, off_y = camera_offset

        # Tile range visible on screen (clamped to map bounds)
        start_col = max(0, int(off_x // TILE_SIZE) - 1)
        start_row = max(0, int(off_y // TILE_SIZE) - 1)
        end_col   = min(self._width,  int((off_x + SCREEN_WIDTH)  // TILE_SIZE) + 2)
        end_row   = min(self._height, int((off_y + SCREEN_HEIGHT) // TILE_SIZE) + 2)

        # Compute borders from current theme (cheap tuple comprehension)
        w_border = _wall_border()
        f_border = _floor_border()

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tile_type = self._data[row][col]

                screen_x = col * TILE_SIZE - int(off_x)
                screen_y = row * TILE_SIZE - int(off_y)

                if tile_type == TILE_WALL:
                    fill_color   = _current_wall_color
                    border_color = w_border
                elif tile_type == TILE_EXIT:
                    # EXIT tile — slightly brighter floor so it reads as a portal
                    fill_color   = tuple(min(255, c + 25) for c in _current_floor_color)
                    border_color = tuple(min(255, c + 40) for c in _current_floor_color)
                else:
                    # TILE_FLOOR (and any future floor-like tiles)
                    fill_color   = _current_floor_color
                    border_color = f_border

                rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(surface, fill_color,   rect)
                pygame.draw.rect(surface, border_color, rect, 1)  # 1-px border
