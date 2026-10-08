"""Tests de los duelistas: rol, motivacion, dialogos y reaccion por faccion.

Comprueba tambien la coherencia entre el rol y la identidad (un campesino no
puede llamarse "Rey Oscuro") y que ningun rival sea un arquetipo malvado.
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
import duelistas
import facciones
import narrativa

NODOS_DUELO = ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono")
MOMENTOS = ("pre", "win", "lose")


class TestCoberturaDeRoles(unittest.TestCase):
    def test_todo_nodo_de_duelo_tiene_rol(self):
        for nodo in NODOS_DUELO:
            self.assertTrue(duelistas.rol_de(nodo), f"{nodo} sin rol")

    def test_cada_rol_declara_quien_es(self):
        for nodo in NODOS_DUELO:
            rol = duelistas.rol_de(nodo)
            for campo in ("rol", "personalidad", "motivacion", "historia"):
                self.assertTrue(rol.get(campo), f"{nodo}: {campo} vacio")

    def test_los_roles_son_distintos_entre_si(self):
        nombres = [duelistas.nombre_rol(n) for n in NODOS_DUELO]
        self.assertEqual(len(set(nombres)), len(nombres),
                         "dos nodos comparten el mismo rol")

    def test_los_nodos_existen_en_el_grafo(self):
        for nodo in NODOS_DUELO:
            self.assertIn(nodo, campana.NODOS)


class TestDialogos(unittest.TestCase):
    def test_cada_rol_tiene_los_tres_momentos(self):
        for nodo in NODOS_DUELO:
            dialogo = duelistas.rol_de(nodo).get("dialogo", {})
            for momento in MOMENTOS:
                self.assertTrue(dialogo.get(momento),
                                f"{nodo} sin dialogo de {momento}")

    def test_las_lineas_son_escenas_validas(self):
        claves = {"texto", "hablante", "fondo", "retrato", "efecto", "musica",
             "color", "mundo"}
        for nodo in NODOS_DUELO:
            for momento in MOMENTOS:
                for e in duelistas.dialogo_de(nodo, momento, "Alguien"):
                    self.assertEqual(set(e), claves, f"{nodo}/{momento}")
                    self.assertTrue(e["texto"].strip())

    def test_el_nombre_del_duelista_se_sustituye(self):
        """__NOMBRE__ se resuelve: si queda, es un bug de presentacion."""
        for nodo in NODOS_DUELO:
            for momento in MOMENTOS:
                for e in duelistas.dialogo_de(nodo, momento, "Pik"):
                    self.assertNotIn("__NOMBRE__", e["texto"],
                                     f"{nodo}/{momento}: placeholder sin resolver")
                    if "Pik" in e["texto"]:
                        self.assertIsNone(e.get("hablante"),
                                          "el nombre ya esta en el texto")

    def test_momento_desconocido_devuelve_vacio(self):
        self.assertEqual(duelistas.dialogo_de("senda", "inventado", "X"), [])

    def test_nodo_desconocido_devuelve_vacio(self):
        self.assertEqual(duelistas.dialogo_de("inventado", "pre", "X"), [])

    def test_la_devolucion_es_una_copia(self):
        primero = duelistas.dialogo_de("senda", "pre", "Pik")
        primero[0]["texto"] = "adulterado"
        self.assertNotEqual(duelistas.dialogo_de("senda", "pre", "Pik")[0]["texto"],
                            "adulterado")


class TestReaccionPorFaccion(unittest.TestCase):
    def test_las_diez_facciones_reaccionan_en_cada_nodo(self):
        for nodo in NODOS_DUELO:
            for faccion in facciones.orden_facciones():
                self.assertTrue(
                    duelistas.reaccion_rol(nodo, faccion),
                    f"{nodo}: {faccion} no tiene reaccion")

    def test_cada_nodo_diez_reacciones_distintas(self):
        for nodo in NODOS_DUELO:
            lineas = [duelistas.reaccion_rol(nodo, f)
                      for f in facciones.orden_facciones()]
            self.assertEqual(len(set(lineas)), 10,
                             f"{nodo}: reacciones repetidas")

    def test_faccion_desconocida_no_rompe(self):
        self.assertEqual(duelistas.reaccion_rol("senda", "inventada"), "")


class TestIdentidadDelRol(unittest.TestCase):
    def test_la_senda_usa_nombres_propios(self):
        """En la senda pelea un vecino, no el campeon de la faccion."""
        for faccion in facciones.orden_facciones():
            propia = duelistas.identidad_rol("senda", faccion)
            self.assertTrue(propia.get("nombre"), f"{faccion} sin nombre propio")
            self.assertTrue(propia.get("titulo"), f"{faccion} sin titulo propio")

    def test_los_diez_nombres_de_senda_son_distintos(self):
        nombres = [duelistas.identidad_rol("senda", f)["nombre"]
                   for f in facciones.orden_facciones()]
        self.assertEqual(len(set(nombres)), 10, "nombres de senda repetidos")

    def test_los_titulos_de_senda_no_son_de_campeon(self):
        """Nada de "Rey Oscuro" en un nodo donde el rival no quiere pelear."""
        for faccion in facciones.orden_facciones():
            titulo = duelistas.identidad_rol("senda", faccion)["titulo"]
            self.assertNotIn("Rey", titulo, f"{faccion}: {titulo}")
            self.assertNotIn("Campeon", titulo, f"{faccion}: {titulo}")

    def test_pik_es_el_goblin_del_prologo(self):
        import prologo
        self.assertEqual(duelistas.identidad_rol("senda", "goblin")["nombre"], "Pik")
        escenas = " ".join(e["texto"] for e in prologo.escenas_despertar())
        self.assertIn("Pik", escenas)

    def test_los_otros_nodos_usan_el_campeon_de_la_faccion(self):
        for nodo in NODOS_DUELO:
            if nodo == "senda":
                continue
            self.assertEqual(duelistas.identidad_rol(nodo, "dragon"), {},
                             f"{nodo} no deberia tener identidad propia")

    def test_el_titulo_del_nodo_manda_sobre_el_de_faccion(self):
        """El mapa ya sobreescribe el titulo por nodo (TITULOS_NODO)."""
        e = campana.nueva_campana("humano")
        d = campana._duelista_de("goblin", "fortaleza")
        self.assertEqual(d["titulo"], campana.TITULOS_NODO["fortaleza"])


class TestCoherenciaRolIdentidad(unittest.TestCase):
    """El bug que motivó `nombres`: un "¿quieres pelear?" con "Rey Oscuro"."""

    def test_el_duelista_de_senda_no_es_el_campeon(self):
        for faccion in facciones.orden_facciones():
            d = campana._duelista_de(faccion, "senda")
            campeon = campana.DUELISTAS[faccion]["nombre"]
            self.assertNotEqual(d["nombre"], campeon,
                                f"{faccion}: en senda sigue siendo el campeon")
            self.assertEqual(d["rol"], "campesino")

    def test_la_senda_no_anuncia_al_campeon(self):
        e = campana.nueva_campana("humano")
        info = campana.info_duelo(e, "senda")
        cartel = " ".join(x["texto"] for x in cinematicas.escenas_nodo(info)[0])
        self.assertNotIn("Rey Oscuro", cartel,
                         "el cartel de la senda anuncia al campeon")

    def test_los_nodos_tardios_si_conservan_el_campeon(self):
        """Fuera de la senda, el rival es el campeon de su faccion.

        Ojo: el rival NO es la faccion del jugador (viene de la escalera), asi
        que hay que preguntarle a `_duelista_de` por la faccion rival.
        """
        for nodo in ("aldea", "ruinas", "fortaleza", "asalto", "trono"):
            for faccion in facciones.orden_facciones():
                d = campana._duelista_de(faccion, nodo)
                self.assertEqual(d["nombre"], campana.DUELISTAS[faccion]["nombre"],
                                 f"{nodo}/{faccion}: perdio el campeon")


class TestNingunRivalEsMalvado(unittest.TestCase):
    """La biblia pide motivos legitimos: nadie quiere el trono por maldad."""

    PALABRAS_MALAS = ("malvado", "malvada", "villano", "villana", "cruel",
                      "perverso", "odiaba", "sabotea")

    def test_ninguna_motivacion_usa_lenguaje_de_villano(self):
        for nodo in NODOS_DUELO:
            texto = duelistas.motivacion_de(nodo).lower()
            for palabra in self.PALABRAS_MALAS:
                self.assertNotIn(palabra, texto,
                                 f"{nodo}: motivacionFvadida {palabra}")

    def test_ningun_dialogo_amenaza_al_duelista(self):
        """Amenazas explicitas, no palabras sueltas.

        "nadie muere por un Juicio" contiene "muere" y es lo contrario de una
        amenaza; por eso la lista busca frases completas y no morfemas.
        """
        amenazas = ("te mato", "te voy a matar", "te quiero muerto",
                    "mujeres a la hoguera", "arranco la cabeza",
                    "no te dejo salir")
        for nodo in NODOS_DUELO:
            for momento in MOMENTOS:
                for e in duelistas.dialogo_de(nodo, momento, "Rival"):
                    texto = e["texto"].lower()
                    for frase in amenazas:
                        self.assertNotIn(frase, texto,
                                         f"{nodo}/{momento}: {texto[:50]}")

    def test_los_derrotados_no_estan_destruidos(self):
        """Perder un duelo no mata a nadie: es un Juicio."""
        for nodo in NODOS_DUELO:
            lineas = duelistas.dialogo_de(nodo, "win", "Rival")
            unido = " ".join(e["texto"].lower() for e in lineas)
            for palabra in ("muerto", "muerte", "asesinado", "cadáver"):
                self.assertNotIn(palabra, unido, f"{nodo}: derrota con muerte")


class TestIntegracionConElFlujo(unittest.TestCase):
    def test_info_duelo_expone_el_rol(self):
        e = campana.nueva_campana("goblin")
        info = campana.info_duelo(e, "fortaleza")
        for campo in ("rol", "personalidad", "motivacion", "historia",
                      "reaccion_rol", "dialogo_pre"):
            self.assertIn(campo, info)
        self.assertEqual(info["rol"], "jefe_arco")
        self.assertTrue(info["dialogo_pre"])

    def test_el_dialogo_pre_entra_en_el_cartel(self):
        e = campana.nueva_campana("vampiro")
        info = campana.info_duelo(e, "fortaleza")
        textos = [x["texto"] for x in cinematicas.escenas_nodo(info)[0]]
        for e2 in info["dialogo_pre"]:
            self.assertIn(e2["texto"], textos,
                          "el dialogo del rol no llega al cartel")

    def test_la_reaccion_del_rol_gana_a_la_generica(self):
        e = campana.nueva_campana("vampiro")
        info = campana.info_duelo(e, "fortaleza")
        textos = [x["texto"] for x in cinematicas.escenas_nodo(info)[0]]
        self.assertIn(info["reaccion_rol"], textos)

    def test_el_posterior_incluye_la_voz_del_rival(self):
        e = campana.nueva_campana("elfo")
        info = campana.info_duelo(e, "trono")
        ganaste = [x["texto"] for x in cinematicas.escenas_posterior(info, True)]
        perdiste = [x["texto"] for x in cinematicas.escenas_posterior(info, False)]
        self.assertNotEqual(ganaste, perdiste)
        # el dialogo del rival se distingue del resto
        propio = [e2["texto"] for e2 in duelistas.dialogo_de("trono", "win", "X")]
        for linea in propio:
            self.assertTrue(any(linea[:30] in t for t in ganaste),
                            f"falta el dialogo de victoria: {linea[:40]}")

    def test_el_fondo_del_posterior_es_el_del_nodo(self):
        e = campana.nueva_campana("humano")
        for nodo in NODOS_DUELO:
            info = campana.info_duelo(e, nodo)
            propio_fondo = campana.NODOS[nodo].get("escena", "campamento")
            for x in cinematicas.escenas_posterior(info, True):
                self.assertEqual(x["fondo"], propio_fondo, nodo)

    def test_los_retratos_apuntan_a_un_avatar_real(self):
        e = campana.nueva_campana("humano")
        for nodo in NODOS_DUELO:
            info = campana.info_duelo(e, nodo)
            for x in cinematicas.escenas_nodo(info)[0]:
                retrato = x.get("retrato")
                if retrato:
                    self.assertTrue(
                        os.path.exists(os.path.join(RAIZ, "assets", f"avatar_{retrato}.png")),
                        f"{nodo}: avatar inexistente {retrato}")


class TestTextoAscii(unittest.TestCase):
    def test_todo_el_texto_de_rol_es_ascii(self):
        for nodo in NODOS_DUELO:
            textos = [duelistas.motivacion_de(nodo), duelistas.historia_de(nodo),
                      duelistas.personalidad_de(nodo)]
            for faccion in facciones.orden_facciones():
                textos.append(duelistas.reaccion_rol(nodo, faccion))
            for momento in MOMENTOS:
                textos += [e["texto"] for e in duelistas.dialogo_de(nodo, momento, "X")]
            for t in textos:
                for ch in t:
                    self.assertLessEqual(ord(ch), 127, f"{nodo}: {ch!r} en {t[:40]!r}")


class TestSinCiclos(unittest.TestCase):
    def test_duelistas_no_importa_campana(self):
        with open(os.path.join(RAIZ, "duelistas.py"), encoding="utf-8") as fh:
            for linea in fh:
                limpio = linea.strip()
                if limpio.startswith(("import ", "from ")):
                    self.assertNotIn(" campana", " " + limpio,
                                     f"duelistas.py importa campana: {limpio}")


if __name__ == "__main__":
    unittest.main()
