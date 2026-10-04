"""Audio: efectos y musica por faccion.

Los efectos y las pistas se generan con `assets/crear_sonidos.py` (solo ondas
cuadradas y de sierra, estilo chiptune) para que el juego no dependa de bancos
de sonido externos. Aqui solo se mezclan, con volumen y afinacion por pantalla.
"""

import os

import pygame

from paths import recurso

_ACTIVO = True
_volumen_sfx = 0.55
_volumen_musica = 0.35
_cache_sfx = {}
_cache_musica = {}
_musica_actual = None
_sfx_actuales = {}
_musica_pausada = False


def disponible():
    return _ACTIVO and pygame.mixer.get_init() is not None


def iniciar():
    """Intenta abrir el dispositivo de sonido. Nunca lanza."""
    global _ACTIVO
    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(24)
        _ACTIVO = True
    except Exception:
        _ACTIVO = False
    return _ACTIVO


def volumen_sfx(v=None):
    global _volumen_sfx
    if v is not None:
        _volumen_sfx = max(0.0, min(1.0, v))
    return _volumen_sfx


def volumen_musica(v=None):
    global _volumen_musica
    if v is not None:
        _volumen_musica = max(0.0, min(1.0, v))
        _ajustar_volumen_musica()
    return _volumen_musica


def _ajustar_volumen_musica():
    """Aplica el volumen al stream de música que este sonando."""
    if not disponible():
        return
    try:
        pygame.mixer.music.set_volume(_volumen_musica)
    except Exception:
        pass


def sfx(nombre, volumen=1.0, canal=None):
    """Reproduce un efecto. `canal` permite que dos sonidos se pisen."""
    if not disponible():
        return
    sonido = _cache_sfx.get(nombre)
    if sonido is None:
        ruta = recurso(os.path.join("assets", nombre))
        if not os.path.exists(ruta):
            _cache_sfx[nombre] = False
            return
        try:
            sonido = pygame.mixer.Sound(ruta)
        except Exception:
            _cache_sfx[nombre] = False
            return
        _cache_sfx[nombre] = sonido
    if sonido is False:
        return
    try:
        sonido.set_volume(max(0.0, min(1.0, _volumen_sfx * volumen)))
        if canal is not None:
            anterior = _sfx_actuales.get(canal)
            if anterior is not None:
                anterior.stop()
            _sfx_actuales[canal] = sonido
        sonido.play()
    except Exception:
        pass


def parar_canal(canal):
    sonido = _sfx_actuales.pop(canal, None)
    if sonido is not None:
        try:
            sonido.stop()
        except Exception:
            pass


def musica(nombre, bucle=True):
    """Carga y reproduce una pista. `nombre` sin extension, p.ej. 'musica_humano'."""
    global _musica_actual, _musica_pausada
    if not disponible() or _musica_actual == nombre:
        return
    _musica_actual = nombre
    pista = _cache_musica.get(nombre)
    if pista is None:
        ruta = recurso(os.path.join("assets", "musica", f"{nombre}.wav"))
        if not os.path.exists(ruta):
            _cache_musica[nombre] = False
            return
        try:
            pista = pygame.mixer.music.load(ruta)
        except Exception:
            _cache_musica[nombre] = False
            return
        _cache_musica[nombre] = pista
    if pista is False:
        return
    try:
        pygame.mixer.music.set_volume(_volumen_musica)
        pygame.mixer.music.play(-1 if bucle else 0)
        _musica_pausada = False
    except Exception:
        pass


def pausar_musica():
    global _musica_pausada
    if disponible() and not _musica_pausada:
        try:
            pygame.mixer.music.pause()
            _musica_pausada = True
        except Exception:
            pass


def reanudar_musica():
    global _musica_pausada
    if disponible() and _musica_pausada:
        try:
            pygame.mixer.music.unpause()
            _musica_pausada = False
        except Exception:
            pass


def detener_musica():
    global _musica_actual
    if disponible():
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
    _musica_actual = None


def musica_de_faccion(faccion):
    return f"musica_{faccion}"


# ------------------------------------------------------- atajos de nombres
COLOCAR = "place.wav"
CAPTURAR = "capture.wav"
CADENA = "chain.wav"
VICTORIA = "win.wav"
DERROTA = "lose.wav"
MENU = "menu.wav"
MENU_MOV = "menu_move.wav"
MENU_OK = "menu_ok.wav"
MENU_BACK = "menu_back.wav"
CARD = "card.wav"
DRAG = "drag.wav"
INVALIDO = "invalid.wav"
CINEMA = "cinema.wav"
RECOMPENSA = "reward.wav"
TORNEO = "boss.wav"