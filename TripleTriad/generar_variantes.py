"""Genera variantes de los fondos de campana con el ComfyUI local.

Por que variantes y no fondos nuevos: que el lugar se parezca a si mismo a lo
largo de la partida es lo que hace el mundo creible. Cambiar la escena entera
en cada nodo rompe la orientacion; cambiar la HORA DEL DIA o el ESTADO DEL
TIEMPO la deja reconocible y sin repetir.

El reparto sale de medir cuantosBackground uses tiene cada fondo en el guion:
    campamento 36  camino 36  umbral 22  trono 17
    ruinas 12  asalto 10  escenario 10  aldea 8  salon 6  fortaleza 5 ...
Ese top-7 son 143 de 178 marcas, asi que ahi va el presupuesto.

Las variantes se nombran `{escena}_{n}.png` y el fondo sin numero es el
original, que se sigue usando por defecto.

    python generar_variantes.py                 # las 24
    python generar_variantes.py --escena camino  # solo una
    python generar_variantes.py --solo-missing   # no rehace lo que ya existe
"""

import argparse
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RAIZ = os.path.dirname(os.path.abspath(__file__))
#: El ancla de estilo del proyecto. En los fondos si se usa: fija la paleta.
ANCLA_DEFECTO = os.path.join(RAIZ, "estilo", "ancla.png")
DESTINO = os.path.join(RAIZ, "assets", "fondos")

#: Los fondos tienen SU PROPIO estilo, que no es el de las cartas. Mirando los
#: originales: `trono` es pixel art morado y oro, `campamento` pixel art azul y
#: verde, `umbral` pixel art teal. Las cartas si son grabado sepia, y los
#: avatares tambien (por eso los dos que rehice van grabados).
#:
#: La primera tanda de estas variantes se genero en grabado porque me fije en las
#: cartas, y quedaban quince fondos pixel art junto a veinticuatro grabados.
#: Los fondos son de lo mas visto del juego: no pueden ir en otro idioma.
#: Asi que aqui se usa el de los fondos: pixel art de 16 bits, con color.
ESTILO = (
    "16-bit pixel art, retro video game background art, limited color palette, "
    "visible square pixels, dark fantasy landscape, side-on cinematic wide shot, "
    "no characters, no people, no text, no letters, no watermark"
)

NEGATIVO = (
    "text, watermark, signature, letters, words, logo, frame, border, ornate "
    "border, picture frame, paper border, smooth gradients, painterly, 3d "
    "render, photorealistic, anime, cartoon, modern, neon, cyberpunk, sci-fi, "
    "blurry, lowres, jpeg artifacts, vignette"
)

#: `{escena: [(nombre, descripcion)]}`. Cada descripcion cambia el momento, no
#: el lugar: eso es lo que mantiene la escena reconocible.
VARIANTES = {
    "camino": [
        ("amanecer", "the same ash road, first pale gold light through the dead "
                     "trunks, long shadows, mist on the ground"),
        ("nevada", "the same ash road under snow, white drifts over the grey "
                   "ash, flat overcast sky, bare trees heavy with snow"),
        ("niebla", "the same ash road swallowed by thick fog, only the nearest "
                   "trunks visible, dim diffuse light"),
        ("noche", "the same ash road at night, cold moonlight, deep blue-black "
                  "shadows, stars between the branches"),
        ("lluvia", "the same ash road under heavy rain, dark puddles reflecting "
                   "a pale sky, water streaming"),
    ],
    "campamento": [
        ("amanecer", "the same camp, the fire almost out, first light on the "
                     "tents, cold ashes"),
        ("tormenta", "the same camp under a storm, tent flaps taut, lightning "
                     "behind the ridge"),
        ("niebla", "the same camp in thick fog, embers drifting as orange "
                   "motes, tents barely visible"),
        ("lluvia", "the same camp in the rain, water hissing in the fire, "
                   "everyone under canvas"),
        ("asedio", "the same camp at night with a distant line of enemy torches "
                   "coming down the road"),
    ],
    "umbral": [
        ("ancho", "the same threshold rift, wide open, the glowing edge far "
                  "across the frame"),
        ("angosto", "the same threshold rift closed almost shut, a thin bright "
                    "seam in the dark"),
        ("deslumbrante", "the same threshold rift blazing white, the edges "
                         "lost in the glare"),
        ("cerrando", "the same threshold rift collapsing, the gap folding in on "
                     "itself, debris"),
    ],
    "trono": [
        ("derrumbe", "the same throne room with more of the pillars fallen, "
                     "rubble across the floor"),
        ("guardia", "the same throne room with a great dragon coiled behind the "
                    "throne, watching"),
        ("nieve", "the same throne room thick with falling ash, the throne "
                  "half buried"),
    ],
    "ruinas": [
        ("profundo", "the same underground ruins much deeper, a narrow passage "
                     "going down"),
        ("derrumbe", "the same underground ruins with part of the ceiling "
                     "collapsed, rubble and beams"),
        ("brasa", "the same underground ruins with the embers far brighter, "
                  "the walls glowing"),
    ],
    "asalto": [
        ("noche", "the same place of ambush at night, only firelight"),
        ("amanecer", "the same place of ambush at first light, mist and long "
                     "shadows"),
    ],
    "escenario": [
        ("vacio", "the same tournament stage empty after the crowd has gone, "
                  "chairs overturned"),
        ("lleno", "the same tournament stage packed, a wall of silhouettes and "
                  "lanterns"),
    ],
}


def total_variantes():
    return sum(len(v) for v in VARIANTES.values())


def _salida(escena, nombre):
    return os.path.join(DESTINO, "%s_%s.png" % (escena, nombre))


def generar_una(escena, nombre, descripcion, args):
    """Genera una variante. Reusa `generar_cartas_comfyui` con su workflow.

    NO arranca ComfyUI: eso se hace UNA vez en `main`, antes del bucle. Aquí
    estaba el otro bug que multiplied las ventanas.
    """
    import generar_cartas_comfyui as g

    salida = _salida(escena, nombre)
    if os.path.exists(salida) and (args.solo_missing or not args.fuerza):
        print("  ya existe: %s_%s.png" % (escena, nombre))
        return True

    positivo = "%s, %s" % (descripcion, ESTILO)
    negativo = ", ".join(p for p in (g.NEGATIVO, NEGATIVO) if p)
    os.makedirs(os.path.dirname(salida), exist_ok=True)

    random.seed()
    seed = args.seed if args.seed is not None else random.randrange(2 ** 32)
    print("  %s_%s | seed %d | %dx%d" % (escena, nombre, seed,
                                         args.ancho, args.alto))
    ok = g.generar_imagen(args.servidor, positivo, negativo, salida, seed,
                          args.ancho, args.alto, args.steps, args.cfg,
                          args.modelo,
                          ancla=args.ancla if args.ancla else None,
                          peso_ipadapter=args.peso_ipadapter,
                          peso_tipo=args.peso_tipo)
    if ok:
        print("    -> %s" % os.path.basename(salida))
    return bool(ok)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escena", nargs="+",
                    help="genera solo estas escenas")
    ap.add_argument("--fuerza", action="store_true",
                    help="regenera tambien lo existente")
    ap.add_argument("--solo-missing", action="store_true",
                    help="no rehace nada que ya exista")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--ancho", type=int, default=512)
    ap.add_argument("--alto", type=int, default=256)
    ap.add_argument("--steps", type=int, default=26)
    ap.add_argument("--cfg", type=float, default=7.5)
    ap.add_argument("--modelo", default="pixelArtDiffusionXL_spriteShaper.safetensors")
    ap.add_argument("--ancla", default=ANCLA_DEFECTO,
                    help="ancla de estilo. En los FONDOS si se usa: es pixel art "
                         "y es la que fija la paleta del juego. En los avatares "
                         "no, porque mete un marco que las cartas no tienen.")
    ap.add_argument("--peso-ipadapter", type=float, default=0.35)
    ap.add_argument("--peso-tipo", default="style transfer")
    ap.add_argument("--servidor", default="http://127.0.0.1:8188")
    ap.add_argument("--bat-arranque", default=r"E:\AI\start-comfyui.bat")
    ap.add_argument("--espera-arranque", type=int, default=60)
    args = ap.parse_args()

    escenas = args.escena or sorted(VARIANTES)
    desconocidas = [e for e in escenas if e not in VARIANTES]
    if desconocidas:
        raise SystemExit("escena desconocida: %s (conocidas: %s)"
                         % (", ".join(desconocidas), ", ".join(sorted(VARIANTES))))

    pendientes = sum(len(VARIANTES[e]) for e in escenas)
    print("Variantes de fondo: %d en %d escenas -> %s"
          % (pendientes, len(escenas), DESTINO))
    print("Se generan a %dx%d: es el tamano que hace que el fondo escale con "
          "factor entero 3 y no deje barras." % (args.ancho, args.alto))

    hechos = fallos = saltados = 0

    # ComfyUI se arranca UNA vez, aqui, y no por variante. `arrancar_servidor`
    # ya es idempotente (comprueba antes de lanzar), pero llamar a el dentro
    # del bucle era lo que multiplicaba las ventanas de consola.
    import generar_cartas_comfyui as g

    version = g.arrancar_servidor(args.servidor, args.bat_arranque,
                                  args.espera_arranque)
    if version is None:
        raise SystemExit("ComfyUI no respondio en %s" % args.servidor)
    print("ComfyUI %s listo\n" % version)

    for escena in escenas:
        print("\n%s (%d variantes)" % (escena, len(VARIANTES[escena])))
        for nombre, descripcion in VARIANTES[escena]:
            antes = os.path.exists(_salida(escena, nombre))
            ok = generar_una(escena, nombre, descripcion, args)
            if not ok:
                fallos += 1
            elif antes and not args.fuerza:
                saltados += 1
            else:
                hechos += 1
            time.sleep(0.4)

    print("\n%d generadas, %d ya estaban, %d fallos (de %d)"
          % (hechos, saltados, fallos, pendientes))
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())