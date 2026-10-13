"""Medidor de costura: donde acaba la pista y donde empieza, en dBFS.

    python medir_cos.py assets/musica/musica_duelo.wav [...]

Manda el valor de pico de los ultimos y primeros 100 ms. Si el final esta
muy por debajo del resto, la pista se oye cortada al repetir con play(-1).
"""
import array
import sys
import wave


def picos_por_frame(crudo, canales):
    muestras = array.array("h")
    muestras.frombytes(crudo)
    if canales == 2:
        return [max(abs(muestras[i]), abs(muestras[i + 1]))
                for i in range(0, len(muestras) - 1, 2)]
    return list(muestras)


def dbs(amplitud):
    if amplitud <= 0:
        return float("-inf")
    return 20 * __import__("math").log10(amplitud / 32767.0)


for ruta in sys.argv[1:]:
    with wave.open(ruta) as w:
        n = w.getnframes()
        sr = w.getframerate()
        canales = w.getnchannels()
        crudo = w.readframes(n)
    frames = picos_por_frame(crudo, canales)
    largo = int(sr * 0.1)
    print(f"{ruta}  {n / sr:.2f}s  {sr} Hz  {canales} ch")
    for etiqueta, ini in (("primeros 100 ms", 0),
                          ("ultimos 100 ms", n - largo),
                          ("pico global", 0)):
        if etiqueta == "pico global":
            pico = max(frames)
        else:
            pico = max(frames[ini:ini + largo])
        print(f"    {etiqueta:<18} {pico:6d}  {dbs(pico):7.1f} dBFS")