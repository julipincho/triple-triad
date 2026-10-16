"""Audita cierres de duelos y minicampañas: antes/después, sin datos reales.

python tools/auditar_v2_1_bloque_02.py antes|despues
La fase anterior carga solo datos narrativos desde cf2b62f.
"""
import ast
import copy
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from contextlib import ExitStack
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE), str(BASE / 'tests')]
TEMP = tempfile.TemporaryDirectory(prefix='tt_v21_b02_')
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import auditoria_visual as av
import campana
import cinematicas
import duelistas
import facciones
import pygame
import ui

BASELINE = 'cf2b62f'


def previous_source(name):
    return subprocess.check_output(['git', 'show', f'{BASELINE}:TripleTriad/{name}.py'], cwd=BASE).decode('utf-8')


def previous_module(name):
    module = types.ModuleType(name + '_antes')
    module.__file__ = str(BASE / (name + '.py'))
    exec(compile(previous_source(name), module.__file__, 'exec'), module.__dict__)
    return module


def walk_routes():
    routes, cases, snapshots = [], {}, {}
    for faction in facciones.orden_facciones():
        for branch in ('aldea', 'ruinas'):
            state = campana.nueva_campana(faction)
            state['_archivo'] = None
            route = []
            while not state.get('completada'):
                if campana.nodo_actual(state) == 'bifurcacion':
                    campana.elegir_bifurcacion(state, branch)
                node = campana.nodo_actual(state)
                info = campana.info_duelo(state)
                before = cinematicas.escenas_nodo(info)[0]
                lost = copy.deepcopy(state)
                campana.registrar_derrota(lost)
                assert campana.nodo_actual(lost) == node
                retry = campana.info_duelo(lost)
                assert (retry['nombre'], retry['retrato'], retry['bando']) == (info['nombre'], info['retrato'], info['bando'])
                defeat = cinematicas.escenas_posterior(retry, False)
                assert not lost.get('completada')
                campana.registrar_victoria(state)
                won_info = campana.info_duelo(state, node)
                victory = cinematicas.escenas_posterior(won_info, True)
                assert victory != defeat
                key = f'{faction}/{branch}/{node}'
                snapshots[key] = dict(previa=before, victoria=victory, derrota=defeat,
                                      rival=info['nombre'], retrato=info['retrato'])
                if faction == 'humano':
                    cases[node + '_victoria'] = victory[0]
                    cases[node + '_rival_victoria'] = next(e for e in victory if e.get('hablante') == info['nombre'])
                    cases[node + '_rival_derrota'] = next(e for e in defeat if e.get('hablante') == info['nombre'])
                route.append(node)
                assert len(route) <= 5
            assert route == ['senda', branch, 'fortaleza', 'asalto', 'trono']
            routes.append(dict(faccion=faction, rama=branch, ruta=route, completada=True))

    for faction in ('elfo_nocturno', 'hombre_pantera', 'hombre_lagarto'):
        state = campana.nueva_mini_campana(faction)
        route = []
        while not state.get('completada'):
            node = campana.nodo_actual(state)
            info = campana.info_duelo(state)
            sequence = cinematicas.escenas_nodo(info)[0]
            snapshots[f'{faction}/{node}'] = dict(previa=sequence, rival=info['nombre'])
            if faction == 'elfo_nocturno':
                cases[node + '_previa'] = sequence[0]
            lost = copy.deepcopy(state)
            campana.registrar_derrota(lost)
            assert campana.nodo_actual(lost) == node and not lost.get('completada')
            campana.registrar_victoria(state)
            route.append(node)
            assert len(route) <= 3
        assert route == ['mini_senda', 'mini_nudo', 'mini_trono']
        routes.append(dict(faccion=faction, mini=True, ruta=route, completada=True))
    return routes, cases, snapshots


def main():
    phase = sys.argv[1]
    assert phase in ('antes', 'despues')
    out = BASE / 'auditoria/v2_1_bloque_02' / phase
    out.mkdir(parents=True, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    with ExitStack() as stack:
        stack.enter_context(patch('campana.nombre_jugador', return_value='Darmagion'))
        if phase == 'antes':
            previous_duelists = previous_module('duelistas')
            stack.enter_context(patch.object(campana, 'duelistas', previous_duelists))
            stack.enter_context(patch.object(cinematicas, 'duelistas', previous_duelists))
            stack.enter_context(patch.object(cinematicas, 'narrativa', previous_module('narrativa')))
            node = next(n for n in ast.parse(previous_source('campana')).body
                        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'NODOS_MINI' for t in n.targets))
            stack.enter_context(patch.object(campana, 'NODOS_MINI', ast.literal_eval(node.value)))
        routes, cases, snapshots = walk_routes()

    (out / 'recorridos.json').write_text(json.dumps(routes, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / 'escenas.json').write_text(json.dumps(snapshots, ensure_ascii=False, indent=2), encoding='utf-8')
    problems, captures, frames_count = [], [], 0
    for scale in (1.0, 1.25, 1.6):
        ui.fijar_escala_texto(scale)
        for name, data in cases.items():
            cine = cinematicas.Cinematica([data], nombre_jugador='Darmagion')
            scene = cine.escena()
            scene.mostrado = len(scene.texto)
            async def draw():
                cine._dibujar(screen, scene, 2)
                pygame.display.flip()
            with patch('cinematicas.resplandor', wraps=cinematicas.resplandor) as glow:
                frames = av.correr_pantalla(name, draw, max_frames=1)
                assert frames and len(set(pygame.image.tobytes(screen, 'RGB'))) > 16, name
                frames_count += 1
                problems.extend(av.auditar_rects(f'{name}_{scale}', frames))
                if scene.efecto == 'titulo':
                    for call in glow.call_args_list:
                        rect = call.args[1]
                        if not screen.get_rect().contains(rect):
                            problems.append(f'{name}_{scale}: titulo desbordado {rect}')
            # Todos los casos se miden a tres escalas; capturas de todos al
            # 100 % y ampliadas de los tres ejemplos de lectura más exigentes.
            if scale == 1.0 or name in ('aldea_rival_victoria', 'trono_victoria', 'mini_trono_previa'):
                file = f'{name}_{scale}.png'
                pygame.image.save(screen, str(out / file))
                captures.append(file)
    protected = json.loads((BASE / 'auditoria/uiux_saneamiento_20261015/proteccion_imagenes.json').read_text(encoding='utf-8'))
    changed = [p for p, sha in protected.items() if hashlib.sha256((BASE / p).read_bytes()).hexdigest() != sha]
    result = dict(fase=phase, base=BASELINE, rutas_principales=20, minicampanas=3,
                  duelos_modelo=109, derrotas_sin_avance=109, frames_medidos=frames_count,
                  capturas=captures, problemas=problems + av.ERRORES,
                  imagenes_protegidas=len(protected), imagenes_modificadas=changed)
    (out / 'resultados.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if phase == 'despues':
        comparison = pygame.Surface((1280, 1260))
        comparison.fill(ui.FONDO)
        font = pygame.font.Font(None, 20)
        examples = ('aldea_rival_victoria', 'trono_victoria', 'mini_trono_previa')
        for row, example in enumerate(examples):
            for col, label in enumerate(('antes', 'despues')):
                path = out.parent / label / f'{example}_1.6.png'
                if path.is_file():
                    x, y = col * 640, row * 420
                    comparison.blit(font.render(f'{label.upper()} / {example} / 160 %', True, ui.DORADO), (x + 12, y + 2))
                    comparison.blit(pygame.transform.smoothscale(pygame.image.load(str(path)), (640, 400)), (x, y + 20))
        pygame.image.save(comparison, str(out.parent / 'comparativa.png'))
    print(json.dumps(result, ensure_ascii=True, indent=2))
    pygame.quit()
    return bool(changed or (phase == 'despues' and result['problemas']))


if __name__ == '__main__':
    sys.exit(main())
