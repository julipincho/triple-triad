"""Ajustes que se recuerdan entre ejecuciones.

Lo que hay en `audio.py` (volumen) es de sesion: se aplica al arrancar y se
pierde al cerrar. Aqui vive lo que tiene que sobrevivir a un reinicio, que es
justo lo que se necesita para probar cosas: activar "saltar cinematica" una
vez y que siga activo al volver a lanzar el juego.

Va en su propio fichero `opciones.json` y NO en el perfil: el perfil es de
progreso de partida (coleccion, finales, fragmentos) y las opciones son
preferencias del jugador. Borrar la partida no deberia apagar tus preferencias,
y viceversa.

Cumple las reglas de rendimiento: se lee UNA vez al arrancar y se cachea.
`opciones()` no toca el disco si el valor ya esta cacheado, asi que se puede
llamar desde un bucle sin coste.
"""

import json
import os

from paths import archivo

ARCHIVO = "opciones.json"

#: Valores por defecto. `saltar_cinematica` viene en False a proposito: el
#: epilogo del final esta protegido por diseno (no se puede saltar la parte que
#: explica el final, y hay un test que lo exige). Este interruptor es para
#: quien esta probando y quiere avanzar rapido, no para el juego de verdad.
_POR_DEFECTO = {
    "saltar_cinematica": False,
    "saltar_dialogo": False,
}

_cache = None


def _leer():
    global _cache
    if _cache is not None:
        return _cache
    base = dict(_POR_DEFECTO)
    try:
        with open(archivo(ARCHIVO), encoding="utf-8") as f:
            datos = json.load(f)
        if isinstance(datos, dict):
            for clave in _POR_DEFECTO:
                if clave in datos:
                    base[clave] = bool(datos[clave])
    except (FileNotFoundError, json.JSONDecodeError, OSError, AttributeError):
        pass  # sin fichero o ilegible: los valores por defecto serves
    _cache = base
    return _cache


def opciones():
    """Todas las opciones, ya leidas. Cacheado: no toca disco."""
    return dict(_leer())


def obtener(clave, por_defecto=None):
    valor = _leer().get(clave, por_defecto)
    return valor


def fijar(clave, valor):
    """Cambia una opcion y la guarda. Devuelve el valor guardado."""
    datos = _leer()
    datos[clave] = bool(valor)
    _persistir(datos)
    return datos[clave]


def alternar(clave):
    """Invierte una opcion booleana. Devuelve el valor nuevo."""
    return fijar(clave, not _leer().get(clave, False))


def _persistir(datos):
    try:
        with open(archivo(ARCHIVO), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # sin permiso de escritura: la opcion vive solo en memoria


def invalidar():
    """Olvida la cache. Para tests y para cuando cambia el directorio de datos."""
    global _cache
    _cache = None


# -------------------------------------------------------------- atajos usados

def saltar_cinematica():
    """True si el jugador ha pedido saltar cineumaticas enteras."""
    return obtener("saltar_cinematica", False)


def saltar_dialogo():
    """True si hay que acelerar el efecto de escritura.

    Diferente de saltar la cinematica entera: aqui las escenas se ven pero el
    texto aparece de golpe y se avanza con ENTER, que es lo que hace falta
    para revisar el guion sin esperar la maquina de escribir.
    """
    return obtener("saltar_dialogo", False)