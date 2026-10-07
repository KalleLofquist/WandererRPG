# main.py — Entry point: game loop, map management, and system wiring.

import pygame
import sounds   # must be imported before pygame.init() to register pre_init call site

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    BLACK,
    MAP_ID_TOWN, MAP_ID_DUNGEON,
    DUNGEON_ENEMY_HP, DUNGEON_ENEMY_DAMAGE, DUNGEON_ENEMY_SPEED,
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
    else:
        data = build_town_map()
        set_town_theme()
        sounds.play_music_town()
        e_hp     = None   # use enemy defaults
        e_speed  = None
        e_damage = None

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


def do_fade(screen: pygame.Surface, clock: pygame.time.Clock,
            fade_in: bool = True, duration_frames: int = 30) -> None:
    """
    Blocking screen-transition fade.

    Captures what is currently on *screen*, then overlays a black surface
    whose alpha changes over *duration_frames* frames.

    fade_in=False : alpha  0 → 255  (fades to black)
    fade_in=True  : alpha 255 → 0   (reveals the snapshot)

    Callers should ensure that the desired end-state image is already
    rendered to *screen* before calling with fade_in=True.

    Args:
        screen:          The pygame display surface.
        clock:           The game clock (used for frame-rate limiting).
        fade_in:         Direction of the fade.
        duration_frames: How many frames the transition lasts.
    """
    black    = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    black.fill(BLACK)
    snapshot = screen.copy()   # preserve whatever was rendered before the call

    for i in range(duration_frames + 1):
        if fade_in:
            alpha = int(255 * (1.0 - i / duration_frames))
        else:
            alpha = int(255 * (i / duration_frames))
        alpha = max(0, min(255, alpha))

        # Restore snapshot, then overlay the semi-opaque black
        screen.blit(snapshot, (0, 0))
        black.set_alpha(alpha)
        screen.blit(black, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

        # Process minimal events during the fade so the OS doesn't think
        # the window has frozen
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit


def _render_world(screen, tilemap, items, enemies, npcs, player, camera,
                  hud_player, frame_counter):
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
    draw_hud(screen, hud_player)


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

def main():
    # Pre-initialise the mixer BEFORE pygame.init() so our sample-rate /
    # bit-depth / channel settings are respected by the driver.
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    sounds.init()   # generate all procedural audio assets

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock  = pygame.time.Clock()

    # ---- Initial world setup ----------------------------------------
    current_map_id = MAP_ID_TOWN

    # Create player at a temporary position; load_map will set the real spawn.
    player = Player(0, 0)

    tilemap, enemies, npcs, items, camera, exit_tiles = load_map(current_map_id, player)
    camera.update(player.rect)   # prime the camera

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

                # Single-press attack
                elif event.key in (pygame.K_SPACE, pygame.K_f):
                    player.try_attack()

                # NPC interaction — E key
                elif event.key == pygame.K_e:
                    # Find the nearest in-range NPC that is either already
                    # talking (advance) or ready to start
                    for npc in npcs:
                        if npc.is_talking:
                            npc.interact()   # advance or close
                            break
                        elif npc.is_in_range(player.rect):
                            npc.interact()   # start dialogue
                            break

                # Close dialogue — Q key
                elif event.key == pygame.K_q:
                    for npc in npcs:
                        if npc.is_talking:
                            npc.close_dialogue()
                            break

        # ---- Update -------------------------------------------------
        keys = pygame.key.get_pressed()
        player.handle_input(keys, tilemap)
        camera.update(player.rect)

        # NPC proximity check (drives "!" indicator)
        for npc in npcs:
            npc.update(player.rect)

        # Enemies
        for enemy in enemies:
            enemy.update(player.rect, tilemap)

        # Combat
        dead_enemies = resolve_combat(player, enemies)
        for dead in dead_enemies:
            if dead in enemies:
                enemies.remove(dead)

        # Item pickup — iterate a copy so we can remove safely
        for item in list(items):
            if player.rect.colliderect(item.rect):
                if item.on_pickup(player):
                    items.remove(item)

        # Player death
        if player.is_dead:
            print("Game Over — the player has fallen.")
            running = False

        # ---- Map transition check -----------------------------------
        if transition_cooldown > 0:
            transition_cooldown -= 1
        else:
            # Find which exit tile (if any) the player's centre is on
            centre_col = player.rect.centerx // TILE_SIZE
            centre_row = player.rect.centery // TILE_SIZE
            triggered_exit = None
            for ex in exit_tiles:
                if ex['col'] == centre_col and ex['row'] == centre_row:
                    triggered_exit = ex
                    break

            if triggered_exit is not None:
                # ---- Transition sequence ----------------------------
                # 1. Render last frame of old map and fade to black
                _render_world(screen, tilemap, items, enemies, npcs,
                              player, camera, player, frame_counter)
                pygame.display.flip()
                do_fade(screen, clock, fade_in=False, duration_frames=30)

                # 2. Load new map (repositions player, switches music)
                current_map_id = triggered_exit['target']
                tilemap, enemies, npcs, items, camera, exit_tiles = \
                    load_map(current_map_id, player)
                camera.update(player.rect)

                # 3. Render first frame of new map so fade_in has something
                #    to reveal
                _render_world(screen, tilemap, items, enemies, npcs,
                              player, camera, player, frame_counter)
                pygame.display.flip()

                # 4. Fade from black to the new map
                do_fade(screen, clock, fade_in=True, duration_frames=30)

                # Prevent immediately re-triggering the exit on the new map
                transition_cooldown = 90   # ~1.5 s at 60 FPS

        # ---- Draw ---------------------------------------------------
        _render_world(screen, tilemap, items, enemies, npcs,
                      player, camera, player, frame_counter)

        # Dialogue boxes rendered on top of everything else (screen space)
        for npc in npcs:
            if npc.is_talking:
                npc.draw_dialogue(screen)
                break   # only one dialogue box at a time

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
