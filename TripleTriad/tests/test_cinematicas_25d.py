"""Tests del motor de fondos cinematográficos 2.5D."""

import os
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("TRIPLETRIAD_DATA", tempfile.mkdtemp(prefix="tt_25d_"))

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame
import cinematicas
import cinematicas_25d
from ui import ANCHO, ALTO


class TestCinematicas25D(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((ANCHO, ALTO))

    def setUp(self):
        cinematicas_25d.recargar()

    def test_manifest_y_capas_existen(self):
        manifest = cinematicas_25d._manifest()
        self.assertIn("escenas", manifest)
        self.assertIn("salon_torneo", manifest["escenas"])
        for nombre, datos in manifest["escenas"].items():
            for capa in datos.get("capas", []):
                ruta = cinematicas_25d.recurso(
                    os.path.join("assets", "cinematicas_25d", capa["archivo"]))
                self.assertTrue(os.path.isfile(ruta), ruta)

    def test_clave_de(self):
        escena = cinematicas.Escena(
            {"fondo": "camino", "fondo_hd": "salon_torneo.png", "texto": ""})
        self.assertEqual(cinematicas_25d.clave_de(escena), "salon_torneo")

    def test_desplazamiento_en_reposo(self):
        manifest = cinematicas_25d._manifest()
        capa = manifest["escenas"]["salon_torneo"]["capas"][2]
        self.assertEqual(cinematicas_25d.desplazamiento(capa, 0.0), (0, 0))
        dx, dy = cinematicas_25d.desplazamiento(capa, 10.0)
        self.assertLessEqual(abs(dx), int(capa["dx"]))
        self.assertLessEqual(abs(dy), int(capa["dy"]))

    def test_dibuja_capas(self):
        datos = {"fondo": "camino", "fondo_hd": "salon_torneo.png", "texto": ""}
        cine = cinematicas.Cinematica([datos])
        escena = cine.escena()
        self.assertTrue(cinematicas_25d.dibujar_fondo(self.screen, escena, 0.0))
        self.assertTrue(getattr(escena, "_25d_clave", None) == "salon_torneo")
        cinematicas_25d.dibujar_particulas(self.screen, escena, 0.0)

    def test_fallback_sin_manifest(self):
        with patch_manifest_vacio():
            escena = cinematicas.Escena(
                {"fondo": "camino", "fondo_hd": "salon_torneo.png", "texto": ""})
            self.assertFalse(cinematicas_25d.dibujar_fondo(self.screen, escena, 0.0))

    def test_flag_desactivado(self):
        original = cinematicas_25d.ACTIVO
        try:
            cinematicas_25d.ACTIVO = False
            escena = cinematicas.Escena(
                {"fondo": "camino", "fondo_hd": "salon_torneo.png", "texto": ""})
            self.assertFalse(cinematicas_25d.dibujar_fondo(self.screen, escena, 0.0))
        finally:
            cinematicas_25d.ACTIVO = original

    def test_movimiento_reducido_anula_desplazamiento(self):
        manifest = cinematicas_25d._manifest()
        capa = manifest["escenas"]["salon_torneo"]["capas"][2]
        with patch_opciones(True):
            self.assertEqual(cinematicas_25d.desplazamiento(capa, 5.0), (0, 0))

    def test_bbox_dentro_de_la_capa(self):
        manifest = cinematicas_25d._manifest()
        for datos in manifest["escenas"].values():
            for capa in datos.get("capas", []):
                bx, by, bw, bh = capa["bbox"]
                self.assertGreaterEqual(bx, 0)
                self.assertGreaterEqual(by, 0)
                self.assertLessEqual(bx + bw, 1328 + 1)
                self.assertLessEqual(by + bh, 744 + 1)


def patch_manifest_vacio():
    import unittest.mock as mock
    return mock.patch.object(cinematicas_25d, "_manifest", return_value={})


def patch_opciones(valor):
    import unittest.mock as mock
    return mock.patch("opciones.movimiento_reducido", return_value=valor)


if __name__ == "__main__":
    unittest.main()
