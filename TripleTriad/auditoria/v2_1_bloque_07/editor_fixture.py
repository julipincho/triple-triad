"""Entrada de auditoría para el editor, solo dentro del navegador temporal."""
import asyncio
import json
import platform
import campana
import main
import pantallas


async def editor(screen, clock):
    deck = await pantallas.armar_mazo(screen, clock, 'humano')
    platform.window.eval('window.__ttEditorFinal=' + json.dumps(dict(mazo=deck)))


def install():
    perfil = campana.cargar_perfil()
    perfil['coleccion'] = campana.coleccion_inicial('humano')
    perfil['mazo'] = list(perfil['coleccion'])
    campana.guardar_perfil(perfil)
    installed = False
    for task in asyncio.all_tasks():
        co = task.get_coro()
        while co is not None:
            frame = getattr(co, 'cr_frame', None)
            if frame and '_duelo_rapido' in frame.f_globals:
                frame.f_globals['_duelo_rapido'] = editor
                installed = True
            co = getattr(co, 'cr_await', None)
    assert installed


def inspect():
    for task in asyncio.all_tasks():
        co = task.get_coro()
        while co is not None:
            frame = getattr(co, 'cr_frame', None)
            if frame and frame.f_code.co_name == 'armar_mazo':
                loc = frame.f_locals
                result = dict(seleccion=list(loc['seleccion']),
                              visibles=list(loc['pagina_items']),
                              rects=[list(rect.center) for name, rect in loc['rects_coleccion']],
                              motivo=loc['motivo'])
                platform.window.eval('window.__ttEditor=' + json.dumps(result))
                return
            co = getattr(co, 'cr_await', None)
    platform.window.eval('window.__ttEditor=null')
