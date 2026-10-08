"""Genera las imagenes del mundo del juego con ComfyUI (herramienta).

Que genera: retratos, escenas de encuentro, siluetas y fondos de cinematica.
NO genera cartas: esas las hace `generar_cartas_comfyui.py` y no se tocan.

Como esta separado
------------------
El pipeline de cartas (estilo.json oscuro -> SpriteShaper -> postproceso CRT)
y este (estilo anime -> Animagine -> downscale nearest) son dos cadenas
distintas. Aqui se importa el TRANSPORTE de `generar_cartas_comfyui`
(`generar_imagen`, `arrancar_servidor`) sin modificar ese archivo. Lo unico que
se reusa es la forma de hablar con ComfyUI.

Lo que produce el pixel art
---------------------------
El checkpoint es de anime, no de pixel art. El pixel sale del ultimo paso: se
genera a `ESCALA_GENERACION` veces el tamano destino y se reduce con vecino mas
cercano. Asi los bloques de color son cuadrados de verdad, sin filtro. No se
pasa por `postprocesar_cartas.py`: su rejilla de 56x79 es para cartas y sus
scanlines son justo lo que aqui no queremos.

El juego nunca importa este modulo.

Uso:
    python generar_escenas.py --listar
    python generar_escenas.py --nara --semilla 1234
    python generar_escenas.py --duelista --variantes        # hoja de contactos
    python generar_escenas.py --todos
    python generar_escenas.py --nara --solo-prompt          # imprime el prompt
    python generar_escenas.py --lote mis_imagenes.json

Solo biblioteca estandar + Pillow.
"""

import argparse
import json
import os
import random
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import estilo_escenas as est  # noqa: E402

# Transporte de ComfyUI: se importa, no se reescribe ni se modifica.
import generar_cartas_comfyui as comfy  # noqa: E402

COMFY_URL = comfy.COMFY_URL
BAT_ARRANQUE = r"E:\AI\start-comfyui.bat"

#: Donde cae cada tipo de imagen. Los nombres los consume el juego.
CARPETA_AVATARES = os.path.join(BASE, "assets")
CARPETA_ESCENAS = os.path.join(BASE, "assets", "escenas")
CARPETA_FONDOS = os.path.join(BASE, "assets", "fondos")

STEPS_DEFECTO = 28
CFG_DEFECTO = 6.0
#: Animagine rinde mejor con sampler/scheduler propios, pero el transporte
#: compartido usa euler/normal. Con euler hay que bajar un poco el cfg.
CFG_ANIME = 7.0

# --------------------------------------------------------------- el catalogo
# Cada imagen: quien es, como se ve, en que encuadre y a donde va.
#
# `sujeto` va en convencion danbooru (tags separados por coma), que es lo que
# espera Animagine XL. No es una frase: son palabras clave.

CATALOGO = {
    # ---- los tres avatares, que son lo primero -----------------------
    # El duelista NO tiene rostro: es el jugador. De espaldas y encapuchado.
    "duelista": {
        "archivo": "avatar_duelista.png",
        "tipo": "avatar",
        "encuadre": "silueta",
        "sujeto": "1boy, back view, from behind, hooded long coat, cloak, "
                  "no face visible, face hidden, featureless, standing, "
                  "holding a deck of cards",
        "extra": "",
        "notas": "El protagonista no tiene nombre ni cara. Si el modelo le "
                 "pone cara, es un fallo: hay que repetir con mas peso en "
                 "'no face visible'.",
    },
    # Nara, la Cronista: el unico acompanante. Habla en toda la campana.
    "nara": {
        "archivo": "avatar_nara.png",
        "tipo": "avatar",
        "encuadre": "retrato",
        "sujeto": "1girl, dark skin, braided hair, scholar, open leather "
                  "book, ink-stained fingers, ink pot, curious expression, "
                  "traveler's cloak, confident",
        "extra": "",
        "notas": "Cronista, no guerrera. Llaves: libro abierto y tinta en los "
                 "dedos. Si sale con arma, se le Noto combatiente.",
    },
    # Juan Rajoy: el rival de la ronda clasificatoria. Habla en el prologo.
    "rajoy": {
        "archivo": "avatar_rajoy.png",
        "tipo": "avatar",
        "encuadre": "retrato",
        # Lo que pidio el jugador: flaco, pelo largo hasta el cuello, anteojos,
        # cabello marron. Se pone al principio del sujeto porque el checkpoint
        # pesa mas lo que esta antes.
        "sujeto": "1boy, older man, thin, gaunt hollow cheeks, prominent "
                  "nose, long straight brown hair to neck length, brown "
                  "hair, glasses, round spectacles, card game tournament "
                  "player, polo shirt, lanyard badge, friendly confident "
                  "smile",
        "extra": "",
        "notas": "Un competidor mas del torneo, no un jefe. Flaco, pelo largo "
                 "al cuello, anteojos, cabello marron. Vestimenta casual "
                 "moderna de torneo, no heroica.",
    },
    # ---- los cinco rivales de la campana -----------------------------
    # Los personajes con nombre del arco. Son los que aparecen en las
    # cinematicas con voz propia, asi que necesitan cara reconocible: si el
    # avatar de faction no alcanza, estos son los que cuentan la historia.
    "pik": {
        "archivo": "avatar_pik.png",
        "tipo": "avatar",
        "encuadre": "retrato",
        "sujeto": "1goblin, young, nervous expression, large ears, "
                  "patched leather vest, short crooked tusk, shuffling cards "
                  "uneasily, scared",
        "extra": "",
        "notas": "El primero que el duelista ve vivo. Dice 'no quiero pelear'. "
                 "Tiene que verse asustado de verdad, no bravocon.",
    },
    "dara": {
        "archivo": "avatar_dara.png",
        "tipo": "avatar",
        "encuadre": "retrato",
        "sujeto": "1woman, village guard, stern protective expression, "
                  "short dark hair, worn leather armor with scratched metal "
                  "pauldron, hand on sword hilt, alert",
        "extra": "",
        "notas": "Guardiana de la aldea. Protege a su gente, no odia al "
                 "duelista. Firme, no cruel.",
    },
    "jefe_arco": {
        "archivo": "avatar_jefe_arco.png",
        "tipo": "avatar",
        "encuadre": "retrato",
        "sujeto": "1man, older commander, grey beard, heavy plate armor, "
                  "weathered scars, tired eyes that have seen too much, "
                  "heavy cloak, holding a helm under one arm",
        "extra": "",
        "notas": "Sabe del Umbral mas que nadie y por eso intenta que nadie "
                 "llegue. Es el rival con mas peso moral.",
    },
    "revancha": {
        "archivo": "avatar_revancha.png",
        "tipo": "avatar",
        "encuadre": "retrato",
        "sujeto": "1woman, bitter grimace, dark messy hair, battle-worn "
                  "armor, arms crossed, refusing to back down, defiant",
        "extra": "",
        "notas": "Vuelve porque perdio y no lo olvido. Rabia contenida, no "
                 "gritos.",
    },
    "gobernante": {
        "archivo": "avatar_gobernante.png",
        "tipo": "avatar",
        "encuadre": "retrato",
        "sujeto": "1man, sovereign, exhausted calm, long dark coat with "
                  "high collar, thin circlet, knowing sorrowful eyes, "
                  "standing straight, no armor",
        "extra": "",
        "notas": "El ultimo rival. No es malvado: esta cansado de cargar con "
                 "el Umbral. Sin armadura: manda con la palabra.",
    },
    # ---- los seis encuentros ----------------------------------------
    "mercader": {
        "archivo": "escenas/mercader.png",
        "tipo": "escena",
        "encuadre": "escena",
        "sujeto": "1man, hooded wandering merchant, pile of odd trinkets, "
                  "canvas pack, open card case, shrewd eyes, night camp",
        "extra": "warm lantern light",
        "notas": "El que reconoce que las cartas del duelista valen 400 anos.",
    },
    "anciano": {
        "archivo": "escenas/anciano.png",
        "tipo": "escena",
        "encuadre": "escena",
        "sujeto": "1old man, tattered hood, long white beard, knowing smile, "
                  "standing among ruins, faint violet glow",
        "extra": "",
        "notas": "Sabe mas de lo que dice. La pista: que parezca que sabe, no que parezca loco.",
    },
    "hermandad": {
        "archivo": "escenas/hermandad.png",
        "tipo": "escena",
        "encuadre": "escena",
        "sujeto": "small group of armored warriors around a campfire, "
                  "sharing a flask, tired but loyal, night",
        "extra": "",
        "notas": "Companenos que ya pelearon a tu lado. Grupo, no lider.",
    },
    "caravana": {
        "archivo": "escenas/caravana.png",
        "tipo": "escena",
        "encuadre": "escena",
        "sujeto": "traveling merchant caravan, covered wagons, sealed card "
                  "boxes for sale, lantern string, dusk road",
        "extra": "",
        "notas": "Vende sobres cerrados. Que se lean sobres, no solo carruajes.",
    },
    "hostil": {
        "archivo": "escenas/hostil.png",
        "tipo": "escena",
        "encuadre": "escena",
        "sujeto": "1man, waist up, mouth open demanding an answer, "
                  "pointing forward with an outstretched accusing finger, "
                  "suspicious glare, tense shoulders, hands empty, "
                  "close forest path background",
        "extra": "cold light, overcast",
        "neg_extra": "sword, weapon, attacking, swinging, fighting, "
                     "armor, helmet",
        "notas": "Te vio con cartas imposibles. Hostil, no menacing.",
    },
    "nara_encuentro": {
        "archivo": "escenas/nara.png",
        "tipo": "escena",
        "encuadre": "escena",
        # Se replica el avatar APROBADO casi palabra por palabra: el pelo en
        # bun con trenza gruesa, los aros dorados, la capa morada con cuello
        # de pelo. Si se describe distinto, el modelo te dibuja otra persona y
        # el jugador no la reconoce entre el prologo y la campana.
        "sujeto": "1girl, dark skin, dark brown hair in a bun with one thick "
                  "braid, gold hoop earrings, purple coat with white fur "
                  "collar, teal beaded necklace, open leather book, "
                  "confronting the viewer, surprised, forest clearing",
        "extra": "",
        "notas": "Tiene que ser la MISMA Nara del avatar aprobado. Duda de "
                 "duda: si el pelo o la ropa cambian, no es ella.",
    },
    # ---- los dos fondos del mundo real ------------------------------
    "salon": {
        "archivo": "fondos/salon.png",
        "tipo": "fondo",
        "encuadre": "fondo",
        "sujeto": "large modern indoor esports tournament hall, rows of "
                  "tables, hanging banners, big screens, crowd of players, "
                  "overhead lighting rigs",
        "extra": "cool white and teal stage lighting, no people in foreground",
        "notas": "Nuestro mundo: el salon del torneo. Debe leerse MODERNO y "
                 "electrico frente al mundo fantastic. Sin ningun personaje "
                 "en primer plano: aqui no hay duelistas dibujados.",
    },
    "apagon": {
        "archivo": "fondos/apagon.png",
        "tipo": "fondo",
        "encuadre": "fondo",
        "sujeto": "darkened empty hall, every light out, total darkness, "
                  "only faint dim emergency exit sign, abandoned, dust in "
                  "the air, scattered playing cards on the floor",
        "extra": "very dark, near monochrome, very low light, deep shadow",
        "neg_extra": "bright, sunny, well lit, daylight, colorful, vibrant, "
                     "saturated, neon, glowing, lit up",
        "notas": "El corte. Casi negro, con las cartas regadas en el suelo.",
    },
}


# --------------------------------------------------------------- utilidades ---

def _slug(nombre):
    import re
    base = (nombre or "").lower().strip()
    for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
                 ("ñ", "n"), ("ü", "u")):
        base = base.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", base).strip("_")


def _destino(entrada):
    """Ruta absoluta de salida de una entrada del catalogo."""
    return os.path.join(BASE, "assets", entrada["archivo"].replace("/", os.sep))


def _variantes(entrada):
    """Variantes de prompt para la hoja de contactos.

    Cambiar UNA cosa por variante (encuadre o estilo) deja claro que senal
    funciona; cambiarlo todo a la vez no dice nada.
    """
    base_estilo = est.ESTILO_DEFECTO
    return [
        ("pixel", base_estilo),
        ("anime", "anime"),
        ("pixel_limpio", "pixel_limpio"),
    ]


def _escala(entrada, factor=None):
    """Tamano destino y tamano de generacion (multiplo del destino)."""
    w, h = est.MEDIDAS[entrada["encuadre"]]
    f = factor or est.ESCALA_GENERACION
    return (w, h), (w * f, h * f)


def _reducir(ruta_origen, destino, tam_destino):
    """Reduce con vecino mas cercano: eso es lo que produce los pixeles."""
    from PIL import Image
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with Image.open(ruta_origen) as im:
        im = im.convert("RGBA")
        if im.size != tuple(tam_destino):
            im = im.resize(tam_destino, Image.NEAREST)
        im.save(destino)
    return destino


def _variantes_de_prompt(entrada):
    """(nombre_variante, positivo, negativo) para cada variante de estilo."""
    salida = []
    for nombre, estilo in _variantes(entrada):
        positivo = est.construir_prompt(
            entrada["sujeto"], encuadre=entrada["encuadre"], estilo=estilo,
            extra=entrada.get("extra", ""))
        salida.append((nombre, positivo,
                       est.construir_negativo(
                           extra=entrada.get("neg_extra", ""),
                           retrato=(entrada["tipo"] == "avatar"))))
    return salida


# ------------------------------------------------------------------ generar ---

def generar_uno(servidor, clave, variante="pixel", semilla=None, modelo=None,
                pasos=STEPS_DEFECTO, cfg=CFG_ANIME, factor=None,
                salida=None, solo_prompt=False):
    """Genera una imagen del catalogo. Devuelve la ruta escrita, o None."""
    entrada = CATALOGO[clave]
    estilo_nombre = dict((n, e) for n, e in _variantes(entrada))[variante]
    positivo = est.construir_prompt(
        entrada["sujeto"], encuadre=entrada["encuadre"], estilo=estilo_nombre,
        extra=entrada.get("extra", ""))
    negativo = est.construir_negativo(
        extra=entrada.get("neg_extra", ""),
        retrato=(entrada["tipo"] == "avatar"))
    (dw, dh), (gw, gh) = _escala(entrada, factor)
    semilla = semilla if semilla is not None else random.getrandbits(32)
    modelo = modelo or est.CHECKPOINT

    if solo_prompt:
        print(f"--- {clave} [{variante}] ---")
        print(f"positivo: {positivo}")
        print(f"negativo: {negativo}")
        print(f"modelo:   {modelo}")
        print(f"tamano:   {gw}x{gh} -> {dw}x{dh}")
        print(f"semilla:  {semilla}")
        return None

    destino = salida or _destino(entrada)
    temporal = os.path.join(os.environ.get("TEMP", BASE), f"gen_{clave}_{variante}.png")
    print(f"  {clave} [{variante}] {gw}x{gh} -> {dw}x{dh} (semilla {semilla})")
    ok = comfy.generar_imagen(
        servidor, positivo, negativo, temporal, semilla,
        gw, gh, pasos, cfg, modelo,
        ancla=None, peso_ipadapter=est.PESO_IPADAPTER)
    if not ok:
        print("  fallo la generacion")
        return None
    return _reducir(temporal, destino, (dw, dh))


def _servidor(args):
    version = comfy.comprobar_servidor(args.servidor)
    if version:
        return version
    if args.no_arrancar:
        print("ComfyUI no responde y --no-arrancar esta puesto.")
        return None
    return comfy.arrancar_servidor(args.servidor, BAT_ARRANQUE, args.espera)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--listar", action="store_true", help="muestra el catalogo")
    p.add_argument("--todos", action="store_true", help="genera todo")
    p.add_argument("--solo", nargs="*", help="genera solo estas claves")
    p.add_argument("--solo-prompt", action="store_true",
                   help="solo imprime el prompt, no genera")
    p.add_argument("--variante", default="pixel",
                   choices=("pixel", "anime", "pixel_limpio"))
    p.add_argument("--semilla", type=int, default=None)
    p.add_argument("--modelo", default=None)
    p.add_argument("--pasos", type=int, default=STEPS_DEFECTO)
    p.add_argument("--cfg", type=float, default=CFG_ANIME)
    p.add_argument("--factor", type=int, default=None,
                   help="multiplo de generacion sobre el destino")
    p.add_argument("--salida", default=None)
    p.add_argument("--servidor", default=COMFY_URL)
    p.add_argument("--no-arrancar", action="store_true")
    p.add_argument("--espera", type=int, default=300)
    p.add_argument("--lote", default=None, help="JSON con una lista de claves")
    args = p.parse_args()

    if args.listar:
        print("catalogo de escenas:")
        for clave, e in CATALOGO.items():
            print(f"  {clave:18s} {e['tipo']:7s} {e['encuadre']:13s} -> {e['archivo']}")
        return 0

    claves = []
    if args.lote:
        with open(args.lote, encoding="utf-8") as f:
            datos = json.load(f)
        claves = [d["clave"] if isinstance(d, dict) else d for d in datos]
    elif args.solo:
        claves = args.solo
    elif args.todos:
        claves = list(CATALOGO)
    else:
        p.print_help()
        return 1

    desconocidas = [c for c in claves if c not in CATALOGO]
    if desconocidas:
        print(f"claves desconocidas: {desconocidas}")
        print(f"disponibles: {', '.join(CATALOGO)}")
        return 1

    if args.solo_prompt:
        for clave in claves:
            generar_uno(args.servidor, clave, variante=args.variante,
                        semilla=args.semilla, modelo=args.modelo,
                        salida=args.salida, solo_prompt=True)
        return 0

    print(f"Comprobando ComfyUI en {args.servidor}...")
    version = _servidor(args)
    if not version:
        print("Sin ComfyUI: no puedo generar.")
        return 1
    print(f"ComfyUI {version} | checkpoint {args.modelo or est.CHECKPOINT}")
    print(f"IPAdapter: {'activo' if est.USAR_IPADAPTER else 'desactivado (el ancla de cartas no aplica aqui)'}")
    print()

    hechos, fallidos = [], []
    for clave in claves:
        r = generar_uno(args.servidor, clave, variante=args.variante,
                        semilla=args.semilla, modelo=args.modelo,
                        pasos=args.pasos, cfg=args.cfg, factor=args.factor,
                        salida=args.salida)
        (hechos if r else fallidos).append(clave)
        time.sleep(0.5)

    print()
    print(f"generadas {len(hechos)}: {', '.join(hechos) or '-'}")
    if fallidos:
        print(f"fallidas {len(fallidos)}: {', '.join(fallidos)}")
    return 0 if not fallidos else 1


if __name__ == "__main__":
    sys.exit(main())
