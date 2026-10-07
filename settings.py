# settings.py — Global constants for the RPG game. No logic here.

# --- Screen ---
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS           = 60

# --- Tiles ---
TILE_SIZE  = 32
MAP_WIDTH  = 50   # in tiles
MAP_HEIGHT = 38   # in tiles

# --- Player ---
PLAYER_SPEED = 3
PLAYER_SIZE  = 28  # square side length in pixels

# --- Colors (R, G, B) ---
WHITE       = (255, 255, 255)
BLACK       = (0,   0,   0)
WALL_COLOR  = (80,  60,  50)   # dark brownish-grey
FLOOR_COLOR = (50,  70,  50)   # dark greenish-grey
PLAYER_COLOR = (70, 130, 200)  # steel blue

# --- Combat ---
PLAYER_MAX_HP            = 100
PLAYER_ATTACK_DAMAGE     = 25
PLAYER_ATTACK_RANGE      = 40   # px in front of player
PLAYER_ATTACK_DURATION   = 12   # frames the hitbox is active
PLAYER_ATTACK_COOLDOWN   = 20   # frames between attacks
PLAYER_INVINCIBILITY_FRAMES = 45

# --- Enemy ---
ENEMY_MAX_HP          = 60
ENEMY_DAMAGE          = 10
ENEMY_SPEED           = 1.5
ENEMY_DETECT_RADIUS   = 150    # px — sight range
ENEMY_LOSE_RADIUS     = 225    # px — chase broken at 1.5× detect
ENEMY_ATTACK_RANGE    = 30     # px — melee reach
ENEMY_ATTACK_COOLDOWN = 90     # frames between enemy attacks

# --- Colors (additions) ---
ENEMY_COLOR          = (180,  50,  50)   # red
ENEMY_HIT_COLOR      = (255, 255, 255)   # flash white on hit
HUD_HP_BAR_COLOR     = (200,  50,  50)   # health bar fill
HUD_HP_BAR_BG_COLOR  = (80,   20,  20)   # health bar background
HUD_HP_TEXT_COLOR    = (255, 255, 255)
