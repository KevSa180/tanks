# constants.py - Constantes globales del juego de tanques

# --- Dimensiones ---
CELL_SIZE = 40          # Píxeles por celda
GRID_COLS = 20          # Columnas del tablero
GRID_ROWS = 15          # Filas del tablero
SCREEN_WIDTH  = CELL_SIZE * GRID_COLS   # 800px
SCREEN_HEIGHT = CELL_SIZE * GRID_ROWS + 60  # 660px (60 para HUD)
HUD_HEIGHT = 60

# --- Rendimiento ---
FPS = 60

# --- Juego ---
PLAYER_LIVES = 3
TOTAL_LEVELS = 3
ENEMY_MOVE_INTERVAL = 500   # ms entre movimientos del enemigo
PROLOG_RECALC_INTERVAL = 2000  # ms para recalcular ruta Prolog
NEAR_DISTANCE = 5           # celdas Manhattan para considerar "cerca"

# --- Direcciones ---
DIR_UP    = 'UP'
DIR_DOWN  = 'DOWN'
DIR_LEFT  = 'LEFT'
DIR_RIGHT = 'RIGHT'

DIRECTIONS = [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]

DIR_DELTA = {
    DIR_UP:    (0, -1),
    DIR_DOWN:  (0,  1),
    DIR_LEFT:  (-1, 0),
    DIR_RIGHT: (1,  0),
}

# --- Estados del juego ---
STATE_MENU             = 'MENU'
STATE_LEVEL_SELECT     = 'LEVEL_SELECT'
STATE_EDITOR_SELECT    = 'EDITOR_SELECT'
STATE_PLAYING          = 'PLAYING'
STATE_GAME_OVER        = 'GAME_OVER'
STATE_WIN              = 'WIN'
STATE_LEVEL_TRANSITION = 'LEVEL_TRANSITION'

# --- Dificultades ---
DIFFICULTY_EASY   = 1
DIFFICULTY_MEDIUM = 2
DIFFICULTY_HARD   = 3

# --- Tipos de enemigos ---
ENEMY_LIGHT  = 'LIGHT'
ENEMY_MEDIUM = 'MEDIUM'
ENEMY_HEAVY  = 'HEAVY'

ENEMY_STATS = {
    ENEMY_LIGHT:  {'health': 1, 'speed': 2, 'damage': 1, 'bullet_speed': 6},
    ENEMY_MEDIUM: {'health': 2, 'speed': 1, 'damage': 2, 'bullet_speed': 5},
    ENEMY_HEAVY:  {'health': 3, 'speed': 1, 'damage': 3, 'bullet_speed': 4},
}

# --- Tipos de objetivos ---
OBJ_TYPE_A = 'TYPE_A'
OBJ_TYPE_B = 'TYPE_B'

OBJ_STATS = {
    OBJ_TYPE_A: {'health': 3, 'points': 500},
    OBJ_TYPE_B: {'health': 1, 'points': 200},
}

# --- Colores (RGB) ---
COLOR_BG          = (26,  26,  46)   # #1a1a2e
COLOR_WALL        = (74,  74,  90)   # #4a4a5a
COLOR_WALL_BORDER = (50,  50,  65)
COLOR_PLAYER      = (0,   255, 136)  # #00ff88
COLOR_ENEMY_LIGHT  = (255, 255, 0)   # #ffff00
COLOR_ENEMY_MEDIUM = (255, 136, 0)   # #ff8800
COLOR_ENEMY_HEAVY  = (255, 34,  0)   # #ff2200
COLOR_OBJ_A       = (0,   136, 255)  # #0088ff
COLOR_OBJ_B       = (136, 255, 0)    # #88ff00
COLOR_BULLET      = (255, 255, 255)  # #ffffff
COLOR_HUD_BG      = (10,  10,  30)
COLOR_WHITE       = (255, 255, 255)
COLOR_BLACK       = (0,   0,   0)
COLOR_GRAY        = (128, 128, 128)
COLOR_YELLOW      = (255, 220, 50)
COLOR_RED         = (220, 50,  50)
COLOR_GREEN       = (50,  220, 100)

ENEMY_COLORS = {
    ENEMY_LIGHT:  COLOR_ENEMY_LIGHT,
    ENEMY_MEDIUM: COLOR_ENEMY_MEDIUM,
    ENEMY_HEAVY:  COLOR_ENEMY_HEAVY,
}

# --- Mapa de caracteres del nivel ---
LEVEL_WALL    = 'W'
LEVEL_FREE    = '.'
LEVEL_PLAYER  = 'P'
LEVEL_OBJ_A   = 'A'
LEVEL_OBJ_B   = 'B'
LEVEL_ENEMY1  = '1'
LEVEL_ENEMY2  = '2'
LEVEL_ENEMY3  = '3'

# --- Puntos por matar enemigos ---
SCORE_KILL_LIGHT  = 100
SCORE_KILL_MEDIUM = 200
SCORE_KILL_HEAVY  = 300

# --- Velocidad de balas ---
PLAYER_BULLET_SPEED  = 8
PLAYER_BULLET_DAMAGE = 1

# --- Acciones Prolog ---
ACTION_ATTACK  = 'atacar'
ACTION_DEFEND  = 'defender'
ACTION_AMBUSH  = 'emboscar'

# --- Roles de enemigos ---
ROLE_HUNTER   = 'HUNTER'    # persigue al jugador
ROLE_DEFENDER = 'DEFENDER'  # guarda los objetivos

# --- Rotación de direcciones (para desatascarse) ---
ROTATION_CW = {
    'UP': 'RIGHT', 'RIGHT': 'DOWN', 'DOWN': 'LEFT', 'LEFT': 'UP'
}
ROTATION_CCW = {
    'UP': 'LEFT', 'LEFT': 'DOWN', 'DOWN': 'RIGHT', 'RIGHT': 'UP'
}
DIR_OPPOSITE = {
    'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'
}

# --- Configuración de niveles (cantidades fijas, posiciones aleatorias) ---
# Nivel N tiene N objetivos primarios (TYPE_A) y N-1 defensores + 1 hunter.
LEVEL_CONFIGS = {
    1: {
        'wall_segments': 3,
        'enemies':    {ENEMY_LIGHT: 2},                          # 1 hunter + 1 defender
        'objectives': {OBJ_TYPE_A: 1},
    },
    2: {
        'wall_segments': 5,
        'enemies':    {ENEMY_LIGHT: 2, ENEMY_MEDIUM: 1},         # 1 hunter + 2 defenders
        'objectives': {OBJ_TYPE_A: 2, OBJ_TYPE_B: 1},
    },
    3: {
        'wall_segments': 7,
        'enemies':    {ENEMY_LIGHT: 2, ENEMY_MEDIUM: 1, ENEMY_HEAVY: 1},  # 1 hunter + 3 defenders
        'objectives': {OBJ_TYPE_A: 3, OBJ_TYPE_B: 2},
    },
}
