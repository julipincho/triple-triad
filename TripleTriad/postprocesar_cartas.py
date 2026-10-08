"""Post-proceso de estilo: paleta del moodboard, niveles, dithering y scanlines.

Herramienta de desarrollo: el juego nunca importa este modulo.

El arte entra como PNG normal (del ComfyUI o de donde sea) y sale convertido
en la estetica que manda `estilo/estilo.json`:

1. **Rejilla logica** = ventana de arte de la carta (`rect_arte` = 56x79).
   Todo el mundo se piensa a esa resolucion; por eso se genera a 56x79 y se
   sube x2 con vecino mas cercano. En el juego, `smoothscale` a la ventana
   (1/2 exacto) recupera los pixeles identicos: sin borronado.
2. **Niveles**: gamma que lleva el brillo medio al objetivo del moodboard,
   con suelo de legibilidad (la ventana es pequena, no se puede oscurecer
   hasta 59/255 sin perder la carta en el tablero).
3. **Scanlines** de 2 px (periodo 2 en la rejilla logica), opcionales.
4. **Cuantizacion** a la paleta del moodboard con dithering ordenado (Bayer),
   que es el tramado tipico de la pixel art retro.

Uso:
    python postprocesar_cartas.py --entrada cartas --salida cartas_crt
    python postprocesar_cartas.py --entrada cartas --salida cartas_crt \\
        --dither fs --scanlines 0 --brillo-obj 80
    python postprocesar_cartas.py --sobrescribir --fuerza   # en sitio (cuidado)

Solo biblioteca estandar + Pillow.
"""

import argparse
import json
import os
import sys

from PIL import Image

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

import estilo  # noqa: E402

try:
    from facciones import FACCIONES  # noqa: E402
except Exception:  # noqa: BLE001 - el script debe funcionar suelto
    FACCIONES = {}

# La ventana de arte real del juego (cartas.rect_arte con RADIO_ORBE=10):
#   x = 10+14, y = 25, w = 104 - 2*24 = 56, h = 79
GRID_DEFECTO = (56, 79)
ESCALA_SALIDA = 2  # la ventana se pinta con smoothscale a 1/2: vecino x2 = identico

# Matriz de Bayer 4x4 (dithering ordenado, el tipico de 16 bits).
BAYER = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]


# ------------------------------------------------------------------- paleta --

def construir_paleta(max_colores=32, faccion=None):
    """Paleta RGB: los colores del moodboard + variantes claras + acento.

    La ficha llega oscura de por si (brillo 59/255); si solo existieran esos
    colores, todo lo que no fuera sombra se quedaria sin escalonar. Por eso se
    derivan un par de tonos mas claros de los tres mas luminosos.

    Ademas se mete el acento de la faccion de la carta (el mismo que ya mete
    el prompt: "dominant accent color"), que es lo que evita que toda la
    serie acabe en gris: el veredicto de la hoja de contactos fue exactamente
    "paleta excesivamente monocroma".
    """
    hexes = list(estilo.PALETA)
    if not hexes:  # sin ficha: paleta de emergencia con la del proyecto
        hexes = ["#101114", "#3a393b", "#725b4d", "#8b7561", "#794131",
                 "#4b2422", "#ad9883", "#141a21"]
    rgb = [tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in hexes]

    luminos = sorted(rgb, key=lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])
    extras = []
    for tono in luminos[-3:]:
        for paso in (36, 72, 96):
            extras.append(tuple(min(255, c + paso) for c in tono))
    rgb = rgb + extras

    if faccion:
        meta = FACCIONES.get(faccion) or {}
        acento = meta.get("acento")
        if acento:
            rgb.append(tuple(acento[:3]))
            rgb.append(tuple(min(255, int(c * 1.35)) for c in acento[:3]))
        claro_oscuro = meta.get("paleta") or ()
        for tono in claro_oscuro:
            rgb.append(tuple(tono[:3]))

    vista, salida = set(), []
    for c in rgb:
        c = tuple(max(0, min(255, int(v))) for v in c)
        if c not in vista:
            vista.add(c)
            salida.append(c)
    return salida[:max_colores]


# ------------------------------------------------------------------ niveles --

def _media_desde_hist(hist, gamma):
    """Media del histograma tras aplicar v' = 255*(v/255)**gamma."""
    total = suma = 0
    for v, n in enumerate(hist):
        if not n:
            continue
        nuevo = 255.0 * ((v / 255.0) ** gamma)
        suma += nuevo * n
        total += n
    return suma / total if total else 0.0


def gamma_para_objetivo(im, objetivo, intentos=24):
    """Busca la gamma que lleva el brillo medio a `objetivo` (biseccion)."""
    hist = im.convert("L").histogram()
    actual = _media_desde_hist(hist, 1.0)
    if actual <= 0 or objetivo <= 0:
        return 1.0
    bajo, alto = 0.15, 6.0
    for _ in range(intentos):
        medio = (bajo + alto) / 2
        if _media_desde_hist(hist, medio) > objetivo:
            bajo = medio
        else:
            alto = medio
    return (bajo + alto) / 2


def aplicar_gamma(im, gamma):
    if abs(gamma - 1.0) < 1e-3:
        return im
    lut = [max(0, min(255, round(255.0 * ((v / 255.0) ** gamma))))
           for v in range(256)]
    return im.point(lut * 3)


def _croma_medio(im):
    """Media de (max-min) por pixel: la MISMA metrica con la que medimos el
    moodboard (33/255). No vale la S de HSV, que usa otra escala y hacia que
    el controlador desaturara en vez de saturar."""
    px = list(im.convert("RGB").getdata())
    if not px:
        return 0.0
    return sum(max(p) - min(p) for p in px) / len(px)


def aplicar_saturacion(im, factor):
    """Escala la croma alrededor del gris de cada pixel.

    Al ser `rgb' = gris + (rgb - gris) * factor`, la distancia (max-min) de
    cada pixel cambia exactamente por `factor`, que es la metrica que
    controlamos.
    """
    if abs(factor - 1.0) < 1e-3:
        return im
    im = im.convert("RGB")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            gris = (r + g + b) / 3.0
            px[x, y] = (
                max(0, min(255, int(round(gris + (r - gris) * factor)))),
                max(0, min(255, int(round(gris + (g - gris) * factor)))),
                max(0, min(255, int(round(gris + (b - gris) * factor)))),
            )
    return im


def saturacion_para_objetivo(im, objetivo, correcciones=2):
    """Factor que lleva la media de (max-min) a `objetivo`.

    La relacion es lineal, asi que basta con dividir; se repite un par de
    veces porque el recorte a [0, 255] algo se lo carga.
    """
    actual = _croma_medio(im)
    if actual <= 0 or objetivo <= 0:
        return 1.0
    factor = objetivo / actual
    for _ in range(correcciones):
        actual = _croma_medio(aplicar_saturacion(im, factor))
        if actual > 0:
            factor *= objetivo / actual
    return factor


# --------------------------------------------------------------- scanlines ---

def aplicar_scanlines(im, periodo=2, fuerza=0.18):
    """Oscurece una de cada `periodo` filas: el tramado CRT de 2 pixeles."""
    if fuerza <= 0:
        return im
    px = im.load()
    w, h = im.size
    for y in range(0, h, periodo):
        for x in range(w):
            r, g, b = px[x, y]
            px[x, y] = (int(r * (1 - fuerza)), int(g * (1 - fuerza)),
                        int(b * (1 - fuerza)))
    return im


# -------------------------------------------------------------- cuantizar ---

def _mas_cercano(r, g, b, paleta):
    mejor, d_mejor = paleta[0], None
    for c in paleta:
        d = (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2
        if d_mejor is None or d < d_mejor:
            mejor, d_mejor = c, d
            if d == 0:
                break
    return mejor


def cuantizar_bayer(im, paleta, amplitud=26.0):
    """Dithering ordenado: el tramado fijo de la pixel art clasica.

    Desplaza el color de cada pixel segun su posicion en la matriz de Bayer
    antes de buscar el color mas cercano de la paleta, asi los degradados se
    resuelven con un patron regular en vez de con ruido.
    """
    im = im.convert("RGB")
    px = im.load()
    w, h = im.size
    salida = Image.new("RGB", (w, h))
    po = salida.load()
    for y in range(h):
        fila = BAYER[y % 4]
        for x in range(w):
            r, g, b = px[x, y]
            desfase = (fila[x % 4] / 16.0 - 0.5) * amplitud
            r = max(0, min(255, int(r + desfase)))
            g = max(0, min(255, int(g + desfase)))
            b = max(0, min(255, int(b + desfase)))
            po[x, y] = _mas_cercano(r, g, b, paleta)
    return salida


def cuantizar_pil(im, paleta, dither=Image.Dither.FLOYDSTEINBERG):
    """Cuantizacion con la paleta fija via Pillow (mas rapida que la nuestra)."""
    plancha = Image.new("P", (1, 1))
    flat = []
    for c in paleta:
        flat.extend(c)
    flat.extend(paleta[-1] * (256 - len(paleta)))  # relleno: colores repetidos
    plancha.putpalette(flat)
    return im.convert("RGB").quantize(palette=plancha, dither=dither).convert("RGB")


# ------------------------------------------------------------- transformacion --

def procesar_imagen(ruta_entrada, paleta, grid=GRID_DEFECTO, escala=ESCALA_SALIDA,
                    dither="bayer", brillo_obj=74.0, sat_obj=33.0,
                    scanlines=0.18, amplitud=26.0):
    """Devuelve la imagen ya en la estetica del moodboard."""
    im = Image.open(ruta_entrada).convert("RGB")

    # 1. a la rejilla logica (la ventana de la carta)
    if im.size != grid:
        im = im.resize(grid, Image.BOX)

    # 2. niveles: brillo y saturacion a los valores del moodboard
    gamma = gamma_para_objetivo(im, brillo_obj)
    im = aplicar_gamma(im, gamma)
    factor = saturacion_para_objetivo(im, sat_obj)
    im = aplicar_saturacion(im, factor)

    # 3. scanlines CRT (2 pixeles en rejilla logica = 1 px en la ventana)
    im = aplicar_scanlines(im, periodo=2, fuerza=scanlines)

    # 4. cuantizacion a la paleta del moodboard
    if dither == "bayer":
        im = cuantizar_bayer(im, paleta, amplitud=amplitud)
    elif dither == "fs":
        im = cuantizar_pil(im, paleta, Image.Dither.FLOYDSTEINBERG)
    else:
        im = cuantizar_pil(im, paleta, Image.Dither.NONE)

    # 5. subir x `escala` con vecino mas cercano: en el juego el smoothscale
    #    a la ventana es 1/2 exacto y devuelve estos mismos pixeles.
    if escala != 1:
        im = im.resize((grid[0] * escala, grid[1] * escala), Image.NEAREST)
    return im, {"gamma": round(gamma, 3), "saturacion": round(factor, 3)}


# ---------------------------------------------------------------------- CLI --

def listar_png(carpeta):
    return sorted(f for f in os.listdir(carpeta) if f.lower().endswith(".png"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", default=os.path.join(RAIZ, "cartas"),
                        help="carpeta con los PNG originales")
    parser.add_argument("--salida", default=os.path.join(RAIZ, "cartas_crt"),
                        help="carpeta destino (se crea si no existe)")
    parser.add_argument("--sobrescribir", action="store_true",
                        help="escribe en la propia carpeta de entrada")
    parser.add_argument("--fuerza", action="store_true",
                        help="procesa aunque el PNG de salida ya exista")
    parser.add_argument("--grid", default="56x79",
                        help="rejilla logica = ventana de arte (56x79)")
    parser.add_argument("--escala", type=int, default=ESCALA_SALIDA,
                        help="subida por vecino mas cercano (2 = 112x158)")
    parser.add_argument("--dither", default="bayer",
                        choices=["bayer", "fs", "ninguno"])
    parser.add_argument("--brillo-obj", type=float, default=90.0,
                        help="brillo medio objetivo (90: validado en la hoja "
                             "de contactos, +5%% sobre el 86 de la 2a ronda)")
    parser.add_argument("--sat-obj", type=float, default=40.0,
                        help="saturacion media objetivo pre-cuantizacion "
                             "(el moodboard marca 33; la cuantizacion se "
                             "carga ~un tercio)")
    parser.add_argument("--scanlines", type=float, default=0.15,
                        help="fuerza de los scanlines (0 = sin scanlines; "
                             "0.15 validado)")
    parser.add_argument("--amplitud", type=float, default=14.0,
                        help="amplitud del dithering Bayer (14: el dither "
                             "fuerte ensucia los rostros)")
    parser.add_argument("--max-colores", type=int, default=32)
    parser.add_argument("--solo", nargs="*", help="solo estos PNG (nombres)")
    args = parser.parse_args()

    try:
        ancho, alto = (int(x) for x in args.grid.lower().split("x"))
    except ValueError:
        print("--grid tiene que ser WxH, por ejemplo 56x79")
        sys.exit(2)
    grid = (ancho, alto)

    if not os.path.isdir(args.entrada):
        print(f"No existe la carpeta de entrada: {args.entrada}")
        sys.exit(2)

    destino = args.entrada if args.sobrescribir else args.salida
    os.makedirs(destino, exist_ok=True)

    paleta_base = construir_paleta(args.max_colores)
    print(f"Paleta base ({len(paleta_base)} colores): "
          + " ".join("#%02x%02x%02x" % c for c in paleta_base[:12])
          + (" ..." if len(paleta_base) > 12 else "")
          + (" | + acento por faccion" if FACCIONES else ""))
    print(f"Rejilla {grid[0]}x{grid[1]} -> salida "
          f"{grid[0] * args.escala}x{grid[1] * args.escala} | "
          f"dither {args.dither} | brillo {args.brillo_obj} | "
          f"sat {args.sat_obj} | scanlines {args.scanlines} | "
          f"amplitud {args.amplitud}")

    nombres = listar_png(args.entrada)
    if args.solo:
        nombres = [n for n in nombres if n in set(args.solo)]
    if not nombres:
        print("No hay PNG que procesar.")
        sys.exit(2)

    params = {
        "grid": list(grid), "escala": args.escala, "dither": args.dither,
        "brillo_obj": args.brillo_obj, "sat_obj": args.sat_obj,
        "scanlines": args.scanlines,
        "amplitud": args.amplitud, "max_colores": args.max_colores,
        "paleta": ["#%02x%02x%02x" % c for c in paleta_base],
        "acento_por_faccion": bool(FACCIONES),
        "fuente": args.entrada,
    }
    hechas = omitidas = fallos = 0
    gammas, factores = [], []
    for nombre in nombres:
        origen = os.path.join(args.entrada, nombre)
        final = os.path.join(destino, nombre)
        if os.path.exists(final) and not args.fuerza and not args.sobrescribir:
            omitidas += 1
            continue
        # el acento de la faccion va en la paleta de ESA carta: el nombre del
        # archivo es {faccion}_{slug}.png, igual que lo escribe cartas.py
        faccion = nombre[:-4].split("_", 1)[0]
        paleta = (construir_paleta(args.max_colores, faccion)
                  if FACCIONES and faccion in FACCIONES else paleta_base)
        try:
            im, extra = procesar_imagen(origen, paleta, grid=grid,
                                        escala=args.escala, dither=args.dither,
                                        brillo_obj=args.brillo_obj,
                                        sat_obj=args.sat_obj,
                                        scanlines=args.scanlines,
                                        amplitud=args.amplitud)
            im.save(final)
            gammas.append(extra["gamma"])
            factores.append(extra["saturacion"])
            hechas += 1
        except Exception as e:  # noqa: BLE001 - no parar un lote por una foto
            print(f"  fallo con {nombre}: {e}")
            fallos += 1

    params["gamma_media"] = (round(sum(gammas) / len(gammas), 3) if gammas else None)
    params["factor_saturacion_media"] = (
        round(sum(factores) / len(factores), 3) if factores else None)
    with open(os.path.join(destino, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Listo: {hechas} procesadas, {omitidas} omitidas, {fallos} fallos "
          f"-> {destino}")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
