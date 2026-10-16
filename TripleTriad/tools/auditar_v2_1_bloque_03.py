"""Mide todo el tramo del prólogo y captura anclas comparables a tres escalas.

python tools/auditar_v2_1_bloque_03.py antes|despues
Antes usa prologo.py de 7689a0f. No altera partidas ni fuentes de trabajo.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unicodedata
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE), str(BASE / 'tests')]
TEMP = tempfile.TemporaryDirectory(prefix='tt_v21_b03_')
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import auditoria_visual as av
import cinematicas
import prologo
import pygame
import ui

BASELINE = '7689a0f'
SEQUENCES = ('despertar', 'encuentro_hostil', 'nara', 'explicacion', 'cierre')


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if not unicodedata.combining(c))


def main():
    phase = sys.argv[1]
    assert phase in ('antes', 'despues')
    out = BASE / 'auditoria/v2_1_bloque_03' / phase
    out.mkdir(parents=True, exist_ok=True)
    module = prologo
    if phase == 'antes':
        module = types.ModuleType('prologo_antes')
        module.__file__ = str(BASE / 'prologo.py')
        source = subprocess.check_output(['git', 'show', f'{BASELINE}:TripleTriad/prologo.py'], cwd=BASE).decode('utf-8')
        exec(compile(source, module.__file__, 'exec'), module.__dict__)
    sequences = {name: getattr(module, 'escenas_' + name)() for name in SEQUENCES}
    (out / 'escenas.json').write_text(json.dumps(sequences, ensure_ascii=False, indent=2), encoding='utf-8')
    # Anclas semánticas: conservan la comparación aunque cambie el índice.
    selectors = {
        'despertar_inicio': ('despertar', lambda d: 'bosque' in normalized(d['texto'])),
        'despertar_torre': ('despertar', lambda d: 'torre' in normalized(d['texto'])),
        'despertar_pik': ('despertar', lambda d: 'no deberias' in normalized(d['texto'])),
        'hostil_aldea': ('encuentro_hostil', lambda d: 'aldea' in normalized(d['texto'])),
        'nara_juicio': ('nara', lambda d: 'juicio' in normalized(d['texto'])),
        'explicacion_umbral': ('explicacion', lambda d: 'grieta' in normalized(d['texto'])),
        'explicacion_trono': ('explicacion', lambda d: 'guarda' in normalized(d['texto'])),
        'explicacion_regreso': ('explicacion', lambda d: 'gana el trono' in normalized(d['texto'])),
        'cierre_titulo': ('cierre', lambda d: d.get('efecto') == 'titulo'),
        'cierre_mazo': ('cierre', lambda d: d is sequences['cierre'][-1]),
    }
    anchors = {label: (name, next(i for i, d in enumerate(sequences[name]) if predicate(d)))
               for label, (name, predicate) in selectors.items()}
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    problems, captures, count = [], [], 0
    for scale in (1.0, 1.25, 1.6):
        ui.fijar_escala_texto(scale)
        for name, sequence in sequences.items():
            for index, data in enumerate(sequence):
                cine = cinematicas.Cinematica([data], nombre_jugador='Darmagion')
                scene = cine.escena()
                scene.mostrado = len(scene.texto)
                async def draw():
                    cine._dibujar(screen, scene, 2)
                    pygame.display.flip()
                with patch('cinematicas.resplandor', wraps=cinematicas.resplandor) as glow:
                    frames = av.correr_pantalla(f'{name}_{index}', draw, max_frames=1)
                    assert frames and len(set(pygame.image.tobytes(screen, 'RGB'))) > 16
                    count += 1
                    problems.extend(av.auditar_rects(f'{name}_{index}_{scale}', frames))
                    if scene.efecto == 'titulo':
                        for call in glow.call_args_list:
                            if not screen.get_rect().contains(call.args[1]):
                                problems.append(f'{name}_{index}_{scale}: titulo desbordado {call.args[1]}')
                for label, anchor in anchors.items():
                    if anchor == (name, index):
                        file = f'{label}_{scale}.png'
                        pygame.image.save(screen, str(out / file))
                        captures.append(file)
    protected = json.loads((BASE / 'auditoria/uiux_saneamiento_20261015/proteccion_imagenes.json').read_text(encoding='utf-8'))
    changed = [p for p, sha in protected.items() if hashlib.sha256((BASE / p).read_bytes()).hexdigest() != sha]
    result = dict(fase=phase, base=BASELINE, escenas_por_tramo={n: len(s) for n, s in sequences.items()},
                  total_escenas=sum(map(len, sequences.values())), frames_medidos=count,
                  capturas=captures, problemas=problems + av.ERRORES,
                  imagenes_protegidas=len(protected), imagenes_modificadas=changed)
    if phase == 'despues':
        previous = json.loads((out.parent / 'antes/escenas.json').read_text(encoding='utf-8'))
        for name in sequences:
            for field in ('fondo', 'fondo_hd', 'retrato', 'mundo'):
                assert {e.get(field) for e in previous[name]} == {e.get(field) for e in sequences[name]}, (name, field)
        result['asignaciones_arte_conservadas'] = True
    (out / 'resultados.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if phase == 'despues':
        comparison = pygame.Surface((1280, 1260))
        comparison.fill(ui.FONDO)
        font = pygame.font.Font(None, 20)
        for row, label in enumerate(('despertar_torre', 'nara_juicio', 'cierre_mazo')):
            for col, part in enumerate(('antes', 'despues')):
                path = out.parent / part / f'{label}_1.6.png'
                assert path.is_file(), path
                x, y = col * 640, row * 420
                comparison.blit(font.render(f'{part.upper()} / {label} / 160 %', True, ui.DORADO), (x + 12, y + 2))
                comparison.blit(pygame.transform.smoothscale(pygame.image.load(str(path)), (640, 400)), (x, y + 20))
        pygame.image.save(comparison, str(out.parent / 'comparativa.png'))
    print(json.dumps(result, ensure_ascii=True, indent=2))
    pygame.quit()
    return bool(changed or (phase == 'despues' and result['problemas']))


if __name__ == '__main__':
    sys.exit(main())
