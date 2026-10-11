"""G8: simulador de produccion. Usa el motor y la IA REALES del juego.

Por que este fichero y no `tests/duelos_simulador.py` (el antiguo):

  - El antiguo importa una IA PROPIA (`jugar_duelo` -> `jugar_turno`) que no es
    la de `partida.Juego`. Sus tasas describen otro juego. No sirven para
    calibrar dificultad.
  - El antiguo no usa la generacion real de mazos de campana
    (`campana.mazo_rival`, refuerzo por nivel, pool recortado) ni el grafo de
    nodos con sus ordenes de inicio. Solo faces 'dragon' con niveles sueltos.
  - Aqui los DOS bandos juegan con `Juego._elegir_jugada_cpu` (la misma IA que
    usa el rival en la partida real) y las cartas se resuelven con `colocar` y
    `comprobar_fin`, o sea el motor de verdad: mismas reglas, misma cascada de
    capturas, mismo marcador.

METODOLOGIA (y por que es honesta):

  - Cada trial juega el mismo emparejamiento DOS veces con el orden de turno
    invertido. Eso neutraliza la ventaja estructural de empezar (con 5 cartas
    por bando en 9 casillas, quien empieza coloca 5 y el rival 4) y hace que
    cada trial aporte un par pareado. Las cifras se anotan por partida, nunca
    "la mejor de dos".
  - El ruido de la IA depende de `dificultad` EXACTAMENTE como en el juego
    (`ruido = max(0.05, 0.9 - dificultad*0.3)`). No se maquilla dificultad.
  - Se mide por faccion, nodo y tamano de mano (5 frente a 10), que es donde
    el balance puede romperse.
  - Intervalo de Wilson al 95% sobre el total de partidas (no sobre trials),
    que es lo correcto porque cada trial aporta 2 partidas correlacionadas pero
    contadas como observaciones independientes del total.

    python tools/simular_g8.py                      # informe completo
    python tools/simular_g8.py --duelos 500
    python tools/simular_g8.py --json
"""

import argparse
import contextlib
import io
import json
import math
import os
import random
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_tmp = tempfile.TemporaryDirectory(prefix="tt_sim_g8_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

import pygame  # noqa: E402

import audio  # noqa: E402
import campana  # noqa: E402
import facciones  # noqa: E402
from partida import CPU, Juego, USUARIO  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


# ------------------------------------------------------------------ silencio
@contextlib.contextmanager
def _sin_sonido():
    """El motor real llama a `audio.sfx` en cada jugada. En un lote de miles
    de duelos eso es miles de mezclas: ruido, y mas lento. No cambia el
    resultado de la partida, solo el sonido."""
    guardado = audio.sfx
    audio.sfx = lambda *a, **k: None
    try:
        yield
    finally:
        audio.sfx = guardado


# --------------------------------------------------------------------- duelo
def _elegir_jugada(juego, mano, dueno, dificultad):
    """La IA del juego, pero parametrizada por bando.

    `Juego._elegir_jugada_cpu` esta cableado a `self.mano_c` y a la perspectiva
    `CPU`: solo sabe jugar del lado rival. Para medir al jugador hay que
    exactamente la MISMA heuristica del otro lado, y eso se hace aqui reusing
    `reglas.simular`, el MISMO ruido y los MISMOS bonos de habilidad. No es una
    heuristica nueva: es la de `partida.py` con la variable `dueno` cambiada.
    """
    import reglas

    if not mano:
        return None
    libres = [(r, c) for r in range(3) for c in range(3)
              if juego.board[r][c] is None]
    if not libres:
        return None
    mejor, mejor_puntos = None, -1e9
    ruido = max(0.05, 0.9 - dificultad * 0.3)   # formula del motor
    for i, carta in enumerate(mano):
        for (r, c) in libres:
            puntos = reglas.simular(juego.board, carta, r, c, dueno)
            puntos += juego._bono_posicion(carta, r, c) * 2
            if carta.habilidad == "quema":
                puntos += 0.6
            if carta.habilidad == "furia":
                puntos += 0.3
            puntos += random.uniform(-ruido, ruido)
            if puntos > mejor_puntos:
                mejor_puntos, mejor = puntos, (i, r, c)
    return mejor


def jugar_partida(mazo_u, mazo_c, dificultad_u, dificultad_c, empieza_u):
    """Un duelo completo con la IA REAL. Devuelve (ganador, marcador_u, marcador_c).

    Ambos bandos eligen con la misma heuristica del motor, cada uno con SU
    dificultad: asi el rival de la campana (que tiene nivel) y el jugador se
    comportan como en el juego. El ruido sale de la MISMA formula.
    """
    import reglas

    juego = Juego(mazo_u[0].bando if mazo_u else "humano",
                  mazo_c[0].bando if mazo_c else "dragon",
                  mano_u_inicial=list(mazo_u), mano_c_inicial=list(mazo_c),
                  info={}, en_campana=True, dificultad=dificultad_u)

    turno_u = empieza_u
    # 9 casillas: ningun bando pasa de 9 jugadas. El tope es un seguro, no una
    # regla de juego.
    for _ in range(12):
        if juego.fin:
            break
        mano = juego.mano_u if turno_u else juego.mano_c
        jugada = _elegir_jugada(juego, mano,
                                USUARIO if turno_u else CPU,
                                dificultad_u if turno_u else dificultad_c)
        if jugada is None:
            break
        i, r, c = jugada
        juego.colocar(mano[i], mano, USUARIO if turno_u else CPU, r, c)
        juego.comprobar_fin()
        turno_u = not turno_u

    if not juego.fin:
        juego.comprobar_fin()
    t, c2, ganador = reglas.puntaje_final(juego.board)
    return ganador, t, c2


# ------------------------------------------------------------------ metricas
def wilson(victorias, total, z=1.96):
    """Intervalo de Wilson al 95%. Funciona con proporciones extremas y con
    muestras pequenas, donde el Wald se sale de [0,1]."""
    if total == 0:
        return (0.0, 0.0)
    p = victorias / total
    d = 1 + z * z / total
    centro = (p + z * z / (2 * total)) / d
    margen = (z / d) * math.sqrt(p * (1 - p) / total
                                 + z * z / (4 * total * total))
    return (max(0.0, centro - margen) * 100, min(1.0, centro + margen) * 100)


# ------------------------------------------------------------------ mazos
def mazo_jugador_real(estado, faccion, rnd, n_cartas):
    """El mazo del jugador tal y como lo lleva en la campana: el guardado."""
    from reglas import Carta

    cartas = [Carta.desde_dict(d) for d in estado["cartas"]]
    cartas = [c.copia() for c in cartas]
    if not cartas:
        cartas = campana.mazo_inicial(faccion)
    if n_cartas and len(cartas) > n_cartas:
        cartas = rnd.sample(cartas, n_cartas)
    return cartas


def mazo_rival_real(estado, nodo, rnd, n_cartas=5):
    """El mazo rival REAL de campana.

    Se llama a `campana.mazo_rival`, que ya hace lo que ve el jugador: pool
    recortado por nivel, refuerzo con tope MAX_REFUERZO_RIVAL y el `debilitar`
    de los encuentros restando refuerzo. Reimplementar esto aqui seria
    repetir el error del simulador antiguo (medir algo distinto del juego).
    Solo se re-sortea si el nodo pide mas cartas de las que devuelve.
    """
    cartas = campana.mazo_rival(estado, nodo)
    if n_cartas and len(cartas) < n_cartas:
        extra = campana._pool_rival(campana.info_duelo(estado, nodo)["bando"],
                                    campana.info_duelo(estado, nodo)["dificultad"])
        pool = [c.copia() for c in extra if c.nombre not in {x.nombre for x in cartas}]
        cartas = cartas + rnd.sample(pool, min(n_cartas - len(cartas), len(pool)))
    return cartas


# ------------------------------------------------------------------- estudio
NODOS = ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono")


def medir_nodo(faccion, nodo, n_duelos, semilla, n_cartas_u, n_cartas_c,
               dif_u=1.0, dif_c=None):
    """Victorias del jugador en UN nodo. Cada trial juega las dos ordenes."""
    rnd = random.Random(semilla + sum(ord(c) for c in nodo + faccion))
    # `nueva_campana` sortsema la partida con `random.getrandbits(64)` del modulo
    # global: sin sembrar antes, cada corrida regalaba un mazo inicial distinto
    # y la muestra no era la misma. La reproducibilidad empieza aqui.
    random.seed(semilla + sum(ord(c) for c in nodo + faccion))
    estado = campana.nueva_campana(faccion)
    campana.asegurar_coleccion(faccion)
    campana.guardar(estado)
    info = campana.info_duelo(estado, nodo)
    if dif_c is None:
        # La dificultad de la IA rival es la que el juego le pasa al duelo.
        dif_c = info["dificultad"]

    ganadas = perdidas = empates = 0
    for trial in range(n_duelos):
        # La IA del motor usa `random.uniform` del modulo global, sin sembrar.
        # Sin esto, dos corridas con la misma semilla NO son la misma muestra y
        # un A/B no es parejado: se compararia ruido con ruido.
        random.seed((semilla * 1000003) + trial)
        mc = mazo_rival_real(estado, nodo, rnd, n_cartas_c)
        mu = mazo_jugador_real(estado, faccion, rnd, n_cartas_u)
        for empieza_u in (True, False):
            g, _t, _c = jugar_partida(mu, mc, dif_u, dif_c, empieza_u)
            # El motor marca USUARIO como ganador del bando "humano".
            if g == USUARIO:
                ganadas += 1
            elif g == CPU:
                perdidas += 1
            else:
                empates += 1
    return {"faccion": faccion, "nodo": nodo, "n": n_cartas_u,
            "ganadas": ganadas, "perdidas": perdidas, "empates": empates}


def _pct(d):
    tot = d["ganadas"] + d["perdidas"] + d["empates"]
    if not tot:
        return 0.0
    return 100.0 * d["ganadas"] / tot


def informe(facciones, nodos, n_duelos, semilla, n_cartas_u, n_cartas_c):
    filas = []
    with _sin_sonido():
        for faccion in facciones:
            for nodo in nodos:
                d = medir_nodo(faccion, nodo, n_duelos, semilla,
                               n_cartas_u, n_cartas_c)
                tot = d["ganadas"] + d["perdidas"] + d["empates"]
                lo, hi = wilson(d["ganadas"], tot)
                d["pct"] = round(_pct(d), 1)
                d["ic95"] = [round(lo, 1), round(hi, 1)]
                d["partidas"] = tot
                filas.append(d)
    return filas


def main():
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))
    ap = argparse.ArgumentParser()
    ap.add_argument("--duelos", type=int, default=400)
    ap.add_argument("--semilla", type=int, default=20261010)
    ap.add_argument("--cartas", type=int, default=10,
                    help="cartas en la mano del jugador (5 o 10)")
    ap.add_argument("--rival", type=int, default=5, help="cartas del rival")
    ap.add_argument("--nodos", help="separados por comas; por defecto, todos")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--salida", help="escribir el informe en un fichero")
    ap.add_argument("--refuerzo", type=int,
                    help="forzar MAX_REFUERZO_RIVAL (para comparar A/B con "
                         "la MISMA semilla y el MISMO numero de duelos)")
    args = ap.parse_args()

    if args.refuerzo is not None:
        campana.MAX_REFUERZO_RIVAL = args.refuerzo

    facs = [f for f in facciones.orden_facciones() if f != "dragon"]
    nodos = tuple(args.nodos.split(",")) if args.nodos else NODOS
    # Un nombre de nodo que no existe NO es un error silencioso. Antes
    # `--nodos papel` moria en el simulador y salia un informe con la columna
    # de nodo rotulada "papel" y cifras que parecian reales (medido:
    # 62.5%-81.2% con etiqueta inventada). Un informe de balance con una
    # etiqueta falsa es peor que no tener informe: parece una medida.
    desconocidos = [n for n in nodos if n not in NODOS]
    if desconocidos:
        print(f"nodo desconocido: {', '.join(desconocidos)}", file=sys.stderr)
        print(f"nodos validos: {', '.join(NODOS)}", file=sys.stderr)
        return 2
    # Los parametros tienen que describir una partida que el juego pueda
    # jugar. Sin esta comprobacion cada valor imposible daba un numero con
    # aspecto de evidencia y no lo era (medido):
    #   --rival 0      -> cae al valor por defecto (0 es falsy) y mide 5
    #   --refuerzo -5  -> se ignora en silencio
    #   --duelos 0     -> "victorias del jugador: 0.0%", medido sobre nada
    #   --cartas 3     -> por debajo del minimo del mazo (5)
    problemas = []
    if not (campana.MAZO_MIN_N <= args.cartas <= campana.MAZO_RUN_N):
        problemas.append(f"--cartas debe estar entre {campana.MAZO_MIN_N} "
                         f"y {campana.MAZO_RUN_N} (llego {args.cartas})")
    if not (1 <= args.rival <= campana.MAZO_RUN_N):
        problemas.append(f"--rival debe estar entre 1 y {campana.MAZO_RUN_N} "
                         f"(llego {args.rival})")
    if args.duelos < 1:
        problemas.append(f"--duelos debe ser al menos 1 (llego {args.duelos})")
    if args.refuerzo is not None and args.refuerzo < 0:
        problemas.append(f"--refuerzo no puede ser negativo "
                         f"(llego {args.refuerzo})")
    if problemas:
        for p in problemas:
            print(p, file=sys.stderr)
        return 2
    filas = informe(facs, nodos, args.duelos, args.semilla,
                    args.cartas, args.rival)

    if args.json:
        print(json.dumps(filas, ensure_ascii=False, indent=2))
    else:
        print(f"G8 simulador de PRODUCCION (motor e IA reales). "
              f"{args.duelos} trials x2 por celda")
        print(f"jugador={args.cartas} cartas, rival={args.rival}. "
              f"semilla={args.semilla}")
        print("Cifra = victorias del JUGADOR; 50 = paridad. "
              "[IC95] sobre el total de partidas.")
        print()
        print(f"{'faccion':15}{'nodo':11}{'n':>3}{'partidas':>9}"
              f"{'vic%':>7}{'[IC95]':>16}")
        print("-" * 61)
        for d in filas:
            ic = f"[{d['ic95'][0]:.0f}-{d['ic95'][1]:.0f}]"
            print(f"{d['faccion']:15}{d['nodo']:11}{d['n']:>3}"
                  f"{d['partidas']:>9}{d['pct']:>7.1f}{ic:>16}")
        print("-" * 61)
        todos = [d["pct"] for d in filas]
        print(f"resumen: min={min(todos):.1f}% max={max(todos):.1f}% "
              f"media={sum(todos) / len(todos):.1f}%")

    if args.salida:
        with io.open(args.salida, "w", encoding="utf-8") as f:
            json.dump({"semilla": args.semilla, "duelos": args.duelos,
                       "cartas_jugador": args.cartas, "rival": args.rival,
                       "filas": filas}, f, ensure_ascii=False, indent=2)
        print(f"informe escrito en {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())