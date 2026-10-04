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
}

AVATARES = {
    "humano": "human knight captain portrait, fantasy, pixel art style",
    "orco": "orc warlord portrait, fantasy, pixel art style",
    "goblin": "goblin warlord king portrait, fantasy, pixel art style",
    "elfo": "elf queen portrait, fantasy, pixel art style",
    "hombre_lobo": "werewolf alpha portrait, fantasy, pixel art style",
    "vampiro": "vampire countess portrait, fantasy, pixel art style",
    "dragon": "dark dragon king portrait, fantasy, pixel art style",
}

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
}


def slug(nombre):
    s = nombre.lower().strip()
    s = re.sub(r"[áà]", "a", s)
    s = re.sub(r"[éè]", "e", s)
    s = re.sub(r"[íì]", "i", s)
    s = re.sub(r"[óò]", "o", s)
    s = re.sub(r"[úù]", "u", s)
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
                "16-bit retro video game card illustration, dark fantasy, no text, no border"
            )
            destino = os.path.join(CARPETA, f"{bando}_{slug(carta.nombre)}.png")
            _pedir(estilo, destino, key, 256, 320)
            time.sleep(1.2)


def generar_avatares(key):
    print("Avatares:")
    os.makedirs(ASSETS, exist_ok=True)
    for bando, prompt in AVATARES.items():
        destino = os.path.join(ASSETS, f"avatar_{bando}.png")
        _pedir(prompt + ", no text, no border", destino, key, 256, 256)
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
    args = parser.parse_args()

    key = cargar_key()
    if not key:
        print("Sin key en .env: usando modo anonimo (muy limitado).")

    if args.fuerza:
        for carpeta in ("cartas", "assets", os.path.join("assets", "fondos")):
            ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), carpeta)
            for f in os.listdir(ruta) if os.path.isdir(ruta) else []:
                if f.endswith(".png"):
                    os.remove(os.path.join(ruta, f))

    if args.solo in ("cartas", "todo"):
        generar_cartas(key)
    if args.solo in ("avatares", "todo"):
        generar_avatares(key)
    if args.solo in ("fondos", "todo"):
        generar_fondos(key)
    print("Listo.")


if __name__ == "__main__":
    main()