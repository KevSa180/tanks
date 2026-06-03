% pathfinding.pl - BFS óptimo + decisiones de movimiento y retirada

% =====================================================================
% Hechos dinámicos
% =====================================================================
:- dynamic muro/2.
:- dynamic libre/2.
:- dynamic tanque_jugador/2.
:- dynamic tanque_enemigo/3.
:- dynamic objetivo/3.

% =====================================================================
% Movimientos válidos
% =====================================================================
movimiento(arriba,    0, -1).
movimiento(abajo,     0,  1).
movimiento(izquierda, -1, 0).
movimiento(derecha,   1,  0).

celda_valida(X, Y) :-
    libre(X, Y),
    \+ muro(X, Y).

% =====================================================================
% Distancia Manhattan
% =====================================================================
distancia_manhattan(X1, Y1, X2, Y2, D) :-
    D is abs(X1 - X2) + abs(Y1 - Y2).

% =====================================================================
% BFS general — ruta más corta garantizada
%
% encontrar_ruta(SX, SY, GX, GY, RutaInv)
%   RutaInv: pos(X,Y) en orden FIN→INICIO (callers hacen reverse/2)
% =====================================================================
encontrar_ruta(GX, GY, GX, GY, [pos(GX, GY)]) :- !.

encontrar_ruta(SX, SY, GX, GY, RutaInv) :-
    bfs_loop([[pos(SX, SY)]], GX, GY, [pos(SX, SY)], RutaInv).

bfs_loop([[pos(GX, GY) | Resto] | _], GX, GY, _, [pos(GX, GY) | Resto]) :- !.

bfs_loop([[pos(CX, CY) | Ruta] | ColaResto], GX, GY, Visitados, RutaFinal) :-
    findall(
        pos(NX, NY),
        (   movimiento(_, DX, DY),
            NX is CX + DX, NY is CY + DY,
            celda_valida(NX, NY),
            \+ member(pos(NX, NY), Visitados)
        ),
        Vecinos
    ),
    construir_rutas(Vecinos, [pos(CX, CY) | Ruta], NuevasRutas),
    append(Visitados, Vecinos, NuevosVisitados),
    append(ColaResto, NuevasRutas, NuevaCola),
    bfs_loop(NuevaCola, GX, GY, NuevosVisitados, RutaFinal).

construir_rutas([], _, []).
construir_rutas([V | Vs], Ruta, [[V | Ruta] | Rs]) :-
    construir_rutas(Vs, Ruta, Rs).

% =====================================================================
% BFS de retirada — busca la celda más cercana (por pasos reales)
%   que esté a distancia Manhattan ≥ 6 del jugador.
%   Si no existe ninguna, falla y el fallback adyacente toma el control.
% =====================================================================
posicion_retirada(EX, EY, JX, JY, RX, RY) :-
    bfs_retirada([[pos(EX, EY)]], JX, JY, [pos(EX, EY)], pos(RX, RY)), !.

% Fallback: si el mapa es muy pequeño y no hay celda a D≥6, la más lejana adyacente
posicion_retirada(EX, EY, JX, JY, RX, RY) :-
    findall(
        D-pos(NX, NY),
        (   movimiento(_, DX, DY),
            NX is EX + DX, NY is EY + DY,
            celda_valida(NX, NY),
            distancia_manhattan(NX, NY, JX, JY, D)
        ),
        Vecinos
    ),
    Vecinos \= [],
    sort(0, @>=, Vecinos, [_-pos(RX, RY) | _]).

% Caso base BFS retirada: celda actual a distancia ≥ 6 del jugador
bfs_retirada([[pos(CX, CY) | _] | _], JX, JY, _, pos(CX, CY)) :-
    distancia_manhattan(CX, CY, JX, JY, D),
    D >= 7, !.

bfs_retirada([[pos(CX, CY) | Ruta] | ColaResto], JX, JY, Visitados, Resultado) :-
    findall(
        pos(NX, NY),
        (   movimiento(_, DX, DY),
            NX is CX + DX, NY is CY + DY,
            celda_valida(NX, NY),
            \+ member(pos(NX, NY), Visitados)
        ),
        Vecinos
    ),
    construir_rutas(Vecinos, [pos(CX, CY) | Ruta], NuevasRutas),
    append(Visitados, Vecinos, NuevosVisitados),
    append(ColaResto, NuevasRutas, NuevaCola),
    bfs_retirada(NuevaCola, JX, JY, NuevosVisitados, Resultado).

% =====================================================================
% Posición de defensa (para DEFENDER)
% =====================================================================
calcular_pos_defensa(OX, OY, JX, JY, DX, OY) :-
    DiffX is JX - OX, DiffY is JY - OY,
    abs(DiffX) >= abs(DiffY), !,
    (DiffX >= 0 -> DX is OX + 1 ; DX is OX - 1).

calcular_pos_defensa(OX, OY, _JX, JY, OX, DY) :-
    DiffY is JY - OY,
    (DiffY >= 0 -> DY is OY + 1 ; DY is OY - 1).

posicion_defensa(OX, OY, JX, JY, FX, FY) :-
    calcular_pos_defensa(OX, OY, JX, JY, DX, DY),
    celda_valida(DX, DY), !,
    FX = DX, FY = DY.

posicion_defensa(OX, OY, _JX, _JY, FX, FY) :-
    movimiento(_, DDX, DDY),
    FX is OX + DDX, FY is OY + DDY,
    celda_valida(FX, FY), !.

% =====================================================================
% Cálculo de ruta según acción
% =====================================================================
calcular_ruta_accion(EX, EY, JX, JY, _OX, _OY, atacar, Ruta) :-
    encontrar_ruta(EX, EY, JX, JY, RutaInv),
    reverse(RutaInv, Ruta).

calcular_ruta_accion(EX, EY, JX, JY, OX, OY, defender, Ruta) :-
    posicion_defensa(OX, OY, JX, JY, DX, DY),
    encontrar_ruta(EX, EY, DX, DY, RutaInv),
    reverse(RutaInv, Ruta).

calcular_ruta_accion(EX, EY, JX, JY, _OX, _OY, emboscar, Ruta) :-
    MX is (EX + JX) // 2, MY is (EY + JY) // 2,
    (celda_valida(MX, MY) ->
        encontrar_ruta(EX, EY, MX, MY, RutaInv)
    ;
        encontrar_ruta(EX, EY, JX, JY, RutaInv)
    ),
    reverse(RutaInv, Ruta).

calcular_ruta_accion(EX, EY, JX, JY, _OX, _OY, retroceder, Ruta) :-
    posicion_retirada(EX, EY, JX, JY, RX, RY),
    encontrar_ruta(EX, EY, RX, RY, RutaInv),
    reverse(RutaInv, Ruta).

% =====================================================================
% Decisión de acción
%
% decidir_accion_rol(EX, EY, JX, JY, OX, OY, Salud, Rol,
%                   Retrocediendo, EnCooldown, Accion)
%
%   Retrocediendo: true  → el tanque YA estaba retrocediendo (histéresis)
%   EnCooldown:   true  → retirada bloqueada 8 s tras completarla
%   Accion:       atacar | defender | retroceder
%
% Jerarquía de reglas:
%   1. Si EnCooldown activo: nunca retroceder, comportamiento normal de rol
%   2. Si Retrocediendo=true y aún cerca (D≤6): continuar retrocediendo
%   3. Si vida=1 y jugador muy cerca (D≤2): iniciar retirada
%   4. HUNTER: atacar siempre
%   5. DEFENDER: atacar si jugador cerca (D≤3), patrullar si no
% =====================================================================

% ── Cooldown activo: suprimir retirada, comportamiento normal de rol ──
decidir_accion_rol(_, _, _, _, _, _, _, hunter, _, true, atacar) :- !.

decidir_accion_rol(EX, EY, JX, JY, _, _, _, defender, _, true, atacar) :-
    distancia_manhattan(EX, EY, JX, JY, D), D =< 3, !.

decidir_accion_rol(_, _, _, _, _, _, _, defender, _, true, defender) :- !.

% ── Sin cooldown: lógica normal ───────────────────────────────────────

% RETROCEDER (continuar histéresis): ya retrocedía y jugador sigue cerca
decidir_accion_rol(EX, EY, JX, JY, _, _, Salud, _, true, false, retroceder) :-
    Salud =< 1,
    distancia_manhattan(EX, EY, JX, JY, D), D =< 6, !.

% RETROCEDER (iniciar): vida baja y jugador muy cerca
decidir_accion_rol(EX, EY, JX, JY, _, _, Salud, _, false, false, retroceder) :-
    Salud =< 1,
    distancia_manhattan(EX, EY, JX, JY, D), D =< 2, !.

% HUNTER: atacar siempre
decidir_accion_rol(_, _, _, _, _, _, _, hunter, _, false, atacar) :- !.

% DEFENDER: atacar si jugador cerca, patrullar si no
decidir_accion_rol(EX, EY, JX, JY, _, _, _, defender, _, false, atacar) :-
    distancia_manhattan(EX, EY, JX, JY, D), D =< 3, !.

decidir_accion_rol(_, _, _, _, _, _, _, defender, _, false, defender) :- !.

% =====================================================================
% INTERFAZ PRINCIPAL para Python
%
% consultar_enemigo(EX, EY, JX, JY, OX, OY, Rol, Salud,
%                  Retrocediendo, EnCooldown, Accion, RutaLista)
% =====================================================================
consultar_enemigo(EX, EY, JX, JY, OX, OY, Rol, Salud,
                  Retrocediendo, EnCooldown, Accion, RutaLista) :-
    decidir_accion_rol(EX, EY, JX, JY, OX, OY, Salud, Rol,
                       Retrocediendo, EnCooldown, Accion),
    (calcular_ruta_accion(EX, EY, JX, JY, OX, OY, Accion, Ruta) ->
        maplist(pos_a_par, Ruta, RutaLista)
    ;
        RutaLista = []
    ).

% Interfaz legada
obtener_ruta(EX, EY, TX, TY, RutaLista) :-
    (encontrar_ruta(EX, EY, TX, TY, RutaInv) ->
        reverse(RutaInv, Ruta),
        maplist(pos_a_par, Ruta, RutaLista)
    ;
        RutaLista = []
    ).

pos_a_par(pos(X, Y), X-Y).
