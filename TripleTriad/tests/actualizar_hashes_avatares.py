"""Rellena HASHES_AVATARES_OK de `test_avatares_sellenos.py` con los hashes
reales de ahora mismo.

Se ejecuta SOLO cuando se ha cambiado un avatar a proposito y el test ha
fallado:

    python tests/actualizar_hashes_avatares.py

Imprime el bloque nuevo para pegarlo. No modifica nada por su cuenta: que el
cambio quede en el diff es justo lo que se quiere ver.
"""

import hashlib
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(RAIZ, "assets")
DESTINO = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "test_avatares_sellenos.py")


def hashes():
    with open(DESTINO, encoding="utf-8") as f:
        texto = f.read()
    bloque = texto.split("HASHES_AVATARES_OK = {", 1)[1].split("}", 1)[0]
    nombres = re.findall(r'"([^"]+\.png)":', bloque)
    salida = []
    for nombre in nombres:
        ruta = os.path.join(CARPETA, nombre)
        if not os.path.exists(ruta):
            print("FALTA %s: no esta en disco" % nombre)
            continue
        with open(ruta, "rb") as f:
            salida.append((nombre, hashlib.sha256(f.read()).hexdigest()[:16]))
    return salida


if __name__ == "__main__":
    filas = hashes()
    ancho = max(len(n) for n, _ in filas) + 4
    print("HASHES_AVATARES_OK = {")
    for nombre, h in filas:
        relleno = " " * (ancho - len(nombre) - 3)
        print('    "%s":%s"%s",' % (nombre, relleno, h))
    print("}")
