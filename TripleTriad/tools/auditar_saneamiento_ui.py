"""Capturas de casos exigentes; mide cartas, retratos y textos en el lienzo real."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE), str(BASE / 'tests')]
TEMP = tempfile.TemporaryDirectory(prefix='tt_uiux_')
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import auditoria_visual as av
import pygame
import ui
import prologo
import narrativa
import partida

OUT = BASE / 'auditoria/uiux_saneamiento_20261015'


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    OUT.mkdir(exist_ok=True)
    state = av.campana.nueva_campana('humano')
    profile = av.campana.cargar_perfil()
    profile['coleccion'] = {c.nombre: c.a_dict() for deck in av.mazos.TODOS.values() for c in deck}
    profile.update(duelos=9999, victorias=8888, moneda=99999,
                   mejor_racha={f: 999 for f in av.facciones.orden_facciones()})
    clock = av.RelojFalso()
    current = {'name': ''}
    def save(frame):
        pygame.image.save(screen, str(OUT / (current['name'] + '.png')))
    ui.observar_flip(save)
    issues, counts = [], {}
    async def skip_intro(*args, **kwargs):
        pass
    for scale in (1.0, 1.25, 1.6):
        ui.fijar_escala_texto(scale)
        cine = av.cinematicas.Cinematica(prologo.escenas_nara(), nombre_jugador='Íñigo Peñalosa')
        scene = next(s for s in cine.escenas if s.hablante == 'Nara')
        scene.mostrado = len(scene.texto)
        game = partida.Juego('humano', 'orco', info={'nombre_jugador': 'Íñigo Peñalosa', 'nombre': 'Vorg'})
        game.t_entrada = 0
        async def draw_dialogue():
            cine._dibujar(screen, scene, 2)
            pygame.display.flip()
        async def draw_duel():
            game.dibujar(screen)
            pygame.display.flip()
        async def draw_observer():
            observer = av.cinematicas.Cinematica(prologo.escenas_encuentro_hostil())
            shot = next(s for s in observer.escenas if s.hablante)
            shot.mostrado = len(shot.texto)
            observer._dibujar(screen, shot, 2)
            pygame.display.flip()
        cases = {
            'coleccion_completa': lambda: av.pantallas.coleccion(screen, clock, state),
            'nombre': lambda: av.pantallas.pedir_nombre(screen, clock, 'Íñigo Peñalosa'),
            'decision_senda': lambda: av.pantallas.decision_narrativa(screen, clock, state, narrativa.decision_de('senda')),
            'decision_fortaleza': lambda: av.pantallas.decision_narrativa(screen, clock, {**state, 'nodo': 'fortaleza'}, narrativa.decision_de('fortaleza')),
            'dialogo': draw_dialogue,
            'duelo': draw_duel,
            'observador': draw_observer,
            'potenciar_dos_filas': lambda: av.pantallas.elegir_carta_para_mejorar(screen, clock, state),
            'selector_minicampana': lambda: av.pantallas.elegir_faccion(screen, clock,
                facciones_disponibles=['elfo_nocturno', 'hombre_pantera', 'hombre_lagarto'], modo='mini'),
        }
        for encounter in ('mercader', 'anciano', 'hermandad', 'caravana', 'hostil', 'nara'):
            cases['evento_' + encounter] = lambda e=encounter: av.pantallas.encuentro(
                screen, clock, state, 'aldea', enc_id=e)
        with patch('campana.cargar_perfil', return_value=profile), patch('campana.nombre_jugador', return_value='Íñigo Peñalosa'), patch('cinematicas.reproducir', new=skip_intro):
            for name, fn in cases.items():
                current['name'] = name + '_' + str(scale).replace('.', '_')
                frames = av.correr_pantalla(name, fn, max_frames=1)
                issues.extend(av.auditar_rects(current['name'], frames))
                issues.extend(av.ERRORES)
                counts[current['name']] = len(frames)
                for frame in frames:
                    images = [r for r, role, _ in frame if role in ('carta_coleccion', 'carta_mejora', 'imagen_evento')]
                    texts = [r for r, role, _ in frame if role == 'texto']
                    for image in images:
                        for text in texts:
                            overlap = image.clip(text)
                            if overlap.w > 2 and overlap.h > 2:
                                issues.append(f'{current["name"]}: imagen {image} pisa texto {text}')
    ui.fijar_escala_texto(1)
    baseline = json.loads((OUT / 'proteccion_imagenes.json').read_text(encoding='utf-8'))
    changed = [p for p, h in baseline.items() if hashlib.sha256((BASE / p).read_bytes()).hexdigest() != h]
    assert not changed, changed
    result = dict(capturas=counts, problemas=issues, imagenes_intactas=len(baseline))
    (OUT / 'resultados.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True, indent=2))
    pygame.quit()
    return bool(issues)


if __name__ == '__main__':
    sys.exit(main())
