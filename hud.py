# hud.py — Draws the HUD (health bar) in screen space.

import pygame
from settings import (
    HUD_HP_BAR_COLOR, HUD_HP_BAR_BG_COLOR, HUD_HP_TEXT_COLOR, WHITE,
)

# --- Module-level font cache ---
# Created once on first draw_hud() call; avoids re-initialising every frame.
_font: pygame.font.Font | None = None

# HUD layout constants
_HUD_X       = 12    # left edge of the HP label
_HUD_Y       = 12    # top edge of the HP row
_BAR_WIDTH   = 150   # pixel width of the health bar
_BAR_HEIGHT  = 18    # pixel height of the health bar
_LABEL_GAP   = 6     # gap between "HP" label and the bar


def _get_font() -> pygame.font.Font:
    """Return the cached HUD font, creating it on first call."""
    global _font
    if _font is None:
        _font = pygame.font.SysFont('arial', 16)
    return _font


def draw_hud(surface: pygame.Surface, player) -> None:
    """
    Render the player's health bar in the top-left corner of the screen.

    Layout (left → right):
      "HP" label | [===health bar===] "75 / 100"

    Args:
        surface: The pygame display surface (screen-space drawing).
        player:  Player instance — must expose .hp and .max_hp.
    """
    font = _get_font()

    # --- "HP" label ---
    label_surf = font.render("HP", True, HUD_HP_TEXT_COLOR)
    label_rect = label_surf.get_rect(midleft=(_HUD_X, _HUD_Y + _BAR_HEIGHT // 2))
    surface.blit(label_surf, label_rect)

    # Bar starts to the right of the label
    bar_x = label_rect.right + _LABEL_GAP
    bar_y = _HUD_Y

    # --- Background rect ---
    bg_rect = pygame.Rect(bar_x, bar_y, _BAR_WIDTH, _BAR_HEIGHT)
    pygame.draw.rect(surface, HUD_HP_BAR_BG_COLOR, bg_rect)

    # --- HP fill rect ---
    hp_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0.0
    fill_w   = max(0, int(_BAR_WIDTH * hp_ratio))
    if fill_w > 0:
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, _BAR_HEIGHT)
        pygame.draw.rect(surface, HUD_HP_BAR_COLOR, fill_rect)

    # --- 1px border around the bar ---
    pygame.draw.rect(surface, WHITE, bg_rect, 1)

    # --- "current / max" text, centred on the bar ---
    hp_text  = f"{player.hp} / {player.max_hp}"
    text_surf = font.render(hp_text, True, HUD_HP_TEXT_COLOR)
    text_rect = text_surf.get_rect(center=bg_rect.center)
    surface.blit(text_surf, text_rect)
