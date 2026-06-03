# entities/enemy_tank.py - Tanque enemigo
#
# Arquitectura:
#   Prolog  → decide la acción (atacar/defender/emboscar),
#             calcula la ruta DFS, decide si disparar y en qué dirección.
#   Python  → crea el objeto, ejecuta el movimiento celda a celda,
#             llama a Prolog, renderiza.  No hace lógica de backend.

import pygame
from entities.tank import Tank
from constants import (
    ENEMY_STATS, ENEMY_COLORS,
    ENEMY_MOVE_INTERVAL, NEAR_DISTANCE,
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_DELTA,
    GRID_COLS, GRID_ROWS,
    ROLE_HUNTER, ROLE_DEFENDER,
    ROTATION_CW, ROTATION_CCW, DIR_OPPOSITE,
    CELL_SIZE
)
import logger

# Intervalos de recálculo por rol (ms)
_RECALC_HUNTER   = 1000   # el hunter actualiza ruta frecuentemente (el jugador se mueve)
_RECALC_DEFENDER = 1500   # el defensor recalcula con frecuencia para que la patrulla sea reactiva


class EnemyTank(Tank):
    """
    Tanque enemigo con dos roles:
      ROLE_HUNTER   – persigue y ataca al jugador; embosca si está lejos.
      ROLE_DEFENDER – custodia su objetivo asignado; ataca si el jugador se acerca.

    TODA la lógica de decisión (acción + ruta + disparo) proviene de Prolog.
    Python solo ejecuta las órdenes: mover el tanque celda a celda y disparar.
    Si Prolog no está disponible, un fallback BFS + heurística Manhattan replica
    el comportamiento para que el juego funcione sin SWI-Prolog instalado.
    """

    def __init__(self, x, y, tank_type, prolog_bridge=None, role=ROLE_HUNTER):
        stats = ENEMY_STATS[tank_type]
        super().__init__(
            x=x, y=y,
            health=stats['health'],
            speed=stats['speed'],
            bullet_damage=stats['damage'],
            color=ENEMY_COLORS[tank_type],
            bullet_speed=stats['bullet_speed']
        )
        self.__tank_type          = tank_type
        self.__role               = role
        self.__prolog_bridge      = prolog_bridge
        self.__assigned_objective = None   # objetivo PRIMARY asignado (solo para DEFENDER)
        self.__current_target     = None   # celda destino actual (x, y)
        self.__current_action     = None   # última acción Prolog: 'atacar'/'defender'/'emboscar'
        self.__current_path       = []     # lista de (x, y) devuelta por Prolog/BFS
        self.__path_index         = 0
        self.__last_move_time     = pygame.time.get_ticks()
        self.__last_recalc_time   = 0      # última vez que se consultó Prolog
        self.__shoot_cooldown     = 0
        self.__shoot_cooldown_max = 60     # ~1 s a 60 FPS
        self.__is_retreating          = False  # estado pasado a Prolog para histéresis
        self.__retreat_cooldown_until = 0      # timestamp: hasta cuándo cooldown activo

        self.__recalc_interval = (
            _RECALC_HUNTER if role == ROLE_HUNTER else _RECALC_DEFENDER
        )

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def get_role(self):
        return self.__role

    def get_tank_type(self):
        return self.__tank_type

    def assign_objective(self, objective):
        """Asigna el objetivo primario que este tanque debe custodiar."""
        self.__assigned_objective = objective

    # ------------------------------------------------------------------
    # Bucle principal de actualización
    # ------------------------------------------------------------------

    def update(self, board, player, objectives, current_time):
        """
        Actualiza el tanque: pide decisión a Prolog, ejecuta movimiento y disparo.
        Retorna Bullet si dispara, None en caso contrario.
        """
        bullet    = None
        ex, ey    = self.get_position()
        px, py    = player.get_position()
        ox, oy    = self.__get_objective_pos(player, objectives)
        role_atom = 'hunter' if self.__role == ROLE_HUNTER else 'defender'

        # ── 1. Recalcular decisión + ruta vía Prolog ──────────────────
        if current_time - self.__last_recalc_time >= self.__recalc_interval:
            self.__last_recalc_time = current_time
            self.__recalcular_ruta(board, ex, ey, px, py, ox, oy, role_atom)

        # ── 2. HUNTER: refrescar target en cada paso de movimiento ────
        #    (el jugador se mueve constantemente; sin esto el hunter sigue
        #     una ruta obsoleta hasta el próximo recálculo completo)
        # No forzar el target al jugador si el hunter decidió retroceder
        if self.__role == ROLE_HUNTER and self.__current_action != 'retroceder':
            self.__current_target = (px, py)

        # ── 3. Mover un paso cada ENEMY_MOVE_INTERVAL ─────────────────
        if current_time - self.__last_move_time >= ENEMY_MOVE_INTERVAL:
            self.__last_move_time = current_time
            self.__follow_path(board)

        # ── 4. Decidir disparo vía Prolog ──────────────────────────────
        if self.__shoot_cooldown <= 0:
            bullet = self.__decidir_disparo(board, player, ex, ey, px, py)

        if self.__shoot_cooldown > 0:
            self.__shoot_cooldown -= 1

        return bullet

    # ------------------------------------------------------------------
    # Decisión y ruta (Prolog → fallback BFS)
    # ------------------------------------------------------------------

    def __recalcular_ruta(self, board, ex, ey, px, py, ox, oy, role_atom):
        """
        Consulta a Prolog: acción estratégica + ruta.
        Si Prolog no responde o devuelve ruta vacía, usa fallback BFS.
        """
        if self.__prolog_bridge and self.__prolog_bridge.is_loaded():
            self.__prolog_bridge.update_board_facts(board, (px, py), (ex, ey))

            now            = pygame.time.get_ticks()
            cooldown_active = now < self.__retreat_cooldown_until

            # Python pasa a Prolog el estado: ¿estaba retrocediendo? ¿cooldown activo?
            # Prolog decide la acción y calcula la ruta óptima (BFS).
            resultado = self.__prolog_bridge.get_decision_and_path(
                ex, ey, px, py, ox, oy, role_atom, self.get_health(),
                self.__is_retreating, cooldown_active)

            if resultado:
                accion, path = resultado
                if not path:
                    logger.log_fallback_reason(
                        self.__tank_type, self.__role, (ex, ey),
                        "Prolog devolvió ruta vacía")
                else:
                    was_retreating        = self.__is_retreating
                    self.__is_retreating  = (accion == 'retroceder')

                    # Si acaba de terminar la retirada: activar cooldown de 8 s
                    if was_retreating and not self.__is_retreating:
                        self.__retreat_cooldown_until = now + 8000

                    # Ejecutar la decisión de Prolog sin modificarla
                    self.__current_action = accion
                    self.__current_path   = path
                    self.__path_index     = 0
                    if accion == 'atacar':
                        self.__current_target = (px, py)
                    elif accion == 'defender':
                        self.__current_target = (ox, oy)
                    elif accion == 'retroceder':
                        self.__current_target = path[-1] if path else (ex, ey)
                    else:
                        self.__current_target = ((ex + px) // 2, (ey + py) // 2)

                    logger.log_decision(
                        id(self), self.__tank_type, self.__role,
                        (ex, ey), accion, self.__current_target,
                        len(path), 'prolog'
                    )
                    return

        # Prolog no disponible o sin ruta → fallback BFS Python
        self.__fallback_ruta_bfs(board, ex, ey, px, py, ox, oy)

    def __fallback_ruta_bfs(self, board, ex, ey, px, py, ox, oy):
        """
        Fallback cuando Prolog no está disponible.
        Replica las mismas reglas de decisión de Prolog con BFS Python.
        """
        now             = pygame.time.get_ticks()
        cooldown_active = now < self.__retreat_cooldown_until
        dist_jugador    = self.__manhattan(ex, ey, px, py)
        umbral_retirada = 6 if (self.__is_retreating and not cooldown_active) else 2

        if not cooldown_active and self.get_health() <= 1 and dist_jugador <= umbral_retirada:
            was = self.__is_retreating
            self.__is_retreating  = True
            self.__current_action = 'retroceder'
            target = self.__fallback_posicion_retirada(px, py, board)
            self.__current_target = target
            self.__current_path   = self.__bfs_path(ex, ey, target[0], target[1], board)
            self.__path_index     = 0
            logger.log_decision(id(self), self.__tank_type, self.__role,
                                 (ex, ey), 'retroceder', target,
                                 len(self.__current_path), 'bfs')
            return

        if self.__is_retreating:
            self.__retreat_cooldown_until = now + 8000
        self.__is_retreating = False

        if self.__role == ROLE_HUNTER or dist_jugador <= 3:
            self.__current_action = 'atacar'
            target = (px, py)
        else:
            self.__current_action = 'defender'
            target = self.__fallback_posicion_defensa(ox, oy, px, py, board)

        self.__current_target = target
        self.__current_path   = self.__bfs_path(ex, ey, target[0], target[1], board)
        self.__path_index     = 0
        logger.log_decision(id(self), self.__tank_type, self.__role,
                             (ex, ey), self.__current_action, target,
                             len(self.__current_path), 'bfs')

    def __fallback_posicion_defensa(self, ox, oy, px, py, board):
        """
        Replica posicion_defensa de Prolog.
        NUNCA devuelve la celda del objetivo: los tanques no pueden pararse en él.
        """
        diff_x = px - ox
        diff_y = py - oy

        # Celda preferida: adyacente al objetivo en dirección al jugador
        if abs(diff_x) >= abs(diff_y):
            dx = 1 if diff_x >= 0 else -1
            candidate = (ox + dx, oy)
        else:
            dy = 1 if diff_y >= 0 else -1
            candidate = (ox, oy + dy)

        cx, cy = candidate
        if (0 <= cx < GRID_COLS and 0 <= cy < GRID_ROWS
                and board.is_walkable(cx, cy)):
            return candidate

        # Celda preferida bloqueada: cualquier adyacente libre
        for d in [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]:
            ddx, ddy = DIR_DELTA[d]
            nx, ny = ox + ddx, oy + ddy
            if (0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS
                    and board.is_walkable(nx, ny)):
                return (nx, ny)

        # Sin celdas adyacentes libres: quedarse en la posición actual del tanque
        return self.get_position()

    def __fallback_posicion_retirada(self, px, py, board):
        """
        Replica posicion_retirada de Prolog: celda adyacente transitable que
        MAXIMIZA la distancia al jugador (el tanque se aleja un paso).
        """
        ex, ey = self.get_position()
        mejor = None
        mejor_dist = -1
        for d in [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]:
            ddx, ddy = DIR_DELTA[d]
            nx, ny = ex + ddx, ey + ddy
            if (0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS
                    and board.is_walkable(nx, ny)):
                dist = self.__manhattan(nx, ny, px, py)
                if dist > mejor_dist:
                    mejor_dist = dist
                    mejor = (nx, ny)
        return mejor if mejor else (ex, ey)

    # ------------------------------------------------------------------
    # Decisión de disparo (Prolog → fallback Python)
    # ------------------------------------------------------------------

    def __decidir_disparo(self, board, player, ex, ey, px, py):
        """
        Pregunta a Prolog si debe disparar y en qué dirección.
        Si Prolog no está disponible usa fallback Python (línea de visión geométrica).
        Retorna Bullet o None.
        """
        if self.__prolog_bridge and self.__prolog_bridge.is_loaded():
            # Actualizar posición del jugador antes de consultar (operación ligera)
            self.__prolog_bridge.update_player_position((px, py))
            debe, direccion = self.__prolog_bridge.get_shoot_decision(
                ex, ey, px, py)
            source = 'prolog'
        else:
            debe, direccion = self.__fallback_shoot_check(player, board)
            source = 'bfs'

        logger.log_shoot(
            id(self), self.__tank_type, self.__role,
            (ex, ey), debe, direccion, source
        )

        if debe and direccion:
            self._set_direction(direccion)
            self.__shoot_cooldown = self.__shoot_cooldown_max
            return self.shoot()

        return None

    def __fallback_shoot_check(self, player, board):
        """
        Fallback: replica debe_disparar + direccion_disparo de decisions.pl.
        """
        ex, ey = self.get_position()
        px, py = player.get_position()
        dist   = self.__manhattan(ex, ey, px, py)

        if dist > NEAR_DISTANCE:
            return (False, None)

        # Misma columna → verificar muros entre ellos
        if ex == px:
            for cy in range(min(ey, py) + 1, max(ey, py)):
                if board.is_wall(ex, cy):
                    return (False, None)
            return (True, DIR_DOWN if py > ey else DIR_UP)

        # Misma fila → verificar muros entre ellos
        if ey == py:
            for cx in range(min(ex, px) + 1, max(ex, px)):
                if board.is_wall(cx, ey):
                    return (False, None)
            return (True, DIR_RIGHT if px > ex else DIR_LEFT)

        return (False, None)

    # ------------------------------------------------------------------
    # Obtención de la posición del objetivo
    # ------------------------------------------------------------------

    def __get_objective_pos(self, player, objectives):
        """
        Para DEFENDER: devuelve el objetivo asignado (o el más cercano si fue destruido).
        Para HUNTER:   devuelve siempre la posición del jugador.
        """
        if self.__role == ROLE_HUNTER:
            return player.get_position()

        # Objetivo asignado aún vivo
        if (self.__assigned_objective
                and not self.__assigned_objective.is_destroyed()):
            return self.__assigned_objective.get_position()

        # Sin asignación o destruido → buscar el más cercano
        ex, ey = self.get_position()
        vivos = [o for o in objectives if not o.is_destroyed()] if objectives else []
        if vivos:
            mas_cercano = min(
                vivos,
                key=lambda o: self.__manhattan(
                    ex, ey, o.get_position()[0], o.get_position()[1])
            )
            return mas_cercano.get_position()

        return player.get_position()

    # ------------------------------------------------------------------
    # Ejecución de movimiento (Python puro: sin lógica de juego)
    # ------------------------------------------------------------------

    def __follow_path(self, board):
        """
        Avanza un paso siguiendo la ruta devuelta por Prolog.
        Si la ruta está agotada o el paso falla, recalcula con BFS inmediato
        y luego intenta moverse hacia el target por Manhattan.
        """
        target = self.__current_target

        # Ya llegamos al destino: no hay que moverse
        if target and self.get_position() == target:
            return

        # Sin ruta: calcular BFS inmediato y continuar
        if not self.__current_path or self.__path_index >= len(self.__current_path):
            if target:
                ex, ey = self.get_position()
                self.__current_path = self.__bfs_path(
                    ex, ey, target[0], target[1], board)
                self.__path_index = 0
            if not self.__current_path:
                self.__try_unstuck(board)
            return

        tx, ty = self.__current_path[self.__path_index]
        ex, ey = self.get_position()

        # La celda actual ya es el paso: saltar
        if (ex, ey) == (tx, ty):
            self.__path_index += 1
            return

        direction = self.__direction_to(ex, ey, tx, ty)
        moved = self.move(direction, board)

        if moved:
            self.__path_index += 1
        else:
            # Paso bloqueado (otro tanque, actualización asíncrona, etc.)
            # Recalcular BFS desde posición actual e intentar el primer paso
            if target:
                ex2, ey2 = self.get_position()
                self.__current_path = self.__bfs_path(
                    ex2, ey2, target[0], target[1], board)
                self.__path_index = 0
                if self.__current_path:
                    nx, ny = self.__current_path[0]
                    if self.move(self.__direction_to(ex2, ey2, nx, ny), board):
                        self.__path_index = 1
                        return
            self.__current_path = []
            self.__try_unstuck(board)

    def __try_unstuck(self, board):
        """
        Mueve el tanque en la dirección que más lo acerca al target (Manhattan).
        Si no hay target, prueba CW → CCW → opuesto (rotación sistemática).
        """
        target = self.__current_target
        if target:
            ex, ey = self.get_position()
            tx, ty = target
            dirs = sorted(
                [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT],
                key=lambda d: self.__manhattan(
                    ex + DIR_DELTA[d][0],
                    ey + DIR_DELTA[d][1],
                    tx, ty
                )
            )
        else:
            cur  = self.get_direction()
            dirs = [ROTATION_CW[cur], ROTATION_CCW[cur], DIR_OPPOSITE[cur], cur]

        for d in dirs:
            if self.move(d, board):
                return

    # ------------------------------------------------------------------
    # BFS (fallback cuando Prolog no está disponible)
    # ------------------------------------------------------------------

    def __bfs_path(self, sx, sy, gx, gy, board):
        """BFS garantiza encontrar el camino si existe."""
        from collections import deque
        queue   = deque([(sx, sy, [])])
        visited = {(sx, sy)}
        while queue:
            cx, cy, path = queue.popleft()
            if cx == gx and cy == gy:
                return path
            for d in [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]:
                ddx, ddy = DIR_DELTA[d]
                nx, ny   = cx + ddx, cy + ddy
                if (0 <= nx < GRID_COLS and 0 <= ny < GRID_ROWS
                        and board.is_walkable(nx, ny)
                        and (nx, ny) not in visited):
                    visited.add((nx, ny))
                    queue.append((nx, ny, path + [(nx, ny)]))
        return []

    # ------------------------------------------------------------------
    # Helpers de geometría
    # ------------------------------------------------------------------

    def __manhattan(self, x1, y1, x2, y2):
        return abs(x1 - x2) + abs(y1 - y2)

    def __direction_to(self, ex, ey, tx, ty):
        dx, dy = tx - ex, ty - ey
        if dx > 0:  return DIR_RIGHT
        if dx < 0:  return DIR_LEFT
        if dy > 0:  return DIR_DOWN
        return DIR_UP

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def render(self, surface):
        """Dibuja el tanque con indicador visual de rol."""
        self._draw_tank(surface, self._color)

        x,  y  = self.get_position()
        px, py = x * CELL_SIZE, y * CELL_SIZE

        if self.__role == ROLE_HUNTER:
            # Rombo rojo → persigue al jugador
            cx = px + CELL_SIZE - 7
            cy = py + 7
            pts = [(cx, cy - 5), (cx + 4, cy), (cx, cy + 5), (cx - 4, cy)]
            import pygame as _pg
            _pg.draw.polygon(surface, (255, 60, 60), pts)
        else:
            # Cuadrado azul → defiende objetivos
            import pygame as _pg
            _pg.draw.rect(surface, (60, 140, 255),
                          _pg.Rect(px + CELL_SIZE - 12, py + 3, 8, 8))
            _pg.draw.rect(surface, (180, 220, 255),
                          _pg.Rect(px + CELL_SIZE - 12, py + 3, 8, 8), 1)
