# player.py — Player entity: movement, collision, combat, rendering, XP/leveling, knockback.

import math
import pygame
from settings import (
    PLAYER_SPEED, PLAYER_SIZE, PLAYER_COLOR, TILE_SIZE,
    PLAYER_MAX_HP, PLAYER_ATTACK_DAMAGE, PLAYER_ATTACK_RANGE,
    PLAYER_ATTACK_DURATION, PLAYER_ATTACK_COOLDOWN,
    PLAYER_INVINCIBILITY_FRAMES,
    PLAYER_HP_PER_LEVEL, PLAYER_ATTACK_PER_LEVEL,
    PLAYER_BASE_XP_PER_LEVEL, PLAYER_XP_SCALE,
    LEVEL_UP_FLASH_DURATION,
    PLAYER_KNOCKBACK_FORCE, PLAYER_KNOCKBACK_FRICTION,
    HUD_LEVEL_UP_COLOR,
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
    Phase 4 additions: XP/leveling, knockback, level-up flash.
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

        # --- XP & leveling ---
        self.level: int               = 1
        self.xp: int                  = 0
        self.xp_to_next_level: int    = PLAYER_BASE_XP_PER_LEVEL
        self.attack_damage: int       = PLAYER_ATTACK_DAMAGE   # grows with level
        self.level_up_flash_timer: int = 0

        # --- Knockback ---
        self.knockback_vx: float = 0.0
        self.knockback_vy: float = 0.0

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

    def update_timers(self, tilemap):
        """
        Decrement all frame-countdown timers and apply knockback movement.
        Must be called once per frame (via handle_input).

        Args:
            tilemap: TileMap instance for knockback wall collision.
        """
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.is_attacking = False

        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1

        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1

        if self.level_up_flash_timer > 0:
            self.level_up_flash_timer -= 1

        # --- Apply knockback ---
        if abs(self.knockback_vx) > 0.5 or abs(self.knockback_vy) > 0.5:
            new_x = self._x + self.knockback_vx
            if self._corners_clear(new_x, self._y, tilemap):
                self._x = new_x
            else:
                self.knockback_vx = 0.0
            new_y = self._y + self.knockback_vy
            if self._corners_clear(self._x, new_y, tilemap):
                self._y = new_y
            else:
                self.knockback_vy = 0.0
            self.knockback_vx *= PLAYER_KNOCKBACK_FRICTION
            self.knockback_vy *= PLAYER_KNOCKBACK_FRICTION

    def try_attack(self):
        """
        Begin an attack swing if the cooldown has expired.
        Sets is_attacking = True for PLAYER_ATTACK_DURATION frames.
        """
        if self.attack_cooldown_timer == 0:
            self.is_attacking          = True
            self.attack_timer          = PLAYER_ATTACK_DURATION
            self.attack_cooldown_timer = PLAYER_ATTACK_COOLDOWN
            try:
                import sounds
                sounds.play_swing()
            except Exception:
                pass

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
            try:
                import sounds
                sounds.play_hit_player()
            except Exception:
                pass

    def apply_knockback(self, from_x: float, from_y: float):
        """Apply knockback away from (from_x, from_y)."""
        dx = self.rect.centerx - from_x
        dy = self.rect.centery - from_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            dx, dy = 0.0, 1.0
            dist = 1.0
        self.knockback_vx = (dx / dist) * PLAYER_KNOCKBACK_FORCE
        self.knockback_vy = (dy / dist) * PLAYER_KNOCKBACK_FORCE

    def add_xp(self, amount: int):
        """Add XP and level up if threshold crossed (may chain-level)."""
        self.xp += amount
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self._level_up()

    def _level_up(self):
        """Apply stat increases for reaching the next level."""
        self.level += 1
        bonus_hp = PLAYER_HP_PER_LEVEL
        self.max_hp += bonus_hp
        self.hp = min(self.hp + bonus_hp, self.max_hp)
        self.attack_damage += PLAYER_ATTACK_PER_LEVEL
        self.xp_to_next_level = int(
            PLAYER_BASE_XP_PER_LEVEL * (PLAYER_XP_SCALE ** (self.level - 1))
        )
        self.level_up_flash_timer = LEVEL_UP_FLASH_DURATION
        try:
            import sounds
            sounds.play_level_up()
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def handle_input(self, keys, tilemap):
        """
        Read WASD / arrow keys and move the player if the destination is clear.
        Space / F triggers an attack.

        Also ticks timers and applies knockback — call once per frame.
        """
        self.update_timers(tilemap)

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

        if keys[pygame.K_SPACE] or keys[pygame.K_f]:
            self.try_attack()

    def draw(self, surface: pygame.Surface, camera):
        """
        Draw the player rectangle, directional arrow, attack hitbox,
        and level-up glow ring.

        Args:
            surface: The pygame surface to draw onto.
            camera:  Camera instance — used to convert world → screen coords.
        """
        # --- Invincibility flash ---
        if self.invincibility_timer > 0 and self.invincibility_timer % 6 < 3:
            return  # skip drawing this frame (flash effect)

        screen_rect = camera.apply(self.rect)

        # --- Attack hitbox preview ---
        if self.is_attacking:
            atk_world_rect  = self.get_attack_rect()
            atk_screen_rect = camera.apply(atk_world_rect)
            atk_surf = pygame.Surface(
                (atk_screen_rect.width, atk_screen_rect.height),
                pygame.SRCALPHA,
            )
            atk_surf.fill(_ATTACK_HITBOX_COLOR)
            surface.blit(atk_surf, (atk_screen_rect.x, atk_screen_rect.y))

        # Main body
        pygame.draw.rect(surface, PLAYER_COLOR, screen_rect)

        # Directional arrow
        self._draw_arrow(surface, screen_rect)

        # --- Level-up glow ring ---
        if self.level_up_flash_timer > 0:
            glow_rect = screen_rect.inflate(8, 8)
            alpha = min(255, self.level_up_flash_timer * 4)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*HUD_LEVEL_UP_COLOR, alpha), glow_surf.get_rect(), 3)
            surface.blit(glow_surf, (glow_rect.x, glow_rect.y))

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
