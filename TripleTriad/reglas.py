"""Logica compartida de Triple Triad (consola, GUI y campana).

Reglas implementadas:
  - basica: la carta colocada gana los lados donde su valor supera al vecino
  - Same:   dos vecinos (amigos o enemigos) con valor opuesto IGUAL
  - Plus:   dos comparaciones distintas con la misma suma
  - cadena: Same/Plus inician un domino de comparaciones basicas
  - habilidad "quema"     : gana o empata contra sus vecinas al colocarla;
                             el muro las protege; no inicia cadena por si sola
  - habilidad "muro"      : el lado mas alto de la carta no puede ser capturado
  - habilidad "furia"     : +1 a todos sus lados si toca una carta amiga
  - habilidad "embestida" : +2 a todos sus lados en la casilla central
  - elemento central: +2 a la faccion elemental en la casilla (1,1)
"""

import copy

from facciones import elemento_central

USUARIO = "T"
CPU = "C"

OPUESTO = {"N": "S", "S": "N", "E": "O", "O": "E"}
DELTA = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "O": (0, -1)}
LADOS = ("N", "S", "E", "O")

HABILIDADES = {
    "quema": "Gana o empata al colocarla; el muro protege. No inicia combo sola.",
    "muro": "Su lado mas alto no puede ser capturado.",
    "furia": "+1 junto a una amiga; solo con su propietario inicial.",
    "embestida": "+2 en el centro; solo con su propietario inicial.",
}


def val(n):
    """Muestra 10 como A."""
    return "A" if n == 10 else str(n)


class Carta:
    def __init__(self, nombre, n, s, e, o, dueno=None, bando=None, habilidad=None):
        self.nombre = nombre
        self.valores = {"N": n, "S": s, "E": e, "O": o}
        self.dueno_inicial = None
        self.dueno = dueno
        self.bando = bando
        self.habilidad = habilidad

    @property
    def dueno(self):
        return self._dueno

    @dueno.setter
    def dueno(self, nuevo):
        # La primera asignacion pertenece al reparto, no a una captura.
        if self.dueno_inicial is None and nuevo is not None:
            self.dueno_inicial = nuevo
        self._dueno = nuevo

    def repartir(self, dueno):
        """Una partida nueva establece una nueva propiedad de origen."""
        self.dueno_inicial = dueno
        self.dueno = dueno

    def habilidad_activa(self):
        return (self.habilidad not in ("furia", "embestida") or
                self.dueno is not None and self.dueno == self.dueno_inicial)

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


def valor_efectivo(carta, r, c, lado, board=None):
    """Valor de un lado con todas las bonificaciones de posicion."""
    v = carta.valores[lado]
    central = (r, c) == (1, 1)
    if carta.habilidad == "embestida" and carta.habilidad_activa() and central:
        v += 2
    # Casilla elemental central: bonus +2 a la faccion que domina ese elemento
    if central and carta.bando and elemento_central(carta.bando) == carta.bando:
        v += 2
    if (carta.habilidad == "furia" and carta.habilidad_activa() and
            board is not None and _vecinas_amigas(board, r, c, carta.dueno)):
        v += 1
    return v


def flips_por_carta(board, r, c):
    """Basica + Same + Plus + habilidades. Devuelve set de posiciones."""
    return _flips(board, r, c)[0]


#: Que regla se ensea cuando una carta cae por mas de una a la vez. El same y
#: el plus se pisan a menudo (dos 5 iguales caen por same, y si ademas sus
#: sumas coinciden por plus), y para el jugador el efecto que tiene que
#: aprender es el same. La basic no se enseña nunca: no es un efecto, es lo de
#: siempre.
MOTIVOS = ("basica", "quema", "plus", "same")


def _regla_principal(fired):
    """La regla mas especifica que actuo, o None si solo hubo basica."""
    for regla in ("same", "plus", "quema"):
        if fired.get(regla):
            return regla
    return None


def _flips(board, r, c):
    """Capturas y cantidades por motivo, sin contar dos veces una captura."""
    motivos = _motivos_captura(board, r, c)
    fired = {"basica": 0}
    for motivo in motivos.values():
        fired[motivo] = fired.get(motivo, 0) + 1
    return set(motivos), fired


def _motivos_captura(board, r, c, especiales=True):
    """Evalua todas las caras antes de cambiar propietarios.

    Los aliados cuentan para Same/Plus; un lado protegido por muro no
    participa. Durante un combo solo se aplica la comparacion estricta.
    """
    carta = board[r][c]
    if carta is None:
        return {}
    motivos = {}
    iguales = []
    sumas = {}
    for lado, (dr, dc) in DELTA.items():
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 3 and 0 <= nc < 3):
            continue
        vecina = board[nr][nc]
        if vecina is None:
            continue
        opuesta = OPUESTO[lado]
        if opuesta in vecina.lados_muro():
            continue  # el muro de la vecina bloquea esta direccion
        m = valor_efectivo(carta, r, c, lado, board)
        e = valor_efectivo(vecina, nr, nc, opuesta, board)
        pos = (nr, nc)
        if vecina.dueno != carta.dueno:
            if m > e:
                motivos[pos] = "basica"
            elif especiales and carta.habilidad == "quema" and m == e:
                motivos[pos] = "quema"
        if m == e:
            iguales.append((nr, nc))
        sumas.setdefault(m + e, []).append((nr, nc))
    if especiales:
        grupos = [("plus", grupo) for grupo in sumas.values() if len(grupo) >= 2]
        if len(iguales) >= 2:
            grupos.append(("same", iguales))
        for regla, grupo in grupos:
            for nr, nc in grupo:
                if board[nr][nc].dueno != carta.dueno:
                    motivos[nr, nc] = regla
    return motivos


def cascada(board, r, c):
    """La captura con cadena, diciendo que efecto disparo cada carta.

    MUTA el tablero igual que `capturas` (no hace copia: esto ya es el juego
    real, no una simulacion). Devuelve `(capturadas, eventos)`, y cada evento
    es `(regla, posicion, origen)`: que regla/volto esa carta y desde que carta
    salio. `regla` es None cuando solo hubo comparacion basica, que no es un
    efecto sino lo de siempre.

    El origen es lo que separa la cadena del resto: si la carta que voltea es
    la que el jugador acaba de colocar, el efecto fue ese; si es una carta que
    ha caido antes en ESTA jugada, el efecto fue el domino.
    """
    origen_carta = board[r][c]
    if origen_carta is None:
        return [], []
    capturadas = []
    eventos = []
    dueno = origen_carta.dueno
    motivos = _motivos_captura(board, r, c)
    cola = []
    for pos, regla in sorted(motivos.items()):
        nr, nc = pos
        board[nr][nc].dueno = dueno
        capturadas.append(pos)
        eventos.append((None if regla == "basica" else regla, pos, (r, c)))
        if regla in ("same", "plus"):
            cola.append(pos)
    while cola:
        # Una oleada usa un solo estado del tablero: las bonificaciones no
        # dependen del orden N/S/E/O ni del orden de la cola.
        siguientes = {}
        for cr, cc in cola:
            for pos in sorted(_motivos_captura(board, cr, cc, especiales=False)):
                siguientes.setdefault(pos, (cr, cc))
        cola = sorted(siguientes)
        for nr, nc in cola:
            board[nr][nc].dueno = dueno
            capturadas.append((nr, nc))
            eventos.append((None, (nr, nc), siguientes[nr, nc]))
    return capturadas, eventos


def resumen_efectos(eventos, origen):
    """Que efectos se han activado en una jugada. Para el cartel.

    Devuelve un dict con las reglas que se activaron (sus cartas), mas
    `cadena`: cuantas cartas cayeron porque cayo una carta anterior en esta
    misma jugada. `origen` es la casilla donde se coloco la carta, que es lo
    que distingue "volteo por su cuenta" de "volteo por domino".
    """
    resumen = {"basica": 0, "cadena": 0}
    for regla, _pos, desde in eventos:
        if desde != origen:
            # No es un efecto en si, pero es lo que el jugador quiere ver: que
            # una sola jugada bien puesta voltea medio tablero.
            resumen["cadena"] += 1
        elif regla:
            resumen[regla] = resumen.get(regla, 0) + 1
        else:
            resumen["basica"] += 1
    return resumen


def capturas(board, r, c):
    """Captura cartas adyacentes con cadena. Devuelve lista de (fila, col)."""
    return cascada(board, r, c)[0]


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
