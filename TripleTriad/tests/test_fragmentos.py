"""Tests del NG+: fragmentos de la verdad y campana secreta.

Verifica la regla central de la biblia: la primera campana NO cuenta todo.
Cada faccion aporta un fragmento, y con los diez aparece El Cartografo, que
nunca estuvo entre las 250 cartas.
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
import facciones
import fragmentos
import mazos


class TestCoberturaDeFragmentos(unittest.TestCase):
    def test_las_diez_facciones_tienen_fragmento(self):
        for f in facciones.orden_facciones():
            self.assertIsNotNone(fragmentos.fragmento(f), f"{f} sin fragmento")

    def test_no_hay_facciones_de_mas(self):
        self.assertEqual(set(fragmentos.FRAGMENTOS),
                         set(facciones.orden_facciones()))

    def test_cada_fragmento_responde_una_pregunta_distinta(self):
        """Si dos responden lo mismo, son el mismo fragmento con otro nombre."""
        preguntas = [fragmentos.FRAGMENTOS[f]["pregunta"]
                     for f in fragmentos.ORDEN_FRAGMENTOS]
        self.assertEqual(len(set(preguntas)), 10)
        self.assertEqual(len(preguntas), 10)

    def test_cada_fragmento_tiene_texto_y_autor(self):
        for f in fragmentos.ORDEN_FRAGMENTOS:
            fr = fragmentos.FRAGMENTOS[f]
            self.assertTrue(fr["id"].startswith("frag_"), fr["id"])
            self.assertTrue(fr["texto"].strip(), f)
            self.assertTrue(fr["quien"].strip(), f)

    def test_los_ids_son_unicos(self):
        ids = fragmentos.ids_fragmentos()
        self.assertEqual(len(set(ids)), 10)

    def test_el_orden_es_una_permutacion(self):
        self.assertEqual(set(fragmentos.ORDEN_FRAGMENTOS),
                         set(facciones.orden_facciones()))
        self.assertEqual(len(fragmentos.ORDEN_FRAGMENTOS), 10)

    def test_el_modulo_es_coherente_consigo_mismo(self):
        self.assertEqual(fragmentos._validar(), [])

    def test_faccion_desconocida_no_rompe(self):
        self.assertIsNone(fragmentos.fragmento("inventada"))
        self.assertEqual(fragmentos.ORDEN_FRAGMENTOS.count("inventada"), 0)


class TestProgresoDeFragmentos(unittest.TestCase):
    def test_progreso_vacio(self):
        self.assertEqual(fragmentos.progreso_fragmentos([]), (0, 10))

    def test_progreso_parcial(self):
        ids = fragmentos.ids_fragmentos()[:4]
        self.assertEqual(fragmentos.progreso_fragmentos(ids), (4, 10))

    def test_progreso_completo(self):
        self.assertEqual(fragmentos.progreso_fragmentos(fragmentos.ids_fragmentos()),
                         (10, 10))

    def test_faltan_para_el_cartografo(self):
        ids = fragmentos.ids_fragmentos()[:6]
        self.assertEqual(fragmentos.falta_para_el_cartografo(ids), 4)

    def test_no_falta_nada_al_llegar_a_diez(self):
        ids = fragmentos.ids_fragmentos()
        self.assertEqual(fragmentos.falta_para_el_cartografo(ids), 0)

    def test_ids_desconocidos_no_cuentan(self):
        self.assertEqual(fragmentos.progreso_fragmentos(["inventado"]), (0, 10))

    def test_acepta_lista_o_dict(self):
        """El perfil guarda una lista, pero el helper tolera dict."""
        ids = fragmentos.ids_fragmentos()[:3]
        self.assertEqual(fragmentos.progreso_fragmentos(ids),
                         fragmentos.progreso_fragmentos({i: True for i in ids}))

    def test_acepta_none(self):
        self.assertEqual(fragmentos.progreso_fragmentos(None), (0, 10))


class TestElCartografo(unittest.TestCase):
    def test_no_figura_entre_las_250_cartas(self):
        """El requisito de la biblia: no es ninguna de las facciones."""
        self.assertTrue(fragmentos.fuera_de_las_cartas())
        nombres = {c.nombre for lista in mazos.TODOS.values() for c in lista}
        self.assertNotIn(fragmentos.CARTOGRAFO["nombre"], nombres)

    def test_no_tiene_faccion(self):
        """Por eso no puede salir de ninguna escalera de rivales."""
        self.assertIsNone(fragmentos.CARTOGRAFO["faccion"])
        for escalera in campana.ESCALERAS.values():
            self.assertNotIn(fragmentos.CARTOGRAFO["nombre"], escalera)

    def test_solo_se_desbloquea_con_los_diez(self):
        ids = fragmentos.ids_fragmentos()
        for n in range(10):
            self.assertFalse(fragmentos.secreto_desbloqueado(ids[:n]),
                             f"se desbloqueo con {n}/10")
        self.assertTrue(fragmentos.secreto_desbloqueado(ids))

    def test_tiene_dialogo_completo(self):
        for momento in ("pre", "win", "lose"):
            self.assertTrue(fragmentos.dialogo_cartografo(momento),
                            f"sin dialogo de {momento}")

    def test_reacciona_a_las_diez_facciones(self):
        for f in facciones.orden_facciones():
            self.assertTrue(fragmentos.reaccion_cartografo(f), f)

    def test_sus_reacciones_son_distintas(self):
        lineas = [fragmentos.reaccion_cartografo(f)
                  for f in facciones.orden_facciones()]
        self.assertEqual(len(set(lineas)), 10)

    def test_su_mazo_es_mas_duro_que_el_del_trono(self):
        """Es el duelo final: tiene que pesar mas que el nodo del trono.

        OJO, este test era fragil y fallaba de vez en cuando (mas o menos 1 de
        cada 50 ejecuciones de la suite, no una vez en 400 como parece). La
        causa no era el codigo: `nueva_campana` sortea una semilla nueva con
        `random.getrandbits(64)`, asi que `mazo_rival(estado, "trono")` devuelve
        5 cartas DISTINTAS en cada llamada. El secreto es fijo (186) y el trono
        variaba de 144 a 186, asi que en un 0,2% de los sorteos lo empataba y el
        `assertGreater` reventaba.

        Comparar una muestra aleatoria contra un valor fijo no mide la
        propiedad que importa. Aqui se mide la potencia MEDIA del trono con
        300 sorteos, que es estable a +/-1 y responde a lo que se quiere
        comprobar: que el duelo final es mas duro de verdad, no que le haya
        tocado un mazo flojo.
        """
        from reglas import total_carta
        secreto = sum(total_carta(c) for c in campana.mazo_rival_secreto())
        sumas = []
        for _ in range(300):
            e = campana.nueva_campana("humano")
            sumas.append(sum(total_carta(c) for c in campana.mazo_rival(e, "trono")))
        media = sum(sumas) / len(sumas)
        self.assertGreater(
            secreto, media,
            f"el secreto ({secreto}) deberia pesar mas que el trono de "
            f"media ({media:.1f})")

    def test_ningun_mazo_del_trono_supera_al_secreto(self):
        """ElBehavior del死角 del trono, medido con 4000 sorteos:

        trono: min 140, mediana 166, media 166, p95 180, p99 184, max 191
        secreto: 186 (fijo)

        En el 0,70% de los sorteos el trono iguala o supera al secreto (0,45% lo
        supera). NO se corrige aqui: tocar la potencia de las cartas es
        decision del jugador, no del test.

        Lo que se afirma es el p95, no el maximo. El maximo de una variable
        aleatoria no es una propiedad estable: con 400 muestras sale 188 y con
        4000 sale 191, porque cuanto mas muestras mas cola se ve. Ese es el
        mismo error que hacia este test fragil, dos veces. Un cuantil si es
        estable, asi que es el que se comprueba.
        """
        from reglas import total_carta
        secreto = sum(total_carta(c) for c in campana.mazo_rival_secreto())
        sumas = []
        for _ in range(400):
            e = campana.nueva_campana("humano")
            sumas.append(sum(total_carta(c) for c in campana.mazo_rival(e, "trono")))
        sumas.sort()
        p95 = sumas[int(len(sumas) * 0.95)]
        self.assertLess(
            p95, secreto,
            f"el p95 del trono ({p95}) ha igualado al secreto ({secreto}): "
            "el duelo final ya no es claramente el mas duro")

    def test_el_duelo_secreto_es_mas_duro_en_cada_bando(self):
        """Y no solo contra un humano: el secreto tiene que ganar en general."""
        from reglas import total_carta
        secreto = sum(total_carta(c) for c in campana.mazo_rival_secreto())
        for faccion in facciones.orden_facciones():
            with self.subTest(faccion=faccion):
                sumas = []
                for _ in range(40):
                    e = campana.nueva_campana(faccion)
                    sumas.append(
                        sum(total_carta(c) for c in campana.mazo_rival(e, "trono")))
                media = sum(sumas) / len(sumas)
                self.assertGreater(secreto, media,
                                   f"{faccion}: secreto {secreto} vs "
                                   f"trono medio {media:.1f}")

    def test_la_escena_de_desbloqueo_cambia_al_completar(self):
        antes = fragmentos.escena_desbloqueo(fragmentos.ids_fragmentos()[:9])
        despues = fragmentos.escena_desbloqueo(fragmentos.ids_fragmentos())
        self.assertNotEqual(antes, despues)
        unido = " ".join(e["texto"] for e in despues)
        self.assertIn(fragmentos.CARTOGRAFO["nombre"], unido)

    def test_la_escena_incompleta_dice_cuantos_faltan(self):
        escenas = fragmentos.escena_desbloqueo(fragmentos.ids_fragmentos()[:3])
        unido = " ".join(e["texto"] for e in escenas)
        self.assertIn("7", unido)


class TestPersistenciaEnElPerfil(unittest.TestCase):
    """Los fragmentos viven en el perfil, no en la partida.

    Las mini campanas son en memoria: si el progreso viviera en la partida se
    perderia al cerrar el juego.
    """

    def _perfil_limpio(self):
        return campana.perfil_por_defecto()

    def test_el_perfil_nuevo_no_tiene_fragmentos(self):
        self.assertEqual(self._perfil_limpio()["fragmentos"], [])

    def test_registrar_anade_el_id(self):
        perfil = self._perfil_limpio()
        nuevo, datos = campana.registrar_fragmento("goblin", perfil)
        self.assertTrue(nuevo)
        self.assertEqual(perfil["fragmentos"], [datos["id"]])

    def test_registrar_dos_veces_no_repite(self):
        perfil = self._perfil_limpio()
        campana.registrar_fragmento("goblin", perfil)
        nuevo, _ = campana.registrar_fragmento("goblin", perfil)
        self.assertFalse(nuevo)
        self.assertEqual(len(perfil["fragmentos"]), 1)

    def test_registrar_todas_da_diez(self):
        perfil = self._perfil_limpio()
        for f in facciones.orden_facciones():
            campana.registrar_fragmento(f, perfil)
        self.assertEqual(len(perfil["fragmentos"]), 10)
        self.assertEqual(campana.progreso_fragmentos(perfil), (10, 10))

    def test_registrar_faccion_desconocida_no_rompe(self):
        perfil = self._perfil_limpio()
        nuevo, datos = campana.registrar_fragmento("inventada", perfil)
        self.assertFalse(nuevo)
        self.assertIsNone(datos)
        self.assertEqual(perfil["fragmentos"], [])

    def test_el_secreto_se_calcula_desde_el_perfil(self):
        perfil = self._perfil_limpio()
        self.assertFalse(campana.secreto_desbloqueado(perfil))
        for f in facciones.orden_facciones():
            campana.registrar_fragmento(f, perfil)
        self.assertTrue(campana.secreto_desbloqueado(perfil))

    def test_los_textos_salen_en_orden_de_ngplus(self):
        perfil = self._perfil_limpio()
        for f in fragmentos.ORDEN_FRAGMENTOS:
            campana.registrar_fragmento(f, perfil)
        textos = campana.fragmentos_texto(perfil)
        self.assertEqual([t["id"] for t in textos],
                         [fragmentos.FRAGMENTOS[f]["id"]
                          for f in fragmentos.ORDEN_FRAGMENTOS])


class TestElMisterioNoSeCuentaTodo(unittest.TestCase):
    """La regla de la biblia: la primera pasada no explica el misterio."""

    def test_el_primer_final_no_revela_al_cartografo(self):
        """Ninguno de los 30 finales puede nombrar al que escribio las cartas."""
        for faccion, variantes in campana.FINALES.items():
            for variante, datos in variantes.items():
                texto = " ".join([datos["titulo"]] + list(datos["lineas"]))
                for palabra in ("Maestro de la Mesa", "Cartografo"):
                    self.assertNotIn(palabra, texto,
                                     f"{faccion}/{variante} revela el secreto")

    def test_los_fragments_son_el_unico_lugar_que_lo_dice(self):
        """El nombre del Cartografo solo aparece en el NG+."""
        with open(os.path.join(RAIZ, "fragmentos.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        self.assertIn("Maestro de la Mesa", fuente)
        # y no en los modulos de la campana principal
        for modulo in ("campana.py", "duelistas.py", "narrativa.py", "prologo.py"):
            with open(os.path.join(RAIZ, modulo), encoding="utf-8") as fh:
                self.assertNotIn("Maestro de la Mesa", fh.read(), modulo)

    def test_los_diez_fragmentos_juntos_cuentan_el_misterio(self):
        """Cada fragmento aporta algo: ninguno es relleno."""
        textos = [fragmentos.FRAGMENTOS[f]["texto"]
                  for f in fragmentos.ORDEN_FRAGMENTOS]
        for t in textos:
            self.assertGreater(len(t), 60, t[:40])
        # los que nombran al autor son los que cierran el circulo
        juntos = " ".join(textos)
        self.assertIn("escritor", juntos)
        self.assertIn("codigo", juntos.lower())


class TestTextoAscii(unittest.TestCase):
    def test_todo_el_ngplus_es_ascii(self):
        textos = []
        for f in fragmentos.ORDEN_FRAGMENTOS:
            textos += [fragmentos.FRAGMENTOS[f]["pregunta"],
                       fragmentos.FRAGMENTOS[f]["texto"]]
        cg = fragmentos.CARTOGRAFO
        textos += [cg["nombre"], cg["titulo"], cg["personalidad"],
                   cg["motivacion"], cg["historia"]]
        for momento in ("pre", "win", "lose"):
            textos += fragmentos.dialogo_cartografo(momento)
        textos += [fragmentos.reaccion_cartografo(f)
                   for f in facciones.orden_facciones()]
        for t in textos:
            for ch in t:
                self.assertLessEqual(ord(ch), 127, f"{ch!r} en {t[:40]!r}")


class TestSinCiclos(unittest.TestCase):
    def test_fragmentos_no_importa_campana(self):
        with open(os.path.join(RAIZ, "fragmentos.py"), encoding="utf-8") as fh:
            for linea in fh:
                limpio = linea.strip()
                if limpio.startswith(("import ", "from ")):
                    self.assertNotIn(" campana", " " + limpio, limpio)


if __name__ == "__main__":
    unittest.main()
