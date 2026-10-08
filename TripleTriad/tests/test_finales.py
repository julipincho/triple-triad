"""Tests de los tres finales y el regreso al mundo real.

La regla que mas importa: `campana.FINALES` (los 30 finales por faccion) NO se
tocaron. Son el final del mundo fantastic. Lo nuevo es la segunda capa, comun
a las diez facciones: la apertura del Umbral y el epilogo en nuestro mundo.
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
import finales
import facciones

VARIANTES = ("dominio", "equilibrio", "caos")


class TestLosTresFinales(unittest.TestCase):
    def test_existen_las_tres_variantes(self):
        for v in VARIANTES:
            self.assertIn(v, finales.UMBRAL, f"{v} sin Umbral")
            self.assertIn(v, finales.EPILOGO, f"{v} sin epilogo")

    def test_cada_umbral_tiene_titulo_y_lineas(self):
        for v in VARIANTES:
            self.assertTrue(finales.UMBRAL[v]["titulo"].strip(), v)
            self.assertGreaterEqual(len(finales.UMBRAL[v]["lineas"]), 3, v)

    def test_cada_epilogo_tiene_titulo_y_lineas(self):
        for v in VARIANTES:
            self.assertTrue(finales.EPILOGO[v]["titulo"].strip(), v)
            self.assertGreaterEqual(len(finales.EPILOGO[v]["lineas"]), 3, v)

    def test_el_modulo_es_coherente(self):
        self.assertEqual(finales._validar(), [])

    def test_no_hay_lineas_vacias(self):
        for v in VARIANTES:
            for linea in finales.UMBRAL[v]["lineas"] + finales.EPILOGO[v]["lineas"]:
                self.assertTrue(linea.strip(), v)

    def test_umbral_y_epilogo_no_se_repiten(self):
        for v in VARIANTES:
            u = set(finales.UMBRAL[v]["lineas"])
            e = set(finales.EPILOGO[v]["lineas"])
            self.assertEqual(u & e, set(), f"{v}: linea repetida")

    def test_los_titulos_son_distintos(self):
        titulos = [finales.UMBRAL[v]["titulo"] for v in VARIANTES]
        titulos += [finales.EPILOGO[v]["titulo"] for v in VARIANTES]
        self.assertEqual(len(set(titulos)), 6)

    def test_variante_desconocida_no_rompe(self):
        self.assertTrue(finales.escenas_umbral("inventada"))
        self.assertTrue(finales.escenas_epilogo("inventada"))
        self.assertTrue(finales.titulo_umbral("inventada"))
        self.assertTrue(finales.musica_umbral("inventada"))
        self.assertTrue(finales.musica_epilogo("inventada"))


class TestElGiroDeCadaFinal(unittest.TestCase):
    """Lo que la biblia pide para cada uno de los tres finales."""

    def _unido(self, v):
        return " ".join(finales.UMBRAL[v]["lineas"] + finales.EPILOGO[v]["lineas"]).lower()

    def test_dominio_te_devuelve_con_algo(self):
        texto = self._unido("dominio")
        self.assertIn("legendaria", texto, "dominio: falta la legendaria")
        self.assertIn("tuio" if False else "tuyo", texto,
                      "dominio: la carta deberia ser el rostro del duelista")

    def test_dominio_hay_algo_que_cruza_en_sentido_contrario(self):
        texto = " ".join(finales.UMBRAL["dominio"]["lineas"]).lower()
        self.assertIn("sentido contrario", texto)

    def test_equilibrio_no_se_entera_casi_nadie(self):
        texto = self._unido("equilibrio")
        self.assertIn("tres segundos", texto)
        self.assertIn("nara", texto.lower(),
                      "equilibrio: la expansion nueva deberia ser de Nara")

    def test_caos_rompe_el_umbral(self):
        texto = self._unido("caos")
        self.assertIn("rompe", texto)
        self.assertIn("se mueve", texto,
                      "caos: la carta del final deberia moverse sola")

    def test_los_tres_finals_difieren_en_el_umbral(self):
        for v in VARIANTES:
            for otro in VARIANTES:
                if v == otro:
                    continue
                self.assertNotEqual(set(finales.UMBRAL[v]["lineas"]),
                                    set(finales.UMBRAL[otro]["lineas"]),
                                    f"{v} y {otro}: Umbral identico")

    def test_los_tres_finals_difieren_en_el_epilogo(self):
        for v in VARIANTES:
            for otro in VARIANTES:
                if v == otro:
                    continue
                self.assertNotEqual(set(finales.EPILOGO[v]["lineas"]),
                                    set(finales.EPILOGO[otro]["lineas"]),
                                    f"{v} y {otro}: epilogo identico")


class TestEscenas(unittest.TestCase):
    def test_las_escenas_son_validas_para_el_reproductor(self):
        claves = {"texto", "hablante", "fondo", "retrato", "efecto", "musica",
             "color", "mundo"}
        for v in VARIANTES:
            for e in finales.escenas_umbral(v) + finales.escenas_epilogo(v):
                self.assertEqual(set(e), claves, v)
                self.assertTrue(e["texto"].strip(), v)

    def test_la_primera_escena_es_titulo(self):
        for v in VARIANTES:
            self.assertEqual(finales.escenas_umbral(v)[0]["efecto"], "titulo")
            self.assertEqual(finales.escenas_epilogo(v)[0]["efecto"], "titulo")

    def test_el_umbral_ocurre_en_el_fondo_umbral(self):
        for v in VARIANTES:
            for e in finales.escenas_umbral(v):
                self.assertEqual(e["fondo"], "umbral", v)

    def test_el_epilogo_ocurre_en_el_mundo_real(self):
        """El epilogo es de vuelta en nuestro mundo: no en el trono ni el bosque."""
        fondos = {"campamento", "campamento"}
        for v in VARIANTES:
            for e in finales.escenas_epilogo(v):
                self.assertIn(e["fondo"], fondos, v)

    def test_los_fondos_existen(self):
        for v in VARIANTES:
            for e in finales.escenas_umbral(v) + finales.escenas_epilogo(v):
                ruta = os.path.join(RAIZ, "assets", "fondos", f"{e['fondo']}.png")
                self.assertTrue(os.path.exists(ruta), f"{v}: {e['fondo']}")

    def test_la_devolucion_es_una_copia(self):
        primera = finales.escenas_umbral("caos")
        primera[0]["texto"] = "adulterado"
        self.assertNotEqual(finales.escenas_umbral("caos")[0]["texto"], "adulterado")


class TestLaMusicaDistingueLosMundos(unittest.TestCase):
    """El mundo real tiene que sonar distinto al fantastic."""

    def test_la_apertura_del_umbral_suena_distinta_en_cada_final(self):
        """El Umbral es un momento distinto segun como se abra."""
        pistas = [finales.musica_umbral(v) for v in VARIANTES]
        self.assertEqual(len(set(pistas)), 3,
                         f"dos finales comparten la musica del Umbral: {pistas}")

    def test_el_caos_deja_el_epilogo_inquieto(self):
        """Es el unico final del que se vuelve con algo roto."""
        self.assertEqual(finales.musica_epilogo("caos"), "musica_duelo")

    def test_el_equilibrio_suena_igual_antes_y_despues(self):
        """A proposito: en ese final no cambio nada, ni la musica."""
        self.assertEqual(finales.musica_umbral("equilibrio"),
                         finales.musica_epilogo("equilibrio"))

    def test_la_musica_existe(self):
        """Las pistas viven en assets/musica/, no en la raiz de assets/."""
        base = os.path.join(RAIZ, "assets", "musica")
        for v in VARIANTES:
            for clave in (finales.musica_umbral(v), finales.musica_epilogo(v)):
                existe = any(os.path.exists(os.path.join(base, clave + ext))
                             for ext in (".ogg", ".wav"))
                self.assertTrue(existe, f"{v}: falta la musica {clave}")

    def test_no_se_pide_un_sfx_como_si_fuera_musica(self):
        """`boss` y `menu` son efectos de sonido: no sirven de banda sonora."""
        for v in VARIANTES:
            for clave in (finales.musica_umbral(v), finales.musica_epilogo(v)):
                self.assertTrue(clave.startswith("musica_"),
                                f"{v}: {clave} no es una pista")


class TestLosFinalesPorFaccionNoCambiaron(unittest.TestCase):
    """Los 30 finales de campana son el final del mundo fantastic: intactos."""

    def test_siguen_habiendo_diez_facciones(self):
        self.assertEqual(set(campana.FINALES), set(facciones.orden_facciones()))

    def test_cada_faccion_sigue_teniendo_las_tres_variantes(self):
        for f in facciones.orden_facciones():
            self.assertEqual(set(campana.FINALES[f]), set(VARIANTES), f)

    def test_cada_final_tiene_titulo_y_lineas(self):
        for f in facciones.orden_facciones():
            for v in VARIANTES:
                datos = campana.FINALES[f][v]
                self.assertTrue(datos["titulo"].strip(), f"{f}/{v}")
                self.assertGreaterEqual(len(datos["lineas"]), 2, f"{f}/{v}")

    def test_la_variante_se_sigue_eligiendo_por_rendimiento(self):
        for estado, esperado in (
            ({"derrotas": 0, "mejor_racha": 5}, "dominio"),
            ({"derrotas": 2, "mejor_racha": 2}, "equilibrio"),
            ({"derrotas": 5, "mejor_racha": 1}, "caos"),
        ):
            self.assertEqual(campana.variante_final(estado), esperado)

    def test_final_de_sigue_devolviendo_la_variante_de_faccion(self):
        for f in facciones.orden_facciones():
            e = campana.nueva_campana(f)
            e["derrotas"], e["mejor_racha"] = 0, 5
            variante, titulo, lineas = campana.final_de(e)
            self.assertEqual(variante, "dominio")
            self.assertEqual(titulo, campana.FINALES[f]["dominio"]["titulo"])


class TestOrdenDeLaSecuenciaFinal(unittest.TestCase):
    """Fantastico -> Umbral -> mundo real. En ese orden, siempre."""

    def test_el_umbral_viene_despues_del_final_de_faccion(self):
        with open(os.path.join(RAIZ, "pantallas.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        i_faccion = fuente.index("cinematicas.escenas_final(titulo, lineas, faccion")
        i_umbral = fuente.index("finales.escenas_umbral(variante)")
        i_epilogo = fuente.index("finales.escenas_epilogo(variante)")
        self.assertLess(i_faccion, i_umbral)
        self.assertLess(i_umbral, i_epilogo)

    def test_el_epilogo_es_obligatorio(self):
        """No se puede saltar la parte que explica el final."""
        with open(os.path.join(RAIZ, "pantallas.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        i_umbral = fuente.index("finales.escenas_umbral(variante)")
        bloque = fuente[i_umbral:i_umbral + 260]
        self.assertIn("permitir_saltar=False", bloque,
                      "el Umbral se podria saltar")


class TestTextoAscii(unittest.TestCase):
    def test_todo_el_modulo_es_ascii(self):
        for v in VARIANTES:
            textos = [finales.UMBRAL[v]["titulo"], finales.EPILOGO[v]["titulo"]]
            textos += finales.UMBRAL[v]["lineas"] + finales.EPILOGO[v]["lineas"]
            for t in textos:
                for ch in t:
                    self.assertLessEqual(ord(ch), 127, f"{v}: {ch!r} en {t[:40]!r}")


class TestSinCiclos(unittest.TestCase):
    def test_finales_no_importa_campana(self):
        with open(os.path.join(RAIZ, "finales.py"), encoding="utf-8") as fh:
            for linea in fh:
                limpio = linea.strip()
                if limpio.startswith(("import ", "from ")):
                    self.assertNotIn(" campana", " " + limpio, limpio)


if __name__ == "__main__":
    unittest.main()
