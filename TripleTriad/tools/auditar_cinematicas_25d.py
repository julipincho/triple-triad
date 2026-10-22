"""Auditoria visual de las cinemáticas 2.5D.

Genera capturas a t=0/4/8 para las tres escenas del piloto, con el 2.5D
activado y desactivado, y mide el tiempo de dibujo. Los PNG quedan en
`auditoria/cinematicas_25d_20261022/`.
"""

import os
import sys
import tempfile
import time
import json
import unittest.mock as mock

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("TRIPLETRIAD_DATA", tempfile.mkdtemp(prefix="tt_audit_25d_"))
sys.path.insert(0, RAIZ)

import pygame

DESTINO = os.path.join(RAIZ, "auditoria", "cinematicas_25d_20261022")
ESCENAS = ["salon_torneo", "camino_lluvioso", "sala_trono"]
TIEMPOS = (0.0, 4.0, 8.0)


def main() -> int:
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    os.makedirs(DESTINO, exist_ok=True)

    import cinematicas
    import cinematicas_25d

    resultados = {}
    for nombre in ESCENAS:
        datos = {"fondo": "camino", "fondo_hd": nombre + ".png", "texto": ""}
        cine = cinematicas.Cinematica([datos])
        escena = cine.escena()
        resultados[nombre] = {}
        for modo in ("25d", "clasico"):
            with mock.patch("cinematicas_25d.ACTIVO", modo == "25d"):
                if modo == "clasico":
                    # Forzar el fallback aunque el conjunto exista.
                    mock.patch("cinematicas_25d.dibujar_fondo", return_value=False).start()
                for t in TIEMPOS:
                    cine._dibujar(screen, escena, t)
                    pygame.display.flip()
                    ruta = os.path.join(DESTINO, f"{nombre}_{modo}_t{int(t)}.png")
                    pygame.image.save(screen, ruta)
                # medir tiempo de dibujo
                inicio = time.perf_counter()
                for _ in range(120):
                    cine._dibujar(screen, escena, 2.0)
                duracion = time.perf_counter() - inicio
                ms = duracion / 120 * 1000
                resultados[nombre][modo] = {
                    "tiempo_medio_ms": round(ms, 3),
                    "fps_equivalentes": round(1000 / ms, 1) if ms else 0,
                }
                if modo == "clasico":
                    mock.patch.stopall()
        print(f"{nombre}: 25d {resultados[nombre]['25d']['tiempo_medio_ms']} ms, "
              f"clasico {resultados[nombre]['clasico']['tiempo_medio_ms']} ms")

    with open(os.path.join(DESTINO, "resultados.json"), "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
