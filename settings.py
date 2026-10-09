# settings.py — Global constants for the RPG game. No logic here.

# --- Screen ---
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS           = 60

# --- Tiles ---
TILE_SIZE  = 32
MAP_WIDTH  = 50   # in tiles
MAP_HEIGHT = 38   # in tiles

# --- Tile type constants ---
TILE_FLOOR = 0
TILE_WALL  = 1
TILE_EXIT  = 2   # walkable, triggers map transition

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
ENEMY_SIZE            = 32         # matches PLAYER_SIZE for consistent collision
ENEMY_MAX_HP          = 60
ENEMY_DAMAGE          = 10
ENEMY_SPEED           = 1.5
ENEMY_DETECT_RADIUS   = 150    # px — sight range
ENEMY_LOSE_RADIUS     = 225    # px — chase broken at 1.5× detect
ENEMY_ATTACK_RANGE    = 30     # px — melee reach
ENEMY_ATTACK_COOLDOWN = 90     # frames between enemy attacks
ENEMY_HIT_FLASH_FRAMES = 8     # frames to show white-flash effect
ENEMY_WAYPOINT_ARRIVE_DIST = 4 # px — waypoint arrival threshold

# --- Colors (additions) ---
ENEMY_COLOR          = (180,  50,  50)   # red
ENEMY_HIT_COLOR      = (255, 255, 255)   # flash white on hit
HUD_HP_BAR_COLOR     = (200,  50,  50)   # health bar fill
HUD_HP_BAR_BG_COLOR  = (80,   20,  20)   # health bar background
HUD_HP_TEXT_COLOR    = (255, 255, 255)

# --- Map IDs ---
MAP_ID_TOWN    = 'town'
MAP_ID_DUNGEON = 'dungeon'

# --- Tile types (duplicated here for convenience) ---
# TILE_EXIT = 2   (defined earlier)

# --- NPC ---
NPC_INTERACT_RADIUS = 48   # px
NPC_COLOR           = (80, 180, 80)    # friendly green
NPC_INDICATOR_COLOR = (255, 230, 50)   # yellow "!" above NPC
NPC_PANEL_WIDTH     = SCREEN_WIDTH - 24   # panel width with 12px padding on each side
NPC_PANEL_HEIGHT    = 130
NPC_PANEL_PADDING   = 12

# --- Items ---
ITEM_SIZE           = 16    # rendered as 16×16 squares
POTION_HEAL_AMOUNT  = 30
POTION_COLOR        = (60, 200, 100)   # bright green
POTION_PULSE_FRAMES = 40               # frames per full pulse cycle

# --- Dungeon enemy (slightly harder) ---
DUNGEON_ENEMY_HP     = 80
DUNGEON_ENEMY_DAMAGE = 15
DUNGEON_ENEMY_SPEED  = 2.0

# --- Dungeon / dialogue colors ---
DUNGEON_WALL_COLOR    = (50,  40,  70)        # dark purple-grey
DUNGEON_FLOOR_COLOR   = (35,  30,  50)        # very dark purple
DIALOGUE_BG_COLOR     = (10,  10,  30, 200)   # semi-transparent dark blue (RGBA)
DIALOGUE_TEXT_COLOR   = (220, 220, 255)
DIALOGUE_BORDER_COLOR = (100, 100, 180)

# --- Knockback ---
PLAYER_KNOCKBACK_FORCE    = 8      # initial px/frame
PLAYER_KNOCKBACK_FRICTION = 0.75   # multiplied each frame
ENEMY_KNOCKBACK_FORCE     = 10
ENEMY_KNOCKBACK_FRICTION  = 0.78

# --- XP & Leveling ---
PLAYER_BASE_XP_PER_LEVEL  = 100    # XP needed for level 2
PLAYER_XP_SCALE           = 1.4    # each level costs 40% more XP
PLAYER_HP_PER_LEVEL       = 15     # max HP gained per level
PLAYER_ATTACK_PER_LEVEL   = 5      # attack damage gained per level
LEVEL_UP_FLASH_DURATION   = 60     # frames for the level-up visual

# --- Enemy XP rewards ---
ENEMY_XP_VALUE         = 20
DUNGEON_ENEMY_XP_VALUE = 35

# --- Quest ---
DUNGEON_KILL_QUEST_TARGET = 4   # number of dungeon enemies to slay

# --- HUD additions ---
HUD_X            = 12    # left edge of the level label
HUD_Y            = 12    # top edge of the HP row
HUD_BAR_WIDTH    = 150   # pixel width of the health bar (and XP bar)
HUD_BAR_HEIGHT   = 18    # pixel height of the health bar
HUD_LABEL_GAP    = 6     # gap between label and the bar
HUD_XP_HEIGHT    = 8     # pixel height of the XP bar
HUD_XP_GAP       = 4     # gap between HP bar bottom and XP bar top
HUD_QUEST_GAP    = 6     # gap between XP bar and quest text
HUD_XP_BAR_COLOR    = (100,  80, 200)   # purple
HUD_XP_BAR_BG_COLOR = (30,   20,  60)
HUD_LEVEL_UP_COLOR  = (255, 220,  50)   # gold

# --- Game states ---
GAME_STATE_PLAYING   = 'playing'
GAME_STATE_GAME_OVER = 'game_over'
