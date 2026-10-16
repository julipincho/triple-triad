"""Mide los textos del resultado y la pausa con las fuentes reales."""
import hashlib
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile
import types
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
TEMP = tempfile.TemporaryDirectory(prefix='tt_v21_b05_')
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import pygame
import campana
import facciones
import partida
import ui
from reglas import CPU, USUARIO


def main():
    global partida
    phase = sys.argv[1]
    assert phase in ('antes', 'despues')
    if phase == 'antes':
        source = subprocess.check_output(['git', 'show', 'efaac75:TripleTriad/partida.py'], cwd=BASE).decode('utf-8')
        partida = types.ModuleType('partida_b05_antes')
        sys.modules[partida.__name__] = partida
        exec(compile(source, str(BASE / 'partida.py'), 'exec'), partida.__dict__)
    out = BASE / 'auditoria/v2_1_bloque_05' / phase
    out.mkdir(parents=True, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    problems, cases = [], []
    for scale in (1.0, 1.25, 1.6):
        ui.fijar_escala_texto(scale)
        for faction in facciones.orden_facciones():
            state = campana.nueva_campana(faction)
            state['_archivo'] = None
            for node in ('senda', 'aldea', 'ruinas', 'fortaleza', 'asalto', 'trono'):
                info = campana.info_duelo(state, node)
                game = partida.Juego(faction, bando_rival=info['bando'], info=info)
                for winner in (USUARIO, CPU, None):
                    game.fin, game.ganador, game.tiempo_fin = True, winner, 100.0
                    game.comentario = info.get('lose' if winner == USUARIO else 'win')
                    game.capturas, game.jugadas, game.cadena_max = 12, 5, 4
                    name = f'{faction}_{node}_{winner}_{scale}'
                    texts, boxes = [], []
                    def draw(surface, text, size, *args, **kwargs):
                        rect = pygame.Rect(0, 0, ui.ancho_texto(text, size), ui.alto_texto(text, size))
                        rect.center = kwargs['centro']
                        texts.append((text, rect))
                        return ui.texto(surface, text, size, *args, **kwargs)
                    original_rect = pygame.draw.rect
                    def rectangle(surface, color, rect, width=0, **kwargs):
                        if width == 3 and color == ui.DORADO:
                            boxes.append(pygame.Rect(rect))
                        return original_rect(surface, color, rect, width, **kwargs)
                    screen.fill(ui.FONDO)
                    with patch.object(partida, 'texto', side_effect=draw), patch('pygame.draw.rect', side_effect=rectangle):
                        game._dibujar_resultado(screen, 103.0)
                    assert boxes and texts
                    for text, rect in texts:
                        if not boxes[0].inflate(-16, -16).contains(rect):
                            problems.append(dict(caso=name, problema='fuera del panel', texto=text))
                    for i, (text, rect) in enumerate(texts):
                        for other, other_rect in texts[i + 1:]:
                            if rect.colliderect(other_rect):
                                problems.append(dict(caso=name, problema='solapamiento', texto=[text, other]))
                    cases.append(name)
                    if faction == 'humano' and node == 'trono':
                        pygame.image.save(screen, str(out / (name + '.png')))
        game.pausa = True
        with patch.object(game, 'dibujar'), patch.object(partida, 'texto', side_effect=draw):
            texts.clear()
            partida._dibujar_pausa(screen, game)
        abandon = next(rect for text, rect in texts if text == 'ABANDONAR DUELO')
        button = partida._rect_abandonar() if hasattr(partida, '_rect_abandonar') else pygame.Rect(510, 430, 260, 44)
        if not button.inflate(-12, -8).contains(abandon):
            problems.append(dict(caso=f'pausa_{scale}', problema='texto fuera del boton'))
        pygame.image.save(screen, str(out / f'pausa_{scale}.png'))
    protected = json.loads((BASE / 'auditoria/uiux_saneamiento_20261015/proteccion_imagenes.json').read_text(encoding='utf-8'))
    changed = [p for p, sha in protected.items() if hashlib.sha256((BASE / p).read_bytes()).hexdigest() != sha]
    result = dict(fase=phase, base='efaac75', casos=len(cases), escalas=[1, 1.25, 1.6], problemas=problems,
                  imagenes_protegidas=len(protected), imagenes_modificadas=changed,
                  limite='Estados controlados; no es una campaña interactiva completa.')
    (out / 'resultados.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(casos=len(cases), problemas=len(problems), imagenes_modificadas=changed)))
    pygame.quit()
    if phase == 'despues':
        assert not problems and not changed


if __name__ == '__main__':
    main()
