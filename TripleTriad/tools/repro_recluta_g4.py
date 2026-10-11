"""Reproduccion G4 por la RUTA REAL del jugador: recompensa 'recluta' -> draft ->
draft_reemplazo, sin validacion de mazo.

Uso:  python tools/repro_recluta_g4.py
"""

import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_tmp = tempfile.TemporaryDirectory(prefix="tt_repro_recluta_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

import campana  # noqa: E402
from reglas import Carta, rareza  # noqa: E402


def validar(estado):
    return campana.validar_mazo(estado["cartas"], campana.coleccion_de())


def prueba_draft_puede_ofrecer_carta_del_mazo():
    print("=" * 70)
    print("A) Puede el draft ofrecer una carta que YA esta en el mazo?")
    print("=" * 70)
    finding = 0
    for intento in range(200):
        estado = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        campana.guardar(estado)
        en_mazo = {d["nombre"] for d in estado["cartas"]}
        ofertas = campana.draft_aleatorio(estado, 3)
        solape = [o.nombre for o in ofertas if o.nombre in en_mazo]
        if solape:
            print(f"  intento {intento}: el draft ofrecio {solape} "
                  f"que ya estaba en el mazo")
            finding += 1
            if finding >= 3:
                break
    print(f"  ofertas que pisaban el mazo en {finding} de 200 intentos")
    return finding > 0


def prueba_recluta_crea_duplicado():
    print()
    print("=" * 70)
    print("B) Recluta: sustituir por una carta que ya tienes dentro")
    print("=" * 70)
    import mazos

    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)

    # Carta A ya esta en el mazo (indice 0). Se ofrece otra carta B, pero el
    # jugador sustituye por... A. draft_reemplazo no lo impide.
    repetida = Carta.desde_dict(estado["cartas"][0])
    otra = campana.draft_aleatorio(estado, 1)[0]
    print(f"  carta ya en el mazo (indice 0): {repetida.nombre}")
    print(f"  la recompensa 'recluta' ofrece: {otra.nombre}")

    # El jugador elige sustituir la carta que NO es (por ejemplo la 5).
    campana.draft_reemplazo(estado, repetida.copia(), 5)
    nombres = [d["nombre"] for d in estado["cartas"]]
    ok, motivo = validar(estado)
    print(f"  mazo tras draft_reemplazo: {nombres}")
    print(f"  validacion -> {'OK' if ok else 'MAL: ' + motivo}")
    return ok


def prueba_encuentro_robo():
    print()
    print("=" * 70)
    print("C) Encuentro 'robo': anadir_carta con mazo lleno")
    print("=" * 70)
    import mazos

    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)
    repetida = Carta.desde_dict(estado["cartas"][0])
    campana.anadir_carta(estado, repetida.copia())
    nombres = [d["nombre"] for d in estado["cartas"]]
    ok, motivo = validar(estado)
    print(f"  robo de una carta ya presente -> {nombres}")
    print(f"  validacion -> {'OK' if ok else 'MAL: ' + motivo}")
    return ok


def prueba_sobre_con_mazo_reducido():
    print()
    print("=" * 70)
    print("D) Sobre con mazo por debajo de 10: el append no mira rarezas")
    print("=" * 70)
    import mazos

    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)
    # Mazo reducido a 6 cartas COMUN, pero REGALADAS antes: una carta que no
    # esta en la coleccion hace el mazo ilegal de partida y el test mediria
    # el fallo equivocado. Hay hueco, y el sobre podria meter una legendaria.
    comunes = [c for c in mazos.TODOS["humano"] if rareza(c)[0] == "COMUN"]
    elegidas = comunes[:6]
    for c in elegidas:
        campana.otorgar_base(c.nombre, c.a_dict())
    estado["cartas"] = [c.a_dict() for c in elegidas]
    campana.guardar(estado)
    for _ in range(6):
        campana.abrir_sobre(estado, cantidad=3)
    r = [rareza(Carta.desde_dict(d))[0] for d in estado["cartas"]]
    ok, motivo = validar(estado)
    print(f"  mazo: n={len(estado['cartas'])} "
          f"LEG={r.count('LEGENDARIA')} RARA={r.count('RARA')} "
          f"COMUN={r.count('COMUN')}")
    print(f"  validacion -> {'OK' if ok else 'MAL: ' + motivo}")
    return ok


if __name__ == "__main__":
    print("Reproduccion G4 por la ruta real de la recompensa 'recluta'")
    print(f"datos aislados en: {_tmp.name}")
    print()
    a = prueba_draft_puede_ofrecer_carta_del_mazo()
    b = prueba_recluta_crea_duplicado()
    c = prueba_encuentro_robo()
    d = prueba_sobre_con_mazo_reducido()
    print()
    print("=" * 70)
    print(f"RESULTADO: draft-pisa-mazo={'SI' if a else 'no'}  "
          f"recluta-duplicado={'pasa' if b else 'FALLA'}  "
          f"robo-duplicado={'pasa' if c else 'FALLA'}  "
          f"sobre-rareza={'pasa' if d else 'FALLA'}")
    print("=" * 70)