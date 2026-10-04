"""Genera efectos y musica chiptune con la libreria estandar.

    python assets/crear_sonidos.py

Produce WAVs 22050 Hz mono en assets/ y assets/musica/. La musica es una
pista por faccion, con escala y tempo propios, hecha de pulsos cuadrados,
triangulos y ruido.
"""

import math
import os
import random
import struct
import wave

SR = 22050
CARPETA = os.path.dirname(os.path.abspath(__file__))
MUSICA = os.path.join(CARPETA, "musica")


# ------------------------------------------------------------------ helpers
def _env(i, n, ataque=0.01, caida=0.25):
    """Envolvente simple: ataque rapido y caida exponencial."""
    t = i / n
    if t < ataque:
        return t / ataque
    return max(0.0, (1.0 - (t - ataque) / max(1e-6, 1.0 - ataque)) ** (1.0 / caida * 3.0))


def _escribir(nombre, muestras, carpeta=CARPETA):
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre)
    with wave.open(ruta, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        data = bytearray()
        for v in muestras:
            v = max(-1.0, min(1.0, v))
            data += struct.pack("<h", int(v * 30000))
        w.writeframes(bytes(data))
    return ruta


def _dur(segundos):
    return int(SR * segundos)


def pulso(freq, duracion, vol=0.3, forma="cuadrada", ataque=0.01, caida=0.25,
          detune=0.0, vibrato=0.0):
    """Genera un tono con forma de onda seleccionable."""
    n = _dur(duracion)
    out = [0.0] * n
    fase = 0.0
    fase2 = 0.0
    for i in range(n):
        t = i / SR
        f = freq * (1.0 + vibrato * math.sin(2 * math.pi * 5.5 * t))
        fase += 2 * math.pi * f / SR
        fase2 += 2 * math.pi * (f * (1.0 + detune)) / SR
        if forma == "cuadrada":
            v = 1.0 if math.sin(fase) >= 0 else -1.0
            if detune:
                v = 0.6 * v + 0.4 * (1.0 if math.sin(fase2) >= 0 else -1.0)
        elif forma == "triangular":
            x = (fase / (2 * math.pi)) % 1.0
            v = 4 * abs(x - 0.5) - 1.0
        elif forma == "sierra":
            v = 2 * ((fase / (2 * math.pi)) % 1.0) - 1.0
        else:  # seno
            v = math.sin(fase)
        out[i] = v * vol * _env(i, n, ataque, caida)
    return out


def ruido(duracion, vol=0.3, caida=0.2, filtro=0.35):
    n = _dur(duracion)
    out = [0.0] * n
    ultimo = 0.0
    rnd = random.Random(1234)
    for i in range(n):
        ultimo = ultimo * (1 - filtro) + rnd.uniform(-1, 1) * filtro
        out[i] = ultimo * vol * _env(i, n, 0.005, caida)
    return out


def mix(*partes):
    largo = max(len(p) for p in partes)
    out = [0.0] * largo
    for p in partes:
        for i, v in enumerate(p):
            out[i] += v
    return out


def silence(duracion):
    return [0.0] * _dur(duracion)


def concat(*partes):
    out = []
    for p in partes:
        out.extend(p)
    return out


def repetir(parte, veces):
    out = []
    for _ in range(veces):
        out.extend(parte)
    return out


def _sumar(lista, inicio, muestras):
    """Suma `muestras` en `lista` desde la posicion `inicio`."""
    for i, v in enumerate(muestras):
        if inicio + i < len(lista):
            lista[inicio + i] += v
    return lista


# ------------------------------------------------------------------- efectos
def efectos():
    """Efectos de interfaz y de juego."""
    print("Efectos...")
    # colocar carta: golpe seco de madera
    _escribir("place.wav", mix(
        pulso(180, 0.06, 0.35, "triangular", caida=0.12),
        pulso(320, 0.05, 0.18, "cuadrada", caida=0.1),
        ruido(0.04, 0.12),
    ))
    # captura: campanilla ascendente
    _escribir("capture.wav", mix(
        pulso(660, 0.07, 0.28, "cuadrada"),
        pulso(880, 0.09, 0.24, "cuadrada", detune=0.004),
        pulso(1320, 0.12, 0.16, "triangular", caida=0.35),
    ))
    # cadena: la captura encadena mas capturas
    _escribir("chain.wav", mix(
        pulso(520, 0.06, 0.22, "cuadrada"),
        pulso(700, 0.06, 0.22, "cuadrada"),
        pulso(930, 0.06, 0.22, "cuadrada"),
        pulso(1240, 0.16, 0.2, "triangular", caida=0.4),
        ruido(0.12, 0.1, caida=0.3),
    ))
    # victoria: arpegio mayor
    _escribir("win.wav", concat(
        pulso(523, 0.11, 0.28, "cuadrada"),
        pulso(659, 0.11, 0.28, "cuadrada"),
        pulso(784, 0.11, 0.28, "cuadrada"),
        pulso(1046, 0.34, 0.3, "cuadrada", caida=0.5, detune=0.005),
        pulso(1568, 0.34, 0.12, "triangular", caida=0.5),
    ))
    # derrota: caida descendente
    _escribir("lose.wav", concat(
        pulso(392, 0.14, 0.26, "triangular", caida=0.4),
        pulso(330, 0.14, 0.26, "triangular", caida=0.4),
        pulso(262, 0.18, 0.26, "triangular", caida=0.4),
        pulso(196, 0.5, 0.24, "triangular", caida=0.6),
    ))
    # navegacion
    _escribir("menu_move.wav", pulso(880, 0.04, 0.16, "cuadrada", caida=0.12))
    _escribir("menu_ok.wav", mix(
        pulso(660, 0.05, 0.22, "cuadrada"),
        pulso(990, 0.09, 0.2, "cuadrada"),
    ))
    _escribir("menu_back.wav", mix(
        pulso(500, 0.05, 0.2, "cuadrada"),
        pulso(330, 0.09, 0.18, "cuadrada"),
    ))
    _escribir("menu.wav", pulso(440, 0.06, 0.2, "triangular", caida=0.15))
    # interaccion con cartas
    _escribir("card.wav", pulso(1200, 0.035, 0.12, "sierra", caida=0.1))
    _escribir("drag.wav", mix(
        pulso(240, 0.05, 0.12, "triangular", caida=0.15),
        ruido(0.05, 0.08),
    ))
    _escribir("invalid.wav", mix(
        pulso(180, 0.09, 0.22, "cuadrada"),
        pulso(150, 0.12, 0.18, "cuadrada", caida=0.3),
    ))
    # cinematica: golpe grave de parchment
    _escribir("cinema.wav", mix(
        pulso(70, 0.5, 0.3, "sierra", caida=0.7),
        pulso(105, 0.4, 0.16, "triangular", caida=0.6),
        ruido(0.3, 0.08, caida=0.5),
    ))
    # recompensa
    _escribir("reward.wav", concat(
        pulso(784, 0.08, 0.22, "triangular"),
        pulso(988, 0.08, 0.22, "triangular"),
        pulso(1319, 0.24, 0.24, "cuadrada", caida=0.45, detune=0.006),
    ))
    # jefe
    _escribir("boss.wav", mix(
        pulso(58, 0.9, 0.34, "sierra", caida=0.9),
        pulso(87, 0.8, 0.22, "cuadrada", caida=0.8, detune=0.01),
        ruido(0.7, 0.12, caida=0.7, filtro=0.15),
    ))
    print(f"  {len(os.listdir(CARPETA))} ficheros en assets/")


# -------------------------------------------------------------------- musica
# Escala menor harmonica/mayor segun faccion + tempo
ESCALAS = {
    "humano": [0, 2, 3, 5, 7, 8, 11],      # menor natural: resuelta y heroica
    "orco": [0, 2, 3, 5, 7, 8, 10],         # frigia: tensa y primitiva
    "elfo": [0, 2, 4, 7, 9],                # pentatonica mayor: luminosa
    "goblin": [0, 2, 4, 6, 7, 9, 11],       # mayor con paso entero comico
    "hombre_lobo": [0, 2, 3, 5, 7, 8, 10],  # menor con b6: salvaje
    "vampiro": [0, 1, 3, 5, 7, 8, 10],     # menor armonica: oscura
    "dragon": [0, 2, 3, 5, 6, 8, 10],       # menor armonica menor: Dense
}
TONICA = {
    "humano": 220.0, "orco": 146.8, "elfo": 261.6, "goblin": 196.0,
    "hombre_lobo": 164.8, "vampiro": 155.6, "dragon": 130.8,
}
TEMPO = {  # pulsos por minuto
    "humano": 104, "orco": 148, "elfo": 92, "goblin": 150,
    "hombre_lobo": 132, "vampiro": 88, "dragon": 116,
}
OLAS = {  # instrumentos por faccion (una letra por capa)
    "humano": "TMH",
    "orco": "MHH",
    "elfo": "TSSH",
    "goblin": "MMH",
    "hombre_lobo": "MMM",
    "vampiro": "TTS",
    "dragon": "MHH",
}
FORMA = {"T": "triangular", "S": "seno", "M": "cuadrada", "H": "saw"}

# Pistas que no son de faccion: combate y(menu).
# El duelo NO reutiliza la pista del rival: cada enfrentamiento suena igual de
# tenso, sin importar contra quien juegues.
TEMAS = {
    "duelo": {
        "tonica": 146.83,          # re menor
        "escala": [0, 2, 3, 5, 7, 8, 11],
        "tempo": 152,
        "capas": "MTHH",
        "progresion": [0, 5, 3, 7],
        "raiz_bajo": True,
        "reps": 12,                # ~19 s de combate
    },
    "explora": {
        "tonica": 196.0,           # sol mayor
        "escala": [0, 2, 4, 7, 9, 11, 14],   # lidia: limpia, luminosa
        "tempo": 76,
        "capas": "TSS",
        "progresion": [0, 5, 7, 2],
        "raiz_bajo": False,
        "reps": 6,                 # ~19 s tranquila
    },
}


def _nota(base, semitonos):
    return base * (2 ** (semitonos / 12.0))


def _nota(base, semitonos):
    return base * (2 ** (semitonos / 12.0))


def _compas(faccion, pulsos, raiz):
    """Un compas sobre la raiz dada (en semitonos): bajo, arpegio y percusion."""
    escala = ESCALAS[faccion]
    t0 = TONICA[faccion]
    capas = OLAS[faccion]
    largo_pulso = 60.0 / TEMPO[faccion]
    largo = int(SR * largo_pulso)
    partes = [[0.0] * largo for _ in capas]

    def _suma(capa_i, ini, sub):
        for x, v in enumerate(sub):
            if ini + x < largo:
                partes[capa_i][ini + x] += v

    for i, capa in enumerate(capas):
        for k in range(pulsos):
            dur = largo_pulso / pulsos
            ini = int(k * dur * SR)
            if capa == "M":
                semi = raiz if k % 2 == 0 else raiz + 4
                _suma(i, ini, pulso(_nota(t0, semi - 12), dur * 0.8, 0.17,
                                   "cuadrada", caida=0.28, detune=0.006))
            elif capa == "T":
                semi = raiz + escala[(k + i) % len(escala)] + 12
                _suma(i, ini, pulso(_nota(t0, semi), dur * 0.9, 0.06,
                                   "triangular", caida=0.35))
            elif capa == "S":
                for j, off in enumerate((3, 7)):
                    _suma(i, ini, pulso(_nota(t0, raiz + off + 12), dur * 1.5,
                                       0.03 - j * 0.01, "seno", ataque=0.3, caida=0.8))
            else:  # percusion
                _suma(i, ini, ruido(dur * (0.5 if k else 0.3),
                                    0.055 if k else 0.08, caida=0.18,
                                    filtro=0.5 if k else 0.18))
    return partes


PROGRESION = [0, 5, 3, 7, 8, 3, 7, 0]


def _tema(nombre, reps=None):
    """Genera una pista que no pertenece a ninguna faccion (duelo, menu)."""
    cfg = TEMAS[nombre]
    reps = reps if reps is not None else cfg.get("reps", 4)
    t0 = cfg["tonica"]
    escala = cfg["escala"]
    capas = cfg["capas"]
    largo_pulso = 60.0 / cfg["tempo"]
    largo = int(SR * largo_pulso)
    pulsos = 4
    pista = []
    rnd = random.Random(sum(ord(c) for c in nombre) * 31)
    for _ in range(reps):
        for raiz in cfg["progresion"]:
            bloque = [0.0] * largo
            for i, capa in enumerate(capas):
                for k in range(pulsos):
                    dur = largo_pulso / pulsos
                    ini = int(k * dur * SR)
                    if capa == "M":
                        octava = -12 if cfg["raiz_bajo"] else 0
                        semi = raiz + (4 if k % 2 else 0) + octava
                        bloque = _sumar(bloque, ini, pulso(
                            _nota(t0, semi), dur * 0.85, 0.17, "cuadrada",
                            caida=0.25, detune=0.008))
                    elif capa == "T":
                        semi = raiz + escala[(k + i * 2) % len(escala)] + 12
                        bloque = _sumar(bloque, ini, pulso(
                            _nota(t0, semi), dur * 0.9, 0.07, "triangular", caida=0.3))
                    elif capa == "S":
                        for j, off in enumerate((0, 4, 7)):
                            bloque = _sumar(bloque, ini, pulso(
                                _nota(t0, raiz + off + 12), dur * 2.0,
                                0.035 - j * 0.008, "seno", ataque=0.35, caida=0.9))
                    else:  # percusion
                        if k % 2 == 0:  # bombo en el tiempo fuerte
                            bloque = _sumar(bloque, ini, pulso(
                                62, dur * 0.5, 0.14, "seno", ataque=0.005, caida=0.18))
                        bloque = _sumar(bloque, ini, ruido(
                            dur * 0.25, 0.05 if k % 2 else 0.085,
                            caida=0.16, filtro=0.55 if k % 2 else 0.22))
            for x in range(largo):
                bloque[x] *= 0.94 + rnd.random() * 0.12
            pista.extend(bloque)
    maximo = max(abs(v) for v in pista) or 1.0
    pista = [v / maximo * 0.5 for v in pista]
    n = int(SR * 0.08)
    for i in range(n):
        pista[i] *= i / n
        pista[-1 - i] *= i / n
    return pista


def musica_temas():
    """Pistas de duelo y de menu."""
    print("Temas...")
    os.makedirs(MUSICA, exist_ok=True)
    for nombre in TEMAS:
        muestras = _tema(nombre)
        _escribir(f"musica_{nombre}.wav", muestras, MUSICA)
        print(f"  musica_{nombre}.wav  ({len(muestras) / SR:.1f}s)")


def musica():
    """Una pista corta por faccion (en bucle)."""
    print("Musica...")
    os.makedirs(MUSICA, exist_ok=True)
    pulsos = 4
    for faccion in ESCALAS:
        largo_pulso = 60.0 / TEMPO[faccion]
        largo = int(SR * largo_pulso)
        rnd = random.Random(sum(ord(c) for c in faccion))
        pista = []
        for _rep in range(3):
            for raiz in PROGRESION:
                capas = _compas(faccion, pulsos, raiz)
                bloque = [0.0] * largo
                for capa in capas:
                    for x, v in enumerate(capa):
                        bloque[x] += v * (0.94 + rnd.random() * 0.12)
                pista.extend(bloque)
        maximo = max(abs(v) for v in pista) or 1.0
        pista = [v / maximo * 0.5 for v in pista]
        n = int(SR * 0.08)
        for i in range(n):
            pista[i] *= i / n
            pista[-1 - i] *= i / n
        _escribir(f"musica_{faccion}.wav", pista, MUSICA)
        print(f"  musica_{faccion}.wav  ({len(pista) / SR:.1f}s)")


def main():
    efectos()
    musica()
    musica_temas()
    print("Listo.")


if __name__ == "__main__":
    main()