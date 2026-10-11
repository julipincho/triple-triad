"""Calibra el recorte del pool rival por nivel de dificultad.

El rival hoy saca 5 cartas del pool completo de 25 (+refuerzo por nivel),
lo que hace a dragon (y a cualquier faccion fuerte) imposible en nodos
tempranos. La propuesta: `mazo_rival` recorta el pool segun el nivel.

Este script prueba varias configuraciones y reporta la MEDIA de victorias
del jugador sobre las 9 facciones, en cada nivel y politica. Configuracion =
(recorte, refuerzo): cuantas cartas del pool ordenado por total se usan en
cada nivel, y cuanto refuerzo (min(nivel, ...)) se aplica.

    python tests/calibrar_dragon.py [--duelos N]
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import campana  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
from reglas import total_carta  # noqa: E402

from duelos_simulador import CARTAS_POR_DUELO, jugar_duelo, mazo_competitivo  # noqa: E402

FACCIONES_PLAYER = [f for f in facciones.orden_facciones() if f != "dragon"]
NIVELES = (0, 1, 2, 3)


def pool_recortado(bando, nivel, recorte):
    pool = sorted(mazos.TODOS[bando], key=total_carta)
    return pool[:recorte[nivel]]


def mazo_rival_config(bando, nivel, recorte, refuerzo, rnd):
    pool = pool_recortado(bando, nivel, recorte)
    cartas = [c.copia() for c in pool]
    bonus = refuerzo[nivel]
    if bonus > 0:
        for c in cartas:
            for lado in ("N", "S", "E", "O"):
                if c.valores[lado] < 10 and rnd.random() < 0.7:
                    c.valores[lado] += min(bonus, 10 - c.valores[lado])
    return [c.copia() for c in rnd.sample(cartas, CARTAS_POR_DUELO)]


def mazo_temprano_jugador(faccion, rnd):
    return [c.copia() for c in rnd.sample(campana.mazo_inicial(faccion), CARTAS_POR_DUELO)]


def medir(faccion, nivel, voraz, config, n, semilla):
    recorte, refuerzo = config
    rnd = random.Random(semilla)
    mano_fab = mazo_competitivo if nivel >= 2 else mazo_temprano_jugador
    vic_p = vic_r = 0
    for _ in range(n):
        dragon = mazo_rival_config("dragon", nivel, recorte, refuerzo,
                                   random.Random(rnd.randrange(2 ** 31)))
        mano = mano_fab(faccion, rnd)
        for primero in (True, False):
            r = jugar_duelo(mano, dragon, rnd, voraz, primero)
            if r == "A":
                vic_p += 1
            elif r == "B":
                vic_r += 1
    tot = vic_p + vic_r
    return 100.0 * vic_p / tot if tot else 50.0


def probar(config, n_duelos, semilla=20261010):
    recorte, refuerzo = config
    print(f"\nConfig: recorte={recorte} refuerzo={refuerzo}")
    print(f"{'nivel':6s} {'aleatorio':>10s} {'voraz':>8s}")
    for nivel in NIVELES:
        medias = {}
        for voraz in (False, True):
            vals = [medir(f, nivel, voraz, config, n_duelos,
                          semilla + sum(ord(c) for c in f))
                    for f in FACCIONES_PLAYER]
            medias[voraz] = sum(vals) / len(vals)
        print(f"n{nivel}     {medias[False]:9.1f}% {medias[True]:7.1f}%")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--duelos", type=int, default=150)
    args = ap.parse_args()

    # Hoy: pool completo de 25 en todos los niveles, refuerzo por nivel.
    probar(([25, 25, 25, 25], [0, 1, 2, 3]), args.duelos)

    # Propuestas: el rival de la senda juega con un pool parecido al del
    # jugador (10 cartas), y el trono con todo.
    probar(([10, 14, 18, 25], [0, 1, 2, 3]), args.duelos)
    probar(([10, 13, 17, 25], [0, 1, 2, 3]), args.duelos)
    probar(([10, 14, 18, 22], [0, 1, 2, 2]), args.duelos)
    probar(([10, 14, 18, 25], [0, 1, 2, 2]), args.duelos)

    print("\nReferencia: 50 = paridad. Objetivo: senda 45-55, aldea 40-50,")
    print("trono 30-45 (jefe duro pero ganable). rango sano del juego: 35-65.")


if __name__ == "__main__":
    main()