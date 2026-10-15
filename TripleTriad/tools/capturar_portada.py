"""Captura de la portada con el logo, con el renderer real (sin ventana)."""
import os
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["TRIPLETRIAD_DATA"] = tempfile.mkdtemp(prefix="tt_portada_")
import pygame
import pantallas
import ui

SALIDA = BASE / "capturas"
SALIDA.mkdir(exist_ok=True)


def main():
    pygame.init()
    screen = pygame.display.set_mode((ui.ANCHO, ui.ALTO))
    # Se pinta UN frame del bucle de la portada sin entrar en el bucle
    # asincrono: se replican a mano las piezas que dibuja, con el mismo codigo
    # de la pantalla, para poder ver el resultado sin esperar pulsaciones.
    import asyncio
    import campana
    import facciones
    from pantallas import (Boton, Fondo, fila_centrada, fila_centrada_por_centro,
                           panel, texto, math_seno, _logo_portada, DORADO,
                           BORDE, TEXTO_TENUE, VERSION_JUEGO, LIMIT_FPS,
                           ANCHO, ALTO)
    import cartas as crt
    import mazos

    clock = pygame.time.Clock()
    fondo = Fondo("dragon")
    t = 1.2
    fondo.dibujar(screen, 0.016)

    logo = _logo_portada()
    sup = logo["logo"]
    screen.blit(sup, (ANCHO // 2 - sup.get_width() // 2,
                      logo["y"] - sup.get_height() // 2))

    print(f"logo en pantalla: {logo['w']}x{logo['h']} de {ANCHO}x{ALTO} "
          f"(estatico, sin pasos de animacion)")

    chips = [f"{len(facciones.orden_facciones())} facciones",
             f"{campana.duelos_por_campana()} duelos",
             "Un final por faccion"]
    CHIP_W = max(200, max(ui.ancho_texto(c, 9) for c in chips) + 24)
    x_chip = fila_centrada(CHIP_W, len(chips), 20)
    for i, c in enumerate(chips):
        x = x_chip + i * (CHIP_W + 20)
        panel(screen, pygame.Rect(x, 390, CHIP_W, 40), (16, 17, 26, 200), BORDE, radio=8, grosor=1)
        texto(screen, c, 9, TEXTO_TENUE, centro=(x + CHIP_W // 2, 410))

    bandos = ["humano", "orco", "elfo", "goblin", "dragon"]
    x_carta = fila_centrada_por_centro(104, len(bandos), 240)
    for i, b in enumerate(bandos):
        carta = mazos.TODOS[b][-1]
        clave = crt._slug(carta.nombre)
        c2 = crt.crear(carta, None)
        x = x_carta + i * 240 + math_seno(t * 0.8 + i) * 8
        y = 530 + math_seno(t * 1.1 + i * 1.7) * 12
        rot = crt.rotar(c2, clave, math_seno(t * 0.5 + i) * 2)
        screen.blit(pygame.transform.scale(crt.sombra(c2, clave), rot.get_size()),
                    (x - rot.get_width() // 2 + 4, y - rot.get_height() // 2 + 6))
        screen.blit(rot, (x - rot.get_width() // 2, y - rot.get_height() // 2))

    boton = Boton(pygame.Rect(ANCHO // 2 - 170, ALTO - 120, 340, 52),
                  "PULSA PARA EMPEZAR", 12)
    boton.dibujar(screen)
    texto(screen, f"version {VERSION_JUEGO}", 8, TEXTO_TENUE, centro=(ANCHO // 2, ALTO - 40))
    pygame.image.save(screen, str(SALIDA / "portada_logo.png"))
    print("captura:", SALIDA / "portada_logo.png")
    pygame.quit()


if __name__ == "__main__":
    main()
