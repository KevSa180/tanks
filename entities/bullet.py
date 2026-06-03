# entities/bullet.py - Proyectil disparado por tanques

import pygame
from constants import (
    CELL_SIZE, DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT,
    DIR_DELTA, GRID_COLS, GRID_ROWS, COLOR_BULLET, HUD_HEIGHT
)


class Bullet:
    """Proyectil que se mueve en línea recta hasta impactar o salir del mapa."""

    def __init__(self, cell_x, cell_y, direction, speed, damage, owner_type):
        # Posición en píxeles (centro de la celda)
        self.__px = cell_x * CELL_SIZE + CELL_SIZE // 2
        self.__py = cell_y * CELL_SIZE + CELL_SIZE // 2
        self.__direction = direction
        self.__speed = speed
        self.__damage = damage
        self.__owner_type = owner_type  # 'PLAYER' o 'ENEMY'
        self.__active = True
        self.__radius = 4

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------

    def update(self):
        """Mueve la bala en su dirección. La desactiva si sale del mapa."""
        dx, dy = DIR_DELTA[self.__direction]
        self.__px += dx * self.__speed
        self.__py += dy * self.__speed

        # Desactivar si sale de los límites del tablero
        max_x = GRID_COLS * CELL_SIZE
        max_y = GRID_ROWS * CELL_SIZE
        if self.__px < 0 or self.__px > max_x or self.__py < 0 or self.__py > max_y:
            self.__active = False

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def get_position(self):
        """Retorna la posición en píxeles (px, py)."""
        return (self.__px, self.__py)

    def get_cell_position(self):
        """Retorna la posición aproximada en celdas de la cuadrícula."""
        return (int(self.__px // CELL_SIZE), int(self.__py // CELL_SIZE))

    def get_damage(self):
        return self.__damage

    def is_player_bullet(self):
        return self.__owner_type == 'PLAYER'

    def is_active(self):
        return self.__active

    def deactivate(self):
        """Marca la bala como inactiva (tras colisión)."""
        self.__active = False

    def get_rect(self):
        """Retorna un pygame.Rect para detección de colisiones."""
        return pygame.Rect(
            self.__px - self.__radius,
            self.__py - self.__radius,
            self.__radius * 2,
            self.__radius * 2
        )

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def render(self, surface):
        """Dibuja la bala como un círculo blanco con brillo."""
        if not self.__active:
            return
        # Brillo exterior
        pygame.draw.circle(surface, (180, 180, 180),
                           (int(self.__px), int(self.__py)), self.__radius + 2)
        # Núcleo blanco
        pygame.draw.circle(surface, COLOR_BULLET,
                           (int(self.__px), int(self.__py)), self.__radius)
