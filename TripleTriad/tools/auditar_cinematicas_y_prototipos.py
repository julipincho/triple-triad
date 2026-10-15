"""Recorrido renderizado de ramas cinematograficas y comparativas aisladas."""
import os
import sys
import json
import math
import random
import struct
import wave
import tempfile
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
TEMP = tempfile.TemporaryDirectory(prefix='tt_auditoria_')
os.environ['TRIPLETRIAD_DATA'] = TEMP.name
import pygame
import cinematicas as cine
import prologo
import finales
import campana
import cartas
import mazos
import ui
import arte_visual
import audio

OUT = BASE / 'auditoria/revision_cinematica_ampliada_20261015'


def secuencias():
    yield 'intro', cine.intro()[0]
    for bloque in ('pre_duelo', 'post_duelo', 'carta_umbral', 'transporte',
                   'despertar', 'encuentro_hostil', 'nara', 'explicacion', 'cierre'):
        yield 'prologo.' + bloque, getattr(prologo, 'escenas_' + bloque)()
    for faccion in cine.APERTURAS:
        yield 'apertura.' + faccion, cine.apertura(faccion)[0]
        estado = campana.nueva_campana(faccion)
        for nodo in ('senda', 'aldea', 'ruinas', 'fortaleza', 'asalto', 'trono'):
            info = campana.info_duelo(estado, nodo)
            yield f'campana.{faccion}.{nodo}.previa', cine.escenas_nodo(info)[0]
            yield f'campana.{faccion}.{nodo}.victoria', cine.escenas_posterior(info, True)
            yield f'campana.{faccion}.{nodo}.derrota', cine.escenas_posterior(info, False)
        for variante, datos in campana.FINALES[faccion].items():
            yield 'final.' + faccion + '.' + variante, cine.escenas_final(
                datos['titulo'], datos['lineas'], faccion)[0]
    for variante in finales.UMBRAL:
        yield 'umbral.' + variante, finales.escenas_umbral(variante)
        yield 'epilogo.' + variante, finales.escenas_epilogo(variante)


def sonido(nombre, confirmar=False, variante=0):
    rate = 44100
    duration = .24 if confirmar else .065
    rng = random.Random(17)
    samples = []
    for i in range(int(rate * duration)):
        t = i / rate
        ataque = min(1, t / .004)
        ruido = rng.uniform(-1, 1) * math.exp(-t * 100) * .07
        tono = math.sin(2 * math.pi * (440 if variante == 0 else 330) * t)
        value = ruido + tono * ataque * math.exp(-t * 35) * .13
        if confirmar:
            for delay, hz in ((0, 523.25), (.065, 783.99 if variante == 0 else 659.25)):
                u = t - delay
                if u >= 0:
                    value += .16 * min(1, u / .008) * math.exp(-u * 21) * math.sin(2 * math.pi * hz * u)
        value *= min(1, (duration - t) / .01)
        samples.append(struct.pack('<h', round(max(-1, min(1, value)) * 32767)))
    with wave.open(str(OUT / nombre), 'wb') as f:
        f.setparams((1, 2, rate, 0, 'NONE', 'not compressed'))
        f.writeframes(b''.join(samples))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    registros = []
    muestras = {}
    for bloque, datos in secuencias():
        for indice, dato in enumerate(datos):
            reproductor = cine.Cinematica([dato], nombre_jugador='El duelista')
            escena = reproductor.escena()
            escena.mostrado = len(escena.texto)
            ruta = ('assets/cinematicas_hd/' + escena.fondo_hd if escena.fondo_hd
                    else escena.fondo_lote or arte_visual.alternativa(ui.ruta_fondo(escena.fondo), 'fondo')
                    or ui.ruta_fondo(escena.fondo))
            reproductor._dibujar(screen, escena, 2)
            registro = dict(id=f'{bloque}.{indice}', texto=dato['texto'], ruta=ruta)
            registros.append(registro)
            if ruta not in muestras:
                nombre = f'{len(muestras):02d}_{Path(ruta).stem}.png'
                pygame.image.save(screen, str(OUT / nombre))
                muestras[ruta] = nombre
    (OUT / 'recorrido.json').write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding='utf-8')
    # Indice del renderer; cada archivo usado tiene una captura representativa.
    hoja = pygame.Surface((1280, math.ceil(len(muestras) / 4) * 220))
    hoja.fill((20, 22, 30))
    for i, (ruta, nombre) in enumerate(muestras.items()):
        x, y = i % 4 * 320, i // 4 * 220
        hoja.blit(pygame.transform.smoothscale(pygame.image.load(str(OUT / nombre)), (320, 200)), (x, y + 20))
        hoja.blit(pygame.font.Font(None, 15).render(nombre, True, 'white'), (x, y))
    pygame.image.save(hoja, str(OUT / 'indice_cinematicas.png'))
    elegidas = sorted((c for grupo in mazos.TODOS.values() for c in grupo), key=lambda c: len(c.nombre), reverse=True)[:6]
    hoja = pygame.Surface((1440, 700)); hoja.fill((20, 22, 30))
    for i, carta in enumerate(elegidas):
        x, y = i % 3 * 480, i // 3 * 350
        for j, separado in enumerate((False, True, 'externo')):
            img = cartas.crear(carta, escala=1.4, nombre_separado=separado)
            hoja.blit(img, (x + j * 155, y + 35))
            etiqueta = 'Actual' if not separado else 'Franja reservada' if separado is True else 'Nombre externo'
            hoja.blit(pygame.font.Font(None, 20).render(etiqueta, True, 'white'), (x + j * 155, y + 10))
            if separado == 'externo':
                for k, linea in enumerate(cartas._lineas_nombre(carta.nombre, 110)):
                    hoja.blit(pygame.font.Font(None, 17).render(linea, True, 'white'), (x + j * 155, y + 245 + 19 * k))
    pygame.image.save(hoja, str(OUT / 'comparativa_cartas.png'))
    sonido('navegacion_suave.wav')
    sonido('confirmacion_cristal.wav', True)
    sonido('confirmacion_calida.wav', True, 1)
    for logico in (audio.MENU_MOVE, audio.MENU_OK, audio.CARD):
        ruta = audio._lote_disponible(logico) or audio._ruta(logico)
        shutil.copy2(ruta, OUT / ('actual_' + logico))
    html = '<meta charset="utf-8"><title>Comparativas</title><style>body{background:#171923;color:white;font:18px sans-serif}img{max-width:100%}</style><h1>Prototipos: selector de facciones</h1>'
    for nombre in ('actual_menu_move', 'actual_menu_ok', 'actual_card',
                   'navegacion_suave', 'confirmacion_cristal', 'confirmacion_calida'):
        html += f'<p>{nombre}</p><audio controls src="{nombre}.wav"></audio>'
    html += '<h1>Nombres de cartas: actual / franja reservada</h1><img src="comparativa_cartas.png"><h1>Cinematicas</h1><img src="indice_cinematicas.png">'
    (OUT / 'comparativas.html').write_text(html, encoding='utf-8')
    pygame.quit()
    print(f'{len(registros)} escenas renderizadas; {len(muestras)} fondos; {OUT}')


if __name__ == '__main__':
    main()
