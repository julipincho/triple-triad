"""Banco de pruebas de render: mide ms/frame del duelo y de la portada.

No es un test (no usa unittest): es una herramienta de diagnostico para saber
que parte del frame se lleva el tiempo. Se ejecuta con el driver de video
falso, asi que no abre ventana y da cifras comparables entre ejecuciones.

    python tests/bench_render.py            # 200 frames de duelo y portada
    python tests/bench_render.py 400 --perfil   # ademas, cProfile ordenado

El navegador (pygbag) ejecuta el mismo codigo sobre WASM/Asyncify, que es
varias veces mas lento: las cifras de aqui son la cota inferior, pero el
*ranking* de donde se va el tiempo es el mismo, y ahi es donde hay que
optimizar (crear Surface y renderizar texto cada frame es carisimo en wasm).
"""

import cProfile
import os
import pstats
import random
import sys
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import cartas as cartas_mod  # noqa: E402
import mazos  # noqa: E402
import partida as partida_mod  # noqa: E402
import pantallas  # noqa: E402
import reglas  # noqa: E402
import ui  # noqa: E402


def _preparar():
    pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()
    return pygame.display.set_mode((ui.ANCHO, ui.ALTO))


def _cronometrar(dibujar, frames, warmup=8):
    """Devuelve (media, p95, maximo) en ms por frame, ya calentado."""
    for _ in range(warmup):
        dibujar()
    muestras = []
    for _ in range(frames):
        t0 = time.perf_counter()
        dibujar()
        muestras.append((time.perf_counter() - t0) * 1000.0)
    muestras.sort()
    media = sum(muestras) / len(muestras)
    p95 = muestras[int(len(muestras) * 0.95)]
    return media, p95, muestras[-1]


def _informe(nombre, media, p95, maxi):
    print(f"{nombre:<10}: media {media:6.2f} ms  p95 {p95:6.2f} ms  max {maxi:6.2f} ms"
          f"   -> techo {1000 / media:5.1f} fps")


def _perfil(dibujar, veces=40):
    dibujar()
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(veces):
        dibujar()
    pr.disable()
    pstats.Stats(pr).sort_stats("tottime").print_stats(25)


class _Parar(Exception):
    """Se lanza desde el reloj para cerrar el bucle de la pantalla."""


class RelojVacio:
    """Reloj que NO espera: la pantalla dibuja tan rapido como puede.

    Es lo que hace falta para medir el coste de un frame y no el tope de 60 fps
    que impone el reloj de verdad.
    """

    def __init__(self, frames, calentar=8):
        self.frames = frames
        self.calentar = calentar
        self.n = 0

    def tick(self, fps=0):
        self.n += 1
        if self.n > self.calentar and self.n > self.frames:
            raise _Parar
        return 16


def pantalla(nombre, frames, perfil=False, Eventos=None):
    """Mide una pantalla real (la de pygame) corrido hasta N frames."""
    import asyncio

    screen = _preparar()
    reloj = RelojVacio(frames)
    original = pygame.event.get
    enviados = Eventos or []

    def eventos():
        if enviados:
            return [enviados.pop()]
        return []

    pygame.event.get = eventos
    inicio = time.perf_counter()
    try:
        if perfil:
            pr = cProfile.Profile()
            pr.enable()
            try:
                asyncio.run(nombre(screen, reloj))
            except _Parar:
                pass
            pr.disable()
            pstats.Stats(pr).sort_stats("tottime").print_stats(25)
            return
        try:
            asyncio.run(nombre(screen, reloj))
        except _Parar:
            pass
        transcurrido = time.perf_counter() - inicio
    finally:
        pygame.event.get = original
    dibujados = reloj.n - reloj.calentar
    media = transcurrido / max(1, dibujados) * 1000
    print(f"{nombre.__name__:20}: media {media:6.2f} ms  -> techo {1000 / media:5.1f} fps")


def faccion(frames, perfil=False):
    """Selector de faccion: 7 fichas + panel lateral con 5 miniaturas.

    Fue la pantalla mas lenta del juego en la web (35 fps) por leer el perfil
    en disco 7 veces por frame y por escalar 12 cartas cada frame.
    """
    eventos = [pygame.event.Event(pygame.MOUSEMOTION, pos=(700, 400),
                                  rel=(0, 0), buttons=(0, 0, 0))]
    pantalla(pantallas.elegir_faccion, frames, perfil, Eventos=eventos)


def duelo(frames, perfil=False):
    """El duelo es la pantalla mas pesada: tablero, mano, HUD y tooltips."""
    screen = _preparar()
    juego = partida_mod.Juego("humano", "orco")
    # algunas cartas en el tablero: es el caso real a mitad de partida
    for carta in list(juego.mano_u)[:4]:
        vacias = reglas.celdas_vacias(juego.board)
        if not vacias:
            break
        r, c = vacias[0]
        juego.colocar(carta, juego.mano_u, partida_mod.USUARIO, r, c)
    juego.t_entrada = 0.0  # sin fundido de entrada midiendo

    def frame():
        juego.dibujar(screen)
        pygame.display.flip()

    if perfil:
        _perfil(frame)
        return
    media, p95, maxi = _cronometrar(frame, frames)
    _informe("duelo", media, p95, maxi)


def portada(frames, perfil=False):
    """Reproduce el cuerpo del bucle de pantallas.portada() sin eventos.

    Incluye lo caro: fondo con 70 particulas, logo, las 5 cartas flotando
    (rotate + sombra nueva por frame) y el boton.
    """
    screen = _preparar()
    fondo = pantallas.Fondo("dragon")
    boton = ui.Boton(pygame.Rect(ui.ANCHO // 2 - 170, ui.ALTO - 120, 340, 52),
                     "PULSA PARA EMPEZAR", 12)
    cartas = [(f, mazos.TODOS[f][-1]) for f in
              ("humano", "orco", "elfo", "goblin", "dragon")]
    t = [0.0]

    def frame():
        t[0] += 1 / 60
        tt = t[0]
        fondo.dibujar(screen, 1 / 60)

        escala = 1 + 0.012 * pantallas.math_seno(tt * 1.6)
        tam = int(40 * escala)
        ui.resplandor(screen, pygame.Rect(ui.ANCHO // 2 - 260, 120, 520, 70),
                      ui.DORADO, 60, 3, 8)
        ui.texto(screen, "TRIPLE TRIAD", tam, ui.DORADO, centro=(ui.ANCHO // 2, 150))
        ui.texto(screen, "Goblins  Elfos  Humanos  Orcos  y mas", 11, ui.TEXTO,
                 centro=(ui.ANCHO // 2, 200))
        for i, sub in enumerate(["Siete facciones", "Cinco duelos",
                                 "Un final por faccion"]):
            x = ui.ANCHO // 2 - 300 + i * 220
            ui.panel(screen, pygame.Rect(x - 90, 250, 180, 40), (16, 17, 26, 200),
                     ui.BORDE, radio=8, grosor=1)
            ui.texto(screen, sub, 9, ui.TEXTO_TENUE, centro=(x, 270))
        for i, (f, carta) in enumerate(cartas):
            sup = cartas_mod.crear(carta, None)
            x = 120 + i * 240 + pantallas.math_seno(tt * 0.8 + i) * 8
            y = 380 + pantallas.math_seno(tt * 1.1 + i * 1.7) * 12
            sombra = pygame.Surface(sup.get_size(), pygame.SRCALPHA)
            sombra.fill((0, 0, 0, 90))
            rot = pygame.transform.rotate(sup, pantallas.math_seno(tt * 0.5 + i) * 2)
            screen.blit(sombra, (x - sup.get_width() // 2 + 4,
                                 y - sup.get_height() // 2 + 6))
            screen.blit(rot, (x - rot.get_width() // 2, y - rot.get_height() // 2))
        boton.actualizar(1 / 60, (0, 0))
        boton.dibujar(screen)
        ui.texto(screen, f"version {pantallas.VERSION_JUEGO}", 8, ui.TEXTO_TENUE,
                 centro=(ui.ANCHO // 2, ui.ALTO - 40))
        pygame.display.flip()

    if perfil:
        _perfil(frame)
        return
    media, p95, maxi = _cronometrar(frame, frames)
    _informe("portada", media, p95, maxi)


def fondo(frames, perfil=False):
    """Solo el fondo animado: es lo que pintan las 19 pantallas."""
    screen = _preparar()
    fondo_ = pantallas.Fondo("dragon")

    def frame():
        fondo_.dibujar(screen, 1 / 60)
        pygame.display.flip()

    if perfil:
        _perfil(frame)
        return
    media, p95, maxi = _cronometrar(frame, frames)
    _informe("fondo", media, p95, maxi)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = {a for a in sys.argv[1:] if a.startswith("-")}
    frames = int(args[0]) if args else 200
    perfil = "--perfil" in flags
    print(f"pygame-ce {pygame.version.ver}, {frames} frames, "
          f"{ui.ANCHO}x{ui.ALTO}, sin ventana")
    duelo(frames, perfil)
    fondo(frames, perfil)
    portada(frames, perfil)
    faccion(frames, perfil)
    pygame.quit()


if __name__ == "__main__":
    random.seed(7)
    main()
