"""Escucha las pistas y efectos nuevos sin jugar el prologo entero.

El prologo encadena las cinco pistas en orden, pero para pasar de la primera a
la ultima hay que ganarle el duelo del tutorial a Juan Rajoy. Este script las
reproduce una detras de otra para,oirlas por separado y volver a pasar la que
no convenga.

    python assets/preescuchar.py            # todas, en orden
    python assets/preescuchar.py musica_bosque musica_umbral
    python assets/preescuchar.py sfx
    python assets/preescuchar.py --sin-cortar   # no corta al acabar

Solo abre el mezclador de pygame y da al play; no toca el perfil ni la partida.
"""

import argparse
import os
import sys
import wave

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

SR = 44100

#: (nombre, que escena del prologo suena aqui) en el orden en que se oyen.
PISTAS = [
    ("musica_torneo", "el salon del torneo, antes del tutorial"),
    ("musica_duelo", "el tutorial contra Juan"),
    ("musica_umbral", "la carta sin faccion y el trono"),
    ("musica_apagon", "el apagon (golpe puntual, no se repite)"),
    ("musica_bosque", "el bosque, la torre y Pik"),
    ("musica_campamento", "Nara y el cierre"),
]

#: Los efectos nuevos de las reglas, que antes sonaban como una captura.
SFX = [
    ("capture.wav", "captura normal"),
    ("chain.wav", "cadena"),
    ("same.wav", "same (nuevo)"),
    ("plus.wav", "plus (nuevo)"),
]

#: Candidatos del Lote 01 de SFX. NO estan integrados: viven en
#: `assets/sfx_candidatos/` y solo se escuchan con `--candidatos`.
CANDIDATOS = [
    ("card_place_01.wav", "colocar carta (v1)"),
    ("card_place_02.wav", "colocar carta (v2)"),
    ("card_flip_01.wav", "giro de carta (v1)"),
    ("card_flip_02.wav", "giro de carta (v2)"),
    ("card_capture_01.wav", "captura (v1)"),
    ("card_capture_02.wav", "captura (v2)"),
    ("same_plus_01.wav", "same/plus"),
    ("combo_chain_01.wav", "cadena (v1)"),
    ("combo_chain_02.wav", "cadena (v2)"),
    ("ability_trigger_01.wav", "habilidad (v1)"),
    ("ability_trigger_02.wav", "habilidad (v2)"),
    ("invalid_move_01.wav", "jugada invalida"),
    ("turn_change_01.wav", "cambio de turno"),
]


def _abrir():
    pygame.mixer.init(frequency=SR, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(8)


def _esperar_sin_cortar():
    """Se queda escuchando hasta que la pista acabe de verdad."""
    while pygame.mixer.music.get_busy():
        pygame.time.wait(200)


def _duracion_wav(ruta):
    """Segundos del WAV. pygame 2 quito `mixer.music.get_length()`."""
    with wave.open(ruta) as w:
        return w.getnframes() / float(w.getframerate())


def _reproducir_pista(nombre, donde, sin_cortar):
    ruta = os.path.join(RAIZ, "assets", "musica", f"{nombre}.wav")
    if not os.path.exists(ruta):
        print(f"  - {nombre}: no esta en assets/musica/")
        return False
    dur = _duracion_wav(ruta)
    pygame.mixer.music.load(ruta)
    pygame.mixer.music.play(0)
    print(f"  > {nombre:<18} {dur:5.1f} s   ({donde})")
    if sin_cortar:
        _esperar_sin_cortar()
    else:
        # Cola de un segundo y medio:asi se oye como cae el bucle.
        pygame.time.wait(int((dur + 1.5) * 1000))
    return True


def _reproducir_sfx():
    print("Efectos (uno detras de otro):")
    for archivo, etiqueta in SFX:
        _tocar(os.path.join(RAIZ, "assets", archivo), archivo, etiqueta)


def _tocar(ruta, archivo, etiqueta):
    if not os.path.exists(ruta):
        print(f"  - {archivo}: no esta")
        return False
    sonido = pygame.mixer.Sound(ruta)
    largo = sonido.get_length()
    sonido.play()
    print(f"  > {archivo:<24} {largo:4.2f} s  ({etiqueta})")
    pygame.time.wait(int(largo * 1000) + 400)
    return True


def _reproducir_candidatos():
    print("Candidatos SFX Lote 01 (NO integrados):\n")
    faltan = 0
    for archivo, etiqueta in CANDIDATOS:
        ruta = os.path.join(RAIZ, "assets", "sfx_candidatos", archivo)
        if not _tocar(ruta, archivo, etiqueta):
            faltan += 1
    if faltan:
        print(f"  {faltan} candidatos no estan en assets/sfx_candidatos/")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nombres", nargs="*",
                        help="pistas concretas; sin nada, todas en orden")
    parser.add_argument("--sfx", action="store_true",
                        help="reproducir solo los efectos de las reglas")
    parser.add_argument("--candidatos", action="store_true",
                        help="reproducir los candidatos del Lote 01 de SFX")
    parser.add_argument("--sin-cortar", action="store_true",
                        help="esperar a que acabe en vez de cortar por pista")
    args = parser.parse_args()

    _abrir()
    print("Ctrl+C para cortar.\n")

    if args.sfx:
        _reproducir_sfx()
        return 0

    if args.candidatos:
        _reproducir_candidatos()
        return 0

    pedidos = args.nombres or [n for n, _ in PISTAS]
    print("Pistas del prologo:\n")
    for nombre in pedidos:
        donde = dict(PISTAS).get(nombre, "sin escena")
        _reproducir_pista(nombre, donde, args.sin_cortar)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nParado.")
        sys.exit(0)