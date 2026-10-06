"""Medidor de fotogramas para diagnostico (`main.py --fps`).

Enchufa `pygame.display.flip` una sola vez y, en cada presentacion, mide el
tiempo desde el flip anterior y lo pinta encima. Sirve para comparar de verdad
cuanto rinde el juego en vez de fiarse de la sensacion:

    python main.py --fps        # escritorio
    (en la web) anadir --fps a los argumentos no es posible: la build se
    compila con main.py como entrada, asi que para medir en el navegador hay
    que tocar `_flip` a mano o usar el panel `gui_debug` de la plantilla.

No se activa solo: `activar()` hay que llamarlo a mano.
"""

import time

import pygame

import ui

_flip_original = None
_anterior = None
_cuadros = []


def activar():
    """Empieza a medir. Idempotente.

    Se llama desde `main.py` con `--fps` (escritorio) o con la variable de
    entorno `TT_FPS=1` (en la web no hay `sys.argv`).
    """
    global _flip_original, _anterior
    if _flip_original is not None:
        return
    _flip_original = pygame.display.flip
    _anterior = time.perf_counter()
    pygame.display.flip = _flip


def desactivar():
    global _flip_original, _anterior
    if _flip_original is None:
        return
    pygame.display.flip = _flip_original
    _flip_original = None
    _anterior = None
    _cuadros.clear()


def _flip():
    global _anterior
    ahora = time.perf_counter()
    if _anterior is not None:
        _cuadros.append((ahora - _anterior) * 1000.0)
        if len(_cuadros) > 120:
            del _cuadros[0:len(_cuadros) - 120]
    _anterior = ahora

    pantalla = pygame.display.get_surface()
    if pantalla is not None and len(_cuadros) >= 10:
        ventana = _cuadros[-60:]
        media = sum(ventana) / len(ventana)
        ordenada = sorted(ventana)
        p95 = ordenada[int(len(ordenada) * 0.95)]
        ui.texto(pantalla, f"{1000 / media:5.1f} fps  {media:5.2f} ms  p95 {p95:5.2f} ms",
                 10, ui.VERDE if media < 17 else ui.ROJO, x=12, y=ui.ALTO - 20,
                 sombra=False)
    return _flip_original()


def reiniciar():
    _cuadros.clear()
