"""Produccion img2img local; solo candidatos, nunca cartas ni originales.

Usa ComfyUI existente y conserva referencias, recetas y hashes por lote.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageEnhance, ImageOps

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from generar_escenas import CATALOGO

LOTE = Path(r"E:\AI\CartonesMazmorrasVisual\exports\pixel_anime_20261013_final")
URL = "http://127.0.0.1:8188"
MODELO = "animagine-xl-4.0.safetensors"
REVISION = False
NUEVO = False


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protegidos():
    # Todo arte de cartas (incluidas versiones archivadas) y los lotes aprobados.
    paths = [p for folder in BASE.glob("cartas*") if folder.is_dir()
             for p in folder.rglob("*") if p.is_file()]
    paths += list((BASE / "assets" / "cinematicas_hd").glob("*.png"))
    return {str(p.relative_to(BASE)): sha(p) for p in sorted(paths)}


def inventario():
    conocidos = {e["archivo"]: e for e in CATALOGO.values()}
    paths = sorted((BASE / "assets").glob("avatar_*.png"))
    paths += sorted((BASE / "assets" / "fondos").glob("*.png"))
    paths += sorted((BASE / "assets" / "escenas").glob("*.png"))
    items = []
    for p in paths:
        rel = p.relative_to(BASE / "assets").as_posix()
        base = rel
        variant = ""
        if rel.startswith("fondos/") and "_" in p.stem:
            root, variant = p.stem.split("_", 1)
            base = "fondos/" + root + ".png"
        entry = conocidos.get(base, {})
        variants = {"amanecer": "warm golden dawn", "noche": "moonlit night",
                    "niebla": "mist and fog", "nevada": "snow covered winter",
                    "nieve": "snow covered winter", "lluvia": "heavy rainfall",
                    "tormenta": "storm clouds lightning", "asedio": "under siege",
                    "brasa": "glowing embers", "derrumbe": "collapsed architecture",
                    "profundo": "deep underground", "guardia": "guards at entrance",
                    "angosto": "narrow magical rift", "ancho": "wide magical rift",
                    "cerrando": "closing magical rift", "deslumbrante": "radiant magical rift",
                    "vacio": "empty stage", "lleno": "crowded stage"}
        items.append(dict(id=p.stem, source=rel,
                          tipo="avatar" if p.name.startswith("avatar_") else "fondo",
                          sujeto=entry.get("sujeto", "fantasy JRPG environment"),
                          extra=entry.get("extra", "") + ", " + variants.get(variant, "")))
    return items


def snapshot():
    LOTE.mkdir(parents=True, exist_ok=True)
    target = LOTE / "protegidos.json"
    if not target.exists():
        target.write_text(json.dumps(protegidos(), indent=2), encoding="utf-8")
    for item in inventario():
        src = BASE / "assets" / item["source"]
        dst = LOTE / "originales" / item["source"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            dst.write_bytes(src.read_bytes())
    (LOTE / "inventario.json").write_text(json.dumps(inventario(), indent=2), encoding="utf-8")


def verificar():
    assert protegidos() == json.loads((LOTE / "protegidos.json").read_text()), "Arte protegido alterado"
    for item in inventario():
        assert sha(BASE / "assets" / item["source"]) == sha(LOTE / "originales" / item["source"])


def generar(item):
    name = item["id"]
    avatar = item["tipo"] == "avatar"
    target = LOTE / ("nuevo" if NUEVO else "revision" if REVISION else "candidatos") / item["source"]
    if target.exists():
        return
    reference = LOTE / "originales" / item["source"]
    if name in ("publico", "escenario", "salon", "apagon"):
        reference = BASE / "assets" / "cinematicas_hd" / "salon_torneo_lleno.png"
    if REVISION and not avatar:
        root = name.split("_", 1)[0]
        reference = LOTE / "candidatos" / "fondos" / (root + ".png")
        if root == "trono":
            reference = BASE / "assets" / "cinematicas_hd" / "sala_trono.png"
        if root in ("escenario", "apagon"):
            reference = BASE / "assets" / "cinematicas_hd" / "salon_torneo_lleno.png"
    size = (768, 768) if avatar else (1024, 576)
    im = Image.open(reference).convert("RGB")
    if REVISION and name in ("apagon", "ceniza"):
        im = ImageEnhance.Color(im).enhance(0.12)
        if name == "apagon":
            im = ImageEnhance.Brightness(im).enhance(0.12)
    im = ImageOps.fit(im, size, method=Image.Resampling.NEAREST)
    upload = LOTE / "referencias" / (name + ".png")
    upload.parent.mkdir(parents=True, exist_ok=True)
    im.save(upload)
    with upload.open("rb") as f:
        r = requests.post(URL + "/upload/image", files={"image": ("pa_" + name + ".png", f, "image/png")}, timeout=60)
    r.raise_for_status()
    uploaded = r.json()
    input_name = "/".join(filter(None, [uploaded.get("subfolder"), uploaded["name"]]))
    subject = item["sujeto"]
    # Las referencias actuales ya corrigieron la anatomia de las bestias.
    if name == "avatar_hombre_lobo":
        subject = "solo, anthro grey wolf warrior, long wolf muzzle, amber eyes, silver fur, leather armor, bust portrait"
    if name == "avatar_hombre_pantera":
        subject = "solo, anthro black panther warrior, rounded feline ears, short feline muzzle, golden eyes, black fur, leather armor, bust portrait"
    positive = ("masterpiece, best quality, very aesthetic, detailed pixel art, anime JRPG, "
                "fine crisp pixel clusters, clean expressive shapes, selective colorful highlights, "
                "rich jewel tones, readable silhouette, balanced palette, delicate shading, " + subject + ", " + item["extra"])
    if avatar:
        positive += ", head and shoulders, same character design, simple muted background, expressive eyes, clean cel shading"
    else:
        positive += ", cinematic wide composition, layered environment, detailed architecture, atmospheric depth"
    negative = "photograph, photorealistic, 3d render, blurry, text, watermark, logo, frame, collage, duplicate, bad anatomy, deformed face, oversaturated"
    if REVISION and not avatar:
        moods = {
            "apagon": "near black modern tournament hall after power failure, lights off, extremely dark silhouettes, faint emergency light, deep black shadows",
            "ceniza": "dead wasteland covered in grey ash, black bare leafless tree, dead twisted branches, grey overcast sky, no living vegetation, monochrome grey",
            "umbral": "huge upright vertical portal, magical blue rift between dark stone pillars, radiant doorway leading to another world, dark interior cavern, floating cards",
            "camino_lluvia": "pine forest road in heavy rain, wet puddles, diagonal rain streaks, grey storm clouds, blue wet foliage",
            "campamento_niebla": "canvas tents and campfire almost hidden in thick white fog, misty forest, cold desaturated blue atmosphere",
            "campamento_tormenta": "canvas tents in heavy thunderstorm, dramatic lightning in dark clouds, heavy diagonal rainfall, wet ground",
            "campamento_asedio": "canvas tents behind wooden barricades, siege camp, sharpened stakes, distant fires, no characters in foreground",
        }
        root = name.split("_", 1)[0]
        positive = "detailed pixel art, anime JRPG background, crisp pixel clusters, wide cinematic composition, "
        positive += moods.get(name, moods.get(root, subject)) + ", " + item["extra"]
        negative += ", split screen, panels, japanese temple, torii, pagoda"
        if name in ("apagon", "ceniza"):
            positive = "detailed pixel art, wide cinematic composition, " + moods[name]
            negative += ", bright, colourful, vibrant, daylight, leaves, green grass, bloom"
    seed = int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)
    denoise = 0.38 if avatar else 0.60
    if REVISION:
        denoise = 0.78
        if name == "apagon":
            denoise = 0.30
    model = MODELO if avatar else "pixelArtDiffusionXL_spriteShaper.safetensors"
    graph = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": model}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": positive, "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["1", 1]}},
        "4": {"class_type": "LoadImage", "inputs": {"image": input_name}},
        "5": {"class_type": "VAEEncode", "inputs": {"pixels": ["4", 0], "vae": ["1", 2]}},
        "6": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["5", 0], "seed": seed, "steps": 24, "cfg": 5.5, "sampler_name": "euler", "scheduler": "normal", "denoise": denoise}},
        "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
        "8": {"class_type": "SaveImage", "inputs": {"images": ["7", 0], "filename_prefix": "pixel_anime_20261013/" + name}},
    }
    if NUEVO:
        graph.pop("4")
        graph["5"] = {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 576, "batch_size": 1}}
        graph["6"]["inputs"].update(denoise=1.0, steps=30, cfg=6.5)
        root = name.split("_", 1)[0]
        subjects = {
            "umbral": "a tall vertical open doorway, glowing blue portal between two massive black stone columns, a bright door shaped opening in dark rock, frontal view, empty ground in front, no people, mysterious dimensional gate, fantasy dungeon",
            "ceniza": "a dead barren wasteland, one completely bare dead tree with thin twisted black branches, grey ash falling like snow, broken towers far away, empty desolate ground, monochrome grey and black, overcast",
            "campamento_niebla": "a small medieval canvas tent almost invisible in dense white fog, faint campfire, pine trees fading into thick blue grey mist, low visibility, foggy campsite",
            "campamento_asedio": "medieval encampment with canvas tents behind a wooden defensive palisade, sharp wooden stakes and shields, distant fire, siege barricades, tense atmosphere",
            "trono_derrumbe": "empty gothic throne room in ruins, shattered columns fallen on stone floor, rubble, collapsed roof, intact empty throne in distance, cold light",
            "trono_guardia": "empty gothic throne room with two armored sentries standing at the sides of the distant empty throne, purple banners, warm braziers, tall columns",
            "trono_nieve": "empty gothic throne room in winter, snow on the floor and steps, frost on columns, ice, broken windows, empty throne, cold blue lighting",
        }
        graph["2"]["inputs"]["text"] = "pixel art, detailed anime JRPG background, wide cinematic composition, " + subjects.get(name, subjects.get(root, subject)) + ", " + item["extra"]
        graph["3"]["inputs"]["text"] += ", fountain, waterfall, pedestal, raised platform, green leaves, collage, panels"
    r = requests.post(URL + "/prompt", json={"prompt": graph}, timeout=60)
    r.raise_for_status()
    pid = r.json()["prompt_id"]
    print(f"GENERANDO {name}: {pid}", flush=True)
    deadline = time.monotonic() + 1800
    while time.monotonic() < deadline:
        history = requests.get(URL + "/history/" + pid, timeout=30).json().get(pid)
        if history:
            if history.get("status", {}).get("status_str") == "error":
                raise RuntimeError(history["status"])
            images = history.get("outputs", {}).get("8", {}).get("images", [])
            if images:
                result = requests.get(URL + "/view", params=images[0], timeout=60)
                result.raise_for_status()
                master = LOTE / ("masters_nuevo" if NUEVO else "masters_revision" if REVISION else "masters") / (name + ".png")
                master.parent.mkdir(parents=True, exist_ok=True)
                master.write_bytes(result.content)
                image = Image.open(master).convert("RGB")
                grid = (256, 256) if avatar else (640, 360)
                final = (256, 256) if avatar else (1280, 720)
                image = image.resize(grid, Image.Resampling.LANCZOS)
                image = ImageEnhance.Color(image).enhance(1.08)
                image = image.quantize(colors=128 if avatar else 192, dither=Image.Dither.NONE).convert("RGB")
                image = image.resize(final, Image.Resampling.NEAREST)
                target.parent.mkdir(parents=True, exist_ok=True)
                image.save(target)
                recipe = dict(item, seed=seed, denoise=denoise, reference_sha256=sha(reference),
                              result_sha256=sha(target), workflow=graph)
                (target.with_suffix(".json")).write_text(json.dumps(recipe, indent=2), encoding="utf-8")
                print(f"LISTO {target}", flush=True)
                return
        time.sleep(2)
    raise TimeoutError(pid)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", nargs="*")
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--verificar", action="store_true")
    parser.add_argument("--revision", action="store_true")
    parser.add_argument("--nuevo", action="store_true")
    args = parser.parse_args()
    REVISION = args.revision
    NUEVO = args.nuevo
    snapshot()
    if args.verificar:
        verificar()
        print("Cartas, lotes aprobados y originales intactos")
    elif not args.snapshot:
        for item in inventario():
            if args.ids is None or item["id"] in args.ids:
                generar(item)
        verificar()
