"""Comprueba nombres y columnas del encabezado con texto ampliado."""
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
TEMP = tempfile.TemporaryDirectory(prefix='tt_barra_')
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import pygame
import campana
import facciones
import partida
import ui
import mazos_rapidos

phase = sys.argv[1]
assert phase in ('antes', 'despues')
module = partida
if phase == 'antes':
    source = subprocess.check_output(['git', 'show', 'a32d189:TripleTriad/partida.py'], cwd=BASE).decode('utf-8')
    module = types.ModuleType('partida_barra_antes')
    sys.modules[module.__name__] = module
    exec(compile(source, str(BASE / 'partida.py'), 'exec'), module.__dict__)
out = BASE / 'auditoria/barra_duelo_20261017' / phase
out.mkdir(parents=True, exist_ok=True)
pygame.init()
screen = pygame.display.set_mode((1280, 800))
problems, count, captures = [], 0, []
for scale in (1, 1.25, 1.6):
    ui.fijar_escala_texto(scale)
    cases = []
    for faction in facciones.orden_facciones():
        state = campana.nueva_campana(faction)
        state['_archivo'] = None
        for node in ('senda', 'aldea', 'ruinas', 'fortaleza', 'asalto', 'trono'):
            cases.append((f'{faction}_{node}', faction, campana.info_duelo(state, node), True))
        for rival in facciones.orden_facciones():
            cases.append((f'{faction}_vs_{rival}', faction,
                          dict(campana.DUELISTAS[rival], bando=rival), False))
    for name, faction, info, campaign in cases:
        info['nombre_jugador'] = 'W' * campana.NOMBRE_MAX
        game = module.Juego(faction, bando_rival=info['bando'], info=info, en_campana=campaign,
                             mano_u_inicial=mazos_rapidos.mazo(faction)[:5],
                             mano_c_inicial=mazos_rapidos.mazo(info['bando'])[:5])
        game.racha = 12
        texts = []
        def draw(surface, text, size, *args, **kwargs):
            rect = pygame.Rect(0, 0, ui.ancho_texto(text, size), ui.alto_texto(text, size))
            if kwargs.get('centro'):
                rect.center = kwargs['centro']
            else:
                rect.topleft = (kwargs['x'], kwargs['y'])
            if rect.top < 74:
                texts.append((text, rect))
            return ui.texto(surface, text, size, *args, **kwargs)
        screen.fill(ui.FONDO)
        with patch.object(module, 'texto', side_effect=draw):
            game._dibujar_hud(screen, 100)
        case = f'{name}_{scale}'
        count += 1
        marker = pygame.Rect(556, 12, 168, 48)
        for i, (text, rect) in enumerate(texts):
            if not pygame.Rect(0, 0, 1280, 74).contains(rect):
                problems.append(dict(caso=case, problema='fuera de barra', texto=text))
            if text not in ('0', '-') and rect.colliderect(marker):
                problems.append(dict(caso=case, problema='sobre marcador', texto=text))
            for other, other_rect in texts[i+1:]:
                if rect.colliderect(other_rect):
                    problems.append(dict(caso=case, problema='solapamiento', texto=[text, other]))
        joined = ' '.join(text for text, _ in texts)
        assert info['nombre_jugador'] in joined and info['nombre'] in joined
        if name in ('humano_fortaleza', 'hombre_pantera_vs_elfo_nocturno'):
            file = case + '.png'
            pygame.image.save(screen, str(out / file))
            captures.append(file)
(out / 'resultados.json').write_text(json.dumps(dict(casos=count, problemas=problems,
    capturas=captures, base='a32d189'), ensure_ascii=False, indent=2), encoding='utf-8')
print(dict(casos=count, problemas=len(problems)))
pygame.quit()
if phase == 'despues':
    assert not problems
