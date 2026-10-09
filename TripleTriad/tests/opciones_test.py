"""Ajustes de test: las opciones se ponen a su valor POR DEFECTO.

Por que hace falta esto: `opciones.json` esta en el directorio de datos del
jugador, y los tests usan ese mismo directorio (lo fuerzan con
`TRIPLETRIAD_DATA`). Si el desarrollador tiene "SALTAR CINE" activado para
probando, la suite se entera: `test_la_cinematica_termina_pulsando_escape_siempre`
fallaba porque la cinematica ya habia terminado antes de procesar el ESC.

Los tests que depended de las opciones deben usar el contexto de este modulo,
que las deja como vienen por defecto y las restaura al terminar.

    import opciones_test
    with opciones_test.sin_opciones():
        ...

No es un `conftest.py` porque el proyecto usa `unittest`, no pytest.
"""

import os
import sys
import tempfile
from contextlib import contextmanager

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

#: Debe fijarse ANTES de importar `opciones`, que es cuando lee el fichero.
os.environ.setdefault(
    "TRIPLETRIAD_DATA",
    os.path.join(tempfile.gettempdir(), "tt_test_opciones_base"))

import opciones  # noqa: E402


def _fijar_defecto():
    """Pone todas las opciones a su valor por defecto y limpia la cache."""
    opciones.invalidar()
    for clave, valor in opciones._POR_DEFECTO.items():
        opciones.fijar(clave, valor)
    opciones.invalidar()


@contextmanager
def sin_opciones(**valores):
    """Contexto: las opciones valen lo indicado (por defecto, el default).

    Al salir se restauran los valores que tenian. Sirve tanto para forzar el
    default (`with sin_opciones():`) como para probar uno concreto
    (`with sin_opciones(saltar_cinematica=True):`).
    """
    antes = opciones.opciones()
    _fijar_defecto()
    try:
        for clave, valor in valores.items():
            opciones.fijar(clave, valor)
        yield opciones
    finally:
        opciones.invalidar()
        for clave, valor in antes.items():
            opciones.fijar(clave, valor)
        opciones.invalidar()


def setUpModule():
    """unittest llama esto antes de los tests del modulo."""
    _fijar_defecto()