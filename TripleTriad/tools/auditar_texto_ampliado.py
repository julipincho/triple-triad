"""La auditoria visual con el TEXTO AMPLIADO (modo lectura).

`tests/auditoria_visual.py` mide los rects de cada pantalla a tamano normal. El
criterio de aceptacion de G7 pide ademas "texto y botones legibles/sin recorte
... con texto ampliado", y ese modo no se comprobaba: el unico sitio donde se
vio un problema fue mirando una captura a ojo (el diario se salia del panel).

Aqui se ejecuta la MISMA auditoria con la escala de tipografia al 125%, que es
lo que hace el jugador cuando activa TEXTO GRANDE en Ajustes. Si algo se sale
de pantalla o se solapa, sale aqui.

    python tools/auditar_texto_ampliado.py
"""

import os
import re
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tests"))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_tmp = tempfile.TemporaryDirectory(prefix="tt_auditoria_texto_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

import pygame  # noqa: E402

import opciones  # noqa: E402
import ui  # noqa: E402

import auditoria_visual as AV  # noqa: E402

#: Escala por defecto de la auditoria. El ajuste TEXTO GRANDE usa 1.25, pero
#: `ui.fijar_escala_texto` admite hasta 1.6, y ese techo tambien tiene que caber:
#:   python tools/auditar_texto_ampliado.py 1.6
ESCALA = 1.25
ESCALAS_AUDITADAS = (1.25, 1.6)


def _auditar_una(AV, escala):
    """Audita todas las pantallas con la tipografia a `escala`."""
    global pantalla
    pantalla = pygame.display.get_surface()
    opciones.fijar("texto_grande", True)
    real = ui.fijar_escala_texto(escala)
    print(f"Auditoria visual con TEXTO AMPLIADO (escala {real})")
    print()

    import campana
    import mazos

    estado_campana = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")

    pantallas = [
        ("12_nombre", lambda: AV.pantallas.pedir_nombre(pantalla, AV.RelojFalso(), "Bartolo")),
        ("12b_editar_mazo", lambda: AV.pantallas._editar_mazo_run(pantalla, AV.RelojFalso(), estado_campana)),
        ("13_portada", lambda: AV.pantallas.portada(pantalla, AV.RelojFalso())),
        ("13b_menu", lambda: AV.pantallas.menu(pantalla, AV.RelojFalso(), estado_campana)),
        ("14_elegir_faccion", lambda: AV.pantallas.elegir_faccion(pantalla, AV.RelojFalso())),
        ("14b_elegir_faccion_rapida", lambda: AV.pantallas.elegir_faccion(
            pantalla, AV.RelojFalso(), modo="rapida")),
        ("15_mapa", lambda: AV.pantallas.mapa_campana(pantalla, AV.RelojFalso(), estado_campana)),
        ("16_elegir_rama", lambda: AV.pantallas.elegir_rama(pantalla, AV.RelojFalso(), estado_campana)),
        ("17_recompensa", lambda: AV.pantallas.recompensa(pantalla, AV.RelojFalso(), estado_campana, "fortaleza")),
        ("18_encuentro", lambda: AV.pantallas.encuentro(pantalla, AV.RelojFalso(), estado_campana, "ruinas")),
        ("19_coleccion", lambda: AV.pantallas.coleccion(pantalla, AV.RelojFalso(), estado_campana)),
        ("20_ajustes", lambda: AV.pantallas.ajustes(pantalla, AV.RelojFalso())),
        ("21_derrota", lambda: AV.pantallas.derrota(pantalla, AV.RelojFalso(), estado_campana)),
        ("22_draft", lambda: AV.pantallas.draft(pantalla, AV.RelojFalso(), estado_campana)),
        ("22b_mejorar", lambda: AV.pantallas.elegir_carta_para_mejorar(pantalla, AV.RelojFalso(), estado_campana)),
        ("22c_reemplazo", lambda: AV.pantallas.draft_reemplazo(pantalla, AV.RelojFalso(), estado_campana, mazos.HUMANOS[2])),
        ("22d_ficha_nodo", lambda: AV.pantallas._ficha_nodo(pantalla, AV.RelojFalso(), estado_campana, "fortaleza")),
        ("27_mini_mapa", lambda: AV.pantallas.mapa_mini(pantalla, AV.RelojFalso(), campana.nueva_mini_campana("elfo_nocturno"))),
        ("28_sobre", lambda: AV.pantallas.revelar_sobre(pantalla, AV.RelojFalso(), [mazos.HUMANOS[1]], [mazos.HUMANOS[0]])),
        ("29_tienda", lambda: AV.pantallas.tienda(pantalla, AV.RelojFalso(), estado_campana)),
        ("30_armar_mazo", lambda: AV.pantallas.armar_mazo(pantalla, AV.RelojFalso(), "humano")),
        ("31_diario", lambda: AV.pantallas.diario_dialogos(pantalla, AV.RelojFalso(), estado_campana)),
        ("32_decision", lambda: AV.pantallas.decision_narrativa(
            pantalla, AV.RelojFalso(), estado_campana,
            __import__("narrativa").decision_de("senda"))),
    ]

    # La ficha lateral de `elegir_faccion` cambia con la faccion elegida: el
    # lema, el arco y el numero de habilidades son distintos en cada una, asi
    # que auditar solo la primera no cubre nada. Se pasa una faccion por vez
    # (`facciones_disponibles`) para que la pantalla arranque en esa.
    import facciones as _fac
    for _f in _fac.orden_facciones():
        pantallas.append((
            f"14c_ficha_{_f}",
            (lambda ff: lambda: AV.pantallas.elegir_faccion(
                pantalla, AV.RelojFalso(), facciones_disponibles=[ff]))(_f),
        ))

    # El DUELO es la pantalla principal del juego y no estaba en la lista. Se
    # montan tres estados distintos porque cada uno dibuja texto distinto:
    # tablero vacio, duelista con rival ya en la casilla de al lado y turno de
    # la CPU (banner de turno, mensaje y animacion de la IA).
    import partida as _partida

    def _juego_tablaso_vacio():
        return _partida.Juego("humano", "orco")

    def _juego_con_captura():
        j = _partida.Juego("humano", "orco")
        j.turno_cpu = True
        j.seleccionada = j.mano_u[0]
        j.mensaje = "Muro bloquea el lado norte: no se puede capturar"
        return j

    def _juego_turno_cpu():
        j = _partida.Juego("humano", "orco")
        j.turno_cpu = False
        j.cpu_en_curso = True
        j.mensaje = "Turno de Orcos. Piensa tu siguiente jugada."
        return j

    def _pantalla_comparar(est):
        """Compara el reemplazo con los mismos tipos que le pasa el editor."""
        import cartas as _crt
        por_nombre = {c.nombre: c for c in mazos.TODOS["elfo"]}
        nombres = [d.get("nombre") for d in est["cartas"]]
        por_nombre.update({c.nombre: c for lista in mazos.TODOS.values()
                           for c in lista})
        bases = {n: {"nombre": n, "n": 5, "s": 5, "e": 5, "o": 5}
                 for n in por_nombre}
        nueva = por_nombre["Sol Naciente"].nombre if "Sol Naciente" in por_nombre \
            else sorted(por_nombre)[0]
        return lambda: AV.pantallas.comparar_reemplazo(
            pantalla, AV.RelojFalso(), nueva, nombres, por_nombre, bases,
            list(por_nombre))

    pantallas.extend([
        ("40_duelo_inicio", lambda: _partida.partida(
            pantalla, AV.RelojFalso(), _juego_con_captura())),
        ("41_duelo_turno_cpu", lambda: _partida.partida(
            pantalla, AV.RelojFalso(), _juego_turno_cpu())),
        ("42_ayuda", lambda: AV.pantallas._pantalla_ayuda(pantalla, AV.RelojFalso())),
        ("43_cartel", lambda: AV.pantallas.cartel(
            pantalla, AV.RelojFalso(), "SIN RECURSOS",
            "No se pudo cargar el audio. El juego sigue sin sonido.")),
        ("44_error", lambda: AV.pantallas.pantalla_error(
            pantalla, AV.RelojFalso(), RuntimeError("fallo de prueba"),
            "Traceback de prueba", "arranque")),
        ("45_epilogo", lambda: AV.pantallas.epilogo(pantalla, AV.RelojFalso(), estado_campana)),
        ("46_comparar_reemplazo", _pantalla_comparar(estado_campana)),
    ])

    problemas_total = []
    for nombre, fn in pantallas:
        frames = AV.correr_pantalla(nombre, fn)
        if AV.ERRORES:
            # Una pantalla que peta no dibuja rects y `auditar_rects` no ve
            # nada: sin este aviso, un fallo grave se camuflaba como "OK".
            problemas_total.extend(f"{n}: ERROR al ejecutar {e}" for n, e in AV.ERRORES)
            print(f"  {nombre}: ERROR AL DIBUJAR (no se puede auditar)")
            continue
        if not frames:
            problemas_total.append(f"{nombre}: no se capturo ningun frame")
            print(f"  {nombre}: SIN FRAMES")
            continue
        problemas = AV.auditar_rects(nombre, frames)
        if problemas:
            problemas_total.extend(problemas)
            print(f"  {nombre}: {len(problemas)} problemas")
            for p in problemas[:4]:
                print(f"      - {p}")
                # AV.textos_de_frame lleva la cadena de cada texto del frame,
                # asi que un solapamiento se nombra en vez de dejar dos rects
                # a interpretar.
                m = re.search(r"en frame (\d+)", p)
                idx = int(m.group(1)) if m else 0
                for r in re.findall(r"<rect\((-?\d+), (-?\d+), (\d+), (\d+)\)>", p):
                    rect = pygame.Rect(*(int(v) for v in r))
                    textos = [c for c, rc in AV.textos_de_frame(idx) if rc == rect]
                    if textos:
                        print(f"          {textos[-1]!r}")
        else:
            print(f"  {nombre}: OK")

    print()
    return problemas_total


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ui.ANCHO, ui.ALTO))
    escalas = [float(a) for a in sys.argv[1:]] or list(ESCALAS_AUDITADAS)
    todos = []
    for e in escalas:
        todos.extend(_auditar_una(AV, e))
    ui.fijar_escala_texto(1.0)
    print()
    if todos:
        print(f"AUDITORIA CON TEXTO AMPLIADO: {len(todos)} problemas")
        return 1
    print("Auditoria con texto ampliado: sin desbordes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())