"""Extrae la ficha de estilo del moodboard con Gemini (herramienta de desarrollo).

Envia `E:\\AI\\moodboard.png` (o la ruta que se le pase) a Gemini como director
de arte y le pide que devuelva, en JSON con esquema forzado, la receta visual
exacta del moodboard: medio, paleta con hex, luz, encuadre, textura, mood,
bloque de prompts para SDXL y prohibiciones.

Ademas envia tres recortes ampliados: la imagen entera se reduce al subirla y
se pierde la textura fina (scanlines, rejilla de pixel, pincelada).

Y envia las medidas que hemos sacado del propio PNG como suelo de verdad, para
que el modelo no se invente la paleta:

    brillo 59/255, saturacion 33/255
    scanlines: autocorrelacion a lag 2 = -0.86 (patron alterno de 2 px)

Salida:
    estilo/estilo.json   version maquina (la consume generar_cartas_comfyui.py)
    estilo/ESTILO.md     version legible, para humanos

Uso:
    python extraer_estilo_moodboard.py
    python extraer_estilo_moodboard.py --imagen E:\\AI\\otro.png
    python extraer_estilo_moodboard.py --solo-mediciones   # sin llamar a Gemini

Solo la biblioteca estandar + Pillow para las mediciones. La clave de Gemini se
lee de `.env` (GEMINI_API_KEY), igual que en revisar_con_gemini.py.
"""

import argparse
import json
import os
import statistics
import sys
from typing import List, TypedDict

from PIL import Image

RAIZ = os.path.dirname(os.path.abspath(__file__))
CARPETA_ESTILO = os.path.join(RAIZ, "estilo")
IMAGEN_DEFECTO = r"E:\AI\moodboard.png"
MODELO = "gemini-3.5-flash"


# ------------------------------------------------------------------ esquema --
# TypedDict: google-genai lo usa como response_schema y valida la forma JSON.

class ColorFicha(TypedDict):
    hex: str
    nombre: str
    uso: str


class PromptsSDXL(TypedDict):
    positivo: str
    negativo: str


class FichaEstilo(TypedDict):
    resumen: str
    medio: str
    paleta: List[ColorFicha]
    luz: str
    encuadre: str
    textura: str
    detalle: str
    mood: str
    sujetos: str
    prompts_sdxl: PromptsSDXL
    prohibiciones: List[str]


PROMPT = """Sos director de arte de un juego de cartas de dark fantasy. Te mando el moodboard
de referencia del proyecto: la unica fuente de verdad sobre como debe verse el arte.

Te mando (1) el moodboard entero y (2) tres recortes ampliados al 100% para que
veas la textura fina: scanlines, rejilla de pincelada o de pixel, bordes.

Tarea: describe su estetica como una receta reproducible para un generador SDXL.

Devuelve EXACTAMENTE el esquema pedido, con todos los campos:

- resumen: una frase con la esencia de la estetica.
- medio: que tecnica se ve (pixel art, oleo, acuarela, digital painting...) y como
  es su textura y pincelada. Si hay scanlines o rejilla, mencionalo aqui.
- paleta: 6-10 colores {{hex, nombre, uso}}, sacados DE LA IMAGEN. Los primeros
  tienen que ser los que medimos abajo; podes anadir 1-2 acentos que veas.
- luz: direccion, dureza, contrastes, temperatura.
- encuadre: plano, angulo, donde queda el sujeto, que hay al fondo.
- textura: grano, scanlines, dithering, pincelada, bordes suaves o duros.
- detalle: nivel de detalle y donde se concentra.
- mood: atmosfera emocional.
- sujetos: como se representan los sujetos (proporcion, pose, expresion, silueta).
- prompts_sdxl.positivo: en INGLES, lista concreta separada por comas, lista para
  pegar en un prompt de SDXL: medio, textura, paleta, luz, encuadre. Nada de
  "masterpiece", "best quality" ni nombres de artistas.
- prompts_sdxl.negativo: en INGLES, todo lo que romperia esta estetica.
- prohibiciones: 4-6 frases cortas en espanol de lo que NO aparece.

Reglas:
1. La paleta respeta los colores medidos (los te paso abajo); solo anade acentos
   que realmente veas.
2. Describe lo que SE VE, no lo que te gustaria ver.
3. Respondes SOLO con el JSON.

Mediciones hechas del PNG (verdad de terreno):
- tamano: {tamano}
- brillo medio: {brillo}/255 (0=negro, 255=blanco)
- saturacion media: {saturacion}/255
- scanlines detectados: si, patron alterno de 2 px (autocorrelacion -0.86)
- paleta dominante por cuantizacion: {paleta}
"""


# ---------------------------------------------------------------- mediciones --

def medir(ruta):
    """Estadisticas baratas del moodboard: las usamos como verdad de terreno."""
    im = Image.open(ruta)
    rgb = im.convert("RGB")
    small = rgb.resize((200, 200))
    q = small.quantize(colors=12, method=Image.MEDIANCUT).convert("RGB")
    total = 200 * 200
    paleta = []
    for n, c in sorted(q.getcolors(total) or [], reverse=True):
        paleta.append({"hex": "#%02x%02x%02x" % c, "pct": round(100 * n / total, 1)})

    # scanlines: high-pass del perfil de fila y autocorrelacion a lag 2
    gris = im.convert("L")
    px = gris.load()
    w, h = gris.size
    perfil = []
    for y in range(h):
        xs = range(0, w, 7)
        perfil.append(sum(px[x, y] for x in xs) / len(xs))
    hp = []
    for i in range(2, len(perfil) - 2):
        hp.append(perfil[i] - sum(perfil[i - 2:i + 3]) / 5)
    num = den = 0.0
    for i in range(len(hp) - 2):
        num += hp[i] * hp[i + 2]
        den += hp[i] * hp[i]
    scan_corr = num / den if den else 0.0

    px2 = list(small.getdata())
    brillos = [0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in px2]
    sats = [max(p) - min(p) for p in px2]
    return {
        "tamano": f"{im.size[0]}x{im.size[1]}",
        "brillo": round(statistics.mean(brillos)),
        "saturacion": round(statistics.mean(sats)),
        "paleta": paleta,
        "scanlines_lag2": round(scan_corr, 3),
        "scanlines": scan_corr < -0.3,
    }


def recortes(ruta, carpeta):
    """Tres ampliaciones al 100% para que se vea la textura fina."""
    im = Image.open(ruta)
    w, h = im.size
    cajas = [
        (int(w * 0.06), int(h * 0.07), int(w * 0.32), int(h * 0.70)),
        (int(w * 0.35), int(h * 0.10), int(w * 0.61), int(h * 0.73)),
        (int(w * 0.65), int(h * 0.50), int(w * 0.91), int(h * 0.99)),
    ]
    os.makedirs(carpeta, exist_ok=True)
    rutas = []
    for i, caja in enumerate(cajas, 1):
        ruta = os.path.join(carpeta, f"corte{i}.png")
        im.crop(caja).save(ruta)
        rutas.append(ruta)
    return rutas


# ------------------------------------------------------------------ consulta --

def _key():
    with open(os.path.join(RAIZ, ".env"), encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("GEMINI_API_KEY="):
                return linea.split("=", 1)[1].strip()
    return os.environ.get("GEMINI_API_KEY")


def consultar(key, ruta, medidas, rutas_cortes):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key)
    paleta_txt = ", ".join(f"{c['hex']} ({c['pct']}%)" for c in medidas["paleta"])
    prompt = PROMPT.format(
        tamano=medidas["tamano"],
        brillo=medidas["brillo"],
        saturacion=medidas["saturacion"],
        paleta=paleta_txt,
    )
    partes = [prompt]
    with open(ruta, "rb") as f:
        partes.append(types.Part.from_bytes(data=f.read(), mime_type="image/png"))
    for c in rutas_cortes:
        with open(c, "rb") as f:
            partes.append(types.Part.from_bytes(data=f.read(), mime_type="image/png"))

    print(f"Consultando {MODELO} (imagen + {len(rutas_cortes)} recortes)...")
    resp = client.models.generate_content(
        model=MODELO,
        contents=partes,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=FichaEstilo,
            temperature=0.2,
        ),
    )
    ficha = getattr(resp, "parsed", None)
    if ficha is None:
        texto = resp.text or ""
        ficha = json.loads(texto)
    return ficha


# ------------------------------------------------------------------- escritura --

def _normalizar(ficha):
    """Rellena huecos y acepta variantes de clave por si el modelo se descuadra."""
    out = dict(ficha)
    paleta = ficha.get("paleta") or []
    norm = []
    for p in paleta:
        if isinstance(p, str):
            norm.append({"hex": p, "nombre": "", "uso": ""})
        elif isinstance(p, dict):
            norm.append({
                "hex": str(p.get("hex", "")),
                "nombre": str(p.get("nombre", "")),
                "uso": str(p.get("uso", "")),
            })
    out["paleta"] = norm
    prompts = ficha.get("prompts_sdxl") or {}
    out["prompts_sdxl"] = {
        "positivo": str(prompts.get("positivo", "")),
        "negativo": str(prompts.get("negativo", "")),
    }
    for campo in ("resumen", "medio", "luz", "encuadre", "textura", "detalle",
                  "mood", "sujetos"):
        out.setdefault(campo, "")
    out.setdefault("prohibiciones", [])
    return out


def escribir_md(ficha, medidas, ruta_md, ruta_imagen):
    paleta = "\n".join(
        f"| `{p['hex'].upper()}` | {p['nombre']} | {p['uso']} |"
        for p in ficha["paleta"]
    )
    proh = "\n".join(f"- {x}" for x in ficha["prohibiciones"])
    scan = (f"si (autocorr lag2 = {medidas['scanlines_lag2']})"
            if medidas.get("scanlines") else "no detectados")
    md = f"""# Ficha de estilo — Triple Triad

Fuente: `{ruta_imagen}` (moodboard). Extraida con {MODELO}.
Este archivo manda sobre el prompt, el post-proceso y cualquier checkpoint.

> {ficha['resumen']}

## Medicion del PNG

| Metrica | Valor |
|---|---|
| Brillo medio | {medidas['brillo']}/255 |
| Saturacion media | {medidas['saturacion']}/255 |
| Scanlines | {scan} |
| Tamano | {medidas['tamano']} |

## Medio
{ficha['medio']}

## Luz
{ficha['luz']}

## Encuadre
{ficha['encuadre']}

## Textura
{ficha['textura']}

## Detalle
{ficha['detalle']}

## Mood
{ficha['mood']}

## Sujetos
{ficha['sujetos']}

## Paleta

| Hex | Nombre | Uso |
|---|---|---|
{paleta}

## Bloque de prompt SDXL

**Positivo:**
```
{ficha['prompts_sdxl']['positivo']}
```

**Negativo:**
```
{ficha['prompts_sdxl']['negativo']}
```

## Prohibiciones
{proh}
"""
    with open(ruta_md, "w", encoding="utf-8") as f:
        f.write(md)


# ----------------------------------------------------------------------- CLI --

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--imagen", default=IMAGEN_DEFECTO,
                        help=f"moodboard (por defecto: {IMAGEN_DEFECTO})")
    parser.add_argument("--salida", default=CARPETA_ESTILO,
                        help="carpeta de salida")
    parser.add_argument("--solo-mediciones", action="store_true",
                        help="solo mide el PNG, sin llamar a Gemini")
    args = parser.parse_args()

    if not os.path.exists(args.imagen):
        print(f"No existe la imagen: {args.imagen}")
        sys.exit(2)

    medidas = medir(args.imagen)
    print(f"Medido {args.imagen}: brillo {medidas['brillo']}/255, "
          f"saturacion {medidas['saturacion']}/255, "
          f"scanlines={'si' if medidas['scanlines'] else 'no'} "
          f"(lag2 {medidas['scanlines_lag2']})")
    print("  paleta: " + ", ".join(f"{c['hex']}({c['pct']}%)"
                                   for c in medidas["paleta"]))

    os.makedirs(args.salida, exist_ok=True)
    ruta_json = os.path.join(args.salida, "estilo.json")
    ruta_md = os.path.join(args.salida, "ESTILO.md")

    if args.solo_mediciones:
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump({"medidas": medidas, "imagen": args.imagen}, f,
                      ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Guardado (solo mediciones): {ruta_json}")
        return

    key = _key()
    if not key:
        print("Falta GEMINI_API_KEY en .env")
        sys.exit(1)

    rutas_cortes = recortes(args.imagen, os.path.join(os.path.dirname(args.imagen),
                                                      "moodboard_cortes"))
    try:
        ficha = consultar(key, args.imagen, medidas, rutas_cortes)
    except Exception as e:  # noqa: BLE001 - informar y salir limpio
        print(f"Error consultando Gemini: {e}")
        sys.exit(1)

    ficha = _normalizar(ficha)
    ficha["medidas"] = medidas
    ficha["imagen"] = args.imagen
    ficha["modelo_extraccion"] = MODELO

    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(ficha, f, ensure_ascii=False, indent=2)
        f.write("\n")
    escribir_md(ficha, medidas, ruta_md, args.imagen)

    print(f"\nResumen: {ficha['resumen']}")
    print(f"Medio  : {ficha['medio'][:160]}")
    print(f"Guardado: {ruta_json}")
    print(f"Guardado: {ruta_md}")


if __name__ == "__main__":
    main()
