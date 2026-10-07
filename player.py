# player.py — Player entity: movement, collision, combat, and rendering.

import pygame
from settings import (
    PLAYER_SPEED, PLAYER_SIZE, PLAYER_COLOR, TILE_SIZE,
    PLAYER_MAX_HP, PLAYER_ATTACK_DAMAGE, PLAYER_ATTACK_RANGE,
    PLAYER_ATTACK_DURATION, PLAYER_ATTACK_COOLDOWN,
    PLAYER_INVINCIBILITY_FRAMES,
)

# A slightly darker shade for the directional arrow
_ARROW_COLOR = tuple(max(0, c - 60) for c in PLAYER_COLOR)

# Semi-transparent yellow for the attack hitbox preview
_ATTACK_HITBOX_COLOR = (255, 230, 50, 120)   # RGBA — drawn on a temp surface


class Player:
    """
    The player character.

    Movement is pixel-based (sub-tile) with tile-based collision:
    we project the player's bounding box one step forward, sample the
    four corners, and only move if every corner lands on a floor tile.

    Phase 2 additions: HP, attack system, invincibility frames.
    """

    # Direction constants — used for arrow rendering and attack hitbox placement
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

        # --- Combat state ---
        self.hp: int              = PLAYER_MAX_HP
        self.max_hp: int          = PLAYER_MAX_HP
        self.is_attacking: bool   = False
        self.attack_timer: int    = 0        # frames remaining in the active swing
        self.attack_cooldown_timer: int = 0  # frames until next attack is allowed
        self.invincibility_timer: int   = 0  # frames of post-hit invincibility

    # ------------------------------------------------------------------ #
    #  Properties                                                          #
    # ------------------------------------------------------------------ #

    @property
    def rect(self) -> pygame.Rect:
        """Current bounding box in world-pixel space (integer)."""
        return pygame.Rect(int(self._x), int(self._y), PLAYER_SIZE, PLAYER_SIZE)

    @property
    def facing(self) -> int:
        """Public alias for _direction — used by external systems."""
        return self._direction

    @property
    def is_dead(self) -> bool:
        """True when the player's HP has reached zero."""
        return self.hp <= 0

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
    #  Combat API                                                          #
    # ------------------------------------------------------------------ #

    def update_timers(self):
        """
        Decrement all frame-countdown timers.  Must be called once per frame
        (either directly from the game loop or from handle_input).
        """
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.is_attacking = False

        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1

        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1

    def try_attack(self):
        """
        Begin an attack swing if the cooldown has expired.
        Sets is_attacking = True for PLAYER_ATTACK_DURATION frames.
        """
        if self.attack_cooldown_timer == 0:
            self.is_attacking          = True
            self.attack_timer          = PLAYER_ATTACK_DURATION
            self.attack_cooldown_timer = PLAYER_ATTACK_COOLDOWN

    def get_attack_rect(self) -> pygame.Rect:
        """
        Return the world-space Rect of the current attack hitbox.

        The hitbox is PLAYER_SIZE wide and PLAYER_ATTACK_RANGE deep,
        placed immediately in front of the player based on facing direction.
        """
        r = self.rect
        if self._direction == self.RIGHT:
            return pygame.Rect(r.right, r.top, PLAYER_ATTACK_RANGE, PLAYER_SIZE)
        elif self._direction == self.LEFT:
            return pygame.Rect(r.left - PLAYER_ATTACK_RANGE, r.top, PLAYER_ATTACK_RANGE, PLAYER_SIZE)
        elif self._direction == self.UP:
            return pygame.Rect(r.left, r.top - PLAYER_ATTACK_RANGE, PLAYER_SIZE, PLAYER_ATTACK_RANGE)
        else:  # DOWN
            return pygame.Rect(r.left, r.bottom, PLAYER_SIZE, PLAYER_ATTACK_RANGE)

    def take_damage(self, amount: int):
        """
        Reduce HP by amount (floored at 0) unless currently invincible.
        Grants PLAYER_INVINCIBILITY_FRAMES of invincibility on hit.
        """
        if self.invincibility_timer == 0:
            self.hp = max(0, self.hp - amount)
            self.invincibility_timer = PLAYER_INVINCIBILITY_FRAMES

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def handle_input(self, keys, tilemap):
        """
        Read WASD / arrow keys and move the player if the destination is clear.
        Space / F triggers an attack.

        Horizontal movement takes priority over vertical.  Each axis is tested
        independently so the player can slide along walls smoothly.

        Also ticks timers — call once per frame.
        """
        self.update_timers()

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

        # Attack input — handled here so it's available from held-key checks;
        # single-press attacks via K_SPACE/K_f events in main.py take priority,
        # but try_attack() is idempotent (no double-trigger while on cooldown).
        if keys[pygame.K_SPACE] or keys[pygame.K_f]:
            self.try_attack()

    def draw(self, surface: pygame.Surface, camera):
        """
        Draw the player rectangle and a small directional arrow.

        Phase 2 additions:
        - Invincibility flash: skip drawing every other 3-frame block.
        - Attack hitbox: semi-transparent yellow rect while is_attacking.

        Args:
            surface: The pygame surface to draw onto.
            camera:  Camera instance — used to convert world → screen coords.
        """
        # --- Invincibility flash ---
        # While invincible, alternate visible/invisible every 3 frames.
        if self.invincibility_timer > 0 and self.invincibility_timer % 6 < 3:
            return  # skip drawing this frame (flash effect)

        screen_rect = camera.apply(self.rect)

        # --- Attack hitbox preview ---
        if self.is_attacking:
            atk_world_rect  = self.get_attack_rect()
            atk_screen_rect = camera.apply(atk_world_rect)

            # Use a temporary surface so we can draw semi-transparently
            atk_surf = pygame.Surface(
                (atk_screen_rect.width, atk_screen_rect.height),
                pygame.SRCALPHA,
            )
            atk_surf.fill(_ATTACK_HITBOX_COLOR)
            surface.blit(atk_surf, (atk_screen_rect.x, atk_screen_rect.y))

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
