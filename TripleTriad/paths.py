"""Rutas de recursos y de datos guardados.

En modo empaquetado (PyInstaller) los recursos se leen de la carpeta temporal
de MyAppImage y los datos del jugador se escriben junto al ejecutable (si hay
permiso) o en la carpeta de usuario.
"""

import os
import sys


def congelado():
    return getattr(sys, "frozen", False)


def dir_recursos():
    """Carpeta de solo lectura con assets, cartas y fuentes."""
    if congelado():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def recurso(ruta):
    return os.path.join(dir_recursos(), ruta)


def _escribible(directorio):
    try:
        os.makedirs(directorio, exist_ok=True)
        prueba = os.path.join(directorio, ".prueba")
        with open(prueba, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(prueba)
        return True
    except OSError:
        return False


def dir_datos():
    """Carpeta donde se guardan las partidas.

    Se puede forzar con la variable de entorno TRIPLETRIAD_DATA (lo usan los
    tests para no tocar los datos del jugador).
    """
    forcible = os.environ.get("TRIPLETRIAD_DATA")
    if forcible and _escribible(forcible):
        return forcible
    candidatos = []
    if congelado():
        candidatos.append(os.path.dirname(os.path.abspath(sys.executable)))
    else:
        candidatos.append(os.path.dirname(os.path.abspath(__file__)))
        candidatos.append(os.getcwd())
    candidatos.append(os.path.join(os.path.expanduser("~"), "TripleTriad"))
    for c in candidatos:
        if _escribible(c):
            return c
    return os.getcwd()


def archivo(nombre):
    return os.path.join(dir_datos(), nombre)


def log_errores():
    """Devuelve la ruta del log de crash, garantindo que el directorio exista."""
    return archivo("crash.log")