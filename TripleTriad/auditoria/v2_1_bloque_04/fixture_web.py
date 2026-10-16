"""Solo pruebas: se inyecta en /tmp del navegador; no se exporta con el juego.

Prepara tableros controlados. Las jugadas del jugador se hacen con CDP;
las capturas se resuelven siempre con el motor real.
"""
import asyncio
import json
import time
import platform
import partida
import opciones
from reglas import Carta, CPU, USUARIO
from ui import mano_rect


def locate():
    for task in asyncio.all_tasks():
        coroutine = task.get_coro()
        seen = set()
        while coroutine is not None and id(coroutine) not in seen:
            seen.add(id(coroutine))
            frame = getattr(coroutine, 'cr_frame', None) or getattr(coroutine, 'gi_frame', None)
            if frame is not None:
                game = frame.f_locals.get('juego')
                if isinstance(game, partida.Juego):
                    return game
            coroutine = getattr(coroutine, 'cr_await', None) or getattr(coroutine, 'gi_yieldfrom', None)
    raise RuntimeError('No se encontro un duelo activo')


def inspect():
    game = locate()
    now = time.time()
    data = dict(turno_cpu=game.turno_cpu, cpu_en_cola=game.cpu_en_cola,
                pausa=game.pausa, historial=game.historial_abierto, fin=game.fin,
                tiempo_fin=game.tiempo_fin, ahora=now,
                efecto=game.efecto[0] if game.efecto else None,
                efecto_edad=now-game.efecto[1] if game.efecto else None,
                mensaje=game.mensaje, jugadas=game.jugadas, capturas=game.capturas,
                mano=[list(mano_rect(i, len(game.mano_u)).center) for i in range(len(game.mano_u))],
                tablero=[[card.dueno if card else None for card in row] for row in game.board],
                movimiento_reducido=opciones.obtener('movimiento_reducido'))
    platform.window.eval('window.__ttAudit=' + json.dumps(data))
    return data


def card(n, s, e, o, owner, ability=None):
    return Carta('Espadachin' if owner == USUARIO else 'Lancero Gruano',
                 n, s, e, o, dueno=owner,
                 bando='humano' if owner == USUARIO else 'orco', habilidad=ability)


def prepare(kind):
    game = locate()
    cpu = kind.startswith('cpu')
    owner, enemy = (CPU, USUARIO) if cpu else (USUARIO, CPU)
    attack = card(2 if 'plus' in kind else 5, 1, 3, 1, owner, 'quema' if 'quema' in kind else None)
    fresh = partida.Juego('humano', bando_rival='orco',
                         mano_u_inicial=[card(1, 1, 1, 1, USUARIO)] if cpu else [attack, card(1, 1, 1, 1, USUARIO)],
                         mano_c_inicial=[attack] if cpu else [card(1, 1, 1, 1, CPU)])
    game.__dict__.clear()
    game.__dict__.update(fresh.__dict__)
    if 'quema' not in kind:
        game.board[0][1] = card(1, 7 if 'plus' in kind else 5, 1, 1, owner)
    game.board[1][2] = card(1, 1, 1, 6 if 'plus' in kind else 3, enemy)
    game.t_entrada = time.time()-10
    if 'final' in kind:
        for r in range(3):
            for c in range(3):
                if (r, c) != (1, 1) and game.board[r][c] is None:
                    game.board[r][c] = card(9, 9, 9, 9, owner)
        game.mano_u = [attack] if not cpu else []
        game.mano_c = [attack] if cpu else []
    if cpu:
        game.turno_cpu = True
        game.cpu_en_cola = 0.1
        game._elegir_jugada_cpu = lambda: (0, 1, 1)
    inspect()
