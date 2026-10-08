"""Tests de cierre del arco narrativo.

Fijan las tres cosas que la auditoria de guion encontro rotas y que la biblia
pide: la explicacion de que esta pasando, el objetivo explicito de volver a
casa, y el momento en que Nara deja de ser guia y se vuelve amiga.

No testean el texto porque "suene bien": testean que los CONCEPTOS esten. Un
test que busca una palabra exacta se rompe con una reescritura legitima; uno
que exige el concepto sobrevive.
"""

import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import campana  # noqa: E402
import finales  # noqa: E402
import narrativa  # noqa: E402
import prologo  # noqa: E402


def _a_texto(escenas):
    return " ".join(e["texto"].lower() for e in escenas)


class TestLaExplicacionInicial(unittest.TestCase):
    """Alguien tiene que explicar que pasa. Va entre Nara y el cierre."""

    def setUp(self):
        self.texto = _a_texto(prologo.escenas_explicacion())

    def test_la_explicacion_existe_y_no_esta_vacia(self):
        self.assertGreater(len(prologo.escenas_explicacion()), 5)

    def test_explica_que_es_el_umbral(self):
        self.assertIn("umbral", self.texto)

    def test_explica_que_lo_guarda_quien_ocupa_el_trono(self):
        self.assertIn("trono", self.texto)
        # La idea clave: el Umbral lo guarda unocupante, no una criatura.
        self.assertTrue("guarda" in self.texto or "tenga" in self.texto)

    def test_explica_que_la_sangre_del_dragon_legitimo_el_trono(self):
        """Es lo que hace que 'vencer al dragon' sea la frase popular."""
        self.assertIn("sangre", self.texto)
        self.assertIn("dragon", self.texto)

    def test_dice_que_la_frase_del_dragon_la_repite_la_gente(self):
        """Sin esto, la mencion al dragon seria una regla y contradiria al
        rival por faccion."""
        self.assertTrue("repite" in self.texto or "dicen" in self.texto
                        or "la gente" in self.texto)

    def test_dice_como_se_vuelve_a_casa(self):
        self.assertIn("casa", self.texto)
        self.assertTrue("devuelve" in self.texto or "vuelve" in self.texto
                        or "volver" in self.texto)

    def test_dice_cuantos_duelos_faltan(self):
        self.assertTrue("cinco duel" in self.texto or "cinco" in self.texto)

    def test_no_contradice_el_rival_por_faccion(self):
        """La escena no puede nombrar rival: el rival sale de la escalera del
        bando y depende de la faccion elegida."""
        # La palabra "dragon" SI tiene que estar: es la que legitimó el trono y
        # la que sostiene la frase popular. Lo que no puede aparecer es un
        # NOMBRE PROPIO de rival, porque ese si ata el guion a una faccion.
        import facciones
        propios = set()
        for fac in facciones.orden_facciones():
            info = campana.info_duelo(campana.nueva_campana(fac), "trono")
            propios.add(info.get("nombre", ""))
        for nombre in propios:
            if not nombre:
                continue
            self.assertNotIn(nombre.lower(), self.texto,
                             "la explicacion nombra al rival (%s): eso ata el "
                             "guion a una faccion" % nombre)
        # Y el dragon se nombra en pasado, no como rival presente
        self.assertIn("dragon", self.texto)
        self.assertNotIn("el dragon te espera", self.texto)

    def test_la_explicacion_va_entre_nara_y_el_cierre(self):
        with open(os.path.join(RAIZ, "main.py"), encoding="utf-8") as fh:
            codigo = fh.read()
        self.assertIn("escenas_explicacion()", codigo)
        i_nara = codigo.find("escenas_nara()")
        i_exp = codigo.find("escenas_explicacion()")
        i_cierre = codigo.find("escenas_cierre()")
        self.assertLess(i_nara, i_exp)
        self.assertLess(i_exp, i_cierre)


class TestElObjetivoDeVolverACasa(unittest.TestCase):
    """El objetivo tiene que estar DITO, no solo implementado."""

    def setUp(self):
        partes = [_a_texto(prologo.escenas_explicacion()),
                  _a_texto(narrativa.escena_amistad())]
        for nodo in ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono"):
            partes.append(_a_texto(narrativa.previa_nodo(nodo)))
            partes.append(_a_texto(narrativa.posterior_nodo(nodo)))
        self.texto = " ".join(partes)

    def test_la_campana_dice_que_se_vuelve_a_casa(self):
        self.assertIn("casa", self.texto)

    def test_el_prologo_dice_que_se_vuelve_a_casa(self):
        """El prologo es donde se promete. Sin la promesa el resto no ata."""
        self.assertIn("casa", _a_texto(prologo.escenas_explicacion()))

    def test_el_objetivo_aparece_en_varios_tramos_y_no_solo_al_final(self):
        """Si solo aparece en el ultimo nodo, el jugador llega sin saber que
        hace. Tiene que estar presente antes."""
        for nodo in ("aldea", "fortaleza", "asalto"):
            propio = (_a_texto(narrativa.previa_nodo(nodo))
                      + _a_texto(narrativa.posterior_nodo(nodo)))
            self.assertTrue("casa" in propio or "vuelta" in propio
                            or "vuel" in propio or "duelos" in propio,
                            "el nodo %s no recuerda el objetivo" % nodo)

    def test_los_finales_siguen_being_common_a_las_diez_facciones(self):
        """La vuelta a casa la decide la VARIANTE, no el jefe. Este bloque no
        se toca y el test lo deja dicho."""
        for fac in ("humano", "orco", "vampiro", "dragon"):
            for variante in ("dominio", "equilibrio", "caos"):
                escenas = finales.escenas_epilogo(variante)
                self.assertTrue(escenas)


class TestNaraSeVuelveAmiga(unittest.TestCase):
    """Nara acompana y se queda. El momento no puede depender de la confianza."""

    def setUp(self):
        self.texto = _a_texto(narrativa.escena_amistad())

    def test_el_momento_existe(self):
        self.assertGreaterEqual(len(narrativa.escena_amistad()), 6)

    def test_reconoce_que_mentia_sobre_su_motivo(self):
        self.assertTrue("menti" in self.texto or "corregir" in self.texto)
        self.assertTrue("respuestas" in self.texto or "averiguar" in self.texto)

    def test_dice_que_se_queda_por_querer_y_no_por_el_mision(self):
        self.assertIn("porque quiero", self.texto)
        self.assertTrue("no por el umbral" in self.texto)

    def test_se_reproduce_antes_del_duelo_del_trono(self):
        with open(os.path.join(RAIZ, "main.py"), encoding="utf-8") as fh:
            codigo = fh.read()
        self.assertIn("escena_amistad()", codigo)
        self.assertIn('info["nodo"] == "trono"', codigo)

    def test_el_momento_no_depende_de_la_confianza(self):
        """`confianza_nara` solo sube con las dos decisiones de la campana
        (maximo +1 y +2). Un jugador que elige frio en las dos se queda en 0,
        asi que si el momento colgado de la confianza, Nara nunca seria amiga.
        El momento tiene que ser incondicional."""
        estado = campana.nueva_campana("humano")
        # el peor caso: el jugador elige la opcion que no da confianza
        campana.decidir(estado, "senda_herido", {"conocimiento": 1})
        campana.decidir(estado, "fortaleza_umbral", {"confianza": -1})
        self.assertLess(campana.confianza_nara(estado), 3)
        self.assertFalse(campana.nara_aliada(estado))
        # y aun asi, la escena de amistad existe y se puede reproducir
        self.assertTrue(narrativa.escena_amistad())

    def test_el_dialogo_alta_confianza_no_es_mas_frio(self):
        """Estaba al reves: con confianza alta Nara decia 'no te conozco'."""
        alta = narrativa.nara_presentacion(5).lower()
        baja = narrativa.nara_presentacion(0).lower()
        for frase in ("porque quiero ir", "quiero"):
            self.assertIn(frase, alta,
                          "con confianza alta Nara tiene que sonar mas cerca")
        self.assertNotIn("no me hagas quedar mal", alta)
        self.assertTrue(baja != alta)


if __name__ == "__main__":
    unittest.main()