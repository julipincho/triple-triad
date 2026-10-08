"""Tests de la auditoria visual: el juego pasa y la puerta muerde.

    python -m unittest tests.test_auditoria -v
"""

import os
import sys
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import auditoria_visual  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


def setUpModule():
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))


class TestAuditoria(unittest.TestCase):
    def test_el_juego_no_tiene_desbordes(self):
        self.assertEqual(auditoria_visual.auditar(), [])

    def test_el_texto_largo_se_detecta(self):
        p = auditoria_visual.exceso_lineas("palabra " * 100, 12, 980, 4, "sintetico")
        self.assertIsNotNone(p)
        self.assertIn("sintetico", p)

    def test_el_texto_corto_pasa(self):
        self.assertIsNone(auditoria_visual.exceso_lineas("corto", 12, 980, 4, "x"))
        self.assertIsNone(auditoria_visual.desborda("HOMBRES", 8, 80, "x"))

    def test_el_nombre_ancho_se_detecta(self):
        # "Hombres Lobo" a tam 11 no cabe en 104px: asi se cazo el bug real
        p = auditoria_visual.desborda("Hombres Lobo", 11, 104, "sintetico")
        self.assertIsNotNone(p)

    def test_el_rect_fuera_se_detecta(self):
        p = auditoria_visual.fuera_pantalla((1200, 700, 200, 200), "sintetico")
        self.assertIsNotNone(p)
        self.assertIsNone(auditoria_visual.fuera_pantalla((100, 100, 200, 200), "x"))


if __name__ == "__main__":
    unittest.main()
