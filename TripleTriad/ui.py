"""Capa de interfaz: tema, tipografia, paneles, botones y transiciones.

Todo lo visual del juego pasa por aqui para mantener un lenguaje coherente:
una paleta base, una fuente pixel, bordes con bisel, y animaciones de
hover/aparicion hechas con interpolacion en vez de saltos.
"""

import math
import os
import random
import time

import pygame

from paths import dir_recursos

from paths import recurso

ANCHO, ALTO = 1280, 800
FUENTE_RUTA = os.path.join("assets", "PressStart2P.ttf")

# ------------------------------------------------------------------- paleta
FONDO = (14, 15, 22)
FONDO_ALT = (24, 20, 28)
PANEL = (18, 19, 28, 232)
PANEL_CLARO = (30, 32, 46, 236)
BORDE = (86, 74, 48)
DORADO = (240, 200, 90)
TEXTO = (238, 236, 224)
TEXTO_TENUE = (158, 158, 172)
TEXTO_ON = (255, 240, 200)
ROJO = (226, 76, 66)
VERDE = (96, 214, 128)
AZUL = (86, 158, 244)
MORADO = (176, 132, 226)
SOMBRA = (0, 0, 0, 150)

# ------------------------------------------------------------------- medidas
CARD_W, CARD_H = 104, 144
CARD_GAP = 12
TABLERO_W = 3 * CARD_W + 2 * CARD_GAP
TABLERO_H = 3 * CARD_H + 2 * CARD_GAP
TABLERO_X = (ANCHO - TABLERO_W) // 2
TABLERO_Y = 150
MANO_Y = ALTO - CARD_H - 18
MANO_GAP = 16

PASO_X = CARD_W + CARD_GAP
PASO_Y = CARD_H + CARD_GAP

ANIM_SEGUNDO = 0.18
TRANSICION = 0.45

# Tope de fotogramas por segundo de TODO el juego. Unico lugar donde se decide:
# ningun bucle debe llamar a clock.tick() con otro valor (lo verifica
# tests/test_estabilidad.py). Evita que el consumo de CPU y memoria se dispare.
LIMIT_FPS = 60

# ---------------------------------------------------------------- medidor real
# `tests/auditoria_visual.py` reproduce cada pantalla con un driver de video
# falso y, con `MEDIR` a True, cada `texto`, `panel` y `Boton.dibujar` que
# termina de pintar apunta su rect final a `_REGISTRO`. Asi la auditoria mide
# lo que REALMENTE se dibuja en lugar de replicar las constantes del código a
# mano, que es lo que dejó pasar siete desbordes y dos solapes reales con el
# informe anterior en verde.
#
# Apagado en producción: es un `if` por llamada y no toca el presupuesto de
# frame, pero no es gratis. Solo se enciende desde los tests.
MEDIR = False

# (rect, rol, contenedora) acumulados en el frame actual. `contenedora` es el
# panel más pequeño que contiene al rect (None si ninguno). Se limpia cada
# `pygame.display.flip` para que un texto no herede paneles de frames anteriores.
_REGISTRO = []
# Paneles pintados en el frame actual, para que `texto` pueda buscar su
# contenedora sin tener que conocer la estructura de la pantalla.
_PANELES_ACTUALES = []
# Acumulado de todos los frames, para que el auditor lo analice al terminar.
_REGISTRO_TODOS = []

# Margen de seguridad: los bordes de paneles con `border_radius` pueden
# quedar 1-2 px fuera de su `rect` teórico sin ser un problema real.
MARGEN_SEGURIDAD = 2


def _contenedora(rect):
    """Panel más pequeño de `_PANELES_ACTUALES` que contiene `rect`."""
    if not MEDIR or not _PANELES_ACTUALES:
        return None
    mejor = None
    mejor_area = None
    for p in _PANELES_ACTUALES:
        if p.contains(rect):
            area = p.w * p.h
            if mejor is None or area < mejor_area:
                mejor = p
                mejor_area = area
    return mejor


def registrar(rect, rol, contenedora=None):
    """Apunta un rect final a `_REGISTRO` si `MEDIR` está activo."""
    if not MEDIR:
        return
    r = pygame.Rect(rect)
    _REGISTRO.append((r, rol, contenedora))


def limpiar_medicion():
    """Vacía todos los registros (llamado al cambiar de pantalla o al fin)."""
    _REGISTRO.clear()
    _PANELES_ACTUALES.clear()
    _REGISTRO_TODOS.clear()


def _volcar_frame():
    """Guarda los rects del frame en `_REGISTRO_TODOS` y los prepara para el siguiente."""
    if not MEDIR:
        return
    for r, rol, contenedora in _REGISTRO:
        _REGISTRO_TODOS.append((r, rol, contenedora))
    _REGISTRO.clear()
    _PANELES_ACTUALES.clear()


def _volcar_frame():
    """Guarda los rects del frame en `_REGISTRO_TODOS` y los prepara para el siguiente.

    Se llama sola desde `pygame.display.flip`, el unico punto por el que
    pasan todos los frames del juego (y de los tests). Asi la auditoria no
    depende de que cada pantalla recuerde de llamar a nada.
    """
    for r, rol, contenedora in _REGISTRO:
        _REGISTRO_TODOS.append((r, rol, contenedora))
    _REGISTRO.clear()
    _PANELES_ACTUALES.clear()


# Envolver `pygame.display.flip` una sola vez: es el punto por el que pasan
# todos los frames y no hay que tocar las 40+ pantallas que lo llaman.
_FLIP_ORIGINAL = pygame.display.flip


def _flip_medicion():
    _volcar_frame()
    _FLIP_ORIGINAL()


if MEDIR:
    pygame.display.flip = _flip_medicion


# ------------------------------------------------------------------ recursos
class Recursos:
    """Carga perezosa y cache de imagenes, fuentes y sonidos."""

    def __init__(self):
        self.imagenes = {}
        self.fuentes = {}
        self.sonidos = {}

    def imagen(self, ruta, escala=None):
        clave = (ruta, escala)
        if clave not in self.imagenes:
            completa = recurso(ruta)
            if os.path.exists(completa):
                try:
                    img = pygame.image.load(completa).convert_alpha()
                except pygame.error:
                    # sin modo video activo: cargamos sin convertir
                    img = pygame.image.load(completa)
            else:
                img = pygame.Surface((32, 32), pygame.SRCALPHA)
                pygame.draw.rect(img, (90, 60, 110), img.get_rect(), border_radius=4)
                pygame.draw.line(img, (200, 180, 230), (8, 16), (24, 16), 2)
            if escala:
                img = pygame.transform.smoothscale(img, escala)
            self.imagenes[clave] = img
        return self.imagenes[clave]

    #: Ruta -> (barra_vertical, barra_horizontal) del escalado entero.
    #: La clave es la RUTA y no `id(imagen)`: CPython reutiliza el id de un
    #: objeto liberado, con lo que una imagen nueva podia heredar el letterbox
    #: de una muerta.
    _letterbox = {}

    def _mejor_factor(self, bw, bh, w, h, tope=8):
        """Factor entero con el que la imagen ocupa mas pantalla.

        Se prueban todos los factores enteros y se gana el que menos pantalla
        desperdicia. Hay dos formas de desperdiciarla y NO valen lo mismo:

          - una BARRA (la imagen no llega): se ve negro en pantalla, se nota.
          - un RECORTE (la imagen se pasa): no se ve nada raro, solo pierdes
            trozo del dibujo original.

        Por eso la barra pesa triple: es el defecto visible. Antes de contar,
        la barra se sumaba por producto y por eso, con un fondo cuadrado
        (256x256), ganaba el factor 4 (1024x1024) con 256px de negro a los
        lados frente al factor 5, que si cubria la pantalla entera. El producto
        vale cero en cuanto falta un solo eje, que es justo el caso que
        importaba.

        Con 512x256 en 1280x800 gana el factor 3: 1536x768, recorta 256px de
        ancho y deja 32px de barra vertical (96% de la pantalla con imagen).
        """
        mejor_f, mejor_coste = 1, None
        for f in range(1, tope + 1):
            nw, nh = bw * f, bh * f
            barras = max(0, w - nw) + max(0, h - nh)
            recorte = max(0, nw - w) + max(0, nh - h)
            coste = 3 * barras + recorte
            if mejor_coste is None or coste < mejor_coste:
                mejor_f, mejor_coste = f, coste
        return mejor_f

    def _escalar_pixelart(self, base, destino):
        """Escala pixel art con FACTOR ENTERO, sin inventar un solo pixel.

        Los fondos se generan a 512x256 y la pantalla es 1280x800. Cualquier
        escala fraccionaria (los 2.5x de `smoothscale`) funde pixeles vecinos y
        difumina los bordes: el mundo se ve pixelado y borroso a la vez.

        Aqui se elige el factor entero que mejor ocupa la pantalla, se escala
        con vecino mas cercano (`scale`, no `smoothscale`) y se recorta el eje
        largo. Cada pixel del original se convierte en un bloque limpio de
        fxf, que es como se ve el pixel art de verdad.

        Devuelve una superficie del tamano exacto de `destino`. Las barras que
        la imagen no cubre se rellenan con `FONDO_ALT` (el color del juego), no
        negro puro, para que el corte no cante.
        """
        w, h = destino
        bw, bh = base.get_width(), base.get_height()
        if bw <= 0 or bh <= 0:
            return base

        factor = self._mejor_factor(bw, bh, w, h)
        nw, nh = bw * factor, bh * factor
        img = pygame.transform.scale(base, (nw, nh))

        if nw >= w and nh >= h:
            # Cubre en ambos ejes: se recorta el excedente por el centro. No
            # queda letra: la imagen llega justa a pantalla completa.
            return img.subsurface(pygame.Rect((nw - w) // 2, (nh - h) // 2, w, h))

        # No cubre en algun eje: lienzo a medida con la imagen centrada. El
        # letterbox que queda lo anota `fondo_pantalla`, que es quien sabe la
        # ruta y por tanto la clave de cache.
        lienzo = pygame.Surface((w, h), pygame.SRCALPHA)
        lienzo.fill(FONDO_ALT + (255,))
        lienzo.blit(img, ((w - nw) // 2, (h - nh) // 2))
        return lienzo

    def _cubrir(self, base, destino):
        """Escala `base` para CUBRIR `destino` sin deformar y recorta el sobrante.

        Los fondos son 512x256 (2:1) y la pantalla 1280x800 (1.6:1). Estirarlos
        hasta que entren aplastaba la imagen un 20% en vertical y se veia: las
        personas salian anchas y los edificios bajos. Un fondo de entorno no
        puede deformarse porque el ojo compara la proporcion con la realidad.

        Se escala por el lado que sobra (aqui la altura) y se recorta el
        centro del eje largo. Perder los bordes es barato en un fondo; deformar
        la imagen no lo es.
        """
        return self._escalar_pixelart(base, destino)

    def fondo_pantalla(self, ruta):
        """Imagen reescalada a pantalla completa, cacheada.

        Cubre la pantalla SIN deformar: ver `_cubrir`. Escala una sola vez:
        hacerlo por frame reserva ~4 MB por imagen y cada frame (del orden de
        240 MB/s), que es la causa del consumo de memoria.

        De paso guarda el letterbox que ha quedado, en `_letterbox`, con la
        RUTA como clave. Antes se guardaba con `id(imagen)`, que no vale: CPython
        reutiliza el id de un objeto liberado, asi que una superficie que se
        queda sin referencias dejaba su entrada puesta y una imagen nueva
       Ocogia un letterbox ajeno. Con clave de ruta no puede pasar.
        """
        clave = ("__fondo__", ruta)
        if clave not in self.imagenes:
            base = self.imagen(ruta)
            bw, bh = base.get_width(), base.get_height()
            if (bw, bh) == (ANCHO, ALTO):
                self.imagenes[clave] = base
                self._letterbox[ruta] = (0, 0)
            else:
                self.imagenes[clave] = self._cubrir(base, (ANCHO, ALTO))
                f = self._mejor_factor(bw, bh, ANCHO, ALTO)
                nw, nh = bw * f, bh * f
                self._letterbox[ruta] = (max(0, ALTO - nh), max(0, ANCHO - nw))
        return self.imagenes[clave]

    def barras_de(self, ruta):
        """(vertical, horizontal) del letterbox del fondo de `ruta`.

        La necesita `cinematicas`: si la imagen ya trae su propio marco, no hay
        que poner otro encima. `(0, 0)` significa que la imagen llega justa a
        pantalla y el marco si aporta.

        El argumento es la RUTA, no la superficie: con `id()` la cache no era
        fiable (ver `fondo_pantalla`).
        """
        return self._letterbox.get(ruta, (0, 0))

    def capa_oscurita(self, alpha=(6, 7, 14, 168)):
        """Capa de oscurecido reutilizable (no se reasigna cada frame)."""
        clave = ("__capa__", alpha)
        if clave not in self.imagenes:
            capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            capa.fill(alpha)
            self.imagenes[clave] = capa
        return self.imagenes[clave]

    def fondo_tocado(self, ruta, alpha=(8, 9, 16, 120)):
        """Fondo a pantalla completa con la capa de oscurecido YA pegada.

        Evita el blit SRCALPHA a pantalla completa de cada frame: se compone
        una sola vez y de aqui en adelante es un blit opaco, que es lo mas
        barato que hay. En wasm la diferencia se nota mucho.
        """
        clave = ("__fondo_tocado__", ruta, alpha)
        if clave not in self.imagenes:
            velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            velo.fill(alpha)
            base = pygame.Surface((ANCHO, ALTO))
            base.blit(self.fondo_pantalla(ruta), (0, 0))
            base.blit(velo, (0, 0))
            self.imagenes[clave] = base
        return self.imagenes[clave]

    def vineta(self, pasos=46, fuerza=80):
        """Vineta reutilizable para dar profundidad al fondo."""
        clave = ("__vineta__", pasos, fuerza)
        if clave not in self.imagenes:
            v = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            for i in range(pasos):
                v.fill((0, 0, 0, fuerza), (i, i, ANCHO - 2 * i, ALTO - 2 * i), 1)
            self.imagenes[clave] = v
        return self.imagenes[clave]

    def fuente(self, tam):
        if tam not in self.fuentes:
            ruta = recurso(FUENTE_RUTA)
            try:
                self.fuentes[tam] = pygame.font.Font(ruta, tam)
            except Exception:  # pragma: no cover - sin fuente disponible
                self.fuentes[tam] = pygame.font.SysFont("consolas", tam, bold=True)
        return self.fuentes[tam]

    def sonido(self, nombre):
        if nombre not in self.sonidos:
            try:
                self.sonidos[nombre] = pygame.mixer.Sound(recurso(os.path.join("assets", nombre)))
            except Exception:
                self.sonidos[nombre] = None
        return self.sonidos[nombre]




# ------------------------------------------------------------------ variantes
# Cada escena tiene varias imagenes: el mismo lugar a distinta hora del dia o
# con distinto tiempo. Sin esto se veia la MISMA imagen 36 veces en una partida
# (`campamento` y `camino` son las que mas se repiten).
#
# La variante se elige con la semilla de la PARTIDA, asi que:
#   - dentro de una partida, la escena se ve siempre igual (el jugador no pierde
#     la orientacion porque el sitio cambie de aspecto al entrar y salir)
#   - al empezar otra partida, sale otra combinacion
#
# El nombre del fondo sin numero es el original y sigue siendo el que se usa
# si no hay ninguna variante. `assets/fondos/camino_lluvia.png` es una variante
# de `camino`.

_VARIANTE_SEMILLA = 0
_VARIANTES_CACHE = {}
_ELECCION = {}
RUTA_FONDOS = "assets/fondos"


def fijar_variantes(semilla):
    """Fija la semilla con la que se eligen las variantes de fondo.

    Se llama al entrar en campana con `estado["semilla"]`. Sin llamada previa
    se usa 0, que da siempre la primera variante: es el mismo fondo de siempre,
    que es lo que quiere quien no ha pedido otra cosa.

    La eleccion se RESUELVE AQUI, no en `ruta_fondo`: esa se llama por frame
    desde las cinematograficas y no puede estar barajando ni creando objetos de
    `random` en cada frame. Aqui se recorre la lista de variantes, que ya esta
    cacheada, y se deja el resultado en `_ELECCION`.
    """
    global _VARIANTE_SEMILLA, _ELECCION
    _VARIANTE_SEMILLA = int(semilla or 0)
    # `random.Random(semilla)` y no `semilla % n`: las semillas de campana son
    # de 64 bits, asi que el resto reparte bien, pero si alguna vez se usara un
    # numero pequeno (`nueva_campana` en los tests) `semilla % 5` las recorreria
    # en ciclo y dos partidas seguidas darian la misma combinacion.
    generador = random.Random(_VARIANTE_SEMILLA)
    _ELECCION = {}
    for escena in _VARIANTES_CACHE or _escenas_con_variantes():
        ruta = _variantes_de(escena, generador)
        # La comprobacion de que el archivo existe va AQUI, no en `ruta_fondo`:
        # `ruta_fondo` se llama por frame y `os.path.exists` en un bucle de
        # dibujo es una lectura de disco por frame. Aqui va una vez por
        # partida, y si el archivo no esta se cae al original.
        if ruta and os.path.exists(recurso(ruta)):
            _ELECCION[escena] = ruta
        else:
            _ELECCION[escena] = ""


def semilla_variantes():
    return _VARIANTE_SEMILLA


def _variantes_de(escena, generador):
    """Elige UNA variante de la escena con el generador dado. Ruta o None."""
    variantes = variantes_de(escena)
    if not variantes:
        return None
    return "%s/%s.png" % (RUTA_FONDOS, generador.choice(variantes))


def _escenas_con_variantes():
    """Escenas base que tienen al menos una variante en disco.

    Se lee el directorio una vez. Solo se usa al fijar la semilla, que pasa
    una vez por partida: no es una lectura de disco por frame.
    """
    carpeta = os.path.join(dir_recursos(), "assets", "fondos")
    try:
        archivos = os.listdir(carpeta)
    except OSError:
        return []
    bases = set()
    for f in archivos:
        if not f.endswith(".png"):
            continue
        nombre = f[:-4]
        if "_" in nombre and "_" not in nombre[nombre.index("_") + 1:]:
            bases.add(nombre[:nombre.index("_")])
    return sorted(bases)


def variantes_de(escena):
    """Nombres de archivo de las variantes de una escena. Cacheado.

    Se lista el directorio UNA vez por escena: `ruta_fondo` se llama por frame
    desde las cinematograficas y recorrer la carpeta cada vez seria una
    lectura de disco por frame.
    """
    if escena in _VARIANTES_CACHE:
        return _VARIANTES_CACHE[escena]
    carpeta = os.path.join(dir_recursos(), "assets", "fondos")
    try:
        archivos = os.listdir(carpeta)
    except OSError:
        archivos = []
    salida = []
    for f in archivos:
        if not f.endswith(".png"):
            continue
        nombre = f[:-4]
        if not nombre.startswith(escena + "_"):
            continue
        # El sufijo tiene que ser UNA palabra: `camino_amanecer` es una variante
        # de `camino`, pero `camino_de_ceniza` seria otra escena con su propio
        # nombre. Pedir un guion bajo hacia justo lo contrario de lo que
        # queremos y dejaba la lista vacia.
        if "_" in nombre[len(escena) + 1:]:
            continue
        salida.append(nombre)
    salida.sort()
    _VARIANTES_CACHE[escena] = salida
    return salida


def invalidar_variantes():
    """Olvida la lista de variantes y la eleccion. Para tests y al regenerar."""
    global _ELECCION
    _VARIANTES_CACHE.clear()
    _ELECCION = {}


def ruta_fondo(escena):
    """Ruta del fondo de una escena, ya con su variante elegida.

    `escena` es el nombre sin extension ("camino"). Devuelve siempre un archivo
    que existe: si la escena no tiene variantes, o la que salio no esta en
    disco, cae en el original.

    Esto se llama POR FRAME desde las cinematograficas, asi que es solo una
    consulta a diccionario: la eleccion y la comprobacion del archivo ya
    estan hechas en `fijar_variantes`, que va una vez por partida. Con
    `os.path.exists` aqui habia una lectura de disco por frame.
    """
    return _ELECCION.get(escena) or "%s/%s.png" % (RUTA_FONDOS, escena)




REC = Recursos()


# ------------------------------------------------- cache de superficies/texto
# En la web (WASM/Asyncify) crear una Surface o renderizar una fuente por
# frame cuesta varias veces mas que en nativo. Todo lo que sea repetido
# frame a frame se cachea aqui. `_limpio` es un dict a proposito (no
# functools.lru_cache) para poder limpiarlo al cambiar el modo de video.
_CACHE_SUP = {}
_CACHE_TXT = {}
_LIMPIO = {}

# Techo de entradas por cache. Si se supera se limpia entero: es mejor tirar
# la cache de vez en cuando que degradarse hasta la excepcion.
MAX_CACHE = 600

# Paso de cuantizacion de los colores que se usan como clave de cache. Los
# colores animados (hover de boton, banner que se apaga) darian una clave
# distinta por frame si no se agrupan: la cache crecia sin fin y ademas
# nunca volveria a acertar.
PASO_COLOR = 8


def _cache_put(cache, clave, valor, tope=MAX_CACHE):
    if len(cache) >= tope:
        cache.clear()
    cache[clave] = valor
    return valor


_COLORES = {}


def color_cache(color):
    """Color apto para usarse de clave: canales en multiplos de PASO_COLOR.

    Se memoriza porque se llama un par de veces por texto y por panel (unas
    200 por frame en las pantallas con muchas fichas) y el calculo es mas
    caro que la propia busqueda en el diccionario.
    """
    if type(color) is tuple:
        clave = color
    else:
        clave = tuple(color)
    valor = _COLORES.get(clave)
    if valor is None:
        canales = tuple((int(c) // PASO_COLOR) * PASO_COLOR for c in clave[:3])
        if len(clave) > 3:
            canales += ((int(clave[3]) // PASO_COLOR) * PASO_COLOR,)
        valor = _cache_put(_COLORES, clave, canales, 512)
    return valor


def superficie(clave, factory, tope=MAX_CACHE):
    """Devuelve (y cachea) la Surface descrita por `clave`.

    `factory` solo se ejecuta la primera vez que aparece esa clave. Sirve para
    halos, sombras y viñetas, que antes se creaban de cero en cada frame.
    """
    sup = _CACHE_SUP.get(clave)
    if sup is None:
        sup = _cache_put(_CACHE_SUP, clave, factory(), tope)
    return sup


def limpiar_cache():
    """Vacia las caches de superficies y texto (cambio de pantalla de video)."""
    _CACHE_SUP.clear()
    _CACHE_TXT.clear()
    _LIMPIO.clear()
    _COLORES.clear()


# ----------------------------------------------------------------- tipografia
_REEMPLAZOS = {
    "¡": "!", "¿": "?", "—": "-", "–": "-", "“": '"', "”": '"',
    "‘": "'", "’": "'", "…": "...", "·": "-", "•": "*",
}


def limpio(texto):
    """La fuente pixel no tiene tildes ni signos raros: los limpiamos.

    El resultado se cachea: `normalize` de unicodedata es de las cosas mas
    caras del frame si se repite, y los textos del juego son pocos y fijos.
    """
    original = texto
    largo = _LIMPIO.get(original)
    if largo is not None:
        return largo
    for a, b in _REEMPLAZOS.items():
        texto = texto.replace(a, b)
    import unicodedata

    nfkd = unicodedata.normalize("NFKD", texto)
    largo = "".join(c for c in nfkd if not unicodedata.combining(c))
    return _cache_put(_LIMPIO, original, largo, 4000)


def _superficie_texto(cadena, tam, color, sombra):
    """Surface del texto, con su sombra ya pegada, cacheada por contenido.

    Devuelve (superficie, desplazamiento_x, desplazamiento_y): cuando hay
    sombra la surface es 2 px mayor y el texto va dentro, para poder blitear
    una sola vez en vez de dos.

    El color se agrupa en `PASO_COLOR` para que un texto con alpha que se
    apaga (el banner del duelo) no genere una entrada por frame. Los textos
    translucidos no se cachean: agruparles el alpha se veria a saltos.
    """
    # Un color ausente no puede tumbar la pantalla. Hay tres constructores de
    # escena con defaults distintos y dos de ellos devuelven None; cuando eso
    # llego hasta aca, `len(None)` reventaba y el juego se cerraba entero. La
    # UI no es el lugar donde un dato incompleto se convierte en un crash.
    if color is None:
        color = TEXTO
    if len(color) > 3 and color[3] < 255:
        return _pinta_texto(REC.fuente(tam), limpio(cadena), color, sombra)
    color = color_cache(color)
    clave = (cadena, tam, color, sombra)
    par = _CACHE_TXT.get(clave)
    if par is not None:
        return par
    return _cache_put(_CACHE_TXT, clave,
                      _pinta_texto(REC.fuente(tam), limpio(cadena), color, sombra))


def _pinta_texto(fuente, cadena, color, sombra):
    img = fuente.render(cadena, True, color)
    if not sombra:
        return (img, 0, 0)
    neg = fuente.render(cadena, True, (8, 8, 14))
    s = pygame.Surface((img.get_width() + 2, img.get_height() + 2), pygame.SRCALPHA)
    s.blit(neg, (0, 0))
    s.blit(img, (2, 2))
    return (s, 2, 2)


def texto(screen, cadena, tam, color=TEXTO, centro=None, y=None, x=None, sombra=True):
    """Dibuja texto ya limpio. `centro` = (x, y) para centrar."""
    img, dx, dy = _superficie_texto(str(cadena), tam, color, sombra)
    ancho, alto = img.get_width() - dx, img.get_height() - dy
    if centro:
        x = centro[0] - ancho // 2
        y = centro[1] - alto // 2
    elif x is None:
        x = (ANCHO - ancho) // 2
    if y is None:
        y = 0
    screen.blit(img, (x - dx, y - dy))
    # La auditoria mide el rect final de verdad. Con MEDIR apagado no se
    # construye ni un solo Rect: en el duelo hay ~13 textos por frame y este
    # es el camino mas caliente del juego.
    if MEDIR:
        r = pygame.Rect(x, y, ancho, alto)
        registrar(r, "texto", _contenedora(r))
    return img


def ancho_texto(cadena, tam):
    return _superficie_texto(str(cadena), tam, TEXTO, False)[0].get_width()


def envolver(cadena, tam, ancho_max):
    """Parte un texto en lineas que caben en `ancho_max`."""
    palabras = limpio(cadena).split()
    lineas, actual = [], ""
    for p in palabras:
        prueba = f"{actual} {p}".strip()
        if ancho_texto(prueba, tam) <= ancho_max or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def envoltura_lineas(cadena, tam, ancho_max):
    """Alias explicito de envolver() para el motor de cinematicallyas."""
    return envolver(cadena, tam, ancho_max)


def parrafo(screen, cadena, tam, color, x, y, ancho_max, interlinea=None, centrado=False):
    interlinea = interlinea or tam + 12
    for linea in envolver(cadena, tam, ancho_max):
        if centrado:
            texto(screen, linea, tam, color, centro=(x + ancho_max // 2, y + interlinea // 2))
        else:
            texto(screen, linea, tam, color, x=x, y=y)
        y += interlinea
    return y


# -------------------------------------------------------------------- utiles
def ease(t):
    """Suaviza 0..1 con una curva_OUT."""
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def alpha_t(ahora, t0, duracion):
    """Alpha de entrada: 0 -> 255 en `duracion` segundos."""
    if t0 is None:
        return 255
    k = max(0.0, min(1.0, (ahora - t0) / duracion))
    return int(255 * ease(k))


def mezcla(color_a, color_b, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(color_a[:3], color_b[:3]))


def con_alpha(color, a):
    return (color[0], color[1], color[2], int(max(0, min(255, a))))


def sombra_panel(screen, rect, radio=10, desfase=6):
    s = superficie(("sombra_panel", rect.w, rect.h, radio),
                   lambda: _sombra_panel(rect.w, rect.h, radio))
    screen.blit(s, (rect.x + desfase, rect.y + desfase))


def _sombra_panel(w, h, radio):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, SOMBRA, s.get_rect(), border_radius=radio)
    return s


def _panel_roto(relleno, w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(relleno)
    return s


def panel(screen, rect, relleno=PANEL, borde=DORADO, radio=10, grosor=2, sombra=True):
    if sombra:
        sombra_panel(screen, rect, radio)
    clave = color_cache(relleno)
    s = superficie(("panel", rect.w, rect.h) + clave,
                   lambda: _panel_roto(clave, rect.w, rect.h))
    screen.blit(s, rect.topleft)
    if borde:
        pygame.draw.rect(screen, borde, rect, grosor, border_radius=radio)
    if MEDIR:
        r = pygame.Rect(rect)
        registrar(r, "panel")
        _PANELES_ACTUALES.append(r)
    return rect


def fila_centrada(ancho_item, n, gap=0, ancho_total=None):
    """`x` inicial para centrar `n` elementos de `ancho_item` con `gap` entre ellos.

    Devuelve la x del primer elemento. El patron antigo era
    `ANCHO//2 - n*60 + i*120`, que desplaza la fila `60 - ancho_item/2` pixeles
    del centro y ademas cambia de signo segun el ancho: con cartas de 73px
    quedaban 23px a la izquierda, y con las de 156px del draft, 18px a la
    derecha. Calcularlo aqui quita esa clase de bug entera: cambiar un ancho
    o una cantidad ya no descuadra nada.
    """
    ancho_total = ANCHO if ancho_total is None else ancho_total
    if n <= 0:
        return 0
    paso = ancho_item + gap
    total = n * ancho_item + (n - 1) * gap
    return (ancho_total - total) // 2


def fila_centrada_paso(ancho_item, n, gap=0, ancho_total=None):
    """Igual que `fila_centrada` pero devuelve tambien el paso entre elementos.

    Devuelve `(x0, paso)`. Se usa donde la posicion depende de una flotacion
    por indice: el anclaje se centra una vez y el movimiento se suma encima.
    """
    ancho_total = ANCHO if ancho_total is None else ancho_total
    paso = ancho_item + gap
    return fila_centrada(ancho_item, n, gap, ancho_total), paso


def fila_centrada_por_centro(ancho_item, n, paso, ancho_total=None):
    """`x` del CENTRO del primer elemento, para filas Pintadas por su centro.

    La portada blitea cada carta en `x - ancho//2`, o sea `x` es el centro. Con
    la cuenta por bordes salia mal: los centros iban de 120 a 1080, centro
    600, y la fila quedaba 40px a la izquierda de los 640 de la pantalla.

    Derivacion: la fila ocupa, de centro a centro, `(n-1)*paso`; para que el
    conjunto quede centrado, el primer centro va a
    `ancho/2 - (n-1)*paso/2`.
    """
    ancho_total = ANCHO if ancho_total is None else ancho_total
    if n <= 1:
        return ancho_total // 2
    return ancho_total // 2 - (n - 1) * paso // 2


def panel_vineta(screen, alpha=0):
    """Vineta perimetral. Cacheada por nivel de alpha.

    Antes creaba una Surface de 1280x800 y pintaba 40 rectangulos en cada
    frame; ahora son 8 niveles precalculados y un solo blit.
    """
    if alpha <= 0:
        return
    nivel = min(15, int(alpha * 16 / 255) + 1)
    v = superficie(
        ("vineta", nivel),
        lambda: _panel_vineta(nivel * 255 // 16),
    )
    screen.blit(v, (0, 0))


def _panel_vineta(alpha):
    v = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for i in range(0, 40):
        a = int(alpha * (i / 40) * 0.5)
        pygame.draw.rect(v, (0, 0, 0, a), (i, i, ANCHO - 2 * i, ALTO - 2 * i), 1)
    return v


def linea_horizontal(screen, y, x0=60, x1=ANCHO - 60, color=BORDE, grosor=1, alpha=255):
    clave = color_cache(con_alpha(color, alpha))
    rgb, a = clave[:3], clave[3]
    s = superficie(
        ("linea", x0, x1 - x0, grosor) + clave,
        lambda: _linea_horizontal(x1 - x0, grosor, rgb, a),
    )
    screen.blit(s, (x0, y))


def _linea_horizontal(ancho, grosor, color, alpha):
    s = pygame.Surface((ancho, grosor), pygame.SRCALPHA)
    s.fill(con_alpha(color, alpha))
    return s


# ------------------------------------------------------------------ botones
class Boton:
    """Boton con estados hover/presion, atajos y animación de escala."""

    def __init__(self, rect, etiqueta, tam=13, relleno=PANEL, borde=DORADO,
                 color=TEXTO, acento=None, sub=None, atajo=None):
        self.rect = pygame.Rect(rect)
        self.etiqueta = etiqueta
        self.tam = tam
        self.relleno = relleno
        self.borde = borde
        self.color = color
        self.acento = acento or borde
        self.sub = sub
        self.atajo = atajo
        self.hover = 0.0
        self.presionado = 0.0
        self.habilitado = True
        self._t0 = time.time()

    def actualizar(self, dt, mouse):
        dentro = self.habilitado and self.rect.collidepoint(mouse)
        objetivo = 1.0 if dentro else 0.0
        self.hover += (objetivo - self.hover) * min(1.0, dt * 14)
        self.presionado = max(0.0, self.presionado - dt * 5)
        return dentro

    def pulsar(self):
        self.presionado = 1.0

    def dibujar(self, screen, ahora=None):
        """Hover: el boton sube y engorda el borde. Pulsado: se hunde."""
        elevacion = -int(7 * self.hover) + int(4 * self.presionado)
        h = self.rect.move(0, elevacion)
        if not self.habilitado:
            panel(screen, h, (18, 18, 24, 180), (70, 70, 80), grosor=2)
            texto(screen, self.etiqueta, self.tam, (110, 110, 120),
                  centro=(h.centerx, h.centery - (6 if self.sub else 0)))
            return
        if self.hover > 0.02:
            resplandor(screen, h, self.acento, int(40 + 90 * self.hover), 2, 10)
        panel(
            screen,
            h,
            con_alpha((26, 27, 38), 215 + 25 * self.hover),
            mezcla(self.borde, self.acento, self.hover),
            grosor=2 + int(2 * self.hover),
        )
        dy = -6 if self.sub else 0
        texto(screen, self.etiqueta, self.tam,
              mezcla(self.color, TEXTO_ON, self.hover),
              centro=(h.centerx, h.centery + dy))
        if self.sub:
            texto(screen, self.sub, 8, TEXTO_TENUE, centro=(h.centerx, h.bottom - 11))
        if self.atajo:
            texto(screen, f"{self.atajo}", 8,
                  con_alpha(mezcla(self.borde, self.acento, self.hover), 200),
                  x=h.right - 18, y=h.y + 6)
        # El botón es su propio contenedor: un texto que pide `centro` dentro
        # del botón queda asociado a él y no a un panel vecino.
        if MEDIR:
            registrar(h, "boton", h)

    def clic(self, pos):
        return self.habilitado and self.rect.collidepoint(pos)


# ----------------------------------------------------------------- eventos
def clic_en(pos, rects):
    return any(r.collidepoint(pos) for r in rects)


def esperar_click_o_tecla(screen, callback=None):
    """Devuelve la posicion del clic o None si se pulso una tecla."""
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        if ev.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            if callback:
                callback(ev)
            return ev
    return None


# ------------------------------------------------------------ transiciones
class Transicion:
    """Fundido a negro para cortar entre pantallas."""

    def __init__(self, duracion=TRANSICION):
        self.duracion = duracion
        self.t = duracion  # 0 = negro total (listo para mostrar)
        self.fase = 1  # 1 = abriendo, -1 = cerrando
        self.al_terminar = None
        self.activo = False

    def abrir(self, callback=None):
        self.t = 0.0
        self.fase = 1
        self.al_terminar = callback
        self.activo = True

    def cerrar(self, callback=None):
        self.t = 0.0
        self.fase = -1
        self.al_terminar = callback
        self.activo = True

    def actualizar(self, dt):
        if not self.activo:
            return
        self.t += dt
        k = min(1.0, self.t / self.duracion)
        if k >= 1.0:
            if self.fase == -1 and self.al_terminar:
                self.al_terminar()
            self.al_terminar = None
            self.activo = False
            self.t = self.duracion

    @property
    def alpha(self):
        if not self.activo:
            return 0
        k = min(1.0, self.t / self.duracion)
        return int(255 * (k if self.fase == -1 else 1 - k))

    def dibujar(self, screen):
        a = self.alpha
        if a > 0:
            s = _capa_negra(a)
            screen.blit(s, (0, 0))


class FundidoTexto:
    """Un texto que aparece letra a letra o se desvanece solo."""

    def __init__(self, cadena, t0=None, duracion=0.5):
        self.cadena = cadena
        self.t0 = t0 if t0 is not None else time.time()
        self.duracion = duracion

    def alpha(self, ahora=None):
        ahora = ahora or time.time()
        return alpha_t(ahora, self.t0, self.duracion)


# Capa auxiliar reutilizable. El fundido de entrada y el de transicion la
# pintan cada frame durante medio segundo; con `fill` no se reserva nada
# (crear una Surface SRCALPHA de 1280x800 son ~4 MB de basura por frame).
_CAPA = None


def _capa_color(color, alpha):
    """Capa de un color plano a pantalla completa, lista para blitear.

    Devuelve la MISMA Surface en todas las llamadas: hay que blitearla antes
    de volver a pedirla (el unico caso son fundidos, uno detras de otro).
    """
    global _CAPA
    if _CAPA is None:
        _CAPA = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    _CAPA.fill((color[0], color[1], color[2], min(255, max(0, int(alpha)))))
    return _CAPA


def _capa_negra(alpha):
    return _capa_color((0, 0, 0), alpha)


def fundido_entrada(screen, t0, duracion=0.45, color=(0, 0, 0)):
    """Capa negra que se desvanece al entrar en una pantalla.

    Se llama en el primer frame de cada pantalla con su propio t0: da la
    sensacion de corte de escena sin tener que coordinar dos pantallas.
    """
    if t0 is None:
        return
    k = min(1.0, (time.time() - t0) / duracion)
    if k >= 1.0:
        return
    a = int(255 * (1 - ease(k)))
    capa = _capa_color(color, a)
    screen.blit(capa, (0, 0))


# ------------------------------------------------------------- fondo animado
# Las chispas se pintan con sprites pre-renderizados y BLEND_RGBA_ADD en vez
# de con `draw.circle` sobre una capa SRCALPHA de 1280x800. La capa obligaba
# a limpiar 4 MB y a pegarla entera con alfa en cada frame: en la web eso solo
# eran ~10 ms. Con los sprites son 70 blits diminutos.
_CHISPA_R = 7
_CHISPA_NIVELES = 8
_CHISPA_COLOR = (220, 210, 190)


def _chispa(nivel, tam):
    """Sprite de una particula: `nivel` de brillo (0..7) y lado `tam`.

    El RGB va premultiplicado porque se suma (BLEND_RGBA_ADD): si solo
    bajáramos el alfa, al sumar se veria el cuadrado entero de la particula.
    """
    brillo = 0.30 + 0.70 * nivel / (_CHISPA_NIVELES - 1)
    s = pygame.Surface((tam, tam), pygame.SRCALPHA)
    r = tam / 2.0
    for y in range(tam):
        for x in range(tam):
            d = math.hypot(x - r + 0.5, y - r + 0.5) / r
            if d >= 1.0:
                continue
            v = int(255 * (1.0 - d) ** 2.2 * brillo)
            s.set_at((x, y), (_CHISPA_COLOR[0] * v // 255, _CHISPA_COLOR[1] * v // 255,
                             _CHISPA_COLOR[2] * v // 255, v))
    return s


class FondoAnimado:
    """Capa de fondo con estelas de ceniza y un resplandor lento."""

    def __init__(self, imagen=None, color_primario=(60, 60, 80), ruta="assets/fondo.png"):
        self.imagen = imagen
        self.ruta = ruta
        self.color = color_primario
        self.particulas = [
            {
                "x": random.uniform(0, ANCHO),
                "y": random.uniform(0, ALTO),
                "v": random.uniform(6, 26),
                "r": random.choice([1, 1, 2, 2, 3]),
                "a": random.uniform(0.15, 0.5),
            }
            for _ in range(70)
        ]
        self.t0 = time.time()

    def actualizar(self, dt):
        for p in self.particulas:
            p["y"] += p["v"] * dt
            p["x"] += p["v"] * 0.25 * dt
            if p["y"] > ALTO + 4:
                p["y"] = -4
                p["x"] = random.uniform(-20, ANCHO)
        return self.t0

    def dibujar(self, screen):
        if self.imagen is not None:
            # fondo + velo ya compuestos: un solo blit opaco por frame
            screen.blit(REC.fondo_tocado(self.ruta, (8, 9, 16, 120)), (0, 0))
        else:
            screen.fill(FONDO)
            for i in range(0, ALTO, 4):
                pygame.draw.line(
                    screen,
                    mezcla(FONDO, self.color, (i / ALTO) * 0.35),
                    (0, i), (ANCHO, i),
                )
        ahora = time.time()
        pulso = 0.5 + 0.5 * math.sin(ahora * 0.4)
        base = _CHISPA_R * 2 + 1
        for p in self.particulas:
            # el brillo late en 8 escalones y el radio en 3: hay 24 sprites
            # pre-renderizados. Con el pulso entero se pediria una Surface
            # nueva por particula y por frame.
            k = p["a"] * (0.6 + 0.4 * pulso)
            nivel = min(_CHISPA_NIVELES - 1, int(k * _CHISPA_NIVELES * 2))
            tam = max(3, int(base * (1 + (p["r"] - 2) * 0.22)))
            chispa = superficie(("chispa", nivel, tam),
                                 lambda n=nivel, t=tam: _chispa(n, t), 32)
            screen.blit(chispa, (int(p["x"]) - tam // 2, int(p["y"]) - tam // 2),
                        special_flags=pygame.BLEND_RGBA_ADD)


# ------------------------------------------------------------------ tooltip
# Los tooltips se apilan y se pintan al final del frame (dibujar_tooltips):
# si se dibujaran en el momento, las cartas siguientes o los botones los
# taparian y el texto quedaba ilegible.
_PENDIENTES = []


def tooltip(screen, cadena, pos, tam=8, ancho=280, lado="auto", arriba=False):
    """Encola un tooltip. Se pinta con dibujar_tooltips() al final del frame.

    `lado` fija la columna ("izq"/"der") y `arriba` lo coloca por encima del
    punto, para no caer sobre la propia carta ni sobre el tablero.
    """
    _PENDIENTES.append((cadena, pos, tam, ancho, lado, arriba))


def dibujar_tooltips(screen):
    """Pinta los tooltips pendientes por encima de todo lo demas."""
    for cadena, pos, tam, ancho, lado, arriba in _PENDIENTES:
        lineas = []
        for trozo in str(cadena).split("\n"):
            lineas.extend(envolver(trozo, tam, ancho - 24) or [""])
        alto = len(lineas) * (tam + 9) + 16
        x, y = _sitiar_tooltip(pos, ancho, alto, lado, arriba)
        rect = pygame.Rect(x, y, ancho, alto)
        sombra_panel(screen, rect, 6)
        panel(screen, rect, (10, 11, 18, 252), DORADO, radio=6, grosor=1, sombra=False)
        ly = y + 8
        for linea in lineas:
            texto(screen, linea, tam, TEXTO, x=x + 12, y=ly)
            ly += tam + 9
    _PENDIENTES.clear()


def _sitiar_tooltip(pos, ancho, alto, lado, arriba):
    """Coloca el tooltip lejos del raton y siempre dentro de la pantalla."""
    px, py = pos
    margen = 18
    if lado == "auto":
        lado = "der" if px < ANCHO * 0.55 else "izq"
    if arriba:
        x, y = px - ancho // 2, py - alto - margen
    elif lado == "der":
        x, y = px + margen, py - alto // 2
    else:
        x, y = px - ancho - margen, py - alto // 2
    x = max(8, min(x, ANCHO - ancho - 8))
    y = max(8, min(y, ALTO - alto - 8))
    return x, y


# ----------------------------------------------------------------- cartitas
def celda_rect(r, c):
    return pygame.Rect(TABLERO_X + c * PASO_X, TABLERO_Y + r * PASO_Y, CARD_W, CARD_H)


# Separación mínima entre cartas de la mano cuando hay muchas: por debajo de
# esto se prefieren solaparlas a dejarlas fuera de pantalla.
MANO_GAP_MIN = 4


def mano_rect(i, total=5):
    """Rectángulo de la carta i-ésima de la mano.

    El paso no es fijo: con pocos huecos usa el hueco normal (CARD_W +
    MANO_GAP), pero cuando la mano tiene más de lo que cabe en pantalla
    achucha el paso hasta que la fila entera quepa. Sin esto, con 24 cartas
    el ancho era 2864 px y el inicio quedaba en -792: 14 de las 24 cartas
    quedaban inalcanzables, y el jugador no podía jugárselas.
    """
    if total <= 1:
        paso = CARD_W
        ancho = CARD_W
    else:
        paso_fijo = CARD_W + MANO_GAP
        paso_ajustado = (ANCHO - CARD_W) / (total - 1)
        paso = max(MANO_GAP_MIN, min(paso_fijo, paso_ajustado))
        ancho = CARD_W + (total - 1) * paso
    inicio = (ANCHO - ancho) // 2
    return pygame.Rect(inicio + i * paso, MANO_Y, CARD_W, CARD_H)


def resplandor(screen, rect, color=DORADO, alpha=120, grosor=3, radio=10):
    """Marco brillante.

    Color y alpha se agrupan (PASO_COLOR y 16 respectivamente) para poder
    cachear la Surface: el halo late continuamente y sin agrupar serian
    ~256 entradas distintas que nunca vuelven a acertar.
    """
    if alpha <= 0:
        return
    nivel = min(255, max(1, int(alpha) // 16 * 16))
    clave = color_cache(color)
    s = superficie(
        ("resplandor", rect.w, rect.h) + clave + (nivel, grosor, radio),
        lambda: _resplandor(rect.w, rect.h, clave, nivel, grosor, radio),
    )
    screen.blit(s, (rect.x - grosor, rect.y - grosor))


def _resplandor(w, h, color, alpha, grosor, radio):
    s = pygame.Surface((w + grosor * 2, h + grosor * 2), pygame.SRCALPHA)
    pygame.draw.rect(s, con_alpha(color, alpha), s.get_rect(), grosor, border_radius=radio)
    return s