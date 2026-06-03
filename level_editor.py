# level_editor.py - Editor visual de niveles del juego

import pygame
import os
from constants import (
    CELL_SIZE, GRID_COLS, GRID_ROWS, SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_BG, COLOR_WHITE, COLOR_WALL, COLOR_PLAYER,
    COLOR_OBJ_A, COLOR_OBJ_B, COLOR_ENEMY_LIGHT, COLOR_ENEMY_MEDIUM,
    COLOR_ENEMY_HEAVY, COLOR_GRAY, FPS,
    LEVEL_WALL, LEVEL_FREE, LEVEL_PLAYER,
    LEVEL_OBJ_A, LEVEL_OBJ_B, LEVEL_ENEMY1, LEVEL_ENEMY2, LEVEL_ENEMY3
)


# Mapa de tile → color para visualización en el editor
TILE_COLORS = {
    LEVEL_WALL:   COLOR_WALL,
    LEVEL_FREE:   (26, 26, 46),
    LEVEL_PLAYER: COLOR_PLAYER,
    LEVEL_OBJ_A:  COLOR_OBJ_A,
    LEVEL_OBJ_B:  COLOR_OBJ_B,
    LEVEL_ENEMY1: COLOR_ENEMY_LIGHT,
    LEVEL_ENEMY2: COLOR_ENEMY_MEDIUM,
    LEVEL_ENEMY3: COLOR_ENEMY_HEAVY,
}

TILE_ORDER = [LEVEL_FREE, LEVEL_WALL, LEVEL_PLAYER,
              LEVEL_OBJ_A, LEVEL_OBJ_B,
              LEVEL_ENEMY1, LEVEL_ENEMY2, LEVEL_ENEMY3]

TILE_NAMES = {
    LEVEL_WALL:   'Muro',
    LEVEL_FREE:   'Vacio',
    LEVEL_PLAYER: 'Tanque jugador',
    LEVEL_OBJ_A:  'Base A (azul)',
    LEVEL_OBJ_B:  'Base B (verde)',
    LEVEL_ENEMY1: 'Enemigo ligero',
    LEVEL_ENEMY2: 'Enemigo medio',
    LEVEL_ENEMY3: 'Enemigo pesado',
}

_PALETTE_Y = GRID_ROWS * CELL_SIZE  # y donde empieza el HUD del editor


class LevelEditor:
    """Editor gráfico que permite diseñar y guardar niveles."""

    def __init__(self, screen, clock, level_number=None, random_mode=True):
        self.__screen = screen
        self.__clock  = clock
        self.__grid = [[LEVEL_FREE for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.__selected_tile = LEVEL_WALL
        self.__font = pygame.font.SysFont('monospace', 14, bold=True)
        self.__font_sm = pygame.font.SysFont('monospace', 11)
        self.__message = ""
        self.__message_timer = 0
        self.__play_requested = False
        self.__level_number = level_number
        self.__random_mode = random_mode

        # Botón de toggle random (esquina derecha del HUD)
        self.__btn_random = pygame.Rect(
            SCREEN_WIDTH - 162, _PALETTE_Y + 9, 154, 38
        )
        self.__init_borders()

    def __init_borders(self):
        for x in range(GRID_COLS):
            self.__grid[0][x] = LEVEL_WALL
            self.__grid[GRID_ROWS - 1][x] = LEVEL_WALL
        for y in range(GRID_ROWS):
            self.__grid[y][0] = LEVEL_WALL
            self.__grid[y][GRID_COLS - 1] = LEVEL_WALL

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def run_editor(self):
        """Bucle principal del editor.

        Retorna (grid_lines, random_mode):
          - grid_lines es lista de strings si el usuario presionó PROBAR, o None.
          - random_mode es el estado actual del toggle al salir.
        """
        self.__play_requested = False
        running = True
        while running:
            self.__clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    running = self.__handle_keydown(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.__handle_click(event)
                elif event.type == pygame.MOUSEMOTION:
                    if pygame.mouse.get_pressed()[0]:
                        self.__handle_click(event)

            self.__render_editor()
            pygame.display.flip()

        grid = self.show_level() if self.__play_requested else None
        return grid, self.__random_mode

    def load_from_grid_strings(self, grid_strings):
        """Carga el nivel desde una lista de strings en la grilla del editor."""
        for y in range(min(GRID_ROWS, len(grid_strings))):
            line = grid_strings[y].ljust(GRID_COLS)
            for x in range(GRID_COLS):
                ch = line[x] if x < len(line) else LEVEL_FREE
                self.__grid[y][x] = ch if ch in TILE_COLORS else LEVEL_FREE

    def load_level(self, path):
        """Carga un nivel desde archivo."""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
            for y in range(min(GRID_ROWS, len(lines))):
                line = lines[y].rstrip('\n').ljust(GRID_COLS)
                for x in range(GRID_COLS):
                    ch = line[x] if x < len(line) else '.'
                    self.__grid[y][x] = ch if ch in TILE_COLORS else LEVEL_FREE
            self.__show_message(f"Cargado: {os.path.basename(path)}")
        except Exception as e:
            self.__show_message(f"Error: {e}")

    def save_level(self):
        """Guarda el nivel en levels/level{N}.txt (o level_nuevo.txt si sin número)."""
        if not self.validate_level():
            return False
        path = self.__get_save_path()
        levels_dir = os.path.dirname(path)
        os.makedirs(levels_dir, exist_ok=True)
        try:
            with open(path, 'w') as f:
                for row in self.__grid:
                    f.write(''.join(row) + '\n')
            self.__show_message(f"Guardado: {os.path.basename(path)}")
            return True
        except Exception as e:
            self.__show_message(f"Error guardando: {e}")
            return False

    def show_level(self):
        return [''.join(row) for row in self.__grid]

    def edit_cell(self, x, y, tile):
        if x == 0 or x == GRID_COLS - 1 or y == 0 or y == GRID_ROWS - 1:
            return
        self.__grid[y][x] = tile

    def validate_level(self):
        has_player = any(self.__grid[y][x] == LEVEL_PLAYER
                         for y in range(GRID_ROWS) for x in range(GRID_COLS))
        has_obj = any(self.__grid[y][x] in (LEVEL_OBJ_A, LEVEL_OBJ_B)
                      for y in range(GRID_ROWS) for x in range(GRID_COLS))
        if not has_player:
            self.__show_message("ERROR: Falta posición del jugador (P)")
            return False
        if not has_obj:
            self.__show_message("ERROR: Falta al menos un objetivo (A o B)")
            return False
        return True

    # ------------------------------------------------------------------
    # Handlers de eventos
    # ------------------------------------------------------------------

    def __handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE:
            return False
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.validate_level():
                self.__play_requested = True
                return False
        elif event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
            self.save_level()
        elif event.key == pygame.K_r and self.__level_number is not None:
            self.__reload_random()
        elif event.key == pygame.K_c:
            self.__clear_grid()
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3,
                           pygame.K_4, pygame.K_5, pygame.K_6,
                           pygame.K_7, pygame.K_8):
            idx = event.key - pygame.K_1
            if idx < len(TILE_ORDER):
                self.__selected_tile = TILE_ORDER[idx]
        return True

    def __handle_click(self, event):
        if hasattr(event, 'pos'):
            mx, my = event.pos
        else:
            mx, my = pygame.mouse.get_pos()

        if my >= _PALETTE_Y:
            self.__handle_palette_click(mx, my)
            return

        cx = mx // CELL_SIZE
        cy = my // CELL_SIZE
        if 0 <= cx < GRID_COLS and 0 <= cy < GRID_ROWS:
            self.edit_cell(cx, cy, self.__selected_tile)

    def __handle_palette_click(self, mx, my):
        # Toggle random mode
        if self.__btn_random.collidepoint(mx, my):
            self.__random_mode = not self.__random_mode
            status = "ON" if self.__random_mode else "OFF"
            self.__show_message(f"Modo random: {status}")
            return

        # Selección de tile
        for i, tile in enumerate(TILE_ORDER):
            px = 10 + i * 44
            rect = pygame.Rect(px, _PALETTE_Y + 8, 36, 36)
            if rect.collidepoint(mx, my):
                self.__selected_tile = tile
                break

    def __clear_grid(self):
        self.__grid = [[LEVEL_FREE for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.__init_borders()

    def __reload_random(self):
        from board import Board
        b = Board()
        grid_strings = b.generate_level_grid(self.__level_number)
        self.load_from_grid_strings(grid_strings)
        self.__show_message(f"Nivel {self.__level_number}: nuevo aleatorio")

    def __get_save_path(self):
        levels_dir = os.path.join(os.path.dirname(__file__), 'levels')
        if self.__level_number is not None:
            return os.path.join(levels_dir, f'level{self.__level_number}.txt')
        return os.path.join(levels_dir, 'level_nuevo.txt')

    def __show_message(self, msg):
        self.__message = msg
        self.__message_timer = 120

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def __render_editor(self):
        self.__screen.fill(COLOR_BG)

        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                tile = self.__grid[y][x]
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.__screen, (26, 26, 46), rect)
                pygame.draw.rect(self.__screen, (50, 50, 70), rect, 1)
                if tile != LEVEL_FREE:
                    self.__draw_icon(self.__screen, tile, rect)

        self.__render_palette()

        if self.__message_timer > 0:
            self.__message_timer -= 1
            msg_surf = self.__font.render(self.__message, True, (255, 220, 100))
            self.__screen.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2,
                                          _PALETTE_Y - 24))

    def __render_palette(self):
        pygame.draw.rect(self.__screen, (15, 15, 35),
                         (0, _PALETTE_Y, SCREEN_WIDTH, SCREEN_HEIGHT - _PALETTE_Y))

        # Tiles
        for i, tile in enumerate(TILE_ORDER):
            px = 10 + i * 44
            py = _PALETTE_Y + 8
            rect = pygame.Rect(px, py, 36, 36)
            pygame.draw.rect(self.__screen, (26, 26, 46), rect)
            if tile != LEVEL_FREE:
                self.__draw_icon(self.__screen, tile, rect)
            border = (255, 255, 0) if tile == self.__selected_tile else (100, 100, 120)
            pygame.draw.rect(self.__screen, border, rect, 2)
            key_surf = self.__font_sm.render(str(i + 1), True, COLOR_WHITE)
            self.__screen.blit(key_surf, (px + 2, py + 1))

        # Info del tile seleccionado
        name = TILE_NAMES.get(self.__selected_tile, '')
        name_surf = self.__font.render(f"Sel: {name}", True, (255, 220, 100))
        self.__screen.blit(name_surf, (372, _PALETTE_Y + 5))

        # Instrucciones (zona izquierda-centro)
        inst1 = "ENTER:jugar  Ctrl+S:guardar  C:limpiar  ESC:salir"
        self.__screen.blit(self.__font_sm.render(inst1, True, COLOR_GRAY),
                           (372, _PALETTE_Y + 22))
        if self.__level_number is not None:
            self.__screen.blit(
                self.__font_sm.render("R: nuevo aleatorio para este nivel", True, (100, 200, 255)),
                (372, _PALETTE_Y + 36)
            )

        # Botón RANDOM ON/OFF (esquina derecha)
        mouse = pygame.mouse.get_pos()
        if self.__random_mode:
            btn_c  = (30, 120, 50)
            btn_hc = (40, 160, 70)
            label  = "RANDOM: ON"
        else:
            btn_c  = (110, 35, 35)
            btn_hc = (150, 50, 50)
            label  = "RANDOM: OFF"

        color = btn_hc if self.__btn_random.collidepoint(mouse) else btn_c
        pygame.draw.rect(self.__screen, color, self.__btn_random, border_radius=6)
        pygame.draw.rect(self.__screen, COLOR_WHITE, self.__btn_random, 2, border_radius=6)
        lbl = self.__font.render(label, True, COLOR_WHITE)
        self.__screen.blit(lbl, lbl.get_rect(center=self.__btn_random.center))

    # ------------------------------------------------------------------
    # Iconos
    # ------------------------------------------------------------------

    def __draw_icon(self, surf, tile, rect):
        if tile == LEVEL_WALL:
            self.__icon_wall(surf, rect)
        elif tile == LEVEL_PLAYER:
            self.__icon_tank(surf, rect, COLOR_PLAYER, None)
        elif tile == LEVEL_ENEMY1:
            self.__icon_tank(surf, rect, COLOR_ENEMY_LIGHT, '1')
        elif tile == LEVEL_ENEMY2:
            self.__icon_tank(surf, rect, COLOR_ENEMY_MEDIUM, '2')
        elif tile == LEVEL_ENEMY3:
            self.__icon_tank(surf, rect, COLOR_ENEMY_HEAVY, '3')
        elif tile == LEVEL_OBJ_A:
            self.__icon_base(surf, rect, COLOR_OBJ_A, 'A')
        elif tile == LEVEL_OBJ_B:
            self.__icon_base(surf, rect, COLOR_OBJ_B, 'B')

    def __icon_wall(self, surf, rect):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        pygame.draw.rect(surf, COLOR_WALL, rect)
        mortar = (40, 40, 52)
        pygame.draw.line(surf, mortar, (x, y + h // 3), (x + w, y + h // 3))
        pygame.draw.line(surf, mortar, (x, y + 2 * h // 3), (x + w, y + 2 * h // 3))
        pygame.draw.line(surf, mortar, (x + w // 2, y), (x + w // 2, y + h // 3))
        pygame.draw.line(surf, mortar, (x + w // 4, y + h // 3), (x + w // 4, y + 2 * h // 3))
        pygame.draw.line(surf, mortar, (x + 3 * w // 4, y + h // 3), (x + 3 * w // 4, y + 2 * h // 3))
        pygame.draw.line(surf, mortar, (x + w // 2, y + 2 * h // 3), (x + w // 2, y + h))

    def __icon_tank(self, surf, rect, color, label):
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        dark = tuple(max(0, c - 70) for c in color)
        m = max(2, w // 6)
        pygame.draw.rect(surf, dark, (x + 1, y + m, m, h - 2 * m))
        pygame.draw.rect(surf, dark, (x + w - m - 1, y + m, m, h - 2 * m))
        body = pygame.Rect(x + m, y + m, w - 2 * m, h - 2 * m)
        pygame.draw.rect(surf, color, body, border_radius=max(2, w // 12))
        pygame.draw.rect(surf, dark, body, 2, border_radius=max(2, w // 12))
        bw = max(2, w // 9)
        pygame.draw.rect(surf, dark, (x + w // 2 - bw // 2, y + 1, bw, h // 2))
        pygame.draw.circle(surf, dark, (x + w // 2, y + h // 2), max(2, w // 7))
        if label:
            f = self.__font if w > 28 else self.__font_sm
            t = f.render(label, True, (255, 255, 255))
            surf.blit(t, t.get_rect(center=(x + w // 2, y + int(h * 0.72))))

    def __icon_base(self, surf, rect, color, label):
        cx, cy = rect.centerx, rect.centery
        r = min(rect.width, rect.height) // 2 - 3
        pygame.draw.circle(surf, color, (cx, cy), r)
        pygame.draw.circle(surf, (240, 240, 240), (cx, cy), r, 2)
        f = self.__font if rect.width > 28 else self.__font_sm
        t = f.render(label, True, (0, 0, 0))
        surf.blit(t, t.get_rect(center=(cx, cy)))
