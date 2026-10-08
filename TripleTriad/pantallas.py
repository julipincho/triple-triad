"""Pantallas: portada, menu, seleccion de faccion, mapa de campana,
recompensas, encuentros, coleccion, ajustes y epilogo.

Cada pantalla es una funcion que dibuja y atiende eventos hasta devolver
un valor. Todas usan la misma paleta y los mismos botones de `ui`.
"""

import os
import time

import pygame

import audio
import campana
import cartas as crt
import compendio
import cinematicas
import encuentros
import facciones
import finales
import mazos
from reglas import LADOS, rareza, val
from ui import (
    ALTO,
    ANCHO,
    BORDE,
    DORADO,
    FondoAnimado,
    PANEL,
    REC,
    ROJO,
    TEXTO,
    TEXTO_ON,
    TEXTO_TENUE,
    VERDE,
    Boton,
    LIMIT_FPS,
    ancho_texto,
    con_alpha,
    dibujar_tooltips,
    envolver,
    fundido_entrada,
    panel,
    parrafo,
    resplandor,
    texto,
    tooltip,
)

import asyncio

VERSION_JUEGO = "1.0"


class Fondo:
    """Fondo animado comun con un tinte de faccion."""

    def __init__(self, faccion="dragon"):
        self.faccion = faccion
        # FondoAnimado escala y cachea el fondo: no reserva memoria por frame
        self.animado = FondoAnimado(
            crt.REC.imagen("assets/fondo.png"),
            facciones.acento(faccion),
            ruta="assets/fondo.png",
        )
        self.t0 = time.time()

    def dibujar(self, screen, dt=0.016):
        self.animado.actualizar(dt)
        self.animado.dibujar(screen)


# --------------------------------------------------------------------- utils
def _botones(screen, botones, mouse, dt):
    for b in botones:
        b.actualizar(dt, mouse)
        b.dibujar(screen)


def _pulsado(botones, pos):
    for b in botones:
        if b.clic(pos):
            b.pulsar()
            audio.sfx(audio.MENU_OK)
            return b
    return None


async def confirmar(screen, clock, titulo, mensaje, aceptar="SI"):
    """Pregunta si/no. Devuelve True si el jugador confirma.

    Vive en el menu porque empezar una campana nueva PISA la que hay. Antes no
    habia forma de empezar de cero con partida en curso, y la unica manera de
    ver el prologo era borrar el `campana.json` a mano desde la consola.
    """
    marco = pygame.Rect(ANCHO // 2 - 320, ALTO // 2 - 150, 640, 300)
    boton_si = Boton(pygame.Rect(marco.centerx - 230, marco.bottom - 78, 210, 52),
                     aceptar, 12, borde=ROJO, acento=ROJO)
    boton_no = Boton(pygame.Rect(marco.centerx + 20, marco.bottom - 78, 210, 52),
                     "VOLVER", 12)
    botones = [boton_si, boton_no]
    t0 = time.time()
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000
        await asyncio.sleep(0)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0
        for b in botones:
            b.actualizar(dt, mouse)
        panel(screen, marco, (28, 20, 24, 248), ROJO, radio=12, grosor=3)
        texto(screen, titulo, 20, ROJO, centro=(marco.centerx, marco.y + 46))
        parrafo(screen, mensaje, 10, TEXTO, marco.x + 40, marco.y + 96,
                marco.w - 80, interlinea=22, centrado=True)
        for b in botones:
            b.dibujar(screen, t)
        texto(screen, "ENTER confirma   ESC vuelve", 8, TEXTO_TENUE,
              centro=(marco.centerx, marco.bottom - 12))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    audio.sfx(audio.MENU_BACK)
                    return False
                if ev.key == pygame.K_RETURN:
                    audio.sfx(audio.MENU_OK)
                    return True
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                b = _pulsado(botones, ev.pos)
                if b is boton_si:
                    return True
                if b is boton_no:
                    return False


def _tecla_navegacion(botones, evento, seleccion):
    """Flechas / tab para moverse entre botones. Devuelve el indice."""
    if evento.key in (pygame.K_DOWN, pygame.K_TAB):
        return (seleccion + 1) % len(botones)
    if evento.key == pygame.K_UP:
        return (seleccion - 1) % len(botones)
    return None


# ------------------------------------------------------------------- portada
async def portada(screen, clock):
    """Pantalla de titulo con la marca animada."""
    fondo = Fondo("dragon")
    t0 = time.time()
    mouse = pygame.mouse.get_pos()
    boton = Boton(pygame.Rect(ANCHO // 2 - 170, ALTO - 120, 340, 52), "PULSA PARA EMPEZAR", 12)
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        t = time.time() - t0
        fondo.dibujar(screen, dt)

        # logo
        escala = 1 + 0.012 * math_seno(t * 1.6)
        tam = int(40 * escala)
        titulo = "TRIPLE TRIAD"
        resplandor(screen, pygame.Rect(ANCHO // 2 - 260, 120, 520, 70), DORADO, 60, 3, 8)
        texto(screen, titulo, tam, DORADO, centro=(ANCHO // 2, 150))
        texto(screen, "Goblins  Elfos  Humanos  Orcos  y mas", 11, TEXTO,
              centro=(ANCHO // 2, 200))
        # subtitulo por paises
        for i, f in enumerate(["Siete facciones", "Cinco duelos", "Un final por faccion"]):
            x = ANCHO // 2 - 300 + i * 220
            panel(screen, pygame.Rect(x - 90, 250, 180, 40), (16, 17, 26, 200), BORDE, radio=8, grosor=1)
            texto(screen, f, 9, TEXTO_TENUE, centro=(x, 270))

        # cartas flotando de fondo (giro y sombra cacheados: antes eran cinco
        # Surface nuevas por frame y eso solo en la portada ya costaba caro)
        for i, f in enumerate(["humano", "orco", "elfo", "goblin", "dragon"]):
            carta = mazos.TODOS[f][-1]
            clave = crt._slug(carta.nombre)
            sup = crt.crear(carta, None)
            x = 120 + i * 240 + math_seno(t * 0.8 + i) * 8
            y = 380 + math_seno(t * 1.1 + i * 1.7) * 12
            sombra = crt.sombra(sup, clave)
            rot = crt.rotar(sup, clave, math_seno(t * 0.5 + i) * 2)
            screen.blit(sombra, (x - sup.get_width() // 2 + 4, y - sup.get_height() // 2 + 6))
            screen.blit(rot, (x - rot.get_width() // 2, y - rot.get_height() // 2))

        boton.actualizar(dt, mouse)
        boton.dibujar(screen)
        texto(screen, f"version {VERSION_JUEGO}", 8, TEXTO_TENUE,
              centro=(ANCHO // 2, ALTO - 40))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                audio.sfx(audio.MENU_OK)
                return


def math_seno(x):
    import math

    return math.sin(x)


# ---------------------------------------------------------------------- menu
async def menu(screen, clock, estado=None):
    """Menu principal.

    Devuelve 'rapida', 'tutorial', 'mini', 'campana', 'nueva', 'coleccion',
    'ajustes' o 'salir'.

    Con partida en curso el boton de la izquierda sigue siendo CONTINUAR
    CAMPANA, y NUEVA CAMPANA esta aparte en la columna derecha: estan las dos
    cosas siempre, no una o la otra.
    """
    fondo = Fondo("dragon")
    hay = bool(estado) and not estado.get("completada")
    faccion = estado.get("faccion", "humano") if hay else "dragon"
    perfil_menu = campana.cargar_perfil()
    mini_ok = bool(perfil_menu.get("finales"))
    t0 = time.time()

    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, "TRIPLE TRIAD", 26, DORADO, centro=(ANCHO // 2, 120))
        texto(screen, "El Umbral del Trono", 10, TEXTO_TENUE, centro=(ANCHO // 2, 152))

        izquierda = [
            Boton(pygame.Rect(ANCHO // 2 - 340, 230, 300, 54), "NUEVA CAMPAÑA",
                  12, sub="Elige faccion y_forja tu final"),
            Boton(pygame.Rect(ANCHO // 2 - 340, 296, 300, 54), "PARTIDA RAPIDA",
                  12, sub="Un duelo suelto, sin campana"),
            Boton(pygame.Rect(ANCHO // 2 - 340, 362, 300, 54), "COLECCION",
                  12, sub="Cartas, mazos y finales"),
            Boton(pygame.Rect(ANCHO // 2 - 340, 428, 300, 54), "MINI CAMPANA",
                  12, sub="3 duelos tras la campana" if mini_ok else "Completa una campana"),
        ]
        izquierda[3].habilitado = mini_ok
        derecha = [
            Boton(pygame.Rect(ANCHO // 2 + 40, 230, 300, 54), "AJUSTES",
                  12, sub="Volumen, pantalla y controles"),
            Boton(pygame.Rect(ANCHO // 2 + 40, 296, 300, 54), "TUTORIAL",
                  12, sub="Aprende a jugar paso a paso"),
            Boton(pygame.Rect(ANCHO // 2 + 40, 362, 300, 54), "NUEVA CAMPANA",
                  12, sub="Empieza de cero y pisa la partida actual" if hay
                  else "Elige faccion y forja tu final"),
            Boton(pygame.Rect(ANCHO // 2 + 40, 428, 300, 54), "SALIR",
                  12, sub="Hasta la proxima partida"),
        ]
        if hay:
            izquierda[0].etiqueta = "CONTINUAR CAMPAÑA"
            titulo_nodo = campana.nodo(campana.nodo_actual(estado))['titulo']
            sub = f"{facciones.nombre(estado['faccion'])} - {titulo_nodo}"
            if ancho_texto(sub, 8) > 280:
                sub = f"{facciones.corto(estado['faccion'])} - {titulo_nodo}"
            izquierda[0].sub = sub
            izquierda[0].acento = facciones.acento(estado["faccion"])

        botones = izquierda + derecha
        _botones(screen, botones, mouse, dt)

        # panel lateral con el estado de la partida si existe
        if hay:
            panel(screen, pygame.Rect(ANCHO // 2 - 300, 494, 600, 190), PANEL, BORDE, radio=10)
            perfil = campana.cargar_perfil()
            racha = estado.get("mejor_racha", 0)
            texto(screen, "CAMPAÑA EN CURSO", 11, DORADO, centro=(ANCHO // 2, 520))
            texto(screen,
                  f"{facciones.nombre(estado['faccion'])}  -  Duelos ganados: {estado.get('victorias', 0)}  -  Racha: {racha}",
                  9, TEXTO, centro=(ANCHO // 2, 550))
            texto(screen,
                  f"Finales: {len(perfil.get('finales', {}))}  -  Duelos: {perfil.get('duelos', 0)}  -  Moneda: {perfil.get('moneda', 0)}",
                  9, TEXTO_TENUE, centro=(ANCHO // 2, 574))
            # mini mazo: las 5 primeras y cuantas mas hay en la coleccion
            cartas = campana.cartas_jugador(estado)
            for i, carta in enumerate(cartas[:5]):
                sup = crt.miniatura(carta, (52, 72))
                x = ANCHO // 2 - 5 * 34 + i * 68
                screen.blit(sup, (x, 590))
            if len(cartas) > 5:
                texto(screen, f"+{len(cartas) - 5} mas en el mazo", 8, TEXTO_TENUE,
                      centro=(ANCHO // 2, 676))

        texto(screen, "ENTER para continuar   ESC para salir", 8, TEXTO_TENUE,
              centro=(ANCHO // 2, ALTO - 30))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return "salir"
                if ev.key == pygame.K_RETURN:
                    audio.sfx(audio.MENU_OK)
                    return "campana" if hay else "nueva"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                b = _pulsado(botones, ev.pos)
                if b is izquierda[0]:
                    return "campana" if hay else "nueva"
                if b is izquierda[1]:
                    return "rapida"
                if b is izquierda[2]:
                    return "coleccion"
                if b is izquierda[3]:
                    return "mini"
                if b is derecha[0]:
                    return "ajustes"
                if b is derecha[1]:
                    return "tutorial"
                if b is derecha[2]:
                    # NUEVA CAMPANA existe SIEMPRE. Antes el boton de la
                    # izquierda se reconvertia en CONTINUAR cuando habia
                    # partida, y no quedaba forma de empezar de cero: para ver
                    # el prologo habia que borrar el guardado a mano.
                    return "nueva"
                if b is derecha[3]:
                    return "salir"


# ----------------------------------------------------------- elegir faccion
def perfil_racha(faccion, perfil=None):
    """Mejor racha guardada para una faccion (0 si no hay ninguna).

    `perfil` se puede pasar ya cargado: leer el JSON del disco por faccion y
    por frame era, solo en esta pantalla, 7 lecturas + 7 parseos en cada
    frame (y en la web el fichero esta en MEMFS, no es gratis).
    """
    if perfil is None:
        perfil = campana.cargar_perfil()
    return perfil.get("mejor_racha", {}).get(faccion, 0)


async def elegir_faccion(screen, clock, facciones_disponibles=None, modo="campana"):
    """Selector de faccion con ficha de estilo y vista previa del mazo.

    `modo`:
      - "campana": explica que la faccion decide rivales y final
      - "rapida" : solo elige bando para un duelo suelto (sincampaigna)
    """
    orden = facciones.orden_facciones()
    if facciones_disponibles:
        orden = [f for f in orden if f in facciones_disponibles]
    rapida = modo == "rapida"
    fondo = Fondo("humano")
    seleccion = 0
    t0 = time.time()
    # el perfil no cambia mientras esta pantalla abierta: se lee una vez
    perfil = campana.cargar_perfil()
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, "ELIGE TU FACCION" if not rapida else "DUELO RAPIDO", 22, DORADO,
              centro=(ANCHO // 2, 74))
        if rapida:
            texto(screen, "Elige con quien quieres pelear", 10, TEXTO_TENUE,
                  centro=(ANCHO // 2, 104))
        else:
            texto(screen, "Tu faccion decide tus rivales y tu final", 10, TEXTO_TENUE,
                  centro=(ANCHO // 2, 104))
            texto(screen, "nunca te enfrentaras a tu propia faccion", 8, VERDE,
                  centro=(ANCHO // 2, 124))

        rects = []
        compacta = len(orden) > 7
        if compacta:
            # 10 facciones no entran en la grilla de 3: 5 columnas x 2 filas.
            # La ficha lateral ya muestra el detalle, aqui basta arte + nombre.
            cols = 5
            paso_x, paso_y = 178, 225
            x0, y0, rw, rh = 50, 160, 168, 210
            escala_carta = 0.55
        else:
            cols = 3
            paso_x, paso_y = 290, 205
            x0, y0, rw, rh = 50, 165, 220, 190
            escala_carta = 0.8
        for i, faccion in enumerate(orden):
            col, fila = i % cols, i // cols
            x = x0 + col * paso_x
            y = y0 + fila * paso_y
            rect = pygame.Rect(x, y, rw, rh)
            rects.append(rect)
            activo = i == seleccion
            marco = pygame.Rect(rect.x, rect.y, rect.w, rect.h)
            panel(screen, marco, (18, 19, 28, 225),
                  facciones.acento(faccion) if activo else BORDE,
                  radio=10, grosor=3 if activo else 1)
            if activo:
                resplandor(screen, marco, facciones.acento(faccion),
                           int(70 + 50 * math_seno(t * 3)), 3, 12)
            carta = mazos.TODOS[faccion][-1]
            sup = crt.crear(carta, None, escala=escala_carta)
            screen.blit(sup, (rect.x + 10, rect.y + 10))
            if compacta:
                lineas = envolver(facciones.nombre(faccion), 8, rect.w - 88)[:2]
                ly = rect.y + 20
                for linea in lineas:
                    texto(screen, linea, 8, facciones.acento(faccion),
                          x=rect.x + 76, y=ly)
                    ly += 14
            else:
                lineas = envolver(facciones.nombre(faccion), 11, rect.w - 116)[:2]
                ly = rect.y + 22
                for linea in lineas:
                    texto(screen, linea, 11, facciones.acento(faccion),
                          x=rect.x + 106, y=ly)
                    ly += 15
                parrafo(screen, mazos.DESCRIPCION_BANDO.get(faccion, ""), 7, TEXTO_TENUE,
                        rect.x + 106, rect.y + 48 if len(lineas) == 1 else rect.y + 64,
                        rect.w - 116, interlinea=12)
            if not rapida:
                if compacta:
                    mejor = perfil_racha(faccion, perfil)
                    if mejor:
                        texto(screen, f"racha: {mejor}", 7, TEXTO_TENUE,
                              x=rect.x + 76, y=rect.bottom - 20)
                else:
                    texto(screen, f"jefe: {facciones.nombre(facciones.rival_final(faccion))}",
                          7, (206, 146, 146), x=rect.x + 106, y=rect.bottom - 34)
                    mejor = perfil_racha(faccion, perfil)
                    if mejor:
                        texto(screen, f"mejor racha: {mejor}", 7, TEXTO_TENUE,
                              x=rect.x + 106, y=rect.bottom - 18)

        # ficha de la faccion seleccionada
        faccion = orden[seleccion]
        cartas = mazos.TODOS[faccion]
        ficha = pygame.Rect(ANCHO - 340, 165, 300, 470)
        panel(screen, ficha, PANEL, facciones.acento(faccion), radio=10)
        texto(screen, facciones.nombre(faccion), 14, facciones.acento(faccion),
              centro=(ficha.centerx, ficha.y + 26))
        y_lema = parrafo(screen, facciones.FACCIONES[faccion]["lema"], 8, TEXTO_ON,
                         ficha.x + 18, ficha.y + 46, ficha.w - 36, interlinea=13, centrado=True)
        # el arco empieza tras el lema (el lema humano ocupa 3 lineas)
        y = max(ficha.y + 84, y_lema + 4)
        y = parrafo(screen, facciones.FACCIONES[faccion]["arco"], 8, TEXTO,
                    ficha.x + 18, y, ficha.w - 36, interlinea=15)
        y += 8
        texto(screen, "TU MAZO", 10, DORADO, centro=(ficha.centerx, y))
        y += 12
        mostradas = cartas[:10]
        filas_mazo = (len(mostradas) + 5) // 6
        for i, carta in enumerate(mostradas):
            sup = crt.miniatura(carta, (36, 50))
            fila, col = divmod(i, 6)
            en_fila = min(6, len(mostradas) - fila * 6)
            x = ficha.centerx - en_fila * 20 + col * 40
            yy = y + fila * 56
            screen.blit(sup, (x, yy))
            if filas_mazo == 1 and carta.habilidad:
                texto(screen, crt.ICONO_HABILIDAD.get(carta.habilidad, ""), 6,
                      TEXTO_TENUE, centro=(x + 18, yy + 54))
        y += 80 if filas_mazo == 1 else filas_mazo * 56 + 8
        if len(cartas) > len(mostradas):
            texto(screen, f"+{len(cartas) - len(mostradas)} mas en el mazo", 7,
                  TEXTO_TENUE, centro=(ficha.centerx, y))
            y += 16
        habilidades = sorted({c.habilidad for c in cartas if c.habilidad})
        if habilidades:
            texto(screen, "HABILIDADES", 8, DORADO, centro=(ficha.centerx, y))
            y += 16
            for hab in habilidades:
                y = parrafo(screen, f"{crt.ICONO_HABILIDAD.get(hab, hab)}: "
                                    f"{crt.descripcion_habilidad(hab)}",
                            7, TEXTO_TENUE, ficha.x + 18, y, ficha.w - 36, interlinea=12)
                y += 4
        else:
            texto(screen, "sin habilidades especiales", 7, TEXTO_TENUE,
                  centro=(ficha.centerx, y + 16))
            y += 30
        if rapida:
            texto(screen, "EN TU MANO", 8, DORADO, centro=(ficha.centerx, y))
            y += 18
            texto(screen, f"Tu rival sera una de las otras {len(orden) - 1} facciones.", 7, TEXTO,
                  x=ficha.x + 18, y=y)
        else:
            texto(screen, "TUS RIVALES EN CAMPANA", 8, DORADO, centro=(ficha.centerx, y))
            y += 18
            # la lista cabe mejor en dos o tres lineas que una por rival:
            # esas 7 lineas se salian de la ficha
            rivales = [facciones.nombre(r) for r in campana.escalera_de(faccion)]
            rivales.append(facciones.nombre(facciones.rival_final(faccion)))
            vistos = set()
            rivales = [r for r in rivales if not (r in vistos or vistos.add(r))]
            y = parrafo(screen, " › ".join(rivales), 7, TEXTO,
                        ficha.x + 18, y, ficha.w - 36, interlinea=12, centrado=True)

        # botones
        # "ELEGIR Y EMPEZAR" queda siempre a la vista: el unico flujo que quedaba
        # ambiguo era como confirmar la faccion.
        aceptar = Boton(pygame.Rect(ANCHO - 330, 650, 280, 46), "ELEGIR Y EMPEZAR", 12,
                        acento=facciones.acento(faccion))
        atras = Boton(pygame.Rect(ANCHO - 330, 706, 280, 38), "VOLVER", 10)
        if rapida:
            # en duelo rapido el boton late para que quede claro como confirmar
            aceptar.pulsar()
        _botones(screen, [aceptar, atras], mouse, dt)
        if rapida:
            texto(screen, "Pulsa ELEGIR Y EMPEZAR para confirmar", 8, DORADO,
                  centro=(ANCHO - 190, 622))
        texto(screen, "clic en una faccion para elegirla   ENTER para confirmar", 8,
              TEXTO_TENUE, centro=(ANCHO // 2, ALTO - 26))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
                for i, rect in enumerate(rects):
                    if rect.collidepoint(mouse):
                        if i != seleccion:
                            seleccion = i
                            audio.sfx(audio.MENU_MOVE)
                        break
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_LEFT, pygame.K_a):
                    seleccion = (seleccion - 1) % len(orden)
                    audio.sfx(audio.MENU_MOVE)
                if ev.key in (pygame.K_RIGHT, pygame.K_d):
                    seleccion = (seleccion + 1) % len(orden)
                    audio.sfx(audio.MENU_MOVE)
                if ev.key in (pygame.K_UP, pygame.K_w):
                    seleccion = (seleccion - cols) % len(orden)
                    audio.sfx(audio.MENU_MOVE)
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    seleccion = (seleccion + cols) % len(orden)
                    audio.sfx(audio.MENU_MOVE)
                if ev.key == pygame.K_RETURN:
                    audio.sfx(audio.MENU_OK)
                    return orden[seleccion]
                if ev.key == pygame.K_ESCAPE:
                    audio.sfx(audio.MENU_BACK)
                    return None
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        if i != seleccion:
                            seleccion = i
                            audio.sfx(audio.CARD)
                        else:
                            audio.sfx(audio.MENU_OK)
                            return orden[i]
                if aceptar.clic(ev.pos):
                    aceptar.pulsar()
                    audio.sfx(audio.MENU_OK)
                    return orden[seleccion]
                if atras.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    return None


# ------------------------------------------------------------ mapa de campana
POSICIONES = {
    "senda": (130, 300),
    "bifurcacion": (320, 440),
    "aldea": (540, 230),
    "ruinas": (540, 505),
    "fortaleza": (760, 440),
    "asalto": (960, 300),
    "trono": (1150, 460),
}
CONEXIONES = [
    ("senda", "bifurcacion"),
    ("bifurcacion", "aldea"),
    ("bifurcacion", "ruinas"),
    ("aldea", "fortaleza"),
    ("ruinas", "fortaleza"),
    ("fortaleza", "asalto"),
    ("asalto", "trono"),
]


async def mapa_campana(screen, clock, estado):
    """Mapa con los nodos visitados, el actual y las ramas."""
    fondo = Fondo(estado["faccion"])
    t0 = time.time()
    ruta = set(estado.get("ruta", []))
    actual = campana.nodo_actual(estado)

    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        fundido_entrada(screen, t0)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, "MAPA DE LA CAMPANA", 20, DORADO, centro=(ANCHO // 2, 60))
        faccion = estado["faccion"]
        texto(screen, facciones.nombre(faccion), 12, facciones.acento(faccion),
              centro=(ANCHO // 2, 92))
        progreso = int(campana.progreso(estado) * 100)
        panel(screen, pygame.Rect(ANCHO // 2 - 220, 112, 440, 28), PANEL, BORDE, radio=8, grosor=1)
        rect_prog = pygame.Rect(ANCHO // 2 - 214, 118, 428 * campana.progreso(estado), 16)
        pygame.draw.rect(screen, facciones.acento(faccion), rect_prog, border_radius=6)
        texto(screen, f"PROGRESO {progreso}%  -  DUELO {len(ruta) + 1} DE 5  -  RACHA {estado.get('racha', 0)}",
              8, TEXTO, centro=(ANCHO // 2, 126))

        # conexiones
        for a, b in CONEXIONES:
            x1, y1 = POSICIONES[a]
            x2, y2 = POSICIONES[b]
            activo = a in ruta and (b in ruta or b == actual)
            color = facciones.acento(faccion) if activo else (60, 58, 52)
            pygame.draw.line(screen, color, (x1, y1), (x2, y2), 5 if activo else 3)
            if activo:
                p = (t * 0.35) % 1.0
                px = int(x1 + (x2 - x1) * p)
                py = int(y1 + (y2 - y1) * p)
                pygame.draw.circle(screen, DORADO, (px, py), 4)

        # nodos
        rects = {}
        for nombre, (x, y) in POSICIONES.items():
            datos = campana.nodo(nombre)
            radio = 46 if datos["tipo"] != "eleccion" else 38
            centro = (x, y)
            posturect = pygame.Rect(x - radio, y - radio, radio * 2, radio * 2)
            rects[nombre] = posturect
            visitado = nombre in ruta
            es_actual = nombre == actual
            if es_actual:
                resplandor(screen, posturect, DORADO, int(90 + 60 * math_seno(t * 3)), 3, radio)
            color = (
                facciones.acento(faccion) if es_actual
                else VERDE if visitado
                else (70, 68, 62)
            )
            pygame.draw.circle(screen, (18, 19, 28), centro, radio)
            pygame.draw.circle(screen, color, centro, radio, 4 if (es_actual or visitado) else 2)
            if datos["tipo"] == "eleccion":
                texto(screen, "?", radio - 6, color, centro=centro)
            elif es_actual:
                rival = campana.rival_de_nodo(estado, nombre)
                texto(screen, facciones.corto(rival), 9, color, centro=(x, y - 6))
                texto(screen, facciones.nombre(rival), 6, TEXTO_TENUE, centro=(x, y + 10))
            elif visitado:
                texto(screen, "OK", 10, color, centro=(x, y - 6))
            else:
                texto(screen, "-", 10, color, centro=(x, y - 6))
            texto(screen, datos["titulo"], 7, TEXTO if (es_actual or visitado) else TEXTO_TENUE,
                  centro=(x, y + radio + 14))

        # panel de estado
        panel(screen, pygame.Rect(40, 620, 500, 140), PANEL, BORDE, radio=10)
        info = campana.info_duelo(estado)
        texto(screen, f"SIGUIENTE: {info['titulo'].upper()}", 10, DORADO, x=60, y=638)
        texto(screen,
              f"Rival: {info['nombre']} ({info['nombre_faccion']})   Dificultad {info['dificultad']}",
              8, TEXTO, x=60, y=662)
        texto(screen,
              f"Victorias {estado.get('victorias', 0)}  Derrotas {estado.get('derrotas', 0)}  "
              f"Mejor racha {estado.get('mejor_racha', 0)}  Aliados: {len(estado.get('aliados', []))}",
              8, TEXTO_TENUE, x=60, y=684)
        if estado.get("debilitar"):
            texto(screen, f"Rival debilitado: -{estado['debilitar']}", 8, VERDE, x=60, y=706)
        texto(screen, "Clic en un nodo ya superado para ver su ficha.", 7, TEXTO_TENUE,
              x=60, y=730)

        # mazo del jugador: las 5 primeras y cuantas mas hay
        cartas = campana.cartas_jugador(estado)
        texto(screen, "TU MAZO", 9, DORADO, x=560, y=612)
        for i, carta in enumerate(cartas[:5]):
            sup = crt.crear(carta, None)
            x = 560 + i * 74
            y = 630
            if sup.get_width():
                pantalla_carta = pygame.transform.scale(sup, (56, 78))
                screen.blit(pantalla_carta, (x, y))
                if pygame.Rect(x, y, 56, 78).collidepoint(mouse):
                    crt.resplandor_carta(screen, pygame.Rect(x, y, 56, 78), carta, None, 110)
                    tooltip(screen, _descripcion_carta(carta), (x + 28, y),
                            ancho=300, arriba=True)
        if len(cartas) > 5:
            texto(screen, f"+{len(cartas) - 5} mas", 8, TEXTO_TENUE, x=560 + 5 * 74, y=662)

        seguir = Boton(pygame.Rect(ANCHO - 300, 660, 260, 50), "SEGUIR", 12,
                       acento=facciones.acento(faccion))
        menu = Boton(pygame.Rect(ANCHO - 300, 722, 260, 38), "GUARDAR Y SALIR", 10)
        tienda_btn = Boton(pygame.Rect(ANCHO - 300, 596, 260, 50), "TIENDA", 12,
                           sub=f"{campana.PRECIO_SOBRE} moneda")
        _botones(screen, [seguir, menu, tienda_btn], mouse, dt)
        dibujar_tooltips(screen)
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return "salir"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if tienda_btn.clic(ev.pos):
                    audio.sfx(audio.MENU_OK)
                    await tienda(screen, clock, estado)
                    continue
                if seguir.clic(ev.pos):
                    seguir.pulsar()
                    audio.sfx(audio.MENU_OK)
                    return "seguir"
                if menu.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    campana.guardar(estado)
                    return "salir"
                for nombre, rect in rects.items():
                    if rect.collidepoint(ev.pos):
                        if nombre == actual:
                            audio.sfx(audio.MENU_OK)
                            return "seguir"
                        if nombre in ruta:
                            audio.sfx(audio.CARD)
                            await _ficha_nodo(screen, clock, estado, nombre)


async def tienda(screen, clock, estado):
    """Tienda: sobres a cambio de moneda. ESC o VOLVER para salir.

    Con estado None (menu/coleccion) no hay mazo de run: las nuevas van
    solo a la coleccion.
    """
    fondo = Fondo((estado or {}).get("faccion", "humano"))
    mensaje = ""
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        texto(screen, "TIENDA", 22, DORADO, centro=(ANCHO // 2, 110))
        texto(screen, f"Moneda: {campana.moneda()}", 12, DORADO,
              centro=(ANCHO // 2, 150))
        caja = pygame.Rect(ANCHO // 2 - 200, 200, 400, 220)
        panel(screen, caja, PANEL, BORDE, radio=10)
        texto(screen, "SOBRE DE CARTAS", 12, TEXTO_ON, centro=(caja.centerx, caja.y + 40))
        texto(screen, "3 cartas al azar del pool", 9, TEXTO, centro=(caja.centerx, caja.y + 80))
        texto(screen, "Legendaria ~10% - pity al 10", 8, TEXTO_TENUE,
              centro=(caja.centerx, caja.y + 112))
        texto(screen, f"Precio: {campana.PRECIO_SOBRE} moneda", 10, DORADO,
              centro=(caja.centerx, caja.y + 150))
        texto(screen, f"Sobres sin legendaria: {campana.pity_sobres()}/9", 8, TEXTO_TENUE,
              centro=(caja.centerx, caja.y + 182))
        comprar = Boton(pygame.Rect(ANCHO // 2 - 160, 450, 320, 54), "COMPRAR SOBRE",
                        12, sub=f"{campana.PRECIO_SOBRE} moneda")
        volver = Boton(pygame.Rect(ANCHO // 2 - 130, 520, 260, 44), "VOLVER", 10)
        _botones(screen, [comprar, volver], mouse, dt)
        if mensaje:
            texto(screen, mensaje, 9, TEXTO, centro=(ANCHO // 2, 600))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if comprar.clic(ev.pos):
                    ok, nuevas, mejoradas = campana.comprar_sobre(estado)
                    if ok:
                        audio.sfx(audio.MENU_OK)
                        sob = campana.cartas_por_nombre(estado, nuevas + mejoradas)
                        await revelar_sobre(
                            screen, clock,
                            [c for c in sob if c.nombre in nuevas],
                            [c for c in sob if c.nombre in mejoradas])
                        mensaje = ""
                    else:
                        audio.sfx(audio.INVALIDO, 0.5)
                        mensaje = "Sin moneda: gana duelos de campana"
                elif volver.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    return


async def mapa_mini(screen, clock, estado):
    """Mapa lineal de la mini campana (3 duelos). Devuelve 'seguir' o 'salir'.

    La mini no se guarda entre sesiones: salir la descarta.
    """
    fondo = Fondo(estado.get("faccion", "elfo_nocturno"))
    nodos = ["mini_senda", "mini_nudo", "mini_trono"]
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        actual = campana.nodo_actual(estado)
        ruta = estado.get("ruta", [])
        texto(screen, "MINI CAMPANA", 22, DORADO, centro=(ANCHO // 2, 120))
        texto(screen, facciones.nombre(estado.get("faccion", "")), 12,
              facciones.acento(estado.get("faccion", "humano")),
              centro=(ANCHO // 2, 156))
        for i, nid in enumerate(nodos):
            datos = campana.nodo(nid)
            rect = pygame.Rect(ANCHO // 2 - 460 + i * 320, 240, 280, 220)
            if nid in ruta:
                borde, etiqueta = VERDE, "COMPLETADO"
            elif nid == actual:
                borde, etiqueta = DORADO, "AHORA"
            else:
                borde, etiqueta = BORDE, "BLOQUEADO"
            panel(screen, rect, PANEL, borde, radio=10)
            texto(screen, datos["titulo"], 10, TEXTO_ON, centro=(rect.centerx, rect.y + 40))
            texto(screen, f"Rival: {facciones.nombre(campana.rival_de_nodo(estado, nid))}",
                  8, TEXTO, centro=(rect.centerx, rect.y + 90))
            texto(screen, f"Nivel {datos.get('dificultad', 0)}", 8, TEXTO_TENUE,
                  centro=(rect.centerx, rect.y + 120))
            texto(screen, etiqueta, 9, borde, centro=(rect.centerx, rect.y + 170))
        luchar = Boton(pygame.Rect(ANCHO // 2 - 320, 520, 300, 54), "LUCHAR", 12,
                       sub=campana.nodo(actual)["titulo"],
                       acento=facciones.acento(estado.get("faccion", "humano")))
        salir = Boton(pygame.Rect(ANCHO // 2 + 20, 520, 300, 54), "ABANDONAR", 12,
                      sub="Se pierde el progreso")
        _botones(screen, [luchar, salir], mouse, dt)
        texto(screen, "ESC para abandonar", 8, TEXTO_TENUE,
              centro=(ANCHO // 2, ALTO - 120))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return "salir"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if luchar.clic(ev.pos):
                    luchar.pulsar()
                    audio.sfx(audio.MENU_OK)
                    return "seguir"
                if salir.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    return "salir"


def filtrar_coleccion(cartas, habilidad=None, rareza_nombre=None):
    """Filtra por habilidad y/o rareza. Puro y testeable."""
    out = list(cartas)
    if habilidad:
        out = [c for c in out if c.habilidad == habilidad]
    if rareza_nombre:
        out = [c for c in out if rareza(c)[0] == rareza_nombre]
    return out


def paginar_coleccion(cartas, pagina, por_pagina=10):
    """Pagina (recorte) y total de paginas. Pagina fuera de rango -> ultima valida."""
    total = max(1, (len(cartas) + por_pagina - 1) // por_pagina)
    pagina = max(0, min(pagina, total - 1))
    return cartas[pagina * por_pagina:(pagina + 1) * por_pagina], total, pagina


def _descripcion_carta(carta, estado=None):
    partes = [carta.nombre, f"{facciones.nombre(carta.bando)} - {rareza(carta)[0]}"]
    if carta.habilidad:
        partes.append(f"{crt.ICONO_HABILIDAD.get(carta.habilidad, carta.habilidad)}: "
                      f"{crt.descripcion_habilidad(carta.habilidad)}")
    partes.append(" | ".join(f"{l}:{val(carta.valores[l])}" for l in LADOS))
    # Compendio dual: si el duelista ya descubrio la verdad de esta carta,
    # aparece debajo. Antes solo existe lo que dice el juego.
    if estado is not None:
        entrada = compendio.entrada(carta.nombre)
        if entrada:
            if campana.compendio_revelada(estado, carta.nombre):
                partes.append("LO QUE REALMENTE PASO: " + entrada["verdad"])
            else:
                partes.append("LO QUE REALMENTE PASO: [sin descubrir]")
    return "\n".join(partes)


async def _ficha_nodo(screen, clock, estado, nombre):
    """Panel informativo de un nodo ya superado."""
    datos = campana.nodo(nombre)
    info = campana.info_duelo(estado, nombre)
    cerrar = Boton(pygame.Rect(ANCHO // 2 - 90, ALTO - 130, 180, 44), "VOLVER", 11)
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        mouse = pygame.mouse.get_pos()
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 190))
        screen.blit(capa, (0, 0))
        caja = pygame.Rect(ANCHO // 2 - 260, 180, 520, 380)
        panel(screen, caja, (20, 20, 30, 245), DORADO, radio=10)
        texto(screen, datos["titulo"], 14, DORADO, centro=(ANCHO // 2, caja.y + 36))
        texto(screen, f"Rival: {info['nombre']} - {info['nombre_faccion']}", 10, TEXTO,
              centro=(ANCHO // 2, caja.y + 76))
        texto(screen, f"Dificultad: {info['dificultad']}", 9, TEXTO_TENUE,
              centro=(ANCHO // 2, caja.y + 104))
        y = caja.y + 140
        for previa in datos.get("previa", []):
            y = parrafo(screen, previa, 8, TEXTO, caja.x + 30, y, caja.w - 60, interlinea=18)
        if info.get("entrada"):
            y += 10
            texto(screen, f"- {info['entrada']}", 8, DORADO, centro=(ANCHO // 2, y))
        _botones(screen, [cerrar], mouse, dt)
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                audio.sfx(audio.MENU_BACK)
                return


async def elegir_rama(screen, clock, estado):
    """La bifurcacion de la campana:Aldea (segura) o Ruinas (riesgosa)."""
    fondo = Fondo(estado["faccion"])
    opciones = campana.opciones_bifurcacion()
    t0 = time.time()
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        fundido_entrada(screen, t0)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, campana.nodo("bifurcacion")["titulo"].upper(), 22, DORADO,
              centro=(ANCHO // 2, 90))
        texto(screen, "Elige donde cae tu destino. Las dos rutas acaban en la fortaleza.",
              10, TEXTO_TENUE, centro=(ANCHO // 2, 124))

        rects = {}
        for i, rama in enumerate(opciones):
            datos = campana.nodo("bifurcacion")["opciones"][rama]
            x = 140 + i * 520
            rect = pygame.Rect(x, 200, 460, 330)
            rects[rama] = rect
            hover = rect.collidepoint(mouse)
            acento = facciones.acento(estado["faccion"]) if hover else BORDE
            panel(screen, rect, (20, 20, 30, 235), acento, radio=12, grosor=3 if hover else 2)
            texto(screen, datos["titulo"].upper(), 15, DORADO, centro=(rect.centerx, rect.y + 46))
            for previa in datos.get("previa", []):
                parrafo(screen, previa, 9, TEXTO, rect.x + 24, rect.y + 90, rect.w - 48,
                        interlinea=20, centrado=True)
            y = rect.y + 170
            y = parrafo(screen, datos["resumen"], 9, TEXTO_ON, rect.x + 30, y,
                        rect.w - 60, interlinea=20, centrado=True)
            # rival de la rama
            rival = campana.rival_de_nodo(estado, rama)
            info = campana.info_duelo(estado, rama)
            y = max(y, rect.y + 250)
            texto(screen, f"Rival: {info['nombre']} ({info['nombre_faccion']})",
                  9, facciones.acento(rival), centro=(rect.centerx, y))
            texto(screen, f"Dificultad {info['dificultad']}", 8, TEXTO_TENUE,
                  centro=(rect.centerx, y + 20))
            # recompensa propia de la rama
            recompensas = campana.recompensas_de(rama)
            texto(screen, "RECOMPENSAS: " + ", ".join(
                {"entrenamiento": "entrenamiento", "recluta": "recluta",
                 "sigilo": "sigilo", "aliado": "pacto",
                 "sobre": "sobre"}[r] for r in recompensas),
                7, TEXTO_TENUE, centro=(rect.centerx, rect.bottom - 20))

        texto(screen, "clic en la ruta que elijas", 9, TEXTO_TENUE, centro=(ANCHO // 2, 580))
        # mazo actual
        cartas = campana.cartas_jugador(estado)
        for i, carta in enumerate(cartas):
            sup = crt.crear(carta, None)
            screen.blit(pygame.transform.scale(sup, (86, 118)),
                        (ANCHO // 2 - len(cartas) * 47 + i * 94, 610))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return None
                if ev.key == pygame.K_LEFT:
                    return opciones[0]
                if ev.key == pygame.K_RIGHT:
                    return opciones[1]
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for rama, rect in rects.items():
                    if rect.collidepoint(ev.pos):
                        audio.sfx(audio.MENU_OK)
                        return rama


# ------------------------------------------------------------------- rewards
def _icono_recompensa(screen, clave, centro, color):
    """Icono simple dibujado a mano para cada recompensa."""
    cx, cy = centro
    if clave == "entrenamiento":
        # flecha hacia arriba: subir un valor
        pygame.draw.polygon(screen, color, [
            (cx, cy - 20), (cx + 16, cy - 2), (cx + 6, cy - 2),
            (cx + 6, cy + 18), (cx - 6, cy + 18), (cx - 6, cy - 2), (cx - 16, cy - 2),
        ])
    elif clave == "sigilo":
        # rombo: marca permanente
        pygame.draw.polygon(screen, color, [
            (cx, cy - 20), (cx + 16, cy), (cx, cy + 20), (cx - 16, cy),
        ])
        pygame.draw.polygon(screen, (20, 20, 30), [
            (cx, cy - 9), (cx + 7, cy), (cx, cy + 9), (cx - 7, cy),
        ])
    elif clave == "recluta":
        # ficha de carta entrando en el mazo
        pygame.draw.rect(screen, color, (cx - 14, cy - 18, 20, 30), border_radius=3, width=2)
        pygame.draw.rect(screen, con_alpha(color, 150), (cx - 4, cy - 10, 20, 30), border_radius=3, width=2)
    elif clave == "aliado":
        # dos circulos que se unen: el pacto
        pygame.draw.circle(screen, color, (cx - 7, cy), 13, 3)
        pygame.draw.circle(screen, color, (cx + 7, cy), 13, 3)
    else:
        pygame.draw.circle(screen, color, centro, 16, 3)


async def recompensa(screen, clock, estado, nodo_id):
    """Elige una recompensa tras ganar el duelo."""
    opciones = campana.recompensas_de(nodo_id)
    fondo = Fondo(estado["faccion"])
    t0 = time.time()
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        fundido_entrada(screen, t0)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, "VICTORIA", 26, VERDE, centro=(ANCHO // 2, 96))
        texto(screen, f"Elige una recompensa - {campana.nodo(nodo_id)['titulo']}", 10, TEXTO_TENUE,
              centro=(ANCHO // 2, 132))

        rects = []
        total = len(opciones)
        for i, clave in enumerate(opciones):
            ancho = 300
            x = ANCHO // 2 - (total * ancho + (total - 1) * 24) // 2 + i * (ancho + 24)
            rect = pygame.Rect(x, 210, ancho, 260)
            rects.append(rect)
            hover = rect.collidepoint(mouse)
            color = facciones.acento(estado["faccion"]) if hover else BORDE
            panel(screen, rect, (20, 20, 30, 230), color, radio=12, grosor=3 if hover else 2)
            icono = {"entrenamiento": "ENTRENAMIENTO", "recluta": "RECLUTA",
                     "sigilo": "SIGILO", "aliado": "PACTO"}.get(clave, clave.upper())
            texto(screen, icono, 12, DORADO, centro=(rect.centerx, rect.y + 46))
            y = parrafo(screen, campana.TEXTO_RECOMPENSA.get(clave, ""), 8, TEXTO,
                        rect.x + 20, rect.y + 90, rect.w - 40, interlinea=18, centrado=True)
            if clave == "aliado":
                f = campana.sustituto_aliado(estado)
                if f:
                    texto(screen, f"Con: {facciones.nombre(f)}", 9,
                          facciones.acento(f), centro=(rect.centerx, rect.bottom - 30))
            # icono de la recompensa
            _icono_recompensa(screen, clave, (rect.centerx, rect.bottom - 62),
                              facciones.acento(estado["faccion"]))

        texto(screen, "clic en la recompensa que quieras", 9, TEXTO_TENUE,
              centro=(ANCHO // 2, 520))
        # mini mazo
        cartas = campana.cartas_jugador(estado)
        for i, carta in enumerate(cartas):
            sup = crt.crear(carta, None)
            screen.blit(pygame.transform.scale(sup, (96, 132)),
                        (ANCHO // 2 - len(cartas) * 52 + i * 104, 560))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        audio.sfx(audio.RECOMPENSA)
                        return opciones[i]
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return opciones[0]


async def armar_mazo(screen, clock, faccion=None):
    """Editor del mazo GLOBAL: de 5 a 10 poseidas, 1 LEG y 3 RARA maximo.

    Guarda en el perfil y devuelve la lista de dicts (None si se cancela).
    """
    from reglas import Carta

    perfil = campana.cargar_perfil()
    coleccion = campana.coleccion_de(perfil)
    poseidas = {}
    for nombre, datos in coleccion.items():
        c = Carta.desde_dict(dict(datos))
        poseidas[nombre] = (datos, c.bando, sum(c.valores.values()))
    nombres = sorted(poseidas, key=lambda n: (poseidas[n][1], -poseidas[n][2], n))
    actual = [n for n in campana.mazo_global(perfil) if n in coleccion]
    seleccion = list(actual) if actual else nombres[:5]
    pagina, fbando = 0, faccion if faccion in facciones.FACCIONES else None
    BANDOS = [None] + facciones.orden_facciones()
    motivo = ""
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo = Fondo(faccion or "dragon")
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        visibles = [n for n in nombres if fbando is None or poseidas[n][1] == fbando]
        pagina_items, total_pags, pagina = paginar_coleccion(visibles, pagina)
        rars = [rareza(Carta.desde_dict(coleccion[n]))[0] for n in seleccion]
        texto(screen, "ARMA TU MAZO", 20, DORADO, centro=(ANCHO // 2, 90))
        texto(screen,
              f"MAZO {len(seleccion)}/{campana.MAZO_RUN_N} (min {campana.MAZO_MIN_N})  -  LEG "
              f"{rars.count('LEGENDARIA')}/{campana.LIMITE_LEGENDARIAS}  -  RARA "
              f"{rars.count('RARA')}/{campana.LIMITE_RARAS}",
              10, TEXTO, centro=(ANCHO // 2, 130))
        for i, nombre in enumerate(pagina_items):
            datos, bando, _total = poseidas[nombre]
            sup = crt.crear(Carta.desde_dict(dict(datos)), None, escala=0.7)
            x = ANCHO // 2 - len(pagina_items) * 60 + i * 120
            rect = pygame.Rect(x, 200, sup.get_width(), sup.get_height())
            if nombre in seleccion:
                resplandor(screen, rect, VERDE, 130, 3, 8)
            elif rect.collidepoint(mouse):
                crt.resplandor_carta(screen, rect, Carta.desde_dict(dict(datos)), None, 110)
            screen.blit(sup, (rect.x, rect.y))
        b_bando = Boton(pygame.Rect(90, 360, 220, 40),
                        f"BANDO: {(fbando or 'TODOS').upper()}", 8)
        b_prev = Boton(pygame.Rect(ANCHO // 2 - 160, 360, 64, 40), "<", 10)
        b_next = Boton(pygame.Rect(ANCHO // 2 + 96, 360, 64, 40), ">", 10)
        _botones(screen, [b_bando, b_prev, b_next], mouse, dt)
        texto(screen, f"{pagina + 1}/{total_pags}", 9, TEXTO, centro=(ANCHO // 2, 380))
        guardar_btn = Boton(pygame.Rect(ANCHO // 2 - 350, 690, 330, 54),
                            "GUARDAR MAZO", 12)
        volver = Boton(pygame.Rect(ANCHO // 2 + 20, 690, 330, 54), "VOLVER", 12)
        _botones(screen, [guardar_btn, volver], mouse, dt)
        if motivo:
            texto(screen, motivo, 9, ROJO, centro=(ANCHO // 2, 660))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return None
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_LEFT:
                pagina -= 1
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RIGHT:
                pagina += 1
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_b:
                fbando = BANDOS[(BANDOS.index(fbando) + 1) % len(BANDOS)]
                pagina = 0
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if b_bando.clic(ev.pos):
                    fbando = BANDOS[(BANDOS.index(fbando) + 1) % len(BANDOS)]
                    pagina = 0
                    audio.sfx(audio.MENU_MOVE)
                    continue
                if b_prev.clic(ev.pos):
                    pagina -= 1
                    audio.sfx(audio.MENU_MOVE)
                    continue
                if b_next.clic(ev.pos):
                    pagina += 1
                    audio.sfx(audio.MENU_MOVE)
                    continue
                if guardar_btn.clic(ev.pos):
                    elegidas = [dict(coleccion[n]) for n in seleccion]
                    ok, motivo = campana.validar_mazo(elegidas, set(coleccion))
                    if ok:
                        audio.sfx(audio.MENU_OK)
                        campana.guardar_mazo_global(list(seleccion))
                        return elegidas
                    audio.sfx(audio.INVALIDO, 0.5)
                    continue
                if volver.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    return None
                for i, nombre in enumerate(pagina_items):
                    x = ANCHO // 2 - len(pagina_items) * 60 + i * 120
                    rect = pygame.Rect(x, 200, 73, 101)
                    if rect.collidepoint(ev.pos):
                        if nombre in seleccion:
                            seleccion.remove(nombre)
                        elif len(seleccion) >= campana.MAZO_RUN_N:
                            motivo = "Mazo lleno: quita una primero"
                        else:
                            seleccion.append(nombre)
                            motivo = ""
                        audio.sfx(audio.CARD)
                        break


async def elegir_carta_para_mejorar(screen, clock, estado):
    cartas = campana.cartas_jugador(estado)
    seleccion = None
    pagina = 0
    while True:
        mouse = pygame.mouse.get_pos()
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        # overlay oscuro: el modal no tapa lo de abajo sin congelar el fondo
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 190))
        screen.blit(capa, (0, 0))
        texto(screen, "ENTRENAMIENTO", 20, DORADO, centro=(ANCHO // 2, 140))
        texto(screen, "Elige la carta que quieres mas fuerte (+1)", 10, TEXTO_TENUE,
              centro=(ANCHO // 2, 176))
        pagina_items, total_pags, pagina = paginar_coleccion(cartas, pagina)
        base = pagina * 10
        rects = []
        for i, carta in enumerate(pagina_items):
            sup = crt.crear(carta, None, escala=0.7)
            x = ANCHO // 2 - len(pagina_items) * 60 + i * 120
            rect = pygame.Rect(x, 240, sup.get_width(), sup.get_height())
            rects.append(rect)
            if rect.collidepoint(mouse):
                crt.resplandor_carta(screen, rect, carta, None, 110)
            screen.blit(sup, (rect.x, rect.y - (12 if rect.collidepoint(mouse) else 0)))
            texto(screen, f"{(i + 1) % 10}", 9, TEXTO_TENUE, centro=(rect.centerx, rect.bottom + 18))
        b_prev = Boton(pygame.Rect(ANCHO // 2 - 160, 640, 64, 40), "<", 10)
        b_next = Boton(pygame.Rect(ANCHO // 2 + 96, 640, 64, 40), ">", 10)
        _botones(screen, [b_prev, b_next], mouse, dt)
        texto(screen, f"{pagina + 1}/{total_pags}", 9, TEXTO, centro=(ANCHO // 2, 660))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.KEYDOWN:
                idx = None
                if pygame.K_1 <= ev.key <= pygame.K_9:
                    idx = ev.key - pygame.K_1
                elif ev.key == pygame.K_0:
                    idx = 9
                elif ev.key == pygame.K_LEFT:
                    pagina -= 1
                    audio.sfx(audio.MENU_MOVE)
                elif ev.key == pygame.K_RIGHT:
                    pagina += 1
                    audio.sfx(audio.MENU_MOVE)
                if idx is not None and base + idx < len(cartas):
                    return base + idx
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if b_prev.clic(ev.pos):
                    pagina -= 1
                    audio.sfx(audio.MENU_MOVE)
                    continue
                if b_next.clic(ev.pos):
                    pagina += 1
                    audio.sfx(audio.MENU_MOVE)
                    continue
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        return base + i


async def draft(screen, clock, estado, ofertas=None):
    """Elige una de las cartas ofrecidas y a quien sustituye."""
    ofertas = ofertas or campana.draft_aleatorio(estado, 3)
    fondo = Fondo(estado["faccion"])
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        texto(screen, "RECLUTA", 22, DORADO, centro=(ANCHO // 2, 110))
        texto(screen, "Elige una carta del pool", 10, TEXTO_TENUE, centro=(ANCHO // 2, 146))
        rects = []
        for i, carta in enumerate(ofertas):
            sup = crt.crear(carta, None, escala=1.5)
            x = ANCHO // 2 - len(ofertas) * 100 + i * 200
            rect = pygame.Rect(x, 210, sup.get_width(), sup.get_height())
            rects.append(rect)
            if rect.collidepoint(mouse):
                crt.resplandor_carta(screen, rect, carta, None, 110)
                tooltip(screen, _descripcion_carta(carta, estado), (rect.centerx, rect.y),
                        ancho=300, arriba=True)
            screen.blit(sup, (rect.x, rect.y))
            etiqueta, color = rareza(carta)
            texto(screen, etiqueta, 8, color, centro=(rect.centerx, rect.bottom + 20))
        dibujar_tooltips(screen)
        pygame.display.flip()
        elegida = None
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        elegida = ofertas[i]
        if elegida:
            audio.sfx(audio.RECOMPENSA)
            return elegida


async def draft_reemplazo(screen, clock, estado, carta):
    """Segunda fase del draft: a quien sustituye la carta nueva."""
    cartas = campana.cartas_jugador(estado)
    pagina = 0
    while True:
        mouse = pygame.mouse.get_pos()
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 190))
        screen.blit(capa, (0, 0))
        texto(screen, "RECLUTA", 20, DORADO, centro=(ANCHO // 2, 96))
        texto(screen, f"{carta.nombre} entra en el mazo. A quien sustituye?", 10, TEXTO_TENUE,
              centro=(ANCHO // 2, 132))
        nueva = crt.crear(carta, None, escala=1.2)
        screen.blit(nueva, (ANCHO // 2 - nueva.get_width() // 2, 170))
        pagina_items, total_pags, pagina = paginar_coleccion(cartas, pagina)
        base = pagina * 10
        rects = []
        for i, vieja in enumerate(pagina_items):
            sup = crt.crear(vieja, None, escala=0.8)
            x = ANCHO // 2 - len(pagina_items) * 60 + i * 120
            rect = pygame.Rect(x, 380, sup.get_width(), sup.get_height())
            rects.append(rect)
            if rect.collidepoint(mouse):
                crt.resplandor_carta(screen, rect, vieja, None, 110)
            screen.blit(sup, (rect.x, rect.y))
            texto(screen, str((i + 1) % 10), 9, TEXTO_TENUE, centro=(rect.centerx, rect.bottom + 18))
        b_prev = Boton(pygame.Rect(ANCHO // 2 - 160, 560, 64, 40), "<", 10)
        b_next = Boton(pygame.Rect(ANCHO // 2 + 96, 560, 64, 40), ">", 10)
        _botones(screen, [b_prev, b_next], mouse, dt)
        texto(screen, f"{pagina + 1}/{total_pags}", 9, TEXTO, centro=(ANCHO // 2, 580))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.KEYDOWN:
                idx = None
                if pygame.K_1 <= ev.key <= pygame.K_9:
                    idx = ev.key - pygame.K_1
                elif ev.key == pygame.K_0:
                    idx = 9
                elif ev.key == pygame.K_LEFT:
                    pagina -= 1
                    audio.sfx(audio.MENU_MOVE)
                elif ev.key == pygame.K_RIGHT:
                    pagina += 1
                    audio.sfx(audio.MENU_MOVE)
                if idx is not None and base + idx < len(cartas):
                    return base + idx
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if b_prev.clic(ev.pos):
                    pagina -= 1
                    audio.sfx(audio.MENU_MOVE)
                    continue
                if b_next.clic(ev.pos):
                    pagina += 1
                    audio.sfx(audio.MENU_MOVE)
                    continue
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        return base + i


async def aplicar_recompensa(screen, clock, estado, clave, nodo_id):
    """Aplica la recompensa elegida y muestra su resultado."""
    if clave == "entrenamiento":
        idx = await elegir_carta_para_mejorar(screen, clock, estado)
        lado = campana.mejorar_carta(estado, idx)
        mensaje = f"{estado['cartas'][idx]['nombre']} sube su {lado.upper()} a {estado['cartas'][idx][lado]}"
    elif clave == "recluta":
        carta = await draft(screen, clock, estado)
        idx = await draft_reemplazo(screen, clock, estado, carta)
        campana.draft_reemplazo(estado, carta, idx)
        mensaje = f"{carta.nombre} entra en el mazo en lugar de otra carta"
    elif clave == "sigilo":
        campana.aplicar_sigilo(estado)
        mensaje = "Todas tus cartas suben su lado mas bajo"
    elif clave == "aliado":
        f = campana.sustituto_aliado(estado)
        if f and campana.desbloquear_aliado(estado, f):
            mensaje = f"Pacto con {facciones.nombre(f)}: sus cartas entran en el draft"
        else:
            campana.aplicar_sigilo(estado)
            mensaje = "Ya pactaste con todos: obtienes un sigilo de guerra"
    elif clave == "sobre":
        nuevas, mejoradas = campana.abrir_sobre(estado)
        sob = campana.cartas_por_nombre(estado, nuevas + mejoradas)
        await revelar_sobre(screen, clock,
                            [c for c in sob if c.nombre in nuevas],
                            [c for c in sob if c.nombre in mejoradas])
        partes = []
        if nuevas:
            partes.append("nuevas: " + ", ".join(nuevas))
        if mejoradas:
            partes.append("duplicadas (+1): " + ", ".join(mejoradas))
        mensaje = "Sobre abierto: " + ("; ".join(partes) if partes else "vacio")
    else:
        mensaje = "Nada que aplicar"
    campana.guardar(estado)
    await cartel(screen, clock, "RECOMPENSA", mensaje)
    return mensaje


async def revelar_sobre(screen, clock, nuevas, mejoradas):
    """Revelado de un sobre carta a carta. Clic revela, ESC sale.

    `nuevas` y `mejoradas` son listas de Carta (las mejoradas ya dieron +1).
    """
    todas = [(c, True) for c in nuevas] + [(c, False) for c in mejoradas]
    fondo = Fondo("dragon")
    reveladas = 0
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        texto(screen, "SOBRE ABIERTO", 22, DORADO, centro=(ANCHO // 2, 110))
        for i, (carta, _es_nueva) in enumerate(todas):
            x = ANCHO // 2 - len(todas) * 60 + i * 120
            rect = pygame.Rect(x, 250, 104, 144)
            if i < reveladas:
                screen.blit(crt.crear(carta, None), (x, 250))
                etiqueta, color = rareza(carta)
                if etiqueta == "LEGENDARIA":
                    resplandor(screen, rect, DORADO, 150, 3, 8)
                texto(screen, etiqueta, 8, color, centro=(rect.centerx, rect.bottom + 18))
            else:
                screen.blit(crt.dorso(), (x, 250))
            if rect.collidepoint(mouse) and i < reveladas:
                crt.resplandor_carta(screen, rect, carta, None, 80)
        if mejoradas:
            parrafo(screen, "Duplicadas (+1): " + ", ".join(c.nombre for c in mejoradas),
                    9, TEXTO_TENUE, ANCHO // 2 - 300, 440, 600, interlinea=20, centrado=True)
        if reveladas < len(todas):
            texto(screen, f"clic para revelar ({reveladas}/{len(todas)})", 9, TEXTO_TENUE,
                  centro=(ANCHO // 2, ALTO - 120))
        else:
            texto(screen, "clic para continuar", 10, DORADO, centro=(ANCHO // 2, ALTO - 120))
        dibujar_tooltips(screen)
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if reveladas < len(todas):
                    carta = todas[reveladas][0]
                    audio.sfx(audio.TORNEO if rareza(carta)[0] == "LEGENDARIA" else audio.RECOMPENSA)
                    reveladas += 1
                else:
                    audio.sfx(audio.MENU_OK)
                    return


async def cartel(screen, clock, titulo, mensaje):
    """Pantalla corta de confirmacion."""
    fondo = Fondo("dragon")
    while True:
        clock.tick(LIMIT_FPS)
        await asyncio.sleep(0)
        fondo.dibujar(screen)
        texto(screen, titulo, 20, DORADO, centro=(ANCHO // 2, ALTO // 2 - 40))
        parrafo(screen, mensaje, 11, TEXTO, ANCHO // 2 - 320, ALTO // 2 + 10, 640,
                interlinea=26, centrado=True)
        texto(screen, "clic para continuar", 9, TEXTO_TENUE, centro=(ANCHO // 2, ALTO - 90))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                audio.sfx(audio.MENU_OK)
                return


def _imagen_encuentro(enc_id):
    """La ilustracion de un encuentro, o None si todavia no se genero.

    Vive en `assets/escenas/<id>.png`. Si falta, la pantalla cae al diseno de
    antes (solo texto): el juego nunca debe romperse por falta de arte.
    """
    ruta = os.path.join("assets", "escenas", f"{enc_id}.png")
    try:
        if not os.path.exists(ruta):
            return None
        img = crt.REC.imagen(ruta)
        return img if img.get_width() > 32 else None
    except Exception:  # noqa: BLE001 - el arte faltante no puede tumbar la pantalla
        return None


async def decision_narrativa(screen, clock, estado, decision):
    """Decision moral antes de un duelo: dos caminos, consecuencias reales.

    A diferencia de `encuentro` (que da recompensas), aqui la decision no
    regala nada: cambia la confianza de Nara y lo que el jugador sabe del
    Umbral. Se registra una sola vez por partida.
    """
    opciones = decision["opciones"]
    t0 = time.time()
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo = campana.nodo(estado.get("nodo") or "senda").get("escena", "camino")
        _fondo_escena(screen, fondo)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, decision["id"].replace("_", " ").upper(), 18, DORADO,
              centro=(ANCHO // 2, 90))
        parrafo(screen, decision["pregunta"], 10, TEXTO, ANCHO // 2 - 430, 160, 860,
                interlinea=24, centrado=True)

        rects = []
        for i, op in enumerate(opciones):
            rect = pygame.Rect(ANCHO // 2 - 340 + i * 360, 340, 320, 150)
            rects.append(rect)
            hover = rect.collidepoint(mouse)
            panel(screen, rect, (20, 20, 30, 235),
                  facciones.acento(estado["faccion"]) if hover else BORDE,
                  radio=12, grosor=3 if hover else 2)
            parrafo(screen, op["texto"], 9, TEXTO, rect.x + 20, rect.y + 46,
                    rect.w - 40, interlinea=20, centrado=True)
        texto(screen, "elegir cambia lo que Nara cree de vos", 9, TEXTO_TENUE,
              centro=(ANCHO // 2, 545))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        op = opciones[i]
                        audio.sfx(audio.MENU_OK)
                        campana.decidir(estado, decision["id"], op["efecto"])
                        campana.guardar(estado)
                        await cartel(screen, clock,
                                     "DECISION: " + op["id"].upper(),
                                     op["respuesta"])
                        return


# ---------------------------------------------------------------- encuentro
def _fondo_escena(screen, nombre):
    """Fondo de cinemática (oscurecido), para momentos narrativos.

    Usa el fondo y las capas cacheadas: escalar a pantalla completa en cada
    frame era lo que mas memoria consumia.
    """
    ruta = f"assets/fondos/{nombre}.png"
    if crt.REC.imagen(ruta).get_width() > 32:
        screen.blit(REC.fondo_pantalla(ruta), (0, 0))
        screen.blit(REC.capa_oscurita((6, 7, 14, 186)), (0, 0))
        screen.blit(REC.vineta(), (0, 0))
        return
    Fondo("dragon").dibujar(screen)


async def encuentro(screen, clock, estado, nodo_id, enc_id=None):
    """Encuentro narrativo con dos opciones y consecuencias reales.

    Antes de las opciones se reproduce la voz del NPC (`encuentros.escena_antes`):
    como se presenta y que dice al ver tu mazo. Al elegir, ademas del efecto
    mecanico, se registra la revelacion que aporta el encuentro.
    """
    enc = campana.encuentro_para(nodo_id, enc_id)
    escenas = encuentros.escena_antes(enc["id"], estado.get("faccion", ""))
    if escenas:
        await cinematicas.reproducir(screen, clock, escenas,
                                     musica=audio.musica_de_menu(),
                                     permitir_saltar=True)
    opciones = enc["opciones"]
    t0 = time.time()
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        _fondo_escena(screen, enc.get("escena", "campamento"))
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, enc["titulo"].upper(), 18, DORADO, centro=(ANCHO // 2, 110))

        # Con ilustracion el diseno es de dos columnas: la escena a la izquierda
        # y el texto y las opciones a la derecha. Sin ella, el de antes.
        img_enc = _imagen_encuentro(enc["id"])
        rects = []
        if img_enc is not None:
            marco = pygame.Rect(64, 168, 512, 384)
            escala = min(marco.w / img_enc.get_width(),
                         marco.h / img_enc.get_height())
            w = int(img_enc.get_width() * escala)
            h = int(img_enc.get_height() * escala)
            dibujo = crt.REC.escalar(img_enc, (w, h)) if hasattr(crt.REC, "escalar")                 else pygame.transform.smoothscale(img_enc, (w, h))
            screen.blit(dibujo, (marco.x, marco.y))
            pygame.draw.rect(screen, facciones.acento(estado["faccion"]),
                             marco, 3, border_radius=8)
            parrafo(screen, enc["texto"], 10, TEXTO, 620, 180, 580,
                    interlinea=24)
            for i, op in enumerate(opciones):
                rect = pygame.Rect(620, 300 + i * 150, 600, 128)
                rects.append(rect)
                hover = rect.collidepoint(mouse)
                panel(screen, rect, (20, 20, 30, 235),
                      facciones.acento(estado["faccion"]) if hover else BORDE,
                      radio=12, grosor=3 if hover else 2)
                texto(screen, op["id"].upper(), 10, DORADO,
                      centro=(rect.centerx, rect.y + 32))
                parrafo(screen, op["texto"], 8, TEXTO, rect.x + 20, rect.y + 62,
                        rect.w - 40, interlinea=18, centrado=True)
            texto(screen, "clic en la opcion que elijas", 9, TEXTO_TENUE,
                  centro=(920, 630))
        else:
            parrafo(screen, enc["texto"], 10, TEXTO, ANCHO // 2 - 420, 170, 840,
                    interlinea=24, centrado=True)
            for i, op in enumerate(opciones):
                rect = pygame.Rect(ANCHO // 2 - 340 + i * 360, 330, 320, 170)
                rects.append(rect)
                hover = rect.collidepoint(mouse)
                panel(screen, rect, (20, 20, 30, 235),
                      facciones.acento(estado["faccion"]) if hover else BORDE,
                      radio=12, grosor=3 if hover else 2)
                texto(screen, op["id"].upper(), 10, DORADO,
                      centro=(rect.centerx, rect.y + 34))
                parrafo(screen, op["texto"], 8, TEXTO, rect.x + 20, rect.y + 70,
                        rect.w - 40, interlinea=18, centrado=True)
            texto(screen, "clic en la opcion que elijas", 9, TEXTO_TENUE,
                  centro=(ANCHO // 2, 540))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        audio.sfx(audio.MENU_OK)
                        titulo, texto_efecto = campana.aplicar_encuentro(estado, opciones[i]["efecto"])
                        campana.guardar(estado)
                        await cartel(screen, clock, titulo, texto_efecto)
                        # El encuentro ademas revela: la recompensa es una parte,
                        # la informacion es la otra.
                        revelacion = campana.revelar_encuentro(estado, enc["id"])
                        if revelacion:
                            await cartel(screen, clock,
                                         "REVELACION: " + revelacion["titulo"].upper(),
                                         revelacion["linea"])
                        return


# ---------------------------------------------------------------- coleccion
async def _ficha_carta(screen, clock, carta):
    """Ficha ampliada de una carta de la coleccion. Clic o ESC para volver."""
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, 190))
        screen.blit(capa, (0, 0))
        sup = crt.crear(carta, None, escala=1.6)
        screen.blit(sup, (ANCHO // 2 - 330, 240))
        caja = pygame.Rect(ANCHO // 2 - 140, 240, 400, 230)
        panel(screen, caja, PANEL, facciones.acento(carta.bando), radio=10)
        texto(screen, carta.nombre, 13, TEXTO_ON, centro=(caja.centerx, caja.y + 30))
        etiqueta, color = rareza(carta)
        texto(screen, f"{facciones.nombre(carta.bando)} - {etiqueta}", 9, color,
              centro=(caja.centerx, caja.y + 58))
        texto(screen, f"N {val(carta.valores['N'])}   S {val(carta.valores['S'])}", 10,
              TEXTO, centro=(caja.centerx, caja.y + 92))
        texto(screen, f"E {val(carta.valores['E'])}   O {val(carta.valores['O'])}", 10,
              TEXTO, centro=(caja.centerx, caja.y + 116))
        if carta.habilidad:
            parrafo(screen,
                    f"{crt.ICONO_HABILIDAD.get(carta.habilidad, '')}: "
                    f"{crt.descripcion_habilidad(carta.habilidad)}",
                    9, TEXTO, caja.x + 20, caja.y + 142, caja.w - 40, interlinea=16)
        else:
            texto(screen, "Sin habilidad especial", 9, TEXTO_TENUE,
                  centro=(caja.centerx, caja.y + 150))
        texto(screen, "Sale en sobres y en el draft", 8, TEXTO_TENUE,
              centro=(caja.centerx, caja.bottom - 18))
        texto(screen, "clic o ESC para volver", 9, DORADO, centro=(ANCHO // 2, 540))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                audio.sfx(audio.MENU_OK)
                return


async def coleccion(screen, clock, estado=None):
    """Mazos, cartas y finales desbloqueados."""
    perfil = campana.cargar_perfil()
    orden = facciones.orden_facciones()
    faccion = estado.get("faccion") if estado else orden[0]
    t0 = time.time()
    fondos = {f: Fondo(f) for f in orden}
    pagina, fhab, frar = 0, None, None
    HABS = [None, "muro", "furia", "embestida", "quema"]
    RARS = [None, "COMUN", "RARA", "LEGENDARIA"]
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondos[faccion].dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, "COLECCION", 22, DORADO, centro=(ANCHO // 2, 60))
        # El progreso ya no se mide en cartas: se mide en historias. Es el
        # cambio de fondo del compendio dual.
        if estado:
            descubiertas, total_historias = campana.compendio_progreso(estado)
            texto(screen, f"{descubiertas}/{total_historias} historias descubiertas",
                  9, DORADO, centro=(ANCHO // 2, 84))
        else:
            texto(screen, f"0/{compendio.total()} historias descubiertas", 9,
                  TEXTO_TENUE, centro=(ANCHO // 2, 84))
        # selector de faccion
        rects = {}
        compacta = len(orden) > 7
        for i, f in enumerate(orden):
            if compacta:
                x = 40 + i * 120
                rect = pygame.Rect(x, 100, 112, 84)
            else:
                x = 60 + i * 170
                rect = pygame.Rect(x, 100, 150, 70)
            rects[f] = rect
            activo = f == faccion
            panel(screen, rect, (18, 19, 28, 225),
                  facciones.acento(f) if activo else BORDE, radio=8, grosor=2 if activo else 1)
            if compacta:
                lineas = envolver(facciones.nombre(f), 7, rect.w - 12)[:2]
                ly = rect.y + 12
                for linea in lineas:
                    texto(screen, linea, 7, facciones.acento(f),
                          centro=(rect.centerx, ly))
                    ly += 13
            else:
                texto(screen, facciones.nombre(f), 8, facciones.acento(f), centro=(rect.centerx, rect.y + 24))
            finales = perfil.get("finales", {}).get(f, [])
            texto(screen, f"{len(finales)}/3 finales", 7, TEXTO_TENUE,
                  centro=(rect.centerx, rect.bottom - 14))
            if activo:
                resplandor(screen, rect, facciones.acento(f), int(60 + 40 * math_seno(t * 3)), 2, 8)

        # mazo de la faccion: 10 por pagina, con filtros de habilidad y rareza
        filtradas = filtrar_coleccion(mazos.TODOS[faccion], fhab, frar)
        pagina_items, total_pags, pagina = paginar_coleccion(filtradas, pagina)
        rects_cartas = []
        for i, carta in enumerate(pagina_items):
            sup = crt.crear(carta, None, escala=1.1)
            fila, col = divmod(i, 5)
            x = 70 + col * 158
            y = 200 + fila * 192
            rect = pygame.Rect(x, y, sup.get_width(), sup.get_height())
            rects_cartas.append((carta, rect))
            if rect.collidepoint(mouse):
                crt.resplandor_carta(screen, rect, carta, None, 120)
                tooltip(screen, _descripcion_carta(carta, estado), (rect.centerx, rect.y),
                        ancho=300, arriba=True)
            screen.blit(sup, (rect.x, rect.y))
            etiqueta, color = rareza(carta)
            texto(screen, etiqueta, 8, color, centro=(rect.centerx, rect.bottom + 18))
        if not pagina_items:
            texto(screen, "Sin cartas con ese filtro", 10, TEXTO_TENUE,
                  centro=(460, 380))
        b_hab = Boton(pygame.Rect(310, 574, 190, 32), f"HAB: {(fhab or 'TODAS').upper()}", 8)
        b_rar = Boton(pygame.Rect(510, 574, 190, 32), f"RAREZA: {frar or 'TODAS'}", 8)
        b_prev = Boton(pygame.Rect(710, 574, 56, 32), "<", 10)
        b_next = Boton(pygame.Rect(862, 574, 56, 32), ">", 10)
        _botones(screen, [b_hab, b_rar, b_prev, b_next], mouse, dt)
        texto(screen, f"{pagina + 1}/{total_pags}", 9, TEXTO, centro=(814, 590))

        # panel de finales: solo entran las que caben; el resto se resume
        alturas = []
        for f in orden:
            conseguidos = perfil.get("finales", {}).get(f, [])
            titulos = [
                campana.FINALES[f][v]["titulo"]
                for v in ("dominio", "equilibrio", "caos")
                if v in conseguidos
            ]
            h = 22 + 8
            if titulos:
                lineas_t = envolver(" / ".join(titulos), 7, 300)
                h += 14 * max(1, len(lineas_t))
            alturas.append((f, conseguidos, titulos, h))
        tope = ALTO - 200 - 96
        visibles, usado = [], 0
        for entrada in alturas:
            if usado + entrada[3] + 60 > tope - 22:
                break
            visibles.append(entrada)
            usado += entrada[3]
        resto = len(alturas) - len(visibles)
        if resto:
            usado += 22
        alto_panel = max(120, usado + 60)
        panel(screen, pygame.Rect(ANCHO - 380, 200, 340, alto_panel), PANEL, BORDE, radio=10)
        texto(screen, "FINALES", 12, DORADO, centro=(ANCHO - 210, 226))
        y = 250
        for f, conseguidos, titulos, _h in visibles:
            color = facciones.acento(f) if conseguidos else (90, 90, 96)
            texto(screen, facciones.nombre(f), 9, color, x=ANCHO - 360, y=y)
            marcas = []
            for variante in ("dominio", "equilibrio", "caos"):
                marcas.append("[X]" if variante in conseguidos else "[ ]")
            # marcas alineadas al margen derecho interior del panel
            ancho_marcas = REC.fuente(8).render("  ".join(marcas), True, TEXTO_TENUE).get_width()
            texto(screen, "  ".join(marcas), 8, TEXTO_TENUE,
                  x=ANCHO - 380 + 340 - 20 - ancho_marcas, y=y)
            y += 22
            if titulos:
                y = parrafo(screen, " / ".join(titulos), 7, TEXTO_TENUE,
                            ANCHO - 360, y, 300, interlinea=14)
            y += 8
        if resto:
            texto(screen, f"+{resto} finales mas", 8, TEXTO_TENUE,
                  centro=(ANCHO - 210, y + 6))

        # estadisticas
        panel(screen, pygame.Rect(60, 620, 500, 140), PANEL, BORDE, radio=10)
        texto(screen, "ESTADISTICAS", 11, DORADO, x=80, y=640)
        texto(screen, f"Duelos: {perfil.get('duelos', 0)}   Victorias: {perfil.get('victorias', 0)}   Moneda: {perfil.get('moneda', 0)}",
              9, TEXTO, x=80, y=668)
        mejor = perfil.get("mejor_racha", {})
        if mejor:
            texto(screen, "Mejor racha por faccion:", 8, TEXTO_TENUE, x=80, y=694)
            con_racha = [f for f in orden if f in mejor]
            for i, f in enumerate(con_racha):
                fila, col = divmod(i, 5)
                texto(screen, f"{facciones.corto(f)}: {mejor[f]}", 8,
                      facciones.acento(f), x=80 + col * 95, y=712 + fila * 18)

        cerrar = Boton(pygame.Rect(ANCHO - 300, ALTO - 70, 260, 46), "VOLVER", 11)
        tienda_btn = Boton(pygame.Rect(60, ALTO - 70, 260, 46), "TIENDA", 11,
                           sub=f"Sobres: {campana.PRECIO_SOBRE} moneda")
        _botones(screen, [cerrar, tienda_btn], mouse, dt)
        dibujar_tooltips(screen)
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_LEFT:
                pagina -= 1
                audio.sfx(audio.MENU_MOVE)
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RIGHT:
                pagina += 1
                audio.sfx(audio.MENU_MOVE)
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_f:
                fhab = HABS[(HABS.index(fhab) + 1) % len(HABS)]
                pagina = 0
                audio.sfx(audio.MENU_MOVE)
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                frar = RARS[(RARS.index(frar) + 1) % len(RARS)]
                pagina = 0
                audio.sfx(audio.MENU_MOVE)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if b_hab.clic(ev.pos):
                    fhab = HABS[(HABS.index(fhab) + 1) % len(HABS)]
                    pagina = 0
                    audio.sfx(audio.MENU_OK)
                elif b_rar.clic(ev.pos):
                    frar = RARS[(RARS.index(frar) + 1) % len(RARS)]
                    pagina = 0
                    audio.sfx(audio.MENU_OK)
                elif b_prev.clic(ev.pos):
                    pagina -= 1
                    audio.sfx(audio.MENU_MOVE)
                elif b_next.clic(ev.pos):
                    pagina += 1
                    audio.sfx(audio.MENU_MOVE)
                    continue
                for carta, rect in rects_cartas:
                    if rect.collidepoint(ev.pos):
                        audio.sfx(audio.CARD)
                        await _ficha_carta(screen, clock, carta)
                        break
                for f, rect in rects.items():
                    if rect.collidepoint(ev.pos):
                        faccion = f
                        pagina = 0
                        audio.sfx(audio.CARD)
                        break
                if cerrar.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    return
                if tienda_btn.clic(ev.pos):
                    audio.sfx(audio.MENU_OK)
                    await tienda(screen, clock, estado)
                    continue


# ----------------------------------------------------------------- ajustes
async def ajustes(screen, clock):
    """Volumen de efectos y musica, pantalla completa y una mano de ayuda.

    Devuelve un dict con los ajustes cambiados para que main los aplique.
    """
    sfx = audio.volumen_sfx()
    musica = audio.volumen_musica()
    fullscreen = bool(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
    fondo = Fondo("elfo")
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()

        texto(screen, "AJUSTES", 24, DORADO, centro=(ANCHO // 2, 96))
        sfx_rect = pygame.Rect(ANCHO // 2 - 300, 240, 600, 36)
        mus_rect = pygame.Rect(ANCHO // 2 - 300, 312, 600, 36)
        texto(screen, "EFECTOS", 11, TEXTO, x=ANCHO // 2 - 300, y=212)
        texto(screen, "MUSICA", 11, TEXTO, x=ANCHO // 2 - 300, y=284)
        for rect, valor in ((sfx_rect, sfx), (mus_rect, musica)):
            pygame.draw.rect(screen, (18, 19, 28), rect, border_radius=8)
            pygame.draw.rect(screen, BORDE, rect, 2, border_radius=8)
            relleno = pygame.Rect(rect.x, rect.y, int(rect.w * valor), rect.h)
            pygame.draw.rect(screen, facciones.acento("elfo"), relleno, border_radius=8)
            pygame.draw.circle(screen, DORADO, (rect.x + int(rect.w * valor), rect.centery), 10)
        texto(screen, f"{int(sfx * 100)}%", 10, TEXTO, x=ANCHO // 2 + 316, y=sfx_rect.centery - 6)
        texto(screen, f"{int(musica * 100)}%", 10, TEXTO, x=ANCHO // 2 + 316, y=mus_rect.centery - 6)

        pantalla_btn = Boton(pygame.Rect(ANCHO // 2 - 300, 386, 600, 44),
                             "PANTALLA COMPLETA: " + ("SI" if fullscreen else "NO"), 11)
        ayuda = Boton(pygame.Rect(ANCHO // 2 - 300, 442, 600, 44), "CONTROLES", 11)
        cerrar = Boton(pygame.Rect(ANCHO // 2 - 130, 510, 260, 50), "VOLVER", 12)
        botones = [pantalla_btn, ayuda, cerrar]
        _botones(screen, botones, mouse, dt)
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return {"fullscreen": fullscreen, "sfx": sfx, "musica": musica}
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if sfx_rect.collidepoint(ev.pos):
                    sfx = max(0.0, min(1.0, (ev.pos[0] - sfx_rect.x) / sfx_rect.w))
                    audio.volumen_sfx(sfx)
                    audio.sfx(audio.MENU_MOVE)
                elif mus_rect.collidepoint(ev.pos):
                    musica = max(0.0, min(1.0, (ev.pos[0] - mus_rect.x) / mus_rect.w))
                    audio.volumen_musica(musica)
                    audio.sfx(audio.MENU_MOVE)
                elif pantalla_btn.clic(ev.pos):
                    fullscreen = not fullscreen
                    pantalla_btn.etiqueta = "PANTALLA COMPLETA: " + ("SI" if fullscreen else "NO")
                    audio.sfx(audio.MENU_OK)
                elif ayuda.clic(ev.pos):
                    audio.sfx(audio.MENU_OK)
                    await _pantalla_ayuda(screen, clock)
                elif cerrar.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    return {"fullscreen": fullscreen, "sfx": sfx, "musica": musica}


async def _pantalla_ayuda(screen, clock):
    """Resumen de controles y reglas, para no obligar al manual."""
    paginas = [
        ("CONTROLES", [
            "Raton: arrastra una carta de la mano al tablero.",
            "Raton sobre una carta: la levanta y muestra la mejor casilla.",
            "Clic: continuar en las cinematicallyas y los menus.",
            "ESC: pausa dentro del duelo, cerrar una pantalla.",
            "Flechas y ENTER: moverse por los menus.",
            "H: recordatorio de Same y Plus.",
            "T: abrir el tutorial completo.",
        ]),
        ("REGLAS QUE CUENTAN", [
            "Basica: ganas la carta vecina si tu lado es mayor.",
            "Same: dos vecinos con el mismo valor Capture.",
            "Plus: dos comparaciones con la misma suma capturan.",
            "Cadena: una carta capturada sigue capturando.",
            "Muro: su mejor lado no puede caer.",
            "Furia: +1 a cada lado si toca una carta amiga.",
            "Embestida: +2 en la casilla central.",
            "Sinergia: 3+ cartas de tu bando dan +1 a todo.",
            "Empatar cuenta como ganar el duelo.",
        ]),
    ]
    indice = 0
    while True:
        clock.tick(LIMIT_FPS)
        await asyncio.sleep(0)
        fondo = Fondo("elfo")
        fondo.dibujar(screen)
        titulo, lineas = paginas[indice]
        texto(screen, titulo, 20, DORADO, centro=(ANCHO // 2, 150))
        y = 230
        for linea in lineas:
            texto(screen, linea, 10, TEXTO, centro=(ANCHO // 2, y))
            y += 34
        texto(screen, f"pagina {indice + 1} de {len(paginas)}   -   clic para passar",
              9, TEXTO_TENUE, centro=(ANCHO // 2, ALTO - 120))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_t:
                import tutorial as _tut

                audio.sfx(audio.MENU_OK)
                await _tut.tutorial(screen, clock)
                return
            if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                audio.sfx(audio.MENU_MOVE)
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return
                indice = (indice + 1) % len(paginas)
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_RETURN and indice == 0:
                    return


async def pantalla_error(screen, clock, exc, traza, contexto=""):
    """Muestra un error inesperado en la ventana en vez de cerrar el proceso.

    Antes el juego escribia crash.log y se cerraba de golpe: si algo fallaba,
    el jugador solo veía la ventana desaparecer sin saber por que.
    """
    from paths import log_errores

    detalle = f"{type(exc).__name__}: {exc}"
    try:
        with open(log_errores(), "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 70 + "\n")
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {detalle}\n")
            if contexto:
                f.write(f"contexto: {contexto}\n")
            f.write(traza + "\n")
    except OSError:
        pass

    clock = clock or type("R", (), {"tick": staticmethod(lambda f=60: 16)})()
    while True:
        clock.tick(LIMIT_FPS)
        await asyncio.sleep(0)
        screen.fill((24, 14, 16))
        # marco
        marco = pygame.Rect(120, 120, ANCHO - 240, ALTO - 240)
        panel(screen, marco, (34, 20, 24, 250), ROJO, radio=10, grosor=3)
        texto(screen, "ALGO HA FALLADO", 22, ROJO, centro=(ANCHO // 2, marco.y + 44))
        parrafo(screen,
                "El juego se ha detenido por un error inesperado. No se ha perdido "
                "tu partida: esta guardada y podras continuar al salir.",
                9, TEXTO, marco.x + 40, marco.y + 90, marco.w - 80, interlinea=20,
                centrado=True)
        parrafo(screen, detalle, 10, DORADO, marco.x + 40, marco.y + 170, marco.w - 80,
                interlinea=20, centrado=True)
        if contexto:
            parrafo(screen, f"Cosa: {contexto}", 8, TEXTO_TENUE, marco.x + 40,
                    marco.y + 230, marco.w - 80, interlinea=16, centrado=True)
        parrafo(screen, "La informacion tecnica esta en crash.log", 8, TEXTO_TENUE,
                marco.x + 40, marco.bottom - 130, marco.w - 80, interlinea=16,
                centrado=True)
        # ultimas lineas de la traza
        lineas = [l for l in traza.strip().splitlines() if l.strip()][-3:]
        y = marco.bottom - 104
        for linea in lineas:
            texto(screen, linea.strip()[:88], 7, (150, 130, 130), centro=(ANCHO // 2, y))
            y += 14
        texto(screen, "clic o ENTER para volver al menu", 10, DORADO,
              centro=(ANCHO // 2, marco.bottom - 34))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                audio.sfx(audio.MENU_OK)
                return


# ------------------------------------------------------------------- derrota
async def derrota(screen, clock, estado):
    """Opciones tras perder un duelo de campana."""
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo = Fondo(estado.get("faccion", "goblin"))
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        texto(screen, "EL DUELO SE TE ESCAPA", 20, ROJO, centro=(ANCHO // 2, 220))
        texto(screen,
              f"Tu racha se rompe. Duelos ganados: {estado.get('victorias', 0)}  -  "
              f"Reintentos: {estado.get('derrotas', 0)}",
              10, TEXTO_TENUE, centro=(ANCHO // 2, 262))
        reintentar = Boton(pygame.Rect(ANCHO // 2 - 320, 340, 300, 52), "REINTENTAR DUELO", 12,
                           acento=facciones.acento(estado.get("faccion", "goblin")))
        mapa = Boton(pygame.Rect(ANCHO // 2 + 20, 340, 300, 52), "VOLVER AL MAPA", 12)
        salir = Boton(pygame.Rect(ANCHO // 2 - 150, 410, 300, 46), "GUARDAR Y SALIR", 11)
        _botones(screen, [reintentar, mapa, salir], mouse, dt)
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return "salir"
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if reintentar.clic(ev.pos):
                    return "reintentar"
                if mapa.clic(ev.pos):
                    return "mapa"
                if salir.clic(ev.pos):
                    campana.guardar(estado)
                    return "salir"


# ------------------------------------------------------------------- final
async def epilogo(screen, clock, estado):
    """Carta de final + cinematica + resumen de la partida."""
    campana.completar(estado)
    variante, titulo, lineas = campana.final_de(estado)
    faccion = estado["faccion"]
    resumen = [
        f"Faccion: {facciones.nombre(faccion)}",
        f"Duelos ganados: {estado.get('victorias', 0)}",
        f"Mejor racha: {estado.get('mejor_racha', 0)}",
        f"Capturas totales: {estado.get('capturas', 0)}",
    ]
    pactos = f"Pactos: {', '.join(facciones.nombre(a) for a in estado.get('aliados', [])) or 'ninguno'}"
    escenas, musica = cinematicas.escenas_final(titulo, lineas, faccion, resumen)
    audio.musica(musica)
    await cinematicas.reproducir(screen, clock, escenas, musica=musica, permitir_saltar=False)

    # El final del mundo fantastic no es el final de la historia: despues
    # se abre el Umbral y el duelista vuelve a nuestro mundo. Esa segunda
    # parte es comun a las diez facciones (ver finales.py).
    await cinematicas.reproducir(
        screen, clock, finales.escenas_umbral(variante),
        musica=finales.musica_umbral(variante), permitir_saltar=False)

    # Y el epilogo, que es donde se descubre que volver no lo salvo.
    await cinematicas.reproducir(
        screen, clock, finales.escenas_epilogo(variante),
        musica=finales.musica_epilogo(variante), permitir_saltar=False)

    nuevo = (estado.get("final") or {}).get("nuevo")
    # volver al menu tras el final
    while True:
        clock.tick(LIMIT_FPS)
        await asyncio.sleep(0)
        fondo = Fondo(faccion)
        fondo.dibujar(screen)
        texto(screen, "FIN DE LA CAMPAÑA", 22, DORADO, centro=(ANCHO // 2, 200))
        texto(screen, titulo, 14, facciones.acento(faccion), centro=(ANCHO // 2, 240))
        y = 300
        for linea in resumen:
            texto(screen, linea, 10, TEXTO, centro=(ANCHO // 2, y))
            y += 26
        y = parrafo(screen, pactos, 10, TEXTO, ANCHO // 2 - 400, y, 800,
                    interlinea=26, centrado=True)
        if nuevo:
            texto(screen, "NUEVO FINAL DESBLOQUEADO", 12, VERDE, centro=(ANCHO // 2, y + 30))
        else:
            texto(screen, "Final ya visto. Prueba con otra faccion o improves tu juego.",
                  9, TEXTO_TENUE, centro=(ANCHO // 2, y + 30))
        texto(screen, "clic para volver al menu", 10, DORADO, centro=(ANCHO // 2, ALTO - 120))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                audio.sfx(audio.MENU_OK)
                return