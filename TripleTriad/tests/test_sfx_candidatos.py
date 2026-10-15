"""Contratos de los SFX candidatos: apagado por defecto, integridad, cache,
rotacion, simultaneos y aislamiento de volumen. No toca musica ni SFX base."""
import os
import sys
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["TRIPLETRIAD_DATA"] = tempfile.mkdtemp(prefix="tt_sfx_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame
import audio
import sfx_candidatos
from paths import recurso


class TestSfxCandidatos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        audio.iniciar()

    def setUp(self):
        sfx_candidatos.reset()

    def test_apagado_por_defecto_no_suena(self):
        self.assertFalse(sfx_candidatos.ACTIVO)
        self.assertIsNone(sfx_candidatos.reproducir("card_place"))

    def test_manifest_y_hashes_intactos(self):
        import json
        with open(recurso("assets/sfx_candidatos/manifest.json"), encoding="utf-8") as f:
            data = json.load(f)
        import hashlib
        for evento in data["eventos"].values():
            for nombre, meta in evento["wav"].items():
                with open(recurso("assets/sfx_candidatos/" + nombre), "rb") as fh:
                    self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), meta["sha256"], nombre)

    def test_cache_marca_ausente_y_no_reintenta(self):
        # El manifiesto debe seguir leyéndose: se aísla el WAV, no `recurso`.
        with mock.patch.object(sfx_candidatos.os.path, "exists", return_value=False), \
                mock.patch.object(sfx_candidatos, "ACTIVO", True):
            self.assertIsNone(sfx_candidatos.reproducir("card_place"))
        # El fallo queda cacheado: no se reintenta en el siguiente evento.
        self.assertIn("card_place_01.wav", sfx_candidatos._cache)
        with mock.patch.object(sfx_candidatos.os.path, "exists", return_value=False), \
                mock.patch.object(sfx_candidatos, "ACTIVO", True):
            self.assertIsNone(sfx_candidatos.reproducir("card_place"))

    def test_rotacion_determinista_entre_variantes(self):
        with mock.patch.object(sfx_candidatos, "ACTIVO", True):
            orden = [sfx_candidatos.reproducir("card_place") for _ in range(4)]
        # dos variantes: alterna v1,v2,v1,v2
        self.assertEqual(orden, ["card_place_01.wav", "card_place_02.wav",
                                 "card_place_01.wav", "card_place_02.wav"])
        sfx_candidatos.reset()
        with mock.patch.object(sfx_candidatos, "ACTIVO", True):
            orden2 = [sfx_candidatos.reproducir("card_place") for _ in range(2)]
        self.assertEqual(orden, [orden2[0], orden2[1], orden[2], orden[3]])

    def test_evento_sin_cablear_suena_pero_queda_registrado(self):
        # ability_trigger y turn_change existen como WAV pero no tienen ancla de
        # audio en el codigo todavia. Si se activan deben sonar, pero el mapa
        # documenta que faltan hooks.
        with mock.patch.object(sfx_candidatos, "ACTIVO", True):
            self.assertIsNotNone(sfx_candidatos.reproducir("ability_trigger"))
            self.assertIsNotNone(sfx_candidatos.reproducir("turn_change"))
        self.assertIsNone(sfx_candidatos.EVENTOS["ability_trigger"]["ancla_evento_existente"])
        self.assertIsNone(sfx_candidatos.EVENTOS["turn_change"]["ancla_evento_existente"])

    def test_limita_simultaneos(self):
        sfx_candidatos._voces.clear()
        with mock.patch.object(sfx_candidatos, "ACTIVO", True):
            for _ in range(sfx_candidatos.MAX_SIMULTANEOS + 2):
                sfx_candidatos.reproducir("combo_chain")
        self.assertLessEqual(len(sfx_candidatos._voces), sfx_candidatos.MAX_SIMULTANEOS)

    def test_volumen_aislado_de_musica_y_sfx_base(self):
        vol_musica_antes = audio.volumen_musica()
        vol_sfx_antes = audio.volumen_sfx()
        sfx_candidatos.volumen(0.9)
        self.assertEqual(audio.volumen_musica(), vol_musica_antes)
        self.assertEqual(audio.volumen_sfx(), vol_sfx_antes)
        self.assertEqual(sfx_candidatos.volumen(), 0.9)

    def test_canal_nombreado_detiene_previo(self):
        with mock.patch.object(sfx_candidatos, "ACTIVO", True):
            sfx_candidatos.reproducir("card_capture", canal="cap")
            self.assertIn(("card_capture", "cap"), sfx_candidatos._canales)
            antes = len(sfx_candidatos._voces)
            sfx_candidatos.reproducir("card_capture", canal="cap")
        # Un sonido con canal no consume una voz libre: el anterior se para.
        self.assertEqual(len(sfx_candidatos._voces), antes)

    def test_reset_limpia_estado(self):
        with mock.patch.object(sfx_candidatos, "ACTIVO", True):
            sfx_candidatos.reproducir("card_place")
        self.assertTrue(sfx_candidatos._voces or sfx_candidatos._rotacion)
        sfx_candidatos.reset()
        self.assertEqual(sfx_candidatos._voces, [])
        self.assertEqual(sfx_candidatos._rotacion, {})


if __name__ == "__main__":
    unittest.main()
