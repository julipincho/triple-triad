"""Tests de las variantes de fondo.

Cada escena (`camino`, `campamento`, `trono`...) tiene varias imagenes del mismo
sitio con distinta luz o distinto clima, y se elige una con la semilla de la
partida. Eso abre tres formas de romperse que estos tests cierran:

  1. Que la semilla no llegue a tiempo y se dibuje siempre el original.
  2. Que la eleccion cambie DENTRO de la partida, con lo que el jugador pierde
     la orientacion al entrar y salir de un sitio.
  3. Que `ruta_fondo` devuelva un archivo que no existe, y se dibuje el
     cuadrado morado de `Recursos.imagen` en pantalla completa.
"""

import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import ui  # noqa: E402
from paths import recurso  # noqa: E402

CARPETA = os.path.join(RAIZ, "assets", "fondos")

#: Las escenas para las que se generaron variantes. Si `generar_variantes.py`
#: anade una escena, el inventario de `test_inventario_fondos` lo delata antes
#: de que este test se quede corto.
ESCENAS_CON_VARIANTES = ("asalto", "camino", "campamento", "escenario",
                         "ruinas", "trono", "umbral")


class TestVariantesDeFondo(unittest.TestCase):
    def setUp(self):
        ui.invalidar_variantes()

    tearDown = setUp

    # ------------------------------------------------------------- en disco
    def test_las_24_variantes_estan_en_disco(self):
        total = sum(len(ui.variantes_de(e)) for e in ESCENAS_CON_VARIANTES)
        self.assertEqual(24, total,
                         "se esperaban 24 variantes y hay %d" % total)

    def test_las_variantes_estan_a_512x256(self):
        """El tamano que hace que el fondo escale con factor entero 3.

        A 768 el factor seria 1 y el fondo se veria pequeno con barras; a 512
        el fondo ocupa el 96% de la pantalla. Un fondo fuera de estos dos
        tamanos se veria borroso o con barras, y aqui se pilla antes.
        """
        from PIL import Image
        for escena in ESCENAS_CON_VARIANTES:
            for variante in ui.variantes_de(escena):
                with Image.open(os.path.join(CARPETA, variante + ".png")) as im:
                    self.assertEqual((512, 256), im.size,
                                     "%s no es 512x256 y el motor lo escala mal"
                                     % variante)

    def test_ninguna_escena_base_se_declara_variante_de_si_misma(self):
        """`camino` no puede ser variante de `camino`: seria un bucle."""
        for escena in ESCENAS_CON_VARIANTES:
            self.assertNotIn(escena, ui.variantes_de(escena))

    # --------------------------------------------------------------- eleccion
    def test_la_semilla_elige_una_variante_real(self):
        for semilla in (0, 1, 7, 12345, 2 ** 63):
            ui.fijar_variantes(semilla)
            for escena in ESCENAS_CON_VARIANTES:
                ruta = ui.ruta_fondo(escena)
                self.assertTrue(os.path.exists(recurso(ruta)),
                                "semilla %d: %s no existe" % (semilla, ruta))

    def test_sin_fijar_semilla_sale_el_original(self):
        """Sin llamada a `fijar_variantes` no se elige nada: se usa el fondo de
        siempre. Es lo que quiere quien no ha pedido variantes, y evita que un
        duelo rapido se lleve por delante la eleccion de la campana."""
        self.assertEqual({}, ui._ELECCION)
        for escena in ESCENAS_CON_VARIANTES:
            self.assertEqual("assets/fondos/%s.png" % escena, ui.ruta_fondo(escena))

    def test_la_misma_semilla_da_los_mismos_fondos(self):
        """Es lo que hace que un sitio no cambie de aspecto al salir y volver."""
        ui.fijar_variantes(4242)
        primera = {e: ui.ruta_fondo(e) for e in ESCENAS_CON_VARIANTES}
        for semilla in (0, 99, 2 ** 40):
            ui.fijar_variantes(4242)
            self.assertEqual(primera, {e: ui.ruta_fondo(e)
                                       for e in ESCENAS_CON_VARIANTES},
                             "la semilla 4242 dejo de ser estable")

    def test_semillas_distintas_dan_combinaciones_distintas(self):
        """Si no, las 24 variantes serian trabajo perdido."""
        vistas = set()
        for semilla in range(40):
            ui.fijar_variantes(semilla)
            vistas.add(tuple(ui.ruta_fondo(e) for e in ESCENAS_CON_VARIANTES))
        # 7 escenas con 2..5 variantes cada una: hay miles de combinaciones
        # posibles, y 40 semillas distintas tienen que dar varias.
        self.assertGreater(len(vistas), 20,
                           "40 semillas solo dieron %d combinaciones"
                           % len(vistas))

    def test_cada_variante_aparece_al_alguna_semilla(self):
        """Ninguna de las 24 puede quedarse sin usarse nunca."""
        vistas = set()
        for semilla in range(200):
            ui.fijar_variantes(semilla)
            vistas.update(ui.ruta_fondo(e) for e in ESCENAS_CON_VARIANTES)
        sin_usar = sorted(
            v for e in ESCENAS_CON_VARIANTES for v in ui.variantes_de(e)
            if "assets/fondos/%s.png" % v not in vistas)
        self.assertEqual([], sin_usar,
                         "estas variantes no salen con ninguna semilla: %s"
                         % sin_usar)

    def test_una_escena_sin_variantes_cae_en_el_original(self):
        """`aldea` no tiene variantes: tiene que devolver su fondo, no fallar."""
        self.assertEqual([], ui.variantes_de("aldea"))
        ui.fijar_variantes(7)
        self.assertEqual("assets/fondos/aldea.png", ui.ruta_fondo("aldea"))

    def test_una_escena_inexistente_no_revienta(self):
        """Se llama con el nombre de la escena, que viene de datos narrativos.
        Que uno se Equivoque no puede ser un crash en plena partida."""
        for nombre in ("", "no_existe", "camino_de_ceniza"):
            self.assertEqual("assets/fondos/%s.png" % nombre,
                             ui.ruta_fondo(nombre))


class TestRendimientoDeVariantes(unittest.TestCase):
    def test_ruta_fondo_no_toca_el_disco_por_llamada(self):
        """Se llama POR FRAME desde las cinematograficas.

        `ruta_fondo` solo mira el diccionario de eleccion. Si vuelven a meter un
        `os.path.exists` por frame (que es lo que hace la comprobacion de
        seguridad) hay que moverla a `fijar_variantes`, que va una vez por
        partida.
        """
        ui.fijar_variantes(3)
        original = os.path.exists

        def prohibida(ruta):
            raise AssertionError("ruta_fondo leyo el disco: %s" % ruta)

        os.path.exists = prohibida
        try:
            for _ in range(100):
                for escena in ESCENAS_CON_VARIANTES:
                    ui.ruta_fondo(escena)
        finally:
            os.path.exists = original


if __name__ == "__main__":
    unittest.main()
