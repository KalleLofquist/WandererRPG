# WandererRPG

A top-down 2D action RPG built from scratch in Python with pygame-ce. Started as a small learning project — grown one phase at a time.

---

## Features

- 🗺️ **Two explorable areas** — a Town and an underground Dungeon, connected by a map transition with a fade effect
- ⚔️ **Action melee combat** — swing your sword with `Space`, enemies flash and die
- 🧠 **Enemy AI** — enemies patrol their rooms and chase you when you get close
- 🗣️ **NPC dialogue** — talk to the Elder in Town for a hint about what lies below
- 🧪 **Health potions** — pick them up off the ground to restore HP
- ❤️ **Health bar HUD** — always visible in the top-left corner
- 🔊 **Procedural audio** — all sound effects and ambient music generated at runtime, no audio files needed

---

## Getting Started

### Requirements

- Python 3.10+
- pygame-ce

### Installation

```bash
pip install pygame-ce
```

> **Note:** This project uses **pygame-ce** (Community Edition), not standard pygame.
> Standard pygame does not have a Python 3.14 wheel — pygame-ce is a drop-in replacement with the same API.

### Run the game

```bash
python main.py
```

---

## Controls

| Key | Action |
|-----|--------|
| `WASD` / Arrow keys | Move |
| `Space` / `F` | Attack |
| `E` | Talk to NPC / advance dialogue |
| `Q` | Close dialogue |
| `ESC` | Quit |

---

## Gameplay Tips

- Walk through the **southern exit** in Room D (bottom of the Town map) to enter the Dungeon
- The **Elder NPC** in Room A can give you a heads-up before you descend
- Pick up **green potions** to heal — they restore 30 HP each
- Dungeon enemies hit harder and have more HP than Town enemies
- You have **invincibility frames** after taking a hit — use them!

---

## Project Structure

```
Game/
├── main.py       # Entry point and game loop
├── settings.py   # All constants and configuration
├── maps.py       # Map definitions (Town + Dungeon)
├── tilemap.py    # Tile rendering and collision
├── camera.py     # Camera that follows the player
├── player.py     # Player movement, combat, and rendering
├── enemy.py      # Enemy AI and combat
├── combat.py     # Hit detection logic
├── npc.py        # NPC interaction and dialogue
├── item.py       # Collectible items (potions)
├── hud.py        # On-screen health bar
└── sounds.py     # Procedurally generated audio
```

---

## Roadmap

- [x] Phase 1 — Player, tilemap, camera, movement, collision
- [x] Phase 2 — Action combat, enemy AI, health system, HUD
- [x] Phase 3 — NPC dialogue, items, second map, procedural audio
- [ ] Phase 4 — Quests, inventory, deeper story

---

## Built With

- [Python](https://www.python.org/) 3.14
- [pygame-ce](https://pyga.me/) 2.5.8

---

## License

This project is open source and available under the [MIT License](LICENSE).
