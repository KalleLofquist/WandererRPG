# combat.py — Resolves combat between player and enemies each frame.

from typing import List
from settings import PLAYER_ATTACK_DAMAGE


def resolve_combat(player, enemies: List) -> List:
    """
    Check all attack interactions for this frame.

    Handles two cases:
    1. Player's active swing hitbox collides with enemies.
    2. Each enemy that is in melee range attacks the player.

    Args:
        player:  Player instance.
        enemies: List of all living Enemy instances.

    Returns:
        A list of Enemy instances that died this frame.
        The caller is responsible for removing them from the main list.
    """
    newly_dead: List = []

    # --- Player attacking enemies ---
    if player.is_attacking:
        attack_rect = player.get_attack_rect()
        for enemy in enemies:
            if attack_rect.colliderect(enemy.rect):
                enemy.take_damage(PLAYER_ATTACK_DAMAGE)
                # Guard against adding the same enemy twice (e.g. multi-frame
                # overlap on the first death frame isn't possible here, but be safe).
                if enemy.is_dead and enemy not in newly_dead:
                    newly_dead.append(enemy)

    # --- Enemies attacking player ---
    # Each enemy uses its own .damage attribute so dungeon enemies hit harder.
    for enemy in enemies:
        if enemy.can_attack_player(player.rect):
            enemy.do_attack()
            player.take_damage(enemy.damage)

    return newly_dead
