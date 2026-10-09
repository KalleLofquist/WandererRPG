# main.py — Entry point: game loop, map management, and system wiring.

import pygame
import sounds   # must be imported before pygame.init() to register pre_init call site

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    BLACK,
    MAP_ID_TOWN, MAP_ID_DUNGEON,
    DUNGEON_ENEMY_HP, DUNGEON_ENEMY_DAMAGE, DUNGEON_ENEMY_SPEED,
    DUNGEON_ENEMY_XP_VALUE,
    GAME_STATE_PLAYING, GAME_STATE_GAME_OVER,
)
from tilemap import (
    TileMap, TILE_FLOOR, TILE_WALL, TILE_EXIT,
    set_town_theme, set_dungeon_theme,
)
from camera  import Camera
from player  import Player
from enemy   import Enemy
from combat  import resolve_combat
from hud     import draw_hud
from maps    import build_town_map, build_dungeon_map
from npc     import NPC
from item    import HealthPotion
from quest   import DungeonClearQuest


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _item_from_spawn(tile_col: int, tile_row: int, item_type: str):
    """Construct the correct Item subclass from a spawn-data entry."""
    if item_type == 'health_potion':
        return HealthPotion(tile_col, tile_row)
    raise ValueError(f"Unknown item type: {item_type!r}")


def load_map(map_id: str, player: Player):
    """
    Build all world objects for *map_id*, reposition the player, switch music.

    The player's HP is intentionally preserved across transitions.

    Args:
        map_id: One of MAP_ID_TOWN or MAP_ID_DUNGEON.
        player: Existing Player instance — its position will be updated.

    Returns:
        (tilemap, enemies, npcs, items, camera, exit_tiles)
        where exit_tiles is a list of {'col', 'row', 'target'} dicts.
    """
    # ---- Fetch raw map data ------------------------------------------
    if map_id == MAP_ID_DUNGEON:
        data = build_dungeon_map()
        set_dungeon_theme()
        sounds.play_music_dungeon()
        # Dungeon-specific enemy stats
        e_hp     = DUNGEON_ENEMY_HP
        e_speed  = DUNGEON_ENEMY_SPEED
        e_damage = DUNGEON_ENEMY_DAMAGE
        e_xp     = DUNGEON_ENEMY_XP_VALUE
    else:
        data = build_town_map()
        set_town_theme()
        sounds.play_music_town()
        e_hp     = None   # use enemy defaults
        e_speed  = None
        e_damage = None
        e_xp     = None   # use default ENEMY_XP_VALUE

    # ---- TileMap -----------------------------------------------------
    tilemap = TileMap(data['grid'])

    # ---- Place player at spawn (preserve HP) -------------------------
    sx, sy = data['player_spawn']
    player._x = float(sx)
    player._y = float(sy)

    # ---- Enemies -----------------------------------------------------
    enemies = []
    for (ex, ey, ps, pe) in data['enemy_spawns']:
        enemies.append(Enemy(
            ex, ey,
            patrol_start=ps,
            patrol_end=pe,
            hp=e_hp,
            speed=e_speed,
            damage=e_damage,
            xp_value=e_xp,
        ))

    # ---- NPCs -------------------------------------------------------
    npcs = []
    for (col, row, name, lines) in data['npc_spawns']:
        npcs.append(NPC(col, row, name, lines))

    # ---- Items -------------------------------------------------------
    items = []
    for (col, row, itype) in data['item_spawns']:
        items.append(_item_from_spawn(col, row, itype))

    # ---- Camera ------------------------------------------------------
    camera = Camera(
        map_width_px  = data['map_width']  * TILE_SIZE,
        map_height_px = data['map_height'] * TILE_SIZE,
    )

    return tilemap, enemies, npcs, items, camera, data['exit_tiles']


def _wire_quest(npcs, quest):
    """Attach the quest to the Elder NPC (if present) in the given NPC list."""
    for npc in npcs:
        if npc.name == 'Elder':
            npc.set_quest(quest)


def do_fade(screen: pygame.Surface, clock: pygame.time.Clock,
            fade_in: bool = True, duration_frames: int = 30) -> None:
    """
    Blocking screen-transition fade.

    fade_in=False : alpha  0 → 255  (fades to black)
    fade_in=True  : alpha 255 → 0   (reveals the snapshot)
    """
    black    = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    black.fill(BLACK)
    snapshot = screen.copy()

    for i in range(duration_frames + 1):
        if fade_in:
            alpha = int(255 * (1.0 - i / duration_frames))
        else:
            alpha = int(255 * (i / duration_frames))
        alpha = max(0, min(255, alpha))

        screen.blit(snapshot, (0, 0))
        black.set_alpha(alpha)
        screen.blit(black, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit


def _render_world(screen, tilemap, items, enemies, npcs, player, camera,
                  hud_player, frame_counter, quest=None):
    """
    Draw a single complete frame: tilemap → items → enemies → NPCs → player → HUD.
    Does NOT call pygame.display.flip().
    """
    screen.fill(BLACK)
    tilemap.draw(screen, camera.offset)

    for item in items:
        item.draw(screen, camera, frame_counter)

    for enemy in enemies:
        enemy.draw(screen, camera)

    for npc in npcs:
        npc.draw(screen, camera)

    hud_player.draw(screen, camera)
    draw_hud(screen, hud_player, quest=quest)


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

def main():
    # Pre-initialise the mixer BEFORE pygame.init()
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    sounds.init()   # generate all procedural audio assets

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock  = pygame.time.Clock()

    # ---- Initial world setup ----------------------------------------
    game_state     = GAME_STATE_PLAYING
    current_map_id = MAP_ID_TOWN
    quest          = DungeonClearQuest()

    # Create player at a temporary position; load_map will set the real spawn.
    player = Player(0, 0)

    tilemap, enemies, npcs, items, camera, exit_tiles = load_map(current_map_id, player)
    camera.update(player.rect)   # prime the camera
    _wire_quest(npcs, quest)

    # ---- State variables --------------------------------------------
    frame_counter       = 0
    transition_cooldown = 0   # prevents re-triggering an exit tile on arrival
    running             = True

    # ---------------------------------------------------------------- #
    #  Main loop                                                         #
    # ---------------------------------------------------------------- #
    while running:

        # ---- Events -------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    running = False

                # --- Restart from game-over screen ---
                elif event.key == pygame.K_r and game_state == GAME_STATE_GAME_OVER:
                    game_state     = GAME_STATE_PLAYING
                    quest          = DungeonClearQuest()
                    player         = Player(0, 0)
                    current_map_id = MAP_ID_TOWN
                    tilemap, enemies, npcs, items, camera, exit_tiles = \
                        load_map(current_map_id, player)
                    camera.update(player.rect)
                    transition_cooldown = 0
                    _wire_quest(npcs, quest)
                    do_fade(screen, clock, fade_in=True, duration_frames=20)

                # Only process gameplay keys when playing
                elif game_state == GAME_STATE_PLAYING:

                    # Single-press attack
                    if event.key in (pygame.K_SPACE, pygame.K_f):
                        player.try_attack()

                    # NPC interaction — E key
                    elif event.key == pygame.K_e:
                        for npc in npcs:
                            if npc.is_talking:
                                npc.interact(player=player)   # advance or close
                                break
                            elif npc.is_in_range(player.rect):
                                npc.interact(player=player)   # start dialogue
                                break

                    # Close dialogue — Q key
                    elif event.key == pygame.K_q:
                        for npc in npcs:
                            if npc.is_talking:
                                npc.close_dialogue()
                                break

        # ---- Update (only when playing) ----------------------------
        if game_state == GAME_STATE_PLAYING:
            keys = pygame.key.get_pressed()
            player.handle_input(keys, tilemap)
            camera.update(player.rect)

            # NPC proximity check (drives "!" indicator)
            for npc in npcs:
                npc.update(player.rect)

            # Enemies
            for enemy in enemies:
                enemy.update(player.rect, tilemap)

            # Combat — pass quest and map ID for XP/quest routing
            dead_enemies = resolve_combat(
                player, enemies,
                quest=quest, current_map_id=current_map_id,
            )
            for dead in dead_enemies:
                if dead in enemies:
                    enemies.remove(dead)

            # Item pickup
            for item in list(items):
                if player.rect.colliderect(item.rect):
                    if item.on_pickup(player):
                        items.remove(item)

            # Player death → game over
            if player.is_dead:
                game_state = GAME_STATE_GAME_OVER

            # ---- Map transition check --------------------------------
            if transition_cooldown > 0:
                transition_cooldown -= 1
            else:
                centre_col = player.rect.centerx // TILE_SIZE
                centre_row = player.rect.centery // TILE_SIZE
                triggered_exit = None
                for ex in exit_tiles:
                    if ex['col'] == centre_col and ex['row'] == centre_row:
                        triggered_exit = ex
                        break

                if triggered_exit is not None:
                    # 1. Render last frame of old map and fade to black
                    _render_world(screen, tilemap, items, enemies, npcs,
                                  player, camera, player, frame_counter, quest=quest)
                    pygame.display.flip()
                    do_fade(screen, clock, fade_in=False, duration_frames=30)

                    # 2. Load new map (repositions player, switches music)
                    current_map_id = triggered_exit['target']
                    tilemap, enemies, npcs, items, camera, exit_tiles = \
                        load_map(current_map_id, player)
                    camera.update(player.rect)

                    # Re-wire quest to Elder NPC on every map load
                    _wire_quest(npcs, quest)

                    # 3. Render first frame of new map so fade_in has something to reveal
                    _render_world(screen, tilemap, items, enemies, npcs,
                                  player, camera, player, frame_counter, quest=quest)
                    pygame.display.flip()

                    # 4. Fade from black to the new map
                    do_fade(screen, clock, fade_in=True, duration_frames=30)

                    transition_cooldown = 90   # ~1.5 s at 60 FPS

        # ---- Draw ---------------------------------------------------
        _render_world(screen, tilemap, items, enemies, npcs,
                      player, camera, player, frame_counter, quest=quest)

        # Dialogue boxes rendered on top of everything else (screen space)
        for npc in npcs:
            if npc.is_talking:
                npc.draw_dialogue(screen)
                break   # only one dialogue box at a time

        # ---- Game Over overlay (drawn over everything) ---------------
        if game_state == GAME_STATE_GAME_OVER:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((80, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            font_big   = pygame.font.SysFont('arial', 64, bold=True)
            font_small = pygame.font.SysFont('arial', 24)

            title = font_big.render('YOU DIED', True, (220, 50, 50))
            hint  = font_small.render('[ R ] Restart   |   [ ESC ] Quit', True, (200, 200, 200))

            screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40)))
            screen.blit(hint,  hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40)))

        pygame.display.flip()

        # ---- Timing -------------------------------------------------
        clock.tick(FPS)
        frame_counter += 1

        fps = clock.get_fps()
        pygame.display.set_caption(
            f"WandererRPG — {current_map_id.title()} — FPS: {fps:.0f}"
        )

    pygame.quit()


if __name__ == "__main__":
    main()
