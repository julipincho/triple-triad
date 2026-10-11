"""G9: que pasa cuando el guardado no se puede leer.

Un `campana.json` ilegible hacia que `cargar()` devolviera `None` y el menu
ofreciera "NUEVA CAMPANA" como si fuera la primera partida: el jugador perdia
su campana sin que nadie le dijera nada. Estos tests atan la distincion entre
"no has jugado nunca" y "tenias algo y se ha roto".
"""

import io
import json
import os
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import campana  # noqa: E402


class TestPartidaDanada(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(prefix="tt_danada_")
        self.addCleanup(self.d.cleanup)
        os.environ["TRIPLETRIAD_DATA"] = self.d.name
        self.ruta = os.path.join(self.d.name, "campana.json")

    def _escribir(self, texto):
        with io.open(self.ruta, "w", encoding="utf-8") as f:
            f.write(texto)

    def test_sin_partida_no_hay_aviso(self):
        """La primera partida de un jugador nuevo no debe asustarlo con nada."""
        self.assertFalse(campana.partida_danada())
        self.assertIsNone(campana.aviso_partida_danada())

    def test_partida_valida_no_hay_aviso(self):
        estado = campana.nueva_campana("humano")
        campana.guardar(estado)
        self.assertFalse(campana.partida_danada())
        self.assertIsNone(campana.aviso_partida_danada())

    def test_json_corrupto_si_se_avisa(self):
        self._escribir("{ esto no es json")
        self.assertTrue(campana.partida_danada())
        aviso = campana.aviso_partida_danada()
        self.assertIsNotNone(aviso)
        self.assertIn(self.ruta, aviso, "el aviso debe decir DONDE esta el archivo")

    def test_json_vacio_si_se_avisa(self):
        self._escribir("")
        self.assertTrue(campana.partida_danada())

    def test_texto_que_no_es_json_sino_una_lista_si_se_avisa(self):
        self._escribir("[1, 2, 3]")
        # una lista SI es JSON valido: no es "danada" por sintaxis. Lo que pasa
        # despues (_migrar devuelve None) es otro asunto.
        self.assertFalse(campana.partida_danada())

    def test_el_juego_no_revienta_con_el_archivo_danado(self):
        """El aviso informa; el juego debe seguir arrancando."""
        self._escribir("{ roto")
        self.assertIsNone(campana.cargar())

    def test_borrar_el_archivo_danado_deja_el_juego_limpio(self):
        """El aviso dice que se puede renombrar o borrar: y debe ser verdad."""
        self._escribir("{ roto")
        self.assertTrue(campana.partida_danada())
        campana.borrar_partida()
        self.assertFalse(campana.partida_danada())
        estado = campana.nueva_campana("humano")
        campana.guardar(estado)
        self.assertIsNotNone(campana.cargar())


if __name__ == "__main__":
    unittest.main()