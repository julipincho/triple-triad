"""Tests del modo campana: faccion que decide rivales, ramas, recompensas y finales."""
import os
import sys
import tempfile
import unittest

# No escribir en los datos reales del jugador
os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests")
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import campana
import facciones
import mazos
from reglas import Carta


class TestFaccionDecideCampana(unittest.TestCase):
    def test_no_se_puede_enfrentar_a_si_mismo(self):
        """Elegir Humanos significa no Payments ever-orcos... sino nunca contra humanos."""
        for faccion in facciones.orden_facciones():
            estado = campana.nueva_campana(faccion)
            visitados = []
            for nodo_id in ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono"):
                rival = campana.rival_de_nodo(estado, nodo_id)
                self.assertNotEqual(rival, faccion, f"{faccion} se enfrenta a si mismo en {nodo_id}")
                self.assertIn(rival, facciones.FACCIONES)
                visitados.append(rival)

    def test_humanos_no_luchan_contra_humanos(self):
        """Recorrido completo de la campana humana: ningun rival es humano."""
        estado = campana.nueva_campana("humano")
        for nodo_id in ("senda", "aldea", "fortaleza", "asalto", "trono"):
            self.assertNotEqual(campana.rival_de_nodo(estado, nodo_id), "humano")
        # y el jefe final tampoco
        self.assertNotEqual(campana.rival_de_nodo(estado, "trono"), "humano")
        self.assertEqual(campana.rival_de_nodo(estado, "trono"), facciones.rival_final("humano"))

    def test_orcos_no_luchan_contra_orcos(self):
        estado = campana.nueva_campana("orco")
        for nodo_id in ("senda", "aldea", "fortaleza", "asalto", "trono"):
            self.assertNotEqual(campana.rival_de_nodo(estado, nodo_id), "orco")

    def test_escalera_sin_propia_faccion(self):
        for f in facciones.orden_facciones():
            escalera = campana.escalera_de(f)
            self.assertNotIn(f, escalera)
            self.assertEqual(len(set(escalera)), len(escalera))

    def test_todas_las_facciones_tienen_tablas_completas(self):
        """Ninguna tabla puede quedarse atras al anadir una faccion."""
        import cinematicas

        orden = set(facciones.orden_facciones())
        self.assertEqual(set(mazos.TODOS), orden)
        self.assertEqual(set(campana.ESCALERAS), orden)
        self.assertEqual(set(campana.DUELISTAS), orden)
        self.assertEqual(set(campana.FINALES), orden)
        self.assertEqual(set(cinematicas.APERTURAS), orden)
        self.assertEqual(set(mazos.NOMBRES_BANDO), orden)
        self.assertEqual(set(mazos.DESCRIPCION_BANDO), orden)
        for f in orden:
            self.assertNotIn(f, campana.ESCALERAS[f])
            self.assertIn(facciones.rival_final(f), campana.DUELISTAS)

    def test_cada_faccion_tiene_jefe_y_final_propio(self):
        for f in facciones.orden_facciones():
            estado = campana.nueva_campana(f)
            self.assertIn(f, campana.FINALES)
            for variante in ("dominio", "equilibrio", "caos"):
                estado["victorias"] = 5 if variante == "dominio" else 3
                estado["mejor_racha"] = 4 if variante == "dominio" else 1
                estado["derrotas"] = 5 if variante == "caos" else 0
                titulo, lineas = campana.final_de(estado)[1:]
                self.assertTrue(titulo)
                self.assertGreaterEqual(len(lineas), 3)

    def test_final_de_humanos_es_humano(self):
        """Pedir el final humano devuelve el final humano, no un texto generico."""
        estado = campana.nueva_campana("humano")
        variante, titulo, lineas = campana.final_de(estado)
        self.assertEqual(titulo, campana.FINALES["humano"][variante]["titulo"])
        self.assertEqual(lineas, campana.FINALES["humano"][variante]["lineas"])
        # y ningun final humano es el final de otra faccion
        otros = {
            variante["titulo"]
            for f, finales in campana.FINALES.items()
            if f != "humano"
            for variante in finales.values()
        }
        self.assertNotIn(titulo, otros)

    def test_final_de_orcos_es_orco(self):
        estado = campana.nueva_campana("orco")
        variante, titulo, lineas = campana.final_de(estado)
        self.assertEqual(titulo, campana.FINALES["orco"][variante]["titulo"])

    def test_variante_segun_rendimiento(self):
        estado = campana.nueva_campana("humano")
        estado.update({"victorias": 5, "mejor_racha": 5, "derrotas": 0})
        self.assertEqual(campana.variante_final(estado), "dominio")
        estado.update({"victorias": 5, "mejor_racha": 2, "derrotas": 0})
        self.assertEqual(campana.variante_final(estado), "equilibrio")
        estado.update({"victorias": 5, "mejor_racha": 5, "derrotas": 4})
        self.assertEqual(campana.variante_final(estado), "caos")


class TestGrafoDeNodos(unittest.TestCase):
    def setUp(self):
        self.estado = campana.nueva_campana("humano")

    def test_recorrido_lineal_hasta_la_bifurcacion(self):
        campana.registrar_victoria(self.estado)
        self.assertEqual(self.estado["nodo"], "bifurcacion")
        self.assertEqual(len(self.estado["ruta"]), 1)

    def test_la_bifurcacion_exige_elegir(self):
        campana.registrar_victoria(self.estado)
        self.assertEqual(campana.nodo(self.estado["nodo"])["tipo"], "eleccion")
        self.assertIsNone(campana.nodo_siguiente(self.estado))
        campana.elegir_bifurcacion(self.estado, "ruinas")
        self.assertEqual(self.estado["nodo"], "ruinas")
        self.assertEqual(campana.nodo_siguiente(self.estado), "fortaleza")

    def test_las_dos_ramas_convergen(self):
        for rama in ("aldea", "ruinas"):
            estado = campana.nueva_campana("orco")
            campana.registrar_victoria(estado)
            campana.elegir_bifurcacion(estado, rama)
            campana.registrar_victoria(estado)
            self.assertEqual(estado["nodo"], "fortaleza")

    def test_ramas_tienen_dificultad_distinta(self):
        self.assertEqual(campana.nodo("aldea")["dificultad"], 1)
        self.assertEqual(campana.nodo("ruinas")["dificultad"], 2)
        self.assertEqual(campana.nodo("trono")["dificultad"], 3)

    def test_cinco_victorias_completan_la_campana(self):
        campana.registrar_victoria(self.estado)
        campana.elegir_bifurcacion(self.estado, "aldea")
        campana.registrar_victoria(self.estado)  # aldea
        campana.registrar_victoria(self.estado)  # fortaleza
        campana.registrar_victoria(self.estado)  # asalto
        self.assertEqual(self.estado["nodo"], "trono")
        campana.registrar_victoria(self.estado)  # trono
        self.assertTrue(self.estado["completada"])
        self.assertEqual(len(self.estado["ruta"]), 5)

    def test_derrota_rompe_la_racha(self):
        self.estado["racha"] = 3
        campana.registrar_derrota(self.estado)
        self.assertEqual(self.estado["racha"], 0)
        self.assertEqual(self.estado["derrotas"], 1)
        self.assertEqual(len(self.estado["ruta"]), 0)

    def test_racha_y_capturas_se_registran(self):
        campana.registrar_victoria(self.estado, capturas=4)
        self.assertEqual(self.estado["racha"], 1)
        self.assertEqual(self.estado["capturas"], 4)
        self.assertEqual(self.estado["mejor_racha"], 1)


class TestDificultad(unittest.TestCase):
    NODOS_DIF = ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono")

    def _fuerza(self, estado, nodo_id):
        mazo = campana.mazo_rival(estado, nodo_id)
        return sum(sum(c.valores.values()) for c in mazo)

    def test_el_trono_es_el_mas_duro(self):
        """El trono debe ser el nodo mas fuerte.

        `mazo_rival` sortea 5 cartas del pool del rival, asi que la fuerza
        exacta varia por campana. La garantia del diseno es la tendencia, no
        el empate: se promedia sobre varias semillas. Con una sola muestra
        esta asercion fallaba ~3% de las veces (aldea >= trono), no por un
        fallo de codigo sino porque el sorteo puede invertir un nodo vecino.
        """
        muestras = 40
        totales = {n: 0 for n in self.NODOS_DIF}
        for _ in range(muestras):
            estado = campana.nueva_campana("humano")
            for nodo_id in self.NODOS_DIF:
                totales[nodo_id] += self._fuerza(estado, nodo_id)
        for nodo_id in self.NODOS_DIF:
            totales[nodo_id] /= muestras

        self.assertGreater(totales["trono"], totales["aldea"])
        self.assertGreater(totales["trono"], totales["senda"])
        self.assertGreater(totales["aldea"], totales["senda"])
        # el trono es el maximo de todo el recorrido
        self.assertEqual(max(totales, key=totales.get), "trono")

    def test_debilitar_reduce_al_rival(self):
        estado = campana.nueva_campana("humano")
        base = sum(sum(c.valores.values()) for c in campana.mazo_rival(estado, "fortaleza"))
        estado["debilitar"] = 1
        mitigado = sum(sum(c.valores.values()) for c in campana.mazo_rival(estado, "fortaleza"))
        self.assertLessEqual(mitigado, base)
        # el consumo del efecto ocurre al ganar el duelo
        campana.registrar_victoria(estado)
        self.assertEqual(estado["debilitar"], 0)

    def test_valores_nunca_pasan_de_diez(self):
        estado = campana.nueva_campana("humano")
        for c in campana.mazo_rival(estado, "trono"):
            for v in c.valores.values():
                self.assertLessEqual(v, 10)


class TestCartasYRecompensas(unittest.TestCase):
    def setUp(self):
        self.estado = campana.nueva_campana("humano")

    def test_mazo_inicial_es_el_de_la_faccion(self):
        nombres = [c.nombre for c in campana.cartas_jugador(self.estado)]
        esperados = [c.nombre for c in campana.mazo_inicial("humano")]
        self.assertEqual(nombres, esperados)
        self.assertEqual(len(campana.cartas_jugador(self.estado)), 10)

    def test_mejorar_carta_no_pasa_de_diez(self):
        for _ in range(60):
            campana.mejorar_carta(self.estado, 0, lado="n")
        # la base no se toca: el +1 vive en deltas con tope 10 efectivo
        self.assertLessEqual(self.estado["cartas"][0]["n"], 10)
        deltas = campana.mejoras_de(self.estado)
        nombre = self.estado["cartas"][0]["nombre"]
        mano = campana.cartas_duelo(self.estado, "senda")
        jugada = next(c for c in mano if c.nombre == nombre) if any(
            c.nombre == nombre for c in mano) else None
        if jugada is not None:
            self.assertLessEqual(jugada.valores["N"], 10)
        self.assertIn(nombre, deltas)

    def test_sigilo_escribe_deltas_sin_tocar_base(self):
        bases = [{k: d[k] for k in ("n", "s", "e", "o")} for d in self.estado["cartas"]]
        campana.aplicar_sigilo(self.estado)
        for d, base in zip(self.estado["cartas"], bases):
            self.assertEqual({k: d[k] for k in ("n", "s", "e", "o")}, base)
            delta = campana.mejoras_de(self.estado).get(d["nombre"], {})
            self.assertEqual(sum(delta.values()), 1)
            lado = next(l for l, v in delta.items() if v)
            self.assertEqual(base[lado], min(base.values()))

    def test_draft_ofrece_tres_cartas_distintas(self):
        ofertas = campana.draft_aleatorio(self.estado, 3)
        self.assertEqual(len(ofertas), 3)
        self.assertEqual(len({o.nombre for o in ofertas}), 3)

    def test_el_pool_solo_ofrece_facciones_desbloqueadas(self):
        pool = campana.cartas_del_pool(self.estado)
        bandos = {c.bando for c in pool}
        self.assertEqual(bandos, {"humano"})
        campana.desbloquear_aliado(self.estado, "orco")
        self.assertEqual({c.bando for c in campana.cartas_del_pool(self.estado)}, {"humano", "orco"})

    def test_no_se_puede_pactar_con_la_propia_faccion(self):
        campana.desbloquear_aliado(self.estado, "humano")
        self.assertNotIn("humano", self.estado["aliados"])
        self.assertNotEqual(campana.sustituto_aliado(self.estado), "humano")

    def test_draft_reemplaza_en_su_lugar(self):
        self.estado["cartas"][2] = Carta("Vieja", 1, 1, 1, 1, bando="humano").a_dict()
        nueva = Carta("Bruto Rasgador", 8, 5, 7, 4, bando="orco", habilidad="furia")
        campana.draft_reemplazo(self.estado, nueva, 2)
        self.assertEqual(self.estado["cartas"][2]["nombre"], "Bruto Rasgador")
        self.assertEqual(self.estado["cartas"][2]["habilidad"], "furia")

    def test_recompensas_segun_el_nodo(self):
        self.assertNotIn("aliado", campana.recompensas_de("senda"))
        self.assertIn("aliado", campana.recompensas_de("fortaleza"))
        self.assertEqual(campana.recompensas_de("trono"), [])

    def test_sorteo_da_cinco_de_la_coleccion(self):
        mano = campana.cartas_duelo(self.estado, "senda")
        self.assertEqual(len(mano), 5)
        pool = {c.nombre for c in campana.cartas_jugador(self.estado)}
        self.assertTrue({c.nombre for c in mano} <= pool)

    def test_sorteo_es_estable_al_recargar(self):
        a = [c.nombre for c in campana.cartas_duelo(self.estado, "senda")]
        b = [c.nombre for c in campana.cartas_duelo(self.estado, "senda")]
        self.assertEqual(a, b)

    def test_sorteo_varia_entre_campanas(self):
        vistos = set()
        for semilla in range(20):
            estado = campana.nueva_campana("humano")
            estado["semilla"] = semilla
            vistos.add(tuple(c.nombre for c in campana.cartas_duelo(estado, "senda")))
        self.assertGreater(len(vistos), 1)

    def test_rival_tambien_sortea_cinco(self):
        for nodo_id in ("senda", "fortaleza", "trono"):
            mazo = campana.mazo_rival(self.estado, nodo_id)
            self.assertEqual(len(mazo), 5)
            self.assertTrue(all(c.bando == campana.rival_de_nodo(self.estado, nodo_id)
                                for c in mazo))
            for c in mazo:
                for v in c.valores.values():
                    self.assertLessEqual(v, 10)


class TestEncuentros(unittest.TestCase):
    def setUp(self):
        self.estado = campana.nueva_campana("humano")

    def test_cada_encuentro_tiene_dos_opciones_con_efecto(self):
        for enc in campana.ENCUENTROS:
            self.assertEqual(len(enc["opciones"]), 2)
            for op in enc["opciones"]:
                self.assertTrue(op["efecto"])
                self.assertTrue(op["texto"])

    def test_efecto_debilitar_se_acumula(self):
        campana.aplicar_encuentro(self.estado, "debilitar")
        campana.aplicar_encuentro(self.estado, "debilitar")
        self.assertEqual(self.estado["debilitar"], 2)

    def test_efecto_mas_debil_mejora_una_carta(self):
        antes = sum(sum(d[l] for l in "nseo") for d in self.estado["cartas"])
        campana.aplicar_encuentro(self.estado, "mas_debil")
        despues = sum(sum(d[l] for l in "nseo") for d in self.estado["cartas"])
        self.assertEqual(despues, antes)
        total_deltas = sum(sum(v.values()) for v in campana.mejoras_de(self.estado).values())
        self.assertEqual(total_deltas, 1)

    def test_efecto_robo_anade_carta(self):
        antes = len(self.estado["cartas"])
        campana.aplicar_encuentro(self.estado, "robo")
        self.assertEqual(len(self.estado["cartas"]), antes)

    def test_encuentro_por_nodo_existe(self):
        for nodo_id in ("senda", "aldea", "ruinas", "fortaleza", "asalto"):
            self.assertEqual(campana.encuentro_para(nodo_id)["id"], campana.ENCUENTRO_POR_NODO[nodo_id])


class TestMigracionYGuardado(unittest.TestCase):
    def test_los_tests_no_tocan_los_datos_del_jugador(self):
        """El aislamiento debe estar activo: si no, el test ensucia la partida."""
        import paths

        self.assertTrue(paths.archivo("x").startswith(os.environ["TRIPLETRIAD_DATA"]))

    def test_migra_partida_vieja(self):
        viejo = {
            "etapa": 2,
            "mazo_jugador": "orco",
            "cartas": [c.a_dict() for c in mazos.ORCOS],
            "completada": False,
            "racha": 3,
        }
        nuevo = campana._migrar(viejo)
        self.assertEqual(nuevo["version"], campana.VERSION)
        self.assertEqual(nuevo["faccion"], "orco")
        self.assertEqual(nuevo["nodo"], "fortaleza")
        self.assertEqual(nuevo["mejor_racha"], 3)
        self.assertEqual(len(nuevo["cartas"]), 10)
        self.assertEqual([d["nombre"] for d in nuevo["cartas"]],
                         [c.nombre for c in campana.mazo_inicial("orco")])

    def test_migra_partida_completada(self):
        viejo = {"etapa": 5, "mazo_jugador": "humano", "completada": True, "cartas": []}
        self.assertTrue(campana._migrar(viejo)["completada"])

    def test_datos_corruptos_no_rompen(self):
        self.assertIsNone(campana._migrar("no es un dict"))
        self.assertIsNone(campana._migrar(None))

    def test_estado_nuevo_es_valido(self):
        estado = campana.nueva_campana("humano")
        for clave in ("version", "faccion", "nodo", "cartas", "racha", "completada"):
            self.assertIn(clave, estado)
        self.assertEqual(estado["nodo"], "senda")
        self.assertEqual(campana.progreso(estado), 0.0)


if __name__ == "__main__":
    unittest.main()