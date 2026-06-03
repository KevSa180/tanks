# board.py - Tablero de juego: gestiona entidades y colisiones

import pygame
import random
from constants import (
    GRID_COLS, GRID_ROWS, CELL_SIZE,
    LEVEL_WALL, LEVEL_FREE, LEVEL_PLAYER,
    LEVEL_OBJ_A, LEVEL_OBJ_B,
    LEVEL_ENEMY1, LEVEL_ENEMY2, LEVEL_ENEMY3,
    OBJ_TYPE_A, OBJ_TYPE_B,
    ENEMY_LIGHT, ENEMY_MEDIUM, ENEMY_HEAVY,
    COLOR_BG, SCORE_KILL_LIGHT, SCORE_KILL_MEDIUM, SCORE_KILL_HEAVY,
    LEVEL_CONFIGS
)
from entities.wall import Wall
from entities.objective import Objective
from entities.enemy_tank import EnemyTank
from constants import ROLE_HUNTER, ROLE_DEFENDER


# Puntos por destruir cada tipo de enemigo
ENEMY_SCORE = {
    ENEMY_LIGHT: SCORE_KILL_LIGHT,
    ENEMY_MEDIUM: SCORE_KILL_MEDIUM,
    ENEMY_HEAVY: SCORE_KILL_HEAVY,
}


class Board:
    """Mantiene el estado del tablero y gestiona todas las interacciones."""

    def __init__(self):
        # Cuadrícula interna: cada celda es 'W' (muro) o '.' (libre)
        self.__grid = [['.' for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.__walls = []        # lista de objetos Wall
        self.__objectives = []   # lista de objetos Objective
        self.__enemies = []      # lista de objetos EnemyTank
        self.__bullets = []      # lista de objetos Bullet
        self.__level = 0
        self.__player_start = (1, 1)  # posición inicial del jugador
        self.__sound_events = []  # eventos de sonido del último check_collisions

    # ------------------------------------------------------------------
    # Carga de nivel
    # ------------------------------------------------------------------

    def load_level(self, level_number, prolog_bridge=None):
        """Genera el nivel con posiciones aleatorias y cantidades predefinidas."""
        self.__level = level_number
        self.__walls = []
        self.__objectives = []
        self.__enemies = []
        self.__bullets = []
        self.__grid = [['.' for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

        grid_data = self.__generate_level(level_number)
        self.__build_from_grid(grid_data, prolog_bridge)

    def load_custom_level(self, grid_lines, prolog_bridge=None):
        """
        Carga un nivel PERSONALIZADO desde una grilla de texto (lista de
        strings, una por fila) creada en el editor.

        No toca los niveles normales ni LEVEL_CONFIGS: solo construye las
        entidades a partir de la grilla recibida.
        """
        self.__level = 0
        self.__walls = []
        self.__objectives = []
        self.__enemies = []
        self.__bullets = []
        self.__grid = [['.' for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

        # Normalizar a una grilla fija GRID_ROWS x GRID_COLS de caracteres
        grid_data = []
        for y in range(GRID_ROWS):
            row = grid_lines[y] if y < len(grid_lines) else ''
            grid_data.append([
                (row[x] if x < len(row) else LEVEL_FREE)
                for x in range(GRID_COLS)
            ])

        self.__build_from_grid(grid_data, prolog_bridge)

    def __generate_level(self, level_number):
        """
        Genera el mapa del nivel de forma aleatoria usando las cantidades
        definidas en LEVEL_CONFIGS. El layout cambia en cada partida pero
        siempre contiene exactamente los mismos tipos y cantidades de entidades.
        """
        config = LEVEL_CONFIGS.get(level_number, LEVEL_CONFIGS[3])

        grid = [['.' for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

        # Bordes siempre son muros
        for x in range(GRID_COLS):
            grid[0][x] = 'W'
            grid[GRID_ROWS - 1][x] = 'W'
        for y in range(GRID_ROWS):
            grid[y][0] = 'W'
            grid[y][GRID_COLS - 1] = 'W'

        # Jugador fijo en esquina superior izquierda
        grid[1][1] = 'P'

        # Zona protegida alrededor del jugador (no se colocan muros ni entidades)
        safe_zone = {
            (1 + dx, 1 + dy)
            for dy in range(-2, 4)
            for dx in range(-1, 5)
            if 0 < 1 + dx < GRID_COLS - 1 and 0 < 1 + dy < GRID_ROWS - 1
        }

        # Colocar segmentos de muros internos (horizontal o vertical, 3-5 celdas)
        for _ in range(config['wall_segments']):
            for _attempt in range(60):
                if random.random() < 0.5:
                    length = random.randint(3, 5)
                    wx = random.randint(1, GRID_COLS - 2 - length)
                    wy = random.randint(1, GRID_ROWS - 2)
                    cells = [(wx + i, wy) for i in range(length)]
                else:
                    length = random.randint(3, 5)
                    wx = random.randint(1, GRID_COLS - 2)
                    wy = random.randint(1, GRID_ROWS - 2 - length)
                    cells = [(wx, wy + i) for i in range(length)]

                if all(
                    (cx, cy) not in safe_zone and grid[cy][cx] == '.'
                    for cx, cy in cells
                ):
                    for cx, cy in cells:
                        grid[cy][cx] = 'W'
                    break

        # Celdas interiores libres que están fuera de la zona segura del jugador
        def free_cells():
            return [
                (x, y)
                for y in range(1, GRID_ROWS - 1)
                for x in range(1, GRID_COLS - 1)
                if grid[y][x] == '.' and (x, y) not in safe_zone
            ]

        used = set()

        # Colocar objetivos primero (más alejados es mejor)
        obj_char = {OBJ_TYPE_A: 'A', OBJ_TYPE_B: 'B'}
        for obj_type, count in config['objectives'].items():
            available = [c for c in free_cells() if c not in used]
            # Preferir celdas más alejadas del jugador
            available.sort(key=lambda c: -(abs(c[0] - 1) + abs(c[1] - 1)))
            for i in range(min(count, len(available))):
                # Elegir aleatoriamente entre las más lejanas (top 40%)
                pool = available[:max(1, len(available) * 2 // 5)]
                pos = random.choice(pool)
                grid[pos[1]][pos[0]] = obj_char[obj_type]
                used.add(pos)
                available.remove(pos)

        # Colocar enemigos
        enemy_char = {ENEMY_LIGHT: '1', ENEMY_MEDIUM: '2', ENEMY_HEAVY: '3'}
        for enemy_type, count in config['enemies'].items():
            available = [c for c in free_cells() if c not in used]
            for _ in range(min(count, len(available))):
                pos = random.choice(available)
                grid[pos[1]][pos[0]] = enemy_char[enemy_type]
                used.add(pos)
                available.remove(pos)

        return grid

    def __build_from_grid(self, grid_data, prolog_bridge):
        """Construye las entidades a partir de los datos de la cuadrícula."""
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                ch = grid_data[y][x]

                if ch == LEVEL_WALL:
                    is_border = (x == 0 or x == GRID_COLS - 1 or
                                 y == 0 or y == GRID_ROWS - 1)
                    self.__walls.append(Wall(x, y, is_border))
                    self.__grid[y][x] = 'W'

                elif ch == LEVEL_PLAYER:
                    self.__player_start = (x, y)
                    self.__grid[y][x] = '.'

                elif ch == LEVEL_OBJ_A:
                    self.__objectives.append(Objective(x, y, OBJ_TYPE_A))
                    self.__grid[y][x] = '.'

                elif ch == LEVEL_OBJ_B:
                    self.__objectives.append(Objective(x, y, OBJ_TYPE_B))
                    self.__grid[y][x] = '.'

                elif ch == LEVEL_ENEMY1:
                    role = ROLE_HUNTER if len(self.__enemies) == 0 else ROLE_DEFENDER
                    self.__enemies.append(EnemyTank(x, y, ENEMY_LIGHT, prolog_bridge, role))
                    self.__grid[y][x] = '.'

                elif ch == LEVEL_ENEMY2:
                    role = ROLE_HUNTER if len(self.__enemies) == 0 else ROLE_DEFENDER
                    self.__enemies.append(EnemyTank(x, y, ENEMY_MEDIUM, prolog_bridge, role))
                    self.__grid[y][x] = '.'

                elif ch == LEVEL_ENEMY3:
                    role = ROLE_HUNTER if len(self.__enemies) == 0 else ROLE_DEFENDER
                    self.__enemies.append(EnemyTank(x, y, ENEMY_HEAVY, prolog_bridge, role))
                    self.__grid[y][x] = '.'

        # Asignar un defensor específico a cada objetivo primario
        self.__assign_guardians()

    def __assign_guardians(self):
        """
        Cumple el requisito: "solo debe existir un tanque que cuide cada objetivo".
        Asigna el defensor más cercano a cada objetivo TYPE_A de forma 1-a-1.
        """
        defensores = [e for e in self.__enemies if e.get_role() == ROLE_DEFENDER]
        primarios  = [o for o in self.__objectives if o.get_type() == OBJ_TYPE_A]

        asignados = set()
        for obj in primarios:
            ox, oy = obj.get_position()
            disponibles = [d for d in defensores if id(d) not in asignados]
            if not disponibles:
                break
            guardian = min(
                disponibles,
                key=lambda d: (abs(d.get_position()[0] - ox)
                               + abs(d.get_position()[1] - oy))
            )
            guardian.assign_objective(obj)
            asignados.add(id(guardian))

    # ------------------------------------------------------------------
    # Consultas de celda
    # ------------------------------------------------------------------

    def is_walkable(self, x, y):
        """
        Retorna True si la celda es transitable para tanques.
        Un muro o un objetivo vivo bloquean el paso: nunca puede haber
        más de un objeto en la misma cuadrícula.
        """
        if x < 0 or x >= GRID_COLS or y < 0 or y >= GRID_ROWS:
            return False
        if self.__grid[y][x] == 'W':
            return False
        for obj in self.__objectives:
            if not obj.is_destroyed():
                ox, oy = obj.get_position()
                if ox == x and oy == y:
                    return False
        return True

    def is_wall(self, x, y):
        """Retorna True si la celda es un muro."""
        if x < 0 or x >= GRID_COLS or y < 0 or y >= GRID_ROWS:
            return True
        return self.__grid[y][x] == 'W'

    def get_all_free_cells(self):
        """Retorna lista de (x, y) de todas las celdas libres."""
        free = []
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                if self.__grid[y][x] != 'W':
                    free.append((x, y))
        return free

    def get_player_start(self):
        return self.__player_start

    # ------------------------------------------------------------------
    # Gestión de balas
    # ------------------------------------------------------------------

    def add_bullet(self, bullet):
        """Agrega una bala al tablero."""
        if bullet is not None:
            self.__bullets.append(bullet)

    def update_bullets(self):
        """Mueve todas las balas activas."""
        for bullet in self.__bullets:
            if bullet.is_active():
                bullet.update()
        # Eliminar balas inactivas
        self.__bullets = [b for b in self.__bullets if b.is_active()]

    # ------------------------------------------------------------------
    # Detección de colisiones
    # ------------------------------------------------------------------

    def check_collisions(self, player):
        """
        Verifica todas las colisiones y aplica daño.
        Retorna (score_gained, player_hit, enemy_destroyed_primary, sound_events).
        sound_events: lista de strings ('explosion', 'base_destroy') ocurridos.
        """
        self.__sound_events = []
        score_gained = 0
        player_hit = False

        # Colisiones bala–muro
        self.__check_bullet_wall_collision()

        # Colisiones bala–tanque
        killed_score, p_hit = self.__check_bullet_tank_collision(player)
        score_gained += killed_score
        player_hit = p_hit

        # Colisiones bala–objetivo (jugador y enemigos)
        obj_score, enemy_destroyed_primary = self.__check_bullet_objective_collision()
        score_gained += obj_score

        return score_gained, player_hit, enemy_destroyed_primary, self.__sound_events

    def __check_bullet_wall_collision(self):
        """Desactiva balas que impactan muros."""
        wall_set = {w.get_position() for w in self.__walls}
        for bullet in self.__bullets:
            if bullet.is_active():
                bx, by = bullet.get_cell_position()
                if (bx, by) in wall_set:
                    bullet.deactivate()

    def __check_bullet_tank_collision(self, player):
        """Aplica daño a tanques impactados. Retorna (score, player_was_hit)."""
        score = 0
        player_hit = False
        px, py = player.get_position()

        for bullet in self.__bullets:
            if not bullet.is_active():
                continue

            bx, by = bullet.get_cell_position()

            # Bala enemiga → jugador
            if not bullet.is_player_bullet() and (bx, by) == (px, py):
                killed = player.take_damage(bullet.get_damage())
                bullet.deactivate()
                player_hit = True
                self.__sound_events.append('explosion')  # tanque del jugador

            # Bala del jugador → enemigos
            elif bullet.is_player_bullet():
                for enemy in self.__enemies:
                    if not enemy.is_alive():
                        continue
                    ex, ey = enemy.get_position()
                    if (bx, by) == (ex, ey):
                        killed = enemy.take_damage(bullet.get_damage())
                        bullet.deactivate()
                        if killed:
                            score += ENEMY_SCORE.get(enemy.get_tank_type(), 100)
                            self.__sound_events.append('explosion')  # tanque enemigo
                        break

        # Eliminar enemigos muertos
        self.__enemies = [e for e in self.__enemies if e.is_alive()]
        return score, player_hit

    def __check_bullet_objective_collision(self):
        """
        Aplica daño a objetivos impactados por cualquier bala.
        Retorna (score_gained, enemy_destroyed_primary).
        """
        from constants import OBJ_TYPE_A
        score_gained = 0
        enemy_destroyed_primary = False
        for bullet in self.__bullets:
            if not bullet.is_active():
                continue
            bx, by = bullet.get_cell_position()
            for obj in self.__objectives:
                if obj.is_destroyed():
                    continue
                ox, oy = obj.get_position()
                if (bx, by) == (ox, oy):
                    destroyed = obj.take_damage(bullet.get_damage())
                    bullet.deactivate()
                    if destroyed:
                        self.__sound_events.append('base_destroy')
                        if bullet.is_player_bullet():
                            score_gained += obj.get_points()
                        elif obj.get_type() == OBJ_TYPE_A:
                            enemy_destroyed_primary = True
                    break
        return score_gained, enemy_destroyed_primary

    # ------------------------------------------------------------------
    # Estado del nivel
    # ------------------------------------------------------------------

    def all_objectives_destroyed(self):
        """Retorna True si todos los objetivos TYPE_A han sido destruidos (condición de victoria)."""
        from constants import OBJ_TYPE_A
        primary = [o for o in self.__objectives if o.get_type() == OBJ_TYPE_A]
        return len(primary) > 0 and all(o.is_destroyed() for o in primary)

    def primary_objectives_intact(self):
        """Retorna lista de objetivos TYPE_A aún no destruidos."""
        from constants import OBJ_TYPE_A
        return [o for o in self.__objectives
                if o.get_type() == OBJ_TYPE_A and not o.is_destroyed()]

    def all_enemies_defeated(self):
        """Retorna True si no quedan enemigos vivos."""
        return len(self.__enemies) == 0

    def objectives_intact(self):
        """Retorna lista de objetivos que aún no han sido destruidos."""
        return [o for o in self.__objectives if not o.is_destroyed()]

    # ------------------------------------------------------------------
    # Accesores para el controlador
    # ------------------------------------------------------------------

    def get_enemies(self):
        return self.__enemies

    def get_objectives(self):
        return self.__objectives

    def get_bullets(self):
        return self.__bullets

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def render(self, surface):
        """Dibuja todas las capas del tablero en orden."""
        # Fondo
        surface.fill(COLOR_BG)

        # Cuadrícula sutil
        grid_color = (30, 30, 50)
        for x in range(0, GRID_COLS * CELL_SIZE, CELL_SIZE):
            pygame.draw.line(surface, grid_color, (x, 0), (x, GRID_ROWS * CELL_SIZE))
        for y in range(0, GRID_ROWS * CELL_SIZE, CELL_SIZE):
            pygame.draw.line(surface, grid_color, (0, y), (GRID_COLS * CELL_SIZE, y))

        # Muros
        for wall in self.__walls:
            wall.render(surface)

        # Objetivos
        for obj in self.__objectives:
            obj.render(surface)

        # Balas
        for bullet in self.__bullets:
            bullet.render(surface)
