"""Hoja de contactos: compara variantes de estilo carta a carta (herramienta).

Misma carta, mismo marco, distinto arte: fila por variante y columna por
carta. Es la puerta de entrada de cualquier cambio de estilo — sin esto se
regeneran 251 PNGs a ciegas.

Ademas saca una segunda hoja con el arte "pelado" ampliado, para ver la
rejilla de pixeles, el tramado y los scanlines de cerca (el juego lo pinta
con smoothscale a 56x79 y ahi no se ve nada).

Uso:
    python postprocesar_cartas.py --salida cartas_crt       # antes
    python hoja_contactos.py                               # hoja A/B
    python hoja_contactos.py --variantes original=cartas crt=cartas_crt \\
        --n 6 --escala 1.6 --salida auditoria/hoja.png

Solo para mirar: el juego no importa este modulo.
"""

import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

import cartas as crt  # noqa: E402
import facciones  # noqa: E402
from reglas import Carta  # noqa: E402
from ui import REC  # noqa: E402

MARGEN = 14
SEPARACION = 10
FONDO = (18, 16, 22)
TEXTO = (225, 215, 200)


def _slug(nombre):
    import re
    import unicodedata

    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def elegir_cartas(carpeta, n):
    """Una carta por faccion (las que existan PNG), hasta `n`."""
    if not os.path.isdir(carpeta):
        return []
    grupos = {}
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.lower().endswith(".png"):
            continue
        base = nombre[:-4]
        if "_" not in base:
            continue
        bando, slug = base.split("_", 1)
        grupos.setdefault(bando, []).append((bando, slug))
    elegidas = []
    for bando in sorted(grupos):
        if bando in facciones.FACCIONES or len(grupos) <= n:
            elegidas.append(grupos[bando][0])
        if len(elegidas) >= n:
            break
    # si no llegamos a n con facciones conocadas, completamos con lo que haya
    for bando in sorted(grupos):
        if len(elegidas) >= n:
            break
        elegidas.extend(grupos[bando][1:1 + (n - len(elegidas))])
    return elegidas[:n]


def carta_desde_png(bando, slug):
    """Carta de mentira con los mismos datos que usara el render."""
    nombre = slug.replace("_", " ")
    return Carta(nombre, 4, 3, 2, 1, bando=bando), nombre


def pintar(carta, escala, carpeta):
    """Render de la carta usando el arte de `carpeta` (inyeccion)."""
    ruta = os.path.join(carpeta, f"{carta.bando}_{_slug(carta.nombre)}.png")
    anterior = crt.imagen_carta
    crt._cache.clear()
    if os.path.exists(ruta):
        imagen = pygame.image.load(ruta).convert()
        crt.imagen_carta = lambda c, _img=imagen: _img  # noqa: E731
    else:
        crt.imagen_carta = lambda c: None  # noqa: E731
    try:
        return crt.crear(carta, "T", escala=escala)
    finally:
        crt.imagen_carta = anterior
        crt._cache.clear()


def texto(cadena, tam, color=TEXTO):
    return REC.fuente(tam).render(cadena, True, color)


def hoja_cartas(variantes, elecciones, escala, salida):
    superficies = []
    for etiqueta, carpeta in variantes:
        fila = []
        for bando, slug in elecciones:
            carta, nombre = carta_desde_png(bando, slug)
            fila.append((nombre, pintar(carta, escala, carpeta)))
        superficies.append((etiqueta, fila))

    ancho_celda = max(s.get_width() for _, f in superficies for _, s in f)
    alto_celda = max(s.get_height() for _, f in superficies for _, s in f)
    ancho_etiqueta = max(texto(e, 15).get_width() for e, _ in superficies) + 16
    ancho = MARGEN + ancho_etiqueta + len(elecciones) * (ancho_celda + SEPARACION)
    alto = (MARGEN + 26
            + len(superficies) * (alto_celda + SEPARACION + 20))

    lienzo = pygame.Surface((ancho, alto))
    lienzo.fill(FONDO)
    lienzo.blit(texto("Hoja de contactos — misma carta, distinto estilo", 17),
                (MARGEN, 8))

    y = MARGEN + 26
    for etiqueta, fila in superficies:
        t = texto(etiqueta, 15)
        lienzo.blit(t, (MARGEN, y + alto_celda // 2 - t.get_height() // 2))
        x = MARGEN + ancho_etiqueta
        for nombre, sup in fila:
            lienzo.blit(sup, (x, y))
            n = texto(nombre, 12)
            lienzo.blit(n, (x + (sup.get_width() - n.get_width()) // 2,
                            y + alto_celda + 2))
            x += ancho_celda + SEPARACION
        y += alto_celda + SEPARACION + 20

    pygame.image.save(lienzo, salida)
    return ancho, alto


def hoja_arte(variantes, elecciones, factor, salida):
    """Lo que ve el jugador, ampliado.

    Cada arte se reduce primero a la ventana real de la carta (56x79, igual
    que hace `cartas.crear` con smoothscale) y luego se amplia con vecino mas
    cercano. Asi las dos variantes se comparan en las mismas condiciones y se
    ven la rejilla, el tramado y los scanlines.
    """
    aw, ah = crt.rect_arte(crt.CARD_W, crt.CARD_H)[2:]
    filas = []
    for etiqueta, carpeta in variantes:
        celdas = []
        for bando, slug in elecciones:
            ruta = os.path.join(carpeta, f"{bando}_{slug}.png")
            if not os.path.exists(ruta):
                celdas.append(None)
                continue
            im = pygame.image.load(ruta).convert()
            im = pygame.transform.smoothscale(im, (aw, ah))
            im = pygame.transform.scale(im, (aw * factor, ah * factor))
            celdas.append(im)
        filas.append((etiqueta, celdas))

    ancho_celda = max(c.get_width() for _, f in filas for c in f if c)
    alto_celda = max(c.get_height() for _, f in filas for c in f if c)
    ancho_etiqueta = max(texto(e, 15).get_width() for e, _ in filas) + 16
    ancho = MARGEN + ancho_etiqueta + len(elecciones) * (ancho_celda + SEPARACION)
    alto = MARGEN + 26 + len(filas) * (alto_celda + SEPARACION + 20)

    lienzo = pygame.Surface((ancho, alto))
    lienzo.fill(FONDO)
    lienzo.blit(texto(f"Arte x{factor} — rejilla, tramado y scanlines", 17),
                (MARGEN, 8))
    y = MARGEN + 26
    for etiqueta, celdas in filas:
        t = texto(etiqueta, 15)
        lienzo.blit(t, (MARGEN, y + alto_celda // 2 - t.get_height() // 2))
        x = MARGEN + ancho_etiqueta
        for c in celdas:
            if c is not None:
                lienzo.blit(c, (x, y))
            x += ancho_celda + SEPARACION
        y += alto_celda + SEPARACION + 20

    pygame.image.save(lienzo, salida)
    return ancho, alto


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variantes", nargs="*", default=None,
                        help="nombre=ruta (por defecto: original=cartas "
                             "crt=cartas_crt)")
    parser.add_argument("--n", type=int, default=6, help="cartas a mostrar")
    parser.add_argument("--escala", type=float, default=1.6,
                        help="escala del render de carta (1.6 = como la "
                             "carta ampliada en el juego)")
    parser.add_argument("--factor", type=int, default=6,
                        help="ampliacion de la ventana de arte (56x79)")
    parser.add_argument("--salida", default=None,
                        help="PNG de la hoja de cartas (por defecto "
                             "auditoria/hoja_contactos.png)")
    args = parser.parse_args()

    variantes = args.variantes or ["original=cartas", "crt=cartas_crt"]
    pares = []
    for v in variantes:
        if "=" not in v:
            print(f"Variante mal: {v} (tiene que ser nombre=ruta)")
            sys.exit(2)
        nombre, ruta = v.split("=", 1)
        carpeta = ruta if os.path.isabs(ruta) else os.path.join(RAIZ, ruta)
        if not os.path.isdir(carpeta):
            print(f"No existe {carpeta}: genera antes esa variante.")
            sys.exit(2)
        pares.append((nombre, carpeta))

    elecciones = elegir_cartas(pares[0][1], args.n)
    if not elecciones:
        print(f"No hay PNG en {pares[0][1]}")
        sys.exit(2)

    pygame.init()
    pygame.display.set_mode((100, 100))

    carpeta_aud = os.path.join(RAIZ, "auditoria")
    os.makedirs(carpeta_aud, exist_ok=True)
    salida = args.salida or os.path.join(carpeta_aud, "hoja_contactos.png")

    print("Cartas: " + ", ".join(f"{b}_{s}" for b, s in elecciones))
    print("Variantes: " + ", ".join(e for e, _ in pares))

    w, h = hoja_cartas(pares, elecciones, args.escala, salida)
    print(f"Guardado: {salida} ({w}x{h})")

    salida_arte = os.path.join(carpeta_aud, "hoja_arte.png")
    w2, h2 = hoja_arte(pares, elecciones, args.factor, salida_arte)
    print(f"Guardado: {salida_arte} ({w2}x{h2})")


if __name__ == "__main__":
    main()
