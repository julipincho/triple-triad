"""Logica compartida de Triple Triad (consola, GUI y campana).

Reglas implementadas:
  - basica: la carta colocada gana los lados donde su valor supera al vecino
  - Same:   dos vecinos enemigos con valor opuesto IGUAL
  - Plus:   dos comparaciones distintas con la misma suma
  - cadena: una carta capturada sigue capturando (efecto domino)
  - habilidad "quema"     : gana o empata la comparacion basica contra sus vecinas
                             (ignora Same y Plus), pero el muro las protege
  - habilidad "muro"      : el lado mas alto de la carta no puede ser capturado
  - habilidad "furia"     : +1 a todos sus lados si toca una carta amiga
  - habilidad "embestida" : +2 a todos sus lados en la casilla central
  - elemento central: +2 a la faccion elemental en la casilla (1,1)
  - sinergia de bando: 3+ cartas amigas del mismo bando => +1 a todos sus lados
"""

import copy

from facciones import elemento_central

USUARIO = "T"
CPU = "C"

OPUESTO = {"N": "S", "S": "N", "E": "O", "O": "E"}
DELTA = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "O": (0, -1)}
LADOS = ("N", "S", "E", "O")

HABILIDADES = {
    "quema": "Gana o empata la comparacion contra cada vecina (sin Same ni Plus).",
    "muro": "Su lado mas alto no puede ser capturado.",
    "furia": "+1 a todos sus lados si toca una carta amiga en el tablero.",
    "embestida": "+2 a todos sus lados si se coloca en la casilla central.",
}


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

    def lados_muro(self):
        """Lados protegidos por la habilidad 'muro' (empate con el mas alto)."""
        if self.habilidad != "muro":
            return set()
        maximo = max(self.valores.values())
        return {d for d, v in self.valores.items() if v == maximo}

    def a_dict(self):
        return {
            "nombre": self.nombre,
            "n": self.valores["N"],
            "s": self.valores["S"],
            "e": self.valores["E"],
            "o": self.valores["O"],
            "bando": self.bando,
            "habilidad": self.habilidad,
        }

    @staticmethod
    def desde_dict(d, bando_por_defecto=None):
        return Carta(
            d["nombre"],
            d["n"],
            d["s"],
            d["e"],
            d["o"],
            bando=d.get("bando") or bando_por_defecto,
            habilidad=d.get("habilidad"),
        )

    def __repr__(self):
        return f"Carta({self.nombre}, {self.valores}, {self.bando}, {self.habilidad})"


def _vecinas_amigas(board, r, c, dueno):
    for lado, (dr, dc) in DELTA.items():
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            x = board[nr][nc]
            if x is not None and x.dueno == dueno:
                return True
    return False


def _sinergia(board, carta):
    if board is None or not carta.bando or carta.dueno is None:
        return 0
    aliadas = sum(
        1
        for fila in board
        for x in fila
        if x and x.dueno == carta.dueno and x.bando == carta.bando
    )
    return 1 if aliadas >= 3 else 0


def valor_efectivo(carta, r, c, lado, board=None):
    """Valor de un lado con todas las bonificaciones de posicion y sinergia."""
    v = carta.valores[lado]
    central = (r, c) == (1, 1)
    if carta.habilidad == "embestida" and central:
        v += 2
    # Casilla elemental central: bonus +2 a la faccion que domina ese elemento
    if central and carta.bando and elemento_central(carta.bando) == carta.bando:
        v += 2
    if carta.habilidad == "furia" and board is not None and _vecinas_amigas(board, r, c, carta.dueno):
        v += 1
    return v + _sinergia(board, carta)


def flips_por_carta(board, r, c):
    """Basica + Same + Plus + habilidades. Devuelve set de posiciones."""
    carta = board[r][c]
    muro = carta.lados_muro()
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
        opuesta = OPUESTO[lado]
        if opuesta in vecina.lados_muro():
            continue  # el muro de la vecina bloquea esta direccion
        m = valor_efectivo(carta, r, c, lado, board)
        e = valor_efectivo(vecina, nr, nc, opuesta, board)
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
    if carta.habilidad == "quema":
        # La quema no barre el tablero entero: solo prende a las vecinas que
        # puede overcome. Antes daba vueltas a TODO lo que la rodeaba sin
        # comparar un solo valor, asi que guardarla para el final (en el
        # centro, con ocho enemigas alrededor) garantia la victoria.
        # Ahora gana la comparacion basica o la empata, y el muro de la
        # vecina la protege: sigue siendo la mejor carta contra una ringa
        # debil, pero ya no es una jugada ganadora garantizada.
        for lado, (dr, dc) in DELTA.items():
            nr, nc = r + dr, c + dc
            if not (0 <= nr < 3 and 0 <= nc < 3):
                continue
            vecina = board[nr][nc]
            if vecina is None or vecina.dueno == carta.dueno:
                continue
            if OPUESTO[lado] in vecina.lados_muro():
                continue  # el muro sigue bloqueando la quema
            m = valor_efectivo(carta, r, c, lado, board)
            e = valor_efectivo(vecina, nr, nc, OPUESTO[lado], board)
            if m >= e:
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
        dueno = board[cr][cc].dueno
        for (nr, nc) in flips_por_carta(board, cr, cc):
            vecina = board[nr][nc]
            if vecina is None or vecina.dueno == dueno:
                continue
            vecina.dueno = dueno
            capturadas.append((nr, nc))
            cola.append((nr, nc))
    return capturadas


def simular(board, carta, r, c, dueno):
    """Cuantas cartas tendria `dueno` si colocara `carta` en (r, c)."""
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


def puntaje_final(board):
    """(tuya, cpu, ganador). ganador: 'T', 'C' o None."""
    t, c = contar(board)
    if t > c:
        return t, c, USUARIO
    if c > t:
        return t, c, CPU
    return t, c, None


def total_carta(carta):
    return sum(carta.valores[d] for d in LADOS)


def rareza(carta):
    """(etiqueta, color) segun la suma de sus cuatro lados."""
    total = total_carta(carta)
    if total >= 33:
        return ("LEGENDARIA", (240, 200, 90))
    if total >= 26:
        return ("RARA", (180, 190, 220))
    return ("COMUN", (160, 160, 150))