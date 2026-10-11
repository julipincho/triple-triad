"""G9: capturas ACTUALES de los estados que hay que revisar.

El objetivo avisa de "no dar por actuales todas las capturas": las que hay en
el repo son anteriores a G1-G8, asi que no sirven para decidir nada. Este
generador pinta las pantallas de verdad, con el codigo de ahora, y cubre los
estados que el cierre pide revisar:

  - normal
  - con el FOCO de teclado visible (el indicador de cian y el galon)
  - texto ampliado (modo lectura al 125%)
  - un estado de ERROR real (excepcion guardada y mostrada por `pantalla_error`)

Las capturas se guardan en `capturas/` como PNG. No se toca ningun asset del
juego: esto solo compone lo que ya hay.

    python tools/capturas_g9.py
"""

import asyncio
import os
import sys
import tempfile
import time
from unittest.mock import patch

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_tmp = tempfile.TemporaryDirectory(prefix="tt_capturas_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

DESTINO = os.path.join(RAIZ, "capturas")

import pygame  # noqa: E402

import campana  # noqa: E402
import opciones  # noqa: E402
import pantallas  # noqa: E402
import ui  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


class Reloj:
    def tick(self, fps=60):
        return 16


class _Fin(Exception):
    """Saca del bucle infinito de la pantalla tras unos frames."""


def pintar(nombre, dibujar, frames=3, eventos=()):
    """Corre `dibujar` unos frames y guarda la pantalla en `capturas/`."""
    pantalla = pygame.display.get_surface()
    estado = {"n": 0}
    cola = list(eventos)

    def get_eventos():
        estado["n"] += 1
        if cola:
            return [cola.pop(0)]
        if estado["n"] > frames:
            raise _Fin()
        return []

    with patch("pygame.event.get", side_effect=get_eventos):
        try:
            r = dibujar(pantalla, Reloj())
            if asyncio.iscoroutine(r):
                asyncio.run(r)
        except _Fin:
            pass
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR pintando {nombre}: {type(exc).__name__}: {exc}")

    ruta = os.path.join(DESTINO, f"{nombre}.png")
    pygame.image.save(pantalla, ruta)
    return ruta


def main():
    os.makedirs(DESTINO, exist_ok=True)
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    opciones.invalidar()

    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)

    # El diario se captura CON contenido: una captura de diario vacio no
    # demuestra que la pantalla funcione, solo que existe.
    for hablante, linea in (
        ("", "Hubo un tiempo en que el mundo amanecia sin ceniza."),
        ("Nara", "Las cartas no son un juego. Son la manera en que el Umbral "
                 "elige a quien deja pasar."),
        ("", "Cruzaste la senda con cinco cartas y ninguna legendaria."),
        ("Nara", "Si vuelves a perder, el paso seguira cerrado. No es una "
                 "amenaza: es como funciona."),
        ("El Anciano del Umbral", "Te veo venir. Te dejo un consejo. Esta vez "
                                  "no cobro."),
    ):
        campana.registrar_dialogo(hablante, linea, faccion="humano")

    def enter():
        return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)

    def tab():
        return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB)

    capturas = []

    print(f"Generando capturas actuales en {DESTINO}")

    # --- estados normales
    capturas.append(pintar("g9_01_menu", lambda s, r: pantallas.menu(s, r, estado)))
    capturas.append(pintar("g9_02_mapa", lambda s, r: pantallas.mapa_campana(s, r, estado)))
    capturas.append(pintar("g9_03_tienda", lambda s, r: pantallas.tienda(s, r, estado)))
    capturas.append(pintar("g9_04_coleccion", lambda s, r: pantallas.coleccion(s, r, estado)))
    capturas.append(pintar("g9_05_ajustes", lambda s, r: pantallas.ajustes(s, r)))
    capturas.append(pintar("g9_06_diario", lambda s, r: pantallas.diario_dialogos(s, r, estado)))

    # --- foco de teclado: se navega y se ve el indicador
    capturas.append(pintar("g9_07_menu_foco", lambda s, r: pantallas.menu(s, r, estado),
                           eventos=[tab()]))
    capturas.append(pintar("g9_08_mapa_foco", lambda s, r: pantallas.mapa_campana(s, r, estado),
                           eventos=[tab()]))
    capturas.append(pintar("g9_09_ajustes_foco", lambda s, r: pantallas.ajustes(s, r),
                           eventos=[tab()]))

    # --- texto ampliado (modo lectura)
    opciones.fijar("texto_grande", True)
    ui.fijar_escala_texto(1.25)
    capturas.append(pintar("g9_10_menu_texto_ampliado",
                           lambda s, r: pantallas.menu(s, r, estado)))
    capturas.append(pintar("g9_11_ajustes_texto_ampliado",
                           lambda s, r: pantallas.ajustes(s, r)))
    capturas.append(pintar("g9_12_diario_texto_ampliado",
                           lambda s, r: pantallas.diario_dialogos(s, r, estado)))
    opciones.fijar("texto_grande", False)
    ui.fijar_escala_texto(1.0)

    # --- error real: se lanza y se muestra la pantalla de error del juego
    def _error_real(s, r):
        return pantallas.pantalla_error(
            s, r, RuntimeError("fallo de prueba"), "Traceback de prueba", "captura")

    capturas.append(pintar("g9_13_error", _error_real))

    print(f"{len(capturas)} capturas escritas")
    for ruta in capturas:
        if os.path.exists(ruta):
            print(f"  {os.path.basename(ruta)}  ({os.path.getsize(ruta) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())