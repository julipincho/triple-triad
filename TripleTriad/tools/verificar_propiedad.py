"""G2: la propiedad de las cartas se reconoce SIN COLOR.

El criterio de aceptacion dice "foco, seleccionado, propio/rival y captura
prevista distinguibles sin depender del color". Este render dibuja las tres
propiedades y las escribe en PNG para poder MIRARLAS, que es la unica forma de
comprobar que una forma se distingue de otra a simple vista.

Ademas mide el contraste entre las tres marcas en su version ACROMATICA (todos
los pixeles a su luminancia), que es la comprobacion objetiva de que no dependen
del color: si convertidas a gris las tres siguen siendo distintas entre si.

    python tools/verificar_propiedad.py
"""

import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_tmp = tempfile.TemporaryDirectory(prefix="tt_prop_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

DESTINO = os.path.join(RAIZ, "capturas")

import pygame  # noqa: E402

import cartas  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
import ui  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


def _luminancia(rgb):
    """Luminancia de un color RGB (acepta tupla)."""
    canales = []
    for v in rgb[:3]:
        c = v / 255.0
        canales.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * canales[0] + 0.7152 * canales[1] + 0.0722 * canales[2]


def silueta(sup, caja, comunes=None):
    """La FORMA de la marca, midiendo su BASE, no su color.

    Cada marca se pinta en dos pasos: una base oscura de forma (cuadrado para
    la propia, rombo para la rival) y encima el color. La base SIEMPRE es
    `(8, 8, 12)`: es el unico elemento de la marca que NO depende ni del dueno
    ni del tinte de la carta. Midiendo esa base se obtiene la forma pura.

    `comunes` son los pixeles oscuros que estan en LAS TRES cartas (sobre todo
    el arco del borde redondeado) y se restan: si no, el borde haria que las
    siluetas difirieran por un motivo que no es la marca.

    Medir el color daria un falso positivo facil: la carta entera se tine por
    dueno (azul, rojo, dorado), asi que tres circulos del mismo color darian
    "siluetas distintas" solo por el fondo, y el test pasaria aunque la
    propiedad hubiera vuelto a depender por completo del color.
    """
    y, x, alto, ancho = caja
    salida = []
    for j in range(alto):
        fila = []
        for i in range(ancho):
            if not comunes:
                fila.append(0)
                continue
            oscuro = _luminancia(sup.get_at((x + i, y + j))[:3]) < 0.02
            fila.append(1 if oscuro and not comunes[j][i] else 0)
        salida.append(fila)
    return salida


def siluetas_comunes(sups, caja):
    """Pixeles oscuros presentes en TODAS las cartas (el borde)."""
    y, x, alto, ancho = caja
    comunes = []
    for j in range(alto):
        fila = []
        for i in range(ancho):
            fila.append(int(all(_luminancia(s.get_at((x + i, y + j))[:3]) < 0.02
                               for s in sups)))
        comunes.append(fila)
    return comunes


def main():
    os.makedirs(DESTINO, exist_ok=True)
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pantalla.fill(ui.FONDO)

    base = mazos.HUMANOS[0]
    marcas = [("T", "PROPIA", ui.AZUL), ("C", "RIVAL", ui.ROJO),
              (None, "LIBRE", ui.DORADO)]

    x0 = 200
    forma = {"T": "marca: cuadrado", "C": "marca: rombo",
             None: "marca: circulo"}
    for i, (dueno, etiqueta, _c) in enumerate(marcas):
        sup = cartas.crear(base, dueno=dueno, escala=2)
        rect = sup.get_rect()
        rect.topleft = (x0 + i * 300, 120)
        pantalla.blit(sup, rect)
        ui.texto(pantalla, etiqueta, 16, ui.DORADO,
                 centro=(rect.centerx, rect.bottom + 40))
        ui.texto(pantalla, forma[dueno], 10, ui.TEXTO_TENUE,
                 centro=(rect.centerx, rect.bottom + 66))
    pygame.display.flip()

    ruta = os.path.join(DESTINO, "g9_14_propiedad_cartas.png")
    pygame.image.save(pantalla, ruta)

    # Comprobacion objetiva: en gris, las tres siluetas NO son identicas.
    print("Comprobacion de la marca de propiedad en gris (sin color):")
    sups = [cartas.crear(base, dueno=d, escala=2) for d, _e, _c in marcas]
    w, h = sups[0].get_size()
    caja = (h - 20, w - 20, 16, 16)
    comunes = siluetas_comunes(sups, caja)
    siluetas = {}
    for sup, (_d, etiqueta, _c) in zip(sups, marcas):
        siluetas[etiqueta] = silueta(sup, caja, comunes)
    nombres = list(siluetas)
    iguales = []
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            if siluetas[nombres[i]] == siluetas[nombres[j]]:
                iguales.append((nombres[i], nombres[j]))
    if iguales:
        print("  FALLO: estas marcas son IDENTICAS en gris:", iguales)
        return 1
    print("  las tres marcas son distintas en gris:", ", ".join(nombres))
    print("  -> la propiedad se lee por FORMA, no solo por color")
    print("  captura:", os.path.basename(ruta))
    return 0


if __name__ == "__main__":
    sys.exit(main())