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
    def __init__(self, nombre, n, s, e, o, dueno=None, bando=None, habilidad=None):
        self.nombre = nombre
        self.valores = {"N": n, "S": s, "E": e, "O": o}
        self.dueno = dueno
        self.bando = bando
        self.habilidad = habilidad

    def lado(self, d):
        return self.valores[d]

    def copia(self):
        return copy.deepcopy(self)


def valor_efectivo(carta, r, c, lado, board=None):
    v = carta.valores[lado]
    # Casilla elemental central: bonus +2 a dragones y hombres lobo
    if (r, c) == (1, 1) and carta.bando in ("dragon", "hombre_lobo"):
        v += 2
    # Sinergia de bando: 3+ cartas amistosas del mismo bando en el tablero => +1 a todos tus lados
    if board is not None and carta.bando:
        aliadas = sum(
            1
            for fila in board
            for x in fila
            if x and x.dueno == carta.dueno and x.bando == carta.bando
        )
        if aliadas >= 3:
            v += 1
    return v


def flips_por_carta(board, r, c):
    """Reglas básica + Same + Plus + habilidad quema. Devuelve set de posiciones."""
    carta = board[r][c]
    basico = set()
    iguales = []
    sumas = {}
    for lado, (dr, dc) in DELTA.items():
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 3 and 0 <= nc < 3):
            continue
        vecina = board[nr][nc]
        if vecina is None or vecina.dueno == carta.dueno:
            continue
        m = valor_efectivo(carta, r, c, lado, board)
        e = valor_efectivo(vecina, nr, nc, OPUESTO[lado], board)
        if m > e:
            basico.add((nr, nc))
        if m == e:
            iguales.append((nr, nc))
        sumas.setdefault(m + e, []).append((nr, nc))
    flips = set(basico)
    if len(iguales) >= 2:  # Same
        flips.update(iguales)
    for grupo in sumas.values():  # Plus
        if len(grupo) >= 2:
            flips.update(grupo)
    if getattr(carta, "habilidad", None) == "quema":
        for lado, (dr, dc) in DELTA.items():
            nr, nc = r + dr, c + dc
            if 0 <= nr < 3 and 0 <= nc < 3 and board[nr][nc] and board[nr][nc].dueno != carta.dueno:
                flips.add((nr, nc))
    return flips


def capturas(board, r, c):
    """Captura cartas adyacentes con cadena. Devuelve lista de (fila, col)."""
    origen = board[r][c]
    if origen is None:
        return []
    capturadas = []
    cola = [(r, c)]
    while cola:
        cr, cc = cola.pop(0)
        for (nr, nc) in flips_por_carta(board, cr, cc):
            vecina = board[nr][nc]
            if vecina is None or vecina.dueno == board[cr][cc].dueno:
                continue
            vecina.dueno = board[cr][cc].dueno
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
