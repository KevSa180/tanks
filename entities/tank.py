# entities/tank.py - Clase abstracta base para todos los tanques

import pygame
from abc import ABC, abstractmethod
from constants import (
    CELL_SIZE, DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT,
    DIR_DELTA, GRID_COLS, GRID_ROWS
)


class Tank(ABC):
    """Clase abstracta que define la interfaz común de todos los tanques."""

    def __init__(self, x, y, health, speed, bullet_damage, color, bullet_speed):
        # Atributos privados de posición y estado
        self.__x = x
        self.__y = y
        self.__health = health
        self.__direction = DIR_UP
        self.__speed = speed
        self.__bullet_damage = bullet_damage
        # Atributos protegidos (accesibles por subclases)
        self._color = color
        self._bullet_speed = bullet_speed

    # ------------------------------------------------------------------
    # Métodos privados de validación
    # ------------------------------------------------------------------

    def __validate_position(self, x, y):
        """Verifica que la posición esté dentro del tablero."""
        return 0 <= x < GRID_COLS and 0 <= y < GRID_ROWS

    def __update_direction(self, direction):
        """Actualiza la dirección interna del tanque."""
        if direction in (DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT):
            self.__direction = direction

    # ------------------------------------------------------------------
    # Métodos públicos de movimiento y combate
    # ------------------------------------------------------------------

    def move(self, direction, board):
        """
        Mueve el tanque en la dirección dada si la celda destino es transitable.
        Retorna True si el movimiento fue exitoso.
        """
        self.__update_direction(direction)
        dx, dy = DIR_DELTA[direction]
        new_x = self.__x + dx
        new_y = self.__y + dy

        if self.__validate_position(new_x, new_y) and board.is_walkable(new_x, new_y):
            self.__x = new_x
            self.__y = new_y
            return True
        return False

    def shoot(self):
        """
        Crea y retorna una bala en la dirección actual del tanque.
        Las subclases pueden sobreescribir para cambiar el tipo de bala.
        """
        from entities.bullet import Bullet
        bullet_x = self.__x
        bullet_y = self.__y
        owner = 'PLAYER' if self.__class__.__name__ == 'PlayerTank' else 'ENEMY'
        return Bullet(
            bullet_x, bullet_y,
            self.__direction,
            self._bullet_speed,
            self.__bullet_damage,
            owner
        )

    def take_damage(self, damage):
        """Resta vida al tanque. Retorna True si muere."""
        self.__health -= damage
        if self.__health < 0:
            self.__health = 0
        return self.__health <= 0

    def is_alive(self):
        """Retorna True si el tanque tiene vida."""
        return self.__health > 0

    # ------------------------------------------------------------------
    # Getters públicos
    # ------------------------------------------------------------------

    def get_position(self):
        """Retorna (x, y) en coordenadas de celda."""
        return (self.__x, self.__y)

    def get_direction(self):
        """Retorna la dirección actual del tanque."""
        return self.__direction

    def get_health(self):
        return self.__health

    def get_speed(self):
        return self.__speed

    def get_damage(self):
        return self.__bullet_damage

    # Setters internos para uso de subclases
    def _set_position(self, x, y):
        self.__x = x
        self.__y = y

    def _set_direction(self, direction):
        self.__update_direction(direction)

    def _set_health(self, health):
        self.__health = health

    # ------------------------------------------------------------------
    # Método abstracto de renderizado
    # ------------------------------------------------------------------

    @abstractmethod
    def render(self, surface):
        """Dibuja el tanque en la superficie dada."""
        pass

    # ------------------------------------------------------------------
    # Método de renderizado compartido (llamado por subclases)
    # ------------------------------------------------------------------

    def _draw_tank(self, surface, color=None):
        """Dibuja el cuerpo del tanque y su cañón según la dirección."""
        if color is None:
            color = self._color

        x, y = self.get_position()
        pixel_x = x * CELL_SIZE
        pixel_y = y * CELL_SIZE

        margin = 5
        # Cuerpo del tanque
        body_rect = pygame.Rect(
            pixel_x + margin,
            pixel_y + margin,
            CELL_SIZE - margin * 2,
            CELL_SIZE - margin * 2
        )
        pygame.draw.rect(surface, color, body_rect)

        # Borde oscuro para profundidad
        dark = tuple(max(0, c - 60) for c in color)
        pygame.draw.rect(surface, dark, body_rect, 2)

        # Cañón según dirección
        cx = pixel_x + CELL_SIZE // 2
        cy = pixel_y + CELL_SIZE // 2
        canon_len = CELL_SIZE // 2 + 4
        canon_w = 6

        direction = self.get_direction()
        if direction == DIR_UP:
            canon_rect = pygame.Rect(cx - canon_w // 2, cy - canon_len, canon_w, canon_len)
        elif direction == DIR_DOWN:
            canon_rect = pygame.Rect(cx - canon_w // 2, cy, canon_w, canon_len)
        elif direction == DIR_LEFT:
            canon_rect = pygame.Rect(cx - canon_len, cy - canon_w // 2, canon_len, canon_w)
        else:  # RIGHT
            canon_rect = pygame.Rect(cx, cy - canon_w // 2, canon_len, canon_w)

        pygame.draw.rect(surface, dark, canon_rect)
