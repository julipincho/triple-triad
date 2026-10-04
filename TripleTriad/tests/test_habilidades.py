"""Tests de las habilidades de carta y de los mazos por faccion."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import facciones
import mazos
from reglas import (
    CPU,
    HABILIDADES,
    LADOS,
    USUARIO,
    Carta,
    capturas,
    flips_por_carta,
    puntaje_final,
    rareza,
    simular,
    valor_efectivo,
)


def tablero_vacio():
    return [[None] * 3 for _ in range(3)]


def poner(board, nombre, n, s, e, o, dueno, r, c, bando=None, habilidad=None):
    carta = Carta(nombre, n, s, e, o, bando=bando, habilidad=habilidad)
    carta.dueno = dueno
    board[r][c] = carta
    return carta


class TestHabilidades(unittest.TestCase):
    def test_muro_bloquea_el_lado_mas_alto(self):
        b = tablero_vacio()
        # la vecina CPU tiene N=9 como lado mas alto: nadie puede capturarla por ahi
        poner(b, "Muro CPU", 9, 2, 2, 2, CPU, 0, 1, habilidad="muro")
        poner(b, "Atacante", 1, 10, 1, 1, USUARIO, 1, 1)
        caps = capturas(b, 1, 1)
        self.assertEqual(caps, [])
        self.assertEqual(b[0][1].dueno, CPU)

    def test_muro_no_bloquea_los_demas_lados(self):
        b = tablero_vacio()
        poner(b, "Muro CPU", 9, 2, 2, 2, CPU, 1, 2, habilidad="muro")
        poner(b, "Atacante", 1, 1, 10, 1, USUARIO, 1, 1)  # E=10 vs su O=2
        caps = capturas(b, 1, 1)
        self.assertIn((1, 2), caps)

    def test_cartas_sin_bando_no_tienen_bonus_elemental(self):
        b = tablero_vacio()
        sin_bando = poner(b, "Huerfana", 7, 7, 7, 7, USUARIO, 1, 1)
        self.assertEqual(valor_efectivo(sin_bando, 1, 1, "N", b), 7)

    def test_muro_solo_aplica_a_valores_maximos(self):
        c = Carta("M", 5, 9, 3, 3, habilidad="muro")
        self.assertEqual(c.lados_muro(), {"S"})

    def test_furia_solo_con_vecina_amiga(self):
        sola = tablero_vacio()
        c = poner(sola, "Furia", 5, 5, 5, 5, USUARIO, 1, 1, bando="orco", habilidad="furia")
        self.assertEqual(valor_efectivo(c, 1, 1, "N", sola), 5)

        con_vecina = tablero_vacio()
        c2 = poner(con_vecina, "Furia", 5, 5, 5, 5, USUARIO, 1, 1, bando="orco", habilidad="furia")
        poner(con_vecina, "Aliado", 5, 5, 5, 5, USUARIO, 1, 0, bando="orco")
        self.assertEqual(valor_efectivo(c2, 1, 1, "N", con_vecina), 6)

    def test_furia_permite_capturar_igual(self):
        b = tablero_vacio()
        b[1][0] = poner(b, "Aliado", 5, 5, 5, 5, USUARIO, 1, 0, bando="orco")
        b[1][1] = poner(b, "Bruto", 5, 5, 5, 5, USUARIO, 1, 1, bando="orco", habilidad="furia")
        b[2][1] = poner(b, "Enemigo", 5, 4, 5, 5, CPU, 2, 1)
        caps = capturas(b, 1, 1)
        self.assertIn((2, 1), caps)  # S=6 (furia) > N=5

    def test_embestida_solo_en_el_centro(self):
        b = tablero_vacio()
        fuera = poner(b, "Trol", 5, 5, 5, 5, USUARIO, 0, 0, bando="orco", habilidad="embestida")
        self.assertEqual(valor_efectivo(fuera, 0, 0, "N", b), 5)
        centro = poner(b, "Trol2", 5, 5, 5, 5, USUARIO, 1, 1, bando="orco", habilidad="embestida")
        self.assertEqual(valor_efectivo(centro, 1, 1, "N", b), 7)

    def test_quema_prende_a_las_vecinas_debiles(self):
        b = tablero_vacio()
        # cada vecina vale 1 en la cara que mira al centro:
        # N->S=1, S->N=1, O->E=1, E->O=1
        poner(b, "N", 9, 1, 9, 9, CPU, 0, 1)
        poner(b, "S", 1, 9, 9, 9, CPU, 2, 1)
        poner(b, "O", 9, 9, 1, 9, CPU, 1, 0)
        poner(b, "E", 9, 9, 9, 1, CPU, 1, 2)
        poner(b, "Quemada", 5, 5, 5, 5, USUARIO, 1, 1, habilidad="quema")
        caps = set(capturas(b, 1, 1))
        self.assertEqual(caps, {(0, 1), (2, 1), (1, 0), (1, 2)})

    def test_quema_no_barre_el_tablero(self):
        """El bug: la quema daba vueltas a todo lo que la rodeaba sin
        comparar nada. Guardada para el final, en el centro con ocho
        enemigas alrededor, garantia la victoria."""
        b = tablero_vacio()
        # valores distintos para no disparar Plus por casualidad
        poner(b, "FuerteN", 9, 9, 1, 1, CPU, 0, 1)
        poner(b, "FuerteS", 8, 8, 1, 1, CPU, 2, 1)
        poner(b, "FuerteO", 7, 1, 7, 1, CPU, 1, 0)
        poner(b, "FuerteE", 6, 1, 1, 6, CPU, 1, 2)
        poner(b, "Quemada", 5, 5, 5, 5, USUARIO, 1, 1, habilidad="quema")
        self.assertEqual(capturas(b, 1, 1), [],
                         "la quema no puede con vecinas mas fuertes")

    def test_quema_no_aporta_ningun_volteo_extra(self):
        """La prueba de fuego: la quema no puede girar ni una carta mas que
        una carta normal con los mismos valores.

        Con ocho vecinas de 9 alrededor, una carta normal de 5 ya dispara
        Plus (5+9=14 en las cuatro direcciones) y la cadena se lleva el
        resto. Eso es otra regla y debe seguir igual: lo que no debe pasar es
        que la habilidad queme las.cartas que la basica no puede.
        """
        def montar(habilidad):
            b = tablero_vacio()
            vecinas = {
                (0, 1): (9, 9, 1, 2),
                (2, 1): (9, 9, 1, 3),
                (1, 0): (9, 2, 9, 1),
                (1, 2): (9, 3, 1, 9),
                (0, 0): (1, 4, 2, 1),
                (0, 2): (2, 5, 1, 1),
                (2, 0): (3, 1, 1, 2),
                (2, 2): (4, 1, 1, 3),
            }
            for (r, c), (n, s, e, o) in vecinas.items():
                poner(b, "R%d%d" % (r, c), n, s, e, o, CPU, r, c)
            poner(b, "Centro", 5, 5, 5, 5, USUARIO, 1, 1, habilidad=habilidad)
            return b

        con_quema = flips_por_carta(montar("quema"), 1, 1)
        sin_quema = flips_por_carta(montar(None), 1, 1)
        self.assertEqual(con_quema, sin_quema,
                         "la quema girando cartas que la basica no puede es el bug")

    def test_quema_no_puede_con_vecinas_de_nueve(self):
        """Sin Plus ni cadena que la Newly: la quema de 5 no toca un 9."""
        b = tablero_vacio()
        # las cuatro vecinas miran al centro con 9, 8, 7 y 6: todas por encima
        # de la quema (5) y con sumas distintas, para que no salte Plus
        poner(b, "N", 9, 9, 1, 2, CPU, 0, 1)   # S=9
        poner(b, "S", 8, 8, 1, 3, CPU, 2, 1)   # N=8
        poner(b, "O", 7, 2, 7, 1, CPU, 1, 0)   # E=7
        poner(b, "E", 6, 3, 1, 6, CPU, 1, 2)   # O=6
        poner(b, "Quemada", 5, 5, 5, 5, USUARIO, 1, 1, habilidad="quema")
        self.assertEqual(capturas(b, 1, 1), [])
        mias = sum(1 for f in b for x in f if x and x.dueno == USUARIO)
        self.assertEqual(mias, 1, "la quema no barre el tablero entero")

    def test_quema_gana_los_empates(self):
        """Sigue siendo especial: gana tambien las comparaciones igualadas."""
        b = tablero_vacio()
        poner(b, "N", 9, 5, 9, 9, CPU, 0, 1)   # S=5 contra N=5 de la quema
        poner(b, "S", 5, 9, 9, 9, CPU, 2, 1)   # N=5 contra S=5
        poner(b, "Quemada", 5, 5, 5, 5, USUARIO, 1, 1, habilidad="quema")
        caps = set(capturas(b, 1, 1))
        self.assertIn((0, 1), caps)
        self.assertIn((2, 1), caps)

    def test_quema_no_toca_el_muro_de_la_vecina(self):
        b = tablero_vacio()
        # la cara maxima de la vecina (S=9) queda protegida por su muro
        poner(b, "Muro", 1, 9, 1, 1, CPU, 0, 1, habilidad="muro")
        poner(b, "Quemada", 9, 9, 9, 9, USUARIO, 1, 1, habilidad="quema")
        self.assertEqual(capturas(b, 1, 1), [])

    def test_quema_no_necesita_same_ni_plus(self):
        """Con una sola igualdad no hay Same, y sin sumas repetidas no hay
        Plus: la quema prende igual."""
        b = tablero_vacio()
        poner(b, "N", 9, 4, 9, 9, CPU, 0, 1)   # S=4 contra N=4: empate
        poner(b, "Quemada", 4, 9, 9, 9, USUARIO, 1, 1, habilidad="quema")
        self.assertIn((0, 1), capturas(b, 1, 1))

    def test_todas_las_habilidades_documentadas(self):
        for c in mazos.HUMANOS + mazos.ORCOS:
            if c.habilidad:
                self.assertIn(c.habilidad, HABILIDADES)


class TestMazos(unittest.TestCase):
    def test_las_siete_facciones_existen(self):
        self.assertEqual(len(mazos.TODOS), 7)
        for f in facciones.orden_facciones():
            self.assertIn(f, mazos.TODOS)
            self.assertIn(f, facciones.FACCIONES)

    def test_los_nuevos_mazos_estan_completos(self):
        for bandos in (mazos.HUMANOS, mazos.ORCOS):
            self.assertEqual(len(bandos), 5)
            for c in bandos:
                self.assertIn(c.bando, ("humano", "orco"))
                for lado in LADOS:
                    self.assertTrue(1 <= c.valores[lado] <= 10, f"{c.nombre}.{lado}")

    def test_totodas_las_cartas_tienen_bando_valido(self):
        for bando, cartas in mazos.TODOS.items():
            for c in cartas:
                self.assertEqual(c.bando, bando)
                self.assertIn(c.bando, facciones.FACCIONES)

    def test_cartas_humanas_y_orcas_son_distintas(self):
        nombres = [c.nombre for c in mazos.HUMANOS + mazos.ORCOS]
        self.assertEqual(len(nombres), len(set(nombres)))

    def test_rarezas_distribuidas(self):
        self.assertEqual(rareza(mazos.HUMANOS[0])[0], "COMUN")
        self.assertEqual(rareza(mazos.HUMANOS[-1])[0], "LEGENDARIA")
        self.assertEqual(rareza(mazos.ORCOS[-1])[0], "LEGENDARIA")


class TestSinergiasYElemento(unittest.TestCase):
    def test_elemento_central_por_faccion(self):
        b = tablero_vacio()
        lobo = poner(b, "Alfa", 7, 7, 7, 7, USUARIO, 1, 1, bando="hombre_lobo")
        self.assertEqual(valor_efectivo(lobo, 1, 1, "N", b), 9)
        dragon = poner(b, "Rey Dragon", 7, 7, 7, 7, USUARIO, 0, 0, bando="dragon")
        self.assertEqual(valor_efectivo(dragon, 0, 0, "N", b), 7)

    def test_humanos_no_tienen_bonus_central(self):
        b = tablero_vacio()
        rey = poner(b, "Rey Aldric", 7, 7, 7, 7, USUARIO, 1, 1, bando="humano")
        self.assertEqual(valor_efectivo(rey, 1, 1, "N", b), 7)

    def test_simular_respeta_habilidades(self):
        b = tablero_vacio()
        b[0][0] = poner(b, "Aliado", 5, 5, 5, 5, USUARIO, 0, 0, bando="orco")
        b[1][1] = poner(b, "Guardia", 6, 6, 6, 6, CPU, 1, 1)
        # Sin furia el S=6 empata con el N=6 de la guardia y NO captura.
        plano = simular(b, Carta("Bruto", 1, 6, 1, 1, bando="orco"), 0, 1, USUARIO)
        self.assertEqual(plano, 2)
        # Con furia (hay una carta amiga adyacente) sube a 7 y captura.
        furioso = simular(b, Carta("Bruto", 1, 6, 1, 1, bando="orco", habilidad="furia"), 0, 1, USUARIO)
        self.assertEqual(furioso, 3)

    def test_puntaje_final(self):
        b = tablero_vacio()
        for i, (r, c) in enumerate([(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]):
            poner(b, "x", 5, 5, 5, 5, USUARIO, r, c)
        poner(b, "y", 5, 5, 5, 5, CPU, 2, 2)
        t, c, ganador = puntaje_final(b)
        self.assertEqual((t, c, ganador), (5, 1, USUARIO))


if __name__ == "__main__":
    unittest.main()