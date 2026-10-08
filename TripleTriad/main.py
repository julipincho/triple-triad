"""Triple Triad - El Umbral del Trono.

Punto de entrada. Aqui se enlazan portada, menu, campana y duelos.
El estado de la campana vive en `campana.py` y se guarda en campana.json.
"""

import os
import random
import sys

# Permite ejecutar desde cualquier carpeta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio  # noqa: E402
import pygame  # noqa: E402

import audio  # noqa: E402
import campana  # noqa: E402
import cinematicas  # noqa: E402
import facciones  # noqa: E402
import fragmentos  # noqa: E402
import narrativa  # noqa: E402
import pantallas  # noqa: E402
import prologo  # noqa: E402
import tutorial  # noqa: E402
from partida import Juego, partida  # noqa: E402,F401
from paths import log_errores  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402,F401

TEST = "--test" in sys.argv
CHECK = "--check" in sys.argv
FPS = "--fps" in sys.argv

# Donde estaba el jugador cuando algo falla. Se escribe en el crash.log para
# poder saber que pantalla Rompio sin reproducing el fallo.
_CONTEXTO = ["menú principal"]


def comprobar_recursos():
    """`main.py --check`: verifica assets y datos, util en el exe empaquetado."""
    import diagnostico

    print(diagnostico.informe())
    return 0 if not diagnostico.verificar_recursos() else 1


async def _duelo_rapido(screen, clock):
    """Partida rapida con tu mazo global contra la faccion que elijas."""
    _CONTEXTO[0] = "duelo rápido: eligiendo rival"
    rival = await pantallas.elegir_faccion(screen, clock, modo="rapida")
    if rival is None:
        _CONTEXTO[0] = "menú principal"
        return
    import campana as _c
    import mazos as _m

    campana.asegurar_mazo_global()
    coleccion = campana.coleccion_de()
    nombres = campana.mazo_global()
    ok, _motivo = campana.validar_mazo(
        [dict(coleccion[n]) for n in nombres if n in coleccion], set(coleccion))
    if not ok:
        mazo = await pantallas.armar_mazo(screen, clock)
        if mazo is None:
            _CONTEXTO[0] = "menú principal"
            return
        nombres = [d["nombre"] for d in mazo]
        coleccion = campana.coleccion_de()
    from reglas import Carta

    mano_u = random.sample(
        [Carta.desde_dict(dict(coleccion[n])) for n in nombres if n in coleccion], 5)
    info = dict(_c.DUELISTAS[rival])
    info.update({"bando": rival, "nombre_faccion": facciones.nombre(rival),
                 "dificultad": 1, "titulo": "Duelo rapido", "escena": "campamento",
                 "previa": [], "tipo": "rapida", "nodo": "rapida"})
    audio.musica(audio.musica_de_faccion(rival))
    _CONTEXTO[0] = f"duelo rápido contra {facciones.nombre(rival)}"
    juego = Juego("humano", bando_rival=rival,
                  mano_u_inicial=mano_u,
                  mano_c_inicial=random.sample([c.copia() for c in _m.TODOS[rival]], 5),
                  info=info, dificultad=1)
    resultado = await partida(screen, clock, juego)
    campana.registrar_duelo_perfil(bool(resultado), None)
    await pantallas.cartel(
        screen, clock,
        "VICTORIA" if resultado.victoria else "DERROTA",
        f"Marcador {resultado.marcador[0]} - {resultado.marcador[1]}  -  "
        f"{resultado.capturas} capturas  -  {resultado.jugadas} cartas colocadas",
    )
    _CONTEXTO[0] = "menú principal"


async def _prologo(screen, clock):
    """Prologo del mundo real: torneo, tutorial, Umbral, despertar y Nara.

    Va antes de elegir faccion (ver la cronologia de la biblia). El tutorial es
    un duelo real contra Juan con las 5 legendarias: el jugador aprende las
    mecánicas jugando, no leyendo. Al cruzar al mundo fantastic el mazo pasa
    a ser el inicial, deliberadamente mas debil.
    """
    _CONTEXTO[0] = "prólogo: sala del torneo"
    audio.musica(prologo.MUSICA_MUNDO_REAL)
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_pre_duelo(),
        musica=prologo.MUSICA_MUNDO_REAL, permitir_saltar=True)

    _CONTEXTO[0] = "prólogo: tutorial contra Juan Rajoy"
    info = prologo.info_duelo_prologo()
    juego = Juego("humano", bando_rival=info["bando"],
                  mano_u_inicial=prologo.mazo_tutorial(),
                  mano_c_inicial=prologo.mazo_rival_rajoy(),
                  info=info, dificultad=0)
    resultado = await partida(screen, clock, juego)

    _CONTEXTO[0] = "prólogo: la carta del Umbral"
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_post_duelo() + prologo.escenas_carta_umbral(),
        musica=prologo.MUSICA_MUNDO_REAL)
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_transporte(),
        musica=prologo.MUSICA_MUNDO_REAL)

    _CONTEXTO[0] = "prólogo: despertar en el bosque"
    musica_fantasia = audio.musica_de_faccion("goblin")
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_despertar(),
        musica=musica_fantasia)
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_encuentro_hostil(),
        musica=musica_fantasia)
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_nara() + prologo.escenas_cierre(),
        musica=musica_fantasia, permitir_saltar=False)
    return resultado


async def _nueva_campana(screen, clock):
    """Prologo, elige faccion, guarda partida nueva y entra en la campana."""
    await _prologo(screen, clock)
    faccion = await pantallas.elegir_faccion(screen, clock)
    if faccion is None:
        return
    estado = campana.nueva_campana(faccion)
    campana.marcar_prologo_visto(estado)
    campana.asegurar_coleccion(faccion)
    campana.asegurar_mazo_global()
    mazo = await pantallas.armar_mazo(screen, clock, faccion)
    if mazo is None:
        _CONTEXTO[0] = "menú principal"
        return
    estado["cartas"] = mazo
    campana.guardar(estado)
    await _campana(screen, clock, estado, nuevo=True)


async def _ganar_fragmento(screen, clock, faccion):
    """Una faccion completada aporta un fragmento de la verdad.

    Es el NG+: la primera vez no hace falta entender el misterio. Cada faccion
    responde una pregunta distinta, y con las diez aparece El Cartografo, que
    nunca estuvo entre las 250 cartas.
    """
    _CONTEXTO[0] = "fragmento de verdad: " + facciones.nombre(faccion)
    nuevo, datos = campana.registrar_fragmento(faccion)
    if not nuevo:
        return
    encontrados, total = campana.progreso_fragmentos()
    await cartel(screen, clock,
                 "FRAGMENTO DE LA VERDAD  %d/%d" % (encontrados, total),
                 datos["pregunta"] + chr(10) + chr(10) + "- " + datos["texto"])
    if campana.secreto_desbloqueado():
        await cinematicas.reproducir(
            screen, clock,
            fragmentos.escena_desbloqueo(campana.fragmentos_obtenidos()),
            musica=audio.musica_de_faccion("dragon"))


async def _campana_secreta(screen, clock, faccion):
    """La campana que no es contra una faccion: contra el que escribio las cartas."""
    _CONTEXTO[0] = "campana secreta: El Maestro de la Mesa"
    rival = fragmentos.CARTOGRAFO
    await cinematicas.reproducir(
        screen, clock,
        fragmentos.escena_desbloqueo(campana.fragmentos_obtenidos()),
        musica=audio.musica_de_faccion("dragon"))
    await cinematicas.reproducir(
        screen, clock,
        [cinematicas.esc(linea, hablante="El Maestro de la Mesa", fondo="umbral")
         for linea in rival["dialogo"]["pre"]],
        musica=audio.musica_de_faccion("dragon"))
    info = {
        "nodo": "trono",
        "titulo": rival["nombre"],
        "escena": "umbral",
        "previa": [],
        "tipo": "secreto",
        "dificultad": 3,
        "bando": faccion,
        "nombre_faccion": "Nadie",
        "nombre": rival["nombre"],
        "titulo_duelo": rival["titulo"],
        "entrada": rival["dialogo"]["pre"][0],
        "captura_player": "",
        "captura_cpu": "",
        "win": rival["dialogo"]["win"][0],
        "lose": rival["dialogo"]["lose"][0],
        "rol": rival["rol"],
        "faccion_jugador": faccion,
    }
    juego = Juego(faccion, bando_rival=faccion,
                  mano_c_inicial=campana.mazo_rival_secreto(),
                  info=info, dificultad=3)
    resultado = await partida(screen, clock, juego)
    if resultado.victoria:
        await cartel(screen, clock, "CAMPANA SECRETA COMPLETA",
                     rival["dialogo"]["win"][1])
    else:
        await cartel(screen, clock, "TODAVIA NO", rival["dialogo"]["lose"][0])
    return resultado


async def _mini_campana(screen, clock):
    """Mini campana de 3 duelos para una faccion nueva. Solo vive en sesion."""
    _CONTEXTO[0] = "mini campaña: eligiendo facción"
    faccion = await pantallas.elegir_faccion(
        screen, clock,
        facciones_disponibles=["elfo_nocturno", "hombre_pantera", "hombre_lagarto"])
    if faccion is None:
        _CONTEXTO[0] = "menú principal"
        return
    estado = campana.nueva_mini_campana(faccion)
    _CONTEXTO[0] = f"mini campaña {facciones.nombre(faccion)}"
    while True:
        await asyncio.sleep(0)
        if estado.get("completada"):
            return
        if await pantallas.mapa_mini(screen, clock, estado) == "salir":
            return
        info = campana.info_duelo(estado)
        escenas, musica = cinematicas.escenas_nodo(info)
        audio.musica(musica)
        _CONTEXTO[0] = f"mini duelo {info['nodo']} contra {info['nombre_faccion']}"
        await cinematicas.reproducir(screen, clock, escenas, musica=musica,
                                     permitir_saltar=True)
        juego = Juego(estado["faccion"], bando_rival=info["bando"],
                      mano_u_inicial=campana.cartas_duelo(estado, info["nodo"]),
                      mano_c_inicial=campana.mazo_rival(estado),
                      info=info, en_campana=True, dificultad=info["dificultad"])
        resultado = await partida(screen, clock, juego)
        if resultado.victoria:
            campana.registrar_victoria(estado, resultado.capturas)
            campana.registrar_duelo_perfil(True, estado["faccion"], estado["racha"])
            if estado.get("completada"):
                datos = campana.MINI_FINALES[estado["faccion"]]
                nuevo = campana.registrar_mini_final(estado["faccion"])
                escenas, musica = cinematicas.escenas_final(
                    datos["titulo"], datos["lineas"], estado["faccion"])
                audio.musica(musica)
                await cinematicas.reproducir(screen, clock, escenas, musica=musica)
                await pantallas.cartel(
                    screen, clock,
                    "MINI CAMPANA COMPLETA" + (" - FINAL NUEVO" if nuevo else ""),
                    datos["titulo"])
                await _ganar_fragmento(screen, clock, estado["faccion"])
                _CONTEXTO[0] = "menú principal"
                return
            clave = await pantallas.recompensa(screen, clock, estado, info["nodo"])
            await pantallas.aplicar_recompensa(screen, clock, estado, clave, info["nodo"])
        else:
            campana.registrar_derrota(estado)
            campana.registrar_duelo_perfil(False, estado["faccion"], 0)
            if await pantallas.derrota(screen, clock, estado) == "salir":
                _CONTEXTO[0] = "menú principal"
                return


async def _campana(screen, clock, estado, nuevo=False):
    """Bucle de campana: mapa -> duelo -> recompensa -> encuentro -> final."""
    campana.asegurar_coleccion(estado["faccion"])
    _CONTEXTO[0] = (
        f"campaña {facciones.nombre(estado['faccion'])}: "
        f"nodo {campana.nodo_actual(estado)}"
    )
    if nuevo:
        escenas, musica = cinematicas.apertura(estado["faccion"])
        campana.marcar_cinematica(f"apertura_{estado['faccion']}")
        audio.musica(musica)
        _CONTEXTO[0] = f"cinemática de apertura {estado['faccion']}"
        await cinematicas.reproducir(screen, clock, escenas, musica=musica)

    while True:
        await asyncio.sleep(0)
        if estado.get("completada"):
            await pantallas.epilogo(screen, clock, estado)
            return
        accion = await pantallas.mapa_campana(screen, clock, estado)
        if accion == "salir":
            campana.guardar(estado)
            return

        # nodo de eleccion: el jugador decide la rama
        if campana.nodo(estado["nodo"])["tipo"] == "eleccion":
            rama = await pantallas.elegir_rama(screen, clock, estado)
            if rama is None:
                continue
            campana.elegir_bifurcacion(estado, rama)

        info = campana.info_duelo(estado)
        # decision moral del nodo, si la hay (se registra y mueve el estado)
        decision = narrativa.decision_de(campana.nodo_actual(estado))
        if decision and decision["id"] not in estado.get("decisiones", []):
            await pantallas.decision_narrativa(screen, clock, estado, decision)
            info = campana.info_duelo(estado)
        # cartel de escenario antes del duelo
        escenas, musica = cinematicas.escenas_nodo(info)
        audio.musica(musica)
        _CONTEXTO[0] = (
            f"cartel de duelo {info['nodo']} contra {info['nombre_faccion']}"
        )
        await cinematicas.reproducir(screen, clock, escenas, musica=musica,
                                     permitir_saltar=True)

        mano = campana.cartas_duelo(estado, info["nodo"])
        mazo_c = campana.mazo_rival(estado)
        juego = Juego(estado["faccion"], bando_rival=info["bando"],
                      mano_u_inicial=mano, mano_c_inicial=mazo_c,
                      info=info, en_campana=True, dificultad=info["dificultad"])
        _CONTEXTO[0] = (
            f"duelo de campaña: {facciones.nombre(estado['faccion'])} contra "
            f"{info['nombre']} ({info['nombre_faccion']}) en {info['nodo']}"
        )
        resultado = await partida(screen, clock, juego)

        if resultado.victoria:
            campana.registrar_victoria(estado, resultado.capturas)
            campana.registrar_duelo_perfil(True, estado["faccion"], estado["racha"])
            campana.premio_duelo(estado, True, resultado.capturas)
            # escena posterior: consecuencia y avance del misterio
            info = campana.info_duelo(estado, info["nodo"])
            _CONTEXTO[0] = f"escena posterior {info['nodo']}"
            await cinematicas.reproducir(
                screen, clock, cinematicas.escenas_posterior(info, True),
                musica=musica, permitir_saltar=True)
            if estado.get("completada"):
                campana.guardar(estado)
                await pantallas.epilogo(screen, clock, estado)
                await _ganar_fragmento(screen, clock, estado["faccion"])
                return
            # recompensa
            clave = await pantallas.recompensa(screen, clock, estado, info["nodo"])
            await pantallas.aplicar_recompensa(screen, clock, estado, clave, info["nodo"])
            # encuentro narrativo antes del siguiente duelo
            if random.random() < 0.65:
                await pantallas.encuentro(screen, clock, estado, info["nodo"])
        else:
            campana.registrar_derrota(estado)
            campana.registrar_duelo_perfil(False, estado["faccion"], 0)
            campana.premio_duelo(estado, False, resultado.capturas)
            # escena posterior de derrota: la derrota tambien cuenta
            info = campana.info_duelo(estado, info["nodo"])
            _CONTEXTO[0] = f"escena posterior {info['nodo']} (derrota)"
            await cinematicas.reproducir(
                screen, clock, cinematicas.escenas_posterior(info, False),
                musica=musica, permitir_saltar=True)
            accion = await pantallas.derrota(screen, clock, estado)
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


async def main():
    pygame.init()
    audio.iniciar()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Triple Triad - El Umbral del Trono")
    reloj = pygame.time.Clock()
    # `--fps` en escritorio, `TT_FPS=1` en la web (no hay argv ahi). Solo para
    # diagnostico: se dibuja encima del juego, no afecta al juego.
    if FPS or os.environ.get("TT_FPS"):
        import depurar

        depurar.activar()

    if TEST:
        # modo prueba: entra directo al duelo y sale solo
        juego = Juego("humano", bando_rival="orco")
        await partida(pantalla, reloj, juego, test_mode=True)
        return

    try:
        audio.musica(audio.musica_de_menu())
        await pantallas.portada(pantalla, reloj)
        if campana.marcar_cinematica("intro"):
            # la intro se ve una sola vez (queda en el perfil) y se puede saltar
            _CONTEXTO[0] = "cinemática de intro"
            escenas, musica = cinematicas.intro()
            audio.musica(musica)
            await cinematicas.reproducir(pantalla, reloj, escenas, musica=musica)
            _CONTEXTO[0] = "menú principal"
        if not campana.tutorial_visto():
            _CONTEXTO[0] = "tutorial: puerta de entrada"
            if await tutorial.puerta_primer_arranque(pantalla, reloj):
                _CONTEXTO[0] = "tutorial"
                await tutorial.tutorial(pantalla, reloj)
            campana.marcar_tutorial(visto=True)
            audio.musica(audio.musica_de_menu())
            _CONTEXTO[0] = "menú principal"
        while True:
            await asyncio.sleep(0)
            estado = campana.cargar()
            accion = await pantallas.menu(pantalla, reloj, estado)
            if accion == "salir":
                return
            # de vuelta al menu: musica tranquila (el duelo pone la suya)
            audio.musica(audio.musica_de_menu())
            if accion == "rapida":
                await _duelo_rapido(pantalla, reloj)
            elif accion == "mini":
                _CONTEXTO[0] = "mini campaña"
                await _mini_campana(pantalla, reloj)
                _CONTEXTO[0] = "menú principal"
            elif accion == "tutorial":
                _CONTEXTO[0] = "tutorial"
                await tutorial.tutorial(pantalla, reloj)
                _CONTEXTO[0] = "menú principal"
            elif accion == "nueva":
                await _nueva_campana(pantalla, reloj)
            elif accion == "campana" and estado and not estado.get("completada"):
                await _campana(pantalla, reloj, estado)
            elif accion == "coleccion":
                await pantallas.coleccion(pantalla, reloj, estado)
            elif accion == "ajustes":
                pantalla = _aplicar_ajustes(pantalla, await pantallas.ajustes(pantalla, reloj))
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - preferimos mostrarlo a morir
        # Antes esto cerraba la ventana en silencio; ahora se explica que paso.
        import traceback

        traza = traceback.format_exc()
        try:
            await pantallas.pantalla_error(pantalla, reloj, exc, traza, contexto())
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
        # pygbag (web) necesita el bucle en asyncio con `await asyncio.sleep(0)`
        asyncio.run(main())
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