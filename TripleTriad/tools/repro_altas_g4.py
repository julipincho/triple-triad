"""Reproduccion aislada del defecto G4: altas por draft/sobre que no pasan por
`validar_mazo`.

Uso:  python tools/repro_altas_g4.py
Solo lee y escribe en un directorio temporal: no toca datos reales.
"""

import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_tmp = tempfile.TemporaryDirectory(prefix="tt_repro_g4_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

import campana  # noqa: E402
from reglas import Carta, rareza, total_carta  # noqa: E402


def resumen_mazo(estado):
    """Rarezas y validacion del mazo actual."""
    rarezas = [rareza(Carta.desde_dict(d))[0] for d in estado["cartas"]]
    return {
        "n": len(estado["cartas"]),
        "LEG": rarezas.count("LEGENDARIA"),
        "RARA": rarezas.count("RARA"),
        "COMUN": rarezas.count("COMUN"),
        "nombres": [d["nombre"] for d in estado["cartas"]],
    }


def caso_sobre_legendaria():
    """Intenta meter 3 legendarias seguidas abriendo sobres."""
    print("=" * 70)
    print("CASO 1: sobres hasta acumular legendarias")
    print("=" * 70)
    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)
    for intento in range(1, 13):
        nuevas, _ = campana.abrir_sobre(estado, cantidad=3)
        r = resumen_mazo(estado)
        ok, motivo = campana.validar_mazo(estado["cartas"], campana.coleccion_de())
        marca = "OK " if ok else "MAL"
        print(f"  sobre {intento:2d}: +{len(nuevas)} nuevas | mazo n={r['n']} "
              f"LEG={r['LEG']} RARA={r['RARA']} COMUN={r['COMUN']} -> {marca}"
              + (f" ({motivo})" if not ok else ""))
        if not ok:
            print(f"    mazo: {r['nombres']}")
            return False
    return True


def caso_draft_legendaria():
    """Fuerza un draft de legendaria con el mazo lleno."""
    print()
    print("=" * 70)
    print("CASO 2: draft de legendaria con mazo lleno (sustitucion)")
    print("=" * 70)
    import mazos

    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)

    # Mazo lleno con 1 legendaria ya dentro y cartas debiles alrededor.
    leg = next(c for c in mazos.TODOS["humano"] if rareza(c)[0] == "LEGENDARIA")
    debiles = sorted(
        (c for c in mazos.TODOS["humano"] if rareza(c)[0] == "COMUN"),
        key=total_carta,
    )[:9]
    estado["cartas"] = [leg.a_dict()] + [c.a_dict() for c in debiles]
    campana.guardar(estado)
    print(f"  mazo inicial: LEG={resumen_mazo(estado)['LEG']}, "
          f"nombre de la legendaria: {leg.nombre}")

    # El draft ofrece esa misma legendaria: se anade por 'sustitucion'.
    campana.anadir_carta(estado, leg.copia())
    r = resumen_mazo(estado)
    ok, motivo = campana.validar_mazo(estado["cartas"], campana.coleccion_de())
    print(f"  tras anadir la MISMA legendaria: n={r['n']} LEG={r['LEG']} "
          f"RARA={r['RARA']} -> {'OK' if ok else 'MAL'}"
          + (f" ({motivo})" if not ok else ""))
    if not ok:
        print(f"    mazo: {r['nombres']}")
    return ok


def caso_duplicados():
    """Fuerza duplicados en el mazo por sobre."""
    print()
    print("=" * 70)
    print("CASO 3: mazo lleno, sobre con cartas que ya estan dentro")
    print("=" * 70)
    import mazos

    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)
    comunes = [c for c in mazos.TODOS["humano"] if rareza(c)[0] == "COMUN"][:10]
    for c in comunes:
        campana.otorgar_base(c.nombre, c.a_dict())
    estado["cartas"] = [c.a_dict() for c in comunes]
    campana.guardar(estado)

    # Via REAL del alta automatica, no un `append` a pelo que se saltaria la
    # politica y solo mediria el fallo del propio script.
    for c in comunes[:3]:
        campana.anadir_carta(estado, c.copia())
    nombres = [d["nombre"] for d in estado["cartas"]]
    duplicados = {n for n in nombres if nombres.count(n) > 1}
    ok, motivo = campana.validar_mazo(estado["cartas"], campana.coleccion_de())
    print(f"  mazo: {len(nombres)} cartas, duplicados={sorted(duplicados) or 'ninguno'}")
    print(f"  validacion -> {'OK' if ok else 'MAL: ' + motivo}")
    return ok


if __name__ == "__main__":
    print("Reproduccion de las altas por draft/sobre frente a validar_mazo")
    print(f"datos aislados en: {_tmp.name}")
    print(f"LIMITE_LEGENDARIAS={campana.LIMITE_LEGENDARIAS} "
          f"LIMITE_RARAS={campana.LIMITE_RARAS} "
          f"MAZO_MIN_N={campana.MAZO_MIN_N} MAZO_RUN_N={campana.MAZO_RUN_N}")
    print()
    r1 = caso_sobre_legendaria()
    r2 = caso_draft_legendaria()
    r3 = caso_duplicados()
    print()
    print("=" * 70)
    print(f"RESULTADO: sobres={'pasa' if r1 else 'FALLA'}  "
          f"draft={'pasa' if r2 else 'FALLA'}  "
          f"duplicados={'pasa' if r3 else 'FALLA'}")
    print("=" * 70)