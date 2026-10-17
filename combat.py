# combat.py — Resolves combat between player and enemies each frame.

from settings import MAP_ID_DUNGEON


def resolve_combat(player, enemies, camera, particle_manager, quest=None, current_map_id=None):
    """
    Resolve all combat interactions for this frame.

    Args:
        player:         Player instance.
        enemies:        List of Enemy instances.
        camera:         Camera instance (for shake).
        particle_manager: ParticleManager instance.
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
                # Only damage each enemy once per swing
                enemy_id = id(enemy)
                if enemy_id not in player._hit_this_swing:
                    player._hit_this_swing.add(enemy_id)
                    enemy.take_damage(player.attack_damage)
                    # Juice: Shake and particles on hit
                    camera.trigger_shake(4, 10)
                    particle_manager.emit(enemy.rect.centerx, enemy.rect.centery, (255, 255, 255), 5)
                    # Knockback: push enemy away from player centre
                    enemy.apply_knockback(px, py)
                    if enemy.is_dead and enemy not in newly_dead:
                        newly_dead.append(enemy)

    # --- Grant XP and notify quest for newly dead enemies ---
    for dead_enemy in newly_dead:
        xp = dead_enemy.xp_value
        player.add_xp(xp)
        # Juice: Burst on death
        particle_manager.emit(dead_enemy.rect.centerx, dead_enemy.rect.centery, (200, 50, 50), 20)
        if quest is not None and current_map_id == MAP_ID_DUNGEON:
            quest.on_enemy_killed()

    # --- Enemies attacking player ---
    for enemy in enemies:
        if not enemy.is_dead and enemy.can_attack_player(player.hitbox):
            enemy.do_attack()
            player.take_damage(enemy.damage)
            # Juice: Heavy shake on player damage
            camera.trigger_shake(8, 15)
            # Knockback: push player away from enemy centre
            player.apply_knockback(enemy.rect.centerx, enemy.rect.centery)

    return newly_dead
