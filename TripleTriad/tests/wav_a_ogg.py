"""Convierte los WAV de `assets/` a OGG (para la build web).

pygbag empaqueta el proyecto tal cual, asi que en la web viajan los dos
formatos si no se quita el WAV. El OGG pesa una décima parte y es lo que
recomienda pygbag: por eso `audio.py` lo prefiere cuando detecta Emscripten.

    python tests/wav_a_ogg.py            # convierte lo que falte
    python tests/wav_a_ogg.py --check    # solo lista lo que falta

Requiere ffmpeg; si no esta en el PATH se busca el que trae imageio-ffmpeg
(deps de moviepy), que es lo que hay instalado en esta maquina.
"""

import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(RAIZ, "assets")


def ffmpeg():
    exe = os.environ.get("FFMPEG")
    if exe and os.path.exists(exe):
        return exe
    from shutil import which

    exe = which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def wavs():
    for carpeta in (ASSETS, os.path.join(ASSETS, "musica")):
        if not os.path.isdir(carpeta):
            continue
        for nombre in sorted(os.listdir(carpeta)):
            if nombre.endswith(".wav"):
                yield os.path.join(carpeta, nombre)


def main():
    check = "--check" in sys.argv
    exe = ffmpeg()
    if not exe:
        print("No encuentro ffmpeg. Instalalo o define FFMPEG=<ruta>")
        return 1
    faltan = []
    gain = 0
    for wav in list(wavs()):
        ogg = wav[:-4] + ".ogg"
        if not os.path.exists(ogg):
            faltan.append(wav)
            continue
        gain += os.path.getsize(wav) - os.path.getsize(ogg)
    for wav in faltan:
        ogg = wav[:-4] + ".ogg"
        if check:
            print("falta", os.path.relpath(ogg, RAIZ))
            continue
        subprocess.run(
            [exe, "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "3", ogg],
            check=True,
        )
        print(f"{os.path.relpath(ogg, RAIZ)}  "
              f"{os.path.getsize(wav) / 1024:.0f} KB -> {os.path.getsize(ogg) / 1024:.0f} KB")
    if not faltan:
        print(f"Todo convertido. El OGG ahorra {gain / 1024 / 1024:.1f} MB en la build web.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
