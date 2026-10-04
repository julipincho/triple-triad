"""Lógica compartida de Triple Triad (consola y GUI)."""

import copy

USUARIO = "T"
CPU = "C"

OPUESTO = {"N": "S", "S": "N", "E": "O", "O": "E"}
DELTA = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "O": (0, -1)}


def val(n):
    """Muestra 10 como A."""
    return "A" if n == 10 else str(n)


class Carta:
    def __init__(self, nombre, n, s, e, o, dueno=None, bando=None):
        self.nombre = nombre
        self.valores = {"N": n, "S": s, "E": e, "O": o}
        self.dueno = dueno
        self.bando = bando

    def lado(self, d):
        return self.valores[d]

    def copia(self):
        return copy.deepcopy(self)


def capturas(board, r, c):
    """Captura cartas adyacentes con cadena. Devuelve lista de (fila, col)."""
    origen = board[r][c]
    if origen is None:
        return []
    capturadas = []
    cola = [(r, c)]
    while cola:
        cr, cc = cola.pop(0)
        carta = board[cr][cc]
        for lado, (dr, dc) in DELTA.items():
            nr, nc = cr + dr, cc + dc
            if not (0 <= nr < 3 and 0 <= nc < 3):
                continue
            vecina = board[nr][nc]
            if vecina is None or vecina.dueno == carta.dueno:
                continue
            if carta.lado(lado) > vecina.lado(OPUESTO[lado]):
                vecina.dueno = carta.dueno
                capturadas.append((nr, nc))
                cola.append((nr, nc))
    return capturadas


def simular(board, carta, r, c, dueno):
    """Cuántas cartas tendría `dueno` si colocara `carta` en (r, c)."""
    nuevo = copy.deepcopy(board)
    nueva = carta.copia()
    nueva.dueno = dueno
    nuevo[r][c] = nueva
    capturas(nuevo, r, c)
    return sum(1 for fila in nuevo for celda in fila if celda and celda.dueno == dueno)


def celdas_vacias(board):
    return [(r, c) for r in range(3) for c in range(3) if board[r][c] is None]


def contar(board):
    t = sum(1 for f in board for x in f if x and x.dueno == USUARIO)
    c = sum(1 for f in board for x in f if x and x.dueno == CPU)
    return t, c
