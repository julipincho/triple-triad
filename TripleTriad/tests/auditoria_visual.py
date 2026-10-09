"""Auditoria visual: detecta textos desbordados y elementos fuera de lugar.

    python tests/auditoria_visual.py

Revisa midiendo el render real (ui.MEDIR) que ningun texto se salga de su panel
y ningun rectangulo se salga de la pantalla. Devuelve codigo 1 si hay problemas.
"""

import os
import sys
import tempfile
import asyncio
import time

# Las capturas no deben tocar los datos del jugador
os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests_auditoria")
)
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402
import audio  # noqa: E402
import campana  # noqa: E402
import cartas as crt  # noqa: E402
import cinematicas  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
import pantallas  # noqa: E402
import tutorial  # noqa: E402
from partida import Juego  # noqa: E402
from reglas import CPU, USUARIO, Carta  # noqa: E402
import ui  # noqa: E402

# Activar medicion real. `ui.MEDIR` hace que `registrar`/`_contenedora` hagan
# su trabajo; no hay que reasignar nada porque la guarda esta dentro de ellas.
ui.MEDIR = True

# Envolver flip para capturar frames
_REGISTRO_FRAMES = []


def _hook_flip():
    # Agrupar los rects del frame actual
    frame_rects = list(ui._REGISTRO)
    _REGISTRO_FRAMES.append(frame_rects)
    ui._volcar_frame()
    ui._FLIP_ORIGINAL()


pygame.display.flip = _hook_flip


class RelojFalso:
    def tick(self, fps=60):
        return 16

    def get_fps(self):
        return 60

    def get_time(self):
        return int(time.time() * 1000)


class _FinDemo(Exception):
    pass


def correr_pantalla(nombre, fn, max_frames=2):
    """Ejecuta una pantalla durante exactamente max_frames y devuelve los rects."""
    get_original = pygame.event.get
    clock_original = pygame.time.Clock
    pygame.time.Clock = RelojFalso
    estado = {"n": 0}

    _REGISTRO_FRAMES.clear()
    ui.limpiar_medicion()

    def get_eventos():
        estado["n"] += 1
        if estado["n"] > max_frames:
            raise _FinDemo()
        # Simular clicks/teclas para avanzar estados de hover si es necesario
        return []

    pygame.event.get = get_eventos
    try:
        resultado = fn()
        if asyncio.iscoroutine(resultado):
            asyncio.run(resultado)
    except _FinDemo:
        pass
    except Exception as exc:
        print(f"ERROR ejecutando {nombre}: {exc!r}")
    finally:
        pygame.event.get = get_original
        pygame.time.Clock = clock_original

    # Devolver una copia de los frames capturados
    return list(_REGISTRO_FRAMES)


def auditar_rects(nombre_pantalla, frames):
    problemas = []
    for f_idx, frame in enumerate(frames):
        # 1. Comprobar fuera de límites (a)
        for rect, rol, contenedora in frame:
            # Tolerancia de MARGEN_SEGURIDAD
            if (rect.left < -ui.MARGEN_SEGURIDAD or 
                rect.top < -ui.MARGEN_SEGURIDAD or 
                rect.right > ui.ANCHO + ui.MARGEN_SEGURIDAD or 
                rect.bottom > ui.ALTO + ui.MARGEN_SEGURIDAD):
                problemas.append(
                    f"[{nombre_pantalla}] Elemento {rol} {rect} se sale de la pantalla "
                    f"({ui.ANCHO}x{ui.ALTO}) en frame {f_idx}"
                )

            # 2. Comprobar desbordes de contenedor (b)
            if contenedora is not None:
                # Comprobar si rect se sale de contenedora (con margen)
                if (rect.left < contenedora.left - ui.MARGEN_SEGURIDAD or 
                    rect.top < contenedora.top - ui.MARGEN_SEGURIDAD or 
                    rect.right > contenedora.right + ui.MARGEN_SEGURIDAD or 
                    rect.bottom > contenedora.bottom + ui.MARGEN_SEGURIDAD):
                    problemas.append(
                        f"[{nombre_pantalla}] Texto {rect} desborda su contenedor {contenedora} "
                        f"en frame {f_idx}"
                    )

        # 3. Comprobar solapamiento de rects del mismo frame (c)
        # Solo comprobamos textos contra textos que no son el mismo y no son del mismo contenedor (ej. parrafos)
        for i, (r1, rol1, c1) in enumerate(frame):
            if rol1 != "texto":
                continue
            for j in range(i + 1, len(frame)):
                r2, rol2, c2 = frame[j]
                if rol2 != "texto":
                    continue
                # Si se solapan de verdad
                if r1.colliderect(r2):
                    # Si no comparten el mismo contenedor exacto (evitamos falsos positivos en parrafos envueltos)
                    if c1 is None or c1 != c2:
                        # Pequeña tolerancia: un overlap de 1-2 px puede ser aceptable por sombras o acentos
                        inter = r1.clip(r2)
                        if inter.width > 2 and inter.height > 2:
                            problemas.append(
                                f"[{nombre_pantalla}] Solapamiento de textos: {r1} y {r2} "
                                f"en frame {f_idx}"
                            )
    return problemas


def exceso_lineas(texto, tam, ancho, max_lineas, donde):
    from ui import envolver
    n = len(envolver(texto, tam, ancho))
    if n > max_lineas:
        return f"{donde}: {n} lineas (max {max_lineas}): {texto[:50]}..."
    return None


def desborda(texto, tam, ancho_max, donde):
    from ui import ancho_texto
    w = ancho_texto(texto, tam)
    if w > ancho_max:
        return f"{donde}: {w}px > {ancho_max}px: {texto[:50]}..."
    return None


def fuera_pantalla(rect, donde):
    x, y, w, h = rect
    if x < 0 or y < 0 or x + w > ui.ANCHO or y + h > ui.ALTO:
        return f"{donde}: rect {rect} fuera de {ui.ANCHO}x{ui.ALTO}"
    return None


def auditar():
    """Ejecuta la auditoria real cuadro a cuadro sobre todas las pantallas."""
    screen = pygame.display.get_surface()
    if screen is None:
        screen = pygame.display.set_mode((ui.ANCHO, ui.ALTO))
    estado_campana = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")

    pantallas_a_auditar = [
        ("12_nombre", lambda: pantallas.pedir_nombre(screen, RelojFalso(), "Bartolo")),
        ("12b_editar_mazo", lambda: pantallas._editar_mazo_run(
            screen, RelojFalso(), estado_campana)),
        ("13_portada", lambda: pantallas.portada(screen, RelojFalso())),
        ("13b_menu", lambda: pantallas.menu(screen, RelojFalso(), estado_campana)),
        ("14_elegir_faccion", lambda: pantallas.elegir_faccion(screen, RelojFalso())),
        ("15_mapa", lambda: pantallas.mapa_campana(screen, RelojFalso(), estado_campana)),
        ("16_elegir_rama", lambda: pantallas.elegir_rama(screen, RelojFalso(), estado_campana)),
        ("17_recompensa", lambda: pantallas.recompensa(screen, RelojFalso(), estado_campana, "fortaleza")),
        ("18_encuentro", lambda: pantallas.encuentro(screen, RelojFalso(), estado_campana, "ruinas")),
        ("19_coleccion", lambda: pantallas.coleccion(screen, RelojFalso(), estado_campana)),
        ("20_ajustes", lambda: pantallas.ajustes(screen, RelojFalso())),
        ("21_derrota", lambda: pantallas.derrota(screen, RelojFalso(), estado_campana)),
        ("22_draft", lambda: pantallas.draft(screen, RelojFalso(), estado_campana)),
        ("22b_mejorar", lambda: pantallas.elegir_carta_para_mejorar(screen, RelojFalso(), estado_campana)),
        ("22c_reemplazo", lambda: pantallas.draft_reemplazo(screen, RelojFalso(), estado_campana, mazos.HUMANOS[2])),
        ("22d_ficha_nodo", lambda: pantallas._ficha_nodo(screen, RelojFalso(), estado_campana, "fortaleza")),
        ("26_elegir_rapida", lambda: pantallas.elegir_faccion(screen, RelojFalso(), modo="rapida")),
        ("27_mini_mapa", lambda: pantallas.mapa_mini(screen, RelojFalso(), campana.nueva_mini_campana("elfo_nocturno"))),
        ("28_sobre", lambda: pantallas.revelar_sobre(screen, RelojFalso(), [mazos.HUMANOS[1]], [mazos.HUMANOS[0]])),
        ("29_tienda", lambda: pantallas.tienda(screen, RelojFalso(), estado_campana)),
        ("30_armar_mazo", lambda: pantallas.armar_mazo(screen, RelojFalso(), "humano")),
    ]

    todos = []
    for nombre, fn in pantallas_a_auditar:
        frames = correr_pantalla(nombre, fn)
        todos.extend(auditar_rects(nombre, frames))
    return todos


def main():
    pygame.init()
    audio.iniciar()
    screen = pygame.display.set_mode((ui.ANCHO, ui.ALTO))

    estado_campana = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")

    pantallas_a_auditar = [
        ("12_nombre", lambda: pantallas.pedir_nombre(screen, RelojFalso(), "Bartolo")),
        ("12b_editar_mazo", lambda: pantallas._editar_mazo_run(
            screen, RelojFalso(), estado_campana)),
        ("13_portada", lambda: pantallas.portada(screen, RelojFalso())),
        ("13b_menu", lambda: pantallas.menu(screen, RelojFalso(), estado_campana)),
        ("14_elegir_faccion", lambda: pantallas.elegir_faccion(screen, RelojFalso())),
        ("15_mapa", lambda: pantallas.mapa_campana(screen, RelojFalso(), estado_campana)),
        ("16_elegir_rama", lambda: pantallas.elegir_rama(screen, RelojFalso(), estado_campana)),
        ("17_recompensa", lambda: pantallas.recompensa(screen, RelojFalso(), estado_campana, "fortaleza")),
        ("18_encuentro", lambda: pantallas.encuentro(screen, RelojFalso(), estado_campana, "ruinas")),
        ("19_coleccion", lambda: pantallas.coleccion(screen, RelojFalso(), estado_campana)),
        ("20_ajustes", lambda: pantallas.ajustes(screen, RelojFalso())),
        ("21_derrota", lambda: pantallas.derrota(screen, RelojFalso(), estado_campana)),
        ("22_draft", lambda: pantallas.draft(screen, RelojFalso(), estado_campana)),
        ("22b_mejorar", lambda: pantallas.elegir_carta_para_mejorar(screen, RelojFalso(), estado_campana)),
        ("22c_reemplazo", lambda: pantallas.draft_reemplazo(screen, RelojFalso(), estado_campana, mazos.HUMANOS[2])),
        ("22d_ficha_nodo", lambda: pantallas._ficha_nodo(screen, RelojFalso(), estado_campana, "fortaleza")),
        ("26_elegir_rapida", lambda: pantallas.elegir_faccion(screen, RelojFalso(), modo="rapida")),
        ("27_mini_mapa", lambda: pantallas.mapa_mini(screen, RelojFalso(), campana.nueva_mini_campana("elfo_nocturno"))),
        ("28_sobre", lambda: pantallas.revelar_sobre(screen, RelojFalso(), [mazos.HUMANOS[1]], [mazos.HUMANOS[0]])),
        ("29_tienda", lambda: pantallas.tienda(screen, RelojFalso(), estado_campana)),
        ("30_armar_mazo", lambda: pantallas.armar_mazo(screen, RelojFalso(), "humano")),
    ]

    todos_los_problemas = []
    print("Iniciando auditoria visual real...")

    for nombre, fn in pantallas_a_auditar:
        frames = correr_pantalla(nombre, fn)
        problemas = auditar_rects(nombre, frames)
        if problemas:
            todos_los_problemas.extend(problemas)
            print(f"  {nombre}: {len(problemas)} problemas detectados.")
        else:
            print(f"  {nombre}: OK.")

    if todos_los_problemas:
        print(f"\nAUDITORIA VISUAL: {len(todos_los_problemas)} problemas reales de diseño:")
        for p in todos_los_problemas:
            print(f"  - {p}")
        return 1

    print("\nAuditoria visual real: ¡sin desbordes ni elementos fuera de lugar!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
