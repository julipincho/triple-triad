"""Tests del tooltip de las cartas del tablero.

El fallo que cubren: la mano tenia tooltip desde hacia tiempo y el tablero
ninguno. Es decir, las habilidades del rival no se veian. Informacion que el
juego te oculta justo cuando mas la necesitas, que es al planning, con el
rival ya comprometido en el centro del tablero.

El contenido sale de la MISMA funcion para mano y tablero. Si anaden una linea
a una y no a la otra, las dos se desincronizan y solo se nota en juego.
"""

import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

import cartas as crt  # noqa: E402
import partida  # noqa: E402
from reglas import CPU, USUARIO, Carta  # noqa: E402

pygame.init()
PANTALLA = pygame.display.set_mode((1280, 800))


def _juego():
    juego = partida.Juego("elfo", "humano")
    return juego


class TestTooltipDelTablero(unittest.TestCase):
    def setUp(self):
        self.juego = _juego()

    def _lineas(self, carta, synergy=False, dueno_extra=None):
        return self.juego._lineas_tooltip(carta, synergy, dueno_extra)

    def test_dice_de_quien_es_la_carta(self):
        """Una carta cambia de bando cada vez que la capturan. Sin decir de
        quien es, el jugador no sabe si lo que ve es suyo o del rival."""
        carta = Carta("X", 5, 5, 5, 5, bando="humano", dueno=CPU)
        self.assertIn("DEL RIVAL", self._lineas(carta, dueno_extra="DEL RIVAL"))
        propio = Carta("Y", 5, 5, 5, 5, bando="elfo", dueno=USUARIO)
        self.assertNotIn("DEL RIVAL", self._lineas(propio, dueno_extra="TUYA"))

    def test_enseña_los_cuatro_lados(self):
        carta = Carta("X", 1, 2, 3, 4, bando="humano", dueno=CPU)
        texto = self._lineas(carta)
        for esperado in ("N: 1", "S: 2", "E: 3", "O: 4"):
            self.assertIn(esperado, texto)

    def test_enseña_la_habilidad_con_su_explicacion(self):
        for habilidad in crt.HABILIDADES:
            carta = Carta("X", 5, 5, 5, 5, bando="humano",
                          dueno=CPU, habilidad=habilidad)
            texto = self._lineas(carta)
            self.assertIn(crt.descripcion_habilidad(habilidad), texto,
                          "la habilidad %s no sale en el tooltip" % habilidad)

    def test_una_carta_sin_habilidad_lo_dice(self):
        carta = Carta("X", 5, 5, 5, 5, bando="humano", dueno=CPU)
        self.assertIn("Sin habilidad especial", self._lineas(carta))

    def test_avisa_de_la_sinergia_solo_si_la_hay(self):
        carta = Carta("X", 5, 5, 5, 5, bando="elfo", dueno=USUARIO)
        self.assertNotIn("SINERGIA", self._lineas(carta, synergy=False))
        self.assertIn("SINERGIA", self._lineas(carta, synergy=True))

    def test_la_mano_y_el_tablero_ensen_lo_mismo(self):
        """Una sola funcion para los dos sitios. Es lo que evita que se
        desincronicen."""
        carta = Carta("X", 3, 4, 5, 6, bando="humano", dueno=USUARIO,
                      habilidad="muro")
        con_dueño = self._lineas(carta, dueno_extra="TUYA")
        # la mano llama sin `dueno_extra`: lo unico que puede cambiar es esa linea
        self.assertEqual(con_dueño.replace("\nTUYA", ""),
                         self._lineas(carta).replace("\nTUYA", ""))
        self.assertIn("MURO", con_dueño)
        self.assertIn("MURO", self._lineas(carta))


class TestHoverSobreElTablero(unittest.TestCase):
    def setUp(self):
        self.juego = _juego()
        self.rival = self.juego.mano_c.pop(0)
        self.rival.dueno = CPU
        self.juego.board[1][1] = self.rival

    def test_al_pasar_por_encima_del_rival_no_revienta(self):
        from ui import celda_rect
        celda = celda_rect(1, 1)
        pygame.mouse.get_pos = lambda: celda.center
        try:
            self.juego.dibujar(PANTALLA)
        finally:
            import importlib
            importlib.reload(pygame.mouse)

    def test_el_resplandor_no_se_dibuja_sin_raton_sobre_la_carta(self):
        """Con el raton lejos, `_dibujar_tablero` no debe encolar tooltip: se
        acumularian por frame y `dibujar_tooltips` los pinta todos."""
        from ui import celda_rect
        pygame.mouse.get_pos = lambda: (0, 0)
        try:
            celda = celda_rect(1, 1)
            for _ in range(5):
                self.juego.dibujar(PANTALLA)
            import ui
            self.assertEqual([], ui._PENDIENTES,
                             "se encolaron tooltips sin que el raton este "
                             "sobre ninguna carta")
            self.assertFalse(celda.collidepoint((0, 0)))
        finally:
            import importlib
            import pygame as _pg
            importlib.reload(_pg.mouse)


if __name__ == "__main__":
    unittest.main()
