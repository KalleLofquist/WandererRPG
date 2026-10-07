# tilemap.py — Tile map rendering and wall-query logic.

import pygame
from settings import (
    TILE_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT,
    WALL_COLOR, FLOOR_COLOR
)

# Tile type constants
TILE_FLOOR = 0
TILE_WALL  = 1

# Slightly darkened border colours for the subtle separation line
_WALL_BORDER  = tuple(max(0, c - 20) for c in WALL_COLOR)
_FLOOR_BORDER = tuple(max(0, c - 15) for c in FLOOR_COLOR)


class TileMap:
    """Holds tile data and draws the visible portion of the map."""

    def __init__(self, data: list[list[int]]):
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
        """Return True if the tile at (tile_x, tile_y) is a wall or out of bounds."""
        if tile_x < 0 or tile_y < 0 or tile_x >= self._width or tile_y >= self._height:
            return True
        return self._data[tile_y][tile_x] == TILE_WALL

    def draw(self, surface: pygame.Surface, camera_offset: tuple[float, float]):
        """
        Draw only the tiles currently visible on screen (plus a 1-tile margin).

        Args:
            surface:       The pygame surface to draw onto.
            camera_offset: (offset_x, offset_y) — world-pixel position of the
                           screen's top-left corner (from Camera).
        """
        off_x, off_y = camera_offset

        # Tile range visible on screen (clamped to map bounds)
        start_col = max(0, int(off_x // TILE_SIZE) - 1)
        start_row = max(0, int(off_y // TILE_SIZE) - 1)
        end_col   = min(self._width,  int((off_x + SCREEN_WIDTH)  // TILE_SIZE) + 2)
        end_row   = min(self._height, int((off_y + SCREEN_HEIGHT) // TILE_SIZE) + 2)

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tile_type = self._data[row][col]

                # World-pixel position → screen position
                screen_x = col * TILE_SIZE - int(off_x)
                screen_y = row * TILE_SIZE - int(off_y)

                if tile_type == TILE_WALL:
                    fill_color   = WALL_COLOR
                    border_color = _WALL_BORDER
                else:
                    fill_color   = FLOOR_COLOR
                    border_color = _FLOOR_BORDER

                rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(surface, fill_color,   rect)
                pygame.draw.rect(surface, border_color, rect, 1)  # 1px border
