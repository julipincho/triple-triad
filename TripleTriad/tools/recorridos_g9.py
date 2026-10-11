"""G9: recorridos INTEGRADOS de extremo a extremo.

La auditoria visual existente (`tests/auditoria_visual.py`) mira si un rect se
sale de la pantalla. Esto es otra cosa: comprobar que un jugador puede
recorrer el juego de principio a fin sin perder progreso, sin quedarse sin
moneda sin poder comprar, sin reintentar sin consecuencias, y sin un final que
no llegue.

Cada recorrido usa la campana real (`campana.*`, `pantallas.menu`), no una
copia. Los datos van a un directorio temporal: nada toca la partida real.

    python tools/recorridos_g9.py
"""

import asyncio
import os
import sys
import tempfile
from unittest.mock import patch

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_tmp = tempfile.TemporaryDirectory(prefix="tt_recorridos_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

import pygame  # noqa: E402

import campana  # noqa: E402
import opciones  # noqa: E402
import pantallas  # noqa: E402
from partida import Resultado  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


class Reloj:
    def tick(self, fps=60):
        return 16


def _pantalla():
    return pygame.display.set_mode((ANCHO, ALTO))


def _resultado(victoria, capturas=0, jugadas=0, marcador=(3, 2)):
    return Resultado(victoria, capturas, jugadas, marcador)


# --------------------------------------------------------------- recorridos
def recorrido_nuevo_jugador():
    """Sin partida, el menu debe ofrecer empezar de cero."""
    clic = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                              pos=(ANCHO // 2 - 340 + 150, 210 + 27))
    with patch("pygame.event.get", return_value=[clic]):
        accion = asyncio.run(pantallas.menu(_pantalla(), Reloj(), None))
    if accion != "nueva":
        return [f"sin partida, el menu no ofrece 'nueva' (ofrecio {accion!r})"]
    return []


def recorrido_reanudacion():
    """Guardar, reabrir y continuar: el estado debe ser el mismo."""
    problemas = []
    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    nodo = estado["nodo"]
    cartas = [d["nombre"] for d in estado["cartas"]]
    campana.guardar(estado)

    recuperada = campana.cargar()
    if recuperada is None:
        return ["no se pudo recuperar la partida guardada"]
    if recuperada["nodo"] != nodo:
        problemas.append(f"el nodo no sobrevive: {nodo} -> {recuperada['nodo']}")
    if [d["nombre"] for d in recuperada["cartas"]] != cartas:
        problemas.append("el mazo no sobrevive al guardado")
    if not campana.puede_continuar(recuperada):
        problemas.append("una partida a medias no se puede continuar")
    return problemas


def recorrido_derrota_y_reintento():
    """Perder no avanza el nodo; ganar si. Y el contrato de moneda es el real.

    Ojo, que aqui es facil comprobar una expectativa equivocada: perder SI da
    moneda. `premio_duelo` es "base + victoria + capturas" y la base es por
    duelo COMPLETADO, win or lose; el desglose se lo enseña al jugador en la
    pantalla de recompensa. Lo que NO debe dar moneda es abandonar, que es
    justamente lo que revisa `recorrido_abandonar`.
    """
    problemas = []
    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)
    nodo_inicial = estado["nodo"]

    # Derrota: no avanza, cuenta la derrota, paga solo la base del duelo.
    antes = campana.moneda()
    ganado = campana.registrar_resultado(estado, _resultado(False, 0, 5, (1, 4)))
    if estado["nodo"] != nodo_inicial:
        problemas.append("perder avanza el nodo: no se puede reintentar el mismo")
    if estado.get("derrotas", 0) != 1:
        problemas.append("perder no conto la derrota")
    if ganado != campana.MONEDA_POR_DUELO:
        problemas.append(f"una derrota deberia pagar solo la base "
                         f"({campana.MONEDA_POR_DUELO}), pago {ganado}")
    if campana.moneda() - antes != ganado:
        problemas.append("la moneda cobrada no coincide con la anunciada")

    # Victoria: avanza y paga mas que una derrota con las mismas capturas.
    antes = campana.moneda()
    ganado = campana.registrar_resultado(estado, _resultado(True, 2, 5, (5, 4)))
    if estado["nodo"] == nodo_inicial:
        problemas.append("ganar no avanza el nodo")
    if campana.moneda() <= antes:
        problemas.append("ganar no dio moneda")
    detalle = estado.get("ultimo_premio") or {}
    if detalle.get("total") != ganado:
        problemas.append("el desglose de moneda no cuadra con lo entregado")
    return problemas


def recorrido_abandonar():
    """Abandonar no es ganar: ni nodo, ni moneda, ni derrota completada."""
    problemas = []
    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)
    nodo = estado["nodo"]
    perfil_antes = campana.cargar_perfil()

    r = Resultado(False, 0, 0, (0, 0))
    r.abandonado = True
    campana.registrar_resultado(estado, r)

    if estado["nodo"] != nodo:
        problemas.append("abandonar avanzo el nodo")
    if estado.get("derrotas", 0) != 0:
        problemas.append("abandonar conto como derrota completada")
    if campana.cargar_perfil() != perfil_antes:
        problemas.append("abandonar toco el perfil (moneda o duelo)")
    return problemas


def recorrido_compra_y_equipar():
    """Comprar un sobre: cobra una vez, entrega y llega a la coleccion."""
    problemas = []
    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)
    campana.ganar_moneda(1000)

    saldo_antes = campana.moneda()
    ok, nuevas, mejoradas = campana.comprar_sobre(estado)
    if not ok:
        return ["con 1000 de moneda no se pudo comprar un sobre"]
    saldo_despues = campana.moneda()
    if saldo_antes - saldo_despues != campana.PRECIO_SOBRE:
        problemas.append(f"cobro incorrecto: {saldo_antes} -> {saldo_despues} "
                          f"(esperaba -{campana.PRECIO_SOBRE})")
    if not (nuevas or mejoradas):
        problemas.append("el sobre no entrego nada")
    coleccion = campana.coleccion_de()
    for nombre in nuevas + mejoradas:
        if nombre not in coleccion:
            problemas.append(f"{nombre} no llego a la coleccion")

    ok2, _n2, _m2 = campana.comprar_sobre(estado)
    if ok2 and campana.moneda() != saldo_despues - campana.PRECIO_SOBRE:
        problemas.append("la segunda compra no cobro lo mismo")
    return problemas


def recorrido_mejorar():
    """Entrenar una carta debe subirla y reflejarse en el mazo."""
    # Ojo: `estado["cartas"]` se serializa en minusculas ("n","s","e","o");
    # `reglas.LADOS` va en mayusculas. Mezclarlos revienta con KeyError.
    lados = ("n", "s", "e", "o")
    problemas = []
    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)

    def fuerza():
        # La mejora NO toca `estado["cartas"]`: es un delta de campana que vive
        # en `estado["mejoras"]`. Medir la base cruda daria siempre el mismo
        # numero y el test pasaria (o fallaria) por el motivo equivocado.
        return sum(sum(c.valores[l.upper()] for l in lados)
                   for c in campana.cartas_jugador(estado))

    # Snapshot del mazo: `mejorar_carta` sube el lado MAS DEBIL, que no es
    # necesariamente el primero. Hay que comparar el lado que devuelve, no un
    # lado supuesto.
    antes_cartas = [dict(d) for d in estado["cartas"]]
    fuerza_antes = fuerza()
    nombre_antes = estado["cartas"][0]["nombre"]
    lado = campana.mejorar_carta(estado, 0)
    if lado is None:
        return ["mejorar_carta no devolvio ningun lado"]
    antes = antes_cartas[0][lado]
    despues = campana.valor_actual(estado, estado["cartas"][0], lado)
    if despues <= antes and antes < 10:
        problemas.append(f"mejorar no subio el lado {lado}: {antes} -> {despues}")
    if fuerza() <= fuerza_antes:
        problemas.append("la mejora no se refleta en el mazo")
    if estado["cartas"][0]["nombre"] != nombre_antes:
        problemas.append("mejorar cambio la carta por otra")
    return problemas


def recorrido_hasta_final():
    """Campana entera, recompensa por recompensa, hasta el final."""
    problemas = []
    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)
    pasos = 0
    visitados = []
    while not estado.get("completada") and pasos < 40:
        pasos += 1
        nodo = campana.nodo_actual(estado)
        visitados.append(nodo)
        if not campana.recompensas_de(nodo):
            problemas.append(f"el nodo {nodo} no ofrece recompensa")
            break
        campana.registrar_resultado(estado, _resultado(True, 2, 5, (5, 4)))
        campana.entregar_recompensa(estado, "entrenamiento", nodo, idx=0)
    if not estado.get("completada"):
        problemas.append(f"la campana no se completo en {pasos} pasos")
    if len(set(visitados)) != len(visitados):
        problemas.append(f"se repitio un nodo: {visitados}")
    return problemas


RECORRIDOS = [
    ("nuevo jugador", recorrido_nuevo_jugador),
    ("reanudacion", recorrido_reanudacion),
    ("derrota y reintento", recorrido_derrota_y_reintento),
    ("abandonar", recorrido_abandonar),
    ("compra y equipar", recorrido_compra_y_equipar),
    ("mejorar carta", recorrido_mejorar),
    ("hasta el final", recorrido_hasta_final),
]


def main():
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))
    opciones.invalidar()
    print(f"Recorridos integrados G9 (datos en {_tmp.name})")
    print("=" * 58)
    fallos = 0
    for nombre, fn in RECORRIDOS:
        try:
            problemas = fn() or []
        except Exception as exc:  # noqa: BLE001
            import traceback
            problemas = [f"EXCEPCION: {type(exc).__name__}: {exc}",
                         traceback.format_exc(limit=3)]
        if problemas:
            fallos += 1
            print(f"[FALLA] {nombre}")
            for p in problemas:
                print(f"         - {p}")
        else:
            print(f"[ OK  ] {nombre}")
    print("=" * 58)
    print(f"recorridos con problemas: {fallos} de {len(RECORRIDOS)}")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())