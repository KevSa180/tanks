# prolog_bridge.py - Puente Python ↔ SWI-Prolog

import os

try:
    from pyswip import Prolog
    PYSWIP_AVAILABLE = True
except ImportError:
    PYSWIP_AVAILABLE = False

# Mapa de átomos Prolog → constantes de dirección Python
_DIR_PROLOG_A_PYTHON = {
    'derecha':   'RIGHT',
    'izquierda': 'LEFT',
    'arriba':    'UP',
    'abajo':     'DOWN',
}


class PrologBridge:
    """
    Gestiona toda la comunicación con SWI-Prolog.

    Responsabilidades de Prolog (backend):
      - Decidir la acción estratégica (atacar / defender / emboscar)
      - Calcular la ruta DFS con heurística Manhattan
      - Decidir si disparar y en qué dirección

    Responsabilidades de Python (solo ejecución):
      - Mover las instancias de tanque a lo largo de la ruta devuelta
      - Renderizar la interfaz gráfica
      - Crear y destruir objetos del juego
    """

    def __init__(self):
        self.__prolog     = None
        self.__is_loaded  = False
        self.__prolog_dir = os.path.join(os.path.dirname(__file__), 'prolog')

    # ------------------------------------------------------------------
    # Carga de la base de conocimiento
    # ------------------------------------------------------------------

    def load_knowledge_base(self):
        """Carga pathfinding.pl y decisions.pl en Prolog."""
        if not PYSWIP_AVAILABLE:
            print("[PrologBridge] pyswip no disponible → usando fallback Python")
            return False
        try:
            self.__prolog = Prolog()
            self.__prolog.consult(
                os.path.join(self.__prolog_dir, 'pathfinding.pl'))
            self.__prolog.consult(
                os.path.join(self.__prolog_dir, 'decisions.pl'))
            self.__is_loaded = True
            print("[PrologBridge] Base de conocimiento cargada correctamente")
            return True
        except Exception as e:
            print(f"[PrologBridge] Error cargando Prolog: {e}")
            self.__is_loaded = False
            return False

    def is_loaded(self):
        return self.__is_loaded

    # ------------------------------------------------------------------
    # Actualización de hechos del tablero (assert dinámico)
    # ------------------------------------------------------------------

    def update_board_facts(self, board, player_pos, enemy_pos):
        """
        Sincroniza el estado completo del tablero con los hechos Prolog.
        Llamar antes de cada solicitud de decisión + ruta.
        """
        if not self.__is_loaded:
            return
        try:
            self.__retractall_hechos()
            self.__assert_muros(board)
            self.__assert_libres(board)
            self.__assert_jugador(player_pos)
        except Exception as e:
            print(f"[PrologBridge] Error actualizando hechos: {e}")
            self.__is_loaded = False

    def update_player_position(self, player_pos):
        """
        Actualiza únicamente la posición del jugador (operación ligera).
        Llamar antes de consultar_disparo para mantener la posición fresca
        sin tener que re-asserstar todos los muros.
        """
        if not self.__is_loaded:
            return
        try:
            px, py = player_pos
            list(self.__prolog.query("retractall(tanque_jugador(_, _))"))
            list(self.__prolog.query(f"assert(tanque_jugador({px}, {py}))"))
        except Exception as e:
            print(f"[PrologBridge] Error actualizando posición jugador: {e}")

    def __retractall_hechos(self):
        for hecho in ['muro', 'libre', 'tanque_jugador']:
            try:
                list(self.__prolog.query(f"retractall({hecho}(_, _))"))
            except Exception:
                pass
        for hecho3 in ['objetivo', 'tanque_enemigo']:
            try:
                list(self.__prolog.query(f"retractall({hecho3}(_, _, _))"))
            except Exception:
                pass

    def __assert_muros(self, board):
        from constants import GRID_COLS, GRID_ROWS
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                if board.is_wall(x, y):
                    list(self.__prolog.query(f"assert(muro({x}, {y}))"))

    def __assert_libres(self, board):
        from constants import GRID_COLS, GRID_ROWS
        for y in range(GRID_ROWS):
            for x in range(GRID_COLS):
                if board.is_walkable(x, y):
                    list(self.__prolog.query(f"assert(libre({x}, {y}))"))

    def __assert_jugador(self, player_pos):
        px, py = player_pos
        list(self.__prolog.query(f"assert(tanque_jugador({px}, {py}))"))

    # ------------------------------------------------------------------
    # INTERFAZ PRINCIPAL: Decisión + Ruta
    # ------------------------------------------------------------------

    def get_decision_and_path(self, ex, ey, px, py, ox, oy, role, health,
                              retreating=False, cooldown=False):
        """
        Consulta Prolog para obtener la acción estratégica y la ruta.

        Parámetros:
          retreating – True si el enemigo ya estaba retrocediendo (histéresis)
          cooldown   – True si la retirada está bloqueada (8 s post-retirada)

        Retorna (accion: str, path: [(x,y)]) o None si Prolog falla.
        """
        if not self.__is_loaded:
            return None
        try:
            ret_atom  = 'true' if retreating else 'false'
            cool_atom = 'true' if cooldown   else 'false'
            query = (f"consultar_enemigo({ex},{ey},{px},{py},"
                     f"{ox},{oy},{role},{health},"
                     f"{ret_atom},{cool_atom},Accion,Ruta)")
            resultados = list(self.__prolog.query(query))
            if resultados:
                accion = str(resultados[0]['Accion'])
                path   = self.__parsear_ruta(resultados[0]['Ruta'])
                return (accion, path)
        except Exception as e:
            print(f"[PrologBridge] Error en get_decision_and_path: {e}")
        return None

    # ------------------------------------------------------------------
    # INTERFAZ PRINCIPAL: Decisión de disparo
    # ------------------------------------------------------------------

    def get_shoot_decision(self, ex, ey, px, py):
        """
        Consulta Prolog si el enemigo debe disparar y en qué dirección.

        Retorna (debe_disparar: bool, direction: str | None).
        direction usa las constantes Python: 'UP','DOWN','LEFT','RIGHT'.
        """
        if not self.__is_loaded:
            return (False, None)
        try:
            query    = f"consultar_disparo({ex},{ey},{px},{py},Debe,Dir)"
            resultados = list(self.__prolog.query(query))
            if resultados:
                debe      = (str(resultados[0]['Debe']) == 'true')
                dir_atomo = str(resultados[0]['Dir'])
                return (debe, _DIR_PROLOG_A_PYTHON.get(dir_atomo))
        except Exception as e:
            print(f"[PrologBridge] Error en get_shoot_decision: {e}")
        return (False, None)

    # ------------------------------------------------------------------
    # Interfaz legada (mantiene compatibilidad con código existente)
    # ------------------------------------------------------------------

    def get_path(self, ex, ey, tx, ty):
        """Legado: ruta de (ex,ey) a (tx,ty). Retorna [(x,y)] o []."""
        if not self.__is_loaded:
            return []
        try:
            resultados = list(self.__prolog.query(
                f"obtener_ruta({ex},{ey},{tx},{ty},Ruta)"))
            if resultados:
                return self.__parsear_ruta(resultados[0]['Ruta'])
        except Exception as e:
            print(f"[PrologBridge] Error en get_path: {e}")
        return []

    def get_action(self, ex, ey, px, py, ox, oy):
        """Legado: consulta acción estratégica."""
        if not self.__is_loaded:
            return 'atacar'
        try:
            resultados = list(self.__prolog.query(
                f"accion_completa({ex},{ey},{px},{py},{ox},{oy},Accion)"))
            if resultados:
                return str(resultados[0]['Accion'])
        except Exception as e:
            print(f"[PrologBridge] Error en get_action: {e}")
        return 'atacar'

    def should_shoot(self, ex, ey, px, py):
        """Legado: True si debe disparar (sin dirección)."""
        debe, _ = self.get_shoot_decision(ex, ey, px, py)
        return debe

    # ------------------------------------------------------------------
    # Helper de parsing
    # ------------------------------------------------------------------

    def __parsear_ruta(self, prolog_path):
        """Convierte lista Prolog X-Y en lista Python de tuplas (x, y)."""
        path = []
        for item in prolog_path:
            try:
                if hasattr(item, 'args'):
                    x, y = int(item.args[0]), int(item.args[1])
                elif isinstance(item, (list, tuple)) and len(item) == 2:
                    x, y = int(item[0]), int(item[1])
                else:
                    partes = str(item).replace('-(', '').replace(')', '').split(',')
                    x, y   = int(partes[0].strip()), int(partes[1].strip())
                path.append((x, y))
            except Exception:
                continue
        return path
