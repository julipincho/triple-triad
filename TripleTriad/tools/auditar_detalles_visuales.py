"""Captura los detalles solicitados sin abrir ni modificar partidas reales."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE), str(BASE / 'tests')]
TEMP = tempfile.TemporaryDirectory(prefix='tt_detalles_')
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import auditoria_visual as av
import pygame
import ui
import narrativa
import cartas

OUT = BASE / 'auditoria/detalles_visuales_20261015'


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    OUT.mkdir(parents=True, exist_ok=True)
    current = {'name': ''}
    def save(frame):
        pygame.image.save(screen, str(OUT / (current['name'] + '.png')))
    ui.observar_flip(save)
    issues, captures = [], []
    state = av.campana.nueva_campana('elfo_nocturno')
    advanced = {**state, 'ruta': ['senda', 'bifurcacion', 'aldea', 'fortaleza'], 'nodo': 'asalto'}
    clock = av.RelojFalso()
    for scale in (1.0, 1.25, 1.6):
        ui.fijar_escala_texto(scale)
        cine = av.cinematicas.Cinematica(narrativa.escena_amistad())
        scene = cine.escena()
        scene.mostrado = len(scene.texto)
        async def nara():
            cine._dibujar(screen, scene, 2)
            pygame.display.flip()
        cases = {
            'mapa_inicio': lambda: av.pantallas.mapa_campana(screen, clock, state),
            'mapa_avanzado': lambda: av.pantallas.mapa_campana(screen, clock, advanced),
            'derrota': lambda: av.pantallas.derrota(screen, clock, state),
            'escena_vista': lambda: av.cinematicas._preguntar_rever(screen, clock),
            'amistad_nara': nara,
        }
        with patch('pantallas.fundido_entrada'), patch('campana.nombre_jugador', return_value='Darmagion'):
            for name, fn in cases.items():
                current['name'] = name + '_' + str(scale).replace('.', '_')
                frames = av.correr_pantalla(name, fn, max_frames=1)
                assert frames, name
                issues.extend(av.auditar_rects(current['name'], frames))
                captures.append(current['name'])
        screen.fill(ui.FONDO)
        card = next(c for deck in av.mazos.TODOS.values() for c in deck if c.habilidad == 'embestida')
        for i, owner in enumerate((None, 'T', 'C')):
            img = cartas.crear(card, owner)
            screen.blit(img, (100 + i * 300, 100))
            screen.blit(pygame.transform.scale(img, (208, 288)), (100 + i * 300, 300))
        pygame.image.save(screen, str(OUT / ('cartas_' + str(scale).replace('.', '_') + '.png')))
    baseline = json.loads((BASE / 'auditoria/uiux_saneamiento_20261015/proteccion_imagenes.json').read_text(encoding='utf-8'))
    changed = [p for p, h in baseline.items() if hashlib.sha256((BASE / p).read_bytes()).hexdigest() != h]
    assert not changed, changed
    issues.extend(av.ERRORES)
    result = dict(capturas=captures, problemas=issues, imagenes_preexistentes_intactas=len(baseline))
    (OUT / 'resultados.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True, indent=2))
    pygame.quit()
    return bool(issues)


if __name__ == '__main__':
    sys.exit(main())
