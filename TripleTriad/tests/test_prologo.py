"""Tests del prologo: mazo del tutorial, contraste con el mundo fantastic,
estabilidad de las 5 legendarias y de las escenas."""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests")
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import campana
import mazos
import prologo
from reglas import rareza, total_carta

FUNCIONES_ESCENAS = (
    "escenas_pre_duelo",
    "escenas_post_duelo",
    "escenas_carta_umbral",
    "escenas_transporte",
    "escenas_despertar",
    "escenas_encuentro_hostil",
    "escenas_nara",
    "escenas_cierre",
)


class TestMazoTutorial(unittest.TestCase):
    def test_son_cinco_cartas_una_por_faccion(self):
        mazo = prologo.mazo_tutorial()
        self.assertEqual(len(mazo), 5)
        bandos = [c.bando for c in mazo]
        for bando in prologo.TUTORIAL_FACCIONES:
            self.assertEqual(bandos.count(bando), 1, f"falta una legendaria de {bando}")

    def test_todas_son_legendarias(self):
        for c in prologo.mazo_tutorial():
            self.assertEqual(rareza(c)[0], "LEGENDARIA", f"{c.nombre} no es legendaria")

    def test_es_la_mas_fuerte_de_su_faccion(self):
        """Cada una es la legendaria de mayor suma de su faccion."""
        for c in prologo.mazo_tutorial():
            propias = [x for x in getattr(mazos, {
                "humano": "HUMANOS", "elfo": "ELFOS", "vampiro": "VAMPIROS",
                "dragon": "DRAGONES", "goblin": "GOBLINS",
            }[c.bando]) if x.nombre == c.nombre]
            self.assertEqual(len(propias), 1, f"{c.nombre} no existe en su pool")
            mejor = prologo.mejor_legendaria(c.bando)
            self.assertEqual(mejor.nombre, c.nombre)

    def test_es_estable_entre_llamadas(self):
        primero = [c.nombre for c in prologo.mazo_tutorial()]
        for _ in range(4):
            self.assertEqual([c.nombre for c in prologo.mazo_tutorial()], primero)

    def test_no_altera_el_pool_original(self):
        """mazo_tutorial devuelve copias: el pool global queda intacto."""
        antes = prologo.mejor_legendaria("humano").nombre
        mazo = prologo.mazo_tutorial()
        mazo[0].nombre = " adulterado"
        self.assertEqual(prologo.mejor_legendaria("humano").nombre, antes)


class TestContrasteConMundoFantastico(unittest.TestCase):
    def test_el_mazo_fantastico_es_mas_debil(self):
        """El poder del mundo real no acompana al duelista."""
        tutorial = max(total_carta(c) for c in prologo.mazo_tutorial())
        for faccion in ("humano", "orco", "elfo", "goblin", "dragon"):
            inicial = max(total_carta(c) for c in campana.mazo_inicial(faccion))
            self.assertGreater(
                tutorial, inicial,
                f"el mazo inicial de {faccion} iguala al tutorial")

    def test_el_duelo_del_tutorial_es_ganable(self):
        """Juan no tiene legendarias: el duelo enseña mecánicas, no humilla."""
        rival = prologo.mazo_rival_rajoy()
        for c in rival:
            self.assertNotEqual(rareza(c)[0], "LEGENDARIA",
                                f"Juan tiene una legendaria: {c.nombre}")

    def test_ambos_mazos_tienen_cinco_cartas(self):
        """En el 3x3 cada bando coloca 5: las manos deben ser comparables."""
        self.assertEqual(len(prologo.mazo_tutorial()), 5)
        self.assertEqual(len(prologo.mazo_rival_rajoy()), 5)

    def test_el_duelista_parte_con_ventaja(self):
        """5 legendarias contra 5 comunes: el duelista gana si juega bien."""
        fuerza_tutorial = sum(total_carta(c) for c in prologo.mazo_tutorial())
        fuerza_rajoy = sum(total_carta(c) for c in prologo.mazo_rival_rajoy())
        self.assertGreater(fuerza_tutorial, fuerza_rajoy)

    def test_mazo_rajoy_es_estable(self):
        primero = [c.nombre for c in prologo.mazo_rival_rajoy()]
        for _ in range(4):
            self.assertEqual([c.nombre for c in prologo.mazo_rival_rajoy()], primero)


class TestRivalJuanRajoy(unittest.TestCase):
    def test_tiene_los_campos_que_pide_el_duelo(self):
        r = prologo.rival_rajoy()
        for campo in ("nombre", "titulo", "bando", "entrada", "win", "lose"):
            self.assertIn(campo, r)
            self.assertTrue(r[campo], f"campo {campo} vacio")

    def test_es_humano_y_no_se_enfrenta_a_si_mismo(self):
        r = prologo.rival_rajoy()
        self.assertEqual(r["bando"], "humano")

    def test_la_voz_es_suya_y_no_del_duelista(self):
        """Juan habla de 'tu' porque es el rival, no el protagonista."""
        r = prologo.rival_rajoy()
        self.assertNotIn("d)", r["win"])


class TestEscenas(unittest.TestCase):
    def test_todas_las_escenas_existen(self):
        for fn in FUNCIONES_ESCENAS:
            self.assertTrue(getattr(prologo, fn)(), f"{fn} devuelve vacio")

    def test_las_escenas_tienen_fondo_valido(self):
        for fn in FUNCIONES_ESCENAS:
            for e in getattr(prologo, fn)():
                fondo = e.get("fondo")
                if fondo:
                    ruta = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "assets", "fondos", f"{fondo}.png")
                    self.assertTrue(os.path.exists(ruta),
                                    f"{fn}: fondo inexistente {fondo}")

    def test_retratos_validos(self):
        """Facciones de bando o personajes con cara: los dos son retrato.

        Los personajes (rajoy, pik, nara) tienen su propio avatar generado, asi
        que no tienen que caer en una faccion.
        """
        import cinematicas
        permitidos = {"humano", "orco", "elfo", "goblin", "hombre_lobo", "vampiro",
                      "dragon", "elfo_nocturno", "hombre_pantera", "hombre_lagarto"}
        permitidos |= set(cinematicas.ETIQUETAS_RETRATO)
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "assets")
        for fn in FUNCIONES_ESCENAS:
            for e in getattr(prologo, fn)():
                retrato = e.get("retrato")
                if retrato:
                    self.assertIn(retrato, permitidos, f"{fn}: retrato {retrato}")
                    self.assertTrue(
                        os.path.exists(os.path.join(base, f"avatar_{retrato}.png")),
                        f"{fn}: falta el avatar de {retrato}")

    def test_orden_del_prologo(self):
        """El prologo va del mundo real al fantastic, y termina eligiendo mazo."""
        orden = (prologo.escenas_pre_duelo() + prologo.escenas_carta_umbral()
                 + prologo.escenas_transporte() + prologo.escenas_despertar()
                 + prologo.escenas_encuentro_hostil() + prologo.escenas_nara()
                 + prologo.escenas_cierre())
        textos = [e["texto"] for e in orden]
        unido = " ".join(textos).lower()
        self.assertIn("ultima ronda clasificatoria", unido)
        self.assertIn("el umbral", unido)
        self.assertIn("no puede ser", unido)          # el despertar
        self.assertIn("no deberias tener eso", unido)  # el goblin
        self.assertIn("amenaza", unido)                # el encuentro hostil
        self.assertIn("aqui esto se llama juicio", unido)
        # Nara aparece despues del hostil, nunca antes
        self.assertLess(unido.index("amenaza"), unido.index("se llama juicio"))

    def test_la_escena_negra_no_tiene_texto(self):
        for e in prologo.escenas_transporte():
            self.assertIsInstance(e["texto"], str)

    def test_humor_meta_del_duelista(self):
        """El contraste de conocimiento debe aparecer, no solo el drama."""
        unido = " ".join(
            e["texto"] for e in (prologo.escenas_despertar()
                                 + prologo.escenas_encuentro_hostil())).lower()
        self.assertTrue(any(s in unido for s in
                            ("la conoces", "mil veces", "no puede ser")),
                        "falta el comentario meta del duelista")


if __name__ == "__main__":
    unittest.main()
