# player.py — Player entity: movement, collision, and rendering.

import pygame
from settings import (
    PLAYER_SPEED, PLAYER_SIZE, PLAYER_COLOR, TILE_SIZE
)

# A slightly darker shade for the directional arrow
_ARROW_COLOR = tuple(max(0, c - 60) for c in PLAYER_COLOR)


class Player:
    """
    The player character.

    Movement is pixel-based (sub-tile) with tile-based collision:
    we project the player's bounding box one step forward, sample the
    four corners, and only move if every corner lands on a floor tile.
    """

    # Direction constants — used for arrow rendering
    RIGHT = 0
    DOWN  = 1
    LEFT  = 2
    UP    = 3

    def __init__(self, x: float, y: float):
        """
        Args:
            x, y: Top-left world-pixel coordinates (floats for sub-pixel precision).
        """
        self._x: float = float(x)
        self._y: float = float(y)
        self._direction: int = self.DOWN   # facing direction for the arrow

    # ------------------------------------------------------------------ #
    #  Properties                                                          #
    # ------------------------------------------------------------------ #

    @property
    def rect(self) -> pygame.Rect:
        """Current bounding box in world-pixel space (integer)."""
        return pygame.Rect(int(self._x), int(self._y), PLAYER_SIZE, PLAYER_SIZE)

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _corners_clear(self, px: float, py: float, tilemap) -> bool:
        """
        Return True if all four corners of a PLAYER_SIZE square placed at
        (px, py) are on floor tiles.
        """
        corners = [
            (px,                        py),
            (px + PLAYER_SIZE - 1,      py),
            (px,                        py + PLAYER_SIZE - 1),
            (px + PLAYER_SIZE - 1,      py + PLAYER_SIZE - 1),
        ]
        for cx, cy in corners:
            tile_x = int(cx) // TILE_SIZE
            tile_y = int(cy) // TILE_SIZE
            if tilemap.is_wall(tile_x, tile_y):
                return False
        return True

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def handle_input(self, keys, tilemap):
        """
        Read WASD / arrow keys and move the player if the destination is clear.

        Horizontal movement takes priority over vertical.  Each axis is tested
        independently so the player can slide along walls smoothly.
        """
        dx = 0
        dy = 0

        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            dx = -PLAYER_SPEED
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx =  PLAYER_SPEED

        if keys[pygame.K_UP]   or keys[pygame.K_w]:
            dy = -PLAYER_SPEED
        elif keys[pygame.K_DOWN]  or keys[pygame.K_s]:
            dy =  PLAYER_SPEED

        # Update facing direction (last pressed direction wins)
        if dx > 0:
            self._direction = self.RIGHT
        elif dx < 0:
            self._direction = self.LEFT
        elif dy < 0:
            self._direction = self.UP
        elif dy > 0:
            self._direction = self.DOWN

        # Try horizontal movement independently
        if dx != 0:
            new_x = self._x + dx
            if self._corners_clear(new_x, self._y, tilemap):
                self._x = new_x

        # Try vertical movement independently (allows wall-sliding)
        if dy != 0:
            new_y = self._y + dy
            if self._corners_clear(self._x, new_y, tilemap):
                self._y = new_y

    def draw(self, surface: pygame.Surface, camera):
        """
        Draw the player rectangle and a small directional arrow.

        Args:
            surface: The pygame surface to draw onto.
            camera:  Camera instance — used to convert world → screen coords.
        """
        screen_rect = camera.apply(self.rect)

        # Main body
        pygame.draw.rect(surface, PLAYER_COLOR, screen_rect)

        # Directional arrow (small filled triangle on the leading face)
        self._draw_arrow(surface, screen_rect)

    def _draw_arrow(self, surface: pygame.Surface, screen_rect: pygame.Rect):
        """Draw a small solid triangle indicating the player's facing direction."""
        cx = screen_rect.centerx
        cy = screen_rect.centery
        r  = screen_rect        # shorthand
        tip_inset = 5           # how far the tip pokes toward the edge
        side_half = 5           # half-width of the arrow base

        if self._direction == self.RIGHT:
            points = [
                (r.right - tip_inset,     cy),
                (r.centerx - side_half,   cy - side_half),
                (r.centerx - side_half,   cy + side_half),
            ]
        elif self._direction == self.LEFT:
            points = [
                (r.left  + tip_inset,     cy),
                (r.centerx + side_half,   cy - side_half),
                (r.centerx + side_half,   cy + side_half),
            ]
        elif self._direction == self.UP:
            points = [
                (cx,                      r.top    + tip_inset),
                (cx - side_half,          r.centery + side_half),
                (cx + side_half,          r.centery + side_half),
            ]
        else:  # DOWN
            points = [
                (cx,                      r.bottom - tip_inset),
                (cx - side_half,          r.centery - side_half),
                (cx + side_half,          r.centery - side_half),
            ]

        pygame.draw.polygon(surface, _ARROW_COLOR, points)
