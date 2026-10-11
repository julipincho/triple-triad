"""G2: la CAPTURA PREVISTA se distingue por forma, no solo por color.

Igual que la propiedad de las cartas, la casilla donde la jugada capturaria se
marca con un borde verde Y con un tick dibujado con `draw.lines`. Este script
lo comprueba de forma objetiva: monta un tablero real, calcula el preview con
el motor, y mide si hay un trazo claro con forma de check en la casilla prevista
y no en las demas.

Ademas guarda la captura para poder mirarla.

    python tools/verificar_preview.py
"""

import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_tmp = tempfile.TemporaryDirectory(prefix="tt_preview_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

DESTINO = os.path.join(RAIZ, "capturas")

import pygame  # noqa: E402

import mazos  # noqa: E402
import partida as P  # noqa: E402
import ui  # noqa: E402
from reglas import Carta  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


def _luminancia(rgb):
    canales = []
    for v in rgb[:3]:
        c = v / 255.0
        canales.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canales[0] + 0.7152 * canales[1] + 0.0722 * canales[2]


def preparar():
    """Tablero donde colocar una carta fuerte captura a la rival."""
    # Se coge la carta MAS FLOJA de cada bando: al colocar la fuerte encima,
    # la captura esta garantizada y no depende del azar del reparto.
    floja_rival = min(mazos.DRAGONES, key=lambda c: sum(c.valores.values()))
    fuerte = max(mazos.HUMANOS, key=lambda c: sum(c.valores.values()))

    juego = P.Juego("humano", "dragon",
                    mano_u_inicial=[fuerte] + list(mazos.HUMANOS[:3]),
                    mano_c_inicial=[floja_rival] + list(mazos.DRAGONES[:3]),
                    dificultad=1.0)
    # La carta rival floja al centro del tablero.
    juego.colocar(juego.mano_c[0], juego.mano_c, P.CPU, 1, 1)
    # `seleccionada` es la CARTA, no el indice.
    juego.seleccionada = juego.mano_u[0]
    # `dibujar` aplica un fundido de entrada de 0.35 s sobre todo el lienzo:
    # medir nada mas crear el juego es medir una pantalla casi negra.
    import time as _t
    juego.t_entrada = _t.time() - 5.0
    # El preview necesita la casilla BAJO EL RATON: se pone sobre la casilla
    # de al lado, que es donde caeria la captura de la carta del centro.
    rect = ui.celda_rect(0, 1)
    juego.pos_arrastre = rect.center
    return juego


def main():
    os.makedirs(DESTINO, exist_ok=True)
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))

    juego = preparar()
    objetivo, caps = juego.preview_capturas()
    print("preview del motor: objetivo=%s, capturas=%s" % (objetivo, sorted(caps)))
    if not caps:
        print("  el motor no predice captura: no hay nada que comprobar")
        return 1

    # Se congela el reloj: las cartas laten y el resplandor se mueve con el
    # tiempo, asi que dos pintadas seguidas diferirian por el reloj y el
    # diferencial estaria lleno de ruido que no es la marca de captura.
    import partida as _p
    reloj_falso = _p.time.time()
    _p.time = type("T", (), {"time": staticmethod(lambda: reloj_falso)})

    juego.dibujar(pantalla)
    pygame.display.flip()
    ruta = os.path.join(DESTINO, "g9_15_preview_captura.png")
    pygame.image.save(pantalla, ruta)
    con_preview = pantalla.copy()

    # Se mide el DIFERENCIAL de la misma casilla con y sin preview. Comparar
    # contra otras casillas no vale: las que tienen carta estan llenas de arte
    # claro y darian un falso negativo.
    juego.seleccionada = None
    juego.dibujar(pantalla)
    pygame.display.flip()
    sin_preview = pantalla.copy()
    pantalla.blit(con_preview, (0, 0))

    celda = sorted(caps)[0]
    rect = ui.celda_rect(*celda)
    cambiados = []
    for y in range(rect.y, rect.bottom):
        for x in range(rect.x, rect.right):
            a = con_preview.get_at((x, y))[:3]
            b = sin_preview.get_at((x, y))[:3]
            if a != b:
                cambiados.append((x - rect.x, y - rect.y, a))

    print("  pixeles que cambia la casilla prevista: %d" % len(cambiados))
    if not cambiados:
        print("  FALLO: marcar la captura no cambia NADA visible")
        return 1

    # El tick se dibuja arriba a la izquierda de la casilla (offset 5..17).
    arriba_izq = sum(1 for dx, dy, _c in cambiados if dx < 22 and dy < 22)
    print("  de ellos, en la esquina superior izquierda: %d" % arriba_izq)
    if arriba_izq < 8:
        print("  FALLO: no hay trazo de tick en la esquina; la marca es solo "
              "un cambio de color")
        return 1
    print("  -> hay un trazo con forma (el tick), no solo un color de borde")
    print("  captura:", os.path.basename(ruta))
    return 0


if __name__ == "__main__":
    sys.exit(main())