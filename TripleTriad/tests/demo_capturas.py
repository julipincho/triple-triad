"""Genera screenshots de auditoría visual en auditoria/."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from main import Juego, ANCHO, ALTO
from reglas import CPU, USUARIO, Carta

SALIDA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "auditoria"
)


def poner(juego, nombre, n, s, e, o, dueno, r, c, resolver=False):
    bando = "goblin" if dueno == USUARIO else "elfo"
    carta = Carta(nombre, n, s, e, o, bando=bando)
    carta.dueno = dueno
    juego.board[r][c] = carta
    if resolver:
        from reglas import capturas
        caps = capturas(juego.board, r, c)
        ahora = __import__("time").time()
        for cr, cc in caps:
            juego.flash.append((cr, cc, ahora, dueno))
    return carta


def render(juego, nombre):
    screen = pygame.display.get_surface()
    juego.dibujar(screen)
    pygame.image.save(screen, os.path.join(SALIDA, nombre))


def main():
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_mode((ANCHO, ALTO))
    os.makedirs(SALIDA, exist_ok=True)

    # 1) Tablero limpio
    j = Juego("goblin")
    render(j, "01_tablero_limpio.png")

    # 2) Captura simple
    j = Juego("goblin")
    poner(j, "Mordedor", 8, 4, 6, 5, CPU, 0, 0)
    poner(j, "Arquero", 7, 5, 8, 3, USUARIO, 0, 1, resolver=True)
    j.ultima_jugada = (0, 1, 0)  # sin animación
    render(j, "02_captura_simple.png")

    # 3) Cadena
    j = Juego("goblin")
    poner(j, "X", 2, 9, 2, 2, CPU, 1, 2)
    poner(j, "Y", 2, 2, 2, 8, CPU, 2, 2)
    poner(j, "Lanzasalgo", 2, 2, 9, 2, USUARIO, 1, 1, resolver=True)
    render(j, "03_cadena.png")

    # 4) Tablero a mitad de partida
    j = Juego("goblin")
    poner(j, "Mordedor", 8, 4, 6, 5, USUARIO, 0, 0)
    poner(j, "Arquero", 7, 5, 8, 6, CPU, 0, 1)
    poner(j, "Brujo Verde", 3, 9, 4, 7, USUARIO, 1, 0)
    poner(j, "Dama Hoja", 5, 8, 4, 9, CPU, 2, 2)
    render(j, "04_mitad_partida.png")

    # 5) Same
    j = Juego("goblin")
    poner(j, "A", 5, 5, 1, 1, CPU, 0, 1)
    poner(j, "B", 1, 1, 5, 1, CPU, 1, 0)
    poner(j, "Mago", 5, 1, 1, 5, USUARIO, 1, 1, resolver=True)
    render(j, "05_same.png")

    # 6) Plus
    j = Juego("goblin")
    poner(j, "A", 1, 3, 1, 1, CPU, 0, 1)
    poner(j, "B", 1, 1, 1, 2, CPU, 1, 2)
    poner(j, "Mago", 5, 1, 6, 1, USUARIO, 1, 1, resolver=True)
    render(j, "06_plus.png")

    print(f"Screenshots en {SALIDA}")


if __name__ == "__main__":
    main()
