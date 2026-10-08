"""Tests de la cinematica de intro: estructura, recursos y humo visual.

    python -m unittest tests.test_intro -v
"""

import os
import sys
import tempfile
import time
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests_intro")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import audio  # noqa: E402
import campana  # noqa: E402
import cinematicas  # noqa: E402
import facciones  # noqa: E402
from paths import recurso  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


def setUpModule():
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))


class TestIntro(unittest.TestCase):
    def test_estructura(self):
        escenas, musica = cinematicas.intro()
        self.assertGreaterEqual(len(escenas), 4)
        self.assertEqual(escenas[0]["efecto"], "titulo")
        self.assertEqual(musica, audio.musica_de_menu())

    def test_fondos_y_retratos_existen(self):
        escenas, _ = cinematicas.intro()
        for e in escenas:
            ruta = recurso(os.path.join("assets", "fondos", f"{e['fondo']}.png"))
            self.assertTrue(os.path.exists(ruta), f"falta el fondo {e['fondo']}")
            if e.get("retrato"):
                self.assertIn(e["retrato"], facciones.FACCIONES)

    def test_se_reproduce_entera_sin_colgarse(self):
        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        escenas, _ = cinematicas.intro()
        cin = cinematicas.Cinematica(escenas)
        vistas = set()
        for _ in range(1000):
            if cin.escena() is None:
                break
            vistas.add(cin.i)
            self.assertTrue(cin.ejecutar_un_frame(pantalla))
            cin.escena().mostrado = len(cin.escena().texto)
            if not cin._avanzar():
                break
        self.assertEqual(vistas, set(range(len(escenas))))

    def test_se_marca_como_vista_una_sola_vez(self):
        # id unico por ejecucion: el perfil de tests vive en un tempdir que
        # persiste entre corridas y no debe contaminar el resultado
        cid = f"intro_prueba_{time.time_ns()}"
        self.assertTrue(campana.marcar_cinematica(cid))
        self.assertFalse(campana.marcar_cinematica(cid))


if __name__ == "__main__":
    unittest.main()
