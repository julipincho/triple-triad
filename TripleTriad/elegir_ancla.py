"""Elige el recorte ancla para IP-Adapter dentro del moodboard.

El moodboard es un collage de capturas; IP-Adapter necesita UNA imagen que
aporte la estetica. Le pedimos a Gemini que localice el recorte con el mejor
retrato/composicion de personaje y guardamos ese recorte (512x512, reescalado
conservando la relacion de aspecto) como `estilo/ancla.png`.

Uso:
    python elegir_ancla.py                     # moodboard -> estilo/ancla.png
    python elegir_ancla.py --imagen otro.png --salida estilo/ancla2.png

Solo biblioteca estandar + Pillow; la clave de Gemini se lee de `.env`.
"""

import argparse
import json
import os
import sys

from PIL import Image

RAIZ = os.path.dirname(os.path.abspath(__file__))
IMAGEN_DEFECTO = r"E:\AI\moodboard.png"
MODELO = "gemini-3.5-flash"

PROMPT = """Te mando el moodboard de un juego de cartas (un collage de capturas de
pantalla, dos filas). Necesito elegir UN recorte de 512x512 que funcione como
imagen ancla de estilo para IP-Adapter: tiene que ser un retrato de personaje
(fantasia oscura) en el que se vea bien el rostro, la armadura/vestimenta y la
paleta.

La imagen mide {ancho}x{alto} pixeles. Devuelve las coordenadas del recorte en
pixeles de la imagen original: x1,y1 = esquina superior izquierda, x2,y2 =
esquina inferior derecha, trazando un recuadro lo mas cuadrado posible
proporcionalmente (aprox 1:1) centrado en el personaje.

Reglas:
- El recorte debe medir LxL con L lo mayor posible (entre 300 y 700 px).
- Si en el recorte hay texto/UI (marcos de carta, texto), evitalo o minimizalo.
- Devuelve SOLO el JSON: {{"x1": n, "y1": n, "x2": n, "y2": n, "por_que": "una frase"}}.
"""


def _key():
    with open(os.path.join(RAIZ, ".env"), encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("GEMINI_API_KEY="):
                return linea.split("=", 1)[1].strip()
    return os.environ.get("GEMINI_API_KEY")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--imagen", default=IMAGEN_DEFECTO)
    parser.add_argument("--salida", default=os.path.join(RAIZ, "estilo", "ancla.png"))
    parser.add_argument("--lado", type=int, default=512, help="lado del recorte")
    parser.add_argument("--coords", default=None,
                        help="coordenadas directas x1,y1,x2,y2 (sin llamar a Gemini)")
    args = parser.parse_args()

    if not os.path.exists(args.imagen):
        print(f"No existe la imagen: {args.imagen}")
        sys.exit(2)
    im = Image.open(args.imagen)
    w, h = im.size

    if args.coords:
        try:
            x1, y1, x2, y2 = (int(v) for v in args.coords.split(","))
        except ValueError:
            print("--coords tiene que ser x1,y1,x2,y2")
            sys.exit(2)
        por_que = "coordenadas pasadas por CLI"
    else:
        key = _key()
        if not key:
            print("Falta GEMINI_API_KEY en .env")
            sys.exit(1)
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=key)
        with open(args.imagen, "rb") as f:
            parte = types.Part.from_bytes(data=f.read(), mime_type="image/png")
        print(f"Consultando {MODELO}...")
        resp = client.models.generate_content(
            model=MODELO,
            contents=[PROMPT.format(ancho=w, alto=h), parte],
            config=types.GenerateContentConfig(
                response_mime_type="application/json", temperature=0.0
            ),
        )
        datos = getattr(resp, "parsed", None) or json.loads(resp.text or "{}")
        x1, y1, x2, y2 = datos["x1"], datos["y1"], datos["x2"], datos["y2"]
        por_que = datos.get("por_que", "")
        print(f"  -> ({x1},{y1})-({x2},{y2}): {por_que}")

    # saneo: dentro de la imagen y al menos 200 px de lado
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if (x2 - x1) < 200 or (y2 - y1) < 200:
        print(f"Recorte demasiado pequeno ({x2-x1}x{y2-y1}): uso el centro.")
        cx, cy = w // 2, h // 4
        lado = min(448, w // 2, h // 2)
        x1, y1, x2, y2 = cx - lado, cy - lado, cx + lado, cy + lado

    recorte = im.crop((x1, y1, x2, y2))
    # reescala a cuadrado conservando relacion de aspecto (centrado)
    lado = args.lado
    ancho, alto = recorte.size
    escala = min(lado / ancho, lado / alto)
    nuevo = (max(1, int(ancho * escala)), max(1, int(alto * escala)))
    recorte = recorte.resize(nuevo, Image.LANCZOS)
    lienzo = Image.new("RGB", (lado, lado), (16, 16, 20))
    lienzo.paste(recorte, ((lado - nuevo[0]) // 2, (lado - nuevo[1]) // 2))
    os.makedirs(os.path.dirname(args.salida), exist_ok=True)
    lienzo.save(args.salida)
    print(f"Guardado ancla: {args.salida} ({lienzo.size[0]}x{lienzo.size[1]})")


if __name__ == "__main__":
    main()