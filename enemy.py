# enemy.py — Enemy entity with patrol/chase AI and combat.

import math
import pygame
from settings import (
    TILE_SIZE, PLAYER_SIZE,
    ENEMY_MAX_HP, ENEMY_SPEED,
    ENEMY_DETECT_RADIUS, ENEMY_LOSE_RADIUS,
    ENEMY_ATTACK_RANGE, ENEMY_ATTACK_COOLDOWN,
    ENEMY_COLOR, ENEMY_HIT_COLOR,
    HUD_HP_BAR_BG_COLOR, WHITE,
)

# Enemy size matches the player for consistent collision feel
ENEMY_SIZE = PLAYER_SIZE

# Arrow indicator color (darker red)
_ENEMY_ARROW_COLOR = tuple(max(0, c - 50) for c in ENEMY_COLOR)

# State constants
STATE_PATROL = 'patrol'
STATE_CHASE  = 'chase'


class Enemy:
    """
    An enemy character with two-state AI:

    PATROL — walks back and forth between two waypoints.
    CHASE  — pursues the player when they come within ENEMY_DETECT_RADIUS;
             gives up when distance exceeds ENEMY_LOSE_RADIUS.

    Collision uses the same four-corner tile-sampling as the Player.
    """

    # Direction constants (mirrors Player)
    RIGHT = 0
    DOWN  = 1
    LEFT  = 2
    UP    = 3

    def __init__(
        self,
        x: float,
        y: float,
        patrol_start: tuple,
        patrol_end: tuple,
    ):
        """
        Args:
            x, y:          World-pixel spawn position (top-left of bounding box).
            patrol_start:  (tile_col, tile_row) of the first patrol waypoint.
            patrol_end:    (tile_col, tile_row) of the second patrol waypoint.
        """
        self._x: float = float(x)
        self._y: float = float(y)
        self._direction: int = self.DOWN

        # Convert tile waypoints to pixel centres so we move toward a point
        # in the middle of the tile, not its top-left corner.
        self._waypoints = [
            (patrol_start[0] * TILE_SIZE + TILE_SIZE // 2 - ENEMY_SIZE // 2,
             patrol_start[1] * TILE_SIZE + TILE_SIZE // 2 - ENEMY_SIZE // 2),
            (patrol_end[0]   * TILE_SIZE + TILE_SIZE // 2 - ENEMY_SIZE // 2,
             patrol_end[1]   * TILE_SIZE + TILE_SIZE // 2 - ENEMY_SIZE // 2),
        ]
        self._waypoint_index: int = 0   # which waypoint we're heading to

        # State machine
        self.state: str = STATE_PATROL

        # Combat
        self.hp: int               = ENEMY_MAX_HP
        self.max_hp: int           = ENEMY_MAX_HP
        self.attack_cooldown_timer: int = 0
        self._hit_flash_timer: int = 0  # counts down for the white-flash effect

    # ------------------------------------------------------------------ #
    #  Properties                                                          #
    # ------------------------------------------------------------------ #

    @property
    def rect(self) -> pygame.Rect:
        """Current bounding box in world-pixel space."""
        return pygame.Rect(int(self._x), int(self._y), ENEMY_SIZE, ENEMY_SIZE)

    @property
    def is_dead(self) -> bool:
        """True when HP reaches zero."""
        return self.hp <= 0

    # ------------------------------------------------------------------ #
    #  Private helpers                                                     #
    # ------------------------------------------------------------------ #

    def _corners_clear(self, px: float, py: float, tilemap) -> bool:
        """Return True if all four corners of the enemy bbox at (px, py) are floor."""
        corners = [
            (px,                       py),
            (px + ENEMY_SIZE - 1,      py),
            (px,                       py + ENEMY_SIZE - 1),
            (px + ENEMY_SIZE - 1,      py + ENEMY_SIZE - 1),
        ]
        for cx, cy in corners:
            tile_x = int(cx) // TILE_SIZE
            tile_y = int(cy) // TILE_SIZE
            if tilemap.is_wall(tile_x, tile_y):
                return False
        return True

    def _move_toward(self, target_x: float, target_y: float, tilemap) -> bool:
        """
        Move one step toward (target_x, target_y) at ENEMY_SPEED.

        Returns True if any movement occurred (used by patrol to detect being
        stuck so it can switch waypoints).
        """
        dx = target_x - self._x
        dy = target_y - self._y
        dist = math.hypot(dx, dy)

        if dist == 0:
            return False

        # Normalise and scale to ENEMY_SPEED
        step_x = (dx / dist) * ENEMY_SPEED
        step_y = (dy / dist) * ENEMY_SPEED

        moved = False

        # Try X axis
        new_x = self._x + step_x
        if self._corners_clear(new_x, self._y, tilemap):
            self._x = new_x
            moved = True

        # Try Y axis (independent — allows wall-sliding)
        new_y = self._y + step_y
        if self._corners_clear(self._x, new_y, tilemap):
            self._y = new_y
            moved = True

        # Update facing direction based on dominant movement axis
        if abs(step_x) >= abs(step_y):
            self._direction = self.RIGHT if step_x > 0 else self.LEFT
        else:
            self._direction = self.DOWN if step_y > 0 else self.UP

        return moved

    # ------------------------------------------------------------------ #
    #  Public API — update                                                 #
    # ------------------------------------------------------------------ #

    def update(self, player_rect: pygame.Rect, tilemap):
        """
        Run the AI state machine and tick timers.  Call once per frame.

        Args:
            player_rect: The player's current world-space bounding box.
            tilemap:     TileMap instance for wall queries.
        """
        # --- Timer ticks ---
        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= 1
        if self._hit_flash_timer > 0:
            self._hit_flash_timer -= 1

        # --- Distance to player ---
        px = player_rect.centerx
        py = player_rect.centery
        ex = self._x + ENEMY_SIZE / 2
        ey = self._y + ENEMY_SIZE / 2
        dist = math.hypot(px - ex, py - ey)

        # --- State transitions ---
        if self.state == STATE_PATROL and dist <= ENEMY_DETECT_RADIUS:
            self.state = STATE_CHASE
        elif self.state == STATE_CHASE and dist > ENEMY_LOSE_RADIUS:
            self.state = STATE_PATROL

        # --- Behaviour ---
        if self.state == STATE_PATROL:
            self._do_patrol(tilemap)
        else:
            self._do_chase(player_rect, tilemap)

    def _do_patrol(self, tilemap):
        """Walk toward the current waypoint; switch when close enough or stuck."""
        wp_x, wp_y = self._waypoints[self._waypoint_index]
        dx = wp_x - self._x
        dy = wp_y - self._y
        dist = math.hypot(dx, dy)

        # Arrived at waypoint (within 4 px) — switch target
        if dist < 4:
            self._waypoint_index = 1 - self._waypoint_index
            return

        moved = self._move_toward(wp_x, wp_y, tilemap)

        # If completely stuck (both axes blocked), switch waypoint to avoid deadlock
        if not moved:
            self._waypoint_index = 1 - self._waypoint_index

    def _do_chase(self, player_rect: pygame.Rect, tilemap):
        """Move toward the player's centre."""
        self._move_toward(
            float(player_rect.centerx - ENEMY_SIZE // 2),
            float(player_rect.centery - ENEMY_SIZE // 2),
            tilemap,
        )

    # ------------------------------------------------------------------ #
    #  Public API — combat                                                 #
    # ------------------------------------------------------------------ #

    def can_attack_player(self, player_rect: pygame.Rect) -> bool:
        """
        Return True if the enemy is in melee range and the cooldown has expired.
        The attack check inflates the enemy's rect by ENEMY_ATTACK_RANGE on all sides.
        """
        inflated = self.rect.inflate(ENEMY_ATTACK_RANGE * 2, ENEMY_ATTACK_RANGE * 2)
        return inflated.colliderect(player_rect) and self.attack_cooldown_timer == 0

    def do_attack(self):
        """Register an attack — resets the cooldown timer."""
        self.attack_cooldown_timer = ENEMY_ATTACK_COOLDOWN

    def take_damage(self, amount: int):
        """Reduce HP (floored at 0) and trigger the white-flash effect."""
        self.hp = max(0, self.hp - amount)
        self._hit_flash_timer = 8

    # ------------------------------------------------------------------ #
    #  Rendering                                                           #
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface, camera):
        """
        Draw the enemy body, optional HP bar, and facing arrow.

        Args:
            surface: The pygame surface to draw onto.
            camera:  Camera instance for world→screen transform.
        """
        screen_rect = camera.apply(self.rect)

        # Body color — flash white when recently hit
        color = ENEMY_HIT_COLOR if self._hit_flash_timer > 0 else ENEMY_COLOR
        pygame.draw.rect(surface, color, screen_rect)

        # HP bar — only visible when the enemy has taken damage
        if self.hp < self.max_hp:
            self._draw_hp_bar(surface, screen_rect)

        # Facing arrow
        self._draw_arrow(surface, screen_rect)

    def _draw_hp_bar(self, surface: pygame.Surface, screen_rect: pygame.Rect):
        """Draw a small HP bar 4px above the enemy rect."""
        bar_w = screen_rect.width
        bar_h = 4
        bar_x = screen_rect.x
        bar_y = screen_rect.y - bar_h - 2   # 2px gap above the enemy

        # Background
        bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, HUD_HP_BAR_BG_COLOR, bg_rect)

        # HP fill
        fill_w = max(0, int(bar_w * (self.hp / self.max_hp)))
        if fill_w > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_w, bar_h)
            pygame.draw.rect(surface, ENEMY_COLOR, fill_rect)

        # 1px border
        pygame.draw.rect(surface, WHITE, bg_rect, 1)

    def _draw_arrow(self, surface: pygame.Surface, screen_rect: pygame.Rect):
        """Draw a small directional triangle on the enemy body."""
        cx = screen_rect.centerx
        cy = screen_rect.centery
        r  = screen_rect
        tip_inset = 4
        side_half = 4

        if self._direction == self.RIGHT:
            points = [
                (r.right - tip_inset,   cy),
                (r.centerx - side_half, cy - side_half),
                (r.centerx - side_half, cy + side_half),
            ]
        elif self._direction == self.LEFT:
            points = [
                (r.left  + tip_inset,   cy),
                (r.centerx + side_half, cy - side_half),
                (r.centerx + side_half, cy + side_half),
            ]
        elif self._direction == self.UP:
            points = [
                (cx,                    r.top    + tip_inset),
                (cx - side_half,        r.centery + side_half),
                (cx + side_half,        r.centery + side_half),
            ]
        else:  # DOWN
            points = [
                (cx,                    r.bottom - tip_inset),
                (cx - side_half,        r.centery - side_half),
                (cx + side_half,        r.centery - side_half),
            ]

        pygame.draw.polygon(surface, _ENEMY_ARROW_COLOR, points)
