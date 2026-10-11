"""G9: los recorridos integrados, como test de suite.

`tools/recorridos_g9.py` se ejecuta a mano y devuelve codigo de salida. Aqui se
comprueba lo mismo pero dentro de la suite, para que un recorrido roto (perdida
de progreso, cobro doble, final que no llega) pare el build y no se discover
en una revision posterior.

Se usan datos aislados por prueba: nada toca la partida real.
"""

import importlib.util
import os
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

from ui import ALTO, ANCHO  # noqa: E402

RUTA = os.path.join(RAIZ, "tools", "recorridos_g9.py")


def _cargar():
    tmp = tempfile.TemporaryDirectory(prefix="tt_g9_test_")
    os.environ["TRIPLETRIAD_DATA"] = tmp.name
    spec = importlib.util.spec_from_file_location("recorridos_g9", RUTA)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["recorridos_g9"] = mod
    spec.loader.exec_module(mod)
    mod._TMP = tmp
    return mod


class TestRecorridosIntegrados(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _cargar()
        pygame.init()
        cls.screen = pygame.display.set_mode((ANCHO, ALTO))

    def _correr(self, nombre):
        for etiqueta, fn in self.mod.RECORRIDOS:
            if etiqueta == nombre:
                return fn() or []
        self.fail(f"no hay recorrido llamado {nombre!r}")

    def test_nuevo_jugador(self):
        self.assertEqual(self._correr("nuevo jugador"), [])

    def test_reanudacion(self):
        self.assertEqual(self._correr("reanudacion"), [])

    def test_derrota_y_reintento(self):
        self.assertEqual(self._correr("derrota y reintento"), [])

    def test_abandonar(self):
        self.assertEqual(self._correr("abandonar"), [])

    def test_compra_y_equipar(self):
        self.assertEqual(self._correr("compra y equipar"), [])

    def test_mejorar_carta(self):
        self.assertEqual(self._correr("mejorar carta"), [])

    def test_hasta_el_final(self):
        self.assertEqual(self._correr("hasta el final"), [])

    def test_todos_los_recorridos_siguen_declarados(self):
        """Si alguien quita un recorrido del listado, este test lo delata."""
        esperados = {"nuevo jugador", "reanudacion", "derrota y reintento",
                     "abandonar", "compra y equipar", "mejorar carta",
                     "hasta el final"}
        self.assertEqual({n for n, _f in self.mod.RECORRIDOS}, esperados)


if __name__ == "__main__":
    unittest.main()