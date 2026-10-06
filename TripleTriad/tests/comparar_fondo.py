"""Compara el fondo animado antes/despues de usar sprites pre-renderizados.

Genera dos PNG del mismo frame (con y sin la capa de particulas clásica) para
comparar a ojo que el cambio no se nota. Herramienta de diagnostico, no test.

    python tests/comparar_fondo.py
"""

import math
import os
import random
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import ui  # noqa: E402

SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "auditoria")


def _particulas_de_prueba(fondo, n):
    """70 particulas con posiciones y alphas fijos: comparables entre capturas."""
    aleatorio = random.Random(1234)
    fondo.particulas = [
        {
            "x": aleatorio.uniform(0, ui.ANCHO),
            "y": aleatorio.uniform(0, ui.ALTO),
            "v": 0.0,
            "r": aleatorio.choice([1, 1, 2, 2, 3]),
            "a": aleatorio.uniform(0.15, 0.5),
        }
        for _ in range(n)
    ]
    return fondo


def _antiguo(screen, fondo, ahora):
    """Como estaba antes: circulos en una capa SRCALPHA a pantalla completa."""
    screen.blit(ui.REC.fondo_tocado(fondo.ruta, (8, 9, 16, 120)), (0, 0))
    capa = pygame.Surface((ui.ANCHO, ui.ALTO), pygame.SRCALPHA)
    pulso = 0.5 + 0.5 * math.sin(ahora * 0.4)
    for p in fondo.particulas:
        pygame.draw.circle(capa, ui.con_alpha((220, 210, 190), 255 * p["a"] * (0.6 + 0.4 * pulso)),
                           (int(p["x"]), int(p["y"])), p["r"])
    screen.blit(capa, (0, 0))


def main():
    pygame.init()
    pygame.display.set_mode((ui.ANCHO, ui.ALTO))
    # `imagen` no es None: es lo que hace pantallas.Fondo y lo que decide que
    # el fondo se pinte en vez de la degradado plano
    fondo = _particulas_de_prueba(
        ui.FondoAnimado(ui.REC.imagen("assets/fondo.png"), ruta="assets/fondo.png"), 70)
    ahora = time.time()

    pantalla = pygame.Surface((ui.ANCHO, ui.ALTO))
    _antiguo(pantalla, fondo, ahora)
    pygame.image.save(pantalla, os.path.join(SALIDA, "fondo_antes.png"))

    pantalla.fill((0, 0, 0))
    fondo.dibujar(pantalla)
    pygame.image.save(pantalla, os.path.join(SALIDA, "fondo_despues.png"))

    print("Capturas en auditoria/fondo_antes.png y fondo_despues.png")
    print("Mismas particulas y mismo instante: solo cambia como se pintan.")


if __name__ == "__main__":
    main()
