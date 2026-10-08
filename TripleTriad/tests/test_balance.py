"""Tests G5: balance, estadistica de sobres y minis con mazos fijos.

    python -m unittest tests.test_balance -v
"""

import os
import random
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests_balance")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import auditoria_poder  # noqa: E402
import campana  # noqa: E402
import mazos  # noqa: E402
from reglas import rareza, total_carta  # noqa: E402


class TestAuditoriaPoder(unittest.TestCase):
    def test_curvas_sanas(self):
        self.assertEqual(auditoria_poder.auditar_poder(), [])

    def test_ninguna_comun_supera_a_una_legendaria(self):
        for bando, cartas in mazos.TODOS.items():
            comunes = [total_carta(c) for c in cartas if rareza(c)[0] == "COMUN"]
            legs = [total_carta(c) for c in cartas if rareza(c)[0] == "LEGENDARIA"]
            self.assertTrue(comunes and legs, bando)
            self.assertLess(max(comunes), min(legs), bando)


class TestEstadisticaSobres(unittest.TestCase):
    def test_distribucion_con_semilla_y_pity(self):
        perfil = campana.cargar_perfil()
        perfil["moneda"] = 0
        perfil["pity_sobres"] = 0
        perfil["coleccion"] = {}
        campana.guardar_perfil(perfil)
        estado = campana.nueva_campana("humano")
        catalogo = {c.nombre: c for cartas in mazos.TODOS.values() for c in cartas}
        random.seed(1234)
        legs = 0
        racha_sin_leg = 0
        max_racha = 0
        total_cartas = 0
        try:
            for _ in range(60):
                nuevas, mejoradas = campana.abrir_sobre(estado)
                sacadas = nuevas + mejoradas
                self.assertEqual(len(sacadas), 3)
                hay = any(rareza(catalogo[n])[0] == "LEGENDARIA" for n in sacadas)
                legs += sum(1 for n in sacadas if rareza(catalogo[n])[0] == "LEGENDARIA")
                total_cartas += len(sacadas)
                if hay:
                    racha_sin_leg = 0
                else:
                    racha_sin_leg += 1
                    max_racha = max(max_racha, racha_sin_leg)
        finally:
            random.seed()
        self.assertEqual(total_cartas, 180)
        # ~3.4% por carta + pity (minimo 6 forzadas en 60 sobres)
        self.assertGreaterEqual(legs, 6)
        self.assertLessEqual(legs, 30)
        # el pity prohibe rachas de 10 sobres sin legendaria
        self.assertLessEqual(max_racha, 9)


class TestMinisMazosFijos(unittest.TestCase):
    def test_mini_usa_iniciales_aunque_haya_coleccion(self):
        perfil = campana.cargar_perfil()
        perfil["coleccion"] = {"Rey Aldric": mazos.HUMANOS[4].a_dict()}
        campana.guardar_perfil(perfil)
        estado = campana.nueva_mini_campana("hombre_pantera")
        self.assertEqual([d["nombre"] for d in estado["cartas"]],
                         [c.nombre for c in campana.mazo_inicial("hombre_pantera")])


if __name__ == "__main__":
    unittest.main()
