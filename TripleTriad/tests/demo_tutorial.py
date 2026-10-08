"""Capturas del tutorial para revision visual.

    python tests/demo_tutorial.py

Genera PNGs en auditoria/ (30_tutorial_*.png). Devuelve codigo 1 si
alguna pagina o practica falla al dibujarse.
"""

import os
import sys
import time
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import tutorial  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402

SALIDA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "auditoria"
)


def guardar(screen, nombre):
    os.makedirs(SALIDA, exist_ok=True)
    pygame.image.save(screen, os.path.join(SALIDA, nombre))
    print(f"  {nombre}")


def main():
    pygame.init()
    screen = pygame.display.set_mode((ANCHO, ALTO))
    fallos = 0

    try:
        paginas = tutorial.paginas_manual()
        for i, pagina in enumerate(paginas):
            atras, saltar, sig = tutorial._botones_manual(i == len(paginas) - 1)
            tutorial.dibujar_pagina(screen, pagina, i, len(paginas))
            for b in (atras, saltar, sig):
                b.actualizar(0.016, (0, 0))
                b.dibujar(screen)
            pygame.display.flip()
            guardar(screen, f"30_tutorial_pagina_{i:02d}_{pagina['id']}.png")
        # confirmacion de salto
        tutorial.dibujar_pagina(screen, paginas[0], 0, len(paginas), confirmar=True)
        pygame.display.flip()
        guardar(screen, "30_tutorial_pagina_confirmar.png")

        for pi, practica in enumerate(tutorial.PRACTICAS):
            juego, guia = tutorial.construir_duelo_practica(practica, pi)
            for s in range(len(practica["pasos"])):
                guia.paso = s
                guia.aplicar_paso(juego)
                juego.t_entrada = time.time() - 10
                juego.dibujar(screen)
                guia.dibujar_extra(screen, juego)
                pygame.display.flip()
                guardar(screen, f"31_tutorial_practica_{pi}_{practica['id']}_paso{s}.png")
        # confirmacion de salida en practica
        juego, guia = tutorial.construir_duelo_practica(tutorial.PRACTICAS[0], 0)
        juego.t_entrada = time.time() - 10
        guia.confirmar_salida = True
        juego.dibujar(screen)
        guia.dibujar_extra(screen, juego)
        pygame.display.flip()
        guardar(screen, "31_tutorial_practica_confirmar.png")
    except Exception:
        traceback.print_exc()
        fallos = 1
    print("OK" if not fallos else "FALLOS")
    return fallos


if __name__ == "__main__":
    raise SystemExit(main())
