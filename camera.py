# camera.py — Follows the player and clamps to map bounds.

import pygame
import random
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

        # Screen shake
        self.shake_duration = 0
        self.shake_intensity = 0
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0

        # Smoothing
        self.lerp_factor = 0.1


    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def update(self, player_rect: pygame.Rect):
        """
        Center the camera on the player, then clamp so the viewport never
        extends beyond the map edges. Uses lerp for smoothness.
        """
        # Desired target offset
        target_x = player_rect.centerx - SCREEN_WIDTH  / 2
        target_y = player_rect.centery - SCREEN_HEIGHT / 2

        # Smoothly interpolate current offset towards target
        self.offset_x += (target_x - self.offset_x) * self.lerp_factor
        self.offset_y += (target_y - self.offset_y) * self.lerp_factor

        # Clamp to map bounds
        self.offset_x = max(0.0, min(self.offset_x,
                                      self.map_width_px  - SCREEN_WIDTH))
        self.offset_y = max(0.0, min(self.offset_y,
                                      self.map_height_px - SCREEN_HEIGHT))

        # Update shake
        if self.shake_duration > 0:
            self.shake_duration -= 1
            self.shake_offset_x = random.uniform(-self.shake_intensity, self.shake_intensity)
            self.shake_offset_y = random.uniform(-self.shake_intensity, self.shake_intensity)
        else:
            self.shake_offset_x = 0.0
            self.shake_offset_y = 0.0

    def trigger_shake(self, intensity: float, duration: int):
        """Start a screen shake effect."""
        self.shake_intensity = intensity
        self.shake_duration = duration

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """
        Return a new Rect shifted into screen-space, including shake offset.
        """
        return pygame.Rect(
            rect.x - int(self.offset_x + self.shake_offset_x),
            rect.y - int(self.offset_y + self.shake_offset_y),
            rect.width,
            rect.height,
        )

    @property
    def offset(self) -> tuple[float, float]:
        """Convenience tuple (offset_x, offset_y) including shake for tilemap.draw()."""
        return (self.offset_x + self.shake_offset_x, self.offset_y + self.shake_offset_y)
