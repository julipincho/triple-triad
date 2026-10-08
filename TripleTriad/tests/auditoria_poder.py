"""Auditoria de poder: curva por faccion y reglas de balance.

    python tests/auditoria_poder.py

Devuelve codigo 1 si alguna regla se viola:
- toda faccion tiene al menos una carta de cada rareza en su pool
- ninguna comun supera en total a una legendaria de su faccion
- la media de totales por faccion esta entre 20 y 30
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mazos import TODOS  # noqa: E402
from reglas import rareza, total_carta  # noqa: E402


def auditar_poder():
    problemas = []
    for bando, cartas in TODOS.items():
        por_rar = {}
        for c in cartas:
            por_rar.setdefault(rareza(c)[0], []).append(total_carta(c))
        for r in ("COMUN", "RARA", "LEGENDARIA"):
            if not por_rar.get(r):
                problemas.append(f"[{bando}] sin cartas {r}")
        if por_rar.get("COMUN") and por_rar.get("LEGENDARIA"):
            if max(por_rar["COMUN"]) >= min(por_rar["LEGENDARIA"]):
                problemas.append(
                    f"[{bando}] una comun ({max(por_rar['COMUN'])}) "
                    f"alcanza a una legendaria ({min(por_rar['LEGENDARIA'])})")
        media = sum(total_carta(c) for c in cartas) / max(1, len(cartas))
        if not 20 <= media <= 30:
            problemas.append(f"[{bando}] media {media:.1f} fuera de 20-30")
    return problemas


def main():
    for bando, cartas in TODOS.items():
        tots = sorted(total_carta(c) for c in cartas)
        print(f"  {bando}: n={len(tots)} min={tots[0]} media={sum(tots)/len(tots):.1f} max={tots[-1]}")
    problemas = auditar_poder()
    if problemas:
        print(f"\nAUDITORIA DE PODER: {len(problemas)} problemas:")
        for p in problemas:
            print(f"  - {p}")
        return 1
    print("\nAuditoria de poder: curvas sanas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
