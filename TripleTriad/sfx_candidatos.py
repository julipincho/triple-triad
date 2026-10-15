"""SFX candidatos del Lote 01: turned OFF por defecto; no sustituye nada.

Diseno:
- Cada evento del manifiesto mapea a una MECANICA existente de `partida.py`
  via `eventos`. Si no hay evento wired, el sonido existe pero queda inerte
  (no se reproduce hasta que se cablea), para no sonar fuera de contexto.
- Variantes rotan por un contador reproducible (no `random`): dos partidas
  iguales suenan igual, y un test puede fijar la secuencia.
- Simultaneos: `MAX_SIMULTANEOS` limitavoices de SFX candidatos vivos a la vez;
  al superar, se roba la mas vieja. Un canal con nombre (`canal=`) se detiene
  antes de sonar el siguiente, como hace `audio.sfx` para las capturas.
- Volumen: usa su propio `_volumen_candidatos` separado de musica y del SFX
  base. Nunca toca `audio.volumen_musica` ni `_volumen_sfx`.
- Carga: una sola vez por WAV y cacheada; un archivo ausente se marca `False`
  y no se reintenta cada evento.

NO auto-integrar. Este modulo solo hace posible la activacion tras tu
aprobacion; la bandera `TRIPLETRIAD_SFX_LOTE01` debe estar en "1" y las
llamadas deben cablearse explicitamente en `partida.py`.
"""

import hashlib
import json
import os
import threading

import pygame

from paths import recurso

#: Apagado por defecto. El juego arranca sin estos sonidos.
ACTIVO = os.environ.get("TRIPLETRIAD_SFX_LOTE01", "0") == "1"

#: Cache nombre->Sound|False, protegida por lock (varios hilos? el juego es
#: monohilo, pero el inicializador puede corridas en paralelo en tests).
_lock = threading.Lock()
_cache = {}

#: Cuantos candidatos suenan a la vez como maximo. Evita que una jugada con
#: many capturas dispare diez voces y saturen el tablero/musica.
MAX_SIMULTANEOS = 4

#: Volumen propio de los candidatos (no el del SFX base). Conservative para
#: que al mezclarse con `audio.sfx` no tapen la banda sonora.
_volumen = 0.5

#: Contadores de rotacion de variante por evento (reproducible).
_rotacion = {}

#: Voces vivas para poder robar la mas vieja cuando se supera el maximo.
_voces = []  # lista de (nombre, Sound)

#: Ultimo sonido por (evento, canal) nombrado, para detenerlo antes del siguiente.
_canales = {}


def volumen(v=None):
    global _volumen
    if v is not None:
        _volumen = max(0.0, min(1.0, v))
    return _volumen


def _catalogo():
    try:
        with open(recurso("assets/sfx_candidatos/manifest.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _sonido(nombre):
    """Carga (y cachea) un WAV candidato. False si falta o no es valido."""
    with _lock:
        if nombre in _cache:
            return _cache[nombre]
    ruta = recurso(os.path.join("assets", "sfx_candidatos", nombre))
    if not os.path.exists(ruta):
        _cache[nombre] = False
        return False
    try:
        sonido = pygame.mixer.Sound(ruta)
    except Exception:
        sonido = False
    _cache[nombre] = sonido
    return sonido


def _robar_si_cede():
    """Detiene la voz candidata mas vieja si se pasa MAX_SIMULTANEOS."""
    while len(_voces) >= MAX_SIMULTANEOS:
        _, viejo = _voces.pop(0)
        try:
            viejo.stop()
        except Exception:
            pass


def reproducir(evento, canal=None, vol=1.0):
    """Suena el SFX del `evento` si esta activo.

    Devuelve el nombre del WAV que sono o None. No lanza nunca.
    """
    if not ACTIVO or pygame.mixer.get_init() is None:
        return None
    info = _catalogo().get("eventos", {}).get(evento)
    if not info:
        return None
    variantes = info.get("variantes") or []
    if not variantes:
        return None

    # Rotacion determinista por evento: indice mod len(variantes).
    idx = _rotacion.get(evento, 0)
    _rotacion[evento] = idx + 1
    nombre = variantes[idx % len(variantes)]

    sonido = _sonido(nombre)
    if sonido is False:
        return None

    # Canal con nombre: para el patron de `audio.sfx(..., canal='cap')`, el
    # candidato con el mismo canal se detiene antes de sonar el siguiente.
    if canal is not None:
        clave = (evento, canal)
        anterior = _canales.get(clave)
        if anterior is not None:
            try:
                anterior.stop()
            except Exception:
                pass
        _canales[clave] = sonido
    else:
        _robar_si_cede()
        _voces.append((nombre, sonido))

    try:
        sonido.set_volume(max(0.0, min(1.0, _volumen * vol)))
        sonido.play()
    except Exception:
        return None
    return nombre


#: Reinicia rotacion/canales/voz. Para tests y para no arrastrar voces entre
#: partidas si el proceso vive mucho.
def reset():
    with _lock:
        _cache.clear()
    _voces.clear()
    _canales.clear()
    _rotacion.clear()


#: Los eventos del lote, con el destino mecanico que ya existe en el juego.
#: `ancla` es donde se cablearia; None = existe el sonido pero aun no hay
#: evento visual que lo sincronice (queda inerte hasta conectarlo).
EVENTOS = {
    "card_place": {
        "ancla": "partida.Juego.colocar -> audio.sfx(audio.COLOCAR) (partida.py:347)",
        "ancla_evento_existente": "audio.COLOCAR",
        "nota": "suena al confirmar la jugada; se encaja con la carta entrando al tablero",
    },
    "card_flip": {
        "ancla": "partida._explosion / flash de captura (partida.py:343-346)",
        "ancla_evento_existente": None,
        "nota": "no hay Sonido de flip propio; el flash es el proxy visual. Sincronizar con el frame de la explosion, no con la decision logica. Hook nuevo recomendado",
    },
    "card_capture": {
        "ancla": "partida.Juego.colocar -> _sonido_de_efecto(resumen), canal='cap' (partida.py:352)",
        "ancla_evento_existente": "audio.CAPTURAR",
        "nota": "se solapa con same/plus; decidir que gana cuando coexisten",
    },
    "ability_trigger": {
        "ancla": "reglas.cascada con motivo 'quema' (partida.py:401-405); habilita muria/furia/embestida",
        "ancla_evento_existente": None,
        "nota": "NO hay evento de audio hoy para la activacion de una habilidad. Requiere hook nuevo",
    },
    "same_plus": {
        "ancla": "partida._sonido_de_efecto: audio.SAME / audio.PLUS (partida.py:115-118)",
        "ancla_evento_existente": "audio.SAME / audio.PLUS",
        "nota": "el codigo distingue same y plus; el candidato es uno solo, hay que decidir si cubre ambos o uno",
    },
    "combo_chain": {
        "ancla": "partida._sonido_de_efecto: audio.CADENA (partida.py:119-120)",
        "ancla_evento_existente": "audio.CADENA",
        "nota": "1 disparo por jugada; el README sugiere variar por eslabon",
    },
    "invalid_move": {
        "ancla": "partida.confirmar_jugada con guia invalida -> audio.sfx(INVALIDO,0.5) (partida.py:552)",
        "ancla_evento_existente": "audio.INVALIDO",
        "nota": "mismo punto que INVALIDO base",
    },
    "turn_change": {
        "ancla": "partida: fin de turno de la CPU / mensaje 'tu turno' (partida.py:480-487)",
        "ancla_evento_existente": None,
        "nota": "NO hay evento de audio hoy. Requiere hook nuevo",
    },
}

#: Eventos del manifiesto SIN sonido ya cableado en el juego: necesitan hook.
SIN_ANCLA = tuple(k for k, v in EVENTOS.items() if v["ancla_evento_existente"] is None)
