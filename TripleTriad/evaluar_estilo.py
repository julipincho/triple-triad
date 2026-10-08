"""Pide veredicto de direccion de arte a Gemini sobre una hoja de contactos.

Herramienta de desarrollo: el juego nunca importa este modulo.

Yo no puedo ver las imagenes, asi que el metro para decidir entre variantes
es Gemini mirando la hoja con la ficha de estilo del lado. Sirve para cualquier
hoja: A/B de prompts, de post-proceso o de checkpoints.

Uso:
    python evaluar_estilo.py auditoria/hoja_contactos.png
    python evaluar_estilo.py auditoria/hoja_contactos.png auditoria/hoja_arte.png
    python evaluar_estilo.py hoja.png --ficha estilo/ESTILO.md

La respuesta se imprime y se guarda en `auditoria/evaluacion.md`.
Solo biblioteca estandar; la clave de Gemini se lee de `.env`.
"""

import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))

PROMPT = """Sos director de arte. Te mando:

1. La ficha de estilo del proyecto (referencia normativa).
2. Una o varias hojas de contactos. En cada hoja: FILAS = variantes (con su
   etiqueta a la izquierda), COLUMNAS = cartas distintas del juego. A veces
   hay una segunda hoja con la ventana de arte de la carta ampliada, que es
   exactamente lo que se ve en pantalla (56x79 pixeles).

Tu veredicto, en espanol, con esta estructura:

## Coherencia con la ficha
Para CADA variante de cada hoja: nota de 1 a 10 y una frase de justificacion
mirando paleta, luz, textura y encuadre.

## Legibilidad en juego
La ventana de arte mide 56x79 y las cartas se ven pequenas en el tablero.
Cada variante: se distingue el personaje? se pierde el rostro en el tramado?
los scanlines ayudan o estorban?

## Problemas concretos
Lista corta y accionable (no generalidades): por ejemplo "el fondo se come al
personaje", "la paleta se queda sin altas luces", "el dithering ensucia las
caras".

## Recomendacion
- Mejor variante global (y por que).
- Cambios concretos de parametros: brillo, saturacion, dithering, scanlines,
  fuerza del prompt, o si hace falta otro checkpoint.
- Si alguna variante NO deberia usarse, digalo claramente.

Sé exigente: si algo no llega a la ficha, dilo. No inventes defectos que no
se vean.
"""


def _key():
    with open(os.path.join(RAIZ, ".env"), encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("GEMINI_API_KEY="):
                return linea.split("=", 1)[1].strip()
    return os.environ.get("GEMINI_API_KEY")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("imagenes", nargs="+", help="PNG a evaluar")
    parser.add_argument("--ficha", default=os.path.join(RAIZ, "estilo", "ESTILO.md"))
    parser.add_argument("--modelo", default="gemini-3.5-flash")
    parser.add_argument("--salida", default=os.path.join(RAIZ, "auditoria",
                                                          "evaluacion.md"))
    parser.add_argument("--extra", default="",
                        help="instruccion adicional en una frase")
    args = parser.parse_args()

    faltan = [i for i in args.imagenes if not os.path.exists(i)]
    if faltan:
        print("No existen: " + ", ".join(faltan))
        sys.exit(2)
    if not os.path.exists(args.ficha):
        print(f"No existe la ficha: {args.ficha}")
        sys.exit(2)

    key = _key()
    if not key:
        print("Falta GEMINI_API_KEY en .env")
        sys.exit(1)

    from google import genai
    from google.genai import types

    with open(args.ficha, encoding="utf-8") as f:
        ficha = f.read()

    partes = [PROMPT]
    if args.extra:
        partes.append(f"Instruccion extra del usuario: {args.extra}")
    partes.append(f"Ficha de estilo:\n\n{ficha}")
    for ruta in args.imagenes:
        with open(ruta, "rb") as f:
            partes.append(types.Part.from_bytes(data=f.read(), mime_type="image/png"))
        print(f"Adjunto: {ruta}")

    print(f"Consultando {args.modelo}...")
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(
        model=args.modelo,
        contents=partes,
        config=types.GenerateContentConfig(temperature=0.3),
    )
    texto = resp.text or ""
    if not texto:
        for candidate in (resp.candidates or []):
            for p in (candidate.content.parts or []):
                if getattr(p, "text", None):
                    texto += p.text
    if not texto:
        print("Gemini no devolvio texto.")
        sys.exit(1)

    os.makedirs(os.path.dirname(args.salida), exist_ok=True)
    with open(args.salida, "w", encoding="utf-8") as f:
        f.write(texto.rstrip() + "\n")
    print("\n" + texto)
    print(f"\nGuardado en {args.salida}")


if __name__ == "__main__":
    main()
