# main.py - Punto de entrada del juego de tanques
# Ejecutar con: python main.py

import sys
import os

# Agregar el directorio raíz al path para que los imports funcionen
sys.path.insert(0, os.path.dirname(__file__))

# Verificar pygame
try:
    import pygame
except ImportError:
    print("ERROR: pygame no está instalado.")
    print("Instalar con: pip install pygame")
    sys.exit(1)

from game_controller import GameController


def main():
    """Función principal: inicializa y corre el juego."""
    print("=" * 50)
    print("  TANK WARS - Juego de Tanques con Prolog")
    print("=" * 50)
    print("Controles:")
    print("  Flechas / WASD → Mover tanque")
    print("  ESPACIO         → Disparar")
    print("  ESC             → Pausa / Menú")
    print("=" * 50)

    controller = GameController()
    controller.run()


if __name__ == '__main__':
    main()
