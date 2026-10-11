"""G8: propiedades estructurales de la economia que no deben romperse.

Los numeros de ritmo (3-4 sobres por campana, 9 duelos) salen de la simulacion
`tools/economia_g8.py`, que no se ata aqui porque seria atar ruido. Lo que si
se ata son las relaciones que, si se rompen, hacen el juego injugable:

  - un duelo completo debe pagar algo, y abandonar nada
  - un sobre no puede costar mas que varias victorias seguidas (bloqueo)
  - el trono no da recompensa (es el remate)
  - la garantia tiene que ser alcanzable dentro de una campana

Ninguno de estos test mira el simulador: mira las reglas del juego.
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
from partida import Resultado  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(prefix="tt_eco_")
        self.addCleanup(self.d.cleanup)
        os.environ["TRIPLETRIAD_DATA"] = self.d.name

    def _campana(self, faccion="humano"):
        campana.guardar_perfil({})
        estado = campana.nueva_campana(faccion)
        campana.asegurar_coleccion(faccion)
        campana.guardar(estado)
        return estado


class TestCosteDeLoQueSeCompra(Base):
    def test_un_duelo_completado_paga(self):
        estado = self._campana()
        campana.gastar_moneda(campana.moneda())
        ganada = campana.registrar_resultado(estado, Resultado(True, 3, 9, (5, 4)))
        self.assertGreater(ganada, 0)

    def test_abandonar_no_paga_nada(self):
        """El incentivo tramposo: cobrar por marcharse rompe la campana."""
        estado = self._campana()
        campana.gastar_moneda(campana.moneda())
        r = Resultado(False, 3, 9, (3, 5))
        r.abandonado = True
        self.assertEqual(campana.registrar_resultado(estado, r), 0)
        self.assertEqual(campana.moneda(), 0)

    def test_ganar_paga_mas_que_perder(self):
        estado_a = self._campana("humano")
        estado_b = campana.cargar()
        campana.guardar_perfil({})
        campana.gastar_moneda(campana.moneda())
        perder = campana.registrar_resultado(estado_a, Resultado(False, 3, 9, (3, 5)))

        estado_b = self._campana("humano")
        campana.guardar_perfil({})
        campana.gastar_moneda(campana.moneda())
        ganar = campana.registrar_resultado(estado_b, Resultado(True, 3, 9, (5, 3)))
        self.assertGreater(ganar, perder)


class TestElSobreNoEsUnMuro(Base):
    def test_tres_victorias_alcanzan_para_un_sobre(self):
        """Si tres victorias no compran un sobre, la tienda es un adorno.

        Con el ritmo medido (~9 duelos y ~3 sobres por campana), un jugador
        tiene que poder comprar varias veces. Si el precio se subiera por
        encima de varias victorias, dejaria de poder.
        """
        tres = campana.MONEDA_VICTORIA * 3
        self.assertGreaterEqual(tres, campana.PRECIO_SOBRE,
                                f"tres victorias ({tres}) no alcanzan un sobre "
                                f"({campana.PRECIO_SOBRE}): la tienda no se usa")

    def test_la_garantia_acumula_entre_campanas(self):
        """El pity vive en el PERFIL, no en la campana.

        Con ~3-4 sobres por campana y PITY_SOBRES=10, la garantia no se
        alcanzaria nunca si contase por partida. Al vivir en el perfil, cruza
        de una campana a otra y el jugador la ve. Esto no es un accidente: es lo
        que hace que abrir sobres a lo largo de varias partidas tenga premio.
        """
        self._campana("humano")
        campana.ganar_moneda(1000)
        campana.comprar_sobre(campana.cargar())
        self.assertIn("pity_sobres", campana.cargar_perfil(),
                      "la garantia deberia vivir en el perfil para cruzar campanas")

    def test_la_garantia_se_acumula_realmente(self):
        """Comprar sin legendaria debe subir el contador, no dejarlo igual."""
        self._campana("humano")
        campana.gastar_moneda(campana.moneda())
        campana.ganar_moneda(1000)
        antes = campana.pity_sobres()
        for _ in range(3):
            campana.comprar_sobre(campana.cargar())
        self.assertGreater(campana.pity_sobres(), antes,
                           "tres sobres sin legendaria no movieron la garantia")


class TestEstructuraDeRecompensas(Base):
    def test_el_trono_no_da_recompensa(self):
        """Es el remate: ganar cierra la campana, no da carta."""
        estado = self._campana()
        self.assertEqual(campana.recompensas_de("trono"), [])

    def test_los_cinco_nodos_de_medio_si_dan_recompensa(self):
        estado = self._campana()
        for nodo in ("senda", "aldea", "ruinas", "fortaleza", "asalto"):
            self.assertTrue(campana.recompensas_de(nodo),
                            f"{nodo} se queda sin recompensa")

    def test_toda_recompensa_sabe_aplicarse_sin_entrada(self):
        """El simulador elige premios automaticos: deben existir sin elegir nada.

        `sigilo` no necesita elegir carta ni indice. Si un nodo solo ofreciera
        `recluta`, el flujo automatico se romperia.
        """
        estado = self._campana()
        for nodo in ("senda", "aldea", "ruinas", "fortaleza", "asalto"):
            opc = campana.recompensas_de(nodo)
            automaticas = [k for k in ("sigilo", "aliado", "sobre") if k in opc]
            if not automaticas:
                self.assertIn("entrenamiento", opc,
                              f"{nodo} no tiene ninguna recompensa automatizable")


if __name__ == "__main__":
    unittest.main()