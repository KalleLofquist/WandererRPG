# combat.py — Resolves combat between player and enemies each frame.

from settings import MAP_ID_DUNGEON


def resolve_combat(player, enemies, quest=None, current_map_id=None):
    """
    Resolve all combat interactions for this frame.

    Args:
        player:         Player instance.
        enemies:        List of Enemy instances.
        quest:          Optional DungeonClearQuest instance.
        current_map_id: Current map ID string (for XP/quest routing).

    Returns:
        List of Enemy instances that died this frame.
    """
    newly_dead = []

    # --- Player attacking enemies ---
    if player.is_attacking:
        attack_rect = player.get_attack_rect()
        px = player.rect.centerx
        py = player.rect.centery
        for enemy in enemies:
            if attack_rect.colliderect(enemy.rect):
                enemy.take_damage(player.attack_damage)
                # Knockback: push enemy away from player centre
                enemy.apply_knockback(px, py)
                if enemy.is_dead and enemy not in newly_dead:
                    newly_dead.append(enemy)

    # --- Grant XP and notify quest for newly dead enemies ---
    for dead_enemy in newly_dead:
        xp = dead_enemy.xp_value
        player.add_xp(xp)
        if quest is not None and current_map_id == MAP_ID_DUNGEON:
            quest.on_enemy_killed()

    # --- Enemies attacking player ---
    for enemy in enemies:
        if enemy.can_attack_player(player.rect):
            enemy.do_attack()
            player.take_damage(enemy.damage)
            # Knockback: push player away from enemy centre
            player.apply_knockback(enemy.rect.centerx, enemy.rect.centery)

    return newly_dead
