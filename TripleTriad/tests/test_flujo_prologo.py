"""Tests de integración del prologo: que main.py lo ejecute en el orden
correcto y que el estado narrativo quede marcado al entrar en campaña.

No renderizan: verifican el cableado leyendo el código de main, que es lo
que se rompió la primera vez que se toco el flujo.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests")
)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import campana
import inspect
import main
import prologo

CODIGO = {}
for nombre in ("main.py", "prologo.py"):
    with open(os.path.join(RAIZ, nombre), encoding="utf-8") as fh:
        CODIGO[nombre] = fh.read()


class TestFlujoDeMain(unittest.TestCase):
    def test_el_prologo_existe_y_es_awaitable(self):
        self.assertTrue(inspect.iscoroutinefunction(main._prologo))

    def test_el_prologue_ocurre_antes_de_elegir_faccion(self):
        """La biblia pide PROLOGO -> DESPERTAR -> APERTURA_FACCION -> CAPITULOS."""
        fuente = inspect.getsource(main._nueva_campana)
        i_prologo = fuente.index("_prologo")
        i_faccion = fuente.index("elegir_faccion")
        self.assertLess(i_prologo, i_faccion,
                        "la faccion se esta eligiendo antes del prologo")

    def test_el_prologo_marca_el_bandera(self):
        fuente = inspect.getsource(main._nueva_campana)
        self.assertIn("marcar_prologo_visto", fuente)

    def test_la_partida_nace_con_el_mazo_debil_del_mundo_fantastico(self):
        """El prologue no deja las legendarias en la partida del jugador."""
        fuente = inspect.getsource(main._nueva_campana)
        # el mazo se arma concreens.armar_mazo (mazos normales), no con el tutorial
        self.assertNotIn("mazo_tutorial", fuente)
        self.assertIn("armar_mazo", fuente)

    def test_el_duelo_ocurre_dentro_del_prologo(self):
        fuente = inspect.getsource(main._prologo)
        self.assertIn("partida(", fuente)
        self.assertIn("mazo_tutorial", fuente)
        self.assertIn("mazo_rival_rajoy", fuente)


class TestOrdenDeLasEscenas(unittest.TestCase):
    """El orden real de reproduccion, tal como lo invoca main._prologo."""

    def _orden_de_main(self):
        fuente = inspect.getsource(main._prologo)
        orden = []
        for nombre in ("escenas_pre_duelo", "escenas_post_duelo",
                       "escenas_carta_umbral", "escenas_transporte",
                       "escenas_despertar", "escenas_encuentro_hostil",
                       "escenas_nara", "escenas_cierre"):
            if f"prologo.{nombre}()" in fuente:
                orden.append(nombre)
        return orden

    def test_se_reproducen_todas(self):
        self.assertEqual(len(self._orden_de_main()), 8)

    def test_el_orden_es_el_del_plan(self):
        self.assertEqual(self._orden_de_main(), [
            "escenas_pre_duelo",
            "escenas_post_duelo",
            "escenas_carta_umbral",
            "escenas_transporte",
            "escenas_despertar",
            "escenas_encuentro_hostil",
            "escenas_nara",
            "escenas_cierre",
        ])

    def test_el_duelo_va_entre_pre_y_post(self):
        fuente = inspect.getsource(main._prologo)
        self.assertLess(fuente.index("escenas_pre_duelo"),
                        fuente.index("partida("))
        self.assertLess(fuente.index("partida("),
                        fuente.index("escenas_post_duelo"))


class TestEstadoNarrativoTrasElPrologo(unittest.TestCase):
    def test_partida_nueva_con_prologo_marcado(self):
        e = campana.nueva_campana("humano")
        campana.marcar_prologo_visto(e)
        self.assertTrue(campana.prologo_visto(e))

    def test_partida_sin_prologo_se_distingue(self):
        e = campana.nueva_campana("humano")
        self.assertFalse(campana.prologo_visto(e))

    def test_el_prologo_no_toca_las_variables_de_nara(self):
        """Ver el prologue no equivale a conocer a Nara: eso pasa en la campaña."""
        e = campana.nueva_campana("humano")
        campana.marcar_prologo_visto(e)
        self.assertEqual(campana.confianza_nara(e), 0)
        self.assertEqual(campana.conocimiento_umbral(e), 0)


class TestInfoDelDuelo(unittest.TestCase):
    def test_info_tiene_la_forma_que_espera_partida(self):
        info = prologo.info_duelo_prologo()
        for campo in ("bando", "nombre", "titulo_duelo", "entrada", "dificultad"):
            self.assertIn(campo, info)
        self.assertEqual(info["nombre"], "Juan Rajoy")
        self.assertEqual(info["bando"], "humano")
        self.assertEqual(info["dificultad"], 0)

    def test_no_es_un_nodo_de_campana(self):
        """El tutorial no puede aparecer en el mapa ni avanzar el progreso."""
        self.assertEqual(prologo.info_duelo_prologo()["nodo"], "prologo")
        self.assertNotIn("prologo", campana.NODOS)
        self.assertNotIn("prologo", campana.NODOS_MINI)


if __name__ == "__main__":
    unittest.main()
