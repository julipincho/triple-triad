"""Diagnostico: comprueba que el juego tiene todo lo que necesita.

    python main.py --check      (tambien dentro del .exe empaquetado)

Devuelve una lista de problemas (vacia = todo correcto). Lo usan tanto el
ejecutable como los tests, para que no haya dos listas que mantener.
"""

import os

import facciones
import mazos
from cartas import _slug
from paths import recurso

FONDOS = ["ceniza", "camino", "aldea", "ruinas", "fortaleza", "trono", "campamento", "asalto"]

SONIDOS = [
    "place.wav", "capture.wav", "chain.wav", "win.wav", "lose.wav",
    "menu.wav", "menu_move.wav", "menu_ok.wav", "menu_back.wav",
    "card.wav", "drag.wav", "invalid.wav", "cinema.wav", "reward.wav", "boss.wav",
]


def _falta(ruta):
    return None if os.path.exists(recurso(ruta)) else ruta


def verificar_recursos():
    """Lista de rutas que faltan o no se pueden leer."""
    problemas = []

    for bando, cartas in mazos.TODOS.items():
        for carta in cartas:
            falta = _falta(os.path.join("cartas", f"{bando}_{_slug(carta.nombre)}.png"))
            if falta:
                problemas.append(f"falta el arte de {carta.nombre} ({falta})")

    for f in facciones.orden_facciones():
        falta = _falta(os.path.join("assets", f"avatar_{f}.png"))
        if falta:
            problemas.append(f"falta el avatar de {facciones.nombre(f)} ({falta})")

    for fondo in FONDOS:
        falta = _falta(os.path.join("assets", "fondos", f"{fondo}.png"))
        if falta:
            problemas.append(f"falta el fondo de cinemática '{fondo}' ({falta})")

    for sonido in SONIDOS:
        falta = _falta(os.path.join("assets", sonido))
        if falta:
            problemas.append(f"falta el efecto de sonido {sonido}")

    for f in facciones.orden_facciones():
        falta = _falta(os.path.join("assets", "musica", f"musica_{f}.wav"))
        if falta:
            problemas.append(f"falta la música de {facciones.nombre(f)} ({falta})")

    for basico in (os.path.join("assets", "fondo.png"),
                   os.path.join("assets", "PressStart2P.ttf")):
        falta = _falta(basico)
        if falta:
            problemas.append(f"falta el recurso base {falta}")

    return problemas


def informe():
    """Texto listo para imprimir con el resultado del chequeo."""
    import mazos as _m

    problemas = verificar_recursos()
    lineas = [
        f"Facciones: {len(_m.TODOS)}",
        f"Cartas: {sum(len(c) for c in _m.TODOS.values())}",
        f"Fondos de cinemática: {len(FONDOS)}",
        "Efectos de sonido: " + str(len(SONIDOS)),
        f"Pistas de música: {len(_m.TODOS)}",
    ]
    if problemas:
        lineas.append("")
        lineas.append(f"PROBLEMAS ({len(problemas)}):")
        lineas += [f"  - {p}" for p in problemas]
    else:
        lineas.append("")
        lineas.append("Todo correcto: no falta ningun recurso.")
    return "\n".join(lineas)