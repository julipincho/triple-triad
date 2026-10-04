"""Genera efectos de sonido sencillos (WAV) con la librería estándar."""
import math
import os
import wave

SR = 22050
CARPETA = os.path.dirname(os.path.abspath(__file__))


def tono(freq, dur, vol=0.3, decay=True):
    n = int(SR * dur)
    frames = bytearray()
    for i in range(n):
        t = i / SR
        amp = vol * (1 - i / n) if decay else vol
        v = int(32767 * amp * math.sin(2 * math.pi * freq * t))
        frames += v.to_bytes(2, "little", signed=True)
    return frames


def guardar(nombre, partes):
    with wave.open(os.path.join(CARPETA, nombre), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        for p in partes:
            w.writeframes(p)


guardar("place.wav", [tono(300, 0.08), tono(200, 0.08)])
guardar("capture.wav", [tono(500, 0.06), tono(700, 0.06), tono(900, 0.1)])
guardar("win.wav", [tono(523, 0.12), tono(659, 0.12), tono(784, 0.12), tono(1046, 0.3)])
print("Sonidos creados.")
