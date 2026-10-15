"""Capturas del renderer real con datos temporales, sin tocar el guardado."""
import os
from pathlib import Path
import sys
import tempfile

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["TRIPLETRIAD_DATA"] = tempfile.mkdtemp(prefix="tt_captura_arte_")
import pygame
import cinematicas
import prologo
import narrativa


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    destino = BASE / "capturas" / "pixel_anime"
    destino.mkdir(parents=True, exist_ok=True)
    escenas = {
        "01_nara_campamento": prologo.escenas_nara()[4],
        "02_rajoy_salon_aprobado": prologo.escenas_post_duelo()[0],
        "03_pik_camino_aprobado": prologo.escenas_despertar()[10],
        "04_apagon": prologo.escenas_transporte()[0],
        "05_aldea": narrativa.previa_nodo("aldea")[0],
        "06_fortaleza": narrativa.previa_nodo("fortaleza")[0],
        "07_umbral": {"fondo": "umbral", "texto": ""},
        "08_presentador": prologo.escenas_pre_duelo()[3],
    }
    for nombre, datos in escenas.items():
        cine = cinematicas.Cinematica([datos], nombre_jugador="El duelista")
        escena = cine.escena()
        escena.mostrado = len(escena.texto)
        cine._dibujar(screen, escena, 2.0)
        pygame.image.save(screen, str(destino / (nombre + ".png")))
    pygame.quit()


if __name__ == "__main__":
    main()
