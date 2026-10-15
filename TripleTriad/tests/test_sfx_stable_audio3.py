"""El lote Stable Audio 3 sustituye SFX por el MISMO nombre logico.

Contratos:
- los doce sonidos mapeados resuelven al WAV del lote;
- lo que no esta en el manifiesto (cinematicas, victoria, derrota, musica)
  NO se redirige, y con hash incorrecto se cae al original;
- la musica no pasa por el selector;
- la suite de siempre sigue pasando (cartas, reglas, mecanicas).
"""
import hashlib
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["TRIPLETRIAD_DATA"] = tempfile.mkdtemp(prefix="tt_sfx3_")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import audio
from paths import recurso

MAPEADOS = ("place.wav", "capture.wav", "same.wav", "plus.wav", "chain.wav",
            "invalid.wav", "menu.wav", "menu_move.wav", "menu_ok.wav",
            "menu_back.wav", "card.wav", "drag.wav")
INTACTOS = ("win.wav", "lose.wav", "cinema.wav", "reward.wav", "boss.wav")


class TestLoteStableAudio3(unittest.TestCase):
    def test_manifest_y_hashes(self):
        with open(recurso("assets/sfx_stable_audio3/manifest.json"), encoding="utf-8") as f:
            mapa = json.load(f)["mapa"]
        self.assertEqual(len(mapa), 12)
        for nombre, e in mapa.items():
            with open(recurso(e["archivo"]), "rb") as fh:
                self.assertEqual(hashlib.sha256(fh.read()).hexdigest(), e["sha256"], nombre)

    def test_los_doce_redirigen(self):
        for nombre in MAPEADOS:
            ruta = audio._lote_disponible(nombre)
            self.assertIsNotNone(ruta, nombre)
            self.assertTrue(ruta.startswith("assets/sfx_stable_audio3/"), nombre)

    def test_cinematicas_y_otros_no_se_redirigen(self):
        for nombre in INTACTOS + ("inexistente.wav",):
            self.assertIsNone(audio._lote_disponible(nombre), nombre)

    def test_hash_roto_cae_al_original(self):
        entrada = dict(audio._lote_sfx()["place.wav"])
        with mock.patch.dict(audio._lote_sfx(), {"place.wav": dict(entrada, sha256="0" * 64)}):
            self.assertIsNone(audio._lote_disponible("place.wav"))

    def test_reversion_por_entorno(self):
        with mock.patch.object(audio, "_LOTE_ACTIVO", False):
            audio._lote_sfx.cache_clear()
            self.assertIsNone(audio._lote_disponible("place.wav"))
        audio._lote_sfx.cache_clear()
        self.assertIsNotNone(audio._lote_disponible("place.wav"))

    def test_musica_no_pasa_por_el_lote(self):
        self.assertNotIn("sfx_stable", audio._ruta_musica("musica_duelo"))
        self.assertEqual(audio.musica_de_duelo(), "musica_duelo")

    def test_musica_duelo_intacta(self):
        import wave
        p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "assets", "musica", "musica_duelo.wav")
        with wave.open(p) as w:
            self.assertEqual(w.getframerate(), 44100)

    def test_dos_hooks_nuevos_existen(self):
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(raiz, "partida.py"), encoding="utf-8") as f:
            fuente = f.read()
        self.assertIn("sfx_stable_audio3/ability.wav", fuente)
        self.assertIn("sfx_stable_audio3/turn_change.wav", fuente)

    def test_formato_identico_al_mixer(self):
        import wave
        mixer = (audio.pygame.mixer.get_init() or (44100, -16, 2, 512))
        with open(recurso("assets/sfx_stable_audio3/manifest.json"), encoding="utf-8") as f:
            mapa = json.load(f)["mapa"]
        for nombre, e in mapa.items():
            with wave.open(recurso(e["archivo"])) as w:
                self.assertEqual(w.getframerate(), 44100, nombre)
                self.assertEqual(w.getnchannels(), 2, nombre)
                self.assertEqual(w.getsampwidth() * 8, 16, nombre)


if __name__ == "__main__":
    unittest.main()
