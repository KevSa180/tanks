# ui/hud.py - Cabezal de información del juego (vidas, puntuación, nivel)

import pygame
from constants import (
    SCREEN_WIDTH, GRID_ROWS, CELL_SIZE, HUD_HEIGHT,
    COLOR_HUD_BG, COLOR_WHITE, COLOR_YELLOW,
    COLOR_PLAYER, COLOR_RED, TOTAL_LEVELS
)


class HUD:
    """Dibuja la barra de información en la parte inferior de la pantalla."""

    def __init__(self, screen):
        self.__screen = screen
        self.__font_main  = pygame.font.SysFont('monospace', 20, bold=True)
        self.__font_small = pygame.font.SysFont('monospace', 14)
        self.__hud_y = GRID_ROWS * CELL_SIZE  # y donde empieza el HUD
        self.__prolog_active = False
        self.__flash_score = 0
        self.__last_score  = 0

    def set_prolog_status(self, active):
        """Indica si Prolog está activo para mostrarlo en el HUD."""
        self.__prolog_active = active

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def render(self, player, current_level, objectives_left):
        """Dibuja el HUD completo."""
        # Fondo del HUD
        hud_rect = pygame.Rect(0, self.__hud_y, SCREEN_WIDTH, HUD_HEIGHT)
        pygame.draw.rect(self.__screen, COLOR_HUD_BG, hud_rect)
        pygame.draw.line(self.__screen, (60, 60, 90),
                         (0, self.__hud_y), (SCREEN_WIDTH, self.__hud_y), 2)

        score = player.get_score()
        lives = player.get_lives()

        # --- Vidas (izquierda) ---
        self.__draw_lives(lives)

        # --- Puntuación (centro) ---
        color = COLOR_YELLOW if self.__flash_score > 0 else COLOR_WHITE
        self.__flash_score = max(0, self.__flash_score - 1)
        score_text = f"PUNTOS: {score}"
        score_surf = self.__font_main.render(score_text, True, color)
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2,
                                                  self.__hud_y + HUD_HEIGHT // 2))
        self.__screen.blit(score_surf, score_rect)

        # --- Nivel (derecha) ---
        level_text = f"NIVEL {current_level}/{TOTAL_LEVELS}"
        level_surf = self.__font_main.render(level_text, True, COLOR_PLAYER)
        level_rect = level_surf.get_rect(midright=(SCREEN_WIDTH - 12,
                                                    self.__hud_y + HUD_HEIGHT // 2 - 10))
        self.__screen.blit(level_surf, level_rect)

        # --- Objetivos restantes ---
        obj_text = f"Objetivos: {objectives_left}"
        obj_surf = self.__font_small.render(obj_text, True, (160, 200, 255))
        obj_rect = obj_surf.get_rect(midright=(SCREEN_WIDTH - 12,
                                               self.__hud_y + HUD_HEIGHT // 2 + 12))
        self.__screen.blit(obj_surf, obj_rect)

        # --- Estado de Prolog (pequeño texto) ---
        prolog_text = "Motor: Prolog" if self.__prolog_active else "Motor: Python"
        prolog_color = (100, 255, 100) if self.__prolog_active else (200, 200, 100)
        prolog_surf = self.__font_small.render(prolog_text, True, prolog_color)
        self.__screen.blit(prolog_surf, (10, self.__hud_y + HUD_HEIGHT - 18))

        # Detectar cambio de puntuación para efecto flash
        if score != self.__last_score:
            self.__flash_score = 30
            self.__last_score = score

    def __draw_lives(self, lives):
        """Dibuja las vidas como corazones."""
        y_center = self.__hud_y + HUD_HEIGHT // 2
        size = 16

        lives_label = self.__font_small.render("VIDAS:", True, (180, 180, 180))
        self.__screen.blit(lives_label, (10, y_center - 8))

        for i in range(lives):
            x = 72 + i * (size + 6)
            self.__draw_heart(x, y_center - size // 2, size, COLOR_RED)

    def __draw_heart(self, x, y, w, color):
        """Dibuja un corazón dentro de un cuadro de lado `w` con esquina (x, y)."""
        r = w // 4
        top_y = y + r
        pygame.draw.circle(self.__screen, color, (x + r, top_y), r)
        pygame.draw.circle(self.__screen, color, (x + 3 * r, top_y), r)
        pygame.draw.polygon(self.__screen, color, [
            (x, top_y),
            (x + 4 * r, top_y),
            (x + 2 * r, y + w),
        ])

    def show_message(self, text, color=COLOR_WHITE):
        """Muestra un mensaje temporal centrado sobre el HUD."""
        font = pygame.font.SysFont('monospace', 28, bold=True)
        surf = font.render(text, True, color)
        rect = surf.get_rect(center=(SCREEN_WIDTH // 2,
                                     GRID_ROWS * CELL_SIZE // 2))
        # Fondo semitransparente
        bg = pygame.Surface((surf.get_width() + 30, surf.get_height() + 16),
                             pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        self.__screen.blit(bg, (rect.x - 15, rect.y - 8))
        self.__screen.blit(surf, rect)
