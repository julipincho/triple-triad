"""G8: la curva de dificultad tiene que SER MONOTONA en su tramo final.

Descubierto midiendo con el motor real (`tools/simular_g8.py`): con
`MAX_REFUERZO_RIVAL = 2`, el tope se alcanzaba ya en el nivel 2, asi que el
trono (nivel 3) recibia EXACTAMENTE el mismo refuerzo que el asalto. Medido con
mazo de 10 cartas el jefe salia al 58.4% de victorias del jugador y el asalto
al 55.2%: el climas de la campana era mas facil que el nodo anterior.

Aqui se ata la propiedad estructural, que es lo que se rompio. La cifra
concreta de dificultad se calibra con playtest humano; esto solo comprueba que
la maquina no vuelva a igualar al jefe con el nodo previo.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import campana  # noqa: E402
from reglas import LADOS  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402

#: Nodos de duelo de la campana, en orden de avance.
NODOS_DUELO = ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono")

_TMP = tempfile.TemporaryDirectory(prefix="tt_curva_")
os.environ["TRIPLETRIAD_DATA"] = _TMP.name


def dificultad(nodo, faccion="humano"):
    """La dificultad que el motor le pasa al rival en ese nodo."""
    estado = campana.nueva_campana(faccion)
    campana.asegurar_coleccion(faccion)
    campana.guardar(estado)
    return campana.info_duelo(estado, nodo)["dificultad"]


def refuerzo_de(nivel, tope):
    """El refuerzo que recibe el rival en un nodo de ese nivel."""
    return min(nivel, tope)


class TestElSimuladorEsReproducible(unittest.TestCase):
    """Sin esto, cualquier A/B de balance compara ruido con ruido.

    La IA del motor usa `random.uniform` del modulo global y `nueva_campana`
    sortea la semilla de la partida con `random.getrandbits`. Sin sembrar en los
    dos sitios, dos corridas con la misma semilla dan resultados distintos y el
    "A/B pareado" no es pareado. Este test es el que avisa.
    """

    def test_dos_corridas_con_la_misma_semilla_coinciden(self):
        import importlib.util
        import json

        import pygame

        pygame.init()
        pygame.display.set_mode((ANCHO, ALTO))
        ruta = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "tools", "simular_g8.py")
        spec = importlib.util.spec_from_file_location("sim_g8_test", ruta)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["sim_g8_test"] = mod
        spec.loader.exec_module(mod)

        comunes = {"humano": 1.2, "orco": 1.2, "elfo": 1.2, "goblin": 1.2,
                   "hombre_lobo": 1.2, "vampiro": 1.2, "elfo_nocturno": 1.2,
                   "hombre_pantera": 1.2, "hombre_lagarto": 1.2}
        a = mod.informe(list(comunes), ("trono",), 12, 4242, 10, 5)
        b = mod.informe(list(comunes), ("trono",), 12, 4242, 10, 5)
        self.assertEqual(
            [f["pct"] for f in a], [f["pct"] for f in b],
            "el simulador no es reproducible: las cifras no significan nada")


class TestElJefeNoSeQuedaIgualAlNodoPrevio(unittest.TestCase):
    def test_el_trono_recibe_mas_refuerzo_que_el_asalto(self):
        top = campana.MAX_REFUERZO_RIVAL
        nivel_asalto = dificultad("asalto")
        nivel_trono = dificultad("trono")
        self.assertGreater(nivel_trono, nivel_asalto,
                           "el trono deberia estar por encima del asalto")
        self.assertGreater(refuerzo_de(nivel_trono, top),
                           refuerzo_de(nivel_asalto, top),
                           "con este tope, trono y asalto reciben el mismo "
                           "refuerzo: el jefe pierde su identidad")

    def test_el_tope_permite_llegar_al_ultimo_nodo(self):
        """El tope debe alcanzar el nivel del trono; si no, el tope es el jefe."""
        nivel_maximo = max(dificultad(n) for n in NODOS_DUELO)
        self.assertGreaterEqual(campana.MAX_REFUERZO_RIVAL, nivel_maximo,
                                "MAX_REFUERZO_RIVAL corta el refuerzo del jefe")

    def test_el_primer_nodo_no_recibe_refuerzo(self):
        """La senda es la puerta de entrada: sin refuerzo."""
        nivel = dificultad("senda")
        self.assertEqual(refuerzo_de(nivel, campana.MAX_REFUERZO_RIVAL), 0)

    def test_la_curva_no_baja_en_el_tramo_medio(self):
        """Los nodos intermedios no pueden ser mas faciles que los tempranos.

        No se impone un 50% artificial: solo que la dificultad NO retroceda
        entre senda, aldea y el tramo deasalto/fortaleza.
        """
        orden = ("senda", "aldea", "ruinas", "fortaleza")
        niveles = [dificultad(n) for n in orden]
        self.assertEqual(niveles, sorted(niveles),
                         "los niveles de dificultad no crecen con el avance")


class TestElRefuerzoNoSePasaDeDiez(unittest.TestCase):
    def test_ningun_lado_supera_el_diez(self):
        """El refuerzo tiene tope por lado: un 11 no existe en este juego."""
        import random

        from reglas import Carta

        guardado = campana.MAX_REFUERZO_RIVAL
        try:
            campana.MAX_REFUERZO_RIVAL = 9
            estado = campana.nueva_campana("humano")
            campana.asegurar_coleccion("humano")
            campana.guardar(estado)
            cartas = campana.mazo_rival(estado, "trono")
            for c in cartas:
                for lado in LADOS:
                    self.assertLessEqual(c.valores[lado], 10)
                    self.assertGreaterEqual(c.valores[lado], 1)
        finally:
            campana.MAX_REFUERZO_RIVAL = guardado

    def test_debilitar_resta_refuerzo_al_rival(self):
        """Los encuentros que debilitan tienen que notarse de verdad."""
        estado = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        campana.guardar(estado)
        antes = [sum(c.valores.values()) for c in campana.mazo_rival(estado, "trono")]
        estado["debilitar"] = 1
        campana.guardar(estado)
        despues = [sum(c.valores.values()) for c in campana.mazo_rival(estado, "trono")]
        self.assertLess(sum(despues), sum(antes),
                        "debilitar=1 no redujo el mazo rival")

    def test_debilitar_se_sigue_notando_en_el_tercer_encuentro(self):
        """El texto del encuentro promete un efecto: no puede saturar en silencio.

        Con el tope de refuerzo en 2, los nodos de nivel 2 llegaban a su tope en
        el segundo `debilitar` y el tercero ya no hacia nada: la promesa mecanica
        se cumplia dos veces y luego dejaba de cumplirse. El trono debe conservar
        margen al menos hasta el tercero.

        OJO: se fija la semilla global ANTES de crear la campana. `mazo_rival`
        sortea con `estado["semilla"]`, que `nueva_campana` genera al azar; sin
        fijarla, el mazo rival cambia en cada ejecucion y la cifra que se
        comprueba aqui depende de la suerte. Asi el test era inestable: pasaba
        6 de 7 veces y fallaba de vez en cuando.
        """
        import random

        from reglas import total_carta

        random.seed(20261010)
        estado = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        campana.guardar(estado)
        fuerzas = []
        for veces in (0, 1, 2, 3):
            estado["debilitar"] = veces
            campana.guardar(estado)
            fuerzas.append(sum(total_carta(c) for c in campana.mazo_rival(estado, "trono")))
        # cada escalon debe restar algo mas que el anterior
        for i in range(3):
            self.assertGreater(fuerzas[i], fuerzas[i + 1],
                               f"debilitar={i + 1} no resto nada en el trono")
        self.assertGreater(fuerzas[0] - fuerzas[3], 30,
                           f"tres encuentros de debilitar deberian notarse: "
                           f"{fuerzas[0]} -> {fuerzas[3]}")


if __name__ == "__main__":
    unittest.main()