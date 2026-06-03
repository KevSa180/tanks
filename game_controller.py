# game_controller.py - Controlador principal del juego

import pygame
import sys
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    STATE_MENU, STATE_LEVEL_SELECT, STATE_PLAYING, STATE_GAME_OVER, STATE_WIN,
    STATE_LEVEL_TRANSITION, TOTAL_LEVELS, GRID_ROWS, CELL_SIZE, HUD_HEIGHT,
    COLOR_BG
)
from board import Board
from entities.player_tank import PlayerTank
from prolog_bridge import PrologBridge
from audio import AudioManager
from ui.menu import Menu
from ui.hud import HUD
import logger


class GameController:
    """Orquesta el bucle principal del juego y las transiciones de estado."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tank Wars")

        self.__screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.__clock  = pygame.time.Clock()
        self.__board  = Board()
        self.__player = None
        self.__current_level = 1
        self.__game_state = STATE_MENU
        self.__custom_mode = False  # True mientras se prueba un nivel del editor

        # Prolog
        self.__prolog_bridge = PrologBridge()
        loaded = self.__prolog_bridge.load_knowledge_base()
        logger.log_prolog_status(loaded)

        # UI
        self.__menu = Menu(self.__screen)
        self.__hud  = HUD(self.__screen)
        self.__hud.set_prolog_status(self.__prolog_bridge.is_loaded())

        # Audio (efectos de sonido)
        self.__audio = AudioManager()

        # Temporizadores
        self.__enemy_update_timer = 0
        self.__transition_timer   = 0
        self.__transition_message = ""
        self.__transition_color   = (255, 255, 255)

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------

    def run(self):
        """Inicia y mantiene el bucle principal del juego."""
        running = True
        while running:
            dt = self.__clock.tick(FPS)

            # Eventos globales (salir) — solo consume QUIT y KEYDOWN
            # para no vaciar los MOUSEBUTTONDOWN que el menú necesita
            for event in pygame.event.get([pygame.QUIT, pygame.KEYDOWN]):
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.__game_state == STATE_PLAYING:
                        self.__game_state = STATE_MENU
                    else:
                        running = False

            self.__update(dt)
            self.__render()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # ------------------------------------------------------------------
    # Inicio y transición de niveles
    # ------------------------------------------------------------------

    def start_game(self, level=1):
        """Inicia el juego desde el nivel indicado (niveles normales)."""
        self.__custom_mode = False
        self.__current_level = level
        self.__board.load_level(level, self.__prolog_bridge)
        start_x, start_y = self.__board.get_player_start()
        self.__player = PlayerTank(start_x, start_y)
        self.__game_state = STATE_PLAYING
        self.__enemy_update_timer = 0
        logger.log_section(f"NIVEL {level} — inicio de partida")

    def next_level(self):
        """Avanza al siguiente nivel conservando la puntuación.

        Las vidas se reinician al máximo: el enunciado indica que el jugador
        tiene hasta tres vidas DENTRO DE CADA NIVEL.
        """
        self.__current_level += 1
        if self.__current_level > TOTAL_LEVELS:
            self.__game_state = STATE_WIN
            return

        self.__board.load_level(self.__current_level, self.__prolog_bridge)
        start_x, start_y = self.__board.get_player_start()
        self.__player.reset_position(start_x, start_y)
        self.__player.reset_lives()
        self.__game_state = STATE_PLAYING
        logger.log_section(f"NIVEL {self.__current_level} — siguiente nivel")

    def game_over(self):
        """Transición al estado Game Over."""
        self.__game_state = STATE_GAME_OVER

    def __launch_editor(self):
        """Abre el editor de niveles (bucle modal).

        Si el usuario presiona PROBAR (ENTER) juega el nivel editado SIN
        alterar los niveles normales; si solo sale (ESC), vuelve al menú.
        """
        from level_editor import LevelEditor
        editor = LevelEditor(self.__screen, self.__clock)
        grid_lines = editor.run_editor()
        if grid_lines:
            self.__start_custom_game(grid_lines)
        else:
            self.__game_state = STATE_MENU

    def __start_custom_game(self, grid_lines):
        """Juega un nivel personalizado creado en el editor (modo de prueba)."""
        self.__custom_mode = True
        self.__current_level = 1
        self.__board.load_custom_level(grid_lines, self.__prolog_bridge)
        start_x, start_y = self.__board.get_player_start()
        self.__player = PlayerTank(start_x, start_y)
        self.__game_state = STATE_PLAYING
        self.__enemy_update_timer = 0

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------

    def __update(self, dt):
        """Actualiza el estado según el estado actual del juego."""
        if self.__game_state == STATE_PLAYING:
            self.__update_playing(dt)
        elif self.__game_state == STATE_LEVEL_TRANSITION:
            self.__update_transition(dt)

    def __update_playing(self, dt):
        """Lógica de actualización durante el juego activo."""
        current_time = pygame.time.get_ticks()

        # --- Input del jugador ---
        bullet = self.__player.handle_input(self.__board)
        if bullet:
            self.__audio.play_sfx('shoot')
        self.__board.add_bullet(bullet)

        # --- Actualizar balas ---
        self.__board.update_bullets()

        # --- Actualizar enemigos ---
        self.__update_enemies(current_time)

        # --- Colisiones ---
        score_gained, player_hit, enemy_destroyed_primary, sound_events = \
            self.__board.check_collisions(self.__player)
        for ev in sound_events:
            self.__audio.play_sfx(ev)
        if score_gained:
            self.__player.add_score(score_gained)

        # --- Jugador golpeado ---
        if player_hit and not self.__player.is_alive():
            alive = self.__player.lose_life()
            if not alive:
                self.game_over()
                return
            else:
                sx, sy = self.__board.get_player_start()
                self.__player.reset_position(sx, sy)
                self.__show_transition("¡Perdiste una vida!", (255, 80, 80), 90)
                return

        # --- Objetivo primario destruido por enemigo ---
        if enemy_destroyed_primary:
            self.__show_transition("¡Objetivo destruido por el enemigo!", (255, 80, 80), 120)
            return

        # --- Verificar condición de nivel completo ---
        self.__check_level_complete()

    def __update_enemies(self, current_time):
        """Actualiza todos los enemigos y agrega sus balas al tablero."""
        objectives = self.__board.get_objectives()
        for enemy in self.__board.get_enemies():
            bullet = enemy.update(
                self.__board,
                self.__player,
                objectives,
                current_time
            )
            if bullet:
                self.__audio.play_sfx('shoot')
            self.__board.add_bullet(bullet)

    def __check_level_complete(self):
        """Verifica si se cumplió la condición de victoria del nivel."""
        # Victoria: el jugador destruyó todos los objetivos primarios
        objectives = self.__board.get_objectives()
        if objectives and self.__board.all_objectives_destroyed():
            if self.__custom_mode or self.__current_level >= TOTAL_LEVELS:
                # Nivel personalizado o último nivel → pantalla de victoria
                self.__game_state = STATE_WIN
            else:
                self.__show_transition(
                    f"¡Nivel {self.__current_level} completado!",
                    (50, 220, 100), 150
                )

    def __show_transition(self, message, color, frames):
        """Inicia una pantalla de transición temporal."""
        self.__transition_message = message
        self.__transition_color   = color
        self.__transition_timer   = frames
        self.__game_state = STATE_LEVEL_TRANSITION

    def __update_transition(self, dt):
        """Cuenta regresiva de la transición."""
        self.__transition_timer -= 1
        if self.__transition_timer <= 0:
            # Decidir qué hacer tras la transición
            if "completado" in self.__transition_message:
                self.next_level()
            elif "Perdiste" in self.__transition_message:
                self.__game_state = STATE_PLAYING
            else:
                # Objetivos destruidos → game over si no hay más vidas
                alive = self.__player.lose_life()
                if not alive:
                    self.game_over()
                else:
                    sx, sy = self.__board.get_player_start()
                    self.__player.reset_position(sx, sy)
                    self.__game_state = STATE_PLAYING

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def __render(self):
        """Dibuja la escena según el estado actual."""
        self.__screen.fill(COLOR_BG)

        if self.__game_state == STATE_MENU:
            self.__render_menu()

        elif self.__game_state == STATE_LEVEL_SELECT:
            self.__render_level_select()

        elif self.__game_state in (STATE_PLAYING, STATE_LEVEL_TRANSITION):
            self.__render_game()
            if self.__game_state == STATE_LEVEL_TRANSITION:
                self.__hud.show_message(self.__transition_message,
                                        self.__transition_color)

        elif self.__game_state == STATE_GAME_OVER:
            self.__render_game_over()

        elif self.__game_state == STATE_WIN:
            self.__render_win()

    def __render_menu(self):
        action = self.__menu.draw_main_menu()
        if action == 'play':
            self.start_game(1)
        elif action == 'levels':
            self.__game_state = STATE_LEVEL_SELECT
        elif action == 'editor':
            self.__launch_editor()
        elif action == 'quit':
            pygame.quit()
            sys.exit()

    def __render_level_select(self):
        result = self.__menu.draw_level_select()
        if isinstance(result, int):
            self.start_game(result)
        elif result == 'back':
            self.__game_state = STATE_MENU

    def __render_game(self):
        # Tablero (fondo + muros + objetivos + balas)
        self.__board.render(self.__screen)

        # Enemigos
        for enemy in self.__board.get_enemies():
            enemy.render(self.__screen)

        # Jugador
        if self.__player:
            self.__player.render(self.__screen)

        # HUD
        objectives_left = len(self.__board.primary_objectives_intact())
        self.__hud.render(self.__player, self.__current_level, objectives_left)

    def __render_game_over(self):
        action = self.__menu.draw_game_over(
            self.__player.get_score() if self.__player else 0
        )
        if action == 'retry':
            self.start_game(1)
        elif action == 'menu':
            self.__game_state = STATE_MENU

    def __render_win(self):
        action = self.__menu.draw_win_screen(
            self.__player.get_score() if self.__player else 0
        )
        if action == 'menu':
            self.__game_state = STATE_MENU

