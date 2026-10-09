# npc.py — NPC entity with proximity interaction and multi-line dialogue.

import math
import pygame
from settings import (
    TILE_SIZE, PLAYER_SIZE,
    NPC_COLOR, NPC_INDICATOR_COLOR, NPC_INTERACT_RADIUS,
    NPC_PANEL_WIDTH, NPC_PANEL_HEIGHT, NPC_PANEL_PADDING,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    DIALOGUE_BG_COLOR, DIALOGUE_TEXT_COLOR, DIALOGUE_BORDER_COLOR,
)
from quest import STATE_INACTIVE, STATE_ACTIVE, STATE_COMPLETE, STATE_REWARDED

# ---- Module-level font cache (created lazily on first use) ------------
_font_name = None   # size-18 for NPC name
_font_body = None   # size-16 for dialogue lines
_font_hint = None   # size-14 for the hint text
_npc_indicator_surf = None
_npc_border_color = tuple(max(0, c - 40) for c in NPC_COLOR)

def _get_fonts():
    global _font_name, _font_body, _font_hint, _npc_indicator_surf
    if _font_name is None:
        _font_name = pygame.font.SysFont('arial', 18, bold=True)
        _font_body = pygame.font.SysFont('arial', 16)
        _font_hint = pygame.font.SysFont('arial', 14)
        # Render the indicator "!" once and cache it
        _npc_indicator_surf = _font_name.render('!', True, NPC_INDICATOR_COLOR)
    return _font_name, _font_body, _font_hint


def _wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list:
    """
    Split *text* into a list of lines that each fit within *max_width* pixels.
    """
    words  = text.split(' ')
    lines  = []
    current = ''
    for word in words:
        candidate = f'{current} {word}' if current else word
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---- Dialogue panel layout constants -----------------------------------
_PANEL_HEIGHT  = NPC_PANEL_HEIGHT
_PANEL_Y       = SCREEN_HEIGHT - _PANEL_HEIGHT - 10
_PANEL_PADDING = NPC_PANEL_PADDING
_PANEL_WIDTH   = NPC_PANEL_WIDTH

# ---- Pre-allocated dialogue panel surface ---
_panel_surf = pygame.Surface((_PANEL_WIDTH, _PANEL_HEIGHT), pygame.SRCALPHA)


class NPC:
    """
    A non-player character that the player can talk to.

    Renders as a green square on the map.  When the player walks within
    NPC_INTERACT_RADIUS pixels a yellow "!" floats above the NPC.
    Pressing E starts / advances / closes the dialogue.
    """

    def __init__(self, tile_col: int, tile_row: int, name: str, dialogue_lines: list):
        """
        Args:
            tile_col:       Tile column of the NPC's top-left corner.
            tile_row:       Tile row of the NPC's top-left corner.
            name:           Display name shown at the top of the dialogue box.
            dialogue_lines: List of strings — each string is one dialogue page.
        """
        # Place the NPC centred on its tile
        self._x = tile_col * TILE_SIZE + (TILE_SIZE - PLAYER_SIZE) // 2
        self._y = tile_row * TILE_SIZE + (TILE_SIZE - PLAYER_SIZE) // 2
        self.name           = name
        self._dialogue_lines = dialogue_lines

        self._line_index    = 0
        self.is_talking     = False
        self._show_indicator = False   # updated every frame by update()

    # ------------------------------------------------------------------ #
    #  Properties                                                          #
    # ------------------------------------------------------------------ #

    @property
    def rect(self) -> pygame.Rect:
        """World-space bounding box (same size as the player)."""
        return pygame.Rect(int(self._x), int(self._y), PLAYER_SIZE, PLAYER_SIZE)

    @property
    def current_line(self) -> str:
        """The dialogue string currently being displayed."""
        if not self._dialogue_lines:
            return ''
        return self._dialogue_lines[self._line_index]

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def set_quest(self, quest) -> None:
        """Wire a DungeonClearQuest to this NPC so dialogue adapts to quest state."""
        self._quest = quest

    def _get_dynamic_lines(self) -> list:
        """Return the appropriate dialogue list based on current quest state."""
        q = getattr(self, '_quest', None)
        if q is None or q.state == STATE_INACTIVE:
            return [
                "Welcome, wanderer. These lands grow dangerous.",
                "Dark creatures stir beneath the old keep to the south.",
                "Slay 4 of the beasts and return to me. I shall reward your bravery.",
            ]
        elif q.state == STATE_ACTIVE:
            return [
                f"How goes the hunt? You have slain {q.kills_current} of {q.kills_needed}.",
                "The entrance is through the southern passage. Stay sharp.",
            ]
        elif q.state == STATE_COMPLETE:
            return [
                "You've done it! The dungeon is cleared of its foul inhabitants.",
                "Take this reward — you have earned it.",
            ]
        elif q.state == STATE_REWARDED:
            return [
                "Well done, wanderer. The keep is safer for your courage.",
                "Rest here a while if you need. You are always welcome.",
            ]
        return ["..."]

    def is_in_range(self, player_rect: pygame.Rect) -> bool:
        """Return True if the player's centre is within NPC_INTERACT_RADIUS."""
        dx = self.rect.centerx - player_rect.centerx
        dy = self.rect.centery - player_rect.centery
        return math.hypot(dx, dy) <= NPC_INTERACT_RADIUS

    def update(self, player_rect: pygame.Rect) -> None:
        """Refresh indicator visibility — call once per frame."""
        self._show_indicator = self.is_in_range(player_rect)

    def interact(self, player=None) -> None:
        """
        Called when the player presses E near this NPC.

        First call  : opens the dialogue at line 0 (rebuilds lines from quest state).
        Subsequent  : advances to the next line.
        After last  : closes; triggers quest accept or reward as appropriate.

        Args:
            player: Player instance — required to grant the quest reward.
        """
        try:
            import sounds
            sounds.play_dialogue()
        except Exception:
            pass

        q = getattr(self, '_quest', None)

        if not self.is_talking:
            # Opening conversation: rebuild lines based on current quest state
            self._dialogue_lines = self._get_dynamic_lines()
            self.is_talking  = True
            self._line_index = 0
        else:
            self._line_index += 1
            if self._line_index >= len(self._dialogue_lines):
                self._line_index = 0
                self.is_talking  = False
                # Accept quest when closing the first (inactive) conversation
                if q is not None and q.state == STATE_INACTIVE:
                    q.accept()
                # Collect reward when closing the 'complete' conversation
                elif q is not None and q.state == STATE_COMPLETE and player is not None:
                    q.collect_reward(player)

    def close_dialogue(self) -> None:
        """Close the dialogue box immediately (Q key)."""
        self.is_talking = False

    # ------------------------------------------------------------------ #
    #  Rendering                                                           #
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface, camera) -> None:
        """
        Draw the NPC body and — if the player is close — a floating "!" above it.

        Args:
            surface: Display surface.
            camera:  Camera instance for world→screen transform.
        """
        screen_rect = camera.apply(self.rect)
        pygame.draw.rect(surface, NPC_COLOR, screen_rect)

        # Small darker outline for readability
        pygame.draw.rect(surface, _npc_border_color, screen_rect, 1)

        # Floating "!" indicator when player is close
        if self._show_indicator:
            _get_fonts()  # ensure fonts and indicator are initialized
            ix = screen_rect.centerx - _npc_indicator_surf.get_width() // 2
            iy = screen_rect.top - _npc_indicator_surf.get_height() - 4
            surface.blit(_npc_indicator_surf, (ix, iy))

    def draw_dialogue(self, surface: pygame.Surface) -> None:
        """
        Draw the dialogue panel in screen space (always on top of everything).

        Layout (bottom of screen):
          ┌──────────────────────────────────────────┐  ← border line
          │  NPC Name (bold)                          │
          │  Dialogue text (word-wrapped)             │
          │                      [ E ] Next | [ Q ] Close │
          └──────────────────────────────────────────┘

        Args:
            surface: The display surface (screen space).
        """
        if not self.is_talking:
            return

        fn, fb, fh = _get_fonts()

        # ---- Semi-transparent background panel --------------------------
        panel_rect = pygame.Rect(
            _PANEL_PADDING, _PANEL_Y,
            _PANEL_WIDTH,   _PANEL_HEIGHT,
        )

        # Reuse the pre-allocated surface
        _panel_surf.fill(DIALOGUE_BG_COLOR)        # RGBA — uses the alpha channel
        surface.blit(_panel_surf, (panel_rect.x, panel_rect.y))

        # Top border line
        pygame.draw.line(
            surface, DIALOGUE_BORDER_COLOR,
            (panel_rect.left,  panel_rect.top),
            (panel_rect.right, panel_rect.top),
            2,
        )
        # Full rectangle border (1 px, drawn after blit so it's opaque)
        pygame.draw.rect(surface, DIALOGUE_BORDER_COLOR, panel_rect, 1)

        # ---- NPC name ---------------------------------------------------
        tx = panel_rect.x + 8
        ty = panel_rect.y + 8
        name_surf = fn.render(self.name, True, DIALOGUE_TEXT_COLOR)
        surface.blit(name_surf, (tx, ty))
        ty += name_surf.get_height() + 4

        # ---- Dialogue body (word-wrapped) --------------------------------
        max_text_w = _PANEL_WIDTH - 16
        lines = _wrap_text(self.current_line, fb, max_text_w)
        for line in lines:
            line_surf = fb.render(line, True, DIALOGUE_TEXT_COLOR)
            surface.blit(line_surf, (tx, ty))
            ty += line_surf.get_height() + 2

        # ---- Hint text (bottom-right) ------------------------------------
        # Work out whether this is the last line so we show "Close" vs "Next"
        if self._line_index >= len(self._dialogue_lines) - 1:
            hint = '[ E ] Close  |  [ Q ] Close'
        else:
            hint = '[ E ] Next  |  [ Q ] Close'
        hint_surf = fh.render(hint, True, DIALOGUE_BORDER_COLOR)
        hx = panel_rect.right  - hint_surf.get_width()  - 8
        hy = panel_rect.bottom - hint_surf.get_height() - 6
        surface.blit(hint_surf, (hx, hy))
