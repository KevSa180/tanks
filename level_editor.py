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

TILE_LABELS = {
    LEVEL_WALL:   'W',
    LEVEL_FREE:   '.',
    LEVEL_PLAYER: 'P',
    LEVEL_OBJ_A:  'A',
    LEVEL_OBJ_B:  'B',
    LEVEL_ENEMY1: '1',
    LEVEL_ENEMY2: '2',
    LEVEL_ENEMY3: '3',
}

TILE_ORDER = [LEVEL_FREE, LEVEL_WALL, LEVEL_PLAYER,
              LEVEL_OBJ_A, LEVEL_OBJ_B,
              LEVEL_ENEMY1, LEVEL_ENEMY2, LEVEL_ENEMY3]

# Nombre legible de cada tile (para la paleta del editor)
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


class LevelEditor:
    """Editor gráfico que permite diseñar y guardar niveles."""

    def __init__(self, screen, clock):
        self.__screen = screen
        self.__clock  = clock
        self.__grid = [[LEVEL_FREE for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.__selected_tile = LEVEL_WALL
        self.__current_file = None
        self.__font = pygame.font.SysFont('monospace', 14, bold=True)
        self.__font_sm = pygame.font.SysFont('monospace', 11)
        self.__message = ""
        self.__message_timer = 0
        self.__play_requested = False   # True si el usuario pidió PROBAR
        self.__init_borders()

    def __init_borders(self):
        """Rellena los bordes con muros."""
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

        Retorna la grilla a jugar (lista de strings) si el usuario presionó
        PROBAR (ENTER), o None si simplemente salió con ESC / cerró la ventana.
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

        return self.show_level() if self.__play_requested else None

    def load_level(self, path):
        """Carga un nivel existente en el editor."""
        try:
            with open(path, 'r') as f:
                lines = f.readlines()
            for y in range(min(GRID_ROWS, len(lines))):
                line = lines[y].rstrip('\n').ljust(GRID_COLS)
                for x in range(GRID_COLS):
                    ch = line[x] if x < len(line) else '.'
                    if ch in TILE_COLORS:
                        self.__grid[y][x] = ch
                    else:
                        self.__grid[y][x] = LEVEL_FREE
            self.__current_file = path
            self.__show_message(f"Cargado: {os.path.basename(path)}")
        except Exception as e:
            self.__show_message(f"Error: {e}")

    def save_level(self, path=None):
        """Guarda el nivel en disco."""
        if not self.validate_level():
            return False
        if path is None:
            # Siempre guardar en el archivo personalizado: nunca sobreescribir
            # los niveles normales (level1/2/3) aunque se hayan cargado con Ctrl+L
            path = self.__ask_filename()
        if path is None:
            return False
        try:
            with open(path, 'w') as f:
                for row in self.__grid:
                    f.write(''.join(row) + '\n')
            self.__current_file = path
            self.__show_message(f"Guardado: {os.path.basename(path)}")
            return True
        except Exception as e:
            self.__show_message(f"Error guardando: {e}")
            return False

    def show_level(self):
        """Retorna el nivel como lista de strings."""
        return [''.join(row) for row in self.__grid]

    def edit_cell(self, x, y, tile):
        """Cambia el tile de una celda (respeta bordes)."""
        if x == 0 or x == GRID_COLS - 1 or y == 0 or y == GRID_ROWS - 1:
            return  # bordes son inmutables
        self.__grid[y][x] = tile

    def validate_level(self):
        """Verifica que el nivel tenga al menos un jugador y un objetivo."""
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
        """Maneja teclas del editor. Retorna False para salir."""
        if event.key == pygame.K_ESCAPE:
            return False
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            # PROBAR: jugar el nivel actual si es válido (tiene P y un objetivo)
            if self.validate_level():
                self.__play_requested = True
                return False
        elif event.key == pygame.K_s and (event.mod & pygame.KMOD_CTRL):
            self.save_level()
        elif event.key == pygame.K_l and (event.mod & pygame.KMOD_CTRL):
            self.__prompt_load()
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
        """Coloca el tile seleccionado en la celda clickeada."""
        if hasattr(event, 'pos'):
            mx, my = event.pos
        else:
            mx, my = pygame.mouse.get_pos()

        # Ignorar clics en la paleta de herramientas
        if my >= GRID_ROWS * CELL_SIZE:
            self.__handle_palette_click(mx, my)
            return

        cx = mx // CELL_SIZE
        cy = my // CELL_SIZE
        if 0 <= cx < GRID_COLS and 0 <= cy < GRID_ROWS:
            self.edit_cell(cx, cy, self.__selected_tile)

    def __handle_palette_click(self, mx, my):
        """Selecciona un tile desde la paleta en el HUD del editor."""
        palette_y = GRID_ROWS * CELL_SIZE + 8
        for i, tile in enumerate(TILE_ORDER):
            px = 10 + i * 44
            rect = pygame.Rect(px, palette_y, 36, 36)
            if rect.collidepoint(mx, my):
                self.__selected_tile = tile
                break

    def __clear_grid(self):
        """Limpia el tablero (preserva bordes)."""
        self.__grid = [[LEVEL_FREE for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.__init_borders()

    def __prompt_load(self):
        """Pide número de nivel y lo carga."""
        levels_dir = os.path.join(os.path.dirname(__file__), 'levels')
        # Cargar nivel 1 por defecto al presionar Ctrl+L
        path = os.path.join(levels_dir, 'level1.txt')
        if os.path.exists(path):
            self.load_level(path)

    def __ask_filename(self):
        """Retorna ruta por defecto para guardar."""
        levels_dir = os.path.join(os.path.dirname(__file__), 'levels')
        return os.path.join(levels_dir, 'level_nuevo.txt')

    def __show_message(self, msg):
        """Muestra un mensaje temporal."""
        self.__message = msg
        self.__message_timer = 120

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def __render_editor(self):
        """Dibuja el editor completo."""
        self.__screen.fill(COLOR_BG)

        # Cuadrícula con iconos representativos de cada elemento
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                tile = self.__grid[y][x]
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.__screen, (26, 26, 46), rect)
                pygame.draw.rect(self.__screen, (50, 50, 70), rect, 1)
                if tile != LEVEL_FREE:
                    self.__draw_icon(self.__screen, tile, rect)

        # Paleta de herramientas
        self.__render_palette()

        # Mensaje temporal
        if self.__message_timer > 0:
            self.__message_timer -= 1
            msg_surf = self.__font.render(self.__message, True, (255, 220, 100))
            self.__screen.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2,
                                          GRID_ROWS * CELL_SIZE - 24))

    def __render_palette(self):
        """Dibuja la paleta de tiles (con iconos) y los controles del editor."""
        palette_y = GRID_ROWS * CELL_SIZE
        pygame.draw.rect(self.__screen, (15, 15, 35),
                         (0, palette_y, SCREEN_WIDTH, SCREEN_HEIGHT - palette_y))

        for i, tile in enumerate(TILE_ORDER):
            px = 10 + i * 44
            py = palette_y + 8
            rect = pygame.Rect(px, py, 36, 36)
            # Fondo oscuro + icono representativo
            pygame.draw.rect(self.__screen, (26, 26, 46), rect)
            if tile != LEVEL_FREE:
                self.__draw_icon(self.__screen, tile, rect)
            # Borde (resaltado si está seleccionado)
            border = (255, 255, 0) if tile == self.__selected_tile else (100, 100, 120)
            pygame.draw.rect(self.__screen, border, rect, 2)
            # Tecla de acceso (1-8) en la esquina
            key_surf = self.__font_sm.render(str(i + 1), True, COLOR_WHITE)
            self.__screen.blit(key_surf, (px + 2, py + 1))

        # Nombre del tile seleccionado
        name = TILE_NAMES.get(self.__selected_tile, '')
        name_surf = self.__font.render(f"Seleccionado: {name}", True, (255, 220, 100))
        self.__screen.blit(name_surf, (372, palette_y + 6))

        # Instrucciones
        instructions = "ENTER:PROBAR  Ctrl+S:guardar  Ctrl+L:cargar  C:limpiar  ESC:salir"
        inst_surf = self.__font_sm.render(instructions, True, COLOR_GRAY)
        self.__screen.blit(inst_surf, (372, palette_y + 30))

    # ------------------------------------------------------------------
    # Iconos representativos de cada elemento (cuadrícula y paleta)
    # ------------------------------------------------------------------

    def __draw_icon(self, surf, tile, rect):
        """Dibuja el icono del `tile` dentro de `rect` (celda o casilla de paleta)."""
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
        """Muro: patrón de ladrillos."""
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
        """Tanque: silueta con orugas, cuerpo, torreta y cañón hacia arriba."""
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        dark = tuple(max(0, c - 70) for c in color)
        m = max(2, w // 6)
        # Orugas laterales
        pygame.draw.rect(surf, dark, (x + 1, y + m, m, h - 2 * m))
        pygame.draw.rect(surf, dark, (x + w - m - 1, y + m, m, h - 2 * m))
        # Cuerpo
        body = pygame.Rect(x + m, y + m, w - 2 * m, h - 2 * m)
        pygame.draw.rect(surf, color, body, border_radius=max(2, w // 12))
        pygame.draw.rect(surf, dark, body, 2, border_radius=max(2, w // 12))
        # Cañón hacia arriba
        bw = max(2, w // 9)
        pygame.draw.rect(surf, dark, (x + w // 2 - bw // 2, y + 1, bw, h // 2))
        # Torreta
        pygame.draw.circle(surf, dark, (x + w // 2, y + h // 2), max(2, w // 7))
        # Etiqueta de tipo (para enemigos)
        if label:
            f = self.__font if w > 28 else self.__font_sm
            t = f.render(label, True, (255, 255, 255))
            surf.blit(t, t.get_rect(center=(x + w // 2, y + int(h * 0.72))))

    def __icon_base(self, surf, rect, color, label):
        """Base/objetivo: núcleo circular con anillo y letra (A/B)."""
        cx, cy = rect.centerx, rect.centery
        r = min(rect.width, rect.height) // 2 - 3
        pygame.draw.circle(surf, color, (cx, cy), r)
        pygame.draw.circle(surf, (240, 240, 240), (cx, cy), r, 2)
        f = self.__font if rect.width > 28 else self.__font_sm
        t = f.render(label, True, (0, 0, 0))
        surf.blit(t, t.get_rect(center=(cx, cy)))
