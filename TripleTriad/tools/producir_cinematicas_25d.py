"""Genera capas 2.5D para cinemáticas a partir de los fondos HD aprobados.

Cada fondo se separa en tres capas (fondo, medio y frente) usando
profundidad + segmentación semántica. Las zonas que quedan ocultas al mover
las capas se rellenan con inpainting, y el resultado se guarda con un pequeño
margen de sobra para que el parallax no enseñe los bordes.

Este script es una herramienta de producción, no parte del juego: necesita
torch/transformers/opencv y se ejecuta con el venv visual, no con el del
juego. Los assets generados sí son runtime y viven en
`assets/cinematicas_25d/`.

Ejemplo:

    E:\\AI\\CartonesMazmorrasVisual\\venv-sdxl\\Scripts\\python.exe ^
        tools/producir_cinematicas_25d.py

    ... --escena salon_torneo --fuerza
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "assets" / "cinematicas_hd"
SALIDA = RAIZ / "assets" / "cinematicas_25d"
EVIDENCIA = RAIZ / "auditoria" / "cinematicas_25d_20261022"

MODELO_PROFUNDIDAD = "depth-anything/Depth-Anything-V2-Small-hf"
MODELO_SEGMENTACION = "nvidia/segformer-b0-finetuned-ade-512-512"

# Margen de sobra de cada capa (px) y tamaño final. El fondo mide 1280x720 y
# se coloca centrado; el parallax nunca llega a enseñar el borde.
RELLENO_X = 24
RELLENO_Y = 12
CAPAS = (
    # (sufijo, dx, dy, periodo, opaca)
    # La capa de fondo se mueve mas que el medio y el frente: el paralaje
    # sale de esa diferencia. Los periodos son distintos para que no oscilen
    # todos a la vez.
    ("00_fondo", 12, 6, 24, True),
    ("01_medio", 5, 2, 18, False),
    ("02_frente", 2, 1, 13, False),
)

# Cada perfil describe qué clases semánticas forman el frente y el medio.
# `frente_regiones` limita una clase a una zona (el árbol izquierdo del
# bosque, por ejemplo, tiene poca profundidad aparente y la segmentación lo
# confunde con el fondo).
PERFILES = {
    "salon_torneo": {
        "frente_clases": ["table", "chair"],
        "frente_profundidad": 0.62,
        "frente_extra": [("plant", 0.70)],
        "medio_clases": ["table", "chair", "plant", "curtain"],
        "particulas": "polvo",
    },
    "camino_lluvioso": {
        "frente_clases": ["tree", "plant", "palm"],
        "frente_regiones": [(0, 0, 700, 720), (1050, 0, 1280, 720)],
        "frente_extra": [("plant", 0.55)],
        "medio_clases": ["tree", "plant", "palm", "road", "water", "river", "earth"],
        "particulas": "lluvia",
    },
    "sala_trono": {
        "frente_clases": ["floor"],
        "frente_extra": [("wall", 0.60)],
        "medio_clases": ["stairway", "wall"],
        "particulas": "brasas",
    },
}


def sha256(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for trozo in iter(lambda: f.read(1024 * 1024), b""):
            h.update(trozo)
    return h.hexdigest()


def limpiar(mascara: np.ndarray, area_min: float = 0.001) -> np.ndarray:
    """Quita ruido y componentes diminutos de una máscara booleana."""
    m = (mascara.astype(np.uint8) * 255)
    nucleo = np.ones((3, 3), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, nucleo)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, nucleo)
    n, etiquetas, stats, _ = cv2.connectedComponentsWithStats(
        (m > 0).astype(np.uint8), 8)
    fuera = np.zeros_like(m)
    minimo = area_min * m.size
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= minimo:
            fuera[etiquetas == i] = 255
    return fuera


def suavizar(mascara: np.ndarray, radio: float = 1.2) -> np.ndarray:
    return cv2.GaussianBlur(mascara, (0, 0), radio)


def _etiquetas(resultado) -> dict[str, np.ndarray]:
    etiquetas: dict[str, np.ndarray] = {}
    for mascara in resultado:
        clase = mascara["label"]
        etiquetas.setdefault(clase, np.zeros(
            np.array(mascara["mask"]).shape, dtype=bool))
        etiquetas[clase] |= np.array(mascara["mask"]) > 0
    return etiquetas


def _mascara_region(forma, region) -> np.ndarray:
    x0, y0, x1, y1 = region
    m = np.zeros(forma, dtype=bool)
    m[y0:y1, x0:x1] = True
    return m


def construir_mascaras(perfil, etiquetas, profundidad):
    forma = profundidad.shape
    frente = np.zeros(forma, dtype=bool)
    for clase in perfil.get("frente_clases", []):
        m = etiquetas.get(clase, np.zeros(forma, dtype=bool))
        umbral = perfil.get("frente_profundidad")
        if umbral is not None:
            m = m & (profundidad >= umbral)
        frente |= m
    for region in perfil.get("frente_regiones", []):
        zona = _mascara_region(forma, region)
        for clase in perfil.get("frente_clases", []):
            frente |= etiquetas.get(clase, np.zeros(forma, dtype=bool)) & zona
    for clase, umbral in perfil.get("frente_extra", []):
        frente |= etiquetas.get(clase, np.zeros(forma, dtype=bool)) & (
            profundidad >= umbral)

    medio = np.zeros(forma, dtype=bool)
    for clase in perfil.get("medio_clases", []):
        medio |= etiquetas.get(clase, np.zeros(forma, dtype=bool))
    medio &= ~frente

    frente = limpiar(frente)
    medio = limpiar(medio)
    medio[frente > 0] = 0
    return frente, medio


def _con_relleno(capa: np.ndarray) -> np.ndarray:
    return np.pad(capa, ((RELLENO_Y, RELLENO_Y), (RELLENO_X, RELLENO_X), (0, 0)),
                  mode="edge")


def _bbox(alpha: np.ndarray) -> list[int]:
    x, y, w, h = cv2.boundingRect((alpha > 0).astype(np.uint8))
    return [int(x), int(y), int(w), int(h)]


def _guardar_capa(imagen, alpha, ruta: Path, opaca: bool):
    if opaca:
        Image.fromarray(imagen, "RGB").save(ruta, optimize=True)
        return
    rgba = np.dstack([imagen, alpha]).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(ruta, optimize=True)


def _contacto(imagen, fondo, medio, frente, destino: Path, dx=0, dy=0):
    """Compone una vista previa con el desplazamiento indicado."""
    comp = Image.fromarray(fondo, "RGB").convert("RGBA")
    comp.alpha_composite(Image.fromarray(
        np.dstack([imagen, medio]).astype(np.uint8), "RGBA"), (dx // 2, dy // 2))
    comp.alpha_composite(Image.fromarray(
        np.dstack([imagen, frente]).astype(np.uint8), "RGBA"), (dx, dy))
    comp.convert("RGB").save(destino, optimize=True)


def procesar(nombre: str, profundidad_pipe, segmentacion_pipe) -> dict:
    perfil = PERFILES[nombre]
    origen = ENTRADA / f"{nombre}.png"
    if not origen.is_file():
        raise FileNotFoundError(origen)
    imagen = Image.open(origen).convert("RGB")
    if imagen.size != (1280, 720):
        raise ValueError(f"{origen.name}: se esperaba 1280x720, no {imagen.size}")

    profundidad = profundidad_pipe(imagen)["depth"]
    profundidad = np.array(profundidad, dtype=np.float32)
    profundidad = cv2.resize(profundidad, (1280, 720), interpolation=cv2.INTER_LINEAR)
    profundidad = (profundidad - profundidad.min()) / max(
        1e-6, profundidad.max() - profundidad.min())
    profundidad = cv2.GaussianBlur(profundidad, (0, 0), 1.5)

    etiquetas = _etiquetas(segmentacion_pipe(imagen))
    frente, medio = construir_mascaras(perfil, etiquetas, profundidad)

    if frente.sum() < 2000:
        raise ValueError(f"{nombre}: el frente quedó vacío; revisar el perfil")
    if medio.sum() < 2000:
        raise ValueError(f"{nombre}: el medio quedó vacío; revisar el perfil")

    base = np.array(imagen)
    union = ((frente | medio).astype(np.uint8) * 255)
    union = cv2.dilate(union, np.ones((3, 3), np.uint8), iterations=1)
    # LaMa rellena zonas grandes sin las manchas que deja Telea. Es una
    # dependencia opcional del venv visual (simple-lama-inpainting).
    try:
        from simple_lama_inpainting import SimpleLama
        lama = SimpleLama()
        fondo = np.array(lama(imagen, Image.fromarray(union, "L")))
    except Exception as error:  # noqa: BLE001
        print(f"  LaMa no disponible ({error}); uso Telea")
        fondo = cv2.inpaint(cv2.cvtColor(base, cv2.COLOR_RGB2BGR), union, 4,
                            cv2.INPAINT_TELEA)
        fondo = cv2.cvtColor(fondo, cv2.COLOR_BGR2RGB)

    # `limpiar` ya devuelve 0/255; multiplicar otra vez desbordaba el uint8 y
    # dejaba un alfa de 1 (capas casi invisibles).
    frente_suave = suavizar(frente)
    medio_suave = suavizar(medio)

    carpeta = SALIDA / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    capas = []
    for sufijo, dx, dy, periodo, opaca in CAPAS:
        if sufijo == "00_fondo":
            contenido = _con_relleno(np.dstack(
                [fondo, np.full(fondo.shape[:2], 255, np.uint8)]).astype(np.uint8))
            alpha = contenido[:, :, 3]
            rgb = contenido[:, :, :3]
            ruta = carpeta / f"{sufijo}.png"
            _guardar_capa(rgb, alpha, ruta, opaca=True)
            bbox = [0, 0, contenido.shape[1], contenido.shape[0]]
        elif sufijo == "01_medio":
            contenido = _con_relleno(np.dstack(
                [base, medio_suave]).astype(np.uint8))
            ruta = carpeta / f"{sufijo}.png"
            _guardar_capa(contenido[:, :, :3], contenido[:, :, 3], ruta, opaca=False)
            bbox = _bbox(contenido[:, :, 3])
        else:
            contenido = _con_relleno(np.dstack(
                [base, frente_suave]).astype(np.uint8))
            ruta = carpeta / f"{sufijo}.png"
            _guardar_capa(contenido[:, :, :3], contenido[:, :, 3], ruta, opaca=False)
            bbox = _bbox(contenido[:, :, 3])
        capas.append({
            "archivo": f"{nombre}/{ruta.name}",
            "sha256": sha256(ruta),
            "opaca": opaca,
            "bbox": bbox,
            "dx": dx,
            "dy": dy,
            "periodo": periodo,
        })

    EVIDENCIA.mkdir(parents=True, exist_ok=True)
    Image.fromarray((profundidad * 255).astype(np.uint8), "L").save(
        EVIDENCIA / f"{nombre}_profundidad.png", optimize=True)
    Image.fromarray(frente_suave, "L").save(
        EVIDENCIA / f"{nombre}_mascara_frente.png", optimize=True)
    Image.fromarray(medio_suave, "L").save(
        EVIDENCIA / f"{nombre}_mascara_medio.png", optimize=True)
    _contacto(base, fondo, medio_suave, frente_suave,
              EVIDENCIA / f"{nombre}_reposo.png")
    _contacto(base, fondo, medio_suave, frente_suave,
              EVIDENCIA / f"{nombre}_movimiento.png", dx=20, dy=9)

    return {
        "origen": f"assets/cinematicas_hd/{nombre}.png",
        "origen_sha256": sha256(origen),
        "particulas": perfil.get("particulas"),
        "capas": capas,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--escena", action="append", choices=sorted(PERFILES),
                        help="escena a generar; repetir para varias")
    parser.add_argument("--fuerza", action="store_true",
                        help="regenerar aunque las capas ya existan")
    args = parser.parse_args()
    escenas = args.escena or list(PERFILES)

    ruta_manifest = SALIDA / "manifest.json"
    manifest = {}
    if ruta_manifest.is_file():
        manifest = json.loads(ruta_manifest.read_text(encoding="utf-8"))
    manifest.setdefault("version", 1)
    manifest.update({
        "lote": "cinematicas_25d_20261022",
        "lienzo": [1280, 800],
        "area": [0, 40, 1280, 720],
        "relleno": [RELLENO_X, RELLENO_Y],
        "modelos": {
            "profundidad": MODELO_PROFUNDIDAD,
            "segmentacion": MODELO_SEGMENTACION,
        },
        "perfiles": PERFILES,
        "escenas": manifest.get("escenas", {}),
    })

    pendientes = []
    for nombre in escenas:
        capas = [SALIDA / nombre / f"{sufijo}.png" for sufijo, *_ in CAPAS]
        if not args.fuerza and all(c.is_file() for c in capas):
            print(f"{nombre}: ya existe (usa --fuerza para regenerar)")
            continue
        pendientes.append(nombre)
    if not pendientes:
        ruta_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
        return 0

    import torch
    from transformers import pipeline

    dispositivo = 0 if torch.cuda.is_available() else -1
    print(f"cargando modelos (device={dispositivo})...")
    profundidad_pipe = pipeline("depth-estimation", model=MODELO_PROFUNDIDAD,
                                device=dispositivo)
    segmentacion_pipe = pipeline("image-segmentation",
                                 model=MODELO_SEGMENTACION, device=dispositivo)
    for nombre in pendientes:
        print(f"procesando {nombre}...")
        manifest["escenas"][nombre] = procesar(
            nombre, profundidad_pipe, segmentacion_pipe)
        print(f"  frente {manifest['escenas'][nombre]['capas'][2]['bbox']} "
              f"medio {manifest['escenas'][nombre]['capas'][1]['bbox']}")

    ruta_manifest.parent.mkdir(parents=True, exist_ok=True)
    ruta_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
    print(f"manifest: {ruta_manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
