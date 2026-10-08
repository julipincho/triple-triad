"""Genera el arte faltante con Stable Diffusion local (sin red de pago).

Requiere el entorno `.sd_env` con torch + diffusers (GPU NVIDIA):

    TripleTriad/.sd_env/Scripts/python.exe tests/generar_local.py

Solo genera lo que falta en `cartas/` (mismo criterio que generar_cartas.py).
Usa CompVis/stable-diffusion-v1-4 en fp16 (entra en 6 GB de VRAM).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch  # noqa: E402
from diffusers import StableDiffusionPipeline  # noqa: E402

from generar_cartas import RAZA, slug  # noqa: E402
from mazos import TODOS  # noqa: E402

CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cartas")
MODELO = "CompVis/stable-diffusion-v1-4"


def faltantes():
    pendientes = []
    for bando, cartas in TODOS.items():
        for carta in cartas:
            destino = os.path.join(CARPETA, f"{bando}_{slug(carta.nombre)}.png")
            if not os.path.exists(destino):
                pendientes.append((bando, carta, destino))
    return pendientes


def main():
    pendientes = faltantes()
    print(f"Faltan {len(pendientes)} imagenes.")
    if not pendientes:
        return 0
    tubo = StableDiffusionPipeline.from_pretrained(
        MODELO, torch_dtype=torch.float16, safety_checker=None,
    )
    tubo = tubo.to("cuda")
    tubo.enable_attention_slicing()
    for bando, carta, destino in pendientes:
        prompt = (
            f"{carta.nombre}, fantasy {RAZA[bando]} character portrait, "
            "pixel art style, 16-bit retro video game card illustration, "
            "dark fantasy, centered portrait, no text, no watermark, no border"
        )
        negativo = "text, words, letters, watermark, signature, border, frame, blurry"
        img = tubo(prompt, negative_prompt=negativo, height=640, width=512,
                   num_inference_steps=30, guidance_scale=7.5).images[0]
        img.save(destino)
        print(f"  generada: {os.path.basename(destino)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
