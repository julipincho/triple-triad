"""Tests del cartel de efecto (SAME, PLUS, CADENA).

El problema que cubren: antes, cualquier captura pintaba el mismo texto,
`CADENA DE n`, tanto si las n cartas cayeron por cadena como si dos cayeron por
same y dos por plus. El efecto era invisible y no se aprendia jugando.

Los tableros son los MISMOS ejemplos que da el tutorial, para que si el motor y
el tutorial dejaran de estar de acuerdo, este test lo note.
"""

import os
import sys
import time
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

import partida  # noqa: E402
import reglas  # noqa: E402
from reglas import CPU, USUARIO, Carta  # noqa: E402

pygame.init()
pantalla = pygame.display.set_mode((ui_ancho := 1280, 800))


def _c(n, s, e, o, dueno, bando="humano"):
    return Carta("T", n, s, e, o, bando=bando, dueno=dueno)


def _tablero():
    return [[None] * 3 for _ in range(3)]


def _juego(board):
    """Un Juego con lo justo para anunciar y dibujar el efecto."""
    juego = partida.Juego.__new__(partida.Juego)
    juego.board = board
    juego.bando = "elfo"
    juego.bando_cpu = "humano"
    juego.rival = None
    juego.efecto = None
    juego.banner = None
    juego._capa_ef = None
    juego._efecto_sup = None
    return juego


class TestDeteccionDeEfectos(unittest.TestCase):
    """Que regla se activo de verdad, no solo que cartas cayeron."""

    def test_same_del_tutorial_se_detecta_como_same(self):
        # "tu N 5 y tu O 7 contra dos 5 y 7 de enfrente"
        b = _tablero()
        b[1][0] = _c(9, 1, 7, 1, CPU)
        b[1][2] = _c(1, 1, 9, 5, CPU)
        b[1][1] = _c(5, 9, 5, 7, USUARIO, "elfo")
        caps, eventos = reglas.cascada(b, 1, 1)
        self.assertEqual(2, len(caps))
        self.assertEqual({"basica": 0, "cadena": 0, "same": 2},
                         reglas.resumen_efectos(eventos, (1, 1)))

    def test_plus_del_tutorial_se_detecta_como_plus(self):
        # "tu N 5 + su S 5 (=10) y tu E 6 + su O 4 (=10)"
        b = _tablero()
        b[0][1] = _c(9, 5, 1, 1, CPU)
        b[1][2] = _c(1, 1, 9, 4, CPU)
        b[1][1] = _c(5, 9, 6, 1, USUARIO, "elfo")
        caps, eventos = reglas.cascada(b, 1, 1)
        self.assertEqual(2, len(caps))
        self.assertEqual({"basica": 0, "cadena": 0, "plus": 2},
                         reglas.resumen_efectos(eventos, (1, 1)))

    def test_la_cadena_se_cuenta_por_el_origen(self):
        # Mi carta tumba a la de arriba, y esa tumba a la de su izquierda.
        b = _tablero()
        b[0][1] = _c(9, 1, 1, 9, CPU)
        b[0][0] = _c(9, 9, 1, 1, CPU)
        b[1][1] = _c(9, 9, 1, 1, USUARIO, "elfo")
        caps, eventos = reglas.cascada(b, 1, 1)
        resumen = reglas.resumen_efectos(eventos, (1, 1))
        self.assertEqual(2, len(caps))
        # Una cae porque la puse yo, la otra porque cayo la anterior.
        self.assertEqual(1, resumen["cadena"])

    def test_una_captura_suelta_no_es_una_cadena(self):
        b = _tablero()
        b[0][1] = _c(9, 1, 1, 1, CPU)
        b[1][1] = _c(9, 9, 1, 1, USUARIO, "elfo")
        caps, eventos = reglas.cascada(b, 1, 1)
        self.assertEqual(1, len(caps))
        self.assertEqual({"basica": 1, "cadena": 0},
                         reglas.resumen_efectos(eventos, (1, 1)))

    def test_cascada_sigue_dando_las_mismas_carturas_que_capturas(self):
        """`capturas` es la mitad izquierda de `cascada`. Si divergen, el juego
        resuelve una cosa y el cartel canta otra."""
        import copy
        import random
        azar = random.Random(7)
        for _ in range(200):
            b = _tablero()
            for r in range(3):
                for c in range(3):
                    if azar.random() < 0.6:
                        b[r][c] = _c(*(azar.randint(1, 10) for _ in range(4)),
                                     azar.choice((USUARIO, CPU)))
            origen = next(((r, c) for r in range(3) for c in range(3)
                           if b[r][c] is not None), None)
            if origen is None:
                continue
            # La copia se hace ANTES de nada: `capturas` y `cascada` voltean
            # cartas en el tablero que reciben, y comparar el original ya
            # capturado contra una copia suya daria siempre cero capturas.
            copia = copy.deepcopy(b)
            esperado = reglas.capturas(b, origen[0], origen[1])
            caps, _ = reglas.cascada(copia, origen[0], origen[1])
            self.assertEqual(sorted(esperado), sorted(caps))


class TestAnuncioDelEfecto(unittest.TestCase):
    def test_el_same_se_anuncia_con_su_nombre(self):
        juego = _juego(_tablero())
        ahora = time.time()
        juego._anunciar_efecto({"basica": 0, "cadena": 0, "same": 2}, ahora, USUARIO)
        self.assertIsNotNone(juego.efecto)
        titulo, _t0, _color, sub, regla = juego.efecto
        self.assertEqual("SAME", titulo)
        self.assertEqual("same", regla)
        self.assertIn("2 por same", sub)

    def test_el_plus_se_anuncia_con_su_nombre(self):
        juego = _juego(_tablero())
        juego._anunciar_efecto({"basica": 0, "cadena": 0, "plus": 2},
                               time.time(), USUARIO)
        self.assertEqual("PLUS", juego.efecto[0])

    def test_la_cadena_dice_cuantas_cartas_cayeron(self):
        juego = _juego(_tablero())
        juego._anunciar_efecto({"basica": 2, "cadena": 2}, time.time(), USUARIO)
        self.assertEqual("CADENA DE 4", juego.efecto[0])

    def test_una_captura_normal_no_pone_nada(self):
        """Sin same, sin plus y sin cadena no hay efecto que nombrar. Antes
        ponia `CADENA DE 1`, que no es una cadena ni de nombre."""
        juego = _juego(_tablero())
        juego._anunciar_efecto({"basica": 1, "cadena": 0}, time.time(), USUARIO)
        self.assertIsNone(juego.efecto)

    def test_cuando_hay_same_el_propio_no_avisa_dos_veces(self):
        """El cartel del efecto y el banner se pisan en el mismo sitio del
        tablero. Si los dos se pintan a la vez se leen fatal."""
        juego = _juego(_tablero())
        juego.banner = ("CADENA DE 2", time.time(), (255, 255, 255), "x")
        juego._anunciar_efecto({"basica": 0, "cadena": 0, "same": 2},
                               time.time(), USUARIO)
        self.assertIsNone(juego.banner)

    def test_el_reparto_suma_lo_que_cayo_de_verdad(self):
        juego = _juego(_tablero())
        juego._anunciar_efecto(
            {"basica": 2, "cadena": 1, "same": 3}, time.time(), USUARIO)
        sub = juego.efecto[3]
        self.assertIn("6 cartas", sub)
        self.assertIn("3 por same", sub)
        self.assertIn("1 por cadena", sub)
        self.assertIn("2 directas", sub)

    def test_el_cartel_no_dura_eternamente(self):
        """Un cartel que no se apaga tapa el tablero y es peor que no tenerlo."""
        juego = _juego(_tablero())
        t0 = time.time()
        juego.efecto = ("SAME", t0, (200, 200, 200), "x", "same")
        juego._dibujar_efecto(pantalla, t0 + partida.DURACION_EFECTO + 0.1)
        self.assertIsNone(juego.efecto)


class TestCartelSeDibuja(unittest.TestCase):
    def setUp(self):
        self.juego = _juego(_tablero())
        self.juego.efecto = ("SAME", time.time(), (140, 190, 255),
                             "caen dos vecinas porque igualan tu numero."
                             "  2 cartas: 2 por same", "same")

    def test_dibujar_el_cartel_no_reventa(self):
        self.juego._dibujar_efecto(pantalla, time.time() + 0.3)

    def test_el_titulo_no_se_sale_del_cartel(self):
        """El caso que paso al principio: la caja se ajustaba al texto medido
        con una fuente y el filete de debajo se salia por los lados."""
        import ui
        for titulo in ("SAME", "PLUS", "CADENA DE 2", "CADENA DE 9"):
            self.juego._efecto_sup = None
            caja = self.juego._superficie_efecto(
                titulo, "caen dos vecinas porque igualan tu numero.  "
                        "8 cartas: 4 por same, 2 por cadena, 2 directas",
                (140, 190, 255))
            self.assertLessEqual(caja.get_width(), 1280 - 80)
            self.assertGreaterEqual(caja.get_width(),
                                    ui.ancho_texto(titulo, 40),
                                    "el titulo se sale de la caja")

    def test_dos_efectos_seguidos_no_dejan_el_anterior_debajo(self):
        """La capa de trabajo se reutiliza y el fondo del cartel es
        semitransparente. Sin limpiar, el titulo anterior asomaba."""
        t0 = time.time()
        self.juego._dibujar_efecto(pantalla, t0 + 0.3)
        antes = pantalla.copy()
        self.juego.efecto = ("PLUS", t0, (140, 190, 255),
                             "caen dos vecinas porque sus sumas coinciden."
                             "  2 cartas: 2 por plus", "plus")
        self.juego._dibujar_efecto(pantalla, t0 + 0.3)
        self.assertNotEqual(pygame.image.tostring(antes, "RGB"),
                            pygame.image.tostring(pantalla, "RGB"),
                            "el segundo efecto no se ve: la capa no se limpia")


if __name__ == "__main__":
    unittest.main()
