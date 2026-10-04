"""Genera las imágenes de las cartas con Pollinations (gratuito con key)."""

import os
import re
import time
import urllib.parse
import urllib.request

from mazos import ELFOS, GOBLINS, HOMBRES_LOBO, VAMPIROS, DRAGONES

CARPETA = os.path.join(os.path.dirname(__file__), "cartas")


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
        with open(os.path.join(os.path.dirname(__file__), ".env"), encoding="utf-8") as f:
            for linea in f:
                if linea.startswith("POLLINATIONS_API_KEY="):
                    return linea.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return os.environ.get("POLLINATIONS_API_KEY")


def generar(carta, key):
    raza = {"goblin": "goblin", "elfo": "elf", "hombre_lobo": "werewolf", "vampiro": "vampire", "dragon": "dragon"}[carta.bando]
    prompt = (
        f"{carta.nombre}, fantasy {raza} character portrait, pixel art style, "
        f"16-bit retro video game card illustration, dark fantasy, no text, no border"
    )
    url = (
        "https://gen.pollinations.ai/image/"
        + urllib.parse.quote(prompt)
        + "?model=flux&width=256&height=320"
    )
    destino = os.path.join(CARPETA, f"{carta.bando}_{slug(carta.nombre)}.png")
    if os.path.exists(destino):
        print(f"Ya existe: {destino}")
        return
    req = urllib.request.Request(url)
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    print(f"Generando {destino}...")
    for intento in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                datos = resp.read()
            with open(destino, "wb") as f:
                f.write(datos)
            return
        except Exception as e:
            print(f"  error ({e}), reintentando...")
            time.sleep(3)
    print(f"  No se pudo generar {destino}")


AVATARES = {
    "goblin": "goblin warlord king portrait, fantasy, pixel art style",
    "elfo": "elf queen portrait, fantasy, pixel art style",
    "hombre_lobo": "werewolf alpha portrait, fantasy, pixel art style",
    "vampiro": "vampire countess portrait, fantasy, pixel art style",
    "dragon": "dark dragon king portrait, fantasy, pixel art style",
}


def generar_avatares(key):
    import urllib.parse, urllib.request
    for bando, prompt in AVATARES.items():
        destino = os.path.join(os.path.dirname(__file__), "assets", f"avatar_{bando}.png")
        if os.path.exists(destino):
            print(f"Ya existe: {destino}")
            continue
        url = (
            "https://gen.pollinations.ai/image/"
            + urllib.parse.quote(prompt + ", no text, no border")
            + "?model=flux&width=256&height=256"
        )
        req = urllib.request.Request(url)
        if key:
            req.add_header("Authorization", f"Bearer {key}")
        print(f"Generando avatar {bando}...")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                datos = resp.read()
            with open(destino, "wb") as f:
                f.write(datos)
        except Exception as e:
            print(f"  error: {e}")
        time.sleep(1)


def main():
    os.makedirs(CARPETA, exist_ok=True)
    key = cargar_key()
    if not key:
        print("Sin key: usando modo anónimo (limitado)")
    for carta in GOBLINS + ELFOS + HOMBRES_LOBO + VAMPIROS + DRAGONES:
        generar(carta, key)
        time.sleep(1)
    generar_avatares(key)
    print("Listo.")


if __name__ == "__main__":
    main()
