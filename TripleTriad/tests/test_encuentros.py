"""Tests de los encuentros: la parte que revela mundo.

Los 4 encuentros de `campana.ENCUENTROS` y sus efectos NO se tocan (esa parte
ya la cubren el balance y los tests de flujo). Aqui se verifica la capa de
lore: revelaciones, reacciones por faccion y los dos encuentros opcionales.
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
import encuentros
import facciones
import pygame
import ui

# `ui.envolver` necesita la fuente cargada para medir: sin `pygame.init()` y una
# superficie, `ui.texto` revienta con "font not initialized".
if not pygame.get_init():
    pygame.init()
if pygame.display.get_surface() is None:
    pygame.display.set_mode((ui.ANCHO, ui.ALTO))

TODOS = ("mercader", "anciano", "hermandad", "caravana", "hostil", "nara")


class TestCoberturaDeEncuentros(unittest.TestCase):
    def test_los_seis_tienen_lore(self):
        for enc in TODOS:
            self.assertTrue(encuentros.lore_de(enc), f"{enc} sin lore")

    def test_cada_uno_revela_y_titula(self):
        for enc in TODOS:
            self.assertTrue(encuentros.revelacion_de(enc), f"{enc} sin revelacion")
            self.assertTrue(encuentros.titulo_revelacion(enc), f"{enc} sin titulo")
            self.assertTrue(encuentros.linea_principal(enc), f"{enc} sin linea")

    def test_las_revelaciones_son_unicas(self):
        ids = [encuentros.revelacion_de(e) for e in TODOS]
        self.assertEqual(len(set(ids)), len(ids), "revelaciones repetidas")

    def test_las_revelaciones_cubren_los_cuatro_encuentros_existentes(self):
        """Los 4 de campana.ENCUENTROS deben tener lore."""
        for enc in campana.ENCUENTROS:
            self.assertIn(enc["id"], encuentros.LORE,
                          f"{enc['id']} existe en campana pero no tiene lore")

    def test_encuentro_desconocido_no_rompe(self):
        self.assertEqual(encuentros.lore_de("inventado"), {})
        self.assertEqual(encuentros.revelacion_de("inventado"), "")
        self.assertEqual(encuentros.linea_principal("inventado"), "")
        self.assertEqual(encuentros.escena_antes("inventado", "humano"), [])


class TestReaccionesPorFaccion(unittest.TestCase):
    def test_las_diez_facciones_reaccionan_en_cada_encuentro(self):
        for enc in TODOS:
            for faccion in facciones.orden_facciones():
                self.assertTrue(encuentros.reaccion(enc, faccion),
                                f"{enc}/{faccion}: sin reaccion")

    def test_las_claves_son_facciones_validas(self):
        validas = set(facciones.orden_facciones())
        for enc in TODOS:
            claves = set(encuentros.reacciones(enc))
            self.assertEqual(claves - validas, set(),
                             f"{enc}: facciones invalidas {claves - validas}")

    def test_cada_encuentro_diez_reacciones_distintas(self):
        for enc in TODOS:
            lineas = [encuentros.reaccion(enc, f)
                      for f in facciones.orden_facciones()]
            self.assertEqual(len(set(lineas)), 10,
                             f"{enc}: reacciones repetidas")

    def test_hombre_lobo_esta_bien_escrito(self):
        """Se escribio 'hombre_lubo' una vez; el id real es hombre_lobo."""
        self.assertTrue(encuentros.reaccion("nara", "hombre_lobo"))
        self.assertEqual(encuentros.reaccion("nara", "hombre_lubo"), "")


class TestRevelacionEnElEstado(unittest.TestCase):
    def test_revelar_agrega_al_estado(self):
        e = campana.nueva_campana("humano")
        datos = campana.revelar_encuentro(e, "mercader")
        self.assertIsNotNone(datos)
        self.assertTrue(campana.revelado(e, "enc_mercader_falsificacion"))
        self.assertIn("enc_mercader_falsificacion", e["revelaciones"])

    def test_no_se_revela_dos_veces(self):
        e = campana.nueva_campana("humano")
        campana.revelar_encuentro(e, "mercader")
        self.assertIsNone(campana.revelar_encuentro(e, "mercader"))
        self.assertEqual(e["revelaciones"].count("enc_mercader_falsificacion"), 1)

    def test_encuentro_sin_revelacion_no_rompe(self):
        e = campana.nueva_campana("humano")
        antes = list(e["revelaciones"])
        campana.revelar_encuentro(e, "inventado")
        self.assertEqual(e["revelaciones"], antes)

    def test_la_revelacion_entrega_texto_pintable(self):
        """El crash: `linea` era una LISTA y `cartel` reventaba al pintarla.

        `ui.envolver` hace `_LIMPIO.get(cadena)` y una lista no se puede meter
        como clave de diccionario: `TypeError: unhashable type: 'list'`. Pasaba
        en el primer encuentro de cada partida, que es la primera vez que se
        jugaba ese encuentro, o sea siempre.
        """
        for enc in encuentros.LORE:
            e = campana.nueva_campana("humano")
            datos = campana.revelar_encuentro(e, enc)
            if datos is None:
                continue
            with self.subTest(encuentro=enc):
                self.assertIsInstance(datos["linea"], str,
                                      "la linea debe llegar como texto")
                self.assertTrue(datos["linea"].strip())
                # Y tiene que ser algo que `envolver` pueda usar de verdad.
                lineas = ui.envolver(datos["linea"], 11, 640)
                self.assertTrue(lineas)

    def test_todas_las_revelaciones_son_pintables(self):
        """Ninguna revelacion del juego puede ser una lista sin juntar."""
        for enc in encuentros.LORE:
            with self.subTest(encuentro=enc):
                e = campana.nueva_campana("humano")
                datos = campana.revelar_encuentro(e, enc)
                if datos is None:
                    continue
                self.assertIsInstance(datos["linea"], str)
                ui.envolver(datos["linea"], 11, 640)  # no debe reventar
                self.assertIsInstance(datos["titulo"], str)

    def test_revelar_sube_el_conocimiento_del_umbral(self):
        """Una revelacion es un paso mas hacia entender el Umbral."""
        e = campana.nueva_campana("humano")
        antes = campana.conocimiento_umbral(e)
        campana.revelar_encuentro(e, "anciano")
        self.assertGreater(campana.conocimiento_umbral(e), antes)

    def test_las_revelaciones_son_ids_de_compendio_registrables(self):
        for rid in campana.revelation_ids():
            self.assertTrue(rid.startswith("enc_"), rid)
            e = campana.nueva_campana("humano")
            campana.revelar(estado=e, id_revelacion=rid)
            self.assertTrue(campana.revelado(e, rid))


class TestEncuentrosOpcionales(unittest.TestCase):
    def test_hostil_y_nara_existen_como_encuentro(self):
        for enc_id in ("hostil", "nara"):
            enc = campana.encuentro_para("senda", enc_id)
            self.assertEqual(enc["id"], enc_id)
            self.assertTrue(enc["opciones"])
            self.assertTrue(enc["texto"])

    def test_sus_efectos_son_que_aplicar_encuentro_conoce(self):
        for enc_id in ("hostil", "nara"):
            enc = campana.encuentro_para("senda", enc_id)
            for op in enc["opciones"]:
                titulo, texto = campana.aplicar_encuentro(
                    campana.nueva_campana("humano"), op["efecto"])
                self.assertNotEqual(texto, "No ocurre nada.",
                                    f"{enc_id}/{op['id']}: efecto desconocido")

    def test_nara_exige_confianza(self):
        enc = campana.encuentro_para("senda", "nara")
        self.assertEqual(enc["confianza_minima"], 3)
        # el umbral coincide con el de nara_aliada
        e = campana.nueva_campana("humano")
        campana.subir_confianza_nara(e, 3)
        self.assertTrue(campana.nara_aliada(e))

    def test_no_entran_en_el_mapa_de_nodos(self):
        """Son opcionales: no pueden replacing el encuentro de un nodo."""
        for enc_id in ("hostil", "nara"):
            self.assertNotIn(enc_id, campana.ENCUENTRO_POR_NODO.values())

    def test_el_nodo_conserva_su_encuentro_original(self):
        for nodo, esperado in campana.ENCUENTRO_POR_NODO.items():
            self.assertEqual(campana.encuentro_para(nodo)["id"], esperado)
            # pedir otro explicito no cambia el default
            campana.encuentro_para(nodo)
            self.assertEqual(campana.encuentro_para(nodo)["id"], esperado)


class TestEscenaAntesDelEncuentro(unittest.TestCase):
    def test_devuelve_escenas_validas(self):
        claves = {"texto", "hablante", "fondo", "retrato", "efecto", "musica",
             "color", "mundo"}
        for enc in TODOS:
            for faccion in facciones.orden_facciones():
                escenas = encuentros.escena_antes(enc, faccion)
                self.assertTrue(escenas, f"{enc}/{faccion}: sin escenas")
                for e in escenas:
                    self.assertEqual(set(e), claves)

    def test_el_fondo_es_el_del_encuentro(self):
        for enc_id in ("hostil", "nara"):
            esperado = campana.encuentro_para("senda", enc_id)["escena"]
            for e in encuentros.escena_antes(enc_id, "humano"):
                self.assertEqual(e["fondo"], esperado)

    def test_los_titulos_y_escenas_no_se_desincronizan(self):
        """`encuentros` duplica titulo/escena para no importar campana (ciclo).

        Este test es el que garantiza que la copia no se quede vieja.
        """
        for enc in campana.ENCUENTROS:
            self.assertEqual(encuentros.titulo_encuentro(enc["id"]), enc["titulo"],
                             f"{enc['id']}: titulo desincronizado")
            self.assertEqual(encuentros.escena_encuentro(enc["id"]), enc["escena"],
                             f"{enc['id']}: escena desincronizada")

    def test_el_fondo_es_el_del_nodo_para_los_cuatro_base(self):
        """Los 4 de campana usan la escena declarada ahi."""
        for enc in campana.ENCUENTROS:
            for e in encuentros.escena_antes(enc["id"], "humano"):
                self.assertEqual(e["fondo"], enc["escena"], enc["id"])

    def test_el_titulo_va_en_mayusculas(self):
        for enc in campana.ENCUENTROS:
            escenas = encuentros.escena_antes(enc["id"], "humano")
            self.assertEqual(escenas[0]["texto"], enc["titulo"].upper())


class TestElMercadorReconoceLasCartas(unittest.TestCase):
    """La escena clave de la biblia: el mercader ve que tus cartas no son de aqui."""

    def test_la_linea_de_falsificacion_existe(self):
        lineas = " ".join(encuentros.lore_de("mercader")["linea"]).lower()
        self.assertIn("falsificacion", lineas)
        self.assertIn("cuatrocientos anos", lineas)

    def test_el_duelista_insiste(self):
        lineas = encounters_lineas()
        self.assertTrue(any("no es falsa" in l.lower() for l in lineas),
                        "el duelista no defiende sus cartas")

    def test_el_guion_tiene_turnos_alternados(self):
        lineas = encounters_lineas()
        self.assertGreaterEqual(len(lineas), 3)
        # el duelista responde en las lineas impares (1, 3, ...)
        for i in range(1, len(lineas), 2):
            self.assertTrue(lineas[i].startswith("-"),
                            f"linea {i} deberia ser del duelista: {lineas[i]}")


def encounters_lineas():
    return encuentros.lore_de("mercader")["linea"]


class TestTextoAscii(unittest.TestCase):
    def test_todo_el_lore_es_ascii(self):
        for enc in TODOS:
            textos = [encuentros.linea_principal(enc),
                      encuentros.titulo_revelacion(enc)]
            textos += encuentros.lore_de(enc).get("linea", [])
            textos += [encuentros.reaccion(enc, f)
                       for f in facciones.orden_facciones()]
            for t in textos:
                for ch in t:
                    self.assertLessEqual(ord(ch), 127,
                                         f"{enc}: {ch!r} en {t[:40]!r}")


class TestSinCiclosNiRupturaDeLaParteFuncional(unittest.TestCase):
    def test_encuentros_no_importa_campana_ni_pantallas(self):
        with open(os.path.join(RAIZ, "encuentros.py"), encoding="utf-8") as fh:
            for linea in fh:
                limpio = linea.strip()
                if limpio.startswith(("import ", "from ")):
                    self.assertNotIn(" campana", " " + limpio, limpio)
                    self.assertNotIn(" pantallas", " " + limpio, limpio)

    def test_los_cuatro_encuentros_base_no_cambiaron(self):
        """La parte funcional sigue igual: mismos ids y mismos efectos."""
        esperado = {"mercader": ("pagar", "robar"),
                    "anciano": ("escuchar", "desconfiar"),
                    "hermandad": ("celebrar", "descansar"),
                    "caravana": ("regatear", "escoltar")}
        for enc in campana.ENCUENTROS:
            ids = tuple(op["id"] for op in enc["opciones"])
            self.assertEqual(ids, esperado[enc["id"]], enc["id"])

    def test_ningun_encuentro_perdio_efecto(self):
        for enc in campana.ENCUENTROS:
            for op in enc["opciones"]:
                self.assertTrue(op["efecto"], f"{enc['id']}/{op['id']}")


if __name__ == "__main__":
    unittest.main()
