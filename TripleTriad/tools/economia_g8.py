"""G8 (economia) + G5 (oferta directa): ritmo de compras de una campana REAL.

El objetivo pide medir "mejoras, reintentos y ritmo de compras", y G5 pide
"evaluar despues, segun economia medida, una oferta directa limitada para
reducir dependencia del azar; no introducirla sin validar coste y progresion".

Este simulador juega una campana entera nodo por nodo con el motor y la IA
reales de `simular_g8`, y aplica la economia real de `campana.py`:

  - moneda por duelo = base + victoria + capturas
  - el jugador compra sobres en cuanto puede, con la garantia (pity) incluida
  - los reintentos salen de perder: se juega otra vez el mismo nodo
  - la recompensa de nodo se cobra y se aplica de verdad
  - se mide ademas el efecto de regalar el PRIMER sobre (oferta directa)
    limitada que G5 pide evaluar antes de introducirla

    python tools/economia_g8.py
"""

import os
import random
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tools"))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_tmp = tempfile.TemporaryDirectory(prefix="tt_economia_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

import pygame  # noqa: E402

import campana  # noqa: E402
import facciones  # noqa: E402
from partida import Resultado, USUARIO  # noqa: E402
from reglas import Carta, rareza  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402

import simular_g8 as SIM  # noqa: E402

#: Nodos con recompensa. El `trono` NO ofrece ninguna (`recompensas_de` devuelve
#: lista vacia): es el remate de la campana, se gana y se cierra la historia.
NODOS_CON_PREMIO = ("senda", "aldea", "ruinas", "fortaleza", "asalto")
NODO_FINAL = "trono"


def _elegir_premio(nodo):
    """La recompensa que mas progresa sin pedirle nada al jugador.

    `sigilo` sube el lado mas debil de TODAS las cartas y no necesita elegir
    carta; es la mejor compra de progreso automatico. `recluta` exigiria una
    carta concreta y un indice, asi que se deja para cuando sea lo unico.
    """
    opc = campana.recompensas_de(nodo)
    for clave in ("sigilo", "entrenamiento", "aliado", "sobre"):
        if clave in opc:
            return clave
    return opc[0] if opc else None


def _nueva_campana(faccion, semilla):
    """Campana desde cero, con el PERFIL tambien desde cero.

    Sin vaciar el perfil, las nueve campañas se acumulan en la misma coleccion
    y la comparacion queda sin sentido: el segundo grupo empieza con cinco
    veces mas cartas que el primero y por eso compra menos "nuevas". Cada
    campana tiene que partir del mismo punto.
    """
    random.seed(semilla)
    campana.guardar_perfil({})        # coleccion, moneda y finales a cero
    estado = campana.nueva_campana(faccion)
    campana.asegurar_coleccion(faccion)
    campana.guardar(estado)
    campana.gastar_moneda(campana.moneda())
    return estado


def _duelo(estado, nodo, dif_jugador):
    """Un duelo real. Devuelve (victoria, capturas, moneda, cartas_nuevas)."""
    rnd = random
    mc = SIM.mazo_rival_real(estado, nodo, rnd, 5)
    mu = SIM.mazo_jugador_real(estado, estado["faccion"], rnd, len(estado["cartas"]))
    dif_rival = campana.info_duelo(estado, nodo)["dificultad"]
    ganador, mios, suyos = SIM.jugar_partida(mu, mc, dif_jugador, dif_rival, True)
    capturas = max(0, mios - suyos)
    r = Resultado(ganador == USUARIO, capturas, 9, (mios, suyos))
    moneda = campana.registrar_resultado(estado, r)
    return ganador == USUARIO, moneda


def _comprar(estado):
    ok, nuevas, mejoradas = campana.comprar_sobre(estado)
    if not ok:
        return 0, 0
    nuevas_nombre = set(nuevas)
    leg = sum(1 for n in nuevas_nombre
              if rareza(Carta.desde_dict(campana.coleccion_de()[n]))[0] == "LEGENDARIA")
    return len(nuevas_nombre), leg


def jugar_campana(faccion, semilla, dif_jugador=1.0, max_reintentos=6,
                  primer_sobre_gratis=False):
    """Una campana completa con la economia real. Devuelve un resumen."""
    estado = _nueva_campana(faccion, semilla + sum(ord(c) for c in faccion))
    compras = nuevas_total = legendarias = reintentos = duelo_n = 0
    completa = False

    if primer_sobre_gratis:
        campana.ganar_moneda(campana.PRECIO_SOBRE)   # el regalo no cuesta nada
        n, l = _comprar(estado)
        compras += 1
        nuevas_total += n
        legendarias += l

    for nodo in NODOS_CON_PREMIO:
        intentos = 0
        gano = False
        while intentos <= max_reintentos:
            intentos += 1
            duelo_n += 1
            gano, _moneda = _duelo(estado, nodo, dif_jugador)
            if intentos > 1:
                reintentos += 1
            if gano:
                clave = _elegir_premio(nodo)
                if clave:
                    campana.entregar_recompensa(estado, clave, nodo, idx=0)
                break
        if not gano:
            break
        while campana.moneda() >= campana.PRECIO_SOBRE:
            n, l = _comprar(estado)
            compras += 1
            nuevas_total += n
            legendarias += l

    # El remate: ganar el trono cierra la campana (no da recompensa).
    intentos = 0
    while intentos <= max_reintentos:
        intentos += 1
        duelo_n += 1
        gano, _moneda = _duelo(estado, NODO_FINAL, dif_jugador)
        if intentos > 1:
            reintentos += 1
        if gano:
            break
    while campana.moneda() >= campana.PRECIO_SOBRE:
        n, l = _comprar(estado)
        compras += 1
        nuevas_total += n
        legendarias += l

    completa = bool(estado.get("completada"))
    return {
        "faccion": faccion,
        "duelos": duelo_n,
        "reintentos": reintentos,
        "compras": compras,
        "gastado": compras * campana.PRECIO_SOBRE,
        "moneda_final": campana.moneda(),
        "cartas_nuevas": nuevas_total,
        "legendarias": legendarias,
        "coleccion": len(campana.coleccion_de()),
        "completo": completa,
    }


def _tabla(filas, titulo):
    print("--- %s ---" % titulo)
    print("%-15s%8s%9s%9s%8s%8s%8s%7s%10s"
          % ("faccion", "duelos", "reintent", "compras", "gastado",
             "nuevas", "legend", "colec", "completa"))
    for r in filas:
        print("%-15s%8d%9d%9d%8d%8d%8d%7d%10s"
              % (r["faccion"], r["duelos"], r["reintentos"], r["compras"],
                 r["gastado"], r["cartas_nuevas"], r["legendarias"],
                 r["coleccion"], "si" if r["completo"] else "NO"))
    comp = sum(1 for r in filas if r["completo"])
    n = len(filas)
    media = lambda k: sum(r[k] for r in filas) / float(n)
    print("  completan %d/%d | duelos %.1f | reintentos %.1f | compras %.1f"
          % (comp, n, media("duelos"), media("reintentos"), media("compras")))
    print("  cartas nuevas %.1f | legendarias %.2f | coleccion %.0f | moneda sin usar %.0f"
          % (media("cartas_nuevas"), media("legendarias"), media("coleccion"),
             media("moneda_final")))
    print()
    return comp, n


def main():
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))
    facs = [f for f in facciones.orden_facciones() if f != "dragon"]
    try:
        n_semillas = int(os.environ.get("TT_SEMILLAS", "6"))
    except ValueError:
        print(f"TT_SEMILLAS no es un numero: {os.environ.get('TT_SEMILLAS')!r}")
        return 2
    if n_semillas < 1:
        # Con 0 semillas la tabla divide por cero y el informe no existe. Un
        # "0 campanas" con medias calculadas seria un numero falso; aqui se
        # dice que no hay muestra.
        print("TT_SEMILLAS tiene que ser al menos 1: sin muestras no hay nada "
              "que promediar.")
        return 2
    semillas = [777 + 1000 * k for k in range(n_semillas)]

    print("Economia de una campana completa (motor, recompensas y sobres reales)")
    print("moneda: duelo=%d victoria=%d captura=%d | sobre=%d garantia cada %d"
          % (campana.MONEDA_POR_DUELO, campana.MONEDA_VICTORIA,
             campana.MONEDA_POR_CAPTURA, campana.PRECIO_SOBRE, campana.PITY_SOBRES))
    print("muestra: %d facciones x %d semillas = %d campanas por grupo"
          % (len(facs), len(semillas), len(facs) * len(semillas)))
    print()

    normal = [jugar_campana(f, s) for f in facs for s in semillas]
    regalo = [jugar_campana(f, s, primer_sobre_gratis=True)
              for f in facs for s in semillas]

    cn, n = _tabla(normal, "NORMAL")
    cg, _ = _tabla(regalo, "CON 1er SOBRE REGALADO (oferta directa)")

    print("=" * 66)
    print("Diferencia por el regalo del primer sobre (media por campana):")
    dn = sum(r["cartas_nuevas"] for r in normal) / float(n)
    dg = sum(r["cartas_nuevas"] for r in regalo) / float(n)
    ln = sum(r["legendarias"] for r in normal) / float(n)
    lg = sum(r["legendarias"] for r in regalo) / float(n)
    tn = sum(r["compras"] for r in normal) / float(n)
    tg = sum(r["compras"] for r in regalo) / float(n)
    tot_n = sum(r["legendarias"] for r in normal)
    tot_g = sum(r["legendarias"] for r in regalo)
    print("  sobres comprados: %.2f -> %.2f  (%+.2f)" % (tn, tg, tg - tn))
    print("  cartas nuevas:    %.2f -> %.2f  (%+.2f)" % (dn, dg, dg - dn))
    print("  legendarias:      %.2f -> %.2f  (%+.2f)   [totales %d -> %d]"
          % (ln, lg, lg - ln, tot_n, tot_g))
    print("  campanas completadas: %d/%d -> %d/%d" % (cn, n, cg, n))
    if tot_n + tot_g < 20:
        print()
        print("  AVISO: el total de legendarias (%d) es demasiado pequeno para"
              % (tot_n + tot_g))
        print("  concluir nada. No se puede afirmar que el regalo cambie la")
        print("  dependencia del azar: falta muestra, no falta analisis.")
    print("=" * 66)
    return 0


if __name__ == "__main__":
    sys.exit(main())