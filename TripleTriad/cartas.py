"""Render de cartas: marco, arte, placa de nombre, orbes de valor y marcas
de habilidad. Las superficies se cachean por contenido para no redibujar
imagenes en cada frame.
"""

import os

import pygame

import facciones
import ui
from paths import recurso
from reglas import HABILIDADES, LADOS, val
from ui import (
    CARD_H,
    CARD_W,
    DORADO,
    REC,
    con_alpha,
    limpio,
    texto,
)

# owner=None -> carta neutra (en la mano antes de colocarla)
AZUL = (86, 158, 244)
ROJO = (226, 76, 66)
NEUTRO = (208, 200, 178)

ICONO_HABILIDAD = {
    "quema": "LLAMA",
    "muro": "MURO",
    "furia": "FURIA",
    "embestida": "EMBESTIDA",
}

_cache = {}

# Techo de la cache de cartas. 250 cartas x combinaciones de dueno,
# sinergia y escala: 2000 es holgado; si se supera se tira entera y se
# vuelve a pintar. Cada entrada pesa ~60 KB: 2000 son ~120 MB en el peor
# caso teorico, en la practica solo viven las que se ven en pantalla.
MAX_CACHE_CARTAS = 2000


def _slug(nombre):
    import re

    s = limpio(nombre).lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def imagen_carta(carta):
    """Carga el arte de una carta (o None si no existe todavia)."""
    ruta = recurso(os.path.join("cartas", f"{carta.bando}_{_slug(carta.nombre)}.png"))
    return REC.imagen(os.path.join("cartas", f"{carta.bando}_{_slug(carta.nombre)}.png")) if os.path.exists(ruta) else None


def _texto_ajustado(cadena, tam, ancho_max, color):
    while True:
        img = REC.fuente(tam).render(limpio(cadena), True, color)
        if img.get_width() <= ancho_max or tam <= 5:
            return img
        tam -= 1


def _lineas_nombre(nombre, ancho_max):
    """Nombre en una o dos lineas, partiendo por la palabra mas larga."""
    limpio_nombre = limpio(nombre)
    if REC.fuente(8).render(limpio_nombre, True, (0, 0, 0)).get_width() <= ancho_max:
        return [limpio_nombre]
    palabras = limpio_nombre.split()
    mejor = None
    for corte in range(1, len(palabras)):
        a, b = " ".join(palabras[:corte]), " ".join(palabras[corte:])
        ancho = max(
            REC.fuente(6).render(a, True, (0, 0, 0)).get_width(),
            REC.fuente(6).render(b, True, (0, 0, 0)).get_width(),
        )
        if mejor is None or ancho < mejor[0]:
            mejor = (ancho, [a, b])
        if ancho <= ancho_max:
            return [a, b]
    return mejor[1] if mejor else [limpio_nombre]


RADIO_ORBE = 10


def posiciones_valor(w, h):
    """Centro de cada orbe de valor: en el punto medio de su lado.

    N arriba-centro, S abajo-centro, O izquierda-centro, E derecha-centro: es
    la disposicion de siempre y se lee sin esfuerzo. Los orbes van apoyados en
    el marco y el retrato se dibuja en la ventana que queda libre entre ellos,
    de forma que ningun numero pisa la imagen.
    """
    r = RADIO_ORBE
    return {
        "N": (w // 2, r + 4),
        "S": (w // 2, h - 28),
        "O": (r + 4, 66),
        "E": (w - r - 4, 66),
    }


def rect_arte(w, h):
    """Ventana central para el retrato: no toca ninguno de los orbes."""
    r = RADIO_ORBE
    return (r + 14, 25, w - 2 * (r + 14), 79)


def crear(carta, dueno=None, habilidad=True, synergy=False, escala=1, bando_dueno=None):
    """Superficie de una carta. `dueno`: 'T', 'C' o None.

    `bando_dueno`: faccion de la baraja que domina la carta ahora mismo.
    Si se pasa, el marco y los orbes toman el color de esa baraja (es el
    feedback visual de quien tiene el dominio); si no, se usa el mapa
    estandar T=AZUL, C=ROJO, None=DORADO.
    """
    clave = (
        carta.nombre,
        tuple(carta.valores[d] for d in LADOS),
        carta.bando,
        carta.habilidad,
        dueno,
        synergy,
        bando_dueno,
    )
    if escala != 1:
        # Las miniaturas de la pantalla de faccion y del menu se piden a
        # escala 0.8 cada frame. `transform.smoothscale` es de las operaciones
        # mas caras que hay, asi que la version escalada tambien se cachea
        # (con su tope: son 35 cartas x 2Dueños, no una cache infinita).
        clave = clave + (escala,)
    if clave in _cache:
        return _cache[clave]

    w, h = CARD_W, CARD_H
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    # Color del marco: el dominio manda (color de la baraja que posee la
    # carta), no el bando original de la carta ni el azul/rojo fijo.
    if bando_dueno and bando_dueno in facciones.FACCIONES:
        claro, oscuro = facciones.FACCIONES[bando_dueno]["paleta"]
    elif dueno == "T":
        claro, oscuro = AZUL, (30, 50, 100)
    elif dueno == "C":
        claro, oscuro = ROJO, (100, 30, 30)
    else:
        claro, oscuro = DORADO, (80, 80, 90)

    # sombra y marco exterior
    pygame.draw.rect(s, (12, 12, 18), (0, 0, w, h), border_radius=8)
    pygame.draw.rect(s, oscuro, (2, 2, w - 4, h - 4), border_radius=7)
    pygame.draw.rect(s, claro, (4, 4, w - 8, h - 8), border_radius=5)

    # arte: panel central, libre de los orbes de valor
    arte = imagen_carta(carta)
    ax, ay, aw, ah = rect_arte(w, h)
    if arte is not None:
        img = pygame.transform.smoothscale(arte, (aw, ah))
        mascara = pygame.Surface((aw, ah), pygame.SRCALPHA)
        for i in range(5):
            mascara.fill((0, 0, 0, 10 * i), (0, 0, aw, ah - 5 - i))
        img.blit(mascara, (0, 0))
        s.blit(img, (ax, ay))
    else:
        inicial = facciones.FACCIONES.get(carta.bando, {}).get("inicial", "?")
        pygame.draw.circle(s, oscuro, (ax + aw // 2, ay + ah // 2), min(aw, ah) // 2)
        pygame.draw.circle(s, claro, (ax + aw // 2, ay + ah // 2), min(aw, ah) // 2, 2)
        texto(s, inicial, 30, (245, 245, 245),
              x=ax + aw // 2 - 12, y=ay + ah // 2 - 18)

    # placa de nombre: bajo el orbe norte, sobre el panel de arte
    lineas = _lineas_nombre(carta.nombre, w - 14)
    alto_placa = 16 if len(lineas) == 1 else 30
    placa = pygame.Surface((w - 8, alto_placa), pygame.SRCALPHA)
    pygame.draw.rect(placa, (0, 0, 0, 200), placa.get_rect(), border_radius=5)
    s.blit(placa, (4, 26))
    if len(lineas) == 1:
        img = _texto_ajustado(lineas[0], 8, w - 14, (245, 245, 245))
        s.blit(img, (w // 2 - img.get_width() // 2, 31))
    else:
        for i, linea in enumerate(lineas[:2]):
            img = _texto_ajustado(linea, 6, w - 14, (245, 245, 245))
            s.blit(img, (w // 2 - img.get_width() // 2, 29 + i * 11))

    # franja del bando: bajo el orbe sur, para que no lo tape
    franja = pygame.Surface((w - 8, 13), pygame.SRCALPHA)
    pygame.draw.rect(franja, oscuro + (235,), franja.get_rect(), border_radius=5)
    s.blit(franja, (4, h - 16))
    etiqueta = facciones.nombre(carta.bando).upper()
    img = _texto_ajustado(etiqueta, 6, w - 16, claro)
    s.blit(img, (w // 2 - img.get_width() // 2, h - 13))

    # indicador de quien capturó la carta: punto de color en la esquina
    # inferior derecha, con el color de la baraja que la domina
    color_dueno = (
        facciones.acento(bando_dueno)
        if bando_dueno in facciones.FACCIONES
        else {"T": AZUL, "C": ROJO}.get(dueno, DORADO)
    )
    pygame.draw.circle(s, color_dueno, (w - 12, h - 12), 6)

    # Valores en el punto medio de cada lado: se leen sin esfuerzo.
    # El panel de arte esta hecho para no solaparlos.
    color_borde = color_dueno
    radio = RADIO_ORBE
    for lado in LADOS:
        cx, cy = posiciones_valor(w, h)[lado]
        pygame.draw.circle(s, (8, 8, 12), (cx, cy), radio)
        pygame.draw.circle(s, color_borde, (cx, cy), radio, 2)
        pygame.draw.circle(s, con_alpha(color_borde, 70), (cx, cy), radio)
        img = REC.fuente(11).render(val(carta.valores[lado]), True, (255, 255, 255))
        s.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))

    # marca de habilidad: sobre la parte baja del retrato (nunca la cara)
    if carta.habilidad and habilidad:
        etiqueta_h = ICONO_HABILIDAD.get(carta.habilidad, carta.habilidad.upper())
        color_h = {
            "quema": (255, 120, 40),
            "muro": (150, 190, 240),
            "furia": (230, 90, 90),
            "embestida": (240, 180, 60),
        }.get(carta.habilidad, DORADO)
        ancho, alto = 46, 13
        bx, by = w // 2 - ancho // 2, ay + ah - alto - 3
        placa_h = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pygame.draw.rect(placa_h, con_alpha(color_h, 225), placa_h.get_rect(), border_radius=5)
        s.blit(placa_h, (bx, by))
        img = _texto_ajustado(etiqueta_h, 6, ancho - 4, (14, 12, 10))
        s.blit(img, (bx + (ancho - img.get_width()) // 2, by + 3))

    # marca de sinergia activa: en la franja del bando, donde no molesta
    if synergy:
        pygame.draw.circle(s, (255, 240, 160), (13, h - 9), 5)
        pygame.draw.circle(s, (12, 12, 18), (13, h - 9), 5, 1)

    if escala == 1:
        _cache[clave] = s
        return s
    escalada = pygame.transform.smoothscale(s, (int(w * escala), int(h * escala)))
    if len(_cache) >= MAX_CACHE_CARTAS:
        _cache.clear()
    _cache[clave] = escalada
    return escalada


def dorso(escala=1):
    """Reverso de carta para el adversario."""
    s = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(s, (12, 12, 18), (0, 0, CARD_W, CARD_H), border_radius=8)
    pygame.draw.rect(s, (58, 40, 84), (3, 3, CARD_W - 6, CARD_H - 6), border_radius=6)
    for i in range(0, CARD_W, 12):
        pygame.draw.line(s, con_alpha((150, 120, 200), 40), (i, 6), (i + 30, CARD_H - 6), 1)
    pygame.draw.rect(s, (96, 70, 130), (3, 3, CARD_W - 6, CARD_H - 6), 2, border_radius=6)
    img = REC.fuente(30).render("?", True, (206, 186, 236))
    s.blit(img, (CARD_W // 2 - img.get_width() // 2, CARD_H // 2 - img.get_height() // 2))
    return pygame.transform.smoothscale(s, (int(CARD_W * escala), int(CARD_H * escala))) if escala != 1 else s


def miniatura(carta, tam=(48, 66)):
    """Carta reducida a `tam`, cacheada.

    La ficha de faccion y el mini mazo del menu pintan cinco miniaturas por
    frame; antes cada una era un `transform.scale` con Surface nueva.
    """
    clave = ("miniatura", carta.nombre, tuple(carta.valores[d] for d in LADOS),
             carta.bando, carta.habilidad, tam)
    if clave in _cache:
        return _cache[clave]
    if len(_cache) >= MAX_CACHE_CARTAS:
        _cache.clear()
    _cache[clave] = pygame.transform.smoothscale(crear(carta, None), tam)
    return _cache[clave]


def rotar(sup, clave, grados):
    """Gira una Superficie `grados` cacheando por grado entero.

    La portada hace flotar cinco cartas girando +-2 grados. `transform.rotate`
    es de las operaciones mas caras que hay (crea una Surface nueva y
    remuestrea), y el giro continuo jamas repite el mismo angulo exacto: sin
    agrupar a grado entero, cada frame serian cinco Surface nuevas. Cinco
    grados por carta y listo: el salto es de 1 grado y no se ve.
    """
    paso = int(round(grados))
    if paso == 0:
        return sup
    return ui.superficie(
        ("rotar",) + tuple(clave) + (paso,),
        lambda: pygame.transform.rotate(sup, paso),
        80,
    )


def sombra(sup, clave, alpha=90):
    """Silueta oscura de una carta, cacheada (la de la portada)."""
    return ui.superficie(
        ("sombra_flota",) + tuple(clave),
        lambda: _sombra_flota(sup.get_size(), alpha),
        40,
    )


def _sombra_flota(tam, alpha):
    s = pygame.Surface(tam, pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    return s


def resplandor_carta(screen, rect, carta, dueno, alpha, bando_dueno=None):
    """Halo de color alrededor de una carta (seleccion, hover).

    Si se pasa `bando_dueno` pinta con la baraja que domina la carta;
    si no, con la propia (comportamiento historico, mazos/coleccion).

    El alpha se agrupa en 16 niveles para poder cachear el halo: se llama en
    cada frame y sin agrupar crearia una Surface nueva cada vez.
    """
    if alpha <= 0:
        return
    color = facciones.acento(bando_dueno) if bando_dueno else (
        facciones.acento(carta.bando) if carta.bando else DORADO
    )
    nivel = min(255, max(1, int(alpha) // 16 * 16))
    halo = ui.superficie(
        ("halo_carta", rect.w, rect.h) + ui.color_cache(color) + (nivel,),
        lambda: _halo_carta(rect.w, rect.h, color, nivel),
    )
    screen.blit(halo, (rect.x - 8, rect.y - 8))


def _halo_carta(w, h, color, alpha):
    halo = pygame.Surface((w + 16, h + 16), pygame.SRCALPHA)
    for i in range(4):
        pygame.draw.rect(
            halo, con_alpha(color, int(alpha * (0.9 - i * 0.2))),
            (i * 4, i * 4, w + 16 - i * 8, h + 16 - i * 8), 2, border_radius=10,
        )
    return halo


def tiene_sinergia(carta, board):
    """True si la carta tiene sinergia de bando activa en el tablero."""
    if not board or not carta.bando:
        return False
    aliadas = sum(
        1 for f in board for x in f
        if x and x.dueno == carta.dueno and x.bando == carta.bando
    )
    return aliadas >= 3


def descripcion_habilidad(habilidad):
    return HABILIDADES.get(habilidad, "")


def _pulsar(surface, t0, duracion=0.35):
    """Efecto de brillo al colocar: escala 1.08 -> 1.0."""
    import time as _time

    k = min(1.0, ((_time.time() - t0) if t0 else 1.0) / duracion)
    if k >= 1:
        return surface
    e = 1 + 0.08 * (1 - ease(k))
    return pygame.transform.smoothscale(surface, (int(CARD_W * e), int(CARD_H * e)))


def ease(k):
    return 1 - (1 - max(0.0, min(1.0, k))) ** 3