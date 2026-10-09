"""Tests de estabilidad: nada debe dejar al jugador encerrado.

    python -m unittest tests.test_estabilidad

Cubre los puntos del plan:
  1. las cinematicallyas se pueden cerrar siempre (el bug del dialogo colgado)
  2. el flujo de duelo rapido devuelve la faccion y hay pantallon de error
  3. las cartas colocan los valores en las esquinas, sin tapar el retrato
  4. los tooltips se encolan y se pintan al final del frame, nunca tapados
  5. el duelo tiene musica propia
  6. todos los bucles respetan LIMIT_FPS y los fondos se cachean
"""

import asyncio
import io
import os
import re
import sys
import tempfile
import time
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# El directorio de tests tambien: `discover` lo anade, pero al lanzar un solo
# modulo (`python -m unittest tests.test_estabilidad`) no, y entonces los
# helpers compartidos como `opciones_test` no se encuentran.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import audio  # noqa: E402
import cinematicas  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
import ui  # noqa: E402
from reglas import CPU, USUARIO  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULOS_CON_BUCLE = ["pantallas.py", "partida.py", "cinematicas.py", "main.py", "tutorial.py"]


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
        """Con permitir_saltar=False (epilogo) ESC tambien tiene que cerrar.

        Necesita las opciones POR DEFECTO: si el desarrollador tiene "SALTAR
        CINE" activado en su `opciones.json`, la cinematica termina antes de leer
        el ESC y este test falla sin que el codigo tenga nada que ver. Por eso
        se envuelve en `sin_opciones()`.
        """
        import opciones_test

        with opciones_test.sin_opciones():
            for permitir in (True, False):
                escenas = [cinematicas.Escena(
                    cinematicas.esc("final", efecto="titulo"))]
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
                    asyncio.run(cin.ejecutar(pantalla, RelojFalso()))
                finally:
                    pygame.event.get = original
                self.assertGreater(
                    enviados[0], 3,
                    f"ESC no funciono con permitir_saltar={permitir}")

    def test_saltar_cine_evita_leer_eventos(self):
        """Con la opcion a SI, la secuencia se cierra sin molestar al jugador."""
        import opciones_test

        escenas = [cinematicas.Escena(cinematicas.esc("una")),
                   cinematicas.Escena(cinematicas.esc("dos"))]
        with opciones_test.sin_opciones(saltar_cinematica=True):
            original = pygame.event.get
            leidos = [0]

            def eventos():
                leidos[0] += 1
                return []
            pygame.event.get = eventos
            try:
                asyncio.run(cinematicas.Cinematica(escenas).ejecutar(
                    _superficie(), RelojFalso()))
            finally:
                pygame.event.get = original
            self.assertEqual(leidos[0], 0,
                             "con SALTAR CINE no deberia leer eventos ni uno")

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

        async def espia(screen, clock, facciones_disponibles=None, modo="campana"):
            llamadas["modo"] = modo
            return None

        import main

        pantallas.elegir_faccion = espia
        try:
            asyncio.run(main._duelo_rapido(_superficie(), RelojFalso()))
        finally:
            pantallas.elegir_faccion = original
        self.assertEqual(llamadas.get("modo"), "rapida")

    def test_el_duelo_rapido_devuelve_al_menu_si_se_cancela(self):
        import main

        original = main.pantallas.elegir_faccion

        async def cancelar(*args, **kw):
            return None

        main.pantallas.elegir_faccion = cancelar
        try:
            # no debe lanzar ni quedarse colgado
            asyncio.run(main._duelo_rapido(_superficie(), RelojFalso()))
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
            faccion = asyncio.run(pantallas.elegir_faccion(pantalla, RelojFalso()))
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
            asyncio.run(
                pantallas.pantalla_error(
                    pantalla, RelojFalso(),
                    ValueError("fallo de prueba"),
                    "Traceback (most recent call last):\n  ValueError: fallo de prueba\n",
                    contexto="duelo de prueba",
                )
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


# ------------------------------------------------ 4. tooltips al final del frame
class TestTooltipsSePintanAlFinal(unittest.TestCase):
    """El bug: tooltip() pintaba en el momento y las cartas siguientes lo
    tapaban. Ahora solo encola y dibujar_tooltips() lo pinta al final."""

    def setUp(self):
        ui._PENDIENTES.clear()

    def tearDown(self):
        ui._PENDIENTES.clear()

    def test_tooltip_no_dibuja_al_instantaneo_solo_encola(self):
        pantalla = _superficie()
        pantalla.fill((0, 0, 0))
        antes = pygame.image.tostring(pantalla, "RGB")

        ui.tooltip(pantalla, "Golpe furiouso\nN: 5   S: 3   E: 6   O: 2",
                   (400, 400), ancho=300, arriba=True)
        ui.tooltip(pantalla, "Segunda ficha\ncon dos lineas", (700, 300),
                   ancho=300, arriba=True)

        self.assertEqual(len(ui._PENDIENTES), 2, "tooltip() debe encolar, no pintar")
        despues = pygame.image.tostring(pantalla, "RGB")
        self.assertEqual(antes, despues,
                         "tooltip() toco la pantalla: se sigue pintando al instante")

    def test_dibujar_tooltips_pinta_y_vacia_la_cola(self):
        pantalla = _superficie()
        pantalla.fill((0, 0, 0))
        antes = pygame.image.tostring(pantalla, "RGB")
        ui.tooltip(pantalla, "Se encola y se pinta al final", (500, 500),
                   ancho=300, arriba=True)
        self.assertEqual(len(ui._PENDIENTES), 1)
        self.assertEqual(antes, pygame.image.tostring(pantalla, "RGB"))

        ui.dibujar_tooltips(pantalla)

        self.assertEqual(ui._PENDIENTES, [], "dibujar_tooltips() debe vaciar la cola")
        self.assertNotEqual(antes, pygame.image.tostring(pantalla, "RGB"),
                            "no se pinto nada en la pantalla")

    def test_el_tooltip_siempre_cae_dentro_de_la_pantalla(self):
        """Ni en las esquinas ni pegado al borde puede salirse."""
        ancho, tam = 300, 8
        alto = 6 * (tam + 9) + 16
        for px in (0, 10, 400, ui.ANCHO - 10, ui.ANCHO - 1):
            for py in (0, 10, 400, ui.ALTO - 10, ui.ALTO - 1):
                for lado in ("auto", "izq", "der"):
                    for arriba in (False, True):
                        x, y = ui._sitiar_tooltip((px, py), ancho, alto, lado, arriba)
                        self.assertGreaterEqual(x, 8, f"se sale por la izquierda en {px},{py}")
                        self.assertGreaterEqual(y, 8, f"se sale por arriba en {px},{py}")
                        self.assertLessEqual(x + ancho, ui.ANCHO - 8,
                                             f"se sale por la derecha en {px},{py}")
                        self.assertLessEqual(y + alto, ui.ALTO - 8,
                                             f"se sale por abajo en {px},{py}")

    def test_un_tooltip_alto_tambien_cabe_en_pantalla(self):
        """Con muchas lineas el alto crece: aun asi no puede salirse."""
        lineas = 30
        alto = lineas * (8 + 9) + 16
        for py in (0, 20, ui.ALTO - 1):
            x, y = ui._sitiar_tooltip((30, py), 300, alto, "der", False)
            self.assertGreaterEqual(y, 8)
            self.assertLessEqual(y + alto, ui.ALTO - 8)

    def test_todo_modulo_que_encola_tiene_que_pintar(self):
        """Si un modulo llama a tooltip() debe llamar tambien a
        dibujar_tooltips(): si no, la cola crece frame a frame y el tooltip
        aparece tarde o en otra pantalla."""
        for nombre in ("pantallas.py", "partida.py", "ui.py", "cartas.py",
                       "cinematicas.py", "main.py"):
            with io.open(os.path.join(RAIZ, nombre), encoding="utf-8") as f:
                codigo = f.read()
            if "tooltip(" not in codigo or nombre == "ui.py":
                continue  # ui.py es quien define y pinta
            self.assertIn("dibujar_tooltips(", codigo,
                          f"{nombre} encola tooltips pero nunca los pinta")

    def test_el_duelo_pinta_el_tooltip_al_final_del_frame(self):
        """Con el raton sobre una carta de la mano, el tooltip se encola
        durante _dibujar_mano y se pinta en dibujar(), sin quedar colgado."""
        import partida as modulo_partida

        pantalla = _superficie()
        juego = modulo_partida.Juego("humano", bando_rival="orco")
        juego.t_entrada = 0
        raton = ui.mano_rect(0, len(juego.cartas_en_mano())).center

        pintadas = []
        original_raton = pygame.mouse.get_pos
        original_pintar = modulo_partida.dibujar_tooltips
        pygame.mouse.get_pos = lambda: raton
        modulo_partida.dibujar_tooltips = lambda sup: (
            pintadas.append(sup), original_pintar(sup))[1]
        try:
            self.assertFalse(juego.fin)
            juego.dibujar(pantalla)
        finally:
            pygame.mouse.get_pos = original_raton
            modulo_partida.dibujar_tooltips = original_pintar

        self.assertTrue(pintadas, "el duelo no llamo a dibujar_tooltips()")
        self.assertEqual(ui._PENDIENTES, [],
                         "quedo un tooltip sin pintar tras dibujar el frame")


# --------------------------------- 4c. el duelo terminado siempre se continua
class TestContinuarTrasElDuelo(unittest.TestCase):
    """El bug: Resultado.__bool__ devuelve `victoria`, asi que al perder el
    duelo `if resultado:` era False y el bucle no se rompia. El jugador se
    quedaba en el cartel de DERROTA y el clic no hacia nada."""

    def _llenar(self, juego, dueno):
        from reglas import Carta

        for i in range(3):
            for j in range(3):
                carta = Carta(f"C{i}{j}", 9, 9, 9, 9,
                              bando="humano" if dueno == USUARIO else "orco")
                carta.dueno = dueno
                juego.board[i][j] = carta
        juego.comprobar_fin()

    def _clic_y_salir(self, preparar, tecla=False, intentos=120):
        """Devuelve el Resultado; falla si el bucle no sale."""
        import partida as modulo_partida

        juego = modulo_partida.Juego("humano", bando_rival="orco")
        preparar(juego)
        self.assertTrue(juego.fin, "el duelo deberia haber terminado")
        # fuera del umbral de now_clickable para no pelear con el retardo
        juego.tiempo_fin = time.time() - 5

        tipo = (pygame.KEYDOWN if tecla else pygame.MOUSEBUTTONDOWN)
        extra = {"key": pygame.K_RETURN} if tecla else {"button": 1, "pos": (640, 400)}
        original = pygame.event.get
        estado = {"n": 0, "enviados": 0}

        class _Colgado(Exception):
            pass

        def eventos():
            estado["n"] += 1
            # hay que cortar: si el bucle no sale, el test se quedaria colgado
            # en vez de fallar (que es justo lo que le pasaba al jugador)
            if estado["n"] > intentos:
                raise _Colgado("el bucle no sale con el clic repetido")
            # el jugador insiste: cada 5 frames, como en el juego real
            if estado["n"] % 5 == 0:
                estado["enviados"] += 1
                return [pygame.event.Event(tipo, **extra)]
            return []

        class RelojConTope(RelojFalso):
            def tick(self, fps=0):
                if estado["n"] > intentos:
                    raise _Colgado("el bucle no sale con el clic repetido")
                return 16

        pygame.event.get = eventos
        try:
            return asyncio.run(modulo_partida.partida(_superficie(), RelojConTope(), juego))
        except _Colgado as e:
            self.fail(str(e))
        finally:
            pygame.event.get = original

    def test_se_continua_tras_ganar(self):
        resultado = self._clic_y_salir(lambda j: self._llenar(j, USUARIO))
        self.assertIsNotNone(resultado, "el clic no salio del bucle tras ganar")
        self.assertTrue(resultado.victoria)
        self.assertEqual(resultado.marcador, (9, 0))

    def test_se_continua_tras_perder(self):
        """Este es el caso que se colgaba: victoria False hacia falsy el
        Resultado y el bucle no se rompia."""
        resultado = self._clic_y_salir(lambda j: self._llenar(j, CPU))
        self.assertIsNotNone(
            resultado,
            "tras perder, el clic no continua: el jugador se queda atrapado",
        )
        self.assertFalse(resultado.victoria)
        self.assertEqual(resultado.marcador, (0, 9))

    def test_tambien_se_continua_con_intro(self):
        resultado = self._clic_y_salir(lambda j: self._llenar(j, CPU), tecla=True)
        self.assertIsNotNone(resultado, "Intro no continua tras el duelo")

    def test_escape_no_trapa_al_ganador(self):
        """Con el duel ya terminado, ESC pausaba el juego y el cartel se
        quedaba ahí: el clic ya no salia porque todo iba a la pausa."""
        import partida as modulo_partida

        juego = modulo_partida.Juego("humano", bando_rival="orco")
        self._llenar(juego, USUARIO)
        juego.tiempo_fin = time.time() - 5

        original = pygame.event.get
        cola = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE,
                                   unicode="")]
        cola += [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                    pos=(640, 400))] * 30
        n = [0]

        def eventos():
            n[0] += 1
            if n[0] > 150:
                raise AssertionError("el clic no salio: el duel quedo en pausa")
            return [cola.pop(0)] if cola else []

        class RelojConTope(RelojFalso):
            def tick(self, fps=0):
                if n[0] > 150:
                    raise AssertionError("el clic no salio: el duel quedo en pausa")
                return 16

        pygame.event.get = eventos
        try:
            resultado = asyncio.run(modulo_partida.partida(_superficie(), RelojConTope(), juego))
        finally:
            pygame.event.get = original
        self.assertTrue(resultado.victoria)
        self.assertFalse(juego.pausa, "ESC no debe pausar un duel ya terminado")

    def test_el_flash_de_captura_se_limpia_al_terminar(self):
        """Con fin=True actualizar() no hacia nada y el ultimo flash se
        quedaba en la lista, redibujandose en cada frame del cartel."""
        import partida as modulo_partida

        juego = modulo_partida.Juego("humano", bando_rival="orco")
        juego.fin = True
        juego.flash = [(2, 1, time.time() - 3, USUARIO)]
        juego.actualizar(0.016)
        self.assertEqual(juego.flash, [],
                         "el flash de captura sobrevive al final del duel")

    def test_el_marcador_llega_a_su_total_aunque_el_duel_haya_acabado(self):
        """Dos cosas a la vez: actualizar() hacia nada con fin=True, y el
        int() truncaba el ascenso (7 -> 7.9 -> 7) y se quedaba corto."""
        import partida as modulo_partida

        juego = modulo_partida.Juego("humano", bando_rival="orco")
        from reglas import Carta

        for i in range(3):
            for j in range(3):
                carta = Carta(f"C{i}{j}", 9, 9, 9, 9, bando="humano")
                carta.dueno = USUARIO
                juego.board[i][j] = carta
        juego.fin = True
        juego.marcador_mostrado = [0, 0]
        for _ in range(60):
            juego.actualizar(0.05)
        self.assertEqual(juego.marcador_mostrado, [9, 0],
                         "el marcador deberia llegar al total real")

    def test_el_marcador_tambien_baja_cuando_el_rival_captura(self):
        import partida as modulo_partida

        juego = modulo_partida.Juego("humano", bando_rival="orco")
        from reglas import Carta

        for i in range(3):
            for j in range(3):
                carta = Carta(f"C{i}{j}", 9, 9, 9, 9, bando="humano")
                carta.dueno = USUARIO
                juego.board[i][j] = carta
        juego.marcador_mostrado = [9, 0]
        juego.board[2][2].dueno = CPU
        for _ in range(60):
            juego.actualizar(0.05)
        self.assertEqual(juego.marcador_mostrado, [8, 1])

    def test_resultado_perdido_es_verdadero_para_booleano(self):
        """Documenta la trampa: por eso el bucle no puede usar `if resultado`."""
        from partida import Resultado

        perdido = Resultado(False, 3, 9, (0, 9))
        self.assertFalse(bool(perdido), "Resultado debe seguir siendo falsy al perder")
        self.assertIsNotNone(perdido, "pero existe: se comprueba con is not None")


# ------------------------------------- 4b. el preview de la mano no se tapa
class TestPreviewDeLaMano(unittest.TestCase):
    """El bug: la carta ampliada de la carta señalada se pintaba dentro del
    bucle de la mano, asi que las cartas siguientes la tapaban."""

    MARCA = (255, 0, 255)

    def setUp(self):
        ui._PENDIENTES.clear()

    def tearDown(self):
        ui._PENDIENTES.clear()

    def _pintar_con_preview_marcado(self, raton):
        """Dibuja un frame y devuelve (pantalla, rect_del_preview, juego).

        El preview se pinta de magenta para reconocerlo en la captura.
        """
        import partida as modulo_partida

        pantalla = _superficie()
        juego = modulo_partida.Juego("humano", bando_rival="orco")
        # el test es de geometria con 5 cartas en mano (los mazos tienen 10)
        juego.mano_u = juego.mano_u[:5]
        juego.mano_c = juego.mano_c[:5]
        # sin fundido ni banner: solo la mano, para que el color se vea puro
        juego.t_entrada = time.time() - 10
        juego.banner = None
        rects = []

        original_preview = modulo_partida.Juego._dibujar_preview
        original_crear = modulo_partida.crt.crear

        def crear(carta, dueno=None, habilidad=True, synergy=False, escala=1,
                  bando_dueno=None):
            if escala != 1:
                s = pygame.Surface((int(ui.CARD_W * escala),
                                    int(ui.CARD_H * escala)))
                s.fill(self.MARCA)
                return s
            return original_crear(carta, dueno, habilidad=habilidad,
                                 synergy=synergy, escala=escala,
                                  bando_dueno=bando_dueno)

        def preview(juego_, screen, mouse, carta):
            rects.append(original_preview(juego_, screen, mouse, carta))
            return rects[-1]

        original_raton = pygame.mouse.get_pos
        pygame.mouse.get_pos = lambda: raton
        modulo_partida.crt.crear = crear
        modulo_partida.Juego._dibujar_preview = preview
        try:
            juego.dibujar(pantalla)
        finally:
            pygame.mouse.get_pos = original_raton
            modulo_partida.crt.crear = original_crear
            modulo_partida.Juego._dibujar_preview = original_preview
        return pantalla, (rects[0] if rects else None), juego

    def test_el_preview_va_encima_de_las_cartas_siguientes(self):
        raton = ui.mano_rect(0, 5).center
        pantalla, rect_preview, juego = self._pintar_con_preview_marcado(raton)
        self.assertIsNotNone(rect_preview, "no se dibujo ningun preview")
        self.assertIsNotNone(juego._hover_mano)

        # la zona del preview que queda encima de la carta siguiente de la mano
        vecina = ui.mano_rect(1, 5)
        solapa = pygame.Rect(rect_preview).clip(vecina)
        self.assertGreater(solapa.w, 0, "el preview no pisa a la vecina: el test no comprueba nada")
        self.assertGreater(solapa.h, 0, "el preview no pisa a la vecina: el test no comprueba nada")
        # un punto dentro del preview y dentro de la vecina, sin el borde redondeado
        punto = (solapa.centerx, solapa.y + 6)
        self.assertEqual(pantalla.get_at(punto)[:3], self.MARCA,
                         "la carta siguiente de la mano tapa el preview ampliado")

    def test_sin_hover_no_se_pinta_preview(self):
        pantalla, rect_preview, juego = self._pintar_con_preview_marcado((5, 5))
        self.assertIsNone(rect_preview, "sin raton sobre la mano no hay preview")
        self.assertIsNone(juego._hover_mano)
        # el magenta solo puede venir del preview: no debe quedar ninguno
        zona = ui.mano_rect(0, 5)
        for y in range(zona.top + 120, zona.bottom, 3):
            for x in range(zona.left, zona.right, 3):
                self.assertNotEqual(pantalla.get_at((x, y))[:3], self.MARCA,
                                    "se pintaron previews sin hover")


# ---------------------------------------------------------- 5. musica del duelo
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
            resultado = asyncio.run(modulo_partida.partida(
                _superficie(), RelojFalso(), juego, test_mode=True
            ))
        finally:
            audio.musica = original
            modulo_partida.audio.musica = original
        self.assertIn("musica_duelo", pedidos)
        self.assertNotIn("musica_orco", pedidos)
        self.assertTrue(resultado)


# ---------------------------------------------------------- 6. fps y memoria
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

    def test_el_fondo_tocado_devuelve_siempre_la_misma_superficie(self):
        a = ui.REC.fondo_tocado("assets/fondo.png", (8, 9, 16, 120))
        b = ui.REC.fondo_tocado("assets/fondo.png", (8, 9, 16, 120))
        self.assertIs(a, b, "el fondo con velo deberia estar cacheado")
        self.assertEqual(a.get_size(), (ui.ANCHO, ui.ALTO))

    def test_el_fondo_tocado_esta_mas_oscurecido_que_el_fondo(self):
        """Componer el velo no puede ser un no-op (bug silencioso)."""
        fondo = ui.REC.fondo_pantalla("assets/fondo.png")
        tocado = ui.REC.fondo_tocado("assets/fondo.png", (8, 9, 16, 200))
        claro = sum(fondo.get_at((100, 100))[:3])
        oscuro = sum(tocado.get_at((100, 100))[:3])
        self.assertLess(oscuro, claro)

    def test_el_cache_de_superficies_no_crece_sin_parada(self):
        """Si una cache crece frame a frame, en la web eso es memoria
        quemando hasta que el navegador mata la pestana."""
        import partida
        import reglas

        ui.limpiar_cache()
        screen = _superficie()
        juego = partida.Juego("humano", bando_rival="orco")
        for carta in list(juego.mano_u)[:4]:
            vacias = reglas.celdas_vacias(juego.board)
            if not vacias:
                break
            r, c = vacias[0]
            juego.colocar(carta, juego.mano_u, USUARIO, r, c)
        juego.t_entrada = 0.0
        for _ in range(20):
            juego.dibujar(screen)
        # los niveles de alpha quantized tardan unos cuantos frames en
        # llenarse; lo que no puede pasar es que la cache siga creciendo
        for _ in range(200):
            juego.dibujar(screen)
        primera = len(ui._CACHE_SUP)
        self.assertLess(primera, 200, "la cache deberia ser pequena de entrada")
        for _ in range(400):
            juego.dibujar(screen)
        segunda = len(ui._CACHE_SUP)
        self.assertLess(segunda, 200,
                        f"la cache deberia ser pequena (hay {segunda} entradas)")
        self.assertLessEqual(segunda, ui.MAX_CACHE,
                             "la cache no puede pasar de su tope sin limpiarse")
        # lo que mantiene acotada la cache de halos es agrupar el alpha: si
        # alguien cachea un alpha continuo, aqui se ve enseguida
        for clave in ui._CACHE_SUP:
            if isinstance(clave, tuple) and clave[:1] == ("resplandor",):
                self.assertEqual(clave[4] % 16, 0,
                                 f"alpha sin cuantizar en la cache: {clave}")


class TestCachesDeRender(unittest.TestCase):
    """Las cachés de ui.py no pueden cambiar ni un pixel de lo que se ve."""

    def setUp(self):
        ui.limpiar_cache()
        self.screen = pygame.Surface((ui.ANCHO, ui.ALTO))

    def _pinta(self, dibujar):
        self.screen.fill((30, 40, 60))
        dibujar(self.screen)
        return pygame.image.tostring(self.screen, "RGB")

    def test_el_texto_cacheado_es_identico_al_sin_cache(self):
        def con_cache(s):
            ui.texto(s, "Prueba 123", 10, ui.DORADO, centro=(400, 300))
        ui.limpiar_cache()
        primero = self._pinta(con_cache)
        segundo = self._pinta(con_cache)
        ui.limpiar_cache()
        sin_cache = self._pinta(con_cache)
        self.assertEqual(primero, segundo, "el texto cacheado debe ser identico")
        self.assertEqual(primero, sin_cache)

    def test_el_texto_con_sombra_va_dos_pixels_mas_arriba_izquierda(self):
        """La sombra debe quedar exactamente como antes: (x+2, y+2)."""
        ui.limpiar_cache()
        con = pygame.Surface((80, 30))
        con.fill((0, 0, 0))
        ui.texto(con, "AB", 10, ui.TEXTO, x=10, y=5, sombra=True)
        ui.limpiar_cache()
        sin = pygame.Surface((80, 30))
        sin.fill((0, 0, 0))
        ui.texto(sin, "AB", 10, ui.TEXTO, x=10, y=5, sombra=False)
        # la version con sombra debe tener todo lo que tiene la sin sombra
        for y in range(sin.get_height()):
            for x in range(sin.get_width()):
                if sin.get_at((x, y))[3] > 0:
                    self.assertGreaterEqual(
                        con.get_at((x, y))[3], sin.get_at((x, y))[3],
                        f"el texto sin sombra tiene algo que la sombra no cubre en {x},{y}",
                    )

    def test_ancho_texto_no_cambia_al_limpiar_cache(self):
        for cadena in ("Hola", "Cadena larga de prueba", "1234567890"):
            ui.limpiar_cache()
            a = ui.ancho_texto(cadena, 9)
            b = ui.ancho_texto(cadena, 9)
            ui.limpiar_cache()
            c = ui.ancho_texto(cadena, 9)
            self.assertEqual(a, c, f"ancho_texto('{cadena}') no es estable")
            self.assertEqual(a, b)

    def test_limpio_se_puede_llamar_ANTES_y_despues_de_cachear(self):
        """`limpio` cachea por el texto original: llamarlo dos veces con el
        texto ya limpio tiene que devolver lo mismo."""
        self.assertEqual(ui.limpio("Árbol"), ui.limpio("Arbol"))
        self.assertEqual(ui.limpio("¿Qué?"), ui.limpio("¿Qué?"))

    def test_panel_y_resplandor_devuelven_el_mismo_pixel(self):
        def dibujar(s):
            ui.panel(s, pygame.Rect(50, 50, 200, 120), ui.PANEL, ui.DORADO)
            ui.resplandor(s, pygame.Rect(300, 300, 120, 60), ui.VERDE, 120, 3, 8)
            ui.panel_vineta(s, 120)
            ui.linea_horizontal(s, 700)
        ui.limpiar_cache()
        primero = self._pinta(dibujar)
        ui.limpiar_cache()
        segundo = self._pinta(dibujar)
        self.assertEqual(primero, segundo,
                         "las superficies cacheadas difieren del dibujado limpio")

    def test_la_capa_reutilizable_se_recarga_en_cada_llamada(self):
        """`_capa_color` devuelve la MISMA Surface siempre: si no la
        rellenara, el fundido se quedaria pegado al ultimo alpha."""
        a = ui._capa_color((0, 0, 0), 255)
        pixel_a = a.get_at((10, 10))
        b = ui._capa_color((255, 0, 0), 10)
        pixel_b = b.get_at((10, 10))
        self.assertIs(a, b, "deberia reutilizarse la misma Surface")
        self.assertEqual(pixel_a[0], 0)
        self.assertEqual(pixel_b[0], 255)
        self.assertGreater(pixel_b[3], 0)

    def test_superficie_no_recrea_la_misma_clave(self):
        llamadas = []

        def factory():
            llamadas.append(1)
            return pygame.Surface((4, 4))

        clave = ("test", "superficie")
        a = ui.superficie(clave, factory)
        b = ui.superficie(clave, factory)
        self.assertIs(a, b)
        self.assertEqual(len(llamadas), 1)
        ui.limpiar_cache()
        c = ui.superficie(clave, factory)
        self.assertIsNot(a, c, "limpiar_cache debe vaciar las superficies")

    def test_color_cache_agrupa_los_canales(self):
        self.assertEqual(ui.color_cache((250, 251, 3)), (248, 248, 0))
        self.assertEqual(ui.color_cache((250, 251, 3, 129)), (248, 248, 0, 128))

    def test_un_hover_continuo_no_hace_crecer_las_caches(self):
        """El boton que late el hover es el peor caso para una cache: si el
        color no se agrupa, cada frame deja una entrada y la cache crece sin
        parar (y encima nunca acierta)."""
        ui.limpiar_cache()
        boton = ui.Boton(pygame.Rect(100, 100, 200, 50), "JUGAR", 12, sub="Enter",
                         atajo="1")
        for i in range(240):
            boton.hover = min(1.0, i / 120.0)
            boton.dibujar(self.screen)
        self.assertLessEqual(len(ui._CACHE_TXT), 24,
                             f"cache de texto: {len(ui._CACHE_TXT)} entradas")
        self.assertLessEqual(len(ui._CACHE_SUP), 24,
                             f"cache de superficies: {len(ui._CACHE_SUP)} entradas")

    def test_el_banner_apagandose_no_hace_crecer_la_cache_de_texto(self):
        """Un texto con alpha decreciente no se cachea (se veria a saltos),
        pero tampoco puede llenar la cache."""
        ui.limpiar_cache()
        for i in range(1, 60):
            a = 255 - i * 4
            ui.texto(self.screen, "VICTORIA", 30, ui.con_alpha(ui.VERDE, a),
                     centro=(400, 300))
        self.assertEqual(len(ui._CACHE_TXT), 0,
                         "los textos translucidos no deben cachearse")


class TestMedidorDeFps(unittest.TestCase):
    """`depurar.activar()` no puede romper el bucle ni el dibujado."""

    def test_el_medidor_pinta_y_se_puede_desactivar(self):
        import depurar

        pantalla = _superficie()
        antes = pygame.display.flip
        try:
            depurar.activar()
            self.assertIsNot(pygame.display.flip, antes)
            for _ in range(12):
                pygame.event.pump()
                pantalla.fill((0, 0, 0))
                pygame.display.flip()
            self.assertTrue(depurar._cuadros, "el medidor deberia haber medido frames")
            self.assertTrue(any(t > 0 for t in depurar._cuadros))
        finally:
            depurar.desactivar()
        self.assertIs(pygame.display.flip, antes, "hay que devolver display.flip")


if __name__ == "__main__":
    unittest.main()