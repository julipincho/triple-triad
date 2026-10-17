"""Inspección de lectura, solo en el navegador temporal de auditoría."""
import asyncio
import json
import platform
import campana
import mazos_rapidos

def inspect():
    result = dict(coleccion=campana.coleccion_de(), mazo=campana.mazo_global(),
                  campana=campana.cargar(), juego=None)
    for task in asyncio.all_tasks():
        co = task.get_coro()
        while co is not None:
            frame = getattr(co, 'cr_frame', None)
            if frame and frame.f_code.co_name == 'partida' and 'juego' in frame.f_locals:
                game = frame.f_locals['juego']
                u = [c.nombre for c in game.mano_u]
                c = [c.nombre for c in game.mano_c]
                assert len(u) <= 5 and len(c) <= 5
                if game.jugadas == 0:
                    assert len(u) == len(c) == 5
                assert set(u) <= set(mazos_rapidos.PREDEFINIDOS[game.bando])
                assert set(c) <= set(mazos_rapidos.PREDEFINIDOS[game.bando_cpu])
                result['juego'] = dict(jugador=game.bando, rival=game.bando_cpu, mano_u=u, mano_c=c,
                                      jugadas=game.jugadas)
            co = getattr(co, 'cr_await', None)
    platform.window.eval('window.__ttRapidos=' + json.dumps(result))
