"""Empaqueta la build web para itch.io.

Genera `tripletriad-web.zip` con el CONTENIDO de `build/web` en la raiz (itch.io
exige que `index.html` este en la raiz del zip) y SIN la carpeta `cdn/`, que
solo hace falta para servir en local (ver HANDOFF: en itch.io se usa el CDN
oficial de pygame-web).

    python -m pygbag --build --disable-sound-format-error --template plantilla_index.tmpl .
    python tests/empaquetar_itch.py

Despues, en itch.io -> Upload new project -> Uploads: subir el zip, marcar
"This file will be played in the browser" y elegir "Extract the .zip".
"""

import os
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(RAIZ, "build", "web")
DESTINO = os.path.join(RAIZ, "tripletriad-web.zip")
ARCHIVOS = ("index.html", "favicon.png", "tripletriad.apk", "tripletriad.tar.gz")


def main():
    faltan = [n for n in ARCHIVOS if not os.path.isfile(os.path.join(WEB, n))]
    if faltan:
        print(f"Falta en build/web: {', '.join(faltan)}")
        print("Genera la build antes: python -m pygbag --build "
              "--disable-sound-format-error --template plantilla_index.tmpl .")
        return 1
    if os.path.exists(DESTINO):
        os.remove(DESTINO)
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for nombre in ARCHIVOS:
            z.write(os.path.join(WEB, nombre), nombre)
    with zipfile.ZipFile(DESTINO) as z:
        nombres = z.namelist()
    assert "index.html" in nombres, "index.html debe estar en la raiz del zip"
    assert not any(n.startswith("cdn") for n in nombres), "la carpeta cdn no se sube"
    print(f"{DESTINO}  ({os.path.getsize(DESTINO) / 1024 / 1024:.2f} MB)")
    for nombre in nombres:
        print(f"  {nombre}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
