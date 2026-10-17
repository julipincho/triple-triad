"""Selector de mazos prestados: captura y medición sin perfiles reales."""
import json
import os
from pathlib import Path
import sys
import tempfile

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE), str(BASE / 'tests')]
TEMP = tempfile.TemporaryDirectory(prefix='tt_rapidos_visual_')
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import auditoria_visual as av
import pygame
import pantallas
import ui
import mazos_rapidos
from reglas import total_carta, rareza

out = BASE / 'auditoria/rapidos_independientes_20261017'
out.mkdir(parents=True, exist_ok=True)
pygame.init()
screen = pygame.display.set_mode((1280, 800))
class Clock:
    def tick(self, fps):
        return 16
problems, captures = [], []
for scale in (1, 1.25, 1.6):
    ui.fijar_escala_texto(scale)
    for mode in ('rapida', 'rapida_rival'):
        async def draw():
            await pantallas.elegir_faccion(screen, Clock(), modo=mode)
        frames = av.correr_pantalla(mode, draw, max_frames=2)
        assert frames
        problems.extend(av.auditar_rects(f'{mode}_{scale}', frames))
        name = f'{mode}_{scale}.png'
        pygame.image.save(screen, str(out / name))
        captures.append(name)
decks = {}
for faction in mazos_rapidos.PREDEFINIDOS:
    cards = mazos_rapidos.mazo(faction)
    decks[faction] = dict(cartas=[c.nombre for c in cards], total=sum(total_carta(c) for c in cards),
                          rarezas=[rareza(c)[0] for c in cards],
                          habilidades=sorted({c.habilidad for c in cards if c.habilidad}))
result = dict(capturas=captures, problemas=problems + av.ERRORES, mazos=decks)
(out / 'visual_y_mazos.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('Problemas:', len(result['problemas']))
assert not result['problemas']
pygame.quit()
