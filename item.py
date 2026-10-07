# item.py — Collectible items: base class and HealthPotion.

import math
import pygame
from settings import (
    TILE_SIZE,
    POTION_COLOR, POTION_HEAL_AMOUNT, POTION_PULSE_FRAMES,
)

# Items are rendered as 16×16 squares (smaller than the player)
_ITEM_SIZE = 16


class Item:
    """
    Abstract base class for all collectible items.

    Subclasses must implement:
        draw(surface, camera, frame_counter)  — rendering
        on_pickup(player)                     — called on collection;
                                                return True to remove the item
    """

    def __init__(self, tile_col: int, tile_row: int):
        """
        Args:
            tile_col: Tile column of the item (centred within the tile).
            tile_row: Tile row of the item.
        """
        # Centre the item within its tile
        self._x = tile_col * TILE_SIZE + (TILE_SIZE - _ITEM_SIZE) // 2
        self._y = tile_row * TILE_SIZE + (TILE_SIZE - _ITEM_SIZE) // 2

    @property
    def rect(self) -> pygame.Rect:
        """World-space bounding box for pickup collision detection."""
        return pygame.Rect(int(self._x), int(self._y), _ITEM_SIZE, _ITEM_SIZE)

    def draw(self, surface: pygame.Surface, camera, frame_counter: int) -> None:
        """Override in subclasses."""
        raise NotImplementedError

    def on_pickup(self, player) -> bool:
        """
        Called when the player collides with this item.

        Returns:
            True  — remove this item from the world.
            False — keep it (e.g. can't pick up right now).
        """
        raise NotImplementedError


class HealthPotion(Item):
    """
    A green flask that restores POTION_HEAL_AMOUNT HP to the player.

    Renders with a sine-wave brightness pulse so it stands out on the map.
    """

    def draw(self, surface: pygame.Surface, camera, frame_counter: int) -> None:
        """
        Draw a pulsing green square at the item's world position.

        Args:
            surface:       Display surface.
            camera:        Camera instance for world→screen transform.
            frame_counter: Global frame counter used to drive the pulse animation.
        """
        # Sinusoidal brightness oscillation ±30 around the base color
        pulse = math.sin(frame_counter / POTION_PULSE_FRAMES * 2.0 * math.pi)
        mod   = int(pulse * 30)
        color = tuple(max(0, min(255, c + mod)) for c in POTION_COLOR)

        screen_rect = camera.apply(self.rect)
        pygame.draw.rect(surface, color, screen_rect)

        # Thin white border so it reads clearly against dark floors
        border = tuple(min(255, c + 60) for c in color)
        pygame.draw.rect(surface, border, screen_rect, 1)

    def on_pickup(self, player) -> bool:
        """
        Heal the player by up to POTION_HEAL_AMOUNT (capped at max HP).

        Returns True (item is consumed on pickup).
        """
        heal = min(POTION_HEAL_AMOUNT, player.max_hp - player.hp)
        if heal > 0:
            player.hp += heal

        # Play potion chime (lazy import avoids circular dependency)
        try:
            import sounds
            sounds.play_potion()
        except Exception:
            pass

        return True   # always remove after pickup
