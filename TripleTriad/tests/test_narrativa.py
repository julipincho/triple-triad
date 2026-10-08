"""Tests de la narrativa de campana: escenas previas y posteriores, decisiones
morales, reacciones por faccion y dialogo de Nara.

Verifica tambien que la estructura de datos narrativos mueve el estado de
verdad (campana.decidir) y que el modulo no depende de campana (evita ciclos).
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
import cinematicas
import facciones
import narrativa


NODOS_DUELO = ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono")


class TestCoberturaDeNodos(unittest.TestCase):
    def test_todo_nodo_de_duelo_tiene_previa_y_posterior(self):
        for nodo in NODOS_DUELO:
            self.assertTrue(narrativa.previa_nodo(nodo), f"{nodo} sin previa")
            self.assertTrue(narrativa.posterior_nodo(nodo), f"{nodo} sin posterior")

    def test_los_nodos_de_campana_existen_en_el_grafo(self):
        for nodo in NODOS_DUELO:
            self.assertIn(nodo, campana.NODOS)

    def test_las_escenas_son_validas_para_el_reproductor(self):
        """Mismas claves que cinematicas.esc: se pasan tal cual."""
        claves = {"texto", "hablante", "fondo", "retrato", "efecto", "musica",
             "color", "mundo"}
        for nodo in NODOS_DUELO:
            for e in narrativa.previa_nodo(nodo) + narrativa.posterior_nodo(nodo):
                self.assertEqual(set(e), claves, f"{nodo}: claves distintas")

    def test_las_escenas_no_dejan_texto_vacio(self):
        for nodo in NODOS_DUELO:
            for e in narrativa.previa_nodo(nodo) + narrativa.posterior_nodo(nodo):
                self.assertTrue(e["texto"].strip(), f"{nodo}: escena sin texto")

    def test_las_devoluciones_son_copias(self):
        """Mutar la salida no puede corromper los datos del modulo."""
        primera = narrativa.previa_nodo("senda")
        primera[0]["texto"] = "adulterado"
        self.assertNotEqual(narrativa.previa_nodo("senda")[0]["texto"], "adulterado")

    def test_fondo_de_escena_existe(self):
        for nodo in NODOS_DUELO:
            for e in narrativa.previa_nodo(nodo) + narrativa.posterior_nodo(nodo):
                ruta = os.path.join(RAIZ, "assets", "fondos", f"{e['fondo']}.png")
                self.assertTrue(os.path.exists(ruta),
                                f"{nodo}: fondo inexistente {e['fondo']}")


class TestNodoDeBifurcacion(unittest.TestCase):
    def test_el_nodo_eleccion_no_tiene_escenas_de_duelo(self):
        """`bifurcacion` es una eleccion, no un duelo: no lleva escenas."""
        self.assertEqual(campana.NODOS["bifurcacion"]["tipo"], "eleccion")
        self.assertEqual(narrativa.previa_nodo("bifurcacion"), [])
        self.assertEqual(narrativa.posterior_nodo("bifurcacion"), [])


class TestReaccionesPorFaccion(unittest.TestCase):
    def test_las_diez_facciones_tienen_reaccion(self):
        for faccion in facciones.orden_facciones():
            self.assertTrue(narrativa.reaccion_mazo(faccion),
                            f"{faccion} sin reaccion al mazo")

    def test_cada_reaccion_empieza_distinta(self):
        primeras = [narrativa.reaccion_mazo(f) for f in facciones.orden_facciones()]
        self.assertEqual(len(set(primeras)), len(primeras),
                         "dos facciones comparten la misma primera linea")

    def test_hay_una_segunda_linea_para_reactividad(self):
        for faccion in facciones.orden_facciones():
            self.assertTrue(narrativa.segunda_reaccion_mazo(faccion),
                            f"{faccion} sin segunda linea")

    def test_faccion_desconocida_no_rompe(self):
        self.assertEqual(narrativa.reaccion_mazo("inexistente"), "")
        self.assertEqual(narrativa.segunda_reaccion_mazo("inexistente"), "")


class TestDialogoDeNara(unittest.TestCase):
    MOMENTOS = ("presentacion", "umbral", "victoria", "derrota")

    def test_todos_los_momentos_responden(self):
        for momento in self.MOMENTOS:
            for confianza in (0, 2, 3, 5):
                linea = narrativa.nara_linea(momento, confianza)
                self.assertTrue(linea.strip(),
                                f"{momento} con confianza {confianza} devuelve vacio")

    def test_el_dialogo_cambia_segun_confianza(self):
        """Reactividad ligera: baja confianza suena distinto a alta."""
        for momento in self.MOMENTOS:
            baja = narrativa.nara_linea(momento, 1)
            alta = narrativa.nara_linea(momento, 4)
            self.assertNotEqual(baja, alta,
                                f"{momento}: mismo dialogo con confianza 1 y 4")

    def test_el_umbral_de_confianza_es_tres(self):
        """nara_aliada() marca a partir de 3; el dialogo debe seguirlo."""
        for momento in self.MOMENTOS:
            self.assertEqual(narrativa.nara_linea(momento, 2),
                             narrativa.nara_linea(momento, 1))
            self.assertEqual(narrativa.nara_linea(momento, 4),
                             narrativa.nara_linea(momento, 5))
            self.assertNotEqual(narrativa.nara_linea(momento, 2),
                                narrativa.nara_linea(momento, 4))

    def test_momento_desconocido_devuelve_vacio(self):
        self.assertEqual(narrativa.nara_linea("inexistente", 3), "")


class TestDecisionesMorales(unittest.TestCase):
    def test_las_decisiones_apuntan_a_nodos_validos(self):
        for nodo, decision in narrativa.DECISION.items():
            self.assertIn(nodo, campana.NODOS, f"decision en nodo inexistente {nodo}")
            self.assertTrue(decision["id"])
            self.assertTrue(decision["pregunta"])
            self.assertGreaterEqual(len(decision["opciones"]), 2)

    def test_cada_opcion_tiene_texto_respuesta_y_efecto(self):
        for decision in narrativa.DECISION.values():
            for op in decision["opciones"]:
                self.assertTrue(op["texto"])
                self.assertTrue(op["respuesta"])
                self.assertIsInstance(op["efecto"], dict)

    def test_los_ids_de_opcion_son_unicos_en_cada_decision(self):
        for decision in narrativa.DECISION.values():
            ids = [op["id"] for op in decision["opciones"]]
            self.assertEqual(len(ids), len(set(ids)), decision["id"])

    def test_aplicar_una_decision_mueve_el_estado(self):
        estado = campana.nueva_campana("humano")
        d = narrativa.decision_de("senda")
        op = d["opciones"][0]
        campana.decidir(estado, d["id"], op["efecto"])
        self.assertIn(d["id"], estado["decisiones"])
        self.assertEqual(estado["confianza_nara"], op["efecto"].get("confianza", 0))
        if "revelacion" in op["efecto"]:
            self.assertTrue(campana.revelado(estado, op["efecto"]["revelacion"]))

    def test_una_decision_no_se_aplica_dos_veces(self):
        estado = campana.nueva_campana("humano")
        d = narrativa.decision_de("fortaleza")
        confianza_tras_dar = d["opciones"][0]["efecto"]["confianza"]
        campana.decidir(estado, d["id"], d["opciones"][0]["efecto"])
        campana.decidir(estado, d["id"], d["opciones"][0]["efecto"])
        # la decision resta confianza: aplicarla dos veces la restaria en doble
        self.assertEqual(estado["confianza_nara"], 0)
        self.assertLess(confianza_tras_dar, 0)

    def test_no_toda_decision_da_recompensa_gratis(self):
        """La fortaleza cobra: una decision tiene que costar algo."""
        d = narrativa.decision_de("fortaleza")
        costes = [op for op in d["opciones"]
                  if op["efecto"].get("confianza", 0) < 0]
        self.assertTrue(costes, "ninguna opcion de la fortaleza tiene coste")


class TestIntegracionConCampana(unittest.TestCase):
    def test_info_duelo_lleva_el_pegame_narrativo(self):
        estado = campana.nueva_campana("goblin")
        campana.subir_confianza_nara(estado, 2)
        campana.subir_conocimiento(estado, 1)
        info = campana.info_duelo(estado)
        self.assertEqual(info["faccion_jugador"], "goblin")
        self.assertEqual(info["confianza_nara"], 2)
        self.assertEqual(info["conocimiento_umbral"], 1)

    def test_escenas_nodo_incluye_la_previa_de_narrativa(self):
        estado = campana.nueva_campana("humano")
        info = campana.info_duelo(estado)
        escenas, _ = cinematicas.escenas_nodo(info)
        textos = [e["texto"] for e in escenas]
        self.assertIn("El camino esta sembrado de ceniza y nadie sabe de donde viene.",
                      textos)
        self.assertTrue(any("cuneta" in t for t in textos),
                        "la previa de narrativa no llego al cartel de escenario")

    def test_escenas_posterior_reacciona_a_la_faccion(self):
        info = campana.info_duelo(campana.nueva_campana("orco"))
        posterior = cinematicas.escenas_posterior(info, True)
        self.assertTrue(any("orco" in e["texto"].lower() for e in posterior),
                        "la reaccion de faccion no llego a la escena posterior")

    def test_escenas_posterior_reacciona_a_la_confianza(self):
        estado = campana.nueva_campana("humano")
        baja = dict(campana.info_duelo(estado), confianza_nara=0)
        alta = dict(campana.info_duelo(estado), confianza_nara=5)
        self.assertNotEqual(cinematicas.escenas_posterior(baja, True),
                            cinematicas.escenas_posterior(alta, True))

    def test_posterior_de_derrota_es_distinto_de_victoria(self):
        info = campana.info_duelo(campana.nueva_campana("elfo"))
        self.assertNotEqual(cinematicas.escenas_posterior(info, True),
                            cinematicas.escenas_posterior(info, False))


class TestSinCiclosDeImportacion(unittest.TestCase):
    def test_narrativa_no_importa_campana(self):
        """Si lo hiciera, campana -> narrativa -> campana seria un ciclo."""
        with open(os.path.join(RAIZ, "narrativa.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        for linea in fuente.splitlines():
            limpio = linea.strip()
            if limpio.startswith("import ") or limpio.startswith("from "):
                self.assertNotIn(" campana", " " + limpio,
                                 f"narrativa.py importa campana: {limpio}")

    def test_los_modulos_se_importan_juntos(self):
        import importlib
        for nombre in ("narrativa", "cinematicas", "campana", "prologo"):
            importlib.import_module(nombre)


class TestTextoVisibleEnAscii(unittest.TestCase):
    def test_el_texto_del_juego_es_ascii(self):
        """El resto del juego es ASCII; el pixel font no cubre otros alfabetos."""
        for nodo in NODOS_DUELO:
            for e in narrativa.previa_nodo(nodo) + narrativa.posterior_nodo(nodo):
                for ch in e["texto"]:
                    self.assertLessEqual(
                        ord(ch), 127,
                        f"{nodo}: caracter no-ascii {ch!r} en {e['texto'][:40]!r}")


if __name__ == "__main__":
    unittest.main()
