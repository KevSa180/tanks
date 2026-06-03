# entities/objective.py - Objetivos que el jugador debe defender y los enemigos destruir

import pygame
from constants import (
    CELL_SIZE, OBJ_TYPE_A, OBJ_TYPE_B, OBJ_STATS,
    COLOR_OBJ_A, COLOR_OBJ_B
)

OBJ_COLORS = {
    OBJ_TYPE_A: COLOR_OBJ_A,
    OBJ_TYPE_B: COLOR_OBJ_B,
}


class Objective:
    """Representa un objetivo en el mapa que tiene salud y puntos."""

    def __init__(self, x, y, objective_type):
        # Atributos privados
        self.__x = x
        self.__y = y
        self.__objective_type = objective_type
        stats = OBJ_STATS[objective_type]
        self.__health = stats['health']
        self.__max_health = stats['health']
        self.__points_value = stats['points']
        self.__is_destroyed = False
        self.__color = OBJ_COLORS[objective_type]
        self.__flash_timer = 0  # efecto visual de daño

    # ------------------------------------------------------------------
    # Combate
    # ------------------------------------------------------------------

    def take_damage(self, damage):
        """Resta vida al objetivo. Retorna True si fue destruido."""
        if self.__is_destroyed:
            return False
        self.__health -= damage
        self.__flash_timer = 10  # frames de flash rojo
        if self.__health <= 0:
            self.__health = 0
            self.__is_destroyed = True
            return True
        return False

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def is_destroyed(self):
        return self.__is_destroyed

    def get_position(self):
        return (self.__x, self.__y)

    def get_points(self):
        return self.__points_value

    def get_type(self):
        return self.__objective_type

    def get_health(self):
        return self.__health

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def render(self, surface):
        """Dibuja el objetivo como un cuadrado con símbolo y barra de vida."""
        if self.__is_destroyed:
            return

        # Efecto de flash al recibir daño
        if self.__flash_timer > 0:
            color = (255, 80, 80)
            self.__flash_timer -= 1
        else:
            color = self.__color

        px = self.__x * CELL_SIZE
        py = self.__y * CELL_SIZE
        margin = 4

        # Cuerpo principal
        body = pygame.Rect(px + margin, py + margin,
                           CELL_SIZE - margin * 2, CELL_SIZE - margin * 2)
        pygame.draw.rect(surface, color, body)

        # Borde blanco
        pygame.draw.rect(surface, (220, 220, 220), body, 2)

        # Símbolo de tipo
        font = pygame.font.SysFont('monospace', 16, bold=True)
        label = 'A' if self.__objective_type == OBJ_TYPE_A else 'B'
        text = font.render(label, True, (0, 0, 0))
        surface.blit(text, (px + CELL_SIZE // 2 - 5, py + CELL_SIZE // 2 - 8))

        # Barra de vida
        bar_w = CELL_SIZE - margin * 2
        bar_h = 4
        bar_x = px + margin
        bar_y = py + CELL_SIZE - margin - bar_h
        # Fondo rojo
        pygame.draw.rect(surface, (180, 0, 0),
                         (bar_x, bar_y, bar_w, bar_h))
        # Vida restante en verde
        if self.__max_health > 0:
            fill = int(bar_w * self.__health / self.__max_health)
            pygame.draw.rect(surface, (0, 220, 0),
                             (bar_x, bar_y, fill, bar_h))
