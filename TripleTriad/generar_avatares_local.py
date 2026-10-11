"""Receta local reproducible para los dos retratos de bestias.

Genera candidatos en auditoria/avatares_local, nunca sobre otros avatares.
--instalar copia exclusivamente los dos candidatos elegidos a assets.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageFilter

import generar_cartas_comfyui as comfy

BASE = Path(__file__).resolve().parent
SALIDA = BASE / "auditoria" / "avatares_local"
SUJETOS = {
    "hombre_lobo": "anthropomorphic grey werewolf warrior, unmistakable wolf head, "
                   "long canine muzzle, black nose, pointed upright ears, amber eyes, "
                   "thick silver grey fur, leather shoulder armor, stern expression",
    "hombre_pantera": "anthropomorphic black panther warrior, unmistakable black leopard "
                      "head, rounded feline ears, short broad feline muzzle, black nose, "
                      "golden feline eyes, black fur with blue grey highlights, "
                      "leather shoulder armor, stern expression",
}
ESTILO = (", single fantasy RPG character portrait, head and shoulders, three quarter "
          "view, face fully visible, detailed hand painted Japanese fantasy game "
          "illustration, fine pixel art, intricate small pixel details, soft shading, "
          "restrained colors, pale grey neutral background, soft even lighting, "
          "centered bust composition, no border")
NEGATIVO = ("human face, human ears, human skin, catboy, catgirl, mask, fursuit, "
            "hood, helmet, muzzle strap, collar, frame, border, text, watermark, "
            "multiple characters, character sheet, grid, panels, split image, "
            "photograph, 3d render, chibi, blocky, oversized pixels, blurry, "
            "full body, scenery, forest, moon, neon, oversaturated")
MODELOS = {
    "pixel": "pixelArtDiffusionXL_spriteShaper.safetensors",
    "sdxl": "sd_xl_base_1.0.safetensors",
    "anime": "animagine-xl-4.0.safetensors",
    "retrato": "animagine-xl-4.0.safetensors",
}
VARIANTE_ELEGIDA = "retrato"
SEMILLA_ELEGIDA = 20261010
POSTPROCESO = dict(salida=256, rejilla=128, reduccion="LANCZOS", ampliacion="NEAREST",
                   enfoque=dict(radius=1, percent=140, threshold=3), colores=128, dither="NONE")


def preparar(original, destino):
    """Paleta compacta y bordes de pixel fino, al tamano de los otros retratos."""
    im = Image.open(original).convert("RGB").resize((128, 128), Image.Resampling.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=1, percent=140, threshold=3))
    im.quantize(colors=128, dither=Image.Dither.NONE).convert("RGBA").resize(
        (256, 256), Image.Resampling.NEAREST).save(destino)


def hashes_otros():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (BASE / "assets").glob("avatar_*.png")
            if p.stem.removeprefix("avatar_") not in SUJETOS}


def generar(nombre, variante, seed, servidor):
    if not comfy.arrancar_servidor(servidor, r"E:\AI\start-comfyui.bat", 180):
        raise RuntimeError("ComfyUI no disponible")
    SALIDA.mkdir(parents=True, exist_ok=True)
    stem = f"{nombre}_{variante}_{seed}"
    original = SALIDA / f"{stem}_original.png"
    receta = dict(nombre=nombre, modelo=MODELOS[variante], seed=seed,
                  positivo=SUJETOS[nombre] + ESTILO, negativo=NEGATIVO,
                  ancho=768, alto=768, pasos=28, cfg=6.0,
                  sampler="euler", scheduler="normal",
                  referencia="assets/avatar_orco.png", **POSTPROCESO)
    if variante in ("anime", "retrato"):
        especie = ("wolf, grey fur, long canine snout, pointed wolf ears" if nombre == "hombre_lobo"
                   else "black panther, black fur, short feline snout, rounded feline ears")
        receta["positivo"] = (
            "masterpiece, best quality, very aesthetic, solo, 1boy, male anthro, furry, "
            + especie + ", animal head, animal nose, yellow eyes, muscular, upper body, "
            "portrait, looking at viewer, three-quarter view, broad shoulders, "
            "brown leather vest, chest visible, fantasy warrior, uncovered face, "
            "retro JRPG portrait, detailed pixel art, textured shading, "
            "detailed fur, pale grey background, simple background, soft lighting")
        receta["negativo"] = NEGATIVO + (
            ", detached head, floating head, bust statue, logo, emblem, "
            "face armor, metal on face, muzzle, bridle, harness, halter, jewelry, "
            "ornament, ornate, mask, straps on face, gold decoration")
        if variante == "retrato":
            receta["positivo"] = receta["positivo"].replace(
                "retro JRPG portrait, detailed pixel art, textured shading",
                "hand painted JRPG character illustration, soft brushwork, "
                "layered fur highlights, detailed textured shading")
            receta["negativo"] += ", flat shading, cel shading, flat colors, vector art"
    # La referencia es de evaluacion visual, no se transfiere su anatomia.
    if not comfy.generar_imagen(servidor, receta["positivo"], receta["negativo"],
                               str(original), seed, 768, 768, 28, 6.0,
                               MODELOS[variante], espera=900):
        raise RuntimeError(f"No se genero {stem}")
    preparar(original, SALIDA / f"{stem}.png")
    (SALIDA / f"{stem}.json").write_text(json.dumps(receta, indent=2), encoding="utf-8")
    print(stem, flush=True)


def instalar(variante, seed):
    antes = hashes_otros()
    candidatos = [SALIDA / f"{nombre}_{variante}_{seed}.png" for nombre in SUJETOS]
    for ruta in candidatos:
        with Image.open(ruta) as im:
            assert im.size == (256, 256)
            im.verify()
    for nombre, ruta in zip(SUJETOS, candidatos):
        (BASE / "assets" / f"avatar_{nombre}.png").write_bytes(ruta.read_bytes())
    assert hashes_otros() == antes, "Se altero otro avatar"
    (SALIDA / "seleccion.json").write_text(json.dumps(
        {"variante": variante, "seed": seed, "otros_avatares_sha256": antes}, indent=2),
        encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variante", choices=MODELOS, default=VARIANTE_ELEGIDA)
    parser.add_argument("--seed", type=int, default=SEMILLA_ELEGIDA)
    parser.add_argument("--servidor", default=comfy.COMFY_URL)
    parser.add_argument("--instalar", action="store_true")
    parser.add_argument("--postprocesar", action="store_true",
                        help="reaplica pixel fino a los originales ya generados")
    args = parser.parse_args()
    if args.postprocesar:
        for nombre in SUJETOS:
            stem = f"{nombre}_{args.variante}_{args.seed}"
            preparar(SALIDA / f"{stem}_original.png", SALIDA / f"{stem}.png")
            ruta = SALIDA / f"{stem}.json"
            receta = json.loads(ruta.read_text(encoding="utf-8"))
            receta.update(POSTPROCESO)
            ruta.write_text(json.dumps(receta, indent=2), encoding="utf-8")
    elif args.instalar:
        instalar(args.variante, args.seed)
    else:
        for nombre in SUJETOS:
            generar(nombre, args.variante, args.seed, args.servidor)


if __name__ == "__main__":
    main()
