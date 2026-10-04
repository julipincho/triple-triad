"""Tests de reglas de Triple Triad."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reglas import CPU, USUARIO, Carta, capturas, celdas_vacias, contar, simular


def carta(n, s, e, o, dueno):
    c = Carta("test", n, s, e, o)
    c.dueno = dueno
    return c


def tablero_vacio():
    return [[None] * 3 for _ in range(3)]


class TestCapturas(unittest.TestCase):
    def test_sin_captura(self):
        b = tablero_vacio()
        b[0][0] = carta(5, 5, 5, 5, CPU)
        b[0][1] = carta(5, 5, 5, 5, USUARIO)  # E=5 no supera O=5
        self.assertEqual(capturas(b, 0, 1), [])
        self.assertEqual(b[0][0].dueno, CPU)

    def test_captura_simple(self):
        b = tablero_vacio()
        b[0][0] = carta(5, 5, 3, 5, CPU)
        b[0][1] = carta(5, 5, 5, 5, USUARIO)  # O... espera, USUARIO arraeja; la carta en 0,1 ya está puesta
        # la carta puesta es USUARIO en (0,1); su O=5 no supera E=3 de CPU? 5>3 sí -> captura
        caps = capturas(b, 0, 1)
        self.assertEqual(caps, [(0, 0)])
        self.assertEqual(b[0][0].dueno, USUARIO)

    def test_captura_cadena(self):
        # USUARIO juega en (1,1) con E alto; captura a CPU en (1,2) que a su vez
        # tiene S alto y captura a CPU en (2,2)
        b = tablero_vacio()
        b[1][2] = carta(2, 9, 2, 2, CPU)   # su O=2 será superado; su S=9
        b[2][2] = carta(2, 2, 2, 8, CPU)   # su N=2 será superado por S=9 del recién capturado
        b[1][1] = carta(2, 2, 9, 2, USUARIO)  # E=9 > O=2
        caps = capturas(b, 1, 1)
        self.assertIn((1, 2), caps)
        self.assertIn((2, 2), caps)
        self.assertEqual(b[1][2].dueno, USUARIO)
        self.assertEqual(b[2][2].dueno, USUARIO)

    def test_no_captura_aliados(self):
        b = tablero_vacio()
        b[0][0] = carta(9, 9, 9, 9, USUARIO)
        b[0][1] = carta(1, 1, 1, 1, USUARIO)
        self.assertEqual(capturas(b, 0, 1), [])
        self.assertEqual(b[0][0].dueno, USUARIO)

    def test_simular_no_muta(self):
        b = tablero_vacio()
        b[0][0] = carta(5, 5, 3, 5, CPU)
        c = carta(5, 5, 5, 9, USUARIO)
        puntos = simular(b, c, 0, 1, USUARIO)
        self.assertEqual(puntos, 2)
        self.assertEqual(b[0][0].dueno, CPU)  # original intacto
        self.assertIsNone(b[0][1])

    def test_captura_ambos_lados(self):
        b = tablero_vacio()
        b[0][1] = carta(9, 9, 9, 9, CPU)
        b[1][0] = carta(9, 9, 9, 9, CPU)
        b[1][1] = carta(10, 1, 5, 10, USUARIO)  # N=10>9 y O=10>9
        caps = capturas(b, 1, 1)
        self.assertIn((0, 1), caps)
        self.assertIn((1, 0), caps)
        self.assertEqual(b[0][1].dueno, USUARIO)
        self.assertEqual(b[1][0].dueno, USUARIO)


    def test_same(self):
        # Same: dos vecinos enemigos con lado opuesto IGUAL al de la carta colocada
        b = tablero_vacio()
        b[0][0] = carta(5, 5, 5, 5, CPU)   # su E=5
        b[0][1] = None
        b[1][0] = carta(5, 1, 1, 1, CPU)   # su N=1... no: su N se compara con S del colocado
        b[1][1] = carta(5, 5, 5, 5, USUARIO)
        b[0][0].dueno = CPU
        b[1][0] = carta(1, 5, 1, 1, CPU)   # su N=1 vs S del colocado (5) -> no
        # Usemos: colocado USUARIO en (1,1) con N=5 y O=5
        b[1][1] = carta(5, 1, 1, 5, USUARIO)
        # CPU en (0,1) con S=5  => igual al N=5 del colocado
        b[0][1] = carta(5, 5, 1, 1, CPU)
        # CPU en (1,0) con E=5 => igual al O=5 del colocado
        b[1][0] = carta(1, 1, 5, 1, CPU)
        caps = capturas(b, 1, 1)
        self.assertIn((0, 1), caps)
        self.assertIn((1, 0), caps)

    def test_plus(self):
        # Plus: sumas iguales en dos comparaciones distintas
        b = tablero_vacio()
        b[1][1] = carta(5, 1, 6, 1, USUARIO)  # N=5, E=6
        b[0][1] = carta(1, 3, 1, 1, CPU)       # S=3 -> suma 5+3=8
        b[1][2] = carta(1, 1, 1, 2, CPU)       # O=2 -> suma 6+2=8
        caps = capturas(b, 1, 1)
        self.assertIn((0, 1), caps)
        self.assertIn((1, 2), caps)

    def test_quema(self):
        b = tablero_vacio()
        b[0][1] = carta(9, 9, 9, 9, CPU)
        c = carta(1, 1, 1, 1, USUARIO)
        c.habilidad = "quema"
        b[1][1] = c
        caps = capturas(b, 1, 1)
        self.assertIn((0, 1), caps)
        self.assertEqual(b[0][1].dueno, USUARIO)

    def test_elemental_centro(self):
        # Dragón en el centro tiene +2
        b = tablero_vacio()
        b[1][1] = Carta("Drake", 7, 7, 7, 7, bando="dragon")
        b[1][1].dueno = USUARIO
        b[0][1] = carta(8, 8, 8, 8, CPU)  # su S=8; Drake N efectivo=9 > 8
        caps = capturas(b, 1, 1)
        self.assertIn((0, 1), caps)


    def test_sinergia_bando(self):
        # 3+ cartas amigas del mismo bando => +1 a los lados y captura
        b = tablero_vacio()
        for (r, c) in [(0, 0), (0, 1), (0, 2)]:
            card = Carta("G", 5, 5, 5, 5, bando="goblin")
            card.dueno = USUARIO
            b[r][c] = card
        colocada = Carta("M", 1, 1, 1, 1, bando="goblin")
        colocada.dueno = USUARIO
        b[1][1] = colocada
        b[2][1] = carta(1, 2, 1, 1, CPU)  # N=1; colocada S=1+1=2 (sinergia) > 1 => captura
        caps = capturas(b, 1, 1)
        self.assertIn((2, 1), caps)


if __name__ == "__main__":
    unittest.main()
