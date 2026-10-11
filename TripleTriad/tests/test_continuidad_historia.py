"""La derrota no avanza el relato y la revancha conserva su identidad."""
import os
import sys
import tempfile
import unittest

os.environ.setdefault("TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tt_continuidad"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import campana
import cinematicas
import facciones
import narrativa


class TestContinuidad(unittest.TestCase):
    def test_derrotas_no_reproducen_consecuencias_de_victoria(self):
        for faccion in facciones.orden_facciones():
            estado = campana.nueva_campana(faccion)
            for nodo in narrativa.NARRATIVA:
                info = campana.info_duelo(estado, nodo)
                derrota = {e["texto"] for e in cinematicas.escenas_posterior(info, False)}
                consecuencias = {e["texto"] for e in narrativa.posterior_nodo(nodo)}
                self.assertFalse(derrota & consecuencias, (faccion, nodo))
                victoria = {e["texto"] for e in cinematicas.escenas_posterior(info, True)}
                self.assertTrue(consecuencias <= victoria)

    def test_revancha_conserva_nombre_y_retrato_en_ambas_ramas(self):
        for faccion in facciones.orden_facciones():
            for rama in ("aldea", "ruinas"):
                for indice, origen in enumerate(("senda", rama)):
                    estado = campana.nueva_campana(faccion)
                    estado.update(eleccion=rama, revancha=indice)
                    antes = campana.info_duelo(estado, origen)
                    despues = campana.info_duelo(estado, "asalto")
                    self.assertEqual((antes["nombre"], antes["retrato"], antes["bando"]),
                                     (despues["nombre"], despues["retrato"], despues["bando"]))
                    escenas, _ = cinematicas.escenas_nodo(despues)
                    presentacion = next(e for e in escenas if e.get("hablante") == despues["nombre"])
                    self.assertEqual(presentacion["retrato"], antes["retrato"])


if __name__ == "__main__":
    unittest.main()
