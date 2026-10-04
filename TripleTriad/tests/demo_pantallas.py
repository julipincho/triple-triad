"""Prueba automatica: dibuja cada pantalla sin ventana para detectar errores.

    python tests/demo_pantallas.py

Genera PNGs en auditoria/ para revision visual y devuelve codigo 1 si alguna
pantalla lanza una excepcion.
"""

import os
import sys
import tempfile
import time

# Las capturas no deben tocar los datos del jugador
os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests_demo")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import audio  # noqa: E402
import campana  # noqa: E402
import cartas as crt  # noqa: E402
import cinematicas  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
import pantallas  # noqa: E402
from partida import Juego  # noqa: E402
from reglas import CPU, USUARIO, Carta  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402

SALIDA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "auditoria"
)


class RelojFalso:
    """Reloj que no espera: las pantallas avanzan a velocidad maxima."""

    def tick(self, fps=60):
        return 16

    def get_fps(self):
        return 60

    def get_time(self):
        return int(time.time() * 1000)


def guardar(screen, nombre):
    os.makedirs(SALIDA, exist_ok=True)
    pygame.image.save(screen, os.path.join(SALIDA, nombre))
    print(f"  {nombre}")


class _FinDemo(Exception):
    """Se lanza para cortar un bucle de pantalla que no acepta ESC."""


def correr(nombre, fn, *args, max_eventos=25):
    """Ejecuta una pantalla parcheando eventos para que termine sola."""
    print(f"{nombre}...")
    get_original = pygame.event.get
    clock_original = pygame.time.Clock
    pygame.time.Clock = RelojFalso
    estado = {"n": 0}

    def get_eventos():
        estado["n"] += 1
        # responde como el jugador para validar el dibujo real
        if estado["n"] == 2:
            return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(5, 5), button=1)]
        if estado["n"] > max_eventos:
            raise _FinDemo()
        return []

    pygame.event.get = get_eventos
    try:
        return fn(*args)
    except _FinDemo:
        return "interrumpido"
    finally:
        pygame.event.get = get_original
        pygame.time.Clock = clock_original


def _info(bando, titulo="Duelo rapido", dificultad=1):
    d = dict(campana.DUELISTAS[bando])
    d.update({"bando": bando, "nombre_faccion": facciones.nombre(bando),
              "titulo": titulo, "dificultad": dificultad, "escena": "campamento",
              "previa": [], "tipo": "rapida", "nodo": "rapida"})
    return d


def duel():
    juego = Juego("humano", bando_rival="orco", dificultad=2, info=_info("orco", dificultad=2))
    # el fundido de entrada ensucia las capturas
    juego.t_entrada = time.time() - 10

    def poner(nombre, n, s, e, o, dueno, r, c, bando=None):
        carta = Carta(nombre, n, s, e, o, bando=bando or ("humano" if dueno == USUARIO else "orco"))
        carta.dueno = dueno
        juego.board[r][c] = carta
        return carta

    poner("Sargento Ferrum", 5, 7, 6, 4, USUARIO, 0, 0)
    poner("Bruto Rasgador", 8, 5, 7, 4, CPU, 0, 1)
    poner("Chaman Karzh", 4, 9, 5, 7, CPU, 1, 0)
    poner("Arquera de Torre", 6, 5, 9, 5, USUARIO, 2, 0)
    # coloca la ultima carta de la mano de verdad para ver capturas y efectos
    carta = juego.mano_u[-1]
    juego.colocar(carta, juego.mano_u, USUARIO, 1, 1)
    juego.ultima_jugada = None
    juego.dibujar(SCREEN)
    guardar(SCREEN, "10_duelo.png")

    for (r, c) in [(1, 2), (2, 1), (2, 2), (0, 2), (1, 0)]:
        poner("Espadachin", 8, 6, 5, 7, USUARIO if (r + c) % 2 else CPU, r, c)
    juego.fin = True
    juego.ganador = USUARIO
    juego.mensaje = "Has ganado el duelo"
    juego.tiempo_fin = time.time() - 1.2
    juego.capturas = 7
    juego.jugadas = 9
    juego.cadena_max = 3
    juego.dibujar(SCREEN)
    guardar(SCREEN, "11_duelo_final.png")

    # pausa
    juego.pausa = True
    juego.dibujar(SCREEN)
    from partida import _dibujar_pausa

    _dibujar_pausa(SCREEN, juego)
    guardar(SCREEN, "11b_pausa.png")
    juego.pausa = False


def hoja_de_cartas():
    """Todas las cartas de todas las facciones en una sola imagen."""
    total_filas = len(facciones.orden_facciones())
    alto = total_filas * 200 + 40
    lienzo = pygame.Surface((ANCHO, alto))
    lienzo.fill((22, 23, 32))
    for i, f in enumerate(facciones.orden_facciones()):
        pygame.draw.line(lienzo, facciones.acento(f), (0, 20 + i * 200), (ANCHO, 20 + i * 200), 1)
        for j, carta in enumerate(mazos.TODOS[f]):
            lienzo.blit(crt.crear(carta, None), (20 + j * 140, 30 + i * 200))
            img = pygame.Surface((ANCHO, 1), pygame.SRCALPHA)
            lienzo.blit(crt.crear(carta, None, escala=0.6),
                        (760 + j * 90, 60 + i * 200))
    superficie = pygame.display.get_surface()
    superficie.blit(lienzo, (0, 0))
    pygame.image.save(lienzo, os.path.join(_s(), "12_todas_las_cartas.png"))
    print("  12_todas_las_cartas.png")


def _s():
    os.makedirs(SALIDA, exist_ok=True)
    return SALIDA


SCREEN = None


def cinematica_demo():
    escenas, musica = cinematicas.apertura("humano")
    cin = cinematicas.Cinematica(escenas)
    for i in range(200):
        if not cin.ejecutar_un_frame(SCREEN):
            break
        if i == 150:
            guardar(SCREEN, "23_cinematica.png")
    # final
    variante, titulo, lineas = campana.final_de(campana.nueva_campana("humano"))
    escenas, musica = cinematicas.escenas_final(titulo, lineas, "humano")
    cin = cinematicas.Cinematica(escenas)
    for i in range(120):
        if not cin.ejecutar_un_frame(SCREEN):
            break
    guardar(SCREEN, "24_final.png")


def main():
    global SCREEN
    pygame.init()
    audio.iniciar()
    SCREEN = pygame.display.set_mode((ANCHO, ALTO))
    os.makedirs(SALIDA, exist_ok=True)
    fallos = []

    pasos = [
        ("duelo", duel),
        ("cartas", hoja_de_cartas),
        ("cinematica", cinematica_demo),
    ]
    estado = campana.nueva_campana("humano")
    pantallas_prueba = [
        ("13_portada", lambda: pantallas.portada(SCREEN, RelojFalso())),
        ("13b_menu", lambda: pantallas.menu(SCREEN, RelojFalso(), estado)),
        ("14_elegir_faccion", lambda: pantallas.elegir_faccion(SCREEN, RelojFalso())),
        ("15_mapa", lambda: pantallas.mapa_campana(SCREEN, RelojFalso(), estado)),
        ("16_elegir_rama", lambda: pantallas.elegir_rama(SCREEN, RelojFalso(), estado)),
        ("17_recompensa", lambda: pantallas.recompensa(SCREEN, RelojFalso(), estado, "fortaleza")),
        ("18_encuentro", lambda: pantallas.encuentro(SCREEN, RelojFalso(), estado, "ruinas")),
        ("19_coleccion", lambda: pantallas.coleccion(SCREEN, RelojFalso(), estado)),
        ("20_ajustes", lambda: pantallas.ajustes(SCREEN, RelojFalso())),
        ("21_derrota", lambda: pantallas.derrota(SCREEN, RelojFalso(), estado)),
        ("22_draft", lambda: pantallas.draft(SCREEN, RelojFalso(), estado)),
        ("22b_mejorar", lambda: pantallas.elegir_carta_para_mejorar(SCREEN, RelojFalso(), estado)),
        ("22c_reemplazo", lambda: pantallas.draft_reemplazo(SCREEN, RelojFalso(), estado,
                                                             mazos.HUMANOS[2])),
        ("22d_ficha_nodo", lambda: pantallas._ficha_nodo(SCREEN, RelojFalso(), estado, "fortaleza")),
        ("25_error", lambda: pantallas.pantalla_error(
            SCREEN, RelojFalso(), ValueError("no se pudo cargar la carta"),
            "Traceback (most recent call last):\n"
            '  File "main.py", line 51, in _duelo_rapido\n'
            "    juego = Juego(faccion, bando_rival=rival, info=info)\n"
            "ValueError: no se pudo cargar la carta\n",
            contexto="duelo rápido: Humanos contra Orcos")),
        ("26_elegir_rapida", lambda: pantallas.elegir_faccion(SCREEN, RelojFalso(), modo="rapida")),
    ]
    for nombre, fn in pasos + pantallas_prueba:
        try:
            if nombre in ("duelo", "cartas", "cinematica"):
                fn()
            else:
                correr(nombre, fn)
                guardar(SCREEN, f"{nombre}.png")
        except Exception as e:  # noqa: BLE001
            import traceback

            fallos.append(f"{nombre}: {e!r}")
            traceback.print_exc()

    if fallos:
        print("\nFALLOS:")
        for f in fallos:
            print(" -", f)
        return 1
    print(f"\nTodo correcto. Capturas en {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())