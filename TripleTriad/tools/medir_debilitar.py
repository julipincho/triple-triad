"""G8: efecto de `debilitar` en el trono con refuerzo capado.

`debilitar` es el efecto de varios encuentros: "el rival llegara mas debil". En
`campana.mazo_rival` el refuerzo del rival es
`nivel_pool - int(estado.get("debilitar", 0))`. En el trono el nivel es 3 y el
refuerzo se topa con `MAX_REFUERZO_RIVAL`, asi que la pregunta es si `debilitar`
sigue restando o si el tope se lo come.

Medida sobre la herramienta de produccion, con el motor real.

    python tools/medir_debilitar.py
"""

import os
import random
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_tmp = tempfile.TemporaryDirectory(prefix="tt_debilitar_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

import pygame  # noqa: E402

import campana  # noqa: E402
import facciones  # noqa: E402
from reglas import total_carta  # noqa: E402

from ui import ALTO, ANCHO  # noqa: E402


def fuerza_rival(estado, nodo):
    """Suma de lados del mazo rival que se enfrentaria en ese nodo."""
    return sum(total_carta(c) for c in campana.mazo_rival(estado, nodo))


def medir(nodo, facciones_prueba, n_sondas=40):
    """Cuanto resta `debilitar` a la fuerza del rival en ese nodo."""
    filas = []
    for faccion in facciones_prueba:
        estado = campana.nueva_campana(faccion)
        campana.asegurar_coleccion(faccion)
        campana.guardar(estado)
        base = fuerza_rival(estado, nodo)
        # `debilitar` se aplica hasta 2 veces; mas alla el refuerzo ya es 0.
        for veces in (1, 2, 3):
            estado["debilitar"] = veces
            campana.guardar(estado)
            filas.append((faccion, nodo, veces, base - fuerza_rival(estado, nodo)))
    return filas


def main():
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))
    facs = [f for f in facciones.orden_facciones() if f != "dragon"]

    print("Efecto de `debilitar` sobre la FUERZA del mazo rival")
    print(f"(motor real; campana.MAX_REFUERZO_RIVAL = {campana.MAX_REFUERZO_RIVAL})")
    print()
    print("Una faccion draws un solo rival por nodo (mazo_rival es determinista")
    print("por semilla), asi que aqui se mide de CUANTO resta, no de un duel.")
    print()
    print(f"{'nodo':11}{'nivel':>6}{'debilitar=1':>13}{'=2':>7}{'=3':>7}")
    for nodo in ("ruinas", "fortaleza", "asalto", "trono"):
        filas = medir(nodo, facs)
        nivel = campana.info_duelo(campana.nueva_campana("humano"), nodo)["dificultad"]
        por = {}
        for _f, _n, veces, resta in filas:
            por.setdefault(veces, []).append(resta)
        meds = {v: sum(por[v]) / len(por[v]) for v in (1, 2, 3)}
        print(f"{nodo:11}{nivel:>6}{meds[1]:>13.1f}{meds[2]:>7.1f}{meds[3]:>7.1f}")
    print()
    print("Un valor 0 significa que `debilitar` ya no resta nada: el tope del")
    print("refuerzo se lo ha comido y el encuentro no tendria efecto real.")
    return 0


if __name__ == "__main__":
    sys.exit(main())