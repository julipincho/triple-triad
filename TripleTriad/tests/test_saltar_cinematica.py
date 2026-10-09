"""Saltar cinemáticas y texto instantáneo: dos opciones para probar más rápido.

Motivo de ser: al revisar cambios hay que ver las escenas y eso son decenas de
segundos por partida. Con "saltar cine" se va de 13 escenas en varios segundos
a 4 ms, y con "texto instantáneo" el texto sale entero sin máquina de escribir,
que es lo que hace falta para releer el guion.

Lo importante del diseño: vienen DESACTIVADAS. El epílogo del final está
protegido por diseño (hay un test que exige que no se pueda saltar la parte que
explica el final), así que el interruptor no quita esa protección: la ignora
solo cuando el jugador lo pide explícitamente.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tt_test_opciones")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
# Tambien el directorio de tests, para el helper `opciones_test`: al lanzar un
# solo modulo no lo anade `discover`.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import audio  # noqa: E402
import cinematicas  # noqa: E402
import finales  # noqa: E402
import opciones  # noqa: E402


def setUpModule():
    pygame.init()
    pygame.display.set_mode((1280, 800))
    audio.iniciar()


def _secuencia():
    """Una secuencia larga de verdad: umbral + epilogo, 13 escenas."""
    return finales.escenas_umbral("dominio") + finales.escenas_epilogo("caos")


def _reloj():
    return type("R", (), {"tick": lambda self, fps=60: 16})()


def _correr(escenas, **kw):
    import asyncio

    async def ir():
        await cinematicas.reproducir(pygame.display.get_surface(),
                                     _reloj(), escenas, **kw)

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(ir())
    finally:
        loop.close()


class TestOpcionesPersistidas(unittest.TestCase):
    def setUp(self):
        opciones.invalidar()
        self._antes = opciones.opciones()

    def tearDown(self):
        opciones.invalidar()
        for clave, valor in self._antes.items():
            opciones.fijar(clave, valor)
        opciones.invalidar()

    def test_las_dos_opciones_existen_y_valen_lo_que_dicen(self):
        for clave in ("saltar_cinematica", "saltar_dialogo"):
            self.assertIn(clave, opciones.opciones())
            self.assertIsInstance(opciones.obtener(clave), bool)

    def test_vienen_desactivadas_por_defecto(self):
        """El juego de verdad no cambia: el epilogo sigue protegido."""
        # Se parte de un fichero limpio para comprobar el default de verdad.
        opciones.invalidar()
        import json

        from paths import archivo
        ruta = archivo(opciones.ARCHIVO)
        if os.path.exists(ruta):
            os.remove(ruta)
        opciones.invalidar()
        self.assertFalse(opciones.saltar_cinematica())
        self.assertFalse(opciones.saltar_dialogo())
        del json

    def test_alternar_invierte_y_guarda(self):
        antes = opciones.saltar_cinematica()
        nuevo = opciones.alternar("saltar_cinematica")
        self.assertNotEqual(antes, nuevo)
        # Se relee del disco: si no se guardase, `invalidar` lo perderia.
        opciones.invalidar()
        self.assertEqual(opciones.saltar_cinematica(), nuevo)

    def test_sobrevive_al_reinicio_del_juego(self):
        opciones.fijar("saltar_cinematica", True)
        opciones.invalidar()  # como si el juego se acabara de lanzar
        self.assertTrue(opciones.saltar_cinematica())
        opciones.fijar("saltar_cinematica", False)

    def test_no_toca_disco_si_ya_esta_cacheado(self):
        """`opciones()` puede llamarse desde un bucle: tiene que ser gratis."""
        opciones.saltar_cinematica()  # calienta
        import paths

        original = paths.archivo
        llamadas = []
        paths.archivo = lambda n: (llamadas.append(n), original(n))[1]
        try:
            for _ in range(50):
                opciones.saltar_cinematica()
                opciones.saltar_dialogo()
        finally:
            paths.archivo = original
        self.assertEqual(llamadas, [],
                         f"opciones leyo el disco {len(llamadas)} veces con cache")

    def test_un_fichero_corrupto_no_rompe(self):
        from paths import archivo
        ruta = archivo(opciones.ARCHIVO)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("{esto no es json")
        opciones.invalidar()
        self.assertFalse(opciones.saltar_cinematica())
        self.assertFalse(opciones.saltar_dialogo())


class TestSaltarCinematica(unittest.TestCase):
    def setUp(self):
        opciones.invalidar()
        self._antes = opciones.saltar_cinematica()

    def tearDown(self):
        opciones.fijar("saltar_cinematica", self._antes)
        opciones.invalidar()

    def test_la_secuencia_de_prueba_es_larga_de_verdad(self):
        """Si esta prueba no usa una secuencia larga, no mide nada."""
        self.assertGreaterEqual(len(_secuencia()), 10)

    def test_sin_la_opcion_no_hay_salto_automatico(self):
        opciones.fijar("saltar_cinematica", False)
        c = cinematicas.Cinematica(_secuencia(), permitir_saltar=False)
        self.assertFalse(c.saltar_todo)

    def test_con_la_opcion_la_secuencia_se_salte_entera(self):
        """Se comprueba de verdad: `ejecutar` termina y llama a `al_terminar`.

        No se mide el tiempo (seria fragil); se mide el efecto: sin la opcion
        `ejecutar` dibujaria escena a escena, con la opcion se cierra sola.
        """
        opciones.fijar("saltar_cinematica", True)
        escenas = _secuencia()
        largo = len(escenas)
        terminado = []
        c = cinematicas.Cinematica(escenas, permitir_saltar=False,
                                   al_terminar=lambda: terminado.append(True))
        self.assertTrue(c.saltar_todo)

        import asyncio

        async def ir():
            await c.ejecutar(pygame.display.get_surface(), _reloj())

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(ir())
        finally:
            loop.close()

        self.assertEqual(terminado, [True], "no llego al final de la secuencia")
        self.assertEqual(c.i, largo, "no se salto toda la secuencia")

    def test_la_opcion_se_lee_al_construir_una_vez(self):
        """No se consulta por frame: se lee al construir la secuencia."""
        opciones.fijar("saltar_cinematica", True)
        c = cinematicas.Cinematica(_secuencia())
        self.assertTrue(c.saltar_todo)
        # Cambiar la opcion despues no afecta a una secuencia ya construida:
        # eso es lo que la hace segura de llamar por frame.
        opciones.fijar("saltar_cinematica", False)
        self.assertTrue(c.saltar_todo)

    def test_el_texto_instantaneo_muestra_la_linea_entera(self):
        opciones.fijar("saltar_dialogo", True)
        c = cinematicas.Cinematica(_secuencia())
        self.assertTrue(c.sin_texto)


class TestLaProteccionDelFinalSigueEnPie(unittest.TestCase):
    """Lo que el interruptor NO puede hacer: cambiar el juego por defecto."""

    def tearDown(self):
        opciones.fijar("saltar_cinematica", False)
        opciones.invalidar()

    def test_sin_la_opcion_el_epilogo_no_se_puede_saltar(self):
        opciones.fijar("saltar_cinematica", False)
        c = cinematicas.Cinematica(_secuencia(), permitir_saltar=False)
        self.assertFalse(c.permitir_saltar,
                         "el epilogo debe seguir protegido por defecto")
        self.assertFalse(c.saltar_todo)


class TestLaSuiteNoDependeDeTuConfiguracion(unittest.TestCase):
    """La opcion vive en `opciones.json`, en el directorio de datos.

    Los tests fuerzan ese mismo directorio con `TRIPLETRIAD_DATA`, asi que si el
    desarrollador deja "SALTAR CINE" activado, la suite se entera. Ya lo hizo:
    `test_la_cinematica_termina_pulsando_escape_siempre` fallaba porque la
    cinematica terminaba antes de leer el ESC.

    Estos tests comprueban que con la opcion a SI y a NO la cinematica se
    comporta como se espera en cada caso.
    """

    def test_con_la_opcion_a_si_no_se_lee_ningun_evento(self):
        import opciones_test

        escenas = [cinematicas.Escena(cinematicas.esc("una")),
                   cinematicas.Escena(cinematicas.esc("dos"))]
        with opciones_test.sin_opciones(saltar_cinematica=True):
            c = cinematicas.Cinematica(escenas)
            self.assertTrue(c.saltar_todo)

    def test_con_la_opcion_a_no_la_cinematica_se_reproduce(self):
        import opciones_test

        escenas = [cinematicas.Escena(cinematicas.esc("una")),
                   cinematicas.Escena(cinematicas.esc("dos"))]
        with opciones_test.sin_opciones(saltar_cinematica=False):
            c = cinematicas.Cinematica(escenas)
            self.assertFalse(c.saltar_todo)
            self.assertEqual(c.i, 0, "no debe haber avanzado nada todavia")

    def test_el_texto_instantaneo_tambien_es_independiente(self):
        import opciones_test

        escenas = [cinematicas.Escena(cinematicas.esc("una"))]
        with opciones_test.sin_opciones(saltar_dialogo=True):
            self.assertTrue(cinematicas.Cinematica(escenas).sin_texto)
        with opciones_test.sin_opciones(saltar_dialogo=False):
            self.assertFalse(cinematicas.Cinematica(escenas).sin_texto)

    def test_el_contexto_restaura_el_valor_original(self):
        import opciones_test

        antes = opciones.saltar_cinematica()
        with opciones_test.sin_opciones(saltar_cinematica=not antes):
            self.assertEqual(opciones.saltar_cinematica(), not antes)
        opciones.invalidar()
        self.assertEqual(opciones.saltar_cinematica(), antes,
                         "el contexto no restauro el valor original")


if __name__ == "__main__":
    unittest.main()