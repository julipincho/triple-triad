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
import opciones  # noqa: E402
import pantallas  # noqa: E402
import prologo  # noqa: E402
import tutorial  # noqa: E402
from partida import Juego, partida  # noqa: E402,F401
from paths import dir_datos, log_errores  # noqa: E402
import ui  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402,F401

TEST = "--test" in sys.argv
CHECK = "--check" in sys.argv
FPS = "--fps" in sys.argv

# Donde estaba el jugador cuando algo falla. Se escribe en el crash.log para
# poder saber que pantalla Rompio sin reproducing el fallo.
_CONTEXTO = ["menú principal"]

# Campanas cuyo resumen de reanudacion ya se mostro en esta ejecucion. Evita
# repetir el cartel cada vez que se vuelve al menu y se pulsa CONTINUAR.
_RESUMEN_VISTO = set()


def comprobar_recursos():
    """`main.py --check`: verifica assets y datos, util en el exe empaquetado."""
    import diagnostico

    print(diagnostico.informe())
    return 0 if not diagnostico.verificar_recursos() else 1


async def _duelo_rapido(screen, clock):
    """Duelo con mazos prestados, independiente de la colección y campaña."""
    _CONTEXTO[0] = "duelo rápido: eligiendo tu mazo"
    faccion = await pantallas.elegir_faccion(screen, clock, modo="rapida")
    if faccion is None:
        _CONTEXTO[0] = "menú principal"
        return
    _CONTEXTO[0] = "duelo rápido: eligiendo rival"
    rival = await pantallas.elegir_faccion(screen, clock, modo="rapida_rival")
    if rival is None:
        _CONTEXTO[0] = "menú principal"
        return
    import mazos_rapidos

    mano_u = random.sample(mazos_rapidos.mazo(faccion), 5)
    info = dict(campana.DUELISTAS[rival])
    info.update({"bando": rival, "nombre_faccion": facciones.nombre(rival),
                 "nombre_jugador": campana.nombre_guardado() or "Tú",
                 "dificultad": 1, "titulo": "Duelo rapido", "escena": "campamento",
                 "previa": [], "tipo": "rapida", "nodo": "rapida"})
    audio.musica(audio.musica_de_faccion(rival))
    _CONTEXTO[0] = f"duelo rápido contra {facciones.nombre(rival)}"
    juego = Juego(faccion, bando_rival=rival,
                  mano_u_inicial=mano_u,
                  mano_c_inicial=random.sample(mazos_rapidos.mazo(rival), 5),
                  info=info, dificultad=1)
    resultado = await partida(screen, clock, juego)
    if resultado.abandonado:
        return
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
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_pre_duelo(),
        musica=prologo.MUSICA_TORNEO, permitir_saltar=True)

    _CONTEXTO[0] = "prólogo: tutorial contra Juan Rajoy"
    info = prologo.info_duelo_prologo()
    while True:
        # Este bucle NO necesita tick propio: cada vuelta delega el frame en
        # `partida.partida(...)`, que ya llama a clock.tick(ui.LIMIT_FPS).
        juego = Juego("humano", bando_rival=info["bando"],
                      mano_u_inicial=prologo.mazo_tutorial(),
                      mano_c_inicial=prologo.mazo_rival_rajoy(),
                      info=info, dificultad=0)
        resultado = await partida(screen, clock, juego)
        if resultado.victoria:
            break
        
        # Castigo riguroso por perder el tutorial: si no clasifica, no puede avanzar.
        # El modal se dibuja sobre el salon del torneo, no sobre el duelo congelado.
        def _salon(scr, dt):
            scr.blit(ui.REC.fondo_pantalla("assets/fondos/salon.png"), (0, 0))
            scr.blit(ui.REC.capa_oscurita((6, 7, 14, 170)), (0, 0))

        reintentar = await pantallas.confirmar(
            screen, clock, "EL TORNEO SE ESCAPA",
            "No has logrado ganar la clasificatoria contra Juan Rajoy. "
            "El torneo no te deja avanzar sin clasificar.",
            aceptar="REINTENTAR", fondo=_salon,
        )
        if not reintentar:
            return None # Aborta prólogo y vuelve al menú

    _CONTEXTO[0] = "prólogo: la carta del Umbral"
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_post_duelo() + prologo.escenas_carta_umbral(),
        musica=prologo.MUSICA_UMBRAL)
    # El apagón es un golpe puntual, no un bucle: es lo único del prólogo que no
    # se repite, por eso lleva pista corta y propia y se pide sin bucle.
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_transporte(),
        musica=prologo.MUSICA_APAGON, bucle=False)

    _CONTEXTO[0] = "prólogo: despertar en el bosque"
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_despertar(),
        musica=prologo.MUSICA_BOSQUE)
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_encuentro_hostil(),
        musica=prologo.MUSICA_BOSQUE)
    _CONTEXTO[0] = "prólogo: Nara explica la situación"
    await cinematicas.reproducir(
        screen, clock, prologo.escenas_nara() + prologo.escenas_explicacion()
        + prologo.escenas_cierre(),
        musica=prologo.MUSICA_CAMPAMENTO, permitir_saltar=False)
    return resultado


async def _nueva_campana(screen, clock):
    """Nombre, prologo, faccion, mazo, y entra en la campana."""
    # El nombre va ANTES del prologo: el prologo es una pelicula para un
    # protagonista anonimo, y meter un teclado en mitad de una escena
    # cinematografica la arruina. ESC deja el nombre como estaba.
    _CONTEXTO[0] = "nombre del duelista"
    # `nombre_guardado` y no `nombre_jugador`: este ultimo devuelve "el
    # duelista" cuando no hay nombre, y precargaria eso en el campo. Con solo
    # pulsar ENTER se guardaria como nombre propio y `tiene_nombre()` mintiria.
    nombre = await pantallas.pedir_nombre(
        screen, clock, inicial=campana.nombre_guardado())
    if nombre is not None and nombre != campana.nombre_guardado():
        campana.establecer_nombre(nombre)
    res = await _prologo(screen, clock)
    if res is None:
        _CONTEXTO[0] = "menú principal"
        return
    faccion = await pantallas.elegir_faccion(screen, clock)
    if faccion is None:
        return
    estado = campana.nueva_campana(faccion)
    campana.marcar_prologo_visto(estado)
    campana.asegurar_coleccion(faccion)
    mazo = await pantallas.armar_mazo(screen, clock, faccion, nuevo=True)
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
    await pantallas.cartel(screen, clock,
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
    if resultado.abandonado:
        return resultado
    if resultado.victoria:
        await pantallas.cartel(screen, clock, "CAMPANA SECRETA COMPLETA",
                              rival["dialogo"]["win"][1])
    else:
        await pantallas.cartel(screen, clock, "TODAVIA NO",
                              rival["dialogo"]["lose"][0])
    return resultado


async def _mini_campana(screen, clock):
    """Mini campana de 3 duelos para una faccion nueva. Solo vive en sesion."""
    _CONTEXTO[0] = "mini campaña: eligiendo facción"
    faccion = await pantallas.elegir_faccion(
        screen, clock,
        facciones_disponibles=["elfo_nocturno", "hombre_pantera", "hombre_lagarto"], modo="mini")
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
        if resultado.abandonado:
            return
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


async def _final_campana(screen, clock, estado):
    await pantallas.epilogo(screen, clock, estado)
    await _ganar_fragmento(screen, clock, estado["faccion"])
    estado.pop("final_pendiente", None)
    campana.guardar(estado)


async def _campana(screen, clock, estado, nuevo=False):
    """Bucle de campana: mapa -> duelo -> recompensa -> encuentro -> final."""
    campana.asegurar_coleccion(estado["faccion"])
    # Los fondos tienen 24 variantes y se elige una por escena con la semilla de
    # la partida: la misma semilla da siempre los mismos fondos (el jugador no
    # pierde la orientacion porque un sitio cambie de aspecto al entrar y salir)
    # y otra semilla da otra combinacion. Se fija aqui, y no en cada dibujo,
    # para no barajar por frame; y aqui, y no en `_nueva_campana`, porque esta
    # funcion es la unica por la que pasan TANTO la partida nueva como la
    # reanudada desde el menu.
    ui.fijar_variantes(estado.get("semilla", 0))
    _CONTEXTO[0] = (
        f"campaña {facciones.nombre(estado['faccion'])}: "
        f"nodo {campana.nodo_actual(estado)}"
    )
    if nuevo:
        escenas, musica = cinematicas.apertura(estado["faccion"])
        audio.musica(musica)
        _CONTEXTO[0] = f"cinemática de apertura {estado['faccion']}"
        await cinematicas.reproducir(screen, clock, escenas, musica=musica,
                                     clave=f"apertura_{estado['faccion']}")

    while True:
        await asyncio.sleep(0)
        if estado.get("completada"):
            await _final_campana(screen, clock, estado)
            return
        pendiente = estado.get("recompensa_pendiente")
        if pendiente:
            clave = await pantallas.recompensa(screen, clock, estado, pendiente)
            await pantallas.aplicar_recompensa(screen, clock, estado, clave, pendiente)
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
        # antes del duelo del trono, Nara deja de ser guia y se queda. Va antes
        # del cartel de nodo para que sea lo ultimo que pasa antes de pelear.
        # Se marca en la partida: reintentar el trono no repite la confesion.
        if info["nodo"] == "trono" and not estado.get("amistad_vista"):
            _CONTEXTO[0] = "campaña: Nara se queda"
            await cinematicas.reproducir(
                screen, clock, narrativa.escena_amistad(),
                musica=audio.musica_de_faccion(estado["faccion"]),
                permitir_saltar=False)
            estado["amistad_vista"] = True
            campana.guardar(estado)
        # cartel de escenario antes del duelo
        escenas, musica = cinematicas.escenas_nodo(info)
        audio.musica(musica)
        _CONTEXTO[0] = (
            f"cartel de duelo {info['nodo']} contra {info['nombre_faccion']}"
        )
        await cinematicas.reproducir(screen, clock, escenas, musica=musica,
                                     permitir_saltar=True,
                                     clave=f"nodo_{estado['faccion']}_{info['nodo']}")

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

        if resultado.abandonado:
            campana.guardar(estado)
            return
        campana.registrar_resultado(estado, resultado)
        if resultado.victoria:
            # escena posterior: consecuencia y avance del misterio
            info = campana.info_duelo(estado, info["nodo"])
            _CONTEXTO[0] = f"escena posterior {info['nodo']}"
            await cinematicas.reproducir(
                screen, clock, cinematicas.escenas_posterior(info, True),
                musica=musica, permitir_saltar=True,
                clave=f"posterior_{estado['faccion']}_{info['nodo']}")
            if estado.get("completada"):
                campana.guardar(estado)
                await _final_campana(screen, clock, estado)
                return
            # recompensa
            clave = await pantallas.recompensa(screen, clock, estado, info["nodo"])
            await pantallas.aplicar_recompensa(screen, clock, estado, clave, info["nodo"])
            # encuentro narrativo antes del siguiente duelo
            if random.random() < 0.65:
                await pantallas.encuentro(screen, clock, estado, info["nodo"])
        else:
            # escena posterior de derrota: la derrota tambien cuenta
            info = campana.info_duelo(estado, info["nodo"])
            _CONTEXTO[0] = f"escena posterior {info['nodo']} (derrota)"
            await cinematicas.reproducir(
                screen, clock, cinematicas.escenas_posterior(info, False),
                musica=musica, permitir_saltar=True,
                clave=f"posterior_derrota_{estado['faccion']}_{info['nodo']}")
            accion = await pantallas.derrota(screen, clock, estado)
            if accion == "salir":
                return


def _archivar_partida():
    """Copia `campana.json` y `perfil.json` antes de empezar de cero.

    Empezar una campana nueva sobrescribe el guardado, asi que antes queda una
    copia con fecha. Es lo unico que separa "probaste otra faccion" de "te
    comiste la partida de la tarde": el jugador decide si quiere la vuelta, pero
    el archivo no desaparece nunca.
    """
    import shutil
    import time as _t

    from paths import archivo

    sello = _t.strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(dir_datos(), "_partida_archivada_%s" % sello)
    try:
        os.makedirs(destino, exist_ok=True)
        copiados = []
        for nombre in ("campana.json", "perfil.json"):
            origen = archivo(nombre)
            if os.path.exists(origen):
                shutil.copy2(origen, os.path.join(destino, nombre))
                copiados.append(nombre)
        print("partida archivada en %s (%s)" % (destino, ", ".join(copiados)))
    except OSError as exc:  # noqa: BLE001 - archivar es una red, no un paso
        print("no se pudo archivar la partida: %s" % exc)


def _aplicar_ajustes(pantalla, ajustes):
    """Aplica los cambios de pantalla y audio devueltos por la pantalla de ajustes."""
    if "sfx" in ajustes:
        audio.volumen_sfx(ajustes["sfx"])
    if "musica" in ajustes:
        audio.volumen_musica(ajustes["musica"])
    if "fullscreen" in ajustes:
        # Se reaplica el MODO, no solo los flags: asi se mantiene el escalado
        # y el juego sigue ocupando 1280x800 logicos en cualquier pantalla.
        pantalla = ui.aplicar_escalado({"completa": ajustes["fullscreen"]})
    return pantalla


async def main():
    if sys.platform == "emscripten":
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
    pygame.init()
    audio.iniciar()
    # El modo lectura cambia la escala global de tipografia: se aplica antes
    # de construir ninguna pantalla.
    ui.fijar_escala_texto(1.25 if opciones.texto_grande() else 1.0)
    # Las preferencias de audio y pantalla sobreviven al reinicio: se aplican
    # al arrancar, no solo mientras la pantalla de Ajustes esta abierta.
    audio.volumen_musica(opciones.volumen_musica())
    audio.volumen_sfx(opciones.volumen_efectos())
    # Pantalla: 1280x800 LOGICOS, ventana redimensionable y escalada. El juego
    # se adapta a la resolucion del monitor y pygame traduce las coordenadas
    # del raton a la superficie logica, asi que el codigo de dibujo no cambia.
    ui.activar_escalado()
    pantalla = ui.aplicar_escalado({"completa": opciones.pantalla_completa()})
    pygame.display.set_caption("Cartones y Mazmorras")
    if sys.platform == "emscripten":
        import web_diagnostico
        web_diagnostico.activar(contexto)
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
        # Aviso de partida dañada: se comprueba UNA vez al entrar al menu, no
        # en cada vuelta. Sin esto, un guardado ilegible hacia que el menu
        # pareciese el de una partida nueva y nadie se enteraba de la perdida.
        aviso_danada = campana.aviso_partida_danada()
        if aviso_danada:
            _CONTEXTO[0] = "aviso: partida dañada"
            await pantallas.cartel(pantalla, reloj, "PARTIDA DANNADA", aviso_danada)
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
                # Empezar de cero PISA la partida en curso. Se avisa y se
                # archiva antes: el jugador decide, y el respaldo queda por si
                # se arrepiente.
                if campana.puede_continuar(estado):
                    ok = await pantallas.confirmar(
                        pantalla, reloj,
                        "EMPEZAR DE CERO",
                        "Hay una campana en curso (%s - %s). Empezar de cero la "
                        "borra y tenes que elegir faccion otra vez. Se guarda "
                        "una copia antes."
                        % (facciones.nombre(estado["faccion"]),
                           campana.nodo(campana.nodo_actual(estado))["titulo"]),
                        aceptar="EMPEZAR DE CERO")
                    if not ok:
                        continue
                    _archivar_partida()
                await _nueva_campana(pantalla, reloj)
            elif accion == "campana" and campana.puede_continuar(estado):
                # Reanudar sin contexto desorientaba: un cartel corto antes del
                # mapa recuerda donde se dejo la partida y que toca. Una vez
                # por ejecucion y campana, no cada vez que se vuelve al menu.
                clave = (estado.get("faccion"), estado.get("semilla"))
                if clave not in _RESUMEN_VISTO:
                    _RESUMEN_VISTO.add(clave)
                    _CONTEXTO[0] = "resumen de reanudación"
                    await pantallas.cartel(pantalla, reloj, "RETOMAS LA CAMPANA",
                                           campana.resumen_campana(estado))
                await _campana(pantalla, reloj, estado)
            elif accion == "coleccion":
                await pantallas.coleccion(pantalla, reloj, estado)
            elif accion == "diario":
                await pantallas.diario_dialogos(pantalla, reloj, estado)
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
