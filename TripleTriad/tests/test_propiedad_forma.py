"""G2: la propiedad de una carta se lee por FORMA, no solo por color.

El criterio de aceptacion pide "propio/rival y captura prevista distinguibles sin
depender del color". La comprobacion aqui es objetiva: se convierte cada marca
a su SILUETA EN GRIS y se comparan. Si las tres fueran iguales en gris, la
propiedad dependeria solo del color, y un jugador con daltonismo (o en una
captura en blanco y negro) no distinguiria su carta de la del rival.
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

import cartas  # noqa: E402
import mazos  # noqa: E402

RUTA = os.path.join(RAIZ, "tools", "verificar_propiedad.py")


def _cargar():
    tmp = tempfile.TemporaryDirectory(prefix="tt_prop_test_")
    os.environ["TRIPLETRIAD_DATA"] = tmp.name
    spec = importlib.util.spec_from_file_location("verificar_propiedad", RUTA)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["verificar_propiedad"] = mod
    spec.loader.exec_module(mod)
    mod._TMP = tmp
    return mod


class TestPropiedadPorForma(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = _cargar()
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def _siluetas(self):
        base = mazos.HUMANOS[0]
        etiquetas = (("T", "PROPIA"), ("C", "RIVAL"), (None, "LIBRE"))
        sups = [cartas.crear(base, dueno=d, escala=2) for d, _e in etiquetas]
        w, h = sups[0].get_size()
        caja = (h - 20, w - 20, 16, 16)
        # El arco del borde redondeado esta en las tres: se resta, para que lo
        # que compare sea solo la FORMA de la marca.
        comunes = self.mod.siluetas_comunes(sups, caja)
        return {e: self.mod.silueta(sup, caja, comunes)
                for sup, (_d, e) in zip(sups, etiquetas)}

    def test_las_tres_marcas_son_distintas_en_gris(self):
        """El criterio literal: distinguibles sin depender del color."""
        s = self._siluetas()
        self.assertNotEqual(s["PROPIA"], s["RIVAL"],
                            "propia y rival se distinguen solo por color")
        self.assertNotEqual(s["PROPIA"], s["LIBRE"],
                            "propia y libre se distinguen solo por color")
        self.assertNotEqual(s["RIVAL"], s["LIBRE"],
                            "rival y libre se distinguen solo por color")

    def test_la_marca_deja_una_senal_visible(self):
        """Ni la marca ni su ausencia pueden pasar desapercibidas.

        PROPIA (cuadrado) y RIVAL (rombo) tienen base oscura: tienen que verse.
        LIBRE no lleva base: su senal ES no tenerla, y eso tambien tiene que
        distingurse, asi que ahi lo que se comprueba es que esta vacia.
        """
        s = self._siluetas()
        for etiqueta in ("PROPIA", "RIVAL"):
            unos = sum(sum(f) for f in s[etiqueta])
            total = len(s[etiqueta]) * len(s[etiqueta][0])
            self.assertGreater(unos, total * 0.15,
                               f"la marca de {etiqueta} es casi invisible en gris")
            self.assertLess(unos, total * 0.95,
                            f"la marca de {etiqueta} tapa todo el recuadro")
        libres = sum(sum(f) for f in s["LIBRE"])
        self.assertEqual(libres, 0,
                         "una carta libre no deberia llevar base de propiedad")


if __name__ == "__main__":
    unittest.main()