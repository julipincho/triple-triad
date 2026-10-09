"""Genera el arte de cartas, avatares y fondos con Pollinations.

Uso:
    python generar_cartas.py            # solo lo que falta
    python generar_cartas.py --fuerza   # regenera todo
"""

import argparse
import os
import random
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
#: Los avatares se generan con `animagine-xl-4.0.safetensors`, que es un modelo
#: de anime, y ASI deben seguir: el menu, el mapa y la pantalla de faccion los
#: enseñan de golpe, y si dos de ellos cambian de idioma visual el menu parece
#: medio roto. Hace un tiempo se rehicieron con `sd_xl_base_1.0` para que casaran
#: con las cartas, y el resultado fue un menu con ocho retratos anime y dos
#: grabados, que es peor que antes.
#:
#: El sufijo describe lo que hace `animagine-xl` con los avatares que ya estaban
#: bien: retrato a busto, de frente, con cel shading y fondo claro.
#:
#: Dos cosas que hay que guardar si se regeneran:
#:   - 28 pasos y CFG 6.0. Con 30 y CFG 6.5 el modelo colapsa en manchas
#:     abstractas: sale una mancha de colores, no un retrato.
#:   - el negativo de `generar_cartas_comfyui.NEGATIVO` MAS el de abajo. Sin
#:     estos terminos, `animagine` mete marcos y cuadritos: de siete lobos
#:     generados, tres salian con marco de foto y uno partido en cuatro
#:     paneles, porque `1girl panther woman` le lee como una hoja de personaje.
#:     `gold collar` es especialmente magnetico para el marco: `gold earring`
#:     pide por lo mismo sin provocarlo.
NEGATIVO_AVATAR = (
    "photorealistic, 3d render, chibi, deformed, human face on a furry body, "
    "hood, mask, picture frame, ornate frame, border, text, watermark"
)

SUFIJO_AVATAR = (
    "masterpiece, best quality, highly detailed, anime style, cel shading, "
    "vibrant colors, character portrait, facing viewer, upper body, "
    "from the waist up, plain flat background, light background, "
    "no text, no watermark"
)

#: Prompt Y CARACTERISTICAS DE LA CRIATURIDAD.
#:
#: "panther warrior portrait" sale un humano con capucha contra una ciudad neon,
#: y "werewolf alpha portrait" sale un chico anime de pelo azul. A `animagine-xl`
#: hay que darle los rasgos uno a uno y en su idioma (etiquetas de Danbooru),
#: no una frase de fantasy: el modelo responde a `wolf ears, muzzle, fangs` y
#: pasa por alto `unmistakably a panther`.
AVATARES = {
    "humano": "1boy, human knight, plate armour, beard, heraldic surcoat, "
              "serious expression, " + SUFIJO_AVATAR,
    "orco": "1boy, orc, heavy brow, tusks, broken nose, battle scars, "
            "iron shoulder plates, " + SUFIJO_AVATAR,
    "goblin": "1boy, goblin, huge pointed ears, wide grin, warts, "
              "crown of twisted iron, " + SUFIJO_AVATAR,
    "elfo": "1girl, elf, long pointed ears, sharp cheekbones, braided hair, "
            "circlet, " + SUFIJO_AVATAR,
    "hombre_lobo": (
        "1boy, werewolf, male werewolf, wolf ears, wolf muzzle, long snout, "
        "bared fangs, shaggy grey fur, amber eyes, torn cloak, muscular, "
        + SUFIJO_AVATAR),
    "vampiro": "1girl, vampire, pale skin, high cheekbones, dark hair, "
               "parted lips, fangs, high collar, " + SUFIJO_AVATAR,
    "dragon": "1boy, dragon, horned reptilian skull, scales, slit pupils, "
              "horned crown, smoke, " + SUFIJO_AVATAR,
    "elfo_nocturno": "1girl, dark elf, obsidian skin, long pointed ears, "
                     "violet eyes, hollow gaze, black circlet, "
                     + SUFIJO_AVATAR,
    "hombre_pantera": (
        "1girl, panther woman, black panther, feline ears, short black muzzle, "
        "bared canine fangs, sleek black fur, amber slit eyes, gold earring, "
        + SUFIJO_AVATAR),
    "hombre_lagarto": "1boy, lizardman, long scaly muzzle, jaw frill, "
                      "crocodile eyes, green scales, " + SUFIJO_AVATAR,
}

#: Los personajes con cara propia (no bandos) van aparte: son gente del guion,
#: pero el mismo estilo les viene bien.
AVATARES_PERSONAJES = {
    "nara": "1girl, woman chronicler, hooded cloak, ink-stained fingers, "
            "calm watchful face, " + SUFIJO_AVATAR,
    "pik": "1boy, scared peasant, dirt on cheeks, torn shirt, wide eyes, "
           + SUFIJO_AVATAR,
    "dara": "1girl, village woman holding a lamp, plain shawl, weathered face, "
            + SUFIJO_AVATAR,
    "jefe_arco": "1boy, armoured commander, beard, scar, plumed helm, "
                + SUFIJO_AVATAR,
    "gobernante": "1boy, weary old ruler, hooded, long beard, sorrowful, "
                  + SUFIJO_AVATAR,
    "revancha": "1boy, ruined man in a torn cloak, bitter stare, ash on his "
                "shoulders, " + SUFIJO_AVATAR,
    "presentador": "1boy, crooked showman, painted grin, ruff collar, "
                   + SUFIJO_AVATAR,
    "rajoy": "1boy, middle aged man in a cheap suit, uncomfortable smile, "
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


#: Modelo con el que se hacen los avatares. Los dieciocho que ya salen bien
#: salieron de aqui, asi que es el que hay que usar para los dos que faltaban.
AVATAR_MODELO = "animagine-xl-4.0.safetensors"

#: El `.bat` que arranca ComfyUI en una ventana nueva. Vive fuera del repo
#: (es la instalacion local del jugador), asi que `arrancar_servidor` avisa si
#: no esta en vez de fallar: los avatares se pueden generar a mano desde la
#: interfaz de ComfyUI y el juego no se entero.
COMFY_BAT = r"E:\AI\start-comfyui.bat"


def generar_avatar_comfyui(nombre, prompt, servidor="http://127.0.0.1:8188",
                           pasos=28, cfg=6.0, lado=512, destino=None):
    """Un avatar por ComfyUI con `animagine-xl`. Devuelve True si se genero.

    Se genera a 512 y se deja en 512: el recorte a 256 lo hace quien lo instala
    en `assets/`, mirando la imagen, no a ciegas.
    """
    import generar_cartas_comfyui as comfy

    if comfy.arrancar_servidor(servidor, COMFY_BAT, 180) is None:
        print("  ComfyUI no respondio en %s" % servidor)
        return False
    if destino is None:
        destino = os.path.join(ASSETS, f"avatar_{nombre}.png")
    negativo = ", ".join(p for p in (comfy.NEGATIVO, NEGATIVO_AVATAR) if p)
    return bool(comfy.generar_imagen(
        servidor, prompt, negativo, destino, random.randrange(2 ** 32),
        lado, lado, pasos, cfg, AVATAR_MODELO, ancla=None))


def generar_avatares(key, solo=None, fuerza=False, comfyui=False):
    """Genera los avatares. `solo` limita a una lista de nombres.

    Con `--fuerza` se rehacen SOLO los que no estan en `AVATARES_BIEN`: los
    demas ya salian bien y regenerarlos seria gastar peticiones para obtener
    algo peor o simplemente distinto.

    `comfyui` usa ComfyUI con `animagine-xl` en vez de Pollinations, que esta
    muerto: la key de `.env` no tiene credito y devuelve HTTP 402.
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
        if comfyui:
            generar_avatar_comfyui(nombre, prompt, destino=destino)
        else:
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
    parser.add_argument("--comfyui", action="store_true",
                        help="los avatares van por ComfyUI con animagine-xl en "
                             "vez de Pollinations, que devuelve HTTP 402 sin "
                             "credito")
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
        generar_avatares(key, solo=args.avatar, fuerza=args.fuerza,
                         comfyui=args.comfyui)
    if args.solo in ("fondos", "todo"):
        generar_fondos(key)
    print("Listo.")


if __name__ == "__main__":
    main()