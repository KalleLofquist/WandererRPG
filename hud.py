# hud.py — Draws the HUD (health bar, XP bar, level, quest tracker) in screen space.

import pygame
from settings import (
    HUD_HP_BAR_COLOR, HUD_HP_BAR_BG_COLOR, HUD_HP_TEXT_COLOR, WHITE,
    HUD_XP_BAR_COLOR, HUD_XP_BAR_BG_COLOR, HUD_LEVEL_UP_COLOR,
    HUD_X, HUD_Y, HUD_BAR_WIDTH, HUD_BAR_HEIGHT,
    HUD_LABEL_GAP, HUD_XP_HEIGHT, HUD_XP_GAP, HUD_QUEST_GAP,
)

# --- Module-level font cache ---
_font: pygame.font.Font | None      = None
_font_small: pygame.font.Font | None = None


def _get_fonts():
    """Return (main_font, small_font), creating them on first call."""
    global _font, _font_small
    if _font is None:
        _font       = pygame.font.SysFont('arial', 16)
        _font_small = pygame.font.SysFont('arial', 14)
    return _font, _font_small


def draw_hud(surface: pygame.Surface, player, quest=None) -> None:
    """
    Render the player's health bar, XP bar, level label, and quest tracker
    in the top-left corner of the screen.

    Args:
        surface: The pygame display surface (screen-space drawing).
        player:  Player instance — must expose .hp, .max_hp, .level,
                 .xp, .xp_to_next_level.
        quest:   Optional DungeonClearQuest instance for quest tracker.
    """
    font, font_small = _get_fonts()

    # --- "Lv.X" label ---
    label_surf = font.render(f"Lv.{player.level}", True, HUD_HP_TEXT_COLOR)
    label_rect = label_surf.get_rect(midleft=(HUD_X, HUD_Y + HUD_BAR_HEIGHT // 2))
    surface.blit(label_surf, label_rect)

    # Bar starts to the right of the label
    bar_x = label_rect.right + HUD_LABEL_GAP
    bar_y = HUD_Y

    # --- HP bar background ---
    bg_rect = pygame.Rect(bar_x, bar_y, HUD_BAR_WIDTH, HUD_BAR_HEIGHT)
    pygame.draw.rect(surface, HUD_HP_BAR_BG_COLOR, bg_rect)

    # --- HP fill ---
    hp_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0.0
    fill_w   = max(0, int(HUD_BAR_WIDTH * hp_ratio))
    if fill_w > 0:
        fill_rect = pygame.Rect(bar_x, bar_y, fill_w, HUD_BAR_HEIGHT)
        pygame.draw.rect(surface, HUD_HP_BAR_COLOR, fill_rect)

    # --- 1px border ---
    pygame.draw.rect(surface, WHITE, bg_rect, 1)

    # --- "current / max" text centred on the bar ---
    hp_text   = f"{player.hp} / {player.max_hp}"
    text_surf = font.render(hp_text, True, HUD_HP_TEXT_COLOR)
    text_rect = text_surf.get_rect(center=bg_rect.center)
    surface.blit(text_surf, text_rect)

    # --- XP bar ---
    xp_y = bar_y + HUD_BAR_HEIGHT + HUD_XP_GAP
    xp_bg_rect = pygame.Rect(bar_x, xp_y, HUD_BAR_WIDTH, HUD_XP_HEIGHT)
    pygame.draw.rect(surface, HUD_XP_BAR_BG_COLOR, xp_bg_rect)

    xp_ratio = player.xp / player.xp_to_next_level if player.xp_to_next_level > 0 else 0.0
    xp_fill_w = max(0, int(HUD_BAR_WIDTH * xp_ratio))
    if xp_fill_w > 0:
        xp_fill_rect = pygame.Rect(bar_x, xp_y, xp_fill_w, HUD_XP_HEIGHT)
        pygame.draw.rect(surface, HUD_XP_BAR_COLOR, xp_fill_rect)

    pygame.draw.rect(surface, WHITE, xp_bg_rect, 1)

    # --- Quest tracker ---
    if quest is not None:
        desc = quest.description
        if desc:
            quest_y = xp_y + HUD_XP_HEIGHT + HUD_QUEST_GAP
            color   = HUD_LEVEL_UP_COLOR if quest.is_complete else WHITE
            q_surf  = font_small.render(desc, True, color)
            surface.blit(q_surf, (HUD_X, quest_y))
