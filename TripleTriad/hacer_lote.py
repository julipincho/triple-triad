"""Construye el lote de fichas para las 250 cartas desde `mazos.TODOS`.

Cada ficha lleva: nombre, faccion, raza, rareza (logica del juego), clase y una
escena breve de una frase (descripcion) que Gemini escribe mirando los nombres.
Con eso el prompt del generador construye un retrato con personalidad sin que
todos los personajes salgan iguales.

Uso:
    python hacer_lote.py                      # -> lote_completo.json
    python hacer_lote.py --sin-gemini         # clase/descripcion vacios (offline)

Solo biblioteca estandar + Pillow al vuelo para leer TODOS; la clave de Gemini
se lee de `.env`.
"""

import argparse
import json
import os
import sys
import zlib

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

from mazos import TODOS  # noqa: E402
from reglas import rareza  # noqa: E402


def _key():
    with open(os.path.join(RAIZ, ".env"), encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("GEMINI_API_KEY="):
                return linea.split("=", 1)[1].strip()
    return os.environ.get("GEMINI_API_KEY")


PROMPT = """Tengo las 250 cartas de un juego de cartas de fantasia oscura. Para cada
una necesito UNA escena breve (una frase, en espanol, sin comas raras) que
describa la pose/acción/escena del personaje para un retrato de tipo busto de
carta, y una clase sugerida de esta lista: guerrero, caballero, mago, brujo,
nigromante, arquero, paladin, berserker, asesino, druida, chaman, clerigo,
cazador, invocador, guardian, capitan, senor, dama, rey, reina, profeta,
heraldo, hechicero, oraculo.

Reglas:
- La escena debe evocar fantasia oscura, luz dramatica, poco color.
- Solo la accion breve, sin nombres propios en la escena: "alzando el hacha
  manchada bajo un cielo ambar".
- Devuelve SOLO el JSON con la misma lista, una entrada por carta:
{"cartas": [{"nombre": "exacto", "clase": "...", "descripcion": "..."}]}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", default=os.path.join(RAIZ, "lote_completo.json"))
    parser.add_argument("--sin-gemini", action="store_true",
                        help="no llama a Gemini: clase y descripcion vacias")
    parser.add_argument("--modelo", default="gemini-3.5-flash")
    args = parser.parse_args()

    cartas = []
    mapas = {}
    for bando, lista in TODOS.items():
        for carta in lista:
            r, _ = rareza(carta)
            cartas.append({
                "nombre": carta.nombre,
                "faccion": bando,
                "raza": bando,
                "rareza": r,
                "seed": zlib.crc32(carta.nombre.encode("utf-8")),
            })
            mapas[carta.nombre] = len(cartas) - 1

    if not args.sin_gemini:
        key = _key()
        if not key:
            print("Sin GEMINI_API_KEY: uso --sin-gemini.")
            sys.exit(1)
        from google import genai
        from google.genai import types

        lista_nombres = [{"nombre": c["nombre"], "raza": c["raza"],
                          "faccion": c["faccion"]} for c in cartas]
        client = genai.Client(api_key=key)
        print(f"Consultando {args.modelo} ({len(cartas)} cartas)...")
        resp = client.models.generate_content(
            model=args.modelo,
            contents=[PROMPT, json.dumps(lista_nombres, ensure_ascii=False)],
            config=types.GenerateContentConfig(
                response_mime_type="application/json", temperature=0.5,
            ),
        )
        datos = getattr(resp, "parsed", None) or json.loads(resp.text or "{}")
        extras = datos.get("cartas") or datos if isinstance(datos, list) else datos.get("cartas", [])
        vistos = set()
        for extra in extras:
            nombre = (extra or {}).get("nombre", "")
            idx = mapas.get(nombre)
            if idx is None or nombre in vistos:
                continue
            vistos.add(nombre)
            cartas[idx]["clase"] = (extra.get("clase") or "").strip().lower()
            cartas[idx]["descripcion"] = (extra.get("descripcion") or "").strip()
        print(f"  descripciones recibidas: {len(vistos)}/{len(cartas)}")
    else:
        for c in cartas:
            c.setdefault("clase", "")
            c.setdefault("descripcion", "")

    con = os.path.dirname(args.salida) or "."
    os.makedirs(con, exist_ok=True)
    with open(args.salida, "w", encoding="utf-8") as f:
        json.dump(cartas, f, ensure_ascii=False, indent=1)
    print(f"Guardado: {args.salida} ({len(cartas)} fichas)")
    ej = cartas[0]
    print("Ejemplo:", json.dumps(ej, ensure_ascii=False))


if __name__ == "__main__":
    main()