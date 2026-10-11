"""Simula duelos contra los dragones con las condiciones reales de campana.

Motivo: el jugador reporta que los dragones base son muy poderosos. Este
simulador mide cuantas veces es posible ganarles replicando EXACTAMENTE como
arma la campana cada mazo:

  - Jugador temprano: las 10 cartas mas debiles de su faccion (mazo_inicial)
    y se sortean 5, que es lo que ocurre en la senda y la aldea.
  - Jugador tardio: el mazo competitivo legal de campana (1 legendaria +
    3 raras + 6 comunes), 5 sorteadas.
  - Rival dragon: el mazo rival recortado por nivel de dificultad (pool de
    cartas debiles en los nodos tempranos, casi el mazo completo en el trono)
    con el refuerzo que aplica mazo_rival (70% por lado de sumar
    min(nivel, MAX_REFUERZO_RIVAL, 10 - valor)) y 5 sorteadas.

Escenarios por nivel (los del grafo de campana):
  senda=0  aldea=1  ruinas=2  fortaleza=2  asalto=2  trono=3

Metodologia identica a duelos_simulador.py: cada trial juega el cruce dos
veces con el orden invertido (la ventaja de empezar es estructural) y se
anota cada partida por separado, con politica aleatoria y voraz.

    python tests/simular_vs_dragon.py [--duelos N] [--semilla S]
"""

import argparse
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import campana  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402

from duelos_simulador import CARTAS_POR_DUELO, jugar_duelo, mazo_competitivo  # noqa: E402

FACCIONES_PLAYER = [f for f in facciones.orden_facciones() if f != "dragon"]


def mazo_temprano(faccion, rnd):
    """Las 10 mas debiles de la faccion (como arranca la campana), 5 sorteadas."""
    cartas = campana.mazo_inicial(faccion)
    return [c.copia() for c in rnd.sample(cartas, CARTAS_POR_DUELO)]


def mazo_tardio(faccion, rnd):
    """Maximo legal de campana: 1 legendaria + 3 raras + 6 comunes, 5 sorteadas."""
    return mazo_competitivo(faccion, rnd)


def mazo_rival_dragon(nivel, rnd):
    """Mazo rival de dragon como lo arma HOY mazo_rival: pool recortado por
    nivel (`_pool_rival`) + refuerzo con tope MAX_REFUERZO_RIVAL."""
    pool = campana._pool_rival("dragon", nivel)
    cartas = [c.copia() for c in pool]
    if nivel > 0:
        for c in cartas:
            for lado in ("N", "S", "E", "O"):
                if c.valores[lado] < 10 and rnd.random() < 0.7:
                    c.valores[lado] += min(nivel, campana.MAX_REFUERZO_RIVAL,
                                           10 - c.valores[lado])
    return [c.copia() for c in rnd.sample(cartas, CARTAS_POR_DUELO)]


def medir(faccion, mazo_jugador, nivel, voraz, n_duelos, semilla):
    """Victorias del jugador contra dragon. `mazo_jugador` fabrica la mano."""
    rnd = random.Random(semilla)
    vic_jug = vic_drag = 0
    for _ in range(n_duelos):
        dragon = mazo_rival_dragon(nivel, random.Random(rnd.randrange(2 ** 31)))
        mano = mazo_jugador(faccion, rnd)
        r1 = jugar_duelo(mano, dragon, rnd, voraz, True)
        r2 = jugar_duelo(mano, dragon, rnd, voraz, False)
        for r in (r1, r2):
            if r == "A":
                vic_jug += 1
            elif r == "B":
                vic_drag += 1
    total = vic_jug + vic_drag
    pct = 100.0 * vic_jug / total if total else 50.0
    err = _error(vic_jug, vic_drag)
    return pct, err


def _error(v, e):
    n = v + e
    if n <= 0:
        return 0.0
    p = v / n
    return 100.0 * 1.96 * math.sqrt(max(0.0, p * (1 - p)) / n)


def tabla(fabrica_mazo, niveles, etiquetas_filas, n_duelos, semilla, titulo):
    print(f"=== {titulo} ===")
    print(f"{'faccion':16s}", end="")
    for nivel in niveles:
        for politica in ("aleat", "voraz"):
            print(f" {'n' + str(nivel) + '(' + politica + ')':>12s}", end="")
    print()
    print("-" * (16 + 13 * len(niveles) * 2 + 2))
    for f in FACCIONES_PLAYER:
        print(f"{f:16s}", end="")
        for nivel in niveles:
            for voraz in (False, True):
                pct, err = medir(f, fabrica_mazo, nivel, voraz,
                                 n_duelos, semilla + sum(ord(c) for c in f))
                print(f" {pct:5.1f}%+-{err:3.1f}", end="")
        print()
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--duelos", type=int, default=300)
    ap.add_argument("--semilla", type=int, default=20261010)
    args = ap.parse_args()

    print(f"Simulacion vs DRAGON (rival: pool recortado por nivel + refuerzo)")
    print(f"{args.duelos} trials x 2 partidas por trial, orden invertido")
    print("Cifra = victorias del JUGADOR. 50 = paridad; <40 = cuesta arriba.")
    print()

    tabla(mazo_temprano, (0, 1), None, args.duelos, args.semilla,
          "TEMPRANO: jugador con las 10 mas debiles (senda n0, aldea n1)")

    tabla(mazo_tardio, (2, 3), None, args.duelos, args.semilla,
          "TARDIO: jugador con mazo competitivo 1L+3R+6C (ruinas/fortaleza n2, jefe n3)")


if __name__ == "__main__":
    main()