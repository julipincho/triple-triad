"""Casos de contrato: lados enfrentados, combos y propiedad de habilidades."""
import copy
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from reglas import (Carta, CPU, USUARIO, DELTA, OPUESTO, capturas, cascada,
                    resumen_efectos, simular, valor_efectivo)


def carta(dueno, n=1, s=1, e=1, o=1, habilidad=None):
    return Carta("Prueba", n, s, e, o, dueno=dueno, habilidad=habilidad)


class TestContrato(unittest.TestCase):
    def test_rotar_tablero_no_cambia_las_capturas_con_bonus_y_combo(self):
        rng = random.Random(20261010)
        for _ in range(300):
            b = [[None] * 3 for _ in range(3)]
            for r in range(3):
                for c in range(3):
                    if rng.random() < .85 or (r, c) == (1, 1):
                        x = carta(rng.choice((USUARIO, CPU)),
                                  *(rng.randint(1, 9) for _ in range(4)),
                                  habilidad=rng.choice((None, "furia", "embestida", "muro", "quema")))
                        x.bando = rng.choice(("humano", "orco", "dragon"))
                        if rng.random() < .3:
                            x.dueno = CPU if x.dueno == USUARIO else USUARIO
                        b[r][c] = x
            rotado = [[None] * 3 for _ in range(3)]
            for r in range(3):
                for c in range(3):
                    if b[r][c] is not None:
                        x = b[r][c].copia()
                        v = x.valores
                        x.valores = {"N": v["O"], "E": v["N"], "S": v["E"], "O": v["S"]}
                        rotado[c][2-r] = x
            caps = capturas(b, 1, 1)
            self.assertEqual({(c, 2-r) for r, c in caps}, set(capturas(rotado, 1, 1)))

    def test_cada_direccion_compara_solo_la_cara_opuesta(self):
        for lado, (dr, dc) in DELTA.items():
            for ataque in range(1, 11):
                for defensa in range(1, 11):
                    with self.subTest(lado=lado, ataque=ataque, defensa=defensa):
                        b = [[None] * 3 for _ in range(3)]
                        b[1][1] = carta(USUARIO, 10, 10, 10, 10)
                        b[1][1].valores[lado] = ataque
                        b[1+dr][1+dc] = carta(CPU, 1, 1, 1, 1)
                        b[1+dr][1+dc].valores[OPUESTO[lado]] = defensa
                        self.assertEqual(capturas(b, 1, 1),
                                         [(1+dr, 1+dc)] if ataque > defensa else [])

    def test_basica_no_inicia_combo(self):
        b = [[None] * 3 for _ in range(3)]
        b[1][0] = carta(USUARIO, e=8)
        b[1][1] = carta(CPU, e=9, o=3)
        b[1][2] = carta(CPU, o=4)
        self.assertEqual(capturas(b, 1, 0), [(1, 1)])
        self.assertEqual(b[1][2].dueno, CPU)

    def test_same_aliado_inicia_combo_basico(self):
        b = [[None] * 3 for _ in range(3)]
        b[1][0] = carta(USUARIO, n=5, e=3)
        b[0][0] = carta(USUARIO, s=5)
        b[1][1] = carta(CPU, e=8, o=3)
        b[1][2] = carta(CPU, o=5)
        caps, eventos = cascada(b, 1, 0)
        self.assertEqual(caps, [(1, 1), (1, 2)])
        self.assertEqual(resumen_efectos(eventos, (1, 0)),
                         {"basica": 0, "cadena": 1, "same": 1})

    def test_plus_con_aliado_y_enemigo_mas_fuerte(self):
        b = [[None] * 3 for _ in range(3)]
        b[1][1] = carta(USUARIO, n=2, e=3)
        b[0][1] = carta(USUARIO, s=7)
        b[1][2] = carta(CPU, o=6)
        caps, eventos = cascada(b, 1, 1)
        self.assertEqual(caps, [(1, 2)])
        self.assertEqual(eventos, [("plus", (1, 2), (1, 1))])

    def test_combo_no_repite_same_plus_ni_quema(self):
        b = [[None] * 3 for _ in range(3)]
        b[1][0] = carta(USUARIO, n=5, e=3)
        b[0][0] = carta(USUARIO, s=5)
        b[1][1] = carta(CPU, n=4, e=4, o=3, habilidad="quema")
        b[0][1] = carta(CPU, s=4)
        b[1][2] = carta(CPU, o=4)
        self.assertEqual(capturas(b, 1, 0), [(1, 1)])

    def test_motivos_mixtos_no_convierten_basica_en_same(self):
        b = [[None] * 3 for _ in range(3)]
        b[1][1] = carta(USUARIO, n=5, s=9, e=7)
        b[0][1] = carta(CPU, s=5)
        b[1][2] = carta(CPU, o=7)
        b[2][1] = carta(CPU, n=2, e=9)
        b[2][2] = carta(CPU, n=8, o=2)
        caps, eventos = cascada(b, 1, 1)
        self.assertEqual(set(caps), {(0, 1), (1, 2), (2, 1)})
        self.assertEqual(resumen_efectos(eventos, (1, 1)),
                         {"basica": 1, "cadena": 0, "same": 2})

    def test_muro_excluye_comparacion_de_same(self):
        b = [[None] * 3 for _ in range(3)]
        b[1][1] = carta(USUARIO, n=5, e=7)
        b[0][1] = carta(CPU, s=5, habilidad="muro")
        b[1][2] = carta(CPU, o=7)
        self.assertEqual(capturas(b, 1, 1), [])

    def test_furia_y_embestida_se_apagan_y_vuelven(self):
        for habilidad, bonus in (("furia", 1), ("embestida", 2)):
            for original, rival in ((USUARIO, CPU), (CPU, USUARIO)):
                with self.subTest(habilidad=habilidad, original=original):
                    b = [[None] * 3 for _ in range(3)]
                    c = b[1][1] = carta(original, 4, 4, 4, 4, habilidad)
                    b[0][1] = carta(original)
                    b[2][1] = carta(rival)
                    self.assertEqual(valor_efectivo(c, 1, 1, "E", b), 4 + bonus)
                    # Captura real desde la derecha; recuperacion desde izquierda.
                    b[1][2] = carta(rival, o=10)
                    self.assertIn((1, 1), capturas(b, 1, 2))
                    self.assertEqual(c.dueno_inicial, original)
                    self.assertEqual(valor_efectivo(c, 1, 1, "E", b), 4)
                    b[1][0] = carta(original, e=10)
                    self.assertIn((1, 1), capturas(b, 1, 0))
                    self.assertEqual(valor_efectivo(c, 1, 1, "E", b), 4 + bonus)

    def test_simulacion_preserva_propietario_original(self):
        b = [[None] * 3 for _ in range(3)]
        c = b[1][1] = carta(USUARIO, 4, 4, 4, 4, "embestida")
        c.dueno = CPU
        ataque = carta(USUARIO, e=5)
        antes = copy.deepcopy(b)
        self.assertEqual(simular(b, ataque, 1, 0, USUARIO), 2)
        self.assertEqual(c.dueno, antes[1][1].dueno)
        self.assertEqual(c.dueno_inicial, USUARIO)
        self.assertIsNone(b[1][0])

    def test_reparto_nuevo_reinicia_propiedad_sin_mutar_coleccion(self):
        c = carta(USUARIO, habilidad="furia")
        c.dueno = CPU
        copia = c.copia()
        copia.repartir(CPU)
        self.assertEqual(copia.dueno_inicial, CPU)
        self.assertEqual(c.dueno_inicial, USUARIO)


if __name__ == "__main__":
    unittest.main()
