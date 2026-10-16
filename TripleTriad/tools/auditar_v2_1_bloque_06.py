"""Auditoría aislada del texto junto a los avatares; no juega campañas."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
TEMP = tempfile.TemporaryDirectory(prefix='tt_v21_b06_')
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import pygame
import campana
import facciones
import partida
import prologo
import ui


def casos():
    yield 'tutorial', 'humano', prologo.info_duelo_prologo()
    for faction in facciones.orden_facciones():
        for branch in ('aldea', 'ruinas'):
            for retry in (0, 1):
                state = campana.nueva_campana(faction)
                state.update(eleccion=branch, revancha=retry, _archivo=None)
                for node in ('senda', branch, 'fortaleza', 'asalto', 'trono'):
                    yield f'{faction}_{branch}_{retry}_{node}', faction, campana.info_duelo(state, node)
    for faction in ('elfo_nocturno', 'hombre_pantera', 'hombre_lagarto'):
        state = campana.nueva_mini_campana(faction)
        state['_archivo'] = None
        for node in ('mini_senda', 'mini_nudo', 'mini_trono'):
            yield f'{faction}_{node}', faction, campana.info_duelo(state, node)


def main():
    module = partida
    phase = sys.argv[1]
    assert phase in ('antes', 'despues')
    if phase == 'antes':
        source = subprocess.check_output(['git', 'show', '1b22063:TripleTriad/partida.py'], cwd=BASE).decode('utf-8')
        module = types.ModuleType('partida_b06_antes')
        sys.modules[module.__name__] = module
        exec(compile(source, str(BASE / 'partida.py'), 'exec'), module.__dict__)
    out = BASE / 'auditoria/v2_1_bloque_06' / phase
    out.mkdir(parents=True, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    problems, count, captures = [], 0, []
    for scale in (1.0, 1.25, 1.6):
        ui.fijar_escala_texto(scale)
        for name, faction, info in casos():
            info['nombre_jugador'] = 'W' * campana.NOMBRE_MAX
            game = module.Juego(faction, bando_rival=info['bando'], info=info)
            for key in ('entrada', 'captura_player', 'captura_cpu'):
                game.comentario = info.get(key)
                if not game.comentario:
                    continue
                game.comentario_t0 = 100
                texts = []
                def draw(surface, text, size, *args, **kwargs):
                    rect = pygame.Rect(0, 0, ui.ancho_texto(text, size), ui.alto_texto(text, size))
                    if kwargs.get('centro'):
                        rect.center = kwargs['centro']
                    else:
                        rect.topleft = (kwargs['x'], kwargs['y'])
                    texts.append((text, rect))
                    return ui.texto(surface, text, size, *args, **kwargs)
                screen.fill(ui.FONDO)
                with patch.object(module, 'texto', side_effect=draw):
                    game._dibujar_avatar(screen, 101)
                case = f'{name}_{key}_{scale}'
                count += 1
                shown = ' '.join(text for text, _ in texts)
                if ' '.join(game.comentario.split()) not in shown:
                    problems.append(dict(caso=case, problema='comentario recortado'))
                for text, rect in texts:
                    if not screen.get_rect().inflate(-16, -16).contains(rect):
                        problems.append(dict(caso=case, problema='fuera de pantalla', texto=text))
                    for avatar in (pygame.Rect(1164, 132, 96, 96), pygame.Rect(1164, 652, 96, 96)):
                        if rect.colliderect(avatar):
                            problems.append(dict(caso=case, problema='texto sobre avatar', texto=text))
                for i, (text, rect) in enumerate(texts):
                    for other, other_rect in texts[i + 1:]:
                        if rect.colliderect(other_rect):
                            problems.append(dict(caso=case, problema='solapamiento', texto=[text, other]))
                if name in ('tutorial', 'humano_aldea_1_asalto') and key == 'entrada':
                    file = case + '.png'
                    pygame.image.save(screen, str(out / file))
                    captures.append(file)
    protected = json.loads((BASE / 'auditoria/uiux_saneamiento_20261015/proteccion_imagenes.json').read_text(encoding='utf-8'))
    changed = [p for p, sha in protected.items() if hashlib.sha256((BASE / p).read_bytes()).hexdigest() != sha]
    result = dict(base='1b22063', fase=phase, casos=count, problemas=problems, capturas=captures,
                  imagenes_protegidas=len(protected), imagenes_modificadas=changed,
                  limite='Estados de HUD controlados, no campañas completas.')
    (out / 'resultados.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(casos=count, problemas=len(problems), imagenes_modificadas=changed)))
    pygame.quit()
    if phase == 'despues':
        assert not problems and not changed


if __name__ == '__main__':
    main()
