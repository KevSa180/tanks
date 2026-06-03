# logger.py - Log visual de decisiones del motor Prolog en la terminal

import time

# ── Códigos ANSI ──────────────────────────────────────────────────────────────
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_DIM    = "\033[2m"

_CYAN   = "\033[96m"
_YELLOW = "\033[93m"
_GREEN  = "\033[92m"
_BLUE   = "\033[94m"
_MAGENTA= "\033[95m"
_RED    = "\033[91m"
_WHITE  = "\033[97m"
_GRAY   = "\033[90m"

# ── Colores por acción ────────────────────────────────────────────────────────
_ACTION_COLOR = {
    'atacar':     _GREEN,
    'defender':   _BLUE,
    'emboscar':   _MAGENTA,
    'retroceder': _RED,
}

# ── Colores por tipo de tanque ────────────────────────────────────────────────
_TYPE_COLOR = {
    'LIGHT':  _YELLOW,
    'MEDIUM': "\033[38;5;208m",   # naranja
    'HEAVY':  _RED,
}

# ── Abreviaciones de rol ──────────────────────────────────────────────────────
_ROLE_LABEL = {
    'HUNTER':   f"{_RED}HUNTER{_RESET}",
    'DEFENDER': f"{_BLUE}DEFNDR{_RESET}",
}

# ── Control de duplicados (evita spam cuando Prolog repite la misma decisión) ─
_last_decision: dict[int, tuple] = {}   # id(enemy) → (accion, target)
_last_shoot:    dict[int, tuple] = {}   # id(enemy) → (debe, dir)


def _ts() -> str:
    """Timestamp HH:MM:SS."""
    t = time.localtime()
    return f"{_GRAY}{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}{_RESET}"


def _tag(source: str) -> str:
    """Etiqueta de fuente: PROLOG o  BFS ."""
    if source == 'prolog':
        return f"{_BOLD}{_CYAN}[PROLOG]{_RESET}"
    return f"{_BOLD}{_YELLOW}[ BFS  ]{_RESET}"


def _enemy_label(tank_type: str, role: str, pos: tuple) -> str:
    tc = _TYPE_COLOR.get(tank_type, _WHITE)
    rl = _ROLE_LABEL.get(role, role)
    return f"{tc}{tank_type}{_RESET}({rl}) @{_GRAY}{pos}{_RESET}"


# ── API pública ───────────────────────────────────────────────────────────────

def log_decision(enemy_id: int, tank_type: str, role: str, pos: tuple,
                 accion: str, target: tuple, path_len: int, source: str):
    """
    Registra la decisión de movimiento de un enemigo.

    enemy_id  – id() del objeto EnemyTank (para suprimir duplicados)
    source    – 'prolog' | 'bfs'
    """
    key = (accion, target)
    if _last_decision.get(enemy_id) == key:
        return                          # misma decisión que antes → silencio
    _last_decision[enemy_id] = key

    ac = _ACTION_COLOR.get(accion, _WHITE)
    label = _enemy_label(tank_type, role, pos)
    action_str = f"{_BOLD}{ac}{accion.upper():>10}{_RESET}"
    path_str   = (f"{_DIM}ruta {path_len} paso(s) → {target}{_RESET}"
                  if path_len else f"{_RED}sin ruta{_RESET}")

    print(f"  {_ts()} {_tag(source)} {label}  {action_str}  {path_str}")


def log_shoot(enemy_id: int, tank_type: str, role: str, pos: tuple,
              debe: bool, direction, source: str):
    """
    Registra la decisión de disparo de un enemigo.
    Solo imprime cuando el resultado cambia o cuando dispara.
    """
    key = (debe, direction)
    if not debe and _last_shoot.get(enemy_id) == key:
        return
    _last_shoot[enemy_id] = key

    if not debe:
        return                          # no dispara → no spam

    label = _enemy_label(tank_type, role, pos)
    dir_str = f"{_BOLD}{_RED}DISPARO → {direction}{_RESET}"
    print(f"  {_ts()} {_tag(source)} {label}  {dir_str}")


def log_fallback_reason(tank_type: str, role: str, pos: tuple, reason: str):
    """Aviso cuando Prolog devuelve ruta vacía y se activa el fallback BFS."""
    label = _enemy_label(tank_type, role, pos)
    print(f"  {_ts()} {_tag('bfs')} {label}  "
          f"{_YELLOW}fallback — {reason}{_RESET}")


def log_prolog_status(loaded: bool):
    """Muestra una sola vez si Prolog cargó o no."""
    if loaded:
        print(f"\n  {_BOLD}{_CYAN}[PROLOG]{_RESET} "
              f"Motor cargado {_GREEN}✓{_RESET}  "
              f"— mostrando decisiones en tiempo real\n")
    else:
        print(f"\n  {_BOLD}{_YELLOW}[ BFS  ]{_RESET} "
              f"Prolog no disponible — usando fallback Python\n")


def log_section(text: str):
    """Línea divisoria con texto (p.ej. inicio de nivel)."""
    bar = "─" * 60
    print(f"\n  {_GRAY}{bar}{_RESET}")
    print(f"  {_BOLD}{_WHITE}  {text}{_RESET}")
    print(f"  {_GRAY}{bar}{_RESET}\n")
