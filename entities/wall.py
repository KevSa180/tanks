# entities/wall.py - Obstáculo indestructible en el mapa

import pygame
from constants import CELL_SIZE, COLOR_WALL, COLOR_WALL_BORDER


class Wall:
    """Muro que bloquea el movimiento y las balas."""

    def __init__(self, x, y, is_border=False):
        # Atributos privados
        self.__x = x
        self.__y = y
        self.__is_border = is_border

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def get_position(self):
        """Retorna (x, y) en coordenadas de celda."""
        return (self.__x, self.__y)

    def is_border(self):
        """Retorna True si este muro es parte del borde del mapa."""
        return self.__is_border

    def get_rect(self):
        """Retorna el pygame.Rect que ocupa este muro."""
        return pygame.Rect(
            self.__x * CELL_SIZE,
            self.__y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def render(self, surface):
        """Dibuja el muro con textura de ladrillos simple."""
        px = self.__x * CELL_SIZE
        py = self.__y * CELL_SIZE

        # Color base
        color = COLOR_WALL_BORDER if self.__is_border else COLOR_WALL
        pygame.draw.rect(surface, color,
                         (px, py, CELL_SIZE, CELL_SIZE))

        # Patrón de ladrillos
        dark = tuple(max(0, c - 20) for c in color)
        light = tuple(min(255, c + 20) for c in color)

        # Líneas horizontales del ladrillo
        for row in range(0, CELL_SIZE, CELL_SIZE // 3):
            pygame.draw.line(surface, dark,
                             (px, py + row), (px + CELL_SIZE, py + row), 1)

        # Líneas verticales (alternadas por fila)
        mid = CELL_SIZE // 2
        pygame.draw.line(surface, dark,
                         (px + mid, py), (px + mid, py + CELL_SIZE // 3), 1)
        pygame.draw.line(surface, dark,
                         (px, py + CELL_SIZE // 3),
                         (px, py + 2 * CELL_SIZE // 3), 1)
        pygame.draw.line(surface, dark,
                         (px + mid, py + CELL_SIZE // 3),
                         (px + mid, py + 2 * CELL_SIZE // 3), 1)

        # Borde exterior
        pygame.draw.rect(surface, dark,
                         (px, py, CELL_SIZE, CELL_SIZE), 1)
