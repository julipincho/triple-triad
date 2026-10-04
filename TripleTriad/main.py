"""Triple Triad - El Umbral del Trono.

Punto de entrada. Aqui se enlazan portada, menu, campana y duelos.
El estado de la campana vive en `campana.py` y se guarda en campana.json.
"""

import os
import random
import sys

# Permite ejecutar desde cualquier carpeta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

import audio  # noqa: E402
import campana  # noqa: E402
import cinematicas  # noqa: E402
import facciones  # noqa: E402
import pantallas  # noqa: E402
from partida import Juego, partida  # noqa: E402,F401
from paths import log_errores  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402,F401

TEST = "--test" in sys.argv
CHECK = "--check" in sys.argv

# Donde estaba el jugador cuando algo falla. Se escribe en el crash.log para
# poder saber que pantalla Rompio sin reproducing el fallo.
_CONTEXTO = ["menú principal"]


def comprobar_recursos():
    """`main.py --check`: verifica assets y datos, util en el exe empaquetado."""
    import diagnostico

    print(diagnostico.informe())
    return 0 if not diagnostico.verificar_recursos() else 1


def _duelo_rapido(screen, clock):
    """Partida rapida: faccion contra faccion, sin progresion."""
    _CONTEXTO[0] = "duelo rápido: eligiendo facción"
    faccion = pantallas.elegir_faccion(screen, clock, modo="rapida")
    if faccion is None:
        _CONTEXTO[0] = "menú principal"
        return
    import campana as _c

    rivales = [f for f in facciones.orden_facciones() if f != faccion]
    rival = random.choice(rivales)
    info = dict(_c.DUELISTAS[rival])
    info.update({"bando": rival, "nombre_faccion": facciones.nombre(rival),
                 "dificultad": 1, "titulo": "Duelo rapido", "escena": "campamento",
                 "previa": [], "tipo": "rapida", "nodo": "rapida"})
    audio.musica(audio.musica_de_faccion(rival))
    _CONTEXTO[0] = (
        f"duelo rápido: {facciones.nombre(faccion)} contra "
        f"{facciones.nombre(rival)}"
    )
    juego = Juego(faccion, bando_rival=rival, info=info, dificultad=1)
    resultado = partida(screen, clock, juego)
    campana.registrar_duelo_perfil(bool(resultado), faccion)
    pantallas.cartel(
        screen, clock,
        "VICTORIA" if resultado.victoria else "DERROTA",
        f"Marcador {resultado.marcador[0]} - {resultado.marcador[1]}  -  "
        f"{resultado.capturas} capturas  -  {resultado.jugadas} cartas colocadas",
    )
    _CONTEXTO[0] = "menú principal"


def _nueva_campana(screen, clock):
    """Elige faccion, guarda partida nueva y entra en la cinemática de apertura."""
    faccion = pantallas.elegir_faccion(screen, clock)
    if faccion is None:
        return
    estado = campana.nueva_campana(faccion)
    campana.guardar(estado)
    _campana(screen, clock, estado, nuevo=True)


def _campana(screen, clock, estado, nuevo=False):
    """Bucle de campana: mapa -> duelo -> recompensa -> encuentro -> final."""
    _CONTEXTO[0] = (
        f"campaña {facciones.nombre(estado['faccion'])}: "
        f"nodo {campana.nodo_actual(estado)}"
    )
    if nuevo:
        escenas, musica = cinematicas.apertura(estado["faccion"])
        campana.marcar_cinematica(f"apertura_{estado['faccion']}")
        audio.musica(musica)
        _CONTEXTO[0] = f"cinemática de apertura {estado['faccion']}"
        cinematicas.reproducir(screen, clock, escenas, musica=musica)

    while True:
        if estado.get("completada"):
            pantallas.epilogo(screen, clock, estado)
            return
        accion = pantallas.mapa_campana(screen, clock, estado)
        if accion == "salir":
            campana.guardar(estado)
            return

        # nodo de eleccion: el jugador decide la rama
        if campana.nodo(estado["nodo"])["tipo"] == "eleccion":
            rama = pantallas.elegir_rama(screen, clock, estado)
            if rama is None:
                continue
            campana.elegir_bifurcacion(estado, rama)

        info = campana.info_duelo(estado)
        # cartel de escenario antes del duelo
        escenas, musica = cinematicas.escenas_nodo(info)
        audio.musica(musica)
        _CONTEXTO[0] = (
            f"cartel de duelo {info['nodo']} contra {info['nombre_faccion']}"
        )
        cinematicas.reproducir(screen, clock, escenas, musica=musica,
                               permitir_saltar=True)

        mano = campana.cartas_jugador(estado)
        mazo_c = campana.mazo_rival(estado)
        juego = Juego(estado["faccion"], bando_rival=info["bando"],
                      mano_u_inicial=mano, mano_c_inicial=mazo_c,
                      info=info, en_campana=True, dificultad=info["dificultad"])
        _CONTEXTO[0] = (
            f"duelo de campaña: {facciones.nombre(estado['faccion'])} contra "
            f"{info['nombre']} ({info['nombre_faccion']}) en {info['nodo']}"
        )
        resultado = partida(screen, clock, juego)

        if resultado.victoria:
            campana.registrar_victoria(estado, resultado.capturas)
            campana.registrar_duelo_perfil(True, estado["faccion"], estado["racha"])
            if estado.get("completada"):
                campana.guardar(estado)
                pantallas.epilogo(screen, clock, estado)
                return
            # recompensa
            clave = pantallas.recompensa(screen, clock, estado, info["nodo"])
            pantallas.aplicar_recompensa(screen, clock, estado, clave, info["nodo"])
            # encuentro narrativo antes del siguiente duelo
            if random.random() < 0.65:
                pantallas.encuentro(screen, clock, estado, info["nodo"])
        else:
            campana.registrar_derrota(estado)
            campana.registrar_duelo_perfil(False, estado["faccion"], 0)
            accion = pantallas.derrota(screen, clock, estado)
            if accion == "salir":
                return


def _aplicar_ajustes(pantalla, ajustes):
    """Aplica los cambios de pantalla y audio devueltos por la pantalla de ajustes."""
    if "sfx" in ajustes:
        audio.volumen_sfx(ajustes["sfx"])
    if "musica" in ajustes:
        audio.volumen_musica(ajustes["musica"])
    if "fullscreen" in ajustes:
        flags = pygame.FULLSCREEN if ajustes["fullscreen"] else 0
        pantalla = pygame.display.set_mode((ANCHO, ALTO), flags)
    return pantalla


def main():
    pygame.init()
    audio.iniciar()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Triple Triad - El Umbral del Trono")
    reloj = pygame.time.Clock()

    if TEST:
        # modo prueba: entra directo al duelo y sale solo
        juego = Juego("humano", bando_rival="orco")
        partida(pantalla, reloj, juego, test_mode=True)
        return

    try:
        audio.musica(audio.musica_de_menu())
        pantallas.portada(pantalla, reloj)
        while True:
            estado = campana.cargar()
            accion = pantallas.menu(pantalla, reloj, estado)
            if accion == "salir":
                return
            # de vuelta al menu: musica tranquila (el duelo pone la suya)
            audio.musica(audio.musica_de_menu())
            if accion == "rapida":
                _duelo_rapido(pantalla, reloj)
            elif accion == "nueva":
                _nueva_campana(pantalla, reloj)
            elif accion == "campana" and estado and not estado.get("completada"):
                _campana(pantalla, reloj, estado)
            elif accion == "coleccion":
                pantallas.coleccion(pantalla, reloj, estado)
            elif accion == "ajustes":
                pantalla = _aplicar_ajustes(pantalla, pantallas.ajustes(pantalla, reloj))
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - preferimos mostrarlo a morir
        # Antes esto cerraba la ventana en silencio; ahora se explica que paso.
        import traceback

        traza = traceback.format_exc()
        try:
            pantallas.pantalla_error(pantalla, reloj, exc, traza, contexto())
        except Exception:  # noqa: BLE001 - si ni el error se dibuja, queda el log
            traceback.print_exc()


def contexto():
    """Donde estaba el jugador cuando algo fallo (va al crash.log)."""
    return _CONTEXTO[0]


def marcar(texto):
    _CONTEXTO[0] = texto


if __name__ == "__main__":
    try:
        if CHECK:
            sys.exit(comprobar_recursos())
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback

        ruta = log_errores()
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                traceback.print_exc(file=f)
        except OSError:
            pass
        traceback.print_exc()
        pygame.quit()
        raise