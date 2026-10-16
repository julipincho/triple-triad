"""Capturas reales, medidas y protección de arte de los apartados 1–3.

Ejecutar antes y después: python tools/auditar_v2_1_bloque_01.py antes|despues
No abre ni modifica guardados del jugador.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import types

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE), str(BASE / 'tests')]
TEMP = tempfile.TemporaryDirectory(prefix='tt_v21_b01_')
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import auditoria_visual as av
import cinematicas
import narrativa
import prologo
import pygame
import ui
from partida import Juego
from reglas import Carta, CPU, USUARIO


def main():
    phase = sys.argv[1]
    assert phase in ('antes', 'despues')
    out = BASE / 'auditoria/v2_1_bloque_01' / phase
    out.mkdir(parents=True, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    game_class = Juego
    if phase == 'antes':
        def baseline_module(name):
            module = types.ModuleType(name + '_antes')
            module.__file__ = str(BASE / (name + '.py'))
            source = subprocess.check_output(['git', 'show', 'cf3ccc3:TripleTriad/' + name + '.py'], cwd=BASE).decode('utf-8')
            exec(compile(source, module.__file__, 'exec'), module.__dict__)
            return module
        baseline_narrativa = baseline_module('narrativa')
        scenes = {node: baseline_narrativa.previa_nodo(node) for node in baseline_narrativa.NARRATIVA}
        scenes['torneo'] = baseline_module('prologo').escenas_pre_duelo()
        game_class = baseline_module('partida').Juego
    else:
        scenes = {node: narrativa.previa_nodo(node) for node in narrativa.NARRATIVA}
        scenes['torneo'] = prologo.escenas_pre_duelo()
    for node, sequence in scenes.items():
        if node != 'torneo':
            cinematicas._continuidad_nodo_hd(sequence, node)
    (out / 'escenas.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding='utf-8')
    captures, problems = [], []
    current = {'name': ''}
    def save_frame(frame):
        assert len(set(pygame.image.tobytes(screen, 'RGB'))) > 16, 'Captura vacia: ' + current['name']
        pygame.image.save(screen, str(out / (current['name'] + '.png')))
    ui.observar_flip(save_frame)

    for scale in (1.0, 1.25, 1.6):
        ui.fijar_escala_texto(scale)
        for node, sequence in scenes.items():
            # El cierre previo contiene el objetivo del duelo en esta pasada.
            cine = cinematicas.Cinematica([sequence[-1]])
            scene = cine.escena()
            scene.mostrado = len(scene.texto)
            async def draw_scene():
                cine._dibujar(screen, scene, 2)
                pygame.display.flip()
            current['name'] = f'{node}_{scale}'
            frames = av.correr_pantalla(current['name'], draw_scene, max_frames=1)
            assert frames, current['name']
            problems.extend(av.auditar_rects(current['name'], frames))
            captures.append(current['name'])

        for effect, summary in (
            ('same', {'same': 2, 'basica': 0, 'cadena': 0}),
            ('plus', {'plus': 2, 'basica': 0, 'cadena': 1}),
            ('quema', {'quema': 1, 'basica': 0, 'cadena': 0}),
        ):
            game = game_class('humano', bando_rival='orco', mano_u_inicial=prologo.mazo_tutorial(),
                         mano_c_inicial=prologo.mazo_rival_rajoy())
            game.board[1][1] = Carta('Espadachin', 8, 6, 5, 7, dueno=USUARIO, bando='humano')
            game.board[0][1] = Carta('Lancero Gruano', 6, 7, 8, 5, dueno=USUARIO, bando='orco')
            game._anunciar_efecto(summary, 100.0, USUARIO)
            game.t_entrada = 90.0
            game.turno_cpu = True
            game.mensaje = 'Tu jugada: 2 capturas. Turno del rival.'
            async def draw_effect():
                # El reloj fijo permite comparar exactamente el mismo instante.
                from unittest.mock import patch
                with patch('partida.time.time', return_value=100.5):
                    game.dibujar(screen)
                pygame.display.flip()
            current['name'] = f'efecto_{effect}_{scale}'
            frames = av.correr_pantalla(current['name'], draw_effect, max_frames=1)
            assert frames, current['name']
            # El cartel cacheado antiguo registra su superficie completa como
            # "texto" con un descriptor callable. Es un panel superpuesto, no
            # un Rect contenedor ni una línea de texto: medirlo como tal evita
            # tanto AttributeError como falsos solapes contra el tablero.
            frames = [[(r, 'panel', None) if callable(c) else (r, role, c)
                       for r, role, c in frame] for frame in frames]
            problems.extend(av.auditar_rects(current['name'], frames))
            captures.append(current['name'])

    baseline_path = BASE / 'auditoria/uiux_saneamiento_20261015/proteccion_imagenes.json'
    baseline = json.loads(baseline_path.read_text(encoding='utf-8'))
    changed = [p for p, sha in baseline.items() if hashlib.sha256((BASE / p).read_bytes()).hexdigest() != sha]
    result = dict(fase=phase, capturas=captures, problemas=problems + av.ERRORES,
                  imagenes_protegidas=len(baseline), imagenes_modificadas=changed,
                  escenas_pre_duelo=len(scenes['torneo']))
    (out / 'resultados.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True, indent=2))
    pygame.quit()
    return bool(result['problemas'] or changed)


if __name__ == '__main__':
    sys.exit(main())
