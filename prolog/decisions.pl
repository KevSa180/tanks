% decisions.pl - Lógica de combate: disparo, línea de visión, peligro

:- use_module(library(lists)).

% =====================================================================
% Hechos dinámicos (compartidos con pathfinding.pl)
% =====================================================================
:- dynamic muro/2.
:- dynamic libre/2.
:- dynamic tanque_jugador/2.
:- dynamic tanque_enemigo/3.

% =====================================================================
% Alineación en línea de visión (misma fila o columna)
% =====================================================================
en_linea_vision(EX, _EY, JX, _JY) :- EX =:= JX, !.
en_linea_vision(_EX, EY, _JX, JY) :- EY =:= JY.

% =====================================================================
% Verificar que no hay muros entre dos puntos alineados
% =====================================================================
hay_muro_entre_fila(Y, X1, X2) :-
    X1 < X2,
    between(X1, X2, MX),
    MX =\= X1, MX =\= X2,
    muro(MX, Y), !.

hay_muro_entre_fila(Y, X1, X2) :-
    X2 < X1,
    hay_muro_entre_fila(Y, X2, X1).

hay_muro_entre_columna(X, Y1, Y2) :-
    Y1 < Y2,
    between(Y1, Y2, MY),
    MY =\= Y1, MY =\= Y2,
    muro(X, MY), !.

hay_muro_entre_columna(X, Y1, Y2) :-
    Y2 < Y1,
    hay_muro_entre_columna(X, Y2, Y1).

% vision_libre(EX, EY, JX, JY): misma fila/columna sin muros entre ellos
vision_libre(EX, EY, EX, JY) :-
    EY =\= JY,
    \+ hay_muro_entre_columna(EX, EY, JY), !.

vision_libre(EX, EY, JX, EY) :-
    EX =\= JX,
    \+ hay_muro_entre_fila(EY, EX, JX), !.

% =====================================================================
% Condición de disparo: dentro de rango Y en línea de visión libre
% =====================================================================
debe_disparar(EX, EY, JX, JY) :-
    Distancia is abs(EX - JX) + abs(EY - JY),
    Distancia =< 5,
    en_linea_vision(EX, EY, JX, JY),
    vision_libre(EX, EY, JX, JY).

% =====================================================================
% Dirección de disparo hacia el jugador
% =====================================================================
direccion_disparo(EX, _EY, JX, _JY, derecha)   :- JX > EX, !.
direccion_disparo(EX, _EY, JX, _JY, izquierda) :- JX < EX, !.
direccion_disparo(_EX, EY, _JX, JY, abajo)     :- JY > EY, !.
direccion_disparo(_EX, _EY, _JX, _JY, arriba).

% =====================================================================
% Nivel de peligro por tipo de tanque (para priorización del jugador)
% =====================================================================
nivel_peligro(pesado,  3).
nivel_peligro(mediano, 2).
nivel_peligro(ligero,  1).

% =====================================================================
% INTERFAZ PRINCIPAL de disparo para Python
%
% consultar_disparo(EX, EY, JX, JY, Debe, Direccion)
%   Debe:      true | false
%   Direccion: arriba | abajo | izquierda | derecha | ninguna
%   Llamado desde PrologBridge.get_shoot_decision()
% =====================================================================
consultar_disparo(EX, EY, JX, JY, true, Dir) :-
    debe_disparar(EX, EY, JX, JY), !,
    direccion_disparo(EX, EY, JX, JY, Dir).

consultar_disparo(_, _, _, _, false, ninguna).
