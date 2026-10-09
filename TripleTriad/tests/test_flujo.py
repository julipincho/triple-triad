"""Prueba de flujo: recorre una campana entera sin ventanas.

Se sustituyen las pantallas y el duelo por dobles de prueba para verificar
que el enrutado de la campana (nodos, ramas, recompensas, encuentros y final)
funciona de principio a fin y que nunca te juegas contra tu faccion.
"""

import asyncio
import os
import sys
import tempfile
import unittest

# Los tests no deben tocar los datos del jugador (campana.json / perfil.json)
os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import campana  # noqa: E402
import cinematicas  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
import pantallas  # noqa: E402
import pygame  # noqa: E402
from partida import Resultado  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


def setUpModule():
    """pygame necesita una superficie para convertir imagenes."""
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))


class RelojFalso:
    def tick(self, fps=60):
        return 16

    def get_fps(self):
        return 60


class TestFlujoDeCampana(unittest.TestCase):
    """Simula la campaña completa para cada faccion."""

    def _simular(self, faccion, victorias=True, perdidas=0, rama="aldea", recompensa="entrenamiento"):
        import main
        from partida import Juego

        registro = {"rivales": [], "pantallas": [], "duelos": 0, "epilogue": 0}
        originales = {}

        async def ara(*args, **kwargs):
            """Sustituto de las pantallas que no queremos exerts de verdad."""
            return None

        # espia sobre el mazo rival: es lo que ve el jugador en cada duelo
        def mazo_rival(estado, nodo_id=None, dificultad_extra=0):
            rival = campana.rival_de_nodo(estado, nodo_id)
            registro["rivales"].append((campana.nodo_actual(estado), rival))
            return mazos.TODOS[rival]

        async def duelo_falso(screen, clock, juego, test_mode=False):
            registro["duelos"] += 1
            if registro["duelos"] > 14:
                raise AssertionError("bucle infinito de duelos")
            # se pierden los primeros `perdidas` duelos
            gana = victorias and registro["duelos"] > perdidas
            return Resultado(gana, 2, 5, (5, 4), False, 1)

        async def derrota_falsa(screen, clock, estado):
            registro["pantallas"].append(("derrota", estado["nodo"]))
            return "reintentar"

        async def mapa_falso(screen, clock, estado):
            registro["pantallas"].append(("mapa", estado["nodo"]))
            return "seguir"

        async def rama_falsa(screen, clock, estado):
            return rama

        async def recompensa_falsa(screen, clock, estado, nodo_id):
            registro["pantallas"].append(("recompensa", nodo_id, recompensa))
            return recompensa

        async def encuentro_falso(screen, clock, estado, nodo_id):
            registro["pantallas"].append(("encuentro", nodo_id))

        async def decision_falsa(screen, clock, estado, decision):
            """La decision moral aplica su primer efecto y sigue."""
            registro["pantallas"].append(("decision", decision["id"]))
            campana.decidir(estado, decision["id"], decision["opciones"][0]["efecto"])

        async def epilogo_falso(screen, clock, estado):
            registro["epilogue"] += 1
            # el epilogo real cierra la campana y registra el final
            campana.completar(estado)
            registro["pantallas"].append(("epilogo", dict(estado["final"])))

        reemplazos = {
            "campana.mazo_rival": mazo_rival,
            # main importa la funcion por su nombre: hay que parchear alli
            "main.partida": duelo_falso,
            "pantallas.mapa_campana": mapa_falso,
            "pantallas.elegir_rama": rama_falsa,
            "pantallas.recompensa": recompensa_falsa,
            "pantallas.aplicar_recompensa": ara,
            "pantallas.encuentro": encuentro_falso,
            "pantallas.derrota": derrota_falsa,
            "pantallas.epilogo": epilogo_falso,
            "pantallas.decision_narrativa": decision_falsa,
            # El cartel del NG+ (fragmento de verdad). Antes no hacia falta
            # parchearlo porque `_ganar_fragmento` llamaba a `cartel` SIN
            # `pantallas.` y reventaba con NameError antes de llegar al cartel:
            # el test no colgaba, pero porque la linea estaba rota. Al
            # arreglarla, el cartel real se ejecuta y espera un clic eterno.
            "pantallas.cartel": ara,
            "cinematicas.reproducir": ara,
        }
        for ruta, fn in reemplazos.items():
            modulo, nombre = ruta.split(".")
            originales[ruta] = getattr(sys.modules[modulo], nombre)
            setattr(sys.modules[modulo], nombre, fn)
        try:
            estado = campana.nueva_campana(faccion)
            asyncio.run(main._campana(pygame.display.get_surface(), RelojFalso(),
                                      estado, nuevo=True))
            return estado, registro
        finally:
            for ruta, fn in originales.items():
                modulo, nombre = ruta.split(".")
                setattr(sys.modules[modulo], nombre, fn)

    def test_campana_humana_llega_al_final_humano(self):
        estado, reg = self._simular("humano")
        self.assertTrue(estado["completada"])
        self.assertEqual(len(estado["ruta"]), 5)
        self.assertEqual(estado["final"]["faccion"], "humano")
        self.assertEqual(estado["final"]["titulo"], campana.FINALES["humano"][estado["final"]["variante"]]["titulo"])
        self.assertEqual(estado["victorias"], 5)
        self.assertEqual(estado["racha"], 5)

    def test_las_decisiones_morales_se_disparan_durante_la_campana(self):
        """La senda y la fortaleza piden decision; se registran en el estado."""
        import narrativa
        estado, reg = self._simular("humano")
        decisiones = [p[1] for p in reg["pantallas"] if p[0] == "decision"]
        self.assertIn(narrativa.DECISION["senda"]["id"], decisiones)
        self.assertIn(narrativa.DECISION["fortaleza"]["id"], decisiones)
        # el efecto se aplico de verdad: no basta con que la pantalla se viera
        for did in decisiones:
            self.assertIn(did, estado["decisiones"])

        # el doble de prueba elige siempre la primera opcion, asi que el saldo
        # es la suma de los efectos de esas opciones (senda +1, fortaleza -1).
        # `decisiones` guarda el id de la decision ("senda_herido"), no el nodo.
        por_id = {d["id"]: d for d in narrativa.DECISION.values()}
        esperado = sum(por_id[d]["opciones"][0]["efecto"].get("confianza", 0)
                       for d in decisiones)
        self.assertEqual(estado["confianza_nara"], esperado)
        self.assertGreater(estado["conocimiento_umbral"], 0)

    def test_la_decision_no_se_pregunta_dos_veces(self):
        estado, reg = self._simular("humano")
        decisiones = [p[1] for p in reg["pantallas"] if p[0] == "decision"]
        self.assertEqual(len(decisiones), len(set(decisiones)))

    def test_campana_orca_llega_al_final_orco(self):
        estado, reg = self._simular("orco")
        self.assertTrue(estado["completada"])
        self.assertEqual(estado["final"]["faccion"], "orco")
        self.assertEqual(len(estado["ruta"]), 5)

    def test_ganar_sin_reintentos_da_final_de_dominio(self):
        estado, reg = self._simular("humano")
        self.assertEqual(estado["final"]["variante"], "dominio")

    def test_derrotas_cambian_el_final_a_caos(self):
        # pierde 4 veces y luego gana los cinco duelos
        estado, reg = self._simular("humano", perdidas=4)
        self.assertTrue(estado["completada"])
        self.assertEqual(estado["derrotas"], 4)
        self.assertEqual(estado["final"]["variante"], "caos")
        # el epilogo se pide igualmente
        self.assertEqual(reg["epilogue"], 1)

    def test_racha_se_rompe_al_perder(self):
        estado, reg = self._simular("orco", perdidas=2)
        self.assertTrue(estado["completada"])
        self.assertEqual(estado["victorias"], 5)
        self.assertEqual(estado["derrotas"], 2)
        # tras perder dos veces, la racha final vuelve a 5 duelos
        self.assertEqual(estado["racha"], 5)
        self.assertEqual(estado["mejor_racha"], 5)
        self.assertEqual(estado["final"]["variante"], "equilibrio")

    def test_nunca_se_juega_contra_la_propia_faccion(self):
        for faccion in facciones.orden_facciones():
            _, reg = self._simular(faccion)
            self.assertTrue(reg["rivales"], faccion)
            for nodo, rival in reg["rivales"]:
                self.assertNotEqual(rival, faccion, f"{faccion} contra si mismo en {nodo}")

    def test_el_jefe_final_es_el_arcoenemigo_de_cada_faccion(self):
        for faccion in facciones.orden_facciones():
            _, reg = self._simular(faccion)
            self.assertEqual(reg["rivales"][-1][1], facciones.rival_final(faccion))

    def test_la_rama_elegida_cambia_el_rival(self):
        _, reg_a = self._simular("humano", rama="aldea")
        _, reg_b = self._simular("humano", rama="ruinas")
        self.assertNotEqual(reg_a["rivales"][1], reg_b["rivales"][1])

    def test_se_pide_recompensa_tras_cada_victoria(self):
        _, reg = self._simular("humano")
        recompensas = [p for p in reg["pantallas"] if p[0] == "recompensa"]
        # 4 recompensas: la del trono no existe
        self.assertEqual(len(recompensas), 4)

    def test_se_llega_al_epilogo_una_vez(self):
        _, reg = self._simular("orco")
        self.assertEqual(reg["epilogue"], 1)
        self.assertEqual([p[0] for p in reg["pantallas"] if p[0] == "epilogo"], ["epilogo"])

    def test_varios_duelos_por_nodo(self):
        _, reg = self._simular("elfo")
        # 5 duelos + bifurcacion (mapa) + 4 recompensas + 1 epilogo
        self.assertEqual(reg["duelos"], 5)


if __name__ == "__main__":
    unittest.main()