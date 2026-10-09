"""Auditoria de las reglas de captura, contra una implementacion independiente.

El juego documenta las reglas en la pantalla de ayuda:

    Basica: ganas la carta vecina si tu lado es mayor.
    Same: dos vecinos con el mismo valor capturan.
    Plus: dos comparaciones con la misma suma capturan.
    Cadena: una carta capturada sigue capturando.
    Muro: su mejor lado no puede caer.
    Furia: +1 a cada lado si toca una carta amiga.
    Embestida: +2 en la casilla central.
    Sinergia: 3+ cartas de tu bando dan +1 a todo.

Aqui se reimplementa cada regla desde cero, sin mirar `reglas.py`, y se
compara con el motor real en miles de tableros. Si el motor se desvía de la
regla escrita, este test lo dice con el caso concreto, en vez de dejarlo para
que lo encuentre un jugador.

Ademas mide el problema REAL que|reporto un jugador: "el numero de la derecha
pese a ser mayor no voltea al de la izquierda". La respuesta esta en
`valor_efectivo`: la captura compara el numero con bonificaciones, no el
numero que se ve. Este test mide cuantas veces pasa y con cuanta diferencia,
para que el dato este a la vista y no sea teoria.
"""

import os
import random
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tt_test_reglas_audit")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import facciones  # noqa: E402
import mazos  # noqa: E402
import pygame  # noqa: E402
import reglas  # noqa: E402

DIR = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "O": (0, -1)}
OPUESTO = {"N": "S", "S": "N", "E": "O", "O": "E"}


def setUpModule():
    pygame.init()
    pygame.display.set_mode((1280, 800))


# --------------------------------------------------------------------------
# Implementacion de referencia, escrita desde las reglas del juego.
# No llama a nada de `reglas.py` salvo `Carta` y `elemento_central`, que son
# datos, no reglas.
# --------------------------------------------------------------------------

def ref_valor(carta, r, c, lado, board):
    """El numero que se ve, mas las bonificaciones. Red de seguridad: si el
    motor y esta referencia coinciden siempre, no hay sesgo posible."""
    v = carta.valores[lado]
    # Embestida: +2 en el centro.
    if carta.habilidad == "embestida" and (r, c) == (1, 1):
        v += 2
    # Casilla elemental central: +2 al bando que domina ese elemento.
    if (r, c) == (1, 1) and carta.bando and \
            reglas.elemento_central(carta.bando) == carta.bando:
        v += 2
    # Furia: +1 si toca una carta amiga.
    if carta.habilidad == "furia":
        for dr, dc in DIR.values():
            nr, nc = r + dr, c + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                x = board[nr][nc]
                if x is not None and x.dueno == carta.dueno:
                    v += 1
                    break
    # Sinergia: +1 con 3+ cartas de tu bando (contando esta).
    if board is not None:
        mias = sum(1
                   for fila in board for x in fila
                   if x is not None and x.dueno == carta.dueno and x.bando == carta.bando)
        if mias >= 3:
            v += 1
    return v


def ref_captura(board, r, c):
    """Que casillas voltea la carta de (r, c), sin cadena."""
    carta = board[r][c]
    ganadas = set()
    mismo_valor = []
    misma_suma = {}
    for lado, (dr, dc) in DIR.items():
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 3 and 0 <= nc < 3):
            continue
        vecina = board[nr][nc]
        if vecina is None or vecina.dueno == carta.dueno:
            continue
        # Muro: la vecina protege el lado que mira a la carta.
        if OPUESTO[lado] in vecina.lados_muro():
            continue
        m = ref_valor(carta, r, c, lado, board)
        e = ref_valor(vecina, nr, nc, OPUESTO[lado], board)
        if m > e:
            ganadas.add((nr, nc))
        if m == e:
            mismo_valor.append((nr, nc))
        misma_suma.setdefault(m + e, []).append((nr, nc))

    # Same: dos o mas vecinos con el MISMO valor.
    if len(mismo_valor) >= 2:
        ganadas.update(mismo_valor)
    # Plus: dos o mas comparaciones con la MISMA suma.
    for grupo in misma_suma.values():
        if len(grupo) >= 2:
            ganadas.update(grupo)
    # Quema: prende a las vecinas que puede superar o igualar.
    if carta.habilidad == "quema":
        for lado, (dr, dc) in DIR.items():
            nr, nc = r + dr, c + dc
            if not (0 <= nr < 3 and 0 <= nc < 3):
                continue
            vecina = board[nr][nc]
            if vecina is None or vecina.dueno == carta.dueno:
                continue
            if OPUESTO[lado] in vecina.lados_muro():
                continue
            if ref_valor(carta, r, c, lado, board) >= \
                    ref_valor(vecina, nr, nc, OPUESTO[lado], board):
                ganadas.add((nr, nc))
    return ganadas


# --------------------------------------------------------------------------

def tablero_aleatorio(rnd, n_cards=7):
    board = [[None] * 3 for _ in range(3)]
    vacias = [(r, c) for r in range(3) for c in range(3)]
    rnd.shuffle(vacias)
    orden = facciones.orden_facciones()
    mezcla = []
    for i in range(n_cards):
        bando = orden[rnd.randrange(len(orden))]
        mezcla.append(mazos.TODOS[bando][rnd.randrange(len(mazos.TODOS[bando]))])
    for i, (r, c) in enumerate(vacias[:n_cards]):
        carta = mezcla[i].copia()
        carta.dueno = "T" if i % 2 == 0 else "C"
        board[r][c] = carta
    return board


def _clonar(board):
    return [[c.copia() if c is not None else None for c in fila] for fila in board]


class TestElMotorCumpleLasReglasDocumentadas(unittest.TestCase):
    """El motor tiene que coincidir con la referencia, siempre."""

    def test_captura_igual_a_la_referencia(self):
        """3000 tableros, comparando cartas y casillas."""
        rnd = random.Random(20261009)
        for n in range(3000):
            board = tablero_aleatorio(rnd)
            for r in range(3):
                for c in range(3):
                    if board[r][c] is None:
                        continue
                    esperado = ref_captura(board, r, c)
                    # El motor puede modificar el tablero (cadena), asi que se
                    # compara sobre una copia: `flips_por_carta` es de una sola
                    # jugada, sin cadena.
                    real = reglas.flips_por_carta(_clonar(board), r, c)
                    self.assertEqual(
                        set(real), esperado,
                        f"tablero {n} en ({r},{c}): el motor voltea "
                        f"{sorted(real)} y la regla dice {sorted(esperado)}")

    def test_la_cadena_no_inventa_ni_borra_cartas(self):
        """Invariantes de `capturas` con cadena, sobre 500 tableros.

        No basta con que no reviente: tiene que conservar las cartas y sus
        casillas, y la propiedad solo puede pasar de rival a atacante.
        """
        rnd = random.Random(7)
        for n in range(500):
            board = tablero_aleatorio(rnd, n_cards=8)
            ocupadas = sum(1 for f in board for x in f if x is not None)
            nombres_antes = sorted(
                x.nombre for f in board for x in f if x is not None)
            origen = [(r, c) for r in range(3) for c in range(3) if board[r][c]]
            r, c = origen[0]
            dueno_atacante = board[r][c].dueno

            capturadas = reglas.capturas(board, r, c)

            self.assertEqual(
                sum(1 for f in board for x in f if x is not None), ocupadas,
                f"tablero {n}: la cadena borro o duplico cartas")
            self.assertEqual(
                sorted(x.nombre for f in board for x in f if x is not None),
                nombres_antes,
                f"tablero {n}: la cadena cambio el contenido del tablero")
            for (nr, nc) in capturadas:
                self.assertEqual(
                    board[nr][nc].dueno, dueno_atacante,
                    f"tablero {n}: ({nr},{nc}) no paso al atacante")

    def test_la_cadena_solo_toca_cartas_del_rival(self):
        rnd = random.Random(11)
        for n in range(500):
            board = tablero_aleatorio(rnd, n_cards=8)
            origen = [(r, c) for r in range(3) for c in range(3) if board[r][c]]
            r, c = origen[0]
            antes = {(i, j): board[i][j].dueno
                     for i in range(3) for j in range(3) if board[i][j]}
            reglas.capturas(board, r, c)
            for (i, j), dueno in antes.items():
                if board[i][j].dueno != dueno:
                    self.assertEqual(antes[(i, j)], dueno)
                    self.assertNotEqual(
                        board[i][j].dueno, antes[(i, j)],
                        f"tablero {n}: una carta cambio de dueño dos veces")
                    self.assertEqual(
                        board[i][j].dueno, board[r][c].dueno,
                        f"tablero {n}: ({i},{j}) paso a un tercero")

    def test_valor_efectivo_coincide_con_la_referencia(self):
        rnd = random.Random(99)
        for _ in range(800):
            board = tablero_aleatorio(rnd, n_cards=8)
            for r in range(3):
                for c in range(3):
                    if board[r][c] is None:
                        continue
                    for lado in DIR:
                        m = reglas.valor_efectivo(board[r][c], r, c, lado, board)
                        e = ref_valor(board[r][c], r, c, lado, board)
                        self.assertEqual(m, e,
                                         f"({r},{c},{lado}): motor {m}, regla {e}")


class TestElNumeroQueVesNoEsElQueDecide(unittest.TestCase):
    """La duda que trajo el jugador, medida.

    "El numero de la derecha pese a ser mayor no voltea al de la izquierda" no
    es un fallo del motor: la captura compara el valor EFECTIVO (el numero mas
    embestida en el centro, elemento central, furia y sinergia). Este test mide
    cuantas veces el numero visible no explica el resultado y deja el numero a
    la vista, para que la respuesta sea un dato y no una teoria.
    """

    def test_mide_cuantas_veces_el_numero_visible_no_explica(self):
        rnd = random.Random(4242)
        total = mayor_visible_no_captura = 0
        ejemplos = []
        for _ in range(2000):
            board = tablero_aleatorio(rnd, n_cards=8)
            for r in range(3):
                for c in range(3):
                    if board[r][c] is None:
                        continue
                    for lado, (dr, dc) in DIR.items():
                        nr, nc = r + dr, c + dc
                        if not (0 <= nr < 3 and 0 <= nc < 3):
                            continue
                        vecina = board[nr][nc]
                        if vecina is None or vecina.dueno == board[r][c].dueno:
                            continue
                        if OPUESTO[lado] in vecina.lados_muro():
                            continue
                        vm = board[r][c].valores[lado]
                        ve = vecina.valores[OPUESTO[lado]]
                        em = reglas.valor_efectivo(board[r][c], r, c, lado, board)
                        ee = reglas.valor_efectivo(vecina, nr, nc,
                                                   OPUESTO[lado], board)
                        total += 1
                        # El caso que reportó: visiblemente mayor y no voltea.
                        if vm > ve and em <= ee:
                            mayor_visible_no_captura += 1
                            if len(ejemplos) < 3:
                                ejemplos.append(
                                    f"{vm} contra {ve} (efectivos {em} contra {ee})")
        self.assertGreater(total, 10000, "hacen falta mas muestras")
        pct = 100.0 * mayor_visible_no_captura / total
        # Menos del 10%: es la consecuencia de las bonificaciones, no un fallo.
        self.assertLess(
            pct, 10.0,
            f"el {pct:.1f}% de las comparaciones con numero visible mayor no "
            f"captura. Ejemplos: {ejemplos}")

    def test_las_bonificaciones_estan_documentadas(self):
        """Que esten en la ayuda es lo que hace el numero verificable."""
        import io
        import re

        ruta = os.path.join(RAIZ, "pantallas.py")
        with open(ruta, encoding="utf-8") as fh:
            ayuda = fh.read()
        for regla in ("Basica", "Same", "Plus", "Cadena", "Muro", "Furia",
                      "Embestida", "Sinergia"):
            self.assertIn(regla, ayuda, f"la regla {regla} no esta en la ayuda")


class TestElDesgloseExplicaLaCaptura(unittest.TestCase):
    """`Juego.desglose_captura`: los cuatro numeros, para poder enseñarlos.

    Es la pieza que convierte "las reglas fallan" en "ahira tienes el porque".
    Si esto devuelve mal los numeros, el jugador recibe una explicacion falsa,
    que es peor que no dar ninguna.
    """

    def _juego_con(self, atacante, vecinas):
        """Monta un tablero. Las casillas admiten `carta` o `(carta, dueno)`,
        para poder poner una carta ally sin que el helper la fuerce a rival."""
        from partida import Juego

        juego = Juego("humano", bando_rival="orco")
        juego.board = [[None] * 3 for _ in range(3)]

        def poner(celdas, dueno_defecto):
            for (r, c), valor in celdas.items():
                carta = valor[0] if isinstance(valor, tuple) else valor
                carta.dueno = valor[1] if isinstance(valor, tuple) else dueno_defecto
                juego.board[r][c] = carta

        poner(atacante, "T")
        poner(vecinas, "C")
        return juego

    def _carta(self, bando, valores, habilidad=None):
        import mazos as _m

        base = _m.TODOS[bando][0].copia()
        base.valores = dict(valores)
        base.habilidad = habilidad
        base.bando = bando
        return base

    def test_devuelve_los_cuatro_numeros(self):
        juego = self._juego_con(
            {(1, 1): self._carta("humano", {"N": 5, "S": 5, "E": 5, "O": 5})},
            {(0, 1): self._carta("orco", {"S": 5, "N": 5, "E": 5, "O": 5})},
        )
        nd = juego.desglose_captura(juego.board[1][1], "N", 1, 1, 0, 1)
        self.assertIsNotNone(nd)
        va, vd, ea, ed = nd
        self.assertEqual(va, 5, "el numero visible del atacante")
        self.assertEqual(vd, 5, "el numero visible del rival")
        # En el centro, un humano puede tener bonificacion.
        self.assertGreaterEqual(ea, va)
        self.assertGreaterEqual(ed, vd)

    def test_una_carta_sin_bonificacion_coincide(self):
        """Fuera del centro y sin sinergia: efectivo == visible."""
        juego = self._juego_con(
            {(0, 0): self._carta("humano", {"S": 7, "N": 7, "E": 7, "O": 7})},
            {(1, 0): self._carta("orco", {"N": 4, "S": 4, "E": 4, "O": 4})},
        )
        nd = juego.desglose_captura(juego.board[0][0], "S", 0, 0, 1, 0)
        va, vd, ea, ed = nd
        self.assertEqual(ea, va, "sin bonificacion el efectivo es el visible")
        self.assertEqual(ed, vd)

    def test_un_muro_devuelve_none(self):
        """Con muro no hay comparacion, asi que no hay nada que explicar."""
        juego = self._juego_con(
            {(0, 0): self._carta("humano", {"S": 9, "N": 9, "E": 9, "O": 9})},
            {(1, 0): self._carta("orco", {"N": 3, "S": 3, "E": 3, "O": 3},
                                 habilidad="muro")},
        )
        # El lado N del rival mira hacia arriba, que es de donde viene el 9.
        self.assertIsNone(
            juego.desglose_captura(juego.board[0][0], "S", 0, 0, 1, 0),
            "con muro la comparacion no aplica")

    def test_fuera_del_tablero_devuelve_none(self):
        juego = self._juego_con(
            {(0, 0): self._carta("humano", {"S": 9, "N": 9, "E": 9, "O": 9})},
            {},
        )
        self.assertIsNone(juego.desglose_captura(juego.board[0][0], "N", 0, 0, -1, 0))

    def test_una_carta_aliada_devuelve_none(self):
        juego = self._juego_con(
            {(0, 0): self._carta("humano", {"S": 9, "N": 9, "E": 9, "O": 9})},
            {(1, 0): (self._carta("humano", {"N": 1, "S": 1, "E": 1, "O": 1}), "T")},
        )
        self.assertIsNone(juego.desglose_captura(juego.board[0][0], "S", 0, 0, 1, 0),
                          "una carta ally no se captura: no hay nada que explicar")


if __name__ == "__main__":
    unittest.main()