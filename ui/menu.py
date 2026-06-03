# ui/menu.py - Pantallas de menú, game over y victoria

import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRID_ROWS, CELL_SIZE,
    COLOR_BG, COLOR_WHITE, COLOR_YELLOW, COLOR_RED,
    COLOR_GREEN, COLOR_PLAYER, COLOR_GRAY, TOTAL_LEVELS,
    DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD
)


class Button:
    """Botón interactivo simple."""

    def __init__(self, x, y, w, h, text, color, hover_color):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self._font = pygame.font.SysFont('monospace', 22, bold=True)

    def draw(self, surface):
        mouse = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse) else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_WHITE, self.rect, 2, border_radius=8)
        text_surf = self._font.render(self.text, True, COLOR_WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False


class Menu:
    """Gestiona todas las pantallas de UI del juego."""

    def __init__(self, screen):
        self.__screen = screen
        self.__font_title = pygame.font.SysFont('monospace', 52, bold=True)
        self.__font_large = pygame.font.SysFont('monospace', 36, bold=True)
        self.__font_medium = pygame.font.SysFont('monospace', 24)
        self.__font_small  = pygame.font.SysFont('monospace', 18)

        cx = SCREEN_WIDTH // 2
        btn_w, btn_h = 220, 50

        self.__btn_play     = Button(cx - btn_w//2, 320, btn_w, btn_h,
                                     "JUGAR",
                                     (30, 100, 60), (40, 160, 90))
        self.__btn_levels   = Button(cx - btn_w//2, 385, btn_w, btn_h,
                                     "NIVELES",
                                     (50, 50, 120), (70, 70, 170))
        self.__btn_editor   = Button(cx - btn_w//2, 450, btn_w, btn_h,
                                     "EDITOR",
                                     (90, 60, 120), (130, 90, 170))
        self.__btn_quit     = Button(cx - btn_w//2, 515, btn_w, btn_h,
                                     "SALIR",
                                     (100, 30, 30), (160, 40, 40))

        # Botones de selección de nivel
        self.__btn_easy   = Button(cx - btn_w//2, 280, btn_w, btn_h,
                                   "NIVEL 1",
                                   (30, 100, 60), (40, 160, 90))
        self.__btn_medium = Button(cx - btn_w//2, 350, btn_w, btn_h,
                                   "NIVEL 2",
                                   (120, 90, 20), (170, 130, 30))
        self.__btn_hard   = Button(cx - btn_w//2, 420, btn_w, btn_h,
                                   "NIVEL 3",
                                   (120, 30, 30), (180, 40, 40))
        self.__btn_back   = Button(cx - btn_w//2, 500, btn_w, btn_h,
                                   "VOLVER",
                                   (60, 60, 60), (90, 90, 90))
        self.__btn_retry    = Button(cx - btn_w//2, 360, btn_w, btn_h,
                                     "REINTENTAR",
                                     (30, 100, 60), (40, 160, 90))
        self.__btn_menu     = Button(cx - btn_w//2, 430, btn_w, btn_h,
                                     "MENÚ PRINCIPAL",
                                     (60, 60, 100), (80, 80, 140))
        self.__btn_next     = Button(cx - btn_w//2, 360, btn_w, btn_h,
                                     "SIGUIENTE NIVEL",
                                     (30, 100, 60), (40, 160, 90))
        self.__btn_win_menu = Button(cx - btn_w//2, 430, btn_w, btn_h,
                                     "MENÚ PRINCIPAL",
                                     (60, 60, 100), (80, 80, 140))

        # Partículas decorativas de fondo
        import random
        self.__particles = [
            (random.randint(0, SCREEN_WIDTH),
             random.randint(0, SCREEN_HEIGHT),
             random.uniform(0.5, 2.0))
            for _ in range(60)
        ]
        self.__tick = 0

    # ------------------------------------------------------------------
    # Pantalla principal (menú)
    # ------------------------------------------------------------------

    def draw_main_menu(self):
        """
        Dibuja la pantalla de inicio y retorna la acción:
        'play', 'levels', 'editor', 'quit' o None.
        """
        self.__draw_animated_bg()
        self.__draw_title("TANK WARS", COLOR_PLAYER, y=120)
        self.__draw_subtitle("Juego de Tanques con Prolog", COLOR_GRAY, y=195)

        lines = [
            "FLECHAS / WASD  →  Mover",
            "ESPACIO         →  Disparar",
            "Destruye todos los objetivos enemigos",
        ]
        for i, line in enumerate(lines):
            self.__blit_center(line, self.__font_small, COLOR_GRAY, y=245 + i * 24)

        self.__btn_play.draw(self.__screen)
        self.__btn_levels.draw(self.__screen)
        self.__btn_editor.draw(self.__screen)
        self.__btn_quit.draw(self.__screen)

        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if self.__btn_play.is_clicked(event):
                return 'play'
            if self.__btn_levels.is_clicked(event):
                return 'levels'
            if self.__btn_editor.is_clicked(event):
                return 'editor'
            if self.__btn_quit.is_clicked(event):
                return 'quit'
        return None

    def draw_level_select(self):
        """
        Dibuja la pantalla de selección de nivel.
        Retorna 1, 2, 3, 'back' o None.
        """
        self.__draw_animated_bg()
        self.__draw_title("SELECCIONAR NIVEL", COLOR_PLAYER, y=120)
        self.__draw_subtitle("Elige desde qué nivel comenzar", COLOR_GRAY, y=195)

        desc = [
            ("NIVEL 1", "2 enemigos ligeros · 1 objetivo primario",   COLOR_GREEN),
            ("NIVEL 2", "3 enemigos · 1 objetivo primario + 1 extra", COLOR_YELLOW),
            ("NIVEL 3", "4 enemigos · 1 objetivo primario + 2 extra", COLOR_RED),
        ]
        for i, (_, text, color) in enumerate(desc):
            self.__blit_center(text, self.__font_small, color, y=318 + i * 70)

        self.__btn_easy.draw(self.__screen)
        self.__btn_medium.draw(self.__screen)
        self.__btn_hard.draw(self.__screen)
        self.__btn_back.draw(self.__screen)

        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if self.__btn_easy.is_clicked(event):
                return DIFFICULTY_EASY
            if self.__btn_medium.is_clicked(event):
                return DIFFICULTY_MEDIUM
            if self.__btn_hard.is_clicked(event):
                return DIFFICULTY_HARD
            if self.__btn_back.is_clicked(event):
                return 'back'
        return None

    # ------------------------------------------------------------------
    # Pantalla de Game Over
    # ------------------------------------------------------------------

    def draw_game_over(self, score):
        """
        Dibuja la pantalla de Game Over.
        Retorna 'retry', 'menu' o None.
        """
        self.__draw_animated_bg()
        self.__draw_title("GAME OVER", COLOR_RED, y=130)
        self.__blit_center(f"Puntuación final: {score}",
                           self.__font_large, COLOR_YELLOW, y=230)
        self.__blit_center("Mejor suerte la próxima vez",
                           self.__font_medium, COLOR_GRAY, y=290)

        self.__btn_retry.draw(self.__screen)
        self.__btn_menu.draw(self.__screen)

        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if self.__btn_retry.is_clicked(event):
                return 'retry'
            if self.__btn_menu.is_clicked(event):
                return 'menu'
        return None

    # ------------------------------------------------------------------
    # Pantalla de victoria de nivel
    # ------------------------------------------------------------------

    def draw_level_complete(self, level, score):
        """
        Dibuja la pantalla de nivel completado.
        Retorna 'next', 'menu' o None.
        """
        self.__draw_animated_bg()
        self.__draw_title(f"NIVEL {level} COMPLETADO", COLOR_GREEN, y=120)
        self.__blit_center(f"Puntuación: {score}",
                           self.__font_large, COLOR_YELLOW, y=220)

        if level < TOTAL_LEVELS:
            self.__blit_center("¿Listo para el siguiente nivel?",
                               self.__font_medium, COLOR_GRAY, y=290)
            self.__btn_next.draw(self.__screen)
        else:
            self.__blit_center("¡Completaste todos los niveles!",
                               self.__font_medium, COLOR_YELLOW, y=290)
            self.__btn_win_menu.draw(self.__screen)

        self.__btn_menu.draw(self.__screen)

        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if level < TOTAL_LEVELS and self.__btn_next.is_clicked(event):
                return 'next'
            if self.__btn_win_menu.is_clicked(event):
                return 'menu'
            if self.__btn_menu.is_clicked(event):
                return 'menu'
        return None

    # ------------------------------------------------------------------
    # Pantalla de victoria final
    # ------------------------------------------------------------------

    def draw_win_screen(self, score):
        """
        Dibuja la pantalla de victoria total.
        Retorna 'menu' o None.
        """
        self.__draw_animated_bg()
        self.__draw_title("¡VICTORIA!", COLOR_YELLOW, y=110)
        self.__draw_subtitle("¡Completaste todos los niveles!", COLOR_GREEN, y=185)
        self.__blit_center(f"Puntuación final: {score}",
                           self.__font_large, COLOR_PLAYER, y=240)
        self.__blit_center("Eres un estratega brillante",
                           self.__font_medium, COLOR_GRAY, y=295)

        self.__btn_win_menu.draw(self.__screen)

        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if self.__btn_win_menu.is_clicked(event):
                return 'menu'
        return None

    # ------------------------------------------------------------------
    # Helpers de dibujado
    # ------------------------------------------------------------------

    def __draw_animated_bg(self):
        """Fondo animado con partículas de estrellas."""
        self.__screen.fill(COLOR_BG)
        self.__tick += 1
        import math
        for i, (px, py, speed) in enumerate(self.__particles):
            alpha = int(128 + 127 * math.sin(self.__tick * speed * 0.05 + i))
            size = 1 if speed < 1.0 else 2
            pygame.draw.circle(self.__screen, (alpha, alpha, alpha), (px, py), size)

    def __draw_title(self, text, color, y):
        surf = self.__font_title.render(text, True, color)
        # Sombra
        shadow = self.__font_title.render(text, True, (0, 0, 0))
        cx = SCREEN_WIDTH // 2
        self.__screen.blit(shadow, shadow.get_rect(center=(cx + 3, y + 3)))
        self.__screen.blit(surf, surf.get_rect(center=(cx, y)))

    def __draw_subtitle(self, text, color, y):
        surf = self.__font_medium.render(text, True, color)
        self.__screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, y)))

    def __blit_center(self, text, font, color, y):
        surf = font.render(text, True, color)
        self.__screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, y)))

    def handle_events(self):
        """Retorna lista de eventos de Pygame (para uso externo si se necesita)."""
        return pygame.event.get()
