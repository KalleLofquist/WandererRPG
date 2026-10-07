# camera.py — Follows the player and clamps to map bounds.

import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    """
    Tracks the player and provides a coordinate transform for rendering.

    The camera stores the world-pixel coordinate of the screen's top-left
    corner (offset_x, offset_y).  Subtracting this offset from any world
    position gives the correct screen position.
    """

    def __init__(self, map_width_px: int, map_height_px: int):
        """
        Args:
            map_width_px:  Full map width  in pixels (MAP_WIDTH  * TILE_SIZE).
            map_height_px: Full map height in pixels (MAP_HEIGHT * TILE_SIZE).
        """
        self.map_width_px  = map_width_px
        self.map_height_px = map_height_px

        self.offset_x: float = 0.0
        self.offset_y: float = 0.0

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def update(self, player_rect: pygame.Rect):
        """
        Center the camera on the player, then clamp so the viewport never
        extends beyond the map edges.
        """
        # Desired offset: put player centre in the middle of the screen
        self.offset_x = player_rect.centerx - SCREEN_WIDTH  / 2
        self.offset_y = player_rect.centery - SCREEN_HEIGHT / 2

        # Clamp to map bounds
        self.offset_x = max(0.0, min(self.offset_x,
                                     self.map_width_px  - SCREEN_WIDTH))
        self.offset_y = max(0.0, min(self.offset_y,
                                     self.map_height_px - SCREEN_HEIGHT))

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """
        Return a new Rect shifted into screen-space.

        Args:
            rect: A world-space pygame.Rect.

        Returns:
            A new pygame.Rect in screen coordinates.
        """
        return pygame.Rect(
            rect.x - int(self.offset_x),
            rect.y - int(self.offset_y),
            rect.width,
            rect.height,
        )

    @property
    def offset(self) -> tuple[float, float]:
        """Convenience tuple (offset_x, offset_y) for tilemap.draw()."""
        return (self.offset_x, self.offset_y)
