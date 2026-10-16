"""Contratos de proteccion, seleccion y presentacion del lote pixel anime."""
import hashlib
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("TRIPLETRIAD_DATA", tempfile.mkdtemp(prefix="tt_arte_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame
import arte_visual
import cinematicas
import ui
from paths import recurso


class TestArtePixelAnime(unittest.TestCase):
    def setUp(self):
        # Estos tests verifican el lote base, independientemente de lotes nuevos.
        sustitucion = patch("arte_visual.lotes_visuales.retrato", return_value=None)
        sustitucion.start()
        self.addCleanup(sustitucion.stop)

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 800))

    def test_manifest_y_originales_intactos(self):
        for original, dato in arte_visual.catalogo().items():
            for ruta, hash_esperado in ((original, dato["original_sha256"]),
                                       (dato["ruta"], dato["sha256"])):
                with open(recurso(ruta), "rb") as f:
                    self.assertEqual(hashlib.sha256(f.read()).hexdigest(), hash_esperado, ruta)

    def test_cartas_y_lotes_aprobados_no_se_redirigen(self):
        for ruta in ("cartas/humano.png", "assets/carta.png",
                     "assets/cinematicas_hd/salon_torneo_lleno.png",
                     "assets/cinematicas_hd/sala_trono.png"):
            for tipo in ("fondo", "retrato"):
                self.assertIsNone(arte_visual.alternativa(ruta, tipo))

    def test_reversion_y_archivo_ausente(self):
        with patch.object(arte_visual, "ACTIVO", False):
            self.assertIsNone(arte_visual.alternativa("assets/avatar_nara.png", "retrato"))
        arte_visual._resolver.cache_clear()
        with patch("arte_visual.os.path.isfile", return_value=False):
            self.assertIsNone(arte_visual.alternativa("assets/avatar_nara.png", "retrato"))
        arte_visual._resolver.cache_clear()

    def test_viewport_720_sin_deformar(self):
        ruta = arte_visual.alternativa("assets/fondos/aldea.png", "fondo")
        base = pygame.image.load(recurso(ruta))
        resultado = ui.REC.fondo_cinematico(ruta)
        self.assertEqual(base.get_size(), (1280, 720))
        self.assertEqual(resultado.get_size(), (1280, 800))
        self.assertEqual(pygame.image.tostring(base, "RGB"),
                         pygame.image.tostring(resultado.subsurface((0, 40, 1280, 720)), "RGB"))

    def test_prioridad_del_hd_aprobado(self):
        datos = {"fondo": "camino", "fondo_hd": "camino_lluvioso.png", "texto": ""}
        cine = cinematicas.Cinematica([datos])
        with patch.object(ui.REC, "fondo_cinematico", wraps=ui.REC.fondo_cinematico) as render:
            cine._dibujar(self.screen, cine.escena(), 2)
            self.assertEqual(len(render.call_args_list), 1)
            self.assertTrue(render.call_args.args[0].endswith("camino_lluvioso.png"))

    def test_variantes_seleccionadas_y_retratos(self):
        for ruta, dato in arte_visual.catalogo().items():
            self.assertEqual(arte_visual.alternativa(ruta, dato["tipo"]), dato["ruta"])
            if dato["tipo"] == "retrato":
                self.assertEqual(ui.REC.imagen(ruta, (150, 150)).get_size(), (150, 150))


if __name__ == "__main__":
    unittest.main()
