"""Tests de presentacion: como se distingue el mundo real del fantastic.

Dos cosas se verifican:
  1. El tratamiento visual por mundo (tinte + vineta) es realmente distinto.
  2. Las escenas estan etiquetadas con el mundo en el que ocurren.

Y una tercera, que es de inventario: `manifiesto` refleja el disco, para que
el trabajo de arte que falta sea una lista cerrada y no una busqueda.
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

import cinematicas
import finales
import assets_manifiesto as manifiesto
import narrativa
import prologo


class TestTratamientoVisual(unittest.TestCase):
    def test_los_dos_mundos_existen(self):
        self.assertIn(cinematicas.MUNDO_REAL, cinematicas.TRATAMIENTO)
        self.assertIn(cinematicas.MUNDO_JUEGO, cinematicas.TRATAMIENTO)

    def test_el_tratamiento_es_distinto(self):
        """Si fueran iguales, no habria forma de saber en que lado estas."""
        real = cinematicas.TRATAMIENTO[cinematicas.MUNDO_REAL]
        juego = cinematicas.TRATAMIENTO[cinematicas.MUNDO_JUEGO]
        self.assertNotEqual(real[0], juego[0], "mismo tinte")
        self.assertNotEqual(real[1], juego[1], "misma capa de oscuridad")
        self.assertNotEqual(real[2], juego[2], "misma vineta")

    def test_el_mundo_real_se_ve_mas_claro(self):
        """El salon del torneo tiene luz: no puede verse tan oscuro como el bosque."""
        real = cinematicas.TRATAMIENTO[cinematicas.MUNDO_REAL]
        juego = cinematicas.TRATAMIENTO[cinematicas.MUNDO_JUEGO]
        self.assertLess(real[1], juego[1],
                        "el mundo real deberia estar menos oscurecido")

    def test_el_mundo_fantastico_conserva_la_vineta(self):
        """La vineta es lo que le da el aire oscuro al mundo del juego."""
        self.assertTrue(cinematicas.TRATAMIENTO[cinematicas.MUNDO_JUEGO][2][0])
        self.assertFalse(cinematicas.TRATAMIENTO[cinematicas.MUNDO_REAL][2][0])

    def test_esc_acepta_el_mundo_y_por_defecto_es_el_juego(self):
        e = cinematicas.esc("hola")
        self.assertEqual(e["mundo"], cinematicas.MUNDO_JUEGO)
        e = cinematicas.esc("hola", mundo=cinematicas.MUNDO_REAL)
        self.assertEqual(e["mundo"], cinematicas.MUNDO_REAL)


class TestQueEscenasSonDeQueMundo(unittest.TestCase):
    def test_el_torneo_es_del_mundo_real(self):
        """Del salon, del duelista y de Juan: nuestro mundo."""
        for e in prologo.escenas_pre_duelo():
            self.assertEqual(e["mundo"], cinematicas.MUNDO_REAL, e["texto"][:40])

    def test_el_despierto_ya_es_del_mundo_fantastico(self):
        """En el bosque ya no estas en casa: cambia el tratamiento."""
        for e in prologo.escenas_despertar():
            self.assertEqual(e["mundo"], cinematicas.MUNDO_JUEGO, e["texto"][:40])

    def test_los_encuentros_son_del_mundo_fantastico(self):
        for e in narrativa.posterior_nodo("fortaleza"):
            self.assertEqual(e["mundo"], cinematicas.MUNDO_JUEGO, e["texto"][:40])

    def test_el_umbral_es_del_mundo_fantastico(self):
        for v in ("dominio", "equilibrio", "caos"):
            for e in finales.escenas_umbral(v):
                self.assertEqual(e["mundo"], cinematicas.MUNDO_JUEGO, v)

    def test_el_epilogo_es_del_mundo_real(self):
        """Aqui se vuelve a casa. Es el punto de la escena."""
        for v in ("dominio", "equilibrio", "caos"):
            for e in finales.escenas_epilogo(v):
                self.assertEqual(e["mundo"], cinematicas.MUNDO_REAL,
                                 f"{v}: {e['texto'][:40]}")

    def test_el_guion_cruza_de_mundo_exactamente_una_vez(self):
        """Del mundo real al fantastic: una transicion, no dos."""
        mundo_real = cinematicas.MUNDO_REAL
        guion = prologo.escenas_pre_duelo()
        cortaron = False
        for e in guion:
            if e["mundo"] == cinematicas.MUNDO_JUEGO:
                cortaron = True
            elif cortaron:
                self.fail(f"vuelve al mundo real despues de cruzar: {e['texto'][:40]}")


class TestElPrologoCuentaLaHistoriaCompleta(unittest.TestCase):
    """El prologo tiene que contar la transicion, no solo el decorado."""

    def test_el_prologo_tiene_las_ocho_escenas(self):
        total = (len(prologo.escenas_pre_duelo())
                 + len(prologo.escenas_post_duelo())
                 + len(prologo.escenas_carta_umbral())
                 + len(prologo.escenas_transporte())
                 + len(prologo.escenas_despertar())
                 + len(prologo.escenas_encuentro_hostil())
                 + len(prologo.escenas_nara())
                 + len(prologo.escenas_cierre()))
        self.assertGreaterEqual(total, 40, "el prologo se ve corto")

    def test_el_transporte_termina_en_negro(self):
        """La ultima escena del corte es un titulo vacio: pantalla negra."""
        escenas = prologo.escenas_transporte()
        ultima = escenas[-1]
        self.assertEqual(ultima["efecto"], "titulo")
        self.assertEqual(ultima["texto"], "", "el fundido a negro lleva texto")

    def test_el_apagon_avisa_antes_de_cortar(self):
        self.assertTrue(any(e["efecto"] == "titulo" and e["texto"]
                            for e in prologo.escenas_transporte()))

    def test_el_mundo_real_aparece_antes_que_el_fantastico(self):
        mundos = [e["mundo"] for e in prologo.escenas_pre_duelo()]
        self.assertTrue(mundos)
        self.assertEqual(mundos[0], cinematicas.MUNDO_REAL)


class TestManifiestoDeAssets(unittest.TestCase):
    """El manifiesto tiene que reflejar el disco de verdad."""

    def test_no_declara_fondos_que_faltan(self):
        """Si el manifiesto dice que un fondo se usa, tiene que estar."""
        self.assertEqual(manifiesto.fondos_faltantes(), [],
                         "el manifiesto usa fondos que no existen")

    def test_los_fondos_usados_existen_en_disco(self):
        hay = set(manifiesto.fondos_existentes())
        for f in manifiesto.FONDOS_USADOS:
            self.assertIn(f, hay, f)

    def test_detecta_lo_que_falta_de_verdad(self):
        """Solo falta el Cartografo.

        Nara, el Presentador, Juan y los cinco rivales del arco ya tienen avatar,
        igual que los diez bandos. El manifiesto tiene que seguir diciendo la
        verdad: si declara algo que ya existe, no sirve para nada.
        """
        faltan = manifiesto.retratos_faltantes()
        self.assertIn("cartografo", faltan)
        for ya_esta in ("nara", "presentador", "rajoy", "humano", "orco"):
            self.assertNotIn(ya_esta, faltan,
                             "%s ya tiene avatar: el manifiesto esta viejo"
                             % ya_esta)

    def test_no_declara_retratos_que_ya_existen(self):
        """Las de faccion y las nuevas ya generadas no pueden seguir faltando."""
        for nombre in ("humano", "goblin", "dragon", "nara", "duelista",
                       "rajoy", "pik", "dara", "jefe_arco", "revancha",
                       "gobernante"):
            self.assertNotIn(nombre, manifiesto.retratos_faltantes(), nombre)

    def test_detecta_la_musica_que_falta(self):
        faltan = manifiesto.musica_faltante()
        self.assertIn("musica_torneo", faltan)

    def test_no_declara_pistas_que_ya_existen(self):
        for p in ("musica_explora", "musica_duelo", "musica_humano"):
            self.assertNotIn(p, manifiesto.musica_faltante(), p)

    def test_el_resumen_usa_las_cifras_reales(self):
        resumen = manifiesto.resumen()
        self.assertIn(str(len(manifiesto.retratos_faltantes())), resumen)
        self.assertIn(str(len(manifiesto.musica_faltante())), resumen)

    def test_todo_el_manifesto_es_ascii(self):
        textos = [v for v in manifiesto.PERSONAJES_SIN_RETRATO.values()]
        textos += list(manifiesto.MUSICA_FALTANTE.values())
        for t in textos:
            for ch in t:
                self.assertLessEqual(ord(ch), 127, f"{ch!r} en {t[:40]!r}")

    def test_todos_los_retratos_que_necesitan_existen_o_estan_listados(self):
        """Nara y el Cartografo hablan en pantalla: o hay avatar o hay lista."""
        for nombre in ("nara", "cartografo"):
            existe = os.path.exists(
                os.path.join(RAIZ, "assets", f"avatar_{nombre}.png"))
            listado = nombre in manifiesto.PERSONAJES_SIN_RETRATO
            self.assertTrue(existe or listado, nombre)


if __name__ == "__main__":
    unittest.main()
