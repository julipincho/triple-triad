"""Envia las capturas del recorrido a Gemini 2.5 Flash y devuelve sugerencias.

Uso:
    python revisar_con_gemini.py
"""

import os
import sys

from google import genai
from google.genai import types

RAIZ = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(RAIZ, "recorrido")

PROMPT = """Sos un director de arte y UX. Te mando 32 capturas de un juego de cartas estilo Triple Triad hecho en Python + pygame, en orden de flujo del jugador. Cada imagen es una pantalla real del juego.

Objetivo: preservar la identidad visual actual y proponer mejoras concretas, no un rediseño genérico. El gancho visual: las cartas cambian de color según la baraja que las posee (feedback de dominio), con 7 facciones y paleta propia por mazo.

Por cada área que analices, dame:
1. Qué está bien y por qué
2. Problemas concretos de legibilidad (contraste, textos, jerarquía, márgenes, solapamientos)
3. Cómo potenciar el código de color de dominio
4. Sugerencias accionables de color/sombras/tipografía/espaciado aplicables en pygame

Usá el archivo INDICE.md (primera imagen) como referencia. Al final, lista priorizada las 10 mejoras de mayor impacto y, si procede, 2-3 ejemplos concretos para la pantalla principal."""


def _key():
    with open(os.path.join(RAIZ, ".env"), encoding="utf-8") as f:
        for linea in f:
            if linea.startswith("GEMINI_API_KEY="):
                return linea.split("=", 1)[1].strip()
    return os.environ.get("GEMINI_API_KEY")


def main():
    key = _key()
    if not key:
        print("Falta GEMINI_API_KEY en .env")
        sys.exit(1)
    client = genai.Client(api_key=key)

    partes = [PROMPT]
    indice = os.path.join(CARPETA, "INDICE.md")
    if os.path.exists(indice):
        with open(indice, encoding="utf-8") as f:
            partes.append(f"Contenido de INDICE.md:\n\n{f.read()}")
    for nombre in sorted(os.listdir(CARPETA)):
        if nombre.lower().endswith(".png"):
            img = os.path.join(CARPETA, nombre)
            with open(img, "rb") as f:
                partes.append(types.Part.from_bytes(data=f.read(), mime_type="image/png"))
            print(f"Adjunto: {nombre}")

    print("Consultando Gemini 2.5 Flash...")
    resp = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=partes,
    )
    salida = resp.text or ""
    if not salida:
        # fallback: extraer texto manualmente de las partes
        for candidate in (resp.candidates or []):
            for p in (candidate.content.parts or []):
                if getattr(p, "text", None):
                    salida += p.text
    print("Finish reason:", resp.candidates[0].finish_reason if resp.candidates else "N/A")
    ruta = os.path.join(CARPETA, "sugerencias_gemini.md")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(salida)
    print("\n--- RESPUESTA ---\n")
    print(salida)
    print(f"\nGuardado en {ruta}")


if __name__ == "__main__":
    main()
