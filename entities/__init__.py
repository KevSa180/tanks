# entities/__init__.py - Exporta todas las entidades del juego
from .tank import Tank
from .player_tank import PlayerTank
from .enemy_tank import EnemyTank
from .objective import Objective
from .bullet import Bullet
from .wall import Wall

__all__ = ['Tank', 'PlayerTank', 'EnemyTank', 'Objective', 'Bullet', 'Wall']
