"""Genera el arte de cartas, avatares y fondos con Pollinations.

Uso:
    python generar_cartas.py            # solo lo que falta
    python generar_cartas.py --fuerza   # regenera todo
"""

import argparse
import os
import re
import time
import urllib.parse
import urllib.request

from mazos import TODOS

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cartas")
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

RAZA = {
    "humano": "human knight",
    "orco": "orc warrior",
    "goblin": "goblin",
    "elfo": "elf",
    "hombre_lobo": "werewolf",
    "vampiro": "vampire",
    "dragon": "dragon",
    "elfo_nocturno": "dark elf",
    "hombre_pantera": "panther warrior",
    "hombre_lagarto": "lizardman warrior",
}

#: Sufijo comun a los avatares.
#:
#: El estilo se decidio DESPUES de mirar las cartas de verdad, no al reves. El
#: prompt decia "pixel art style" y el resultado salia anime: pelo azul, ojos
#: grandes, capuchas y ciudades neon. Las cartas, que pasan por el mismo
#: pipeline, salen grabados medievales en sepia. Para el mismo bando, dos
#: lenguatesjos visuales distintos: en la carta un lobo de armadura oscura,
#: en el avatar un chico de pelo azul.
#:
#: El sufijo empuja al grabado entintado, que es lo que ya hacen las cartas,
#: y descarta explicitamente lo que salia antes.
SUFIJO_AVATAR = (
    "medieval woodcut engraving, etched ink lines, sepia and bone white on dark "
    "background, 15th century manuscript illumination, heavy crosshatching, "
    "high contrast, icon portrait, bust shot, facing the viewer, no text, "
    "no border, not anime, not photorealistic, no modern clothing"
)

#: Prompt Y CARACTERISTICAS DE LA CRIATURIDAD. "panther warrior portrait" sale
#: un humano con capucha: hay que decir pantera, hocico, colmillos y orejas.
AVATARES = {
    "humano": "human knight captain in plate armour, bearded, heraldic surcoat, "
              "stern face, " + SUFIJO_AVATAR,
    "orco": "orc warlord, heavy brow, tusks, broken nose, battle scars, iron "
            "shoulder plates, " + SUFIJO_AVATAR,
    "goblin": "goblin warlord king, huge pointed ears, wide grin, warts, "
              "crude crown of twisted iron, " + SUFIJO_AVATAR,
    "elfo": "elf queen, long pointed ears, sharp cheekbones, braided hair, "
            "circlet, " + SUFIJO_AVATAR,
    "hombre_lobo": (
        "werewolf alpha, full lupine head, long grey muzzle and bared fangs, "
        "pricked pointed ears, shaggy dark fur, burning amber eyes, fur ruff "
        "over chainmail, humanoid but unmistakably a wolf, " + SUFIJO_AVATAR),
    "vampiro": "vampire countess, pale skin, high cheekbones, dark hair, "
               "parted lips showing fangs, high collar, " + SUFIJO_AVATAR,
    "dragon": "dragon king, horned reptilian skull, scales, slit pupils, "
              "horned crown, smoke, " + SUFIJO_AVATAR,
    "elfo_nocturno": "dark elf queen, obsidian skin, long pointed ears, "
                     "violet eyes, hollow gaze, black circlet, " + SUFIJO_AVATAR,
    "hombre_pantera": (
        "black panther warrior, full feline head, short black muzzle and bared "
        "canine fangs, rounded panther ears, sleek black fur, amber slit eyes, "
        "whip and heavy collar, humanoid but unmistakably a black panther, "
        + SUFIJO_AVATAR),
    "hombre_lagarto": "lizardman chieftain, long scaly muzzle, jaw frill, "
                      "crocodile eyes, scutes along the brow, " + SUFIJO_AVATAR,
}

#: Los personajes con cara propia (no bandos) van aparte: son gente del guion,
#: pero el mismo estilo les viene bien.
AVATARES_PERSONAJES = {
    "nara": "woman chronicler, hooded cloak, ink-stained fingers, calm "
            "watchful face, " + SUFIJO_AVATAR,
    "pik": "scared peasant boy, dirt on cheeks, torn shirt, wide eyes, "
           + SUFIJO_AVATAR,
    "dara": "village woman with a lamp, plain shawl, weathered face, "
            + SUFIJO_AVATAR,
    "jefe_arco": "armoured commander, bearded, scarred, plumed helm, "
                + SUFIJO_AVATAR,
    "gobernante": "weary ruler, hooded, long beard, sorrowful, " + SUFIJO_AVATAR,
    "revancha": "ruined man in a torn cloak, bitter stare, ash on his "
                "shoulders, " + SUFIJO_AVATAR,
    "presentador": "crooked showman with a painted grin, ruff collar, "
                   + SUFIJO_AVATAR,
    "rajoy": "middle aged man in a cheap suit, uncomfortable smile, "
             + SUFIJO_AVATAR,
}

#: Avatares que ya salen bien y NO hay que rehacer. Los dos que fallaban
#: (hombre_lobo y hombre_pantera) NO estan aqui a proposito: con `--fuerza` se
#: regeneran solo los que faltan de esta lista.
AVATARES_BIEN = (
    "humano", "orco", "goblin", "elfo", "vampiro", "dragon",
    "elfo_nocturno", "hombre_lagarto",
    "nara", "pik", "dara", "jefe_arco", "gobernante", "revancha",
    "presentador", "rajoy",
)

# Fondos de las cinematicas: (nombre, prompt)
FONDOS = {
    "ceniza": "dark fantasy kingdom covered in grey ash, burning horizon, ruined towers, cinematic, pixel art style, no text",
    "camino": "ash covered road through dead forest at dusk, fantasy, cinematic wide shot, pixel art style, no text",
    "aldea": "small medieval fantasy village at night with warm lantern light, hope, cinematic, pixel art style, no text",
    "ruinas": "ancient underground ruins glowing with embers, fantasy, cinematic, pixel art style, no text",
    "fortaleza": "fortress on a cliff above a valley of ash, fantasy, cinematic, pixel art style, no text",
    "trono": "throne room of ash and broken pillars, dragon silhouette in the background, fantasy, cinematic, pixel art style, no text",
    "campamento": "fantasy war camp at night with campfire and banners, cinematic, pixel art style, no text",
    "asalto": "fantasy night assault, burning banners and stone stairs, cinematic, pixel art style, no text",
    "amanecer": "dawn breaking over a peaceful fantasy valley with villages and forests, warm hopeful light, calm before the storm, cinematic wide shot, pixel art style, no text",
    "umbral": "colossal cracked stone portal floating above an ashen plain, violet light spilling out, tiny silhouettes watching from below, dark fantasy, cinematic wide shot, pixel art style, no text",
    "estandartes": "war banners of rival fantasy factions gathered before a battlefield of ash, huge dragon shadow overhead, epic standoff, cinematic wide shot, pixel art style, no text",
}


def slug(nombre):
    s = nombre.lower().strip()
    for a, b in (("á", "a"), ("à", "a"), ("é", "e"), ("è", "e"), ("í", "i"),
                 ("ì", "i"), ("ó", "o"), ("ò", "o"), ("ú", "u"), ("ù", "u"),
                 ("ñ", "n"), ("ü", "u"), ("ç", "c")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def cargar_key():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), encoding="utf-8") as f:
            for linea in f:
                if linea.startswith("POLLINATIONS_API_KEY="):
                    return linea.split("=", 1)[1].strip()
    except OSError:
        pass
    return os.environ.get("POLLINATIONS_API_KEY")


def _pedir(prompt, destino, key, ancho, alto, modelo="flux", intentos=3):
    if os.path.exists(destino):
        print(f"  ya existe: {os.path.basename(destino)}")
        return True
    url = (
        f"https://gen.pollinations.ai/image/{urllib.parse.quote(prompt)}"
        f"?model={modelo}&width={ancho}&height={alto}&nologo=true&private=true"
    )
    req = urllib.request.Request(url)
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    for intento in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                datos = resp.read()
            if len(datos) < 2000:
                raise ValueError("respuesta demasiado pequena")
            with open(destino, "wb") as f:
                f.write(datos)
            print(f"  generada: {os.path.basename(destino)}")
            return True
        except Exception as e:  # noqa: BLE001 - red intermitente
            print(f"  fallo ({e}), reintento {intento + 1}/{intentos}")
            time.sleep(4)
    return False


def generar_cartas(key, solo_nuevas=True):
    os.makedirs(CARPETA, exist_ok=True)
    print("Cartas:")
    for bando, cartas in TODOS.items():
        for carta in cartas:
            estilo = (
                f"{carta.nombre}, fantasy {RAZA[bando]} character portrait, pixel art style, "
                "16-bit retro video game card illustration, dark fantasy, no text, no words, "
                "no letters, no watermark, no signature, no border"
            )
            destino = os.path.join(CARPETA, f"{bando}_{slug(carta.nombre)}.png")
            _pedir(estilo, destino, key, 256, 320)
            time.sleep(1.2)


def generar_avatares(key, solo=None, fuerza=False):
    """Genera los avatares. `solo` limita a una lista de nombres.

    Con `--fuerza` se rehacen SOLO los que no estan en `AVATARES_BIEN`: los
    demas ya salian bien y regenerarlos seria gastar peticiones para obtener
    algo peor o simplemente distinto.
    """
    print("Avatares:")
    os.makedirs(ASSETS, exist_ok=True)
    objetivo = dict(AVATARES_PERSONAJES)
    objetivo.update(AVATARES)

    if solo:
        faltan = [n for n in solo if n in objetivo]
        if not faltan:
            raise SystemExit(
                "ninguno de %s es un avatar conocido; conocidos: %s"
                % (", ".join(solo), ", ".join(sorted(objetivo))))
    elif fuerza:
        faltan = [n for n in objetivo if n not in AVATARES_BIEN]
        print("  con --fuerza solo se rehacen los que no estan en "
              "AVATARES_BIEN: %s" % ", ".join(faltan))
    else:
        faltan = list(objetivo)

    for nombre in faltan:
        prompt = objetivo[nombre]
        destino = os.path.join(ASSETS, f"avatar_{nombre}.png")
        _pedir(prompt, destino, key, 256, 256)
        time.sleep(1.2)


def generar_fondos(key, solo_nuevos=True):
    print("Fondos de cinematicallyas:")
    destino_carpeta = os.path.join(ASSETS, "fondos")
    os.makedirs(destino_carpeta, exist_ok=True)
    for nombre, prompt in FONDOS.items():
        destino = os.path.join(destino_carpeta, f"{nombre}.png")
        _pedir(prompt, destino, key, 640, 360)
        time.sleep(1.5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuerza", action="store_true", help="regenera tambien lo existente")
    parser.add_argument("--solo", choices=["cartas", "avatares", "fondos"], default="todo")
    parser.add_argument("--avatar", nargs="+", metavar="NOMBRE",
                        help="genera solo estos avatares (por ejemplo: "
                             "hombre_lobo hombre_pantera)")
    args = parser.parse_args()

    key = cargar_key()
    if not key:
        print("Sin key en .env: usando modo anonimo (muy limitado).")

    if args.fuerza:
        # Los avatares NO se borran aqui: los que ya salen bien (los de
        # `AVATARES_BIEN`) se perderian y luego hay que pagar peticiones para
        # regenerarlos. `generar_avatares` decide por su cuenta cuales rehacer.
        carpetas = ["cartas"]
        if args.solo in ("fondos", "todo"):
            carpetas.append(os.path.join("assets", "fondos"))
        if args.solo == "cartas":
            carpetas = ["cartas"]
        for carpeta in carpetas:
            ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), carpeta)
            for f in os.listdir(ruta) if os.path.isdir(ruta) else []:
                if f.endswith(".png"):
                    os.remove(os.path.join(ruta, f))

    if args.solo in ("cartas", "todo"):
        generar_cartas(key)
    if args.solo in ("avatares", "todo"):
        generar_avatares(key, solo=args.avatar, fuerza=args.fuerza)
    if args.solo in ("fondos", "todo"):
        generar_fondos(key)
    print("Listo.")


if __name__ == "__main__":
    main()