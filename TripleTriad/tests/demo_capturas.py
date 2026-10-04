"""Demos visuales de las reglas: genera capturas en auditoria/.

    python tests/demo_capturas.py

Cada escena monta un tablero concreto para revisar de un vistazo que la
captura basica, la cadena, el Same, el Plus, la habilidad quema y las nuevas
habilidades (muro, furia, embestida) se dibujan bien.
"""

import os
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import campana  # noqa: E402
from main import ALTO, ANCHO, Juego  # noqa: E402
from reglas import CPU, USUARIO, Carta, capturas  # noqa: E402

SALIDA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "auditoria"
)


def poner(juego, nombre, n, s, e, o, dueno, r, c, bando=None, habilidad=None):
    bando = bando or ("humano" if dueno == USUARIO else "orco")
    carta = Carta(nombre, n, s, e, o, bando=bando, habilidad=habilidad)
    carta.dueno = dueno
    juego.board[r][c] = carta
    return carta


def resolver(juego, r, c):
    """Aplica la cadena de capturas para que el dibujo muestre los efectos."""
    caps = capturas(juego.board, r, c)
    ahora = time.time()
    for cr, cc in caps:
        juego.flash.append((cr, cc, ahora, USUARIO))
        juego._explosion(cr, cc, USUARIO)
    return caps


def render(juego, nombre):
    screen = pygame.display.get_surface()
    # el fundido de entrada oscureceria la captura: lo damos por terminado
    juego.t_entrada = time.time() - 10
    juego.dibujar(screen)
    pygame.image.save(screen, os.path.join(SALIDA, nombre))
    print(f"  {nombre}")


def juego_nuevo(bando="humano", rival="orco"):
    info = dict(campana.DUELISTAS[rival])
    info.update({"bando": rival, "nombre_faccion": "Orcos", "titulo": "Demo de reglas",
                 "dificultad": 1, "escena": "campamento", "previa": [],
                 "tipo": "rapida", "nodo": "rapida"})
    return Juego(bando, bando_rival=rival, info=info)


def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    pygame.display.set_mode((ANCHO, ALTO))
    os.makedirs(SALIDA, exist_ok=True)

    # 1) Tablero limpio con la mano del jugador
    render(juego_nuevo(), "01_tablero_limpio.png")

    # 2) Captura simple: la carta colocada supera al vecino
    j = juego_nuevo()
    poner(j, "Bruto Rasgador", 8, 5, 7, 4, CPU, 0, 0, bando="orco")
    poner(j, "Sargento Ferrum", 5, 7, 6, 4, USUARIO, 0, 1)
    resolver(j, 0, 1)
    render(j, "02_captura_simple.png")

    # 3) Cadena: una captura arrastra a las demas
    j = juego_nuevo()
    poner(j, "Chaman Karzh", 2, 9, 2, 2, CPU, 1, 2, bando="orco", habilidad="quema")
    poner(j, "Trol de Ceniza", 2, 2, 2, 8, CPU, 2, 2, bando="orco")
    poner(j, "Rey Aldric", 2, 2, 10, 2, USUARIO, 1, 1)
    resolver(j, 1, 1)
    render(j, "03_cadena.png")

    # 4) Same: dos vecinos con el valor opuesto igual
    j = juego_nuevo()
    poner(j, "Lancero", 5, 1, 1, 1, CPU, 0, 1, bando="orco")
    poner(j, "Lancero", 1, 1, 5, 1, CPU, 1, 0, bando="orco")
    poner(j, "Espadachin", 5, 1, 1, 5, USUARIO, 1, 1)
    resolver(j, 1, 1)
    render(j, "04_same.png")

    # 5) Plus: dos comparaciones con la misma suma
    j = juego_nuevo()
    poner(j, "A", 1, 3, 1, 1, CPU, 0, 1, bando="orco")
    poner(j, "B", 1, 1, 1, 2, CPU, 1, 2, bando="orco")
    poner(j, "Arquera", 5, 1, 6, 1, USUARIO, 1, 1)
    resolver(j, 1, 1)
    render(j, "05_plus.png")

    # 6) Habilidad quemа: captura sin comparar valores
    j = juego_nuevo()
    poner(j, "Guardián", 9, 9, 9, 9, CPU, 0, 1, bando="orco")
    poner(j, "Chaman Karzh", 1, 1, 1, 1, USUARIO, 1, 1,
          bando="humano", habilidad="quema")
    resolver(j, 1, 1)
    render(j, "06_quema.png")

    # 7) Muro: la vecina con su mejor lado protegido no cae
    j = juego_nuevo()
    poner(j, "Muro", 9, 2, 2, 2, CPU, 0, 1, bando="orco", habilidad="muro")
    poner(j, "Atacante", 1, 10, 1, 1, USUARIO, 1, 1)
    caps = resolver(j, 1, 1)
    print(f"  (muro bloquea la captura: {len(caps) == 0})")
    render(j, "07_muro.png")

    # 8) Furia: +1 por vecino aliado
    j = juego_nuevo()
    poner(j, "Aliado", 5, 5, 5, 5, USUARIO, 1, 0, bando="humano")
    poner(j, "Bruto Rasgador", 5, 6, 5, 5, USUARIO, 1, 1,
          bando="humano", habilidad="furia")
    poner(j, "Enemigo", 5, 4, 5, 5, CPU, 2, 1, bando="orco")
    resolver(j, 1, 1)
    render(j, "08_furia.png")

    # 9) Embestida: +2 en la casilla central
    j = juego_nuevo()
    poner(j, "Enemigo", 8, 8, 8, 8, CPU, 0, 1, bando="orco")
    poner(j, "Trol de Ceniza", 5, 5, 5, 5, USUARIO, 1, 1,
          bando="humano", habilidad="embestida")
    resolver(j, 1, 1)
    render(j, "09_embestida.png")

    # 10) Sinergia: tres cartas del mismo bando +1 a todo
    j = juego_nuevo()
    for (r, c) in [(0, 0), (0, 2), (2, 2)]:
        poner(j, "Aliado", 5, 5, 5, 5, USUARIO, r, c, bando="humano")
    poner(j, "Espadachin", 1, 5, 1, 1, USUARIO, 1, 1, bando="humano")
    poner(j, "Enemigo", 4, 4, 4, 4, CPU, 2, 1, bando="orco")
    resolver(j, 1, 1)
    render(j, "10_sinergia.png")

    print(f"\nScreenshots en {SALIDA}")


if __name__ == "__main__":
    main()