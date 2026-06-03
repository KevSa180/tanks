# entities/player_tank.py - Tanque controlado por el jugador

import pygame
from entities.tank import Tank
from constants import (
    COLOR_PLAYER, PLAYER_BULLET_SPEED, PLAYER_BULLET_DAMAGE,
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT, PLAYER_LIVES,
    SCORE_KILL_LIGHT, SCORE_KILL_MEDIUM, SCORE_KILL_HEAVY
)


class PlayerTank(Tank):
    """Tanque del jugador. Hereda de Tank y añade manejo de input y vidas."""

    def __init__(self, x, y):
        super().__init__(
            x=x, y=y,
            health=1,
            speed=3,
            bullet_damage=PLAYER_BULLET_DAMAGE,
            color=COLOR_PLAYER,
            bullet_speed=PLAYER_BULLET_SPEED
        )
        # Atributos privados del jugador
        self.__lives = PLAYER_LIVES
        self.__score = 0
        self.__shoot_cooldown = 0      # frames de espera entre disparos
        self.__shoot_cooldown_max = 20  # ~0.33s a 60 FPS
        self.__move_cooldown = 0       # frames de espera entre pasos
        self.__move_cooldown_max = 10  # ~0.17s a 60 FPS (1 celda por paso)

    # ------------------------------------------------------------------
    # Manejo de input (teclado)
    # ------------------------------------------------------------------

    def handle_input(self, board):
        """
        Lee el estado del teclado y ejecuta movimiento.
        Retorna una Bullet si el jugador dispara, o None.
        """
        keys = pygame.key.get_pressed()
        bullet = None

        if self.__move_cooldown <= 0:
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.move(DIR_UP, board)
                self.__move_cooldown = self.__move_cooldown_max
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.move(DIR_DOWN, board)
                self.__move_cooldown = self.__move_cooldown_max
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.move(DIR_LEFT, board)
                self.__move_cooldown = self.__move_cooldown_max
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.move(DIR_RIGHT, board)
                self.__move_cooldown = self.__move_cooldown_max
        else:
            self.__move_cooldown -= 1

        # Disparar con ESPACIO
        if keys[pygame.K_SPACE] and self.__shoot_cooldown <= 0:
            bullet = self.shoot()
            self.__shoot_cooldown = self.__shoot_cooldown_max

        if self.__shoot_cooldown > 0:
            self.__shoot_cooldown -= 1

        return bullet

    # ------------------------------------------------------------------
    # Gestión de vidas
    # ------------------------------------------------------------------

    def lose_life(self):
        """Resta una vida y respawnea el tanque con salud completa. Retorna True si sigue vivo."""
        self.__lives -= 1
        if self.__lives > 0:
            self._set_health(1)  # restaurar salud
            return True
        return False

    def get_lives(self):
        return self.__lives

    def reset_lives(self):
        """Reinicia las vidas al máximo. Se llama al iniciar cada nivel.

        El enunciado indica que el jugador tiene hasta tres vidas DENTRO DE
        CADA NIVEL, por lo que deben restaurarse al avanzar de nivel.
        """
        self.__lives = PLAYER_LIVES
        self._set_health(1)

    # ------------------------------------------------------------------
    # Puntuación
    # ------------------------------------------------------------------

    def add_score(self, points):
        """Suma puntos al marcador del jugador."""
        self.__score += points

    def get_score(self):
        return self.__score

    # ------------------------------------------------------------------
    # Reposicionar al inicio del nivel
    # ------------------------------------------------------------------

    def reset_position(self, x, y):
        """Reposiciona el tanque y restaura su salud."""
        self._set_position(x, y)
        self._set_health(1)

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def render(self, surface):
        """Dibuja el tanque del jugador con un pequeño indicador de dirección."""
        self._draw_tank(surface, self._color)
