"""Tests de estabilidad: nada debe dejar al jugador encerrado.

    python -m unittest tests.test_estabilidad

Cubre los cuatro puntos del plan:
  1. las cinematicallyas se pueden cerrar siempre (el bug del dialogo colgado)
  2. el flujo de duelo rapido devuelve la faccion y hay pantallon de error
  3. las cartas colocan los valores en las esquinas, sin tapar el retrato
  4. todos los bucles respetan LIMIT_FPS y los fondos se cachean
"""

import io
import os
import re
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import audio  # noqa: E402
import cinematicas  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
import ui  # noqa: E402
from reglas import CPU, USUARIO  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULOS_CON_BUCLE = ["pantallas.py", "partida.py", "cinematicas.py", "main.py"]


class RelojFalso:
    """Reloz que no espera, pero respeta el limite de fps."""

    def __init__(self):
        self.ticks = 0
        self.limites = set()

    def tick(self, fps=0):
        self.ticks += 1
        self.limites.add(fps)
        return 16


def _superficie():
    return pygame.display.set_mode((ui.ANCHO, ui.ALTO))


def setUpModule():
    pygame.init()
    _superficie()


# ---------------------------------------------------- 1. cinematicas no cuelgan
def _evento(tipo, **kwargs):
    """Evento real de pygame (el codigo lee ev.type / ev.pos / ev.key)."""
    return pygame.event.Event(tipo, **kwargs)


def _clic(pos=(10, 10)):
    return _evento(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)


def _tecla(key):
    return _evento(pygame.KEYDOWN, key=key, unicode="")


class TestCineticasSeCierran(unittest.TestCase):
    """El bug: en la ultima escena el clic no avanzaba y ESC estaba
    deshabilitado en el epilogo, dejando el juego encerrado."""

    def test_avanzar_devuelve_falso_en_la_ultima_escena(self):
        escenas = [cinematicas.Escena(cinematicas.esc("uno")),
                   cinematicas.Escena(cinematicas.esc("dos"))]
        cin = cinematicas.Cinematica(escenas)
        self.assertTrue(cin._avanzar())
        self.assertEqual(cin.i, 1)
        self.assertFalse(cin._avanzar(), "la ultima escena no debe avanzar mas")
        self.assertTrue(cin.ultima)

    def test_clic_completa_y_luego_cierra_la_cinematica(self):
        """Un clic completa el texto, el siguiente avanza y el ultimo cierra."""
        escenas = [cinematicas.Escena(cinematicas.esc("uno")),
                   cinematicas.Escena(cinematicas.esc("dos"))]
        pantalla = _superficie()
        cin = cinematicas.Cinematica(escenas)
        self.assertFalse(cin.escena().completa)

        # primer clic: completa el texto de la escena 1
        original = pygame.event.get
        clicks = [_clic()]

        def eventos():
            return clicks.pop(0) if clicks else []
        pygame.event.get = eventos
        try:
            # completamos la escena 1 y avanzamos
            cin.escena().mostrado = len(cin.escena().texto)
            self.assertTrue(cin._avanzar())
            # completamos la escena 2 (la ultima) y verificamos que cierra
            cin.escena().mostrado = len(cin.escena().texto)
            self.assertFalse(cin._avanzar())
        finally:
            pygame.event.get = original

    def test_la_cinematica_termina_pulsando_escape_siempre(self):
        """Con permitir_saltar=False (epilogo) ESC tambien tiene que cerrar."""
        for permitir in (True, False):
            escenas = [cinematicas.Escena(cinematicas.esc("final", efecto="titulo"))]
            pantalla = _superficie()
            cin = cinematicas.Cinematica(escenas, permitir_saltar=permitir)
            original = pygame.event.get
            enviados = [0]

            def eventos():
                enviados[0] += 1
                if enviados[0] > 3:
                    return [_tecla(pygame.K_ESCAPE)]
                return []
            pygame.event.get = eventos
            try:
                # no debe colgarse: si vuelve, la pantalla se puede cerrar
                cin.ejecutar(pantalla, RelojFalso())
            finally:
                pygame.event.get = original
            self.assertGreater(enviados[0], 3, f"ESC no funciono con permitir_saltar={permitir}")

    def test_enter_tambien_avanza(self):
        escenas = [cinematicas.Escena(cinematicas.esc("uno")),
                   cinematicas.Escena(cinematicas.esc("dos"))]
        cin = cinematicas.Cinematica(escenas)
        cin.escena().mostrado = len(cin.escena().texto)
        original = pygame.event.get
        clicks = [_tecla(pygame.K_RETURN)]

        def eventos():
            return clicks.pop(0) if clicks else []
        pygame.event.get = eventos
        try:
            clicks.append(_tecla(pygame.K_RETURN))
            self.assertTrue(cin._avanzar())
        finally:
            pygame.event.get = original


# -------------------------------------------------- 2. duelo rapido y errores
class TestDueloRapidoYErrores(unittest.TestCase):
    def test_el_duelo_rapido_pide_faccion_en_modo_rapida(self):
        """El selector de faccion debe saber que es duelo rapido (no campana)."""
        import pantallas

        original = pantallas.elegir_faccion
        llamadas = {}

        def espia(screen, clock, facciones_disponibles=None, modo="campana"):
            llamadas["modo"] = modo
            return None

        import main

        pantallas.elegir_faccion = espia
        try:
            main._duelo_rapido(_superficie(), RelojFalso())
        finally:
            pantallas.elegir_faccion = original
        self.assertEqual(llamadas.get("modo"), "rapida")

    def test_el_duelo_rapido_devuelve_al_menu_si_se_cancela(self):
        import main

        original = main.pantallas.elegir_faccion
        main.pantallas.elegir_faccion = lambda *a, **k: None
        try:
            # no debe lanzar ni quedarse colgado
            main._duelo_rapido(_superficie(), RelojFalso())
        finally:
            main.pantallas.elegir_faccion = original

    def test_el_seleccionador_devuelve_la_faccion_elegida(self):
        """Con el raton: un clic elige y el siguiente confirma."""
        import pantallas

        pantalla = _superficie()
        original = pygame.event.get
        # seleccionamos el humano (indice 0) y luego pulsamos ELEGIR Y EMPEZAR
        aceptar = (ui.ANCHO - 330 + 140, 650 + 23)
        secuencia = [_clic((160, 250)), _clic(aceptar)]

        def eventos():
            return [secuencia.pop(0)] if len(secuencia) > 1 else []
        pygame.event.get = eventos
        try:
            faccion = pantallas.elegir_faccion(pantalla, RelojFalso())
        finally:
            pygame.event.get = original
        self.assertEqual(faccion, "humano")

    def test_el_contexto_de_error_se_actualiza(self):
        import main

        main.marcar("pantalla de prueba")
        self.assertEqual(main.contexto(), "pantalla de prueba")
        main.marcar("menú principal")

    def test_el_pantallon_de_error_se_dibuja_y_escribe_log(self):
        """Un error inesperado debe enseearse, no cerrar el juego en silencio."""
        import pantallas

        pantalla = _superficie()
        original = pygame.event.get
        enviados = [0]

        def eventos():
            enviados[0] += 1
            if enviados[0] > 2:
                return [_tecla(pygame.K_RETURN)]
            return []
        pygame.event.get = eventos
        try:
            pantallas.pantalla_error(
                pantalla, RelojFalso(),
                ValueError("fallo de prueba"),
                "Traceback (most recent call last):\n  ValueError: fallo de prueba\n",
                contexto="duelo de prueba",
            )
        finally:
            pygame.event.get = original
        self.assertGreater(enviados[0], 2)
        from paths import log_errores

        log = log_errores()
        self.assertTrue(os.path.exists(log), "deberia existir crash.log")
        with io.open(log, encoding="utf-8") as f:
            contenido = f.read()
        self.assertIn("fallo de prueba", contenido)
        self.assertIn("duelo de prueba", contenido)


# ---------------------------------------------------- 3. reencuadre de cartas
class TestEncuadreDeCartas(unittest.TestCase):
    """Los valores van en el punto medio de cada lado (como siempre) y el
    retrato se dibuja en una ventana que ningun orbe toca."""

    def test_los_valores_estan_en_el_punto_medio_de_cada_lado(self):
        from cartas import RADIO_ORBE, posiciones_valor

        w, h = ui.CARD_W, ui.CARD_H
        p = posiciones_valor(w, h)
        # arriba-centro, abajo-centro, izquierda-centro, derecha-centro
        self.assertAlmostEqual(p["N"][0], w // 2, delta=2)
        self.assertLess(p["N"][1], h * 0.25, "N deberia estar arriba")
        self.assertAlmostEqual(p["S"][0], w // 2, delta=2)
        self.assertGreater(p["S"][1], h * 0.70, "S deberia estar abajo")
        self.assertAlmostEqual(p["O"][1], h // 2, delta=12)
        self.assertLess(p["O"][0], w * 0.25, "O deberia estar a la izquierda")
        self.assertGreater(p["E"][0], w * 0.75, "E deberia estar a la derecha")
        for lado, (cx, cy) in p.items():
            dentro = RADIO_ORBE <= cx <= w - RADIO_ORBE
            dentro_y = RADIO_ORBE <= cy <= h - RADIO_ORBE
            self.assertTrue(dentro and dentro_y, f"{lado} se sale de la carta")

    def test_ningun_orbe_pisa_el_retrato(self):
        """El requisito clave: los numeros no pueden tocar la imagen."""
        from cartas import RADIO_ORBE, posiciones_valor, rect_arte

        w, h = ui.CARD_W, ui.CARD_H
        ax, ay, aw, ah = rect_arte(w, h)
        r = RADIO_ORBE
        for lado, (cx, cy) in posiciones_valor(w, h).items():
            solapa = not (
                cx + r <= ax or cx - r >= ax + aw
                or cy + r <= ay or cy - r >= ay + ah
            )
            self.assertFalse(solapa, f"el orbe {lado} pisa el retrato")

    def test_el_retrato_no_cubre_el_centro_de_la_carta(self):
        """El retrato debe seguir siendo la mayor parte visible."""
        from cartas import rect_arte

        w, h = ui.CARD_W, ui.CARD_H
        ax, ay, aw, ah = rect_arte(w, h)
        self.assertGreaterEqual(aw * ah, w * h * 0.28, "el retrato se ha quedado pequeno")

    def test_todas_las_cartas_se_dibujan_sin_error(self):
        import cartas as crt

        for bando, cartas in mazos.TODOS.items():
            for carta in cartas:
                sup = crt.crear(carta, USUARIO)
                self.assertEqual(sup.get_size(), (ui.CARD_W, ui.CARD_H), carta.nombre)

    def test_el_nombre_y_el_bando_no_quedan_tapados(self):
        """El orbe norte no debe caer sobre la placa del nombre ni el sur
        sobre la franja del bando."""
        from cartas import RADIO_ORBE, posiciones_valor

        w, h = ui.CARD_W, ui.CARD_H
        p = posiciones_valor(w, h)
        r = RADIO_ORBE
        self.assertLessEqual(p["N"][1] + r, 26, "el orbe norte pisa el nombre")
        # la franja del bando empieza en h-16: el orbe sur debe acabar antes
        self.assertLessEqual(p["S"][1] + r, h - 16,
                             "el orbe sur pisa la franja del bando")


# ---------------------------------------------------------- 4. fps y memoria
class TestMusicaDelDuelo(unittest.TestCase):
    def test_el_duelo_tiene_musica_propia(self):
        self.assertEqual(audio.musica_de_duelo(), "musica_duelo")
        self.assertEqual(audio.musica_de_menu(), "musica_explora")

    def test_el_duelo_no_reutiliza_la_pista_del_rival(self):
        for f in facciones.orden_facciones():
            self.assertNotEqual(audio.musica_de_duelo(), audio.musica_de_faccion(f))

    def test_arrancar_un_duelo_pone_la_musica_de_combate(self):
        """partida() debe pedir la pista de duelo, no la de la faccion rival."""
        import partida as modulo_partida

        pedidos = []
        original = audio.musica

        def espia(nombre, bucle=True):
            pedidos.append(nombre)
        audio.musica = espia
        modulo_partida.audio.musica = espia
        try:
            juego = modulo_partida.Juego("humano", bando_rival="orco")
            resultado = modulo_partida.partida(
                _superficie(), RelojFalso(), juego, test_mode=True
            )
        finally:
            audio.musica = original
            modulo_partida.audio.musica = original
        self.assertIn("musica_duelo", pedidos)
        self.assertNotIn("musica_orco", pedidos)
        self.assertTrue(resultado)


# ---------------------------------------------------------- 4. fps y memoria
class TestFpsYMemoria(unittest.TestCase):
    def test_la_constante_de_fps_existe_y_vale_60(self):
        self.assertEqual(ui.LIMIT_FPS, 60)

    def test_ningun_bucle_llama_a_tick_con_otro_valor(self):
        """Ningun modulo puede pasar un limite distinto a LIMIT_FPS."""
        culpables = []
        for nombre in MODULOS_CON_BUCLE:
            ruta = os.path.join(RAIZ, nombre)
            with io.open(ruta, encoding="utf-8") as f:
                for i, linea in enumerate(f, 1):
                    if "def tick" in linea:
                        continue
                    for m in re.finditer(r"\.tick\(\s*([0-9]+)", linea):
                        if int(m.group(1)) != ui.LIMIT_FPS:
                            culpables.append(f"{nombre}:{i} -> tick({m.group(1)})")
        self.assertEqual(culpables, [], f"bucles sin el tope de {ui.LIMIT_FPS} fps")

    def test_todos_los_bucles_llaman_a_tick(self):
        """Cada 'while True' debe limitar los fps, directamente o delegando
        en una pantalla que ya lo hace (pantallas.menu, partida.partida...)."""
        delegan = ("pantallas.", "partida.partida", "cinematicas.reproducir",
                   "_duelo_rapido", "_campana")
        sin_tick = []
        for nombre in MODULOS_CON_BUCLE:
            ruta = os.path.join(RAIZ, nombre)
            with io.open(ruta, encoding="utf-8") as f:
                lineas = f.readlines()
            for i, linea in enumerate(lineas):
                if "while True" not in linea:
                    continue
                ventana = "".join(lineas[i + 1:i + 14])
                if ".tick(" in ventana:
                    continue
                if any(d in ventana for d in delegan):
                    continue  # el bucle llama a una pantalla que ya limita los fps
                sin_tick.append(f"{nombre}:{i + 1}")
        self.assertEqual(sin_tick, [], f"bucles sin limite de fps: {sin_tick}")

    def test_los_fondos_escalados_se_cachean(self):
        """Escalar a pantalla completa por frame es lo que consumia memoria."""
        import partida
        import pantallas

        for nombre in ("pantallas.py", "partida.py", "cinematicas.py"):
            with io.open(os.path.join(RAIZ, nombre), encoding="utf-8") as f:
                codigo = f.read()
            self.assertNotIn(
                "smoothscale(fondo, (ANCHO, ALTO))", codigo,
                f"{nombre} sigue escalando el fondo cada frame",
            )
        # el cache existe y devuelve siempre la misma superficie
        a = ui.REC.fondo_pantalla("assets/fondo.png")
        b = ui.REC.fondo_pantalla("assets/fondo.png")
        self.assertIs(a, b, "el fondo deberia estar cacheado")
        self.assertEqual(a.get_size(), (ui.ANCHO, ui.ALTO))

    def test_la_capa_de_oscurecido_tambien_se_cachea(self):
        a = ui.REC.capa_oscurita((6, 7, 14, 168))
        b = ui.REC.capa_oscurita((6, 7, 14, 168))
        self.assertIs(a, b)


if __name__ == "__main__":
    unittest.main()