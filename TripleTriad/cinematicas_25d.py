"""Cinemáticas 2.5D: fondo, plano medio y primer plano con paralaje suave.

El motor dibuja las capas ya generadas por `tools/producir_cinematicas_25d.py`.
No hay inpainting ni segmentación en runtime: cargar tres PNG y desplazarlos
unos píxeles. El movimiento se calcula con `t`, no con delta de frame, así que
es reproducible y no acumula deriva.

Si falta el manifiesto, falta una capa o el jugador pidió movimiento reducido,
el módulo devuelve `False` y `cinematicas._dibujar` sigue por el camino de
siempre (HD o fondo clásico). La variable `TRIPLETRIAD_CINEMATICAS_25D=0`
desactiva la función sin borrar recursos.
"""

from __future__ import annotations

import json
import math
import os
import random
import zlib
from collections import OrderedDict

import pygame

import opciones
from paths import recurso

ACTIVO = os.environ.get("TRIPLETRIAD_CINEMATICAS_25D", "1") != "0"

_RUTA_MANIFEST = "assets/cinematicas_25d/manifest.json"
_MANIFEST = None
_CACHE: "OrderedDict[tuple[str, bool], pygame.Surface]" = OrderedDict()
_CACHE_MAX = 12
_SPRITES = None


# --------------------------------------------------------------------- datos
def recargar():
    """Olvida manifiesto y superficies; útil para tests y para cambiar de lote."""
    global _MANIFEST
    _MANIFEST = None
    _CACHE.clear()


def _manifest() -> dict:
    global _MANIFEST
    if _MANIFEST is None:
        try:
            with open(recurso(_RUTA_MANIFEST), encoding="utf-8") as f:
                _MANIFEST = json.load(f)
        except (OSError, ValueError):
            _MANIFEST = {}
    return _MANIFEST


def _area() -> list[int]:
    return list(_manifest().get("area", [0, 40, 1280, 720]))


def _relleno() -> list[int]:
    return list(_manifest().get("relleno", [24, 12]))


def _base_nombre(valor) -> str:
    texto = str(valor or "").replace("\\", "/").rsplit("/", 1)[-1]
    return texto.rsplit(".", 1)[0]


def clave_de(escena) -> str | None:
    """Nombre del conjunto 2.5D que corresponde a una escena, si existe."""
    if not ACTIVO:
        return None
    escenas = _manifest().get("escenas", {})
    explicita = getattr(escena, "fondo_25d", None)
    if explicita:
        if explicita in escenas:
            return explicita
        return None
    for valor in (
        getattr(escena, "fondo_hd", None),
        getattr(escena, "fondo_lote", None),
        getattr(escena, "fondo", None),
    ):
        clave = _base_nombre(valor)
        if clave in escenas:
            return clave
    return None


def datos_de(escena):
    clave = clave_de(escena)
    if not clave:
        return None, None
    return clave, _manifest()["escenas"][clave]


# ------------------------------------------------------------------ superficies
def _capa(archivo: str, opaca: bool) -> pygame.Surface | None:
    clave = (archivo, opaca)
    cache = _CACHE.get(clave)
    if cache is not None:
        _CACHE.move_to_end(clave)
        return cache
    ruta = recurso(os.path.join("assets", "cinematicas_25d", archivo))
    try:
        imagen = pygame.image.load(ruta)
        imagen = imagen.convert() if opaca else imagen.convert_alpha()
    except (pygame.error, FileNotFoundError, OSError):
        return None
    _CACHE[clave] = imagen
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)
    return imagen


def _bbox(capa: dict, superficie: pygame.Surface) -> tuple[int, int, int, int]:
    bbox = capa.get("bbox")
    if (isinstance(bbox, (list, tuple)) and len(bbox) == 4
            and bbox[2] > 0 and bbox[3] > 0):
        return tuple(int(v) for v in bbox)
    return 0, 0, superficie.get_width(), superficie.get_height()


def desplazamiento(capa: dict, t: float) -> tuple[int, int]:
    """Desplazamiento en píxeles para una capa en el instante `t`."""
    if opciones.movimiento_reducido():
        return 0, 0
    periodo = max(1.0, float(capa.get("periodo", 20)))
    dx = float(capa.get("dx", 0))
    dy = float(capa.get("dy", 0))
    return (
        int(round(dx * math.sin(2 * math.pi * t / periodo))),
        int(round(dy * math.sin(2 * math.pi * t / (periodo * 1.37)))),
    )


# --------------------------------------------------------------------- dibujo
def dibujar_fondo(screen, escena, t: float) -> bool:
    """Pinta las capas 2.5D. Devuelve False si hay que usar el fondo normal."""
    if not ACTIVO:
        return False
    clave, datos = datos_de(escena)
    if not datos:
        return False
    capas = datos.get("capas") or []
    if len(capas) < 2:
        return False

    # Cargar todo antes de pintar: si falta una capa, el fallback no deja
    # media escena dibujada.
    preparadas = []
    for capa in capas:
        superficie = _capa(capa.get("archivo", ""), bool(capa.get("opaca")))
        if superficie is None:
            return False
        preparadas.append((superficie, capa, _bbox(capa, superficie)))

    area = pygame.Rect(*_area())
    relleno_x, relleno_y = _relleno()
    anterior = screen.get_clip()
    screen.set_clip(area)
    try:
        for superficie, capa, (bx, by, bw, bh) in preparadas:
            dx, dy = desplazamiento(capa, t)
            screen.blit(
                superficie,
                (area.x - relleno_x + dx + bx, area.y - relleno_y + dy + by),
                (bx, by, bw, bh),
            )
    finally:
        screen.set_clip(anterior)

    escena._25d_clave = clave
    escena._25d_datos = datos
    return True


def dibujar_particulas(screen, escena, t: float) -> None:
    """Añade lluvia, brasas o polvo sobre el fondo 2.5D."""
    if not ACTIVO:
        return
    datos = getattr(escena, "_25d_datos", None)
    if not datos:
        return
    tipo = datos.get("particulas")
    if not tipo:
        return
    # Con movimiento reducido no movemos capas ni partículas: es la opción
    # que existe justamente para evitar este tipo de animación.
    if opciones.movimiento_reducido():
        return

    particulas = getattr(escena, "_25d_particulas", None)
    if particulas is None or particulas.tipo != tipo:
        semilla = zlib.crc32(str(getattr(escena, "_25d_clave", "")).encode("utf-8"))
        particulas = _Particulas(tipo, semilla & 0xFFFFFFFF)
        escena._25d_particulas = particulas

    area = pygame.Rect(*_area())
    anterior = screen.get_clip()
    screen.set_clip(area)
    try:
        particulas.dibujar(screen, t, area)
    finally:
        screen.set_clip(anterior)


# ------------------------------------------------------------------ partículas
def _sprites():
    global _SPRITES
    if _SPRITES is not None:
        return _SPRITES

    lluvia = []
    for alpha in (70, 100, 130):
        s = pygame.Surface((4, 18), pygame.SRCALPHA)
        pygame.draw.line(s, (195, 215, 235, alpha), (0, 0), (2, 17), 1)
        lluvia.append(s)

    brasas = []
    for brillo in (0.55, 0.75, 1.0):
        s = pygame.Surface((9, 9), pygame.SRCALPHA)
        for y in range(9):
            for x in range(9):
                d = math.hypot(x - 4, y - 4) / 4.2
                if d < 1.0:
                    v = int(255 * (1.0 - d) ** 2.0 * brillo)
                    s.set_at((x, y), (255, 170, 90, v))
        brasas.append(s)

    polvo = []
    for alpha in (35, 55, 75):
        s = pygame.Surface((3, 3), pygame.SRCALPHA)
        pygame.draw.circle(s, (225, 220, 205, alpha), (1, 1), 1)
        polvo.append(s)

    _SPRITES = {"lluvia": lluvia, "brasas": brasas, "polvo": polvo}
    return _SPRITES


class _Particulas:
    """Sistema determinista: la posición es función de `t`, no de los frames."""

    def __init__(self, tipo: str, semilla: int):
        self.tipo = tipo
        self.rng = random.Random(semilla)
        self.datos = []
        if tipo == "lluvia":
            for i in range(82):
                self.datos.append((
                    self.rng.uniform(0, 1280 + 80),
                    self.rng.uniform(0, 720 + 40),
                    self.rng.uniform(0.70, 1.30),
                    i % 3,
                ))
        elif tipo == "brasas":
            for i in range(36):
                self.datos.append((
                    self.rng.uniform(0, 1280),
                    self.rng.uniform(0, 720),
                    self.rng.uniform(0.55, 1.25),
                    self.rng.uniform(0, math.tau),
                    i % 3,
                ))
        elif tipo == "polvo":
            for i in range(54):
                self.datos.append((
                    self.rng.uniform(0, 1280),
                    self.rng.uniform(0, 720),
                    self.rng.uniform(0.5, 1.4),
                    self.rng.uniform(0, math.tau),
                    i % 3,
                ))

    def dibujar(self, screen, t: float, area: pygame.Rect) -> None:
        if self.tipo == "lluvia":
            self._lluvia(screen, t, area)
        elif self.tipo == "brasas":
            self._brasas(screen, t, area)
        elif self.tipo == "polvo":
            self._polvo(screen, t, area)

    def _lluvia(self, screen, t, area):
        sprites = _sprites()["lluvia"]
        for x0, y0, vel, variante in self.datos:
            x = area.x + (x0 + 46 * vel * t) % (area.w + 80) - 40
            y = area.y + (y0 + 540 * vel * t) % (area.h + 40) - 20
            screen.blit(sprites[variante], (int(x), int(y)))

    def _brasas(self, screen, t, area):
        sprites = _sprites()["brasas"]
        for x0, y0, vel, fase, variante in self.datos:
            x = area.x + x0 + 13 * math.sin(0.65 * t + fase)
            y = area.y + (y0 - 24 * vel * t) % (area.h + 20) - 10
            brillo = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(1.8 * t + fase))
            sprite = sprites[min(2, int(brillo * 3))]
            screen.blit(sprite, (int(x), int(y)), special_flags=pygame.BLEND_RGBA_ADD)

    def _polvo(self, screen, t, area):
        sprites = _sprites()["polvo"]
        for x0, y0, vel, fase, variante in self.datos:
            x = area.x + (x0 + 7 * vel * t) % area.w
            y = area.y + y0 + 5 * math.sin(0.35 * t + fase)
            screen.blit(sprites[variante], (int(x), int(y)))
