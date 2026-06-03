# audio.py - Gestor de efectos de sonido

import os
import pygame

SFX_BASE     = 0.6
VOLUME_STEPS = [0.0, 0.34, 0.67, 1.0]


class AudioManager:
    """Centraliza la reproducción de efectos de sonido."""

    def __init__(self, assets_dir=None):
        self.__enabled = False
        self.__sounds  = {}
        self.__level   = 3
        self.__assets  = assets_dir or os.path.join(
            os.path.dirname(__file__), 'assets')

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.__enabled = True
        except Exception as e:
            print(f"[Audio] mixer no disponible, juego sin sonido: {e}")
            return

        self.__load_sounds()

    def __load_sounds(self):
        sfx = {
            'shoot':        'shoot.wav',
            'explosion':    'explosion.wav',
            'base_destroy': 'base_destroy.wav',
        }
        for name, filename in sfx.items():
            path = os.path.join(self.__assets, filename)
            if os.path.exists(path):
                try:
                    self.__sounds[name] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"[Audio] no se pudo cargar {filename}: {e}")

    def play_sfx(self, name):
        """Reproduce un efecto de sonido (respeta el volumen maestro)."""
        if not self.__enabled:
            return
        snd = self.__sounds.get(name)
        if snd:
            snd.set_volume(SFX_BASE * VOLUME_STEPS[self.__level])
            snd.play()

    def cycle_volume(self):
        """Baja el volumen maestro un paso; tras el silencio vuelve al máximo."""
        self.__level = (self.__level - 1) % len(VOLUME_STEPS)
        return self.__level

    def get_volume_level(self):
        return self.__level

    def is_enabled(self):
        return self.__enabled
