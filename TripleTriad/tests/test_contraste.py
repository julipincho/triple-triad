"""G2: el contraste se mide sobre los fondos REALES, no sobre una tabla.

`tools/auditar_contraste.py` compone cada pantalla de verdad (fondo, capas,
vineta y paneles), la vuelve a pintar sin una sola letra, y mide el color que
queda detras de cada texto. Aqui se fija ese suelo para que no retroceda.

La metrica se autocomprueba contra valores conocidos de WCAG: si la formula se
equivoca, este test lo detecta antes de que sirva para dar un color por bueno.
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

RUTA_AUDITOR = os.path.join(RAIZ, "tools", "auditar_contraste.py")


def _cargar_auditor():
    """Carga el auditor como modulo (tools/ no es un paquete)."""
    tmp = tempfile.TemporaryDirectory(prefix="tt_auditor_")
    os.environ["TRIPLETRIAD_DATA"] = tmp.name
    spec = importlib.util.spec_from_file_location("auditar_contraste", RUTA_AUDITOR)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["auditar_contraste"] = mod
    spec.loader.exec_module(mod)
    # El temporal vive mientras dure el proceso del test.
    mod._TMP = tmp
    return mod


class TestLaMetricaEsFiel(unittest.TestCase):
    """Antes de fiar una cifra, comprobar que la cifra es correcta."""

    @classmethod
    def setUpClass(cls):
        cls.aud = _cargar_auditor()

    def test_blanco_sobre_negro_es_el_maximo_de_wcag(self):
        self.assertAlmostEqual(self.aud.contraste((255, 255, 255), (0, 0, 0)), 21.0,
                               places=2)

    def test_un_color_contra_si_mismo_es_uno(self):
        self.assertAlmostEqual(self.aud.contraste((120, 60, 30), (120, 60, 30)), 1.0,
                               places=6)

    def test_la_luminancia_responde_al_orden_correcto(self):
        """Mas claro = mas luminancia. Si esto falla, la formula esta mal."""
        oscuro = self.aud.luminancia((10, 10, 10))
        medio = self.aud.luminancia((128, 128, 128))
        claro = self.aud.luminancia((250, 250, 250))
        self.assertLess(oscuro, medio)
        self.assertLess(medio, claro)

    def test_contraste_es_simetrico(self):
        a, b = (238, 236, 224), (18, 19, 28)
        self.assertAlmostEqual(self.aud.contraste(a, b), self.aud.contraste(b, a),
                               places=9)

    def test_el_adorno_no_cuenta_como_texto(self):
        """Un guion que une nodos no es texto que el jugador lea."""
        self.assertFalse(self.aud._es_legible("-"))
        self.assertFalse(self.aud._es_legible("?"))
        self.assertFalse(self.aud._es_legible("   "))
        self.assertFalse(self.aud._es_legible("=="))
        # "+3 mas" SI es informacion: lleva una cifra que el jugador lee.
        self.assertTrue(self.aud._es_legible("+3 mas"))
        self.assertTrue(self.aud._es_legible("POSEIDA"))
        self.assertTrue(self.aud._es_legible("COMUN"))


class TestContrasteMedidoSobreFondoReal(unittest.TestCase):
    """El suelo medido. Si esto baja, alguien rompio la legibilidad."""

    CORTE = 4.5

    #: Pantallas que se miden. Las mas densas en texto y las que tienen arte
    #: detras: son las que fallan cuando algo se rompe.
    PANTALLAS = ("menu", "mapa_campana", "coleccion", "tienda", "ajustes",
                 "recompensa", "elegir_rama", "draft", "diario_dialogos")

    @classmethod
    def setUpClass(cls):
        cls.aud = _cargar_auditor()
        import pygame

        from ui import ALTO, ANCHO

        pygame.init()
        cls.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        cls.resultados = cls.aud.auditar(cls.pantalla)

    def test_se_midio_al_menos_nueve_pantallas(self):
        """Si el auditor deja de capturar rects, esto avisa antes de dar verde."""
        nombres = {r["pantalla"] for r in self.resultados}
        faltan = set(self.PANTALLAS) - nombres
        self.assertFalse(faltan, f"el auditor no midio: {sorted(faltan)}")

    def test_toda_pantalla_supera_el_corte_por_media(self):
        Fallos = []
        for r in self.resultados:
            if not r["cumple_normal"]:
                Fallos.append(
                    f"{r['pantalla']}: {r['contraste_minimo']} < {self.CORTE} "
                    f"({r['peores'][:2]})")
        self.assertFalse(Fallos, "contraste insuficiente:\n  " + "\n  ".join(Fallos))

    def test_el_texto_mas_degradado_esta_identificado(self):
        """Un minimo sin localizar no sirve: debe decir color, sitio y texto."""
        for r in self.resultados:
            if r["peores"]:
                peor = r["peores"][0]
                self.assertIn("color", peor)
                self.assertIn("rect", peor)
                self.assertIn("texto", peor)
                self.assertTrue(peor["texto"], "un peor caso sin texto no es localizable")

    def test_no_queda_el_gris_suelto_que_fallaba_el_contraste(self):
        """Regresion concreta y.localizada.

        Las facciones sin final conseguido en la pantalla de finales se
        apagaban con (90, 90, 96), un gris elegido a ojo: daba 2.8:1 y no era un
        color del sistema. Ahora usan TEXTO_TENUE. Este test ata ese cambio a un
        sitio concreto, para que no vuelva por donde vino.
        """
        import io

        with io.open(os.path.join(RAIZ, "pantallas.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        self.assertNotIn("(90, 90, 96)", fuente,
                         "vuelve el gris suelto que daba 2.8:1 en la pantalla "
                         "de finales; usa TEXTO_TENUE")


if __name__ == "__main__":
    unittest.main()