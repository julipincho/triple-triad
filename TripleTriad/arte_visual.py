"""Seleccion reversible de arte pixel anime; cartas y lotes HD son intocables."""
import json
import os
from functools import lru_cache

from paths import recurso
import lotes_visuales

ACTIVO = os.environ.get("TRIPLETRIAD_ARTE_PIXEL_ANIME", "1") != "0"


@lru_cache(maxsize=1)
def catalogo():
    try:
        with open(recurso("assets/pixel_anime/manifest.json"), encoding="utf-8") as f:
            return json.load(f)["seleccion"]
    except (OSError, ValueError, KeyError):
        return {}


def alternativa(ruta, tipo):
    """Solo rutas aprobadas del manifiesto; un archivo ausente usa el original."""
    if tipo == "retrato":
        nuevo = lotes_visuales.retrato(ruta)
        if nuevo:
            return nuevo
    if not ACTIVO:
        return None
    ruta = os.fspath(ruta).replace("\\", "/")
    return _resolver(ruta, tipo)


@lru_cache(maxsize=256)
def _resolver(ruta, tipo):
    # Presencia verificada una vez; no consultar disco por frame.
    if tipo == "fondo":
        permitida = ruta.startswith("assets/fondos/")
    else:
        permitida = (ruta.startswith("assets/avatar_")
                     or ruta.startswith("assets/escenas/"))
    if not permitida:
        return None
    registro = catalogo().get(ruta)
    if not registro or registro["tipo"] != tipo:
        return None
    destino = registro["ruta"]
    if not destino.startswith("assets/pixel_anime/") or ".." in destino.split("/"):
        return None
    return destino if os.path.isfile(recurso(destino)) else None
