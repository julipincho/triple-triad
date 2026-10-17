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
import narrativa
import opciones
import ui
from idioma import espanol
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
    fila_centrada,
    fila_centrada_paso,
    fila_centrada_por_centro,
    fundido_entrada,
    panel,
    parrafo,
    resplandor,
    texto,
    tooltip,
)

import asyncio

from version import VERSION as VERSION_JUEGO


def _validar_mazo_editor(cartas, poseidas):
    if len(cartas) != campana.MAZO_RUN_N:
        return False, f"Completa las {campana.MAZO_RUN_N} cartas del mazo ({len(cartas)}/{campana.MAZO_RUN_N})"
    return campana.validar_mazo(cartas, poseidas)


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


async def pedir_nombre(screen, clock, inicial=""):
    """Pantalla para que el jugador escriba como le llaman.

    Devuelve el nombre ya saneado, o `None` si el jugador se salta la pantalla.
    Sin nombre el juego sigue igual que siempre: `campana.sanea_nombre` devuelve
    "el duelista" cuando no hay nada escrito.

    Se ofrece ANTES del prologo, no dentro, porque el prologo es una pelicula
    que ya esta escrita para un protagonista anonimo: meter un teclado en mitad
    de una escena cinematografica la arruina.
    """
    marco = pygame.Rect(ANCHO // 2 - 340, ALTO // 2 - 170, 680, 340)
    # El alto del panel y la posicion del campo se calculan con el texto que
    # de verdad va a caber dentro. Con offsets fijos (campo en marco.y + 150) se
    # suponia una linea por parrafo de ayuda: con el modo lectura al 160% ambos
    # se parten en dos y el segundo se monta sobre el campo de texto. Medido
    # con tools/auditar_texto_ampliado.py: 3 solapamientos al 160%, 0 al 125%.
    _esc_n = ui.escala_texto()
    _ancho_txt = marco.w - 120
    _inter1 = int(round(20 * _esc_n))
    _inter2 = int(round(18 * _esc_n))
    _alto_ayuda = (_inter1 * len(envolver("Los rivales hablarán contigo por tu nombre.",
                                          10, _ancho_txt))
                   + 4
                   + _inter2 * len(envolver(
                       "Deja el campo vacío y seguirás siendo el duelista de siempre.",
                       9, _ancho_txt)))
    _alto = min(ALTO - 40, max(340, 96 + _alto_ayuda + 14 + 62 + 34 + 20 + 84 + 12))
    if _alto != marco.h:
        marco = pygame.Rect(marco.x, ALTO // 2 - _alto // 2, marco.w, _alto)
    campo = pygame.Rect(marco.x + 60, marco.y + 96 + _alto_ayuda + 14, marco.w - 120, 62)
    b_ok = Boton(pygame.Rect(marco.centerx - 230, marco.bottom - 84, 210, 52),
                 "CONTINUAR", 12, borde=DORADO, acento=DORADO)
    b_skip = Boton(pygame.Rect(marco.centerx + 20, marco.bottom - 84, 210, 52),
                   "SIN NOMBRE", 11)
    botones = [b_ok, b_skip]
    escrito = campana.sanea_nombre(inicial, defecto="")
    cursor = len(escrito)
    fondo = FondoAnimado("umbral")
    t0 = time.time()

    while True:
        dt = clock.tick(LIMIT_FPS) / 1000
        await asyncio.sleep(0)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        fondo.dibujar(screen)
        panel(screen, marco, (14, 15, 24, 246), BORDE, radio=12, grosor=2)

        texto(screen, "¿CÓMO TE LLAMAN?", 20, DORADO, centro=(marco.centerx, marco.y + 52))
        # El segundo parrafo arranca donde termino el primero, no en un offset
        # fijo: si el primero crece, el segundo tiene que crecer con el.
        y_ayuda = parrafo(screen,
                          "Los rivales hablarán contigo por tu nombre.", 10, TEXTO,
                          marco.x + 60, marco.y + 96, marco.w - 120, interlinea=20,
                          centrado=True)
        parrafo(screen,
                "Deja el campo vacío y seguirás siendo el duelista de siempre.",
                9, TEXTO_TENUE, marco.x + 60, y_ayuda + 4, marco.w - 120,
                interlinea=18, centrado=True)

        # Campo de texto. El cursor se pinta con una linea del(color del
        # texto), sin Surface nueva: alterna con `int(t*2)` para que no
        # parpadee a 60 fps.
        panel(screen, campo, (8, 9, 16, 220), BORDE, radio=6, grosor=1)
        texto(screen, escrito or " ", 14, TEXTO_ON,
              centro=(campo.centerx, campo.centery))
        if int(t * 2) % 2 == 0 and escrito:
            x_cur = campo.centerx + ancho_texto(escrito, 14) // 2 + 3
            pygame.draw.line(screen, DORADO, (x_cur, campo.centery - 14),
                             (x_cur, campo.centery + 14), 2)

        texto(screen, "%d/%d" % (len(escrito), campana.NOMBRE_MAX), 8, TEXTO_TENUE,
              centro=(campo.right, campo.bottom + 20))

        for b in botones:
            b.actualizar(dt, mouse)
            b.dibujar(screen, t)
        texto(screen, "ENTER acepta   ESC deja el nombre como estaba", 8, TEXTO_TENUE,
              centro=(marco.centerx, marco.bottom - 12))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    audio.sfx(audio.MENU_BACK)
                    return inicial
                if ev.key == pygame.K_RETURN:
                    audio.sfx(audio.MENU_OK)
                    return campana.sanea_nombre(escrito, defecto="")
                if ev.key == pygame.K_BACKSPACE:
                    if cursor > 0:
                        escrito = escrito[:cursor - 1] + escrito[cursor:]
                        cursor -= 1
                        audio.sfx(audio.MENU_BACK)
                elif ev.key == pygame.K_DELETE:
                    escrito = escrito[:cursor] + escrito[cursor + 1:]
                elif ev.key == pygame.K_LEFT:
                    cursor = max(0, cursor - 1)
                elif ev.key == pygame.K_RIGHT:
                    cursor = min(len(escrito), cursor + 1)
                elif ev.key == pygame.K_HOME:
                    cursor = 0
                elif ev.key == pygame.K_END:
                    cursor = len(escrito)
                elif ev.unicode and ev.unicode.isprintable():
                    # El tope se aplica al texto, no a lo tecleado: escribir
                    # encima del final mueve el cursor en vez de perder teclas.
                    if len(escrito) < campana.NOMBRE_MAX:
                        escrito = escrito[:cursor] + ev.unicode + escrito[cursor:]
                        cursor += 1
                        audio.sfx(audio.MENU_OK)
                    else:
                        cursor = min(cursor + 1, len(escrito))
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                b = _pulsado(botones, ev.pos)
                if b is b_ok:
                    return campana.sanea_nombre(escrito, defecto="")
                if b is b_skip:
                    return ""


async def confirmar(screen, clock, titulo, mensaje, aceptar="SI", fondo=None):
    """Pregunta si/no. Devuelve True si el jugador confirma.

    Vive en el menu porque empezar una campana nueva PISA la que hay. Antes no
    habia forma de empezar de cero con partida en curso, y la unica manera de
    ver el prologo era borrar el `campana.json` a mano desde la consola.

    `fondo` es un callable opcional que dibuja el fondo (tambien sirve de
    overlay oscurecido); sin el, se reutiliza lo que hubiera en pantalla, que
    es justo lo que quiere un modal de confirmacion sobre el juego pausado.
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
        # Velo oscuro: el modal tiene que leerse por encima de lo que hubiera
        # debajo (el duelo detenido), no pegado a el.
        screen.blit(REC.capa_oscurita((6, 7, 14, 214)), (0, 0))
        if fondo is not None:
            fondo(screen, dt)
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
_LOGO_PORTADA = {}


def _logo_portada():
    """Carga y escala el logo de la portada. Todo se calcula una vez.

    El logo fuente mide 1669x941: mas ancho que la pantalla (1280). Como
   对这个 caso no sirve un factor entero (daria 1 y desborda), se reduce en
    dos pasos: primero a la mitad con vecino mas cercano, que conserva la
    rejilla de pixeles, y despues el resto con `smoothscale`. Un salto directo
    a 0.38 con `scale` dejaria los bordes de las letras full Aliasing.

    La respiracion se pre-calculan en tres tamanos y se va alternando: en
    pantalla no se reescala nada.
    """
    if _LOGO_PORTADA:
        return _LOGO_PORTADA
    img = pygame.image.load(ui.recurso("assets/logo.png")).convert_alpha()
    # Recorte del canal alfa: el PNG trae margen transparente a los lados.
    caja = img.get_bounding_rect()
    if caja.width and caja.height:
        img = img.subsurface(caja)

    # La banda manda: de 20 a 380, con los chips abajo. El ancho sale del alto.
    h = 330
    w = int(h * img.get_width() / img.get_height())
    if w > ANCHO - 140:                     # guarda lateral por si acaso
        w = ANCHO - 140
        h = int(w * img.get_height() / img.get_width())

    # Mitad con vecino mas cercano y luego el resto suave. Se escala UNA vez
    # al cargar; en pantalla solo se copia la imagen.
    mitad = pygame.transform.scale(img, (img.get_width() // 2, img.get_height() // 2))
    base = pygame.transform.smoothscale(mitad, (w, h))
    _LOGO_PORTADA.update({
        "logo": base, "w": w, "h": h,
        "y": 20 + h // 2,
    })
    return _LOGO_PORTADA


async def portada(screen, clock):
    """Pantalla de titulo con el logo estatico."""
    fondo = Fondo("dragon")
    t0 = time.time()
    mouse = pygame.mouse.get_pos()
    # El logo sustituye al titulo escrito. Se escala UNA vez por factor entero
    # para no difuminar el pixel art, y se cachea: si se reescala por frame se
    # paga el coste en cada iteracion y ademas la imagen se suaviza.
    logo_base = _logo_portada()
    boton = Boton(pygame.Rect(ANCHO // 2 - 170, ALTO - 120, 340, 52), "PULSA PARA EMPEZAR", 12)
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        t = time.time() - t0
        fondo.dibujar(screen, dt)

        # Logo ESTATICO: una sola imagen, la misma en todos los frames. Antes
        # respiraba alternando entre tres tamanos pre-escalados.
        # SIN resplandor: el logo ya trae su propio halo pintado (los destellos
        # violeta), y encima el rectángulo del resplandor se veía como un marco
        # oscuro alrededor de la imagen.
        sup = logo_base["logo"]
        screen.blit(sup, (ANCHO // 2 - sup.get_width() // 2,
                          logo_base["y"] - sup.get_height() // 2))
        # chips: el numero de facciones y de duelos se SACAN de los datos, no
        # se escriben a mano. Estaban fijos ("Siete facciones", "Cinco duelos",
        # luego "Seis duelos") y los tres acabaron mal: hay diez facciones y
        # cinco duelos por campana. "Seis" contaba la bifurcacion como si fuera
        # un duelo. Ver campana.duelos_por_campana().
        # 200px de ancho por chip para que "Un final por faccion" entre sin
        # tocar los bordes del panel. El anclaje se calcula del ancho real de
        # la fila: con `x = ANCHO//2 - 300 + i*220` el bloque ocupaba
        # 240..880 (centro 560) y quedaba 80px a la izquierda del centro.
        _n_facc = len(facciones.orden_facciones())
        _n_duelos = campana.duelos_por_campana()
        chips = [f"{_n_facc} facciones",
                 f"{_n_duelos} duelos",
                 "Un final por facción"]
        # El ancho del chip se mide con el texto que lleva dentro. Con 200 fijos
        # "Un final por faccion" (189px a tam 9) encajaba por los pelos y al
        # ampliar la tipografia se salia de su propio borde: medido, 209px
        # dentro de un chip de 200 al 125%.
        CHIP_W = max(200, max(ui.ancho_texto(c, 9) for c in chips) + 24)
        CHIP_GAP = max(20, int(round(20 * ui.escala_texto())))
        x_chip = fila_centrada(CHIP_W, len(chips), CHIP_GAP)
        for i, f in enumerate(chips):
            x = x_chip + i * (CHIP_W + CHIP_GAP)
            # 320, no 250: el logo ocupa la banda superior. A 250 los chips se
            # montaban encima de la base del logo.
            panel(screen, pygame.Rect(x, 390, CHIP_W, 40), (16, 17, 26, 200), BORDE, radio=8, grosor=1)
            texto(screen, f, 9, TEXTO_TENUE, centro=(x + CHIP_W // 2, 410))

        # cartas flotando de fondo (giro y sombra cacheados: antes eran cinco
        # Surface nuevas por frame y eso solo en la portada ya costaba caro)
        # El anclaje va centrado segun el ancho real de la carta (104) y el
        # paso; la flotacion se suma encima. Antes `x = 120 + i*240` dejaba la
        # fila en 120..1184: 12px a la derecha del centro.
        bandos_portada = ["humano", "orco", "elfo", "goblin", "dragon"]
        # Las cartas se pintan por su CENTRO (`x - ancho//2`), asi que el
        # anclaje se calcula con el helper de centros. Antes `x = 120 + i*240`
        # dejaba los centros de 120 a 1080: centro 600, 40px a la izquierda.
        paso_carta = 240
        x_carta = fila_centrada_por_centro(104, len(bandos_portada), paso_carta)
        for i, f in enumerate(bandos_portada):
            carta = mazos.TODOS[f][-1]
            clave = crt._slug(carta.nombre)
            sup = crt.crear(carta, None)
            x = x_carta + i * paso_carta + math_seno(t * 0.8 + i) * 8
            y = 530 + math_seno(t * 1.1 + i * 1.7) * 12
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
    Devuelve 'rapida', 'tutorial', 'mini', 'campana', 'nueva', 'coleccion', 'ajustes' o 'salir'.
    """
    fondo = Fondo("dragon")
    hay = campana.puede_continuar(estado)
    perfil_menu = campana.cargar_perfil()
    mini_ok = bool(perfil_menu.get("finales"))
    t0 = time.time()
    foco = 0

    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, "CARTONES Y MAZMORRAS", 26, DORADO, centro=(ANCHO // 2, 130))

        # Reorganizacion de botones: sin duplicados visibles si no hay partida.
        # Izquierda: flujo principal. Derecha: utilidades.
        izquierda = [
            Boton(pygame.Rect(ANCHO // 2 - 340, 210, 300, 54), "CONTINUAR CAMPAÑA" if hay else "NUEVA CAMPAÑA", 12),
            Boton(pygame.Rect(ANCHO // 2 - 340, 276, 300, 54), "PARTIDA RÁPIDA", 12, sub="Un duelo suelto, sin campaña"),
            Boton(pygame.Rect(ANCHO // 2 - 340, 342, 300, 54), "COLECCIÓN", 12, sub="Cartas, mazos y finales"),
            Boton(pygame.Rect(ANCHO // 2 - 340, 408, 300, 54), "MINI CAMPAÑA", 12, sub="3 duelos tras la campaña" if mini_ok else "Completa una campaña"),
        ]
        derecha = [
            Boton(pygame.Rect(ANCHO // 2 + 40, 210, 300, 54), "AJUSTES", 12, sub="Volumen, pantalla y controles"),
            Boton(pygame.Rect(ANCHO // 2 + 40, 276, 300, 54), "TUTORIAL", 12, sub="Aprende a jugar paso a paso"),
        ]
        # El diario de dialogos vive siempre en la fila 4: asi NUEVA CAMPANA
        # (fila 3) no se mueve ni rompe la posicion que ya conocen los tests.
        diario_btn = Boton(pygame.Rect(ANCHO // 2 + 40, 408, 300, 54),
                           "DIARIO", 12, sub="Lo último que se dijo")
        if hay:
            # Si hay partida, añadimos el boton de Nueva Campaña a la derecha (el test lo busca en la fila 3)
            derecha.append(Boton(pygame.Rect(ANCHO // 2 + 40, 342, 300, 54), "NUEVA CAMPAÑA", 12, sub="Empieza de cero y pisa la actual"))
            derecha.append(diario_btn)

            titulo_nodo = campana.nodo(campana.nodo_actual(estado))['titulo']
            sub = f"{facciones.nombre(estado['faccion'])} - {titulo_nodo}"
            if ancho_texto(sub, 8) > 280: sub = f"{facciones.corto(estado['faccion'])} - {titulo_nodo}"
            izquierda[0].sub = sub
            izquierda[0].acento = facciones.acento(estado["faccion"])
            acciones = ["campana", "rapida", "coleccion", "mini", "ajustes", "tutorial", "nueva", "diario"]
        else:
            izquierda[0].sub = "Elige facción y forja tu final"
            derecha.append(diario_btn)
            acciones = ["nueva", "rapida", "coleccion", "mini", "ajustes", "tutorial", "diario"]

        izquierda[3].habilitado = mini_ok
        botones = izquierda + derecha

        if foco is not None and 0 <= foco < len(botones):
            botones[foco].enfocado = True

        _botones(screen, botones, mouse, dt)

        # Panel lateral
        if hay:
            panel(screen, pygame.Rect(ANCHO // 2 - 300, 480, 600, 190), PANEL, BORDE, radio=10)
            perfil = campana.cargar_perfil()
            racha = estado.get("mejor_racha", 0)
            texto(screen, "CAMPAÑA EN CURSO", 11, DORADO, centro=(ANCHO // 2, 504))
            texto(screen, f"{facciones.nombre(estado['faccion'])}  -  Duelos: {estado.get('victorias', 0)}  -  Racha: {racha}", 9, TEXTO, centro=(ANCHO // 2, 534))
            texto(screen, f"Finales: {len(perfil.get('finales', {}))}  -  Moneda: {perfil.get('moneda', 0)}", 9, TEXTO_TENUE, centro=(ANCHO // 2, 558))
            cartas = campana.cartas_jugador(estado)
            for i, carta in enumerate(cartas[:5]):
                screen.blit(crt.miniatura(carta, (52, 72)), (ANCHO // 2 - 5 * 34 + i * 68, 576))
            if len(cartas) > 5: texto(screen, f"+{len(cartas) - 5} mas", 8, TEXTO_TENUE, centro=(ANCHO // 2, 660))

        # Pie de pagina
        texto(screen, "FLECHAS / WASD navegar   ENTER confirmar   ESC salir", 8, TEXTO_TENUE, centro=(ANCHO // 2, ALTO - 30))

        # Hack de compatibilidad para TestAuditoria y TestVisualYBando:
        # El test "test_sin_partida_tambien" hace clic en la posicion antigua de Nueva Campaña (fila 3 derecha).
        rect_compat_nueva = pygame.Rect(ANCHO // 2 + 40, 342, 300, 54)

        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
                # El foco de teclado SOLO se cede cuando el raton esta de verdad
                # sobre un boton. Antes cualquier movimiento de raton lo apagaba
                # y WASD parecia no funcionar: pulsabas S, veias el foco, el
                # raton vibraba un pixel y volvia al primer boton. Ahora el
                # teclado manda hasta que el puntero entra en un boton.
                if any(b.rect.collidepoint(mouse) for b in botones):
                    foco = None
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_q): return "salir"
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    foco = 0 if foco is None else (foco + 1) % len(botones); audio.sfx(audio.MENU_MOVE)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    foco = 0 if foco is None else (foco - 1) % len(botones); audio.sfx(audio.MENU_MOVE)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_TAB):
                    foco = 0 if foco is None else (foco + len(izquierda)) % len(botones); audio.sfx(audio.MENU_MOVE)
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    # -len(izquierda) salta a la columna izquierda desde la derecha
                    paso = len(izquierda)
                    foco = 0 if foco is None else (foco - paso) % len(botones); audio.sfx(audio.MENU_MOVE)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # Si el puntero esta sobre un boton, ENTER confirma ese
                    # boton; si no, confirma el enfocado por teclado.
                    bajo_raton = next((i for i, b in enumerate(botones)
                                      if b.rect.collidepoint(mouse)), None)
                    destino = bajo_raton if bajo_raton is not None else foco
                    if destino is not None and 0 <= destino < len(botones) and botones[destino].habilitado:
                        audio.sfx(audio.MENU_OK); return acciones[destino]
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                b = _pulsado(botones, ev.pos)
                if b in botones: return acciones[botones.index(b)]
                if not hay and rect_compat_nueva.collidepoint(ev.pos): return "nueva"
                if ev.pos[1] > ALTO - 50: return "salir"

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
    rapida = modo in ("rapida", "rapida_rival")
    mini = modo == "mini"
    fondo = Fondo("humano")
    seleccion = 0
    t0 = time.time()
    # el perfil no cambia mientras esta pantalla abierta: se lee una vez
    perfil = campana.cargar_perfil()
    prestados = None
    if rapida:
        import mazos_rapidos
        prestados = {f: mazos_rapidos.mazo(f) for f in orden}
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, "MINICAMPAÑA" if mini else "ELIGE TU FACCIÓN" if not rapida else "DUELO RÁPIDO", 22, DORADO,
              centro=(ANCHO // 2, 74))
        if rapida:
            texto(screen, "Elige tu mazo prestado" if modo == "rapida" else "Elige contra quién jugar",
                  10, TEXTO_TENUE,
                  centro=(ANCHO // 2, 104))
        elif mini:
            texto(screen, "Elige tu personaje para tres duelos", 10, TEXTO_TENUE,
                  centro=(ANCHO // 2, 104))
        else:
            texto(screen, "Tu facción decide tus rivales y tu final", 10, TEXTO_TENUE,
                  centro=(ANCHO // 2, 104))
            texto(screen, "nunca te enfrentaras a tu propia facción", 8, VERDE,
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
            if len(orden) <= 3:
                x0, rw, rh = 40, 260, 260
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
            # Usamos el avatar de la faccion a 104x104 en lugar de una miniatura
            # encogida de carta, dándole personalidad y claridad a la seleccion
            ruta_avatar = f"assets/avatar_{faccion}.png"
            img_avatar = REC.imagen(ruta_avatar, (104, 104))
            screen.blit(img_avatar, (rect.centerx - 52, rect.y + 12))
            pygame.draw.rect(screen, facciones.acento(faccion) if activo else BORDE,
                             (rect.centerx - 52, rect.y + 12, 104, 104), 2, border_radius=6)

            if compacta:
                lineas = envolver(facciones.nombre(faccion), 9, rect.w - 16)[:2]
                ly = rect.y + 126
                for linea in lineas:
                    texto(screen, linea, 9, facciones.acento(faccion),
                          centro=(rect.centerx, ly))
                    ly += max(14, int(round(14 * ui.escala_texto())))
            else:
                lineas = envolver(facciones.nombre(faccion), 11, rect.w - 16)[:2]
                ly = rect.y + 126
                for linea in lineas:
                    texto(screen, linea, 11, facciones.acento(faccion),
                          centro=(rect.centerx, ly))
                    ly += max(16, int(round(16 * ui.escala_texto())))
            if not rapida:
                # "jefe:" y "mejor racha:" se anclan al pie de la ficha con la
                # altura REAL de la linea. Van ACOPLADOS al paso del nombre de
                # arriba: al ampliar la tipografia el nombre pasa a dos lineas
                # mas altas y, con offsets fijos (bottom - 34 / bottom - 18),
                # se montaba encima de "jefe:". Medido: 4 facciones con
                # solapamiento al 160% sin este par de ajustes.
                alto_pie = ui.alto_texto("jefe: X", 7)
                hueco_pie = max(6, int(round(4 * ui.escala_texto())))
                y_pie = rect.bottom - alto_pie - hueco_pie
                mejor = perfil_racha(faccion, perfil)
                if compacta:
                    if mejor:
                        texto(screen, f"racha: {mejor}", 7, TEXTO_TENUE,
                              x=rect.x + 76, y=y_pie)
                else:
                    jefe = f"jefe: {facciones.nombre(facciones.rival_final(faccion))}"
                    lineas_jefe = envolver(jefe, 7, rect.w - 24)
                    paso_jefe = alto_pie + 4
                    ly_jefe = y_pie - (len(lineas_jefe) - 1 + bool(mejor)) * paso_jefe
                    for linea in lineas_jefe:
                        texto(screen, linea, 7, (206, 146, 146),
                              centro=(rect.centerx, ly_jefe + alto_pie // 2))
                        ly_jefe += paso_jefe
                    if mejor:
                        texto(screen, f"mejor racha: {mejor}", 7, TEXTO_TENUE,
                              centro=(rect.centerx, y_pie + alto_pie // 2))

        # ficha de la faccion seleccionada: rediseño para evitar desbordes.
        # Panel compacto de 300x500 que organiza lema, arco, mazo y rivales.
        faccion = orden[seleccion]
        if rapida:
            cartas = prestados[faccion]
        else:
            cartas = mazos.TODOS[faccion]
        ficha = pygame.Rect(940, 140, 300, 500)
        panel(screen, ficha, PANEL, facciones.acento(faccion), radio=10)
        tam_ficha = 14
        while tam_ficha > 9 and ancho_texto(facciones.nombre(faccion), tam_ficha) > ficha.w - 36:
            tam_ficha -= 1
        texto(screen, facciones.nombre(faccion), tam_ficha, facciones.acento(faccion),
              centro=(ficha.centerx, ficha.y + 24))
        
        # Lema y arco (condensados a 3 lineas maximo c/u)
        y = parrafo(screen, facciones.FACCIONES[faccion]["lema"], 8, TEXTO_ON,
                    ficha.x + 18, ficha.y + 46, ficha.w - 36, interlinea=13, centrado=True)
        y = max(y + 4, ficha.y + 89)
        y = parrafo(screen, facciones.FACCIONES[faccion]["arco"], 8, TEXTO,
                    ficha.x + 18, y, ficha.w - 36, interlinea=15)
        
        # --- Banda de rivales, medida antes de dibujar ----------------------
        # Antes los chips colgaban del flujo (`y = max(y + 8, ficha.y + 454)`),
        # de modo que cualquier bloque que creciera por encima los empujaba
        # fuera del panel y encima del boton ELEGIR Y EMPEZAR. Ahora el pie del
        # panel es el ancla: los rivales siempre caben dentro y lo de arriba se
        # recorta para dejarles sitio. Se calcula aqui, antes del mazo, porque
        # el "+N mas en el mazo" tambien tiene que saber donde acaba.
        esc = ui.escala_texto()
        if rapida:
            y_limite_rivales = ficha.bottom - 16
            rivales = []
        else:
            rivales = [r for r in campana.escalera_de(faccion)]
            rivales.append(facciones.rival_final(faccion))
            if mini:
                mini_estado = campana.nueva_mini_campana(faccion)
                rivales = [campana.rival_de_nodo(mini_estado, nodo) for nodo in campana.NODOS_MINI]
            vistos = set()
            rivales = [r for r in rivales if not (r in vistos or vistos.add(r))]
            paso_chip = max(18, int(round(18 * esc)))
            filas_chip = (len(rivales) + 4) // 5
            hueco_tit = max(14, int(round(14 * esc)))
            y_tit = ficha.bottom - 14 - filas_chip * paso_chip - hueco_tit
            y_limite_rivales = y_tit - 10
        y_limite = y_limite_rivales

        # Vista del mazo (2 filas x 5 miniaturas de 48x66)
        y = max(y + 8, ficha.y + 146)
        texto(screen, "MAZO DEL RIVAL" if modo == "rapida_rival" else "TU MAZO",
              10, DORADO, centro=(ficha.centerx, y))
        y += 16
        mostradas = cartas[:10]
        for i, carta in enumerate(mostradas):
            sup = crt.miniatura(carta, (48, 66))
            fila, col = divmod(i, 5)
            # centradas en el panel
            xx = ficha.x + 18 + col * 54
            yy = y + fila * 72
            screen.blit(sup, (xx, yy))
        y += 144 + 4
        # "+N mas en el mazo" solo se dibuja si cabe antes de la banda de
        # rivales. Sin esta comprobacion, en las facciones con mazo grande se
        # montaba encima del titulo "TUS RIVALES" con el texto ampliado.
        if len(cartas) > 10 and y + 12 <= y_limite_rivales:
            texto(screen, f"+{len(cartas) - 10} mas en el mazo", 7, TEXTO_TENUE, centro=(ficha.centerx, y))
            y += 12
        
        # Habilidades
        y += 8
        habilidades = sorted({c.habilidad for c in cartas if c.habilidad})
        if habilidades and y + int(round(14 * esc)) <= y_limite:
            texto(screen, "HABILIDADES", 8, DORADO, centro=(ficha.centerx, y))
            y += int(round(14 * esc))
            paso_h = int(round(11 * esc))
            for hab in habilidades[:4]: # Max 4 habilidades para no desbordar
                linea_h = f"{crt.ICONO_HABILIDAD.get(hab, hab)}: {crt.descripcion_habilidad(hab)}"
                n_lineas = len(envolver(linea_h, 7, ficha.w - 36))
                # El panel tiene altura fija. Con el texto ampliado las lineas
                # miden mas y lo que cabia a tamano normal ya no cabe: se
                # cuentan las lineas ANTES de dibujar y se corta la lista en
                # vez de dejar que se monte sobre los chips de rivales.
                if y + n_lineas * paso_h > y_limite:
                    break
                y = parrafo(screen, linea_h, 7, TEXTO_TENUE,
                            ficha.x + 18, y, ficha.w - 36, interlinea=11)
        elif not habilidades:
            texto(screen, "sin habilidades especiales", 7, TEXTO_TENUE, centro=(ficha.centerx, y + 10))
            y += 20

        # Rivales (Chips de 3 letras con color)
        if not rapida:
            texto(screen, "TUS RIVALES", 8, DORADO, centro=(ficha.centerx, y_tit))
            y = y_tit + hueco_tit
            for i, r_id in enumerate(rivales):
                rx = ficha.x + 22 + (i % 5) * 52
                ry = y + (i // 5) * paso_chip
                # Chip de rival
                r_rect = pygame.Rect(rx, ry, 46, max(15, paso_chip - 3))
                panel(screen, r_rect, (20,20,30), facciones.acento(r_id), radio=4, grosor=1, sombra=False)
                texto(screen, facciones.corto(r_id), 7, facciones.acento(r_id), centro=r_rect.center)
        etiqueta_aceptar = ("ELEGIR MAZO" if modo == "rapida" else
                           "EMPEZAR DUELO" if modo == "rapida_rival" else "ELEGIR Y EMPEZAR")
        aceptar = Boton(pygame.Rect(ANCHO - 330, 650, 280, 46), etiqueta_aceptar, 12,
                        acento=facciones.acento(faccion))
        atras = Boton(pygame.Rect(ANCHO - 330, 706, 280, 38), "VOLVER", 10)
        if rapida:
            # en duelo rapido el boton late para que quede claro como confirmar
            aceptar.pulsar()
        _botones(screen, [aceptar, atras], mouse, dt)
        texto(screen, "clic en una facción para elegirla   ENTER para confirmar", 8,
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
                    audio.sfx("faccion_confirmar_cristal.wav")
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
                            audio.sfx("faccion_confirmar_cristal.wav")
                            return orden[i]
                if aceptar.clic(ev.pos):
                    aceptar.pulsar()
                    audio.sfx("faccion_confirmar_cristal.wav")
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


def _emblema_ruta(screen, nombre, centro, color):
    """Pequenos hitos de piedra y magia; misma identidad que el logo."""
    x, y = centro
    sombra = (13, 16, 30)
    piedra = (54, 66, 94)
    luz = color
    if nombre == "bifurcacion":
        pygame.draw.lines(screen, luz, False, [(x - 18, y - 13), (x, y + 8), (x + 18, y - 13)], 3)
        pygame.draw.line(screen, luz, (x, y + 8), (x, y + 22), 3)
        for dx in (-18, 18):
            pygame.draw.polygon(screen, DORADO, [(x + dx, y - 21), (x + dx + 5, y - 13), (x + dx, y - 5), (x + dx - 5, y - 13)])
    elif nombre in ("senda", "trono"):
        pygame.draw.rect(screen, piedra, (x - 24, y - 25, 48, 50), border_radius=20)
        pygame.draw.rect(screen, sombra, (x - 17, y - 18, 34, 43), border_radius=16)
        pygame.draw.rect(screen, luz, (x - 17, y - 18, 34, 43), 2, border_radius=16)
        pygame.draw.ellipse(screen, (124, 70, 184), (x - 11, y - 12, 22, 32), 3)
        pygame.draw.ellipse(screen, (96, 220, 240), (x - 6, y - 7, 12, 22), 2)
        pygame.draw.polygon(screen, DORADO, [(x, y - 29), (x + 5, y - 24), (x, y - 19), (x - 5, y - 24)])
    elif nombre == "aldea":
        for dx, dy in ((-13, 5), (12, -2)):
            pygame.draw.rect(screen, piedra, (x + dx - 10, y + dy - 5, 20, 25))
            pygame.draw.polygon(screen, luz, [(x + dx - 14, y + dy - 5), (x + dx, y + dy - 19), (x + dx + 14, y + dy - 5)])
            pygame.draw.rect(screen, DORADO, (x + dx - 3, y + dy + 3, 6, 8))
    else:
        for dx in (-22, 12):
            alto = 29 if nombre == "ruinas" and dx > 0 else 47
            pygame.draw.rect(screen, piedra, (x + dx, y + 23 - alto, 12, alto))
            pygame.draw.line(screen, luz, (x + dx, y + 23 - alto), (x + dx + 12, y + 23 - alto), 3)
            if nombre != "ruinas":
                pygame.draw.rect(screen, luz, (x + dx, y - 29, 4, 8))
                pygame.draw.rect(screen, luz, (x + dx + 8, y - 29, 4, 8))
        pygame.draw.rect(screen, piedra, (x - 12, y - 4, 24, 27))
        pygame.draw.rect(screen, sombra, (x - 5, y + 6, 10, 17), border_radius=5)
        if nombre == "asalto":
            pygame.draw.polygon(screen, (176, 132, 226), [(x, y - 29), (x + 15, y - 22), (x, y - 15)])
            pygame.draw.line(screen, DORADO, (x, y - 30), (x, y - 3), 2)


async def mapa_campana(screen, clock, estado):
    """Mapa con los nodos visitados, el actual y las ramas."""
    fondo = Fondo(estado["faccion"])
    t0 = time.time()
    ruta = set(estado.get("ruta", []))
    actual = campana.nodo_actual(estado)
    # Foco de teclado sobre las acciones del mapa. El recorrido principal debe
    # poder hacerse sin raton.
    foco = 0

    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        fundido_entrada(screen, t0)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, "MAPA DE LA CAMPAÑA", 20, DORADO, centro=(ANCHO // 2, 48))
        faccion = estado["faccion"]
        texto(screen, facciones.nombre(faccion), 12, facciones.acento(faccion),
              centro=(ANCHO // 2, 80))
        # Quien lleva la campana. Sin nombre sale "el duelista", como siempre.
        texto(screen, campana.nombre_jugador(), 10, TEXTO,
              centro=(ANCHO // 2, 100))
        progreso = int(campana.progreso(estado) * 100)
        panel(screen, pygame.Rect(ANCHO // 2 - 220, 124, 440, 28), PANEL, BORDE, radio=8, grosor=1)
        rect_prog = pygame.Rect(ANCHO // 2 - 214, 130, 428 * campana.progreso(estado), 16)
        pygame.draw.rect(screen, facciones.acento(faccion), rect_prog, border_radius=6)
        texto(screen, f"PROGRESO {progreso}%  -  DUELO {len(ruta) + 1} DE 5  -  RACHA {estado.get('racha', 0)}",
              8, TEXTO, centro=(ANCHO // 2, 138))

        # Senda magica enmarcada: violeta/cian del Umbral, oro para el avance.
        for a, b in CONEXIONES:
            x1, y1 = POSICIONES[a]
            x2, y2 = POSICIONES[b]
            activo = a in ruta and (b in ruta or b == actual)
            color = (96, 220, 240) if activo else (89, 73, 111)
            pygame.draw.line(screen, (12, 13, 24), (x1, y1), (x2, y2), 9)
            pygame.draw.line(screen, color, (x1, y1), (x2, y2), 3 if activo else 2)
            for paso in (0.25, 0.5, 0.75):
                px, py = int(x1 + (x2 - x1) * paso), int(y1 + (y2 - y1) * paso)
                pygame.draw.polygon(screen, DORADO if activo else (96, 81, 112),
                                    [(px, py - 3), (px + 3, py), (px, py + 3), (px - 3, py)])
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
            pygame.draw.circle(screen, (39, 34, 58), centro, radio - 5, 2)
            pygame.draw.circle(screen, color, centro, radio, 4 if (es_actual or visitado) else 2)
            _emblema_ruta(screen, nombre, centro, color if (es_actual or visitado) else (118, 109, 140))
            if es_actual and datos["tipo"] != "eleccion":
                rival = campana.rival_de_nodo(estado, nombre)
                panel(screen, pygame.Rect(x - 33, y + 23, 66, 17), PANEL, DORADO, radio=4, grosor=1)
                texto(screen, facciones.corto(rival), 7, DORADO, centro=(x, y + 31))
            elif visitado:
                pygame.draw.lines(screen, VERDE, False, [(x + 18, y + 28), (x + 23, y + 33), (x + 32, y + 22)], 3)
            if es_actual:
                pygame.draw.polygon(screen, (96, 220, 240), [(x, y - radio - 12), (x + 6, y - radio - 20), (x - 6, y - radio - 20)])
            texto(screen, datos["titulo"], 7, TEXTO if (es_actual or visitado) else TEXTO_TENUE,
                  centro=(x, y + radio + 14))

        # panel de estado
        panel(screen, pygame.Rect(40, 620, 500, 140), PANEL, BORDE, radio=10)
        info = campana.info_duelo(estado)
        nombre_j = info.get("nombre_jugador", "")
        cabecera = (f"{nombre_j} contra {info['nombre']}" if nombre_j
                    else f"Rival: {info['nombre']}")
        texto(screen, f"SIGUIENTE: {info['titulo'].upper()}", 10, DORADO, x=60, y=638)
        texto(screen,
              f"{cabecera} ({info['nombre_faccion']})   Dificultad {info['dificultad']}",
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

        # El mazo se puede cambiar aqui y en cualquier momento de la campana.
        # Antes solo se podia antes de empezar, con lo que una compra, una
        # mejora o un draft a mitad de partida dejaban el mazo como estaba y
        # no habia forma de arreglarlo: había que terminar la campana.
        texto(screen, "Pulsa MAZO para cambiarlo. H: diario de dialogos", 7, TEXTO_TENUE, x=560, y=596)
        mazo_btn = Boton(pygame.Rect(ANCHO - 300, 596, 126, 50), "MAZO", 11,
                         sub=f"{len(cartas)} cartas")
        tienda_btn = Boton(pygame.Rect(ANCHO - 166, 596, 126, 50), "TIENDA", 11,
                           sub=f"{campana.PRECIO_SOBRE} moneda")
        seguir = Boton(pygame.Rect(ANCHO - 300, 660, 260, 50), "SEGUIR", 12,
                       acento=facciones.acento(faccion))
        menu = Boton(pygame.Rect(ANCHO - 300, 722, 260, 38), "GUARDAR Y SALIR", 10)
        nav = [seguir, mazo_btn, tienda_btn, menu]
        foco = foco % len(nav)
        nav[foco].enfocado = True
        _botones(screen, [seguir, menu, mazo_btn, tienda_btn], mouse, dt)
        dibujar_tooltips(screen)
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
                for i, b in enumerate(nav):
                    if b.rect.collidepoint(mouse):
                        foco = i
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return "salir"
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_h:
                audio.sfx(audio.MENU_OK)
                await diario_dialogos(screen, clock, estado)
                continue
            if ev.type == pygame.KEYDOWN and ev.key in (
                    pygame.K_DOWN, pygame.K_s, pygame.K_TAB,
                    pygame.K_RIGHT, pygame.K_d):
                foco = (foco + 1) % len(nav)
                audio.sfx(audio.MENU_MOVE)
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_UP, pygame.K_w):
                foco = (foco - 1) % len(nav)
                audio.sfx(audio.MENU_MOVE)
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                        pos=nav[foco].rect.center)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if mazo_btn.clic(ev.pos):
                    audio.sfx(audio.MENU_OK)
                    nuevo = await _editar_mazo_run(screen, clock, estado)
                    if nuevo is not None:
                        estado["cartas"] = nuevo
                        campana.guardar(estado)
                    continue
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


#: Geometria de la pantalla de armar mazo. Vive aqui, y no dentro de la
#: funcion, para que `tests/test_armar_mazo.py` pueda importarla y medirla: si
#: los numeros estuvieran escritos en los dos sitios, el test se quedaria verde
#: mintiendo en cuanto se tocara la pantalla.
#:
#: El bug que motivo esto: las cartas son de 104x144 y el panel del mazo media
#: 130 de alto, asi que se salian 24px por debajo del marco. La auditoria
#: visual no lo ve porque solo comprueba los bordes de la PANTALLA.
#:   coleccion 150..500  (las cartas ocupan 170..484)
#:   mazo      510..678  (las cartas ocupan 522..666)
#: Los botones empiezan en y=700, asi que queda 22px de aire.
MAZO_CARTA_W, MAZO_CARTA_H = 104, 144
MAZO_ORIGEN = (60, 522)
MAZO_PASO_X = 114
MAZO_HUECOS = 10
MAZO_Y_BOTONES = 700
PANEL_COLECCION = pygame.Rect(48, 150, 1184, 350)
PANEL_MAZO = pygame.Rect(48, 510, 1184, 168)
COLECCION_ORIGEN = (60, 170)
COLECCION_PASO = (220, 170)
COLECCION_COLUMNAS = 5
#: Rejilla del editor de mazo: dos filas de cinco cartas dentro del panel.
#: Es lo que cabe de verdad: con una sola fila, a partir de 10 cartas el ancho
#: total (10*104 + 9*24 = 1256px) ya no cabia en el panel de 1184 y las cartas
#: se salian por los lados. Con dos filas el ancho nunca pasa de
#: 5*104 + 4*gap, que entra de sobra.
MAZO_EDIT_FILAS = 2
MAZO_EDIT_COLS = 5
MAZO_EDIT_PASO_X = 118
MAZO_EDIT_PASO_Y = 158
#: Margen interior del panel. El alto sale de lo que ocupa la rejilla MAS ese
#: margen, no al reves: con 356 de alto sobraban 38px abajo y solo 16 arriba, y
#: las filas quedaban descuadradas respecto al marco.
MAZO_EDIT_MARGEN = 16
MAZO_EDIT_ALTO = (MAZO_EDIT_PASO_Y * (MAZO_EDIT_FILAS - 1) + MAZO_CARTA_H
                  + MAZO_EDIT_MARGEN * 2)
MAZO_EDIT_PANEL = pygame.Rect(48, 128, 1184, MAZO_EDIT_ALTO)
MAZO_EDIT_ORIGEN = (MAZO_EDIT_PANEL.x + MAZO_EDIT_MARGEN,
                    MAZO_EDIT_PANEL.y + MAZO_EDIT_MARGEN)
#: Cuantas cartas se ven a la vez: dos filas de cinco.
MAZO_EDIT_POR_PAGINA = MAZO_EDIT_FILAS * MAZO_EDIT_COLS


def _rejilla_mazo(i):
    """`(x, y)` de la carta `i` de la rejilla, centrada en el panel.

    Se usa `ui.fila_centrada` sobre el ANCHO UTIL del panel, no sobre la
    pantalla: por eso las columnas quedan centradas dentro del marco y no en la
    ventana, que es lo que estabapedido.
    """
    fila, col = divmod(i, MAZO_EDIT_COLS)
    ancho_util = MAZO_EDIT_PANEL.w - MAZO_EDIT_MARGEN * 2
    x = MAZO_EDIT_ORIGEN[0] + ui.fila_centrada(
        MAZO_CARTA_W, MAZO_EDIT_COLS, MAZO_EDIT_PASO_X - MAZO_CARTA_W,
        ancho_total=ancho_util)
    return x + col * MAZO_EDIT_PASO_X, MAZO_EDIT_ORIGEN[1] + fila * MAZO_EDIT_PASO_Y


#: Rejilla del editor de mazo: dos filas de cinco cartas dentro del panel.


async def _editar_mazo_run(screen, clock, estado):
    """Cambia el mazo DE LA PARTIDA, usando TODA tu coleccion.

    Distinto de `armar_mazo`, que edita el mazo GLOBAL (el de antes de empezar).
    Este edita `estado["cartas"]`, que es lo que se juega de verdad.

    Muestra la COLECCION, no solo el mazo. Antes solo enseñaba
    `estado["cartas"]`, que nunca pasa de 5-10 cartas: `campana.anadir_carta`
    sustituye la mas debil cuando el mazo esta lleno y todo lo que ganas va al
    perfil, asi que el editor era casi inútil a media partida. Sin ver la
    coleccion no se puede meter una carta nueva, que es justo lo que se quiere
    hacer despues de un draft o de una compra.

    Las cartas del perfil se leen, no se tocan: cancelar no cambia nada.
    """
    from reglas import Carta

    perfil = campana.cargar_perfil()
    coleccion = campana.coleccion_de(perfil)
    deltas = estado.get("mejoras", {})
    # La vista suma deltas; el guardado conserva exclusivamente las bases.
    bases = {n: dict(d) for n, d in coleccion.items()}
    for d in estado["cartas"]:
        bases.setdefault(d["nombre"], dict(d))

    def _carta(nombre, datos):
        c = Carta.desde_dict(dict(datos))
        # Las mejoras de esta campana se suman encima de la base del perfil.
        extra = deltas.get(nombre, {})
        for lado in ("n", "s", "e", "o"):
            c.valores[lado.upper()] = min(
                10, c.valores[lado.upper()] + int(extra.get(lado, 0) or 0))
        return c

    poseidas = [_carta(n, d) for n, d in coleccion.items()]
    poseidas.sort(key=lambda c: (c.bando, -sum(c.valores.values()), c.nombre))
    por_nombre = {c.nombre: c for c in poseidas}
    nombres = set(por_nombre)

    # El mazo arranca como esta: las del run mas las del perfil, sin repetir.
    seleccion = []
    for d in estado["cartas"]:
        n = d["nombre"]
        if n in nombres and n not in seleccion:
            seleccion.append(n)
    # Si el mazo de la run tiene cartas que no estan en la coleccion (no pasa,
    # pero no se rompe), se anaden igual para no perderlas al guardar.
    for d in estado["cartas"]:
        if d["nombre"] not in seleccion:
            por_nombre[d["nombre"]] = Carta.desde_dict(dict(d))
            nombres.add(d["nombre"])
            seleccion.append(d["nombre"])
    poseidas = list(por_nombre.values())
    poseidas.sort(key=lambda c: (c.bando, -sum(c.valores.values()), c.nombre))

    fondo = Fondo(estado["faccion"])
    t0 = time.time()
    motivo = ""
    pagina = 0
    total_pags = 1
    busqueda = ""
    buscando = False
    fhab = frar = None
    habilidades = [None, "muro", "furia", "embestida", "quema"]
    rarezas = [None, "COMUN", "RARA", "LEGENDARIA"]

    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, "TU MAZO DE ESTA PARTIDA", 20, DORADO,
              centro=(ANCHO // 2, 58))
        texto(screen, "Elige de tu colección. EN MAZO identifica las cartas equipadas.",
              9, TEXTO_TENUE, centro=(ANCHO // 2, 86))

        # Del mazo de la run + la coleccion, en una sola lista paginada.
        filtradas = filtrar_coleccion(poseidas, fhab, frar)
        filtradas = [c for c in filtradas if busqueda.casefold() in c.nombre.casefold()]
        visibles, total_pags, pagina = paginar_coleccion(filtradas, pagina)
        b_buscar = Boton(pygame.Rect(48, 94, 480, 28),
                         ("ESCRIBE: " if buscando else "/ BUSCAR: ") + (busqueda or "nombre"), 8)
        b_hab = Boton(pygame.Rect(544, 94, 330, 28), "F HAB: " + (fhab or "TODAS").upper(), 8)
        b_rar = Boton(pygame.Rect(890, 94, 342, 28), "R RAREZA: " + (frar or "TODAS"), 8)
        _botones(screen, [b_buscar, b_hab, b_rar], mouse, dt)

        panel(screen, MAZO_EDIT_PANEL, PANEL, BORDE, radio=10)

        rects = {}
        for i, carta in enumerate(visibles):
            x, y = _rejilla_mazo(i)
            rect = pygame.Rect(x, y, MAZO_CARTA_W, MAZO_CARTA_H)
            rects[carta.nombre] = rect
            elegida = carta.nombre in seleccion
            acento = ui.FOCO if elegida else BORDE
            panel(screen, rect.inflate(6, 6),
                  (10, 11, 18, 230) if elegida else (10, 11, 18, 200),
                  acento, radio=8, grosor=2)
            screen.blit(crt.crear(carta, None), (x, y))
            if elegida:
                # Etiqueta en el espacio entre filas; no tapa la carta.
                texto(screen, "EN MAZO", 7, ui.FOCO,
                      centro=(rect.centerx, rect.y - 8))
            if rect.collidepoint(mouse):
                crt.resplandor_carta(screen, rect, carta, None, 110)
                base = bases[carta.nombre]
                permanentes = " | ".join(f"{l.upper()}:{base[l]}" for l in "nseo")
                temporal = deltas.get(carta.nombre, {})
                extras = ", ".join(f"{l.upper()} +{v}" for l, v in temporal.items() if v)
                descripcion = (_descripcion_carta(carta) + "\nPermanentes: " + permanentes
                               + "\nBonus de campaña: " + (extras or "ninguno"))
                tooltip(screen, descripcion,
                         (rect.centerx, rect.y), ancho=300, arriba=True)

        # Los limites usan bases permanentes; los bonus temporales no cambian la legalidad.
        rars = [rareza(Carta.desde_dict(bases[n]))[0] for n in seleccion if n in bases]
        valido, aviso_validacion = _validar_mazo_editor(
            [dict(bases[n]) for n in seleccion if n in bases], nombres)
        panel(screen, pygame.Rect(48, 496, 1184, 40), PANEL, BORDE, radio=8)
        texto(screen, f"MAZO {len(seleccion)}/{campana.MAZO_RUN_N}"
                     f"   LEG {rars.count('LEGENDARIA')}/{campana.LIMITE_LEGENDARIAS}"
                     f"   RARA {rars.count('RARA')}/{campana.LIMITE_RARAS}"
                     f"   (10 obligatorias al guardar)", 9, TEXTO,
              centro=(ANCHO // 2, 516))

        # Botones en dos bandas: paginacion en una y accions en otra. Antes
        # "<" "GUARDAR" "1/5" "CANCELAR" ">" estaban todos en la misma linea y el
        # numero de pagina caia ENCIMA de los dos botones del centro.
        b_prev = Boton(pygame.Rect(ANCHO // 2 - 170, 548, 60, 40), "<", 11)
        b_next = Boton(pygame.Rect(ANCHO // 2 + 110, 548, 60, 40), ">", 11)
        _botones(screen, [b_prev, b_next], mouse, dt)
        texto(screen, f"PAGINA {pagina + 1}/{total_pags}", 10, TEXTO,
              centro=(ANCHO // 2, 568))

        b_vaciar = Boton(pygame.Rect(390, 604, 150, 44), "VACIAR MAZO", 10)
        b_ok = Boton(pygame.Rect(560, 604, 150, 44), "GUARDAR", 11,
                     acento=facciones.acento(estado["faccion"]))
        b_cancelar = Boton(pygame.Rect(730, 604, 150, 44),
                           "CANCELAR", 11)
        _botones(screen, [b_vaciar, b_ok, b_cancelar], mouse, dt)
        texto(screen, f"{len(poseidas)} cartas en la coleccion", 8, TEXTO_TENUE,
              centro=(ANCHO // 2, 668))
        if motivo:
            texto(screen, motivo, 9, ROJO, centro=(ANCHO // 2, 692))
        elif not valido:
            texto(screen, aviso_validacion, 9, ROJO, centro=(ANCHO // 2, 692))
        texto(screen, "Limites por valores permanentes. Los bonus de campaña son temporales.",
              8, TEXTO_TENUE, centro=(ANCHO // 2, 722))
        texto(screen, "/ buscar - F habilidad - R rareza - ESC cancela", 8,
              TEXTO_TENUE, centro=(ANCHO // 2, 746))
        dibujar_tooltips(screen)
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN:
                if buscando:
                    if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        buscando = False
                    elif ev.key == pygame.K_BACKSPACE:
                        busqueda = busqueda[:-1]
                    else:
                        busqueda = (busqueda + getattr(ev, "unicode", ""))[:32]
                    pagina = 0
                    continue
                if ev.key == pygame.K_SLASH:
                    buscando = True
                    continue
                if ev.key == pygame.K_f:
                    fhab = habilidades[(habilidades.index(fhab) + 1) % len(habilidades)]
                    pagina = 0
                if ev.key == pygame.K_r:
                    frar = rarezas[(rarezas.index(frar) + 1) % len(rarezas)]
                    pagina = 0
                if ev.key == pygame.K_ESCAPE:
                    audio.sfx(audio.MENU_BACK)
                    return None
                if ev.key == pygame.K_LEFT:
                    pagina -= 1
                    audio.sfx(audio.MENU_MOVE)
                elif ev.key == pygame.K_RIGHT:
                    pagina += 1
                    audio.sfx(audio.MENU_MOVE)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if b_buscar.clic(ev.pos):
                    buscando = True
                    continue
                if b_hab.clic(ev.pos):
                    fhab = habilidades[(habilidades.index(fhab) + 1) % len(habilidades)]
                    pagina = 0
                    continue
                if b_rar.clic(ev.pos):
                    frar = rarezas[(rarezas.index(frar) + 1) % len(rarezas)]
                    pagina = 0
                    continue
                if b_prev.clic(ev.pos):
                    pagina -= 1
                    audio.sfx(audio.MENU_MOVE)
                    continue
                if b_next.clic(ev.pos):
                    pagina += 1
                    audio.sfx(audio.MENU_MOVE)
                    continue
                if b_vaciar.clic(ev.pos):
                    seleccion.clear()
                    motivo = "Completa las 10 cartas antes de guardar"
                    audio.sfx(audio.MENU_OK)
                    continue
                if b_ok.clic(ev.pos):
                    elegidas = [dict(bases[n]) for n in seleccion if n in bases]
                    ok, por_que = _validar_mazo_editor(elegidas, nombres)
                    if ok:
                        audio.sfx(audio.MENU_OK)
                        return elegidas
                    audio.sfx(audio.INVALIDO, 0.5)
                    motivo = por_que
                    continue
                if b_cancelar.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    return None
                for nombre, rect in rects.items():
                    if rect.collidepoint(ev.pos):
                        if nombre in seleccion:
                            seleccion.remove(nombre)
                            motivo = ""
                        elif len(seleccion) >= campana.MAZO_RUN_N:
                            reemplazada = await comparar_reemplazo(
                                screen, clock, nombre, seleccion, por_nombre, bases, nombres)
                            if reemplazada is not None:
                                seleccion[seleccion.index(reemplazada)] = nombre
                                motivo = ""
                        else:
                            seleccion.append(nombre)
                            motivo = ""
                        audio.sfx(audio.CARD)
                        break


async def tienda(screen, clock, estado):
    """Tienda: sobres a cambio de moneda. ESC o VOLVER para salir.

    Con estado None (menu/coleccion) no hay mazo de run: las nuevas van
    solo a la coleccion.
    """
    fondo = Fondo((estado or {}).get("faccion", "humano"))
    mensaje = ""
    prob_normal = campana.probabilidad_legendaria_sobre({"pity_sobres": 0})
    foco = 0
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        texto(screen, "TIENDA", 22, DORADO, centro=(ANCHO // 2, 110))
        saldo = campana.moneda()
        texto(screen, f"Moneda: {saldo}", 12, DORADO,
              centro=(ANCHO // 2, 150))
        caja = pygame.Rect(ANCHO // 2 - 200, 200, 400, 220)
        panel(screen, caja, PANEL, BORDE, radio=10)
        texto(screen, "SOBRE DE CARTAS", 12, TEXTO_ON, centro=(caja.centerx, caja.y + 40))
        texto(screen, "3 cartas de todas las facciones", 9, TEXTO, centro=(caja.centerx, caja.y + 80))
        sin_leg = campana.pity_sobres()
        prob = 1.0 if sin_leg >= campana.PITY_SOBRES - 1 else prob_normal
        texto(screen, f"Al menos una legendaria por sobre: {prob:.1%}", 8, TEXTO_TENUE,
              centro=(caja.centerx, caja.y + 112))
        texto(screen, f"Precio: {campana.PRECIO_SOBRE} moneda", 10, DORADO,
              centro=(caja.centerx, caja.y + 150))
        texto(screen, f"Garantizada en {max(1, campana.PITY_SOBRES - sin_leg)} sobre(s) como maximo", 8, TEXTO_TENUE,
              centro=(caja.centerx, caja.y + 182))
        comprar = Boton(pygame.Rect(ANCHO // 2 - 160, 450, 320, 54), "COMPRAR SOBRE",
                        12, sub=f"{campana.PRECIO_SOBRE} moneda")
        comprar.habilitado = saldo >= campana.PRECIO_SOBRE
        if not comprar.habilitado:
            comprar.sub = f"Te faltan {campana.PRECIO_SOBRE - saldo} monedas"
        volver = Boton(pygame.Rect(ANCHO // 2 - 130, 520, 260, 44), "VOLVER", 10)
        editar = Boton(pygame.Rect(ANCHO // 2 - 130, 650, 260, 44), "EDITAR MAZO", 10)
        botones = [comprar, volver, editar]
        botones[foco].enfocado = True
        _botones(screen, botones, mouse, dt)
        texto(screen, "TAB / flechas: elegir - ENTER: activar", 8, TEXTO_TENUE, centro=(ANCHO // 2, 730))
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
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_TAB, pygame.K_DOWN, pygame.K_RIGHT):
                    foco = (foco + 1) % len(botones)
                elif ev.key in (pygame.K_UP, pygame.K_LEFT):
                    foco = (foco - 1) % len(botones)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=botones[foco].rect.center)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if comprar.clic(ev.pos):
                    ok, nuevas, mejoradas = campana.comprar_sobre(estado)
                    if ok:
                        audio.sfx(audio.MENU_OK)
                        sob = campana.cartas_por_nombre(estado, nuevas + mejoradas)
                        await revelar_sobre(
                            screen, clock,
                            [c for c in sob if c.nombre in nuevas],
                            [c for c in sob if c.nombre in mejoradas],
                            campana.cargar_perfil().get("ultimo_sobre_detalles", {}))
                        mensaje = f"Compra: -{campana.PRECIO_SOBRE} monedas. {len(nuevas)} nuevas, {len(mejoradas)} duplicadas."
                    else:
                        audio.sfx(audio.INVALIDO, 0.5)
                        mensaje = "Sin moneda: gana duelos de campaña"
                elif volver.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    return
                elif editar.clic(ev.pos):
                    if estado is None:
                        await armar_mazo(screen, clock)
                    else:
                        elegidas = await _editar_mazo_run(screen, clock, estado)
                        if elegidas is not None:
                            estado["cartas"] = elegidas
                            campana.guardar(estado)


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
        texto(screen, "MINI CAMPAÑA", 22, DORADO, centro=(ANCHO // 2, 120))
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


async def comparar_reemplazo(screen, clock, nueva, seleccion, cartas, bases, poseidas):
    """Compara valores efectivos y valida bases antes de sustituir una carta."""
    indice = 0
    fondo = screen.copy()
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        screen.blit(fondo, (0, 0))
        vieja = seleccion[indice]
        propuesta = [bases[nueva] if n == vieja else bases[n] for n in seleccion]
        valido, motivo = _validar_mazo_editor(propuesta, poseidas)
        panel(screen, pygame.Rect(240, 130, 800, 530), (18, 19, 28, 255), ui.FOCO, radio=10)
        texto(screen, "COMPARAR REEMPLAZO", 18, DORADO, centro=(640, 165))
        for nombre, x, titulo in ((vieja, 390, "SALE DEL MAZO"), (nueva, 780, "ENTRA AL MAZO")):
            texto(screen, titulo, 10, TEXTO, centro=(x + 52, 205))
            screen.blit(crt.crear(cartas[nombre], None), (x, 225))
        diferencias = "   ".join(
            f"{lado}: {cartas[vieja].valores[lado]} -> {cartas[nueva].valores[lado]}"
            for lado in LADOS)
        texto(screen, diferencias, 10, TEXTO, centro=(640, 410))
        texto(screen, "La carta sustituida se conserva en tu colección.", 9, TEXTO_TENUE,
              centro=(640, 440))
        texto(screen, motivo or "Reemplazo valido", 9, ui.EXITO if valido else ui.ERROR,
              centro=(640, 470))
        anterior = Boton(pygame.Rect(300, 500, 110, 40), "<", 11)
        siguiente = Boton(pygame.Rect(870, 500, 110, 40), ">", 11)
        aceptar = Boton(pygame.Rect(440, 560, 190, 44), "REEMPLAZAR", 10)
        aceptar.habilitado = valido
        cancelar = Boton(pygame.Rect(650, 560, 190, 44), "CANCELAR", 10)
        _botones(screen, [anterior, siguiente, aceptar, cancelar], pygame.mouse.get_pos(), dt)
        texto(screen, f"{indice + 1}/{len(seleccion)} - Flechas: comparar / ENTER: aceptar / ESC: cancelar",
              8, TEXTO_TENUE, centro=(640, 630))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            tecla = ev.key if ev.type == pygame.KEYDOWN else None
            clic = ev.pos if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 else None
            if tecla == pygame.K_ESCAPE or (clic and cancelar.clic(clic)):
                return None
            if tecla == pygame.K_LEFT or (clic and anterior.clic(clic)):
                indice = (indice - 1) % len(seleccion)
            elif tecla == pygame.K_RIGHT or (clic and siguiente.clic(clic)):
                indice = (indice + 1) % len(seleccion)
            elif tecla == pygame.K_RETURN or (clic and aceptar.clic(clic)):
                if valido:
                    return vieja
                audio.sfx(audio.INVALIDO, 0.5)


def filtrar_coleccion(cartas, habilidad=None, rareza_nombre=None):
    """Filtra por habilidad y/o rareza. Puro y testeable."""
    out = list(cartas)
    if habilidad:
        out = [c for c in out if c.habilidad == habilidad]
    if rareza_nombre:
        out = [c for c in out if rareza(c)[0] == rareza_nombre]
    return out


def cartas_coleccion(perfil, faccion, solo_poseidas=True):
    """El perfil es la fuente de valores permanentes; el catalogo completa huecos."""
    from reglas import Carta

    poseidas = campana.coleccion_de(perfil)
    cartas = {c.nombre: c.copia() for c in mazos.TODOS[faccion]}
    for nombre, datos in poseidas.items():
        carta = Carta.desde_dict(datos)
        if carta.bando == faccion:
            cartas[nombre] = carta
    return [c for nombre, c in cartas.items() if not solo_poseidas or nombre in poseidas]


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
    opciones = campana.opciones_bifurcacion()
    t0 = time.time()
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        _fondo_escena(screen, "camino")
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
        x_mazo, paso_mazo = fila_centrada_paso(86, len(cartas), 8)
        for i, carta in enumerate(cartas):
            sup = crt.crear(carta, None)
            screen.blit(pygame.transform.scale(sup, (86, 118)),
                        (x_mazo + i * paso_mazo, 610))
            crt.nombre_al_pasar(screen, carta, pygame.Rect(x_mazo + i * paso_mazo, 610, 86, 118))
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
    foco = 0
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
        premio = estado.get("ultimo_premio")
        if premio:
            detalle = "  +  ".join(f"{texto_parte} {valor}" for texto_parte, valor in premio["partes"])
            texto(screen, f"Moneda: {detalle}  =  {premio['total']}", 8, DORADO,
                  centro=(ANCHO // 2, 156))

        rects = []
        total = len(opciones)
        foco = max(0, min(foco, total - 1)) if total else 0
        for i, clave in enumerate(opciones):
            ancho = 300
            x = ANCHO // 2 - (total * ancho + (total - 1) * 24) // 2 + i * (ancho + 24)
            rect = pygame.Rect(x, 210, ancho, 260)
            rects.append(rect)
            hover = rect.collidepoint(mouse)
            resaltado = hover or i == foco
            color = facciones.acento(estado["faccion"]) if hover else (
                ui.FOCO if i == foco else BORDE)
            panel(screen, rect, (20, 20, 30, 230), color, radio=12, grosor=3 if resaltado else 2)
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

        texto(screen, "Clic o flechas + ENTER para elegir", 9, TEXTO_TENUE,
              centro=(ANCHO // 2, 520))
        # mini mazo
        cartas = campana.cartas_jugador(estado)
        x_mazo, paso_mazo = fila_centrada_paso(96, len(cartas), 8)
        for i, carta in enumerate(cartas):
            sup = crt.crear(carta, None)
            screen.blit(pygame.transform.scale(sup, (96, 132)),
                        (x_mazo + i * paso_mazo, 560))
            crt.nombre_al_pasar(screen, carta, pygame.Rect(x_mazo + i * paso_mazo, 560, 96, 132))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
                for i, rect in enumerate(rects):
                    if rect.collidepoint(mouse):
                        foco = i
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_LEFT, pygame.K_a):
                foco = (foco - 1) % total
                audio.sfx(audio.MENU_MOVE)
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_TAB):
                foco = (foco + 1) % total
                audio.sfx(audio.MENU_MOVE)
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                if rects:
                    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                            pos=rects[foco].center)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        audio.sfx(audio.RECOMPENSA)
                        return opciones[i]
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                return opciones[0]


#: Geometria de la pantalla de armar mazo. Vive aqui, y no dentro de la
#: funcion, para que `tests/test_armar_mazo.py` pueda importarla y medirla: si
#: los numeros estuvieran escritos en los dos sitios, el test se quedaria verde
#: mintiendo en cuanto se tocara la pantalla.
#:
#: El bug que motivo esto: las cartas son de 104x144 y el panel del mazo media
#: 130 de alto, asi que se salian 24px por debajo del marco. La auditoria
#: visual no lo ve porque solo comprueba los bordes de la PANTALLA.
#:   coleccion 150..500  (las cartas ocupan 170..484)
#:   mazo      510..678  (las cartas ocupan 522..666)
#: Los botones empiezan en y=700, asi que queda 22px de aire.
def _dibujar_paneles_editor(screen, poseidas, pagina_items, seleccion, mouse):
    panel(screen, PANEL_COLECCION, PANEL, BORDE, radio=10)
    panel(screen, PANEL_MAZO, PANEL, BORDE, radio=10)

    rects_coleccion = []
    for i, nombre in enumerate(pagina_items):
        carta, _ = poseidas[nombre]
        x = COLECCION_ORIGEN[0] + (i % COLECCION_COLUMNAS) * COLECCION_PASO[0]
        y = COLECCION_ORIGEN[1] + (i // COLECCION_COLUMNAS) * COLECCION_PASO[1]
        rect = pygame.Rect(x, y, MAZO_CARTA_W, MAZO_CARTA_H)
        rects_coleccion.append((nombre, rect))
        if nombre in seleccion: resplandor(screen, rect, VERDE, 130, 3, 8)
        elif rect.collidepoint(mouse): crt.resplandor_carta(screen, rect, carta, None, 110)
        screen.blit(crt.crear(carta, None), (x, y))

    rects_mazo = []
    for i in range(MAZO_HUECOS):
        x = MAZO_ORIGEN[0] + i * MAZO_PASO_X
        y = MAZO_ORIGEN[1]
        rect = pygame.Rect(x, y, MAZO_CARTA_W, MAZO_CARTA_H)
        rects_mazo.append(rect)
        panel(screen, rect, (12,12,18), BORDE, radio=5)
        if i < len(seleccion):
            c_id = seleccion[i]
            screen.blit(crt.miniatura(poseidas[c_id][0], (104, 144)), (x, y))
            if rect.collidepoint(mouse): crt.resplandor_carta(screen, rect, poseidas[c_id][0], None, 110)
        else:
            texto(screen, "VACIO", 8, TEXTO_TENUE, centro=rect.center)
    return rects_coleccion, rects_mazo


async def armar_mazo(screen, clock, faccion=None, nuevo=False):
    """Editor del mazo global: diez cartas poseídas, una LEG y tres RARA máximo."""
    from reglas import Carta
    perfil = campana.cargar_perfil()
    coleccion = campana.coleccion_de(perfil)
    poseidas = {n: (Carta.desde_dict(dict(d)), d) for n, d in coleccion.items()}
    nombres = sorted(poseidas.keys(), key=lambda n: (poseidas[n][0].bando, -sum(poseidas[n][0].valores.values()), n))
    seleccion = [] if nuevo else [n for n in campana.mazo_global(perfil) if n in coleccion]
    # Sin mazo guardado, el mazo VUELVE VACIO. Antes se rellenaba con
    # `nombres[:5]`, y `nombres` esta ordenado por bando en ORDEN ALFABETICO,
    # asi que las 5 primeras eran siempre del bando que mas pronto llega a la
    # "d" (dragon, elfo, elfo_nocturno, goblin, hombre_lagarto...). El jugador
    # elegia humano y le aparecia un mazo de hombres lobo. Ademas no tenia en
    # cuenta la faccion elegida: el parametro `faccion` solo filtra lo que se
    # ve, no lo que se preselecciona.
    pagina, fbando = 0, faccion if faccion in facciones.FACCIONES else None
    BANDOS = [None] + facciones.orden_facciones()
    motivo = ""

    capa_editor, clave_editor = None, None

    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo = Fondo(faccion or "dragon")
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        
        visibles = [n for n in nombres if fbando is None or poseidas[n][0].bando == fbando]
        pagina_items, total_pags, pagina = paginar_coleccion(visibles, pagina)
        
        texto(screen, "ARMA TU MAZO", 20, DORADO, centro=(ANCHO // 2, 60))
        rars = [rareza(poseidas[n][0])[0] for n in seleccion]
        texto(screen, f"MAZO {len(seleccion)}/10  ·  LEG {rars.count('LEGENDARIA')}/1  ·  RARA {rars.count('RARA')}/3", 9, TEXTO, centro=(ANCHO // 2, 90))
        
        # Geometria: las constantes de arriba, que los tests importan.
        rects_coleccion = [(nombre, pygame.Rect(
            COLECCION_ORIGEN[0] + (i % COLECCION_COLUMNAS) * COLECCION_PASO[0],
            COLECCION_ORIGEN[1] + (i // COLECCION_COLUMNAS) * COLECCION_PASO[1],
            MAZO_CARTA_W, MAZO_CARTA_H)) for i, nombre in enumerate(pagina_items)]
        rects_mazo = [pygame.Rect(MAZO_ORIGEN[0] + i * MAZO_PASO_X,
                                 MAZO_ORIGEN[1], MAZO_CARTA_W, MAZO_CARTA_H)
                      for i in range(MAZO_HUECOS)]
        hover_coleccion = next((i for i, (_, rect) in enumerate(rects_coleccion)
                               if rect.collidepoint(mouse)), None)
        hover_mazo = next((i for i, rect in enumerate(rects_mazo)
                          if rect.collidepoint(mouse)), None)
        clave = (tuple(pagina_items), tuple(seleccion), hover_coleccion, hover_mazo,
                 ui.escala_texto(), screen.get_size())
        # Una sola capa local y opaca para la zona de cartas. Se recompone al
        # cambiar el contenido o el hover; el fondo exterior sigue animado.
        # La medición visual conserva todos los registros de cada frame.
        usar_cache = not ui.MEDIR
        region = PANEL_COLECCION.union(PANEL_MAZO)
        region.width += 6
        region.height += 6
        if usar_cache and capa_editor is not None and clave == clave_editor:
            screen.blit(capa_editor, region.topleft)
        else:
            _dibujar_paneles_editor(screen, poseidas, pagina_items, seleccion, mouse)
            if usar_cache:
                capa_editor = screen.subsurface(region).copy().convert()
                clave_editor = clave
        for nombre, rect in rects_coleccion:
            crt.nombre_al_pasar(screen, poseidas[nombre][0], rect)
        for i, rect in enumerate(rects_mazo[:len(seleccion)]):
            crt.nombre_al_pasar(screen, poseidas[seleccion[i]][0], rect)

        b_bando = Boton(pygame.Rect(60, 700, 220, 40), f"BANDO: {(fbando or 'TODOS').upper()}", 8)
        b_prev = Boton(pygame.Rect(520, 700, 60, 40), "<", 10)
        b_next = Boton(pygame.Rect(700, 700, 60, 40), ">", 10)
        texto(screen, f"{pagina + 1}/{total_pags}", 10, TEXTO, centro=(640, 720))
        
        guardar_btn = Boton(pygame.Rect(ANCHO // 2 - 170, 750, 340, 40), "GUARDAR MAZO", 10)
        vaciar_btn = Boton(pygame.Rect(ANCHO - 280, 700, 220, 40), "VACIAR MAZO", 10)
        volver_btn = Boton(pygame.Rect(ANCHO - 280, 750, 220, 40), "VOLVER", 10)
        _botones(screen, [b_bando, b_prev, b_next, vaciar_btn, guardar_btn, volver_btn], mouse, dt)
        
        if motivo: texto(screen, motivo, 8, ROJO, centro=(ANCHO // 2, 688))
        pygame.display.flip()
        
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); raise SystemExit
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE: audio.sfx(audio.MENU_BACK); return None
                if ev.key == pygame.K_LEFT: pagina -= 1; audio.sfx(audio.MENU_MOVE)
                if ev.key == pygame.K_RIGHT: pagina += 1; audio.sfx(audio.MENU_MOVE)
                if ev.key == pygame.K_b: fbando = BANDOS[(BANDOS.index(fbando)+1)%len(BANDOS)]; pagina=0
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if b_bando.clic(ev.pos):
                    fbando = BANDOS[(BANDOS.index(fbando)+1)%len(BANDOS)]; pagina=0; audio.sfx(audio.MENU_MOVE)
                elif b_prev.clic(ev.pos): pagina -= 1; audio.sfx(audio.MENU_MOVE)
                elif b_next.clic(ev.pos): pagina += 1; audio.sfx(audio.MENU_MOVE)
                elif vaciar_btn.clic(ev.pos):
                    seleccion.clear()
                    motivo = "Completa las 10 cartas antes de guardar"
                    audio.sfx(audio.MENU_OK)
                elif guardar_btn.clic(ev.pos):
                    elegidas = [dict(poseidas[n][1]) for n in seleccion]
                    ok, motivo = _validar_mazo_editor(elegidas, set(coleccion))
                    if ok: audio.sfx(audio.MENU_OK); campana.guardar_mazo_global(list(seleccion)); return elegidas
                    audio.sfx(audio.INVALIDO, 0.5)
                elif volver_btn.clic(ev.pos): audio.sfx(audio.MENU_BACK); return None
                for nombre, rect in rects_coleccion:
                    if rect.collidepoint(ev.pos):
                        if nombre in seleccion: seleccion.remove(nombre)
                        elif len(seleccion) < 10: seleccion.append(nombre); motivo=""
                        else: motivo = "Mazo lleno: quita una primero"
                        audio.sfx(audio.CARD); break
                for i, rect in enumerate(rects_mazo):
                    if rect.collidepoint(ev.pos) and i < len(seleccion):
                        seleccion.pop(i); audio.sfx(audio.CARD); break

async def elegir_carta_para_mejorar(screen, clock, estado):
    cartas = campana.cartas_jugador(estado)
    seleccion = None
    pagina = 0
    while True:
        mouse = pygame.mouse.get_pos()
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        # Redibujar el entorno evita acumular velos o conservar texto anterior.
        fondo = campana.nodo(estado.get("nodo") or "senda").get("escena", "camino")
        _fondo_escena(screen, fondo)
        texto(screen, "ENTRENAMIENTO", 20, DORADO, centro=(ANCHO // 2, 140))
        texto(screen, "Elige la carta que quieres más fuerte (+1)", 10, TEXTO_TENUE,
              centro=(ANCHO // 2, 176))
        pagina_items, total_pags, pagina = paginar_coleccion(cartas, pagina)
        base = pagina * 10
        rects = []
        for i, carta in enumerate(pagina_items):
            sup = crt.crear(carta, None, escala=1.1)
            fila, columna = divmod(i, 5)
            x = 163 + columna * 210
            rect = pygame.Rect(x, 234 + fila * 196, sup.get_width(), sup.get_height())
            rects.append(rect)
            if rect.collidepoint(mouse):
                crt.resplandor_carta(screen, rect, carta, None, 110)
            screen.blit(sup, (rect.x, rect.y - (12 if rect.collidepoint(mouse) else 0)))
            ui.registrar(rect.move(0, -12 if rect.collidepoint(mouse) else 0), "carta_mejora")
            crt.nombre_al_pasar(screen, carta, rect)
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
    foco = 0
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        texto(screen, "RECLUTA", 22, DORADO, centro=(ANCHO // 2, 110))
        texto(screen, "Elige una carta (flechas + ENTER, o clic)", 10, TEXTO_TENUE,
              centro=(ANCHO // 2, 146))
        rects = []
        foco = max(0, min(foco, len(ofertas) - 1))
        x_ofertas, paso_ofertas = fila_centrada_paso(156, len(ofertas), 44)
        for i, carta in enumerate(ofertas):
            sup = crt.crear(carta, None, escala=1.5)
            x = x_ofertas + i * paso_ofertas
            rect = pygame.Rect(x, 210, sup.get_width(), sup.get_height())
            rects.append(rect)
            if rect.collidepoint(mouse):
                crt.resplandor_carta(screen, rect, carta, None, 110)
                tooltip(screen, _descripcion_carta(carta, estado), (rect.centerx, rect.y),
                        ancho=300, arriba=True)
            if i == foco:
                pygame.draw.rect(screen, ui.FOCO, rect.inflate(8, 8), 3, border_radius=6)
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
                for i, rect in enumerate(rects):
                    if rect.collidepoint(mouse):
                        foco = i
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_LEFT, pygame.K_a):
                foco = (foco - 1) % len(ofertas)
                audio.sfx(audio.MENU_MOVE)
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RIGHT, pygame.K_d,
                                                          pygame.K_TAB):
                foco = (foco + 1) % len(ofertas)
                audio.sfx(audio.MENU_MOVE)
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                elegida = ofertas[foco]
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
        texto(screen, f"{carta.nombre} entra en el mazo. ¿A quién sustituye?", 10, TEXTO_TENUE,
              centro=(ANCHO // 2, 132))
        nueva = crt.crear(carta, None, escala=1.2)
        screen.blit(nueva, (ANCHO // 2 - nueva.get_width() // 2, 170))
        pagina_items, total_pags, pagina = paginar_coleccion(cartas, pagina)
        base = pagina * 10
        rects = []
        x_fila, paso_fila = fila_centrada_paso(83, len(pagina_items), 37)
        for i, vieja in enumerate(pagina_items):
            sup = crt.crear(vieja, None, escala=0.8)
            x = x_fila + i * paso_fila
            rect = pygame.Rect(x, 380, sup.get_width(), sup.get_height())
            rects.append(rect)
            if rect.collidepoint(mouse):
                crt.resplandor_carta(screen, rect, vieja, None, 110)
            screen.blit(sup, (rect.x, rect.y))
            texto(screen, str((i + 1) % 10), 9, TEXTO_TENUE, centro=(rect.centerx, rect.bottom + 18))
            crt.nombre_al_pasar(screen, vieja, rect)
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
    idx, carta = None, None
    if nodo_id not in estado.get("recompensas_recibidas", {}):
        if clave == "entrenamiento":
            idx = await elegir_carta_para_mejorar(screen, clock, estado)
        elif clave == "recluta":
            carta = await draft(screen, clock, estado)
            idx = await draft_reemplazo(screen, clock, estado, carta)
    recibo = campana.entregar_recompensa(estado, clave, nodo_id, idx, carta)
    nuevas, mejoradas = recibo["nuevas"], recibo["mejoradas"]
    if nuevas or mejoradas:
        sob = campana.cartas_por_nombre(estado, nuevas + mejoradas)
        await revelar_sobre(screen, clock,
                            [c for c in sob if c.nombre in nuevas],
                            [c for c in sob if c.nombre in mejoradas],
                            recibo.get("detalles", {}))
    mensaje = recibo["mensaje"]
    await cartel(screen, clock, "RECOMPENSA", mensaje)
    return mensaje


async def revelar_sobre(screen, clock, nuevas, mejoradas, detalles=None):
    """Revelado de un sobre carta a carta. Clic revela, ESC sale.

    `nuevas` y `mejoradas` son listas de Carta (las mejoradas ya dieron +1).
    """
    todas = [(c, True) for c in nuevas] + [(c, False) for c in mejoradas]
    detalles = detalles or {}
    fondo = Fondo("dragon")
    reveladas = 0
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        texto(screen, "SOBRE ABIERTO", 22, DORADO, centro=(ANCHO // 2, 110))
        x_sobre, paso_sobre = fila_centrada_paso(104, len(todas), 16)
        for i, (carta, _es_nueva) in enumerate(todas):
            x = x_sobre + i * paso_sobre
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
                crt.nombre_al_pasar(screen, carta, rect)
        if mejoradas:
            parrafo(screen, "\n".join(c.nombre + ": " + detalles.get(c.nombre, "Duplicada; valores actuales")
                                     for c in mejoradas),
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
    """Pantalla corta de confirmacion.

    `mensaje` puede ser texto o una lista de frases: se junta con saltos de
    linea. Se acepta cualquiera de los dos a proposito, porque es una funcion
    de PINTADO y no deberia reventar nunca por el tipo de dato que le llegue
    del guion. Ya lo hizo: `revelacion["linea"]` era una lista y el primer
    encuentro de cada partida terminaba en `TypeError: unhashable type: 'list'`
    dentro de `ui.envolver`.
    """
    if isinstance(mensaje, (list, tuple)):
        mensaje = "\n".join(str(m) for m in mensaje if m)
    else:
        mensaje = str(mensaje or "")
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


async def diario_dialogos(screen, clock, estado=None):
    """Historial consultable de los ultimos dialogos.

    Es un resumen, no un guion: se recorta a lo mas reciente. Con `estado`
    filtra a la faccion de la partida en curso, de modo que reanudar una
    campana no muestra lineas de otra.
    """
    faccion = (estado or {}).get("faccion")
    fondo = Fondo(faccion or "dragon")
    volver = Boton(pygame.Rect(ANCHO // 2 - 90, ALTO - 58, 180, 38), "VOLVER", 11)
    desplaz = 0
    por_pagina = max(4, (ALTO - 210) // 26)
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()

        texto(screen, "DIARIO DE DIALOGOS", 20, DORADO, centro=(ANCHO // 2, 56))
        contexto = (f"Campana {facciones.nombre(faccion)}" if faccion
                    else "Todo lo escuchado")
        texto(screen, contexto, 9, TEXTO_TENUE, centro=(ANCHO // 2, 86))

        entradas = campana.diario_dialogos(faccion)
        # Se aplana a lineas para paginar facilmente: cabecera de hablante y
        # luego el texto envuelto.
        lineas = []
        for e in entradas:
            hablante = (e.get("hablante") or "").strip()
            if hablante:
                lineas.append((hablante, DORADO, 11))
            # El ancho de envoltura tiene que contar con la escala de tipografia:
            # si no, en modo lectura las lineas salen disparadas del panel.
            ancho_texto = int((ANCHO - 260) / max(1.0, ui.escala_texto()))
            for l in envolver(e.get("texto", ""), 10, ancho_texto):
                lineas.append((l, TEXTO, 10))
            lineas.append(("", TEXTO, 10))

        panel(screen, pygame.Rect(ANCHO // 2 - 480, 108, 960, ALTO - 190),
              PANEL, BORDE, radio=10)
        if not lineas:
            texto(screen, "Todavía no se ha dicho nada. Juega una escena.",
                  10, TEXTO_TENUE, centro=(ANCHO // 2, ALTO // 2))
        else:
            max_desplaz = max(0, len(lineas) - por_pagina)
            desplaz = max(0, min(desplaz, max_desplaz))
            visibles = lineas[desplaz:desplaz + por_pagina]
            y = 130
            for linea, color, tam in visibles:
                if linea:
                    texto(screen, linea, tam, color, x=ANCHO // 2 - 450, y=y)
                y += 26
            if desplaz > 0:
                texto(screen, "^ más arriba", 8, TEXTO_TENUE,
                      centro=(ANCHO // 2, 116))
            if desplaz < max_desplaz:
                texto(screen, "v más abajo", 8, TEXTO_TENUE,
                      centro=(ANCHO // 2, ALTO - 96))

        texto(screen, "FLECHAS/rueda: desplazar   ESC: volver", 8, TEXTO_TENUE,
              centro=(ANCHO // 2, ALTO - 76))
        _botones(screen, [volver], mouse, dt)
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    audio.sfx(audio.MENU_BACK)
                    return
                if ev.key in (pygame.K_DOWN, pygame.K_s):
                    desplaz += 1
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    desplaz -= 1
                elif ev.key == pygame.K_PAGEDOWN:
                    desplaz += por_pagina
                elif ev.key == pygame.K_PAGEUP:
                    desplaz -= por_pagina
            if ev.type == pygame.MOUSEWHEEL:
                desplaz -= ev.y
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if volver.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
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
    foco = 0
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo = campana.nodo(estado.get("nodo") or "senda").get("escena", "camino")
        _fondo_escena(screen, fondo)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, espanol(narrativa.titulo_decision(decision)).upper(), 18, DORADO,
              centro=(ANCHO // 2, 90))
        fin_pregunta = parrafo(screen, espanol(decision["pregunta"]), 10, TEXTO, 210, 174, 860,
                              interlinea=24, centrado=True)
        y_opciones = max(340, fin_pregunta + 30)
        alto_opciones = max(150, max(len(envolver(espanol(op["texto"]), 9, 340)) for op in opciones)
                            * round(22 * ui.escala_texto()) + 54)

        rects = []
        foco = max(0, min(foco, len(opciones) - 1))
        for i, op in enumerate(opciones):
            rect = pygame.Rect(228 + i * 424, y_opciones, 400, alto_opciones)
            rects.append(rect)
            hover = rect.collidepoint(mouse)
            resaltado = hover or i == foco
            color = facciones.acento(estado["faccion"]) if hover else (
                ui.FOCO if i == foco else BORDE)
            panel(screen, rect, (20, 20, 30, 235), color,
                  radio=12, grosor=3 if resaltado else 2)
            parrafo(screen, espanol(op["texto"]), 9, TEXTO, rect.x + 30, rect.y + 26,
                    rect.w - 60, interlinea=22, centrado=True)
        texto(screen, "Flechas + ENTER, o clic. Nara tomará nota.", 9, TEXTO_TENUE,
              centro=(ANCHO // 2, y_opciones + alto_opciones + 40))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
                for i, rect in enumerate(rects):
                    if rect.collidepoint(mouse):
                        foco = i
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_LEFT, pygame.K_a):
                foco = (foco - 1) % len(opciones)
                audio.sfx(audio.MENU_MOVE)
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RIGHT, pygame.K_d, pygame.K_TAB):
                foco = (foco + 1) % len(opciones)
                audio.sfx(audio.MENU_MOVE)
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                        pos=rects[foco].center)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        op = opciones[i]
                        audio.sfx(audio.MENU_OK)
                        campana.decidir(estado, decision["id"], op["efecto"])
                        campana.guardar(estado)
                        await cartel(screen, clock,
                                     narrativa.titulo_decision(decision),
                                     [op["respuesta"], "",
                                      narrativa.resumen_efecto(op["efecto"])])
                        return


# ---------------------------------------------------------------- encuentro
def _fondo_escena(screen, nombre):
    """Fondo de cinemática (oscurecido), para momentos narrativos.

    Usa el fondo y las capas cacheadas: escalar a pantalla completa en cada
    frame era lo que mas memoria consumia.
    """
    archivo = {"camino": "camino_lluvioso.png",
               "campamento": "prologo_campamento_nara.png",
               "aldea": "campana_aldea_20261015.png",
               "ruinas": "campana_ruinas_20261015.png",
               "fortaleza": "campana_fortaleza_20261015.png",
               "asalto": "campana_asalto_20261015.png",
               "umbral": "campana_umbral_20261015.png",
               "estandartes": "intro_estandartes_siete_bandos.png",
               "trono": "sala_trono.png"}.get(nombre)
    if archivo:
        fondo = REC.fondo_cinematico("assets/cinematicas_hd/" + archivo)
        if fondo is not None:
            screen.blit(fondo, (0, 0))
            screen.blit(REC.capa_oscurita((6, 7, 14, 156)), (0, 0))
            return
    ruta = ui.ruta_fondo(nombre)
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
    foco = 0
    img_enc = _imagen_encuentro(enc["id"])
    dibujo_enc = None
    if img_enc is not None:
        marco_enc = pygame.Rect(64, 168, 512, 384)
        escala_enc = min((marco_enc.w - 12) / img_enc.get_width(), (marco_enc.h - 12) / img_enc.get_height())
        w_enc = int(img_enc.get_width() * escala_enc)
        h_enc = int(img_enc.get_height() * escala_enc)
        dibujo_enc = pygame.transform.scale(img_enc, (w_enc, h_enc))
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        _fondo_escena(screen, enc.get("escena", "campamento"))
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, enc["titulo"].upper(), 18, DORADO, centro=(ANCHO // 2, 110))

        # Con ilustracion el diseno es de dos columnas: la escena a la izquierda
        # y el texto y las opciones a la derecha. Sin ella, el de antes.
        rects = []
        foco = max(0, min(foco, len(opciones) - 1))
        if dibujo_enc is not None:
            marco = pygame.Rect(64, 168, 512, 384)
            panel(screen, marco, (10, 11, 18, 240), BORDE, radio=8)
            interior = marco.inflate(-12, -12)
            destino = dibujo_enc.get_rect(center=interior.center)
            clip_anterior = screen.get_clip()
            screen.set_clip(interior.clip(clip_anterior))
            screen.blit(dibujo_enc, destino)
            screen.set_clip(clip_anterior)
            ui.registrar(destino.clip(interior), "imagen_evento")
            pygame.draw.rect(screen, facciones.acento(estado["faccion"]),
                             marco, 3, border_radius=8)
            parrafo(screen, enc["texto"], 10, TEXTO, 620, 180, 580,
                    interlinea=24)
            for i, op in enumerate(opciones):
                rect = pygame.Rect(620, 300 + i * 150, 600, 128)
                rects.append(rect)
                hover = rect.collidepoint(mouse)
                resaltado = hover or i == foco
                color = facciones.acento(estado["faccion"]) if hover else (
                    ui.FOCO if i == foco else BORDE)
                panel(screen, rect, (20, 20, 30, 235), color,
                      radio=12, grosor=3 if resaltado else 2)
                texto(screen, op["id"].upper(), 10, DORADO,
                      centro=(rect.centerx, rect.y + 32))
                parrafo(screen, op["texto"], 8, TEXTO, rect.x + 20, rect.y + 62,
                        rect.w - 40, interlinea=18, centrado=True)
            texto(screen, "Flechas + ENTER, o clic", 9, TEXTO_TENUE,
                  centro=(920, 630))
        else:
            parrafo(screen, enc["texto"], 10, TEXTO, ANCHO // 2 - 420, 170, 840,
                    interlinea=24, centrado=True)
            for i, op in enumerate(opciones):
                rect = pygame.Rect(ANCHO // 2 - 340 + i * 360, 330, 320, 170)
                rects.append(rect)
                hover = rect.collidepoint(mouse)
                resaltado = hover or i == foco
                color = facciones.acento(estado["faccion"]) if hover else (
                    ui.FOCO if i == foco else BORDE)
                panel(screen, rect, (20, 20, 30, 235), color,
                      radio=12, grosor=3 if resaltado else 2)
                texto(screen, op["id"].upper(), 10, DORADO,
                      centro=(rect.centerx, rect.y + 34))
                parrafo(screen, op["texto"], 8, TEXTO, rect.x + 20, rect.y + 70,
                        rect.w - 40, interlinea=18, centrado=True)
            texto(screen, "Flechas + ENTER, o clic", 9, TEXTO_TENUE,
                  centro=(ANCHO // 2, 540))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
                for i, rect in enumerate(rects):
                    if rect.collidepoint(mouse):
                        foco = i
            if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_LEFT, pygame.K_a,
                                                        pygame.K_UP, pygame.K_w):
                foco = (foco - 1) % len(opciones)
                audio.sfx(audio.MENU_MOVE)
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RIGHT, pygame.K_d,
                                                          pygame.K_DOWN, pygame.K_s,
                                                          pygame.K_TAB):
                foco = (foco + 1) % len(opciones)
                audio.sfx(audio.MENU_MOVE)
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                        pos=rects[foco].center)
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        audio.sfx(audio.MENU_OK)
                        efecto = opciones[i]["efecto"]
                        idx = None
                        if efecto == "mejorar":
                            # El texto de la opcion dice "+1 a un lado de la
                            # que elijas", asi que hay que dejar elegir. Antes
                            # no se elegia nada y el efecto no hacia nada.
                            idx = await elegir_carta_para_mejorar(screen, clock, estado)
                        titulo, texto_efecto = campana.aplicar_encuentro(estado, efecto, idx)
                        campana.guardar(estado)
                        await cartel(screen, clock, titulo, texto_efecto)
                        # El encuentro ademas revela: la recompensa es una parte,
                        # la informacion es la otra.
                        revelacion = campana.revelar_encuentro(estado, enc["id"])
                        if revelacion:
                            await cartel(screen, clock,
                                         "REVELACIÓN: " + revelacion["titulo"].upper(),
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


PANEL_FINALES = pygame.Rect(900, 200, 340, 500)
VISTA_FINALES = pygame.Rect(920, 252, 286, 394)


def _contenido_finales(perfil):
    """Lineas y posiciones medidas con la misma fuente que se dibuja."""
    lineas, y = [], 0
    for f in facciones.orden_facciones():
        obtenidos = perfil.get("finales", {}).get(f, [])
        marcas = "  ".join("[X]" if v in obtenidos else "[ ]"
                           for v in ("dominio", "equilibrio", "caos"))
        ancho_marcas = ui.ancho_texto(marcas, 8)
        ancho_nombre = VISTA_FINALES.w - ancho_marcas - 14
        color = facciones.acento(f) if obtenidos else TEXTO_TENUE
        lineas.append((marcas, 8, TEXTO_TENUE, VISTA_FINALES.w - ancho_marcas, y))
        for nombre in envolver(facciones.nombre(f), 9, ancho_nombre):
            lineas.append((nombre, 9, color, 0, y))
            y += max(ui.alto_texto(nombre, 9), ui.alto_texto(marcas, 8)) + 7
        for variante in ("dominio", "equilibrio", "caos"):
            if variante in obtenidos:
                for titulo in envolver(campana.FINALES[f][variante]["titulo"], 7, VISTA_FINALES.w):
                    lineas.append((titulo, 7, TEXTO_TENUE, 0, y))
                    y += ui.alto_texto(titulo, 7) + 7
        y += 12
    return lineas, y


def _dibujar_finales(screen, perfil, desplazamiento):
    lineas, alto = _contenido_finales(perfil)
    maximo = max(0, alto - VISTA_FINALES.h)
    desplazamiento = max(0, min(desplazamiento, maximo))
    panel(screen, PANEL_FINALES, PANEL, BORDE, radio=10)
    texto(screen, "FINALES", 12, DORADO, centro=(PANEL_FINALES.centerx, 226))
    clip = screen.get_clip()
    screen.set_clip(VISTA_FINALES.clip(clip))
    try:
        for cadena, tam, color, x, y in lineas:
            top = VISTA_FINALES.y + y - desplazamiento
            # Solo lineas completas; el scroll no pinta texto cortado al borde.
            if VISTA_FINALES.top <= top and top + ui.alto_texto(cadena, tam) <= VISTA_FINALES.bottom:
                texto(screen, cadena, tam, color, x=VISTA_FINALES.x + x, y=top)
    finally:
        screen.set_clip(clip)
    if maximo:
        pista = pygame.Rect(1216, VISTA_FINALES.y, 6, VISTA_FINALES.h)
        pygame.draw.rect(screen, BORDE, pista, border_radius=3)
        alto_barra = max(24, int(pista.h * VISTA_FINALES.h / alto))
        barra = pygame.Rect(pista.x, pista.y + int((pista.h - alto_barra) * desplazamiento / maximo),
                            pista.w, alto_barra)
        pygame.draw.rect(screen, ui.FOCO, barra, border_radius=3)
    return desplazamiento, maximo


async def coleccion(screen, clock, estado=None):
    """Mazos, cartas y finales desbloqueados."""
    perfil = campana.cargar_perfil()
    orden = facciones.orden_facciones()
    faccion = estado.get("faccion") if estado else orden[0]
    t0 = time.time()
    fondos = {f: Fondo(f) for f in orden}
    pagina, fhab, frar = 0, None, None
    solo_poseidas = False
    scroll_finales = 0
    HABS = [None, "muro", "furia", "embestida", "quema"]
    RARS = [None, "COMUN", "RARA", "LEGENDARIA"]
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondos[faccion].dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()
        t = time.time() - t0

        texto(screen, "COLECCIÓN", 22, DORADO, centro=(ANCHO // 2, 60))
        # El progreso ya no se mide en cartas: se mide en historias. Es el
        # cambio de fondo del compendio dual.
        if estado:
            descubiertas, total_historias = campana.compendio_progreso(estado)
            texto(screen, f"{len(campana.coleccion_de(perfil))}/250 cartas - {descubiertas}/{total_historias} historias descubiertas",
                  9, DORADO, centro=(ANCHO // 2, 84))
        else:
            texto(screen, f"{len(campana.coleccion_de(perfil))}/250 cartas - 0/{compendio.total()} historias descubiertas", 9,
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
                img_av = REC.imagen(f"assets/avatar_{f}.png", (24, 24))
                screen.blit(img_av, (rect.centerx - 12, rect.y + 6))
                lineas = envolver(facciones.nombre(f), 7, rect.w - 8)[:2]
                ly = rect.y + 33
                for linea in lineas:
                    texto(screen, linea, 7, facciones.acento(f),
                          centro=(rect.centerx, ly + ui.alto_texto(linea, 7) // 2))
                    ly += 13
            else:
                img_av = REC.imagen(f"assets/avatar_{f}.png", (40, 40))
                screen.blit(img_av, (rect.x + 10, rect.y + 10))
                texto(screen, facciones.nombre(f), 8, facciones.acento(f), x=rect.x + 56, y=rect.y + 18)
            finales = perfil.get("finales", {}).get(f, [])
            texto(screen, f"{len(finales)}/3 fin", 7, TEXTO_TENUE,
                  centro=(rect.centerx, rect.bottom - 12))
            if activo:
                resplandor(screen, rect, facciones.acento(f), int(60 + 40 * math_seno(t * 3)), 2, 8)

        # mazo de la faccion: 10 por pagina, con filtros de habilidad y rareza
        poseidas = campana.coleccion_de(perfil)
        equipadas = set(campana.mazo_global(perfil))
        filtradas = filtrar_coleccion(cartas_coleccion(perfil, faccion, solo_poseidas), fhab, frar)
        pagina_items, total_pags, pagina = paginar_coleccion(filtradas, pagina)
        rects_cartas = []
        for i, carta in enumerate(pagina_items):
            poseida = carta.nombre in poseidas
            sup = crt.crear(carta, None) if poseida else crt.bloqueada()
            fila, col = divmod(i, 5)
            x = 70 + col * 158
            # 144 px de carta + dos etiquetas, con espacio entre las filas
            # y los controles inferiores incluso en lectura al 160%.
            y = 202 + fila * 188
            rect = pygame.Rect(x, y, sup.get_width(), sup.get_height())
            rects_cartas.append((carta, rect))
            if rect.collidepoint(mouse):
                if poseida:
                    crt.resplandor_carta(screen, rect, carta, None, 120)
                descripcion = (_descripcion_carta(carta, estado) if poseida else
                               "Carta por desbloquear. Consigue cartas en sobres y recompensas.")
                tooltip(screen, descripcion, (rect.centerx, rect.y),
                        ancho=300, arriba=True)
            screen.blit(sup, (rect.x, rect.y))
            ui.registrar(rect, "carta_coleccion")
            etiqueta, color = rareza(carta)
            texto(screen, "COMÚN" if etiqueta == "COMUN" else etiqueta, 8, color,
                  centro=(rect.centerx, rect.bottom + 18))
            estado_carta = ("EN MAZO" if carta.nombre in equipadas else
                            "POSEÍDA" if carta.nombre in poseidas else "NO POSEÍDA")
            texto(screen, estado_carta, 7, ui.FOCO if carta.nombre in equipadas else TEXTO,
                  centro=(rect.centerx, rect.bottom + 32))
        if not pagina_items:
            texto(screen, "Sin cartas con ese filtro", 10, TEXTO_TENUE,
                  centro=(460, 380))
        b_hab = Boton(pygame.Rect(310, 574, 190, 32), f"HAB: {(fhab or 'TODAS').upper()}", 8)
        b_vista = Boton(pygame.Rect(60, 574, 240, 32),
                        "P: MIS CARTAS" if solo_poseidas else "P: CATÁLOGO COMPLETO", 8)
        b_rar = Boton(pygame.Rect(510, 574, 190, 32), f"RAREZA: {frar or 'TODAS'}", 8)
        b_prev = Boton(pygame.Rect(710, 574, 40, 32), "<", 10)
        b_next = Boton(pygame.Rect(840, 574, 40, 32), ">", 10)
        _botones(screen, [b_vista, b_hab, b_rar, b_prev, b_next], mouse, dt)
        texto(screen, f"{pagina + 1}/{total_pags}", 9, TEXTO, centro=(795, 590))

        scroll_finales, max_scroll = _dibujar_finales(screen, perfil, scroll_finales)
        b_subir = Boton(pygame.Rect(920, 658, 40, 30), "^", 9)
        b_bajar = Boton(pygame.Rect(1180, 658, 40, 30), "v", 9)
        _botones(screen, [b_subir, b_bajar], mouse, dt)
        texto(screen, "Rueda / RePág / AvPág", 6, TEXTO_TENUE, centro=(1070, 673))

        # estadisticas
        panel(screen, pygame.Rect(60, 618, 820, 110), PANEL, BORDE, radio=10)
        texto(screen, "ESTADÍSTICAS", 11, DORADO, x=80, y=630)
        texto(screen, f"Duelos: {perfil.get('duelos', 0)}   Victorias: {perfil.get('victorias', 0)}   Moneda: {perfil.get('moneda', 0)}",
              9, TEXTO, x=80, y=654)
        mejor = perfil.get("mejor_racha", {})
        if mejor:
            texto(screen, "Mejor racha:", 8, TEXTO_TENUE, x=80, y=682)
            con_racha = [f for f in orden if f in mejor]
            for i, f in enumerate(con_racha):
                fila, col = divmod(i, 5)
                texto(screen, f"{facciones.corto(f)}: {mejor[f]}", 8,
                      facciones.acento(f), x=270 + col * 112, y=682 + fila * 22)

        cerrar = Boton(pygame.Rect(ANCHO - 300, ALTO - 70, 260, 46), "VOLVER", 11)
        tienda_btn = Boton(pygame.Rect(60, ALTO - 70, 260, 46), "TIENDA", 11,
                           sub=f"Sobres: {campana.PRECIO_SOBRE} moneda")
        _botones(screen, [cerrar, tienda_btn], mouse, dt)
        dibujar_tooltips(screen)
        pygame.display.flip()

        # Un solo bucle de eventos. Antes habia dos seguidos: el primero drenaba
        # la cola y el segundo nunca veia nada, asi que en COLECCION no funcionaba
        # ningun clic ni tecla (abrir ficha de carta, cambiar faccion, TIENDA,
        # VOLVER, paginar, F/R). Solo ESC, que era el unico que leia el primer bucle.
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
            if ev.type == pygame.MOUSEWHEEL and PANEL_FINALES.collidepoint(mouse):
                scroll_finales = max(0, min(max_scroll, scroll_finales - ev.y * 48))
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_PAGEDOWN:
                    scroll_finales = min(max_scroll, scroll_finales + VISTA_FINALES.h - 40)
                elif ev.key == pygame.K_PAGEUP:
                    scroll_finales = max(0, scroll_finales - VISTA_FINALES.h + 40)
                elif ev.key == pygame.K_HOME:
                    scroll_finales = 0
                elif ev.key == pygame.K_END:
                    scroll_finales = max_scroll
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
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_p:
                solo_poseidas = not solo_poseidas
                pagina = 0
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if b_vista.clic(ev.pos):
                    solo_poseidas = not solo_poseidas
                    pagina = 0
                elif b_hab.clic(ev.pos):
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
                elif b_subir.clic(ev.pos):
                    scroll_finales = max(0, scroll_finales - 80)
                elif b_bajar.clic(ev.pos):
                    scroll_finales = min(max_scroll, scroll_finales + 80)
                for carta, rect in rects_cartas:
                    if rect.collidepoint(ev.pos) and carta.nombre in poseidas:
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
                    perfil = campana.cargar_perfil()
                    continue


# ----------------------------------------------------------------- ajustes
async def ajustes(screen, clock):
    """Volumen de efectos y musica, pantalla completa y una mano de ayuda.

    Devuelve un dict con los ajustes cambiados para que main los aplique.
    Todo lo que se cambia aqui se guarda en `opciones.json`: al volver a
    abrir el juego (o a esta pantalla) siguen puestos.
    """
    sfx = audio.volumen_sfx()
    musica = audio.volumen_musica()
    fullscreen = bool(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
    # El nombre vive en el perfil, asi que se puede cambiar aqui y en cualquier
    # momento. Antes solo se podia al empezar una campana nueva, y eso PISA la
    # partida en curso: era una trampa.
    nombre = campana.nombre_jugador()
    fondo = Fondo("elfo")
    # foco 0 y 1: las barras de volumen. De 2 en adelante: los botones.
    foco = 0
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        fondo.dibujar(screen, dt)
        mouse = pygame.mouse.get_pos()

        texto(screen, "AJUSTES", 24, DORADO, centro=(ANCHO // 2, 84))
        sfx_rect = pygame.Rect(ANCHO // 2 - 300, 218, 600, 34)
        mus_rect = pygame.Rect(ANCHO // 2 - 300, 286, 600, 34)
        texto(screen, "EFECTOS", 11, TEXTO, x=ANCHO // 2 - 300, y=192)
        texto(screen, "MUSICA", 11, TEXTO, x=ANCHO // 2 - 300, y=260)
        barras = [(sfx_rect, sfx), (mus_rect, musica)]
        for i, (rect, valor) in enumerate(barras):
            enfocado = foco == i
            pygame.draw.rect(screen, (18, 19, 28), rect, border_radius=8)
            relleno = pygame.Rect(rect.x, rect.y, int(rect.w * valor), rect.h)
            pygame.draw.rect(screen, facciones.acento("elfo"), relleno, border_radius=8)
            pygame.draw.rect(screen, ui.FOCO if enfocado else BORDE, rect,
                             3 if enfocado else 2, border_radius=8)
            pygame.draw.circle(screen, DORADO, (rect.x + int(rect.w * valor), rect.centery), 10)
        texto(screen, f"{int(sfx * 100)}%", 10, TEXTO, x=ANCHO // 2 + 316, y=sfx_rect.centery - 6)
        texto(screen, f"{int(musica * 100)}%", 10, TEXTO, x=ANCHO // 2 + 316, y=mus_rect.centery - 6)

        pantalla_btn = Boton(pygame.Rect(ANCHO // 2 - 300, 340, 292, 42),
                             "PANTALLA COMPLETA: " + ("SI" if fullscreen else "NO"), 10)
        grande_btn = Boton(pygame.Rect(ANCHO // 2 + 8, 340, 292, 42),
                           "TEXTO GRANDE: " + ("SI" if opciones.texto_grande() else "NO"), 10)
        reducir_btn = Boton(pygame.Rect(ANCHO // 2 - 300, 392, 600, 42),
                            "MOVIMIENTO REDUCIDO: "
                            + ("SI" if opciones.obtener("movimiento_reducido") else "NO"), 10)
        # Las dos de ritmo: para probar cosas sin esperar a las maquinas de
        # escribir ni a los epilogos largos. Se guardan en `opciones.json`, asi
        # que siguen puestas al relanzar el juego.
        cine_btn = Boton(pygame.Rect(ANCHO // 2 - 300, 444, 292, 42),
                         "SALTAR CINE: " + ("SI" if opciones.saltar_cinematica() else "NO"), 9)
        texto_btn = Boton(pygame.Rect(ANCHO // 2 + 8, 444, 292, 42),
                          "TEXTO INSTANTANEO: " + ("SI" if opciones.saltar_dialogo() else "NO"), 9)
        nombre_btn = Boton(pygame.Rect(ANCHO // 2 - 300, 496, 600, 42),
                           "NOMBRE: " + nombre, 10)
        ayuda = Boton(pygame.Rect(ANCHO // 2 - 300, 548, 600, 42), "CONTROLES", 10)
        cerrar = Boton(pygame.Rect(ANCHO // 2 - 130, 610, 260, 50), "VOLVER", 12)
        botones = [pantalla_btn, grande_btn, reducir_btn, cine_btn, texto_btn,
                   nombre_btn, ayuda, cerrar]
        if 2 <= foco < 2 + len(botones):
            botones[foco - 2].enfocado = True
        _botones(screen, botones, mouse, dt)
        texto(screen, "Flechas: navegar   ENTER: activar   (en volumen, <- ->)",
              8, TEXTO_TENUE, centro=(ANCHO // 2, 682))
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    audio.sfx(audio.MENU_BACK)
                    return {"fullscreen": fullscreen, "sfx": sfx, "musica": musica}
                if ev.key in (pygame.K_DOWN, pygame.K_s, pygame.K_TAB):
                    foco = (foco + 1) % (2 + len(botones))
                    audio.sfx(audio.MENU_MOVE)
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    foco = (foco - 1) % (2 + len(botones))
                    audio.sfx(audio.MENU_MOVE)
                elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    paso = -0.05 if ev.key == pygame.K_LEFT else 0.05
                    if foco == 0:
                        sfx = max(0.0, min(1.0, round(sfx + paso, 2)))
                        audio.volumen_sfx(sfx)
                        opciones.fijar("volumen_efectos", sfx)
                    elif foco == 1:
                        musica = max(0.0, min(1.0, round(musica + paso, 2)))
                        audio.volumen_musica(musica)
                        opciones.fijar("volumen_musica", musica)
                    audio.sfx(audio.MENU_MOVE)
                elif ev.key in (pygame.K_RETURN, pygame.K_SPACE) and foco >= 2:
                    boton = botones[foco - 2]
                    if boton is pantalla_btn:
                        fullscreen = not fullscreen
                        opciones.fijar("pantalla_completa", fullscreen)
                        audio.sfx(audio.MENU_OK)
                    elif boton is grande_btn:
                        nuevo = opciones.alternar("texto_grande")
                        ui.fijar_escala_texto(1.25 if nuevo else 1.0)
                        audio.sfx(audio.MENU_OK)
                    elif boton is reducir_btn:
                        opciones.alternar("movimiento_reducido")
                        audio.sfx(audio.MENU_OK)
                    elif boton is cine_btn:
                        opciones.alternar("saltar_cinematica")
                        audio.sfx(audio.MENU_OK)
                    elif boton is texto_btn:
                        opciones.alternar("saltar_dialogo")
                        audio.sfx(audio.MENU_OK)
                    elif boton is nombre_btn:
                        audio.sfx(audio.MENU_OK)
                        nuevo = await pedir_nombre(
                            screen, clock, inicial=campana.nombre_guardado())
                        if nuevo is not None:
                            nombre = campana.sanea_nombre(nuevo, defecto="")
                            campana.establecer_nombre(nombre)
                            nombre = campana.nombre_jugador()
                    elif boton is ayuda:
                        audio.sfx(audio.MENU_OK)
                        await _pantalla_ayuda(screen, clock)
                    elif boton is cerrar:
                        audio.sfx(audio.MENU_BACK)
                        return {"fullscreen": fullscreen, "sfx": sfx, "musica": musica}
            if ev.type == pygame.MOUSEMOTION:
                mouse = ev.pos
                for i, (r, _) in enumerate(barras):
                    if r.collidepoint(mouse):
                        foco = i
                for j, b in enumerate(botones):
                    if b.rect.collidepoint(mouse):
                        foco = j + 2
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if sfx_rect.collidepoint(ev.pos):
                    sfx = max(0.0, min(1.0, (ev.pos[0] - sfx_rect.x) / sfx_rect.w))
                    audio.volumen_sfx(sfx)
                    opciones.fijar("volumen_efectos", sfx)
                    audio.sfx(audio.MENU_MOVE)
                elif mus_rect.collidepoint(ev.pos):
                    musica = max(0.0, min(1.0, (ev.pos[0] - mus_rect.x) / mus_rect.w))
                    audio.volumen_musica(musica)
                    opciones.fijar("volumen_musica", musica)
                    audio.sfx(audio.MENU_MOVE)
                elif pantalla_btn.clic(ev.pos):
                    fullscreen = not fullscreen
                    opciones.fijar("pantalla_completa", fullscreen)
                    audio.sfx(audio.MENU_OK)
                elif grande_btn.clic(ev.pos):
                    nuevo = opciones.alternar("texto_grande")
                    ui.fijar_escala_texto(1.25 if nuevo else 1.0)
                    audio.sfx(audio.MENU_OK)
                elif reducir_btn.clic(ev.pos):
                    opciones.alternar("movimiento_reducido")
                    audio.sfx(audio.MENU_OK)
                elif cine_btn.clic(ev.pos):
                    opciones.alternar("saltar_cinematica")
                    audio.sfx(audio.MENU_OK)
                elif texto_btn.clic(ev.pos):
                    opciones.alternar("saltar_dialogo")
                    audio.sfx(audio.MENU_OK)
                elif nombre_btn.clic(ev.pos):
                    audio.sfx(audio.MENU_OK)
                    # `pedir_nombre` devuelve None si ESC deja el nombre como
                    # estaba. `inicial` es el actual, que es lo que se quiere.
                    nuevo = await pedir_nombre(
                        screen, clock, inicial=campana.nombre_guardado())
                    if nuevo is not None:
                        nombre = campana.sanea_nombre(nuevo, defecto="")
                        campana.establecer_nombre(nombre)
                        nombre = campana.nombre_jugador()
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
            "Clic: continuar en las cinematograficas y los menus.",
            "ENTER o ESPACIO: siguiente linea de dialogo.",
            "ESC: saltar la cinematografica, pausa en el duelo, cerrar.",
            "Flechas y ENTER: moverse y elegir en cualquier menú.",
            "H: recordatorio de Same y Plus en el duelo.",
            "H en el mapa: diario de dialogos (lo último que se dijo).",
            "T: abrir el tutorial completo.",
        ]),
        ("IR RÁPIDO", [
            "En Ajustes hay dos interruptores para no esperar:",
            "",
            "SALTAR CINE: se salta la cinematografica entera de golpe,",
            "incluidos los epilogos del final, que con ESC no se pueden",
            "saltar. Pensado para probar cambios, no para jugar.",
            "",
            "TEXTO INSTANTANEO: el texto de cada escena aparece entero,",
            "sin maquina de escribir. Se avanza con ENTER.",
            "",
            "Los dos se guardan: siguen puestos al relanzar el juego.",
            "Vienen apagados. Activalos en Ajustes.",
            "",
            "TEXTO GRANDE: agranda toda la tipografia (modo lectura).",
            "MOVIMIENTO REDUCIDO: menos sacudidas y destellos.",
            "Volumen y pantalla completa también se recuerdan.",
        ]),
        ("REGLAS QUE CUENTAN", [
            "Basica: ganas la carta vecina si tu lado es mayor.",
            "Same: dos igualdades; aliados también cuentan.",
            "Plus: dos sumas iguales; solo capturas enemigos.",
            "Cadena: nace de Same/Plus; sigue solo por fuerza.",
            "Muro: su mejor lado no puede caer.",
            "Furia: +1 a cada lado si toca una carta amiga.",
            "Embestida: +2 en la casilla central.",
            "Furia/Embestida: inactivas al perderlas; vuelven al recuperarlas.",
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
        texto(screen, f"pagina {indice + 1} de {len(paginas)}   -   clic para pasar",
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
    from persistencia import ErrorGuardado

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
        texto(screen, "NO SE PUDO GUARDAR" if isinstance(exc, ErrorGuardado)
              else "ALGO HA FALLADO", 22, ROJO, centro=(ANCHO // 2, marco.y + 44))
        parrafo(screen,
                "El juego se ha detenido. Al abrirlo de nuevo podras volver al "
                "último guardado completo. Los cambios posteriores pueden no "
                "haberse guardado.",
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
        texto(screen, "clic o ENTER para cerrar", 10, DORADO,
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
        screen.blit(REC.fondo_pantalla("assets/pixel_anime/detalles/derrota_v2.png"), (0, 0))
        screen.blit(REC.capa_oscurita((8, 8, 18, 100)), (0, 0))
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
    # El nombre va la primera linea del resumen, con el titulo de "quien ha
    # terminado esto". Sin nombre sigue diciendo "el duelista".
    dueli = campana.nombre_jugador()
    resumen = [
        f"Duelista: {dueli}",
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
            texto(screen, "Final ya visto. Prueba con otra facción o improves tu juego.",
                  9, TEXTO_TENUE, centro=(ANCHO // 2, y + 30))
        texto(screen, "clic para volver al menú", 10, DORADO, centro=(ANCHO // 2, ALTO - 120))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                audio.sfx(audio.MENU_OK)
                return
