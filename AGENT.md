# WandererRPG — Agent Context

A top-down 2D RPG built in Python with **pygame-ce** (Community Edition).
Started as a learning project, grown phase by phase.

---

## Quick Start

```bash
python main.py
```

Controls:
- **WASD / Arrow keys** — move
- **Space / F** — attack
- **E** — interact with NPC (advance dialogue)
- **Q** — close dialogue
- **ESC** — quit

---

## Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.14.3 | Language |
| pygame-ce | 2.5.8 | Game loop, rendering, input, audio |
| numpy | latest | Procedural sound generation (graceful fallback if absent) |

> **Note:** Standard `pygame` has no Python 3.14 wheel — always use `pygame-ce`.
> Install: `pip install pygame-ce`

---

## Project Structure

```
Game/
├── main.py       # Entry point, game loop, map transitions, wiring
├── settings.py   # ALL constants live here — tweak numbers here first
├── maps.py       # Map grid definitions for Town and Dungeon
├── tilemap.py    # TileMap class — renders tiles, wall queries, theme switching
├── camera.py     # Camera — follows player, clamps to map edges
├── player.py     # Player — movement, collision, combat, HP, rendering
├── enemy.py      # Enemy — patrol/chase AI, combat, rendering
├── combat.py     # resolve_combat() — hit detection between player and enemies
├── npc.py        # NPC — proximity interaction, dialogue box rendering
├── item.py       # Item base class + HealthPotion
├── hud.py        # draw_hud() — HP bar in screen space
├── sounds.py     # Procedurally generated SFX + ambient music
└── AGENT.md      # This file
```

---

## Architecture Overview

### Game Loop (`main.py`)
```
pre_init mixer → pygame.init() → sounds.init()
→ load_map() → main loop:
    events (quit / ESC / E-interact / Q-close / attack)
    → player.handle_input()   [also ticks timers]
    → enemy.update() × N
    → resolve_combat()
    → item pickup check
    → exit tile check → do_fade() + load_map()
    → draw: tilemap → items → enemies → NPCs → player → HUD → dialogue
    → display.flip() → clock.tick(FPS)
```

### Key Functions in `main.py`
- `load_map(map_id, player)` — builds all world objects for a map ID, switches music/theme, returns `(tilemap, enemies, npcs, items, camera, exit_tiles)`. **Player HP is preserved across calls.**
- `do_fade(screen, clock, fade_in, duration_frames)` — animates a black overlay for map transitions.

---

## Tile System

Tile type constants (defined in `settings.py`, exported from `tilemap.py`):

| Value | Constant | Behaviour |
|-------|----------|-----------|
| `0` | `TILE_FLOOR` | Walkable |
| `1` | `TILE_WALL` | Solid — blocks movement |
| `2` | `TILE_EXIT` | Walkable — triggers map transition |

- `TileMap.is_wall(tx, ty)` — returns `True` for walls **and** out-of-bounds coords.
- `TileMap.get_tile(tx, ty)` — returns the raw tile int (safe, returns TILE_WALL if OOB).
- **Dungeon theming:** call `tilemap.set_dungeon_theme()` / `set_town_theme()` to switch the colors used in `draw()` without changing tile data.

---

## Maps (`maps.py`)

Each builder returns a dict:
```python
{
    'grid':         list[list[int]],
    'player_spawn': (px, py),               # world-pixel coords
    'enemy_spawns': [(x, y, p_start, p_end), ...],
    'npc_spawns':   [(tile_col, tile_row, name, [lines]), ...],
    'item_spawns':  [(tile_col, tile_row, 'potion'), ...],
    'exit_tiles':   [{'col': c, 'row': r, 'target': map_id}, ...],
    'map_width':    int,   # tiles
    'map_height':   int,   # tiles
}
```

### Town layout (50×38 tiles)
```
Room A (2-14, 2-12)   ←→  Room B (18-30, 2-12)   ←→  Room C (34-47, 2-12)
      ↕                          ↕                           ↕
Room D (6-20, 18-33)  ←→  Room E (28-44, 18-33)
```
- Player spawns in Room A
- Elder NPC at tile (5, 4) — Room A
- Exit to Dungeon at tile (13, 34) — bottom of Room D
- Potions in Rooms A and B

### Dungeon layout (50×38 tiles)
```
Room1 (4-14, 2-10)  →  Room2 (18-28, 2-10)  →  Room3 (32-46, 2-14)
   ↓                                                      ↓
Room4 (4-20, 16-28)  →  Room5 (24-46, 18-34)
```
- Player spawns in Room 1 (entry)
- Exit back to Town at tile (8, 3) — top of Room 1
- 6 enemies across Rooms 2–5
- Potions in Rooms 3 and 5

---

## Player (`player.py`)

### Key state
| Attribute | Type | Purpose |
|-----------|------|---------|
| `_x`, `_y` | float | World-pixel position (sub-pixel precision) |
| `hp`, `max_hp` | int | Health |
| `is_attacking` | bool | True while swing hitbox is active |
| `attack_timer` | int | Frames remaining in swing |
| `attack_cooldown_timer` | int | Frames until next attack allowed |
| `invincibility_timer` | int | Frames of post-hit immunity |
| `_direction` | int | Facing: RIGHT=0, DOWN=1, LEFT=2, UP=3 |

### Collision pattern
Four-corner sampling: checks all 4 corners of the bounding box at the projected position. Each axis tested independently for wall-sliding.

### Attack hitbox
`get_attack_rect()` returns a `pygame.Rect` projected from the player's facing edge, `PLAYER_ATTACK_RANGE` deep and `PLAYER_SIZE` wide.

---

## Enemy (`enemy.py`)

### Constructor
```python
Enemy(x, y, patrol_start, patrol_end, hp=None, speed=None, damage=None)
```
- `patrol_start` / `patrol_end` — `(tile_col, tile_row)` tuples
- Override hp/speed/damage for dungeon variants (uses `DUNGEON_ENEMY_*` constants)

### State machine
```
PATROL ──(dist ≤ ENEMY_DETECT_RADIUS)──→ CHASE
CHASE  ──(dist > ENEMY_LOSE_RADIUS)────→ PATROL
```
Hysteresis prevents flickering. Patrol switches waypoint on arrival (<4px) or when stuck.

---

## Combat (`combat.py`)

`resolve_combat(player, enemies) → list[Enemy]`

Each frame:
1. If `player.is_attacking`: check `player.get_attack_rect()` vs each `enemy.rect`
2. For each enemy: check `enemy.can_attack_player(player.rect)` — inflated rect + cooldown
3. Returns list of newly-dead enemies (caller removes them from the list)

Enemy damage uses `enemy.damage` (per-instance), not the global constant — so dungeon enemies hit harder.

---

## NPC (`npc.py`)

```python
NPC(tile_col, tile_row, name, dialogue_lines)
```

- `npc.update(player_rect)` — call each frame to update the "!" indicator
- `npc.interact()` — advances dialogue, plays bleep sound
- `npc.close_dialogue()` — hides dialogue box
- `npc.draw(surface, camera)` — draws body + indicator
- `npc.draw_dialogue(surface)` — draws bottom-screen dialogue panel (screen space)

Dialogue panel: full-width, 120px tall, anchored to bottom of screen. Shows name, current line, and `[E] Next | [Q] Close` hint.

---

## Items (`item.py`)

```python
HealthPotion(tile_col, tile_row)
```

- 16×16px pulsing green square
- `item.draw(surface, camera, frame_counter)` — pass the frame counter for pulse animation
- `item.on_pickup(player)` — heals `min(POTION_HEAL_AMOUNT, max_hp - hp)`, plays sound, returns `True` (remove from list)
- Pickup: check `player.rect.colliderect(item.rect)` each frame, iterate a copy of the list

---

## Sounds (`sounds.py`)

All sounds are generated procedurally from numpy sine waves at runtime. No audio files needed.

### API
```python
sounds.init()              # call once after pygame.init()
sounds.play_swing()        # player attack
sounds.play_hit_enemy()    # enemy takes damage
sounds.play_hit_player()   # player takes damage
sounds.play_potion()       # potion picked up
sounds.play_dialogue()     # NPC dialogue opens
sounds.play_music_town()   # start looping town ambient drone
sounds.play_music_dungeon()# start looping dungeon ambient drone
sounds.stop_music()        # stop ambient
```

Gracefully degrades to no-ops if numpy is not installed.

### Adding a new sound
1. Add a numpy waveform generator function in `sounds.py`
2. Store the result as a `pygame.Sound` in `init()`
3. Add a `play_*()` function
4. Call it from the relevant class using a lazy import: `import sounds; sounds.play_*()`

---

## HUD (`hud.py`)

`draw_hud(surface, player)` — call last in the draw step (screen space).

Renders a health bar in the top-left corner. Font is cached at module level after first call.

---

## Settings Reference (`settings.py`)

All magic numbers live here. Key groups:

| Group | Constants |
|-------|-----------|
| Screen | `SCREEN_WIDTH`, `SCREEN_HEIGHT`, `FPS` |
| Tiles | `TILE_SIZE`, `MAP_WIDTH`, `MAP_HEIGHT`, `TILE_FLOOR`, `TILE_WALL`, `TILE_EXIT` |
| Player | `PLAYER_SPEED`, `PLAYER_SIZE`, `PLAYER_MAX_HP`, `PLAYER_ATTACK_*`, `PLAYER_INVINCIBILITY_FRAMES` |
| Enemy (town) | `ENEMY_MAX_HP`, `ENEMY_DAMAGE`, `ENEMY_SPEED`, `ENEMY_DETECT_RADIUS`, `ENEMY_LOSE_RADIUS`, `ENEMY_ATTACK_*` |
| Enemy (dungeon) | `DUNGEON_ENEMY_HP`, `DUNGEON_ENEMY_DAMAGE`, `DUNGEON_ENEMY_SPEED` |
| NPC | `NPC_INTERACT_RADIUS`, `NPC_COLOR`, `NPC_INDICATOR_COLOR` |
| Items | `POTION_HEAL_AMOUNT`, `POTION_COLOR`, `POTION_PULSE_FRAMES` |
| Maps | `MAP_ID_TOWN`, `MAP_ID_DUNGEON` |
| Colors | `WALL_COLOR`, `FLOOR_COLOR`, `PLAYER_COLOR`, `ENEMY_COLOR`, `DUNGEON_WALL_COLOR`, `DUNGEON_FLOOR_COLOR`, `DIALOGUE_*`, `HUD_*` |

---

## Extending the Game

### Add a new map
1. Add a `MAP_ID_*` constant in `settings.py`
2. Add a `build_*_map()` function in `maps.py` returning the standard dict
3. Handle the new ID in `load_map()` in `main.py`

### Add a new enemy type
Pass overriding `hp`, `speed`, `damage` kwargs to `Enemy(...)`.

### Add a new item type
Subclass `Item` in `item.py`, implement `draw()` and `on_pickup()`.

### Add a new NPC
Add an entry to `npc_spawns` in the relevant map builder in `maps.py`.

### Add a new sound
See the Sounds section above.

---

## Phase Roadmap

| Phase | Status | Contents |
|-------|--------|---------|
| 1 | ✅ Done | Player, tilemap, camera, movement, collision |
| 2 | ✅ Done | Action melee combat, patrol/chase enemies, health + HUD |
| 3 | ✅ Done | NPC + dialogue, health potions, second map (Dungeon), procedural sounds |
| 4 | 🔜 Next | Quests, inventory, more story |

---

## Git / GitHub

- Repo: https://github.com/KalleLofquist/WandererRPG
- Branch: `main`
- Commit after each completed phase or significant feature
