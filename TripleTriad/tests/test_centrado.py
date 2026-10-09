"""El centrado de filas no se descuadra nunca.

El patron viejo `ANCHO//2 - n*60 + i*120` desplazaba cada fila una cantidad
que dependia del ancho del elemento, y cambiaba de signo segun este: con
cartas de 73px la fila quedaba 23px a la izquierda y con las de 156px del
draft, 18px a la derecha. Estos tests fijan la regla para que corregir un
ancho o una cantidad no vuelva a descuadrar nada.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tt_test_centrado")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

import ui  # noqa: E402


def setUpModule():
    pygame.init()
    pygame.display.set_mode((ui.ANCHO, ui.ALTO))


class TestFilaCentrada(unittest.TestCase):
    def _span(self, x0, ancho, n, paso):
        """Extremos de una fila de n elementos."""
        return x0, x0 + (n - 1) * paso + ancho

    def test_el_bloque_queda_centrado_en_la_pantalla(self):
        for ancho in (30, 73, 83, 86, 96, 104, 156, 200):
            for n in (1, 2, 3, 5, 10):
                for gap in (0, 8, 16, 20, 47, 190):
                    with self.subTest(ancho=ancho, n=n, gap=gap):
                        x0 = ui.fila_centrada(ancho, n, gap)
                        izq, der = self._span(x0, ancho, n, ancho + gap)
                        # La diferencia de los dos margenes es como mucho 1px
                        # por redondeo entero.
                        self.assertLessEqual(
                            abs((izq) - (ui.ANCHO - der)), 1,
                            f"fila descentrada: {izq}..{der} de {ui.ANCHO}")

    def test_no_se_sale_de_la_pantalla_si_cabe(self):
        """Cuando la fila cabe, no se sale por ningun lado."""
        for ancho in (30, 73, 104, 156, 200):
            for n in (1, 3, 5, 10, 25):
                for gap in (0, 16, 47, 190):
                    total = n * ancho + (n - 1) * gap
                    if total > ui.ANCHO:
                        continue  # no cabe en ningun caso
                    with self.subTest(ancho=ancho, n=n, gap=gap):
                        x0 = ui.fila_centrada(ancho, n, gap)
                        izq, der = self._span(x0, ancho, n, ancho + gap)
                        self.assertGreaterEqual(izq, 0)
                        self.assertLessEqual(der, ui.ANCHO)

    def test_si_no_cabe_devuelve_un_anchor_negativo(self):
        """Una fila mas ancha que la pantalla no se puede centrar.

        El helper devuelve la x real (negativa) en vez de recortar a cero:
        recortarla esconderia el primer elemento sin avisar. Quien llame con
        muchas cartas tiene que reducir el paso, como hace `mano_rect`.
        """
        ancho, n, gap = 104, 25, 16
        self.assertGreater(n * ancho + (n - 1) * gap, ui.ANCHO)
        self.assertLess(ui.fila_centrada(ancho, n, gap), 0)

    def test_cero_elementos_no_revienta(self):
        self.assertEqual(ui.fila_centrada(104, 0), 0)
        self.assertEqual(ui.fila_centrada_paso(104, 0), (0, 104))

    def test_la_version_con_paso_devuelve_el_mismo_anchor(self):
        for ancho in (73, 104, 156):
            for n in (1, 3, 5, 10):
                for gap in (0, 16, 47):
                    x0, paso = ui.fila_centrada_paso(ancho, n, gap)
                    self.assertEqual(x0, ui.fila_centrada(ancho, n, gap))
                    self.assertEqual(paso, ancho + gap)

    def test_una_sola_carta_va_centrada(self):
        x0 = ui.fila_centrada(104, 1)
        self.assertEqual(x0 + 52, ui.ANCHO // 2)

    def test_el_anchor_no_depende_del_ancho_del_elemento(self):
        """El error del patron viejo: mover el ancho movia el centro."""
        centros = []
        for ancho in (73, 104, 156, 200):
            x0 = ui.fila_centrada(ancho, 3, 16)
            izq, der = self._span(x0, ancho, 3, ancho + 16)
            centros.append((izq + der) / 2)
        for c in centros:
            self.assertAlmostEqual(c, ui.ANCHO / 2, delta=1)


class TestFilaCentradaPorCentro(unittest.TestCase):
    """Filas que se pintan por el centro (la portada blitea cartas asi)."""

    def test_el_conjunto_de_centros_queda_centrado(self):
        for ancho in (73, 104, 156, 200):
            for n in (2, 3, 5):
                for paso in (16, 120, 240):
                    with self.subTest(ancho=ancho, n=n, paso=paso):
                        c0 = ui.fila_centrada_por_centro(ancho, n, paso)
                        primero = c0 - ancho // 2
                        ultimo = c0 + (n - 1) * paso + ancho // 2
                        self.assertLessEqual(
                            abs(primero - (ui.ANCHO - ultimo)), 2,
                            f"fila descentrada: {primero}..{ultimo} de {ui.ANCHO}")

    def test_una_sola_carta_al_centro(self):
        self.assertEqual(ui.fila_centrada_por_centro(104, 1, 240), ui.ANCHO // 2)

    def test_las_cartas_de_la_portada_quedan_centradas(self):
        # lo que hace pantallas.portada: 5 cartas de 104 con paso 240
        paso = 240
        c0 = ui.fila_centrada_por_centro(104, 5, paso)
        self.assertEqual(c0, 160)
        izq = c0 - 52
        der = c0 + 4 * paso + 52
        self.assertEqual(izq, 108)
        self.assertEqual(der, 1172)
        self.assertEqual((izq + der) // 2, ui.ANCHO // 2)


class TestChipsyCartasDePortada(unittest.TestCase):
    """Los dos casos que se veian descentrados en pantalla."""

    def test_los_chips_de_la_portada_estan_centrados(self):
        # lo que hace pantallas.portada con la lista de chips (pintados por
        # su borde izquierdo, asi que va con `fila_centrada`)
        chips = ["Diez facciones", "Seis duelos", "Un final por faccion"]
        w, gap = 200, 20
        x0 = ui.fila_centrada(w, len(chips), gap)
        izq = x0
        der = x0 + (len(chips) - 1) * (w + gap) + w
        self.assertEqual(izq, 320)
        self.assertEqual(der, 960)
        self.assertEqual((izq + der) // 2, ui.ANCHO // 2)


if __name__ == "__main__":
    unittest.main()