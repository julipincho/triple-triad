"""Integra en el juego las pistas generadas con ACE-Step 1.5.

Las pruebas de ACE-Step salen en 48 kHz estereo float32 (~11,5 MB por pista de
30 s) y con nombre UUID. Eso no puede entrar tal cual en `assets/musica/`:
el juego se publica en itch.io y pesa.

Este script hace la conversion con la misma politica que el resto del proyecto:

- **WAV nativo a 44100 Hz, 16-bit, estereo**, que es exactamente como
  `audio.iniciar()` abre el mixer de pygame. Ahi no hay remuestreo al cargar.
  (Los assets chiptune existentes son 22050 Hz mono porque son pulsos cuadrados
  sin contenido por encima de 5 kHz; una pista orquestal si lo tiene, y
  bajarla a mono 22050 se nota.)
- **OGG Vorbis** para la version web, donde `audio.es_web()` lo prefiere al WAV.

    python assets/integrar_musica_ia.py [--ffmpeg RUTA] [--solo NAMES]

Los TOML viven en `E:\\AI\\ACE-Step-1.5\\pruebas_musica_prologo\\` y cada
generacion es reproducible por su semilla fija. Este script solo mueve y
convierte: no genera musica ni decide si una pista es buena.
"""

import argparse
import array
import glob
import os
import shutil
import subprocess
import sys
import wave

# Carpeta del proyecto (este archivo vive en assets/).
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(RAIZ, "assets", "musica")

ORIGEN = r"E:\AI\ACE-Step-1.5\pruebas_musica_prologo\salida"
FFMPEG_POR_DEFECTO = r"E:\AI\ACE-Step-1.5\ffmpeg-local\bin\ffmpeg.exe"

#: Carpeta de la prueba -> (nombre con el que lo busca el juego, cierra bucle).
#: Los nombres no son inventos: `musica_torneo` y `musica_umbral` ya estaban
#: pedidos en `assets_manifiesto.MUSICA_FALTANTE`.
PISTAS = {
    "05_salon_torneo": ("musica_torneo", True),
    "06_umbral": ("musica_umbral", True),
    # El apagon es un golpe puntual de la transicion entre mundos: no se repite,
    # asi que se integra sin cerrar el bucle (y el juego lo pide sin bucle).
    "07_apagon": ("musica_apagon", False),
    "08_bosque": ("musica_bosque", True),
    "09_campamento": ("musica_campamento", True),
}

#: Menu y las diez facciones. Vienen de otro lote de pruebas, con su propia raiz.
#: Los nombres de destino coinciden con los que `audio.musica_de_faccion()`
#: construye, asi que no hay que tocar el codigo del juego para que encajen.
FACCIONES = {
    "10_menu": "musica_explora",
    "11_humano": "musica_humano",
    "12_orco": "musica_orco",
    "13_elfo": "musica_elfo",
    "14_goblin": "musica_goblin",
    "15_hombre_lobo": "musica_hombre_lobo",
    "16_vampiro": "musica_vampiro",
    "17_dragon": "musica_dragon",
    "18_elfo_nocturno": "musica_elfo_nocturno",
    "19_hombre_pantera": "musica_hombre_pantera",
    "20_hombre_lagarto": "musica_hombre_lagarto",
}

#: Raiz del segundo lote de pruebas (menu y facciones).
ORIGEN_FACCIONES = r"E:\AI\ACE-Step-1.5\pruebas_musica_facciones\salida"

#: El duelo ya tiene render validado, pero nunca se integro: el WAV que usa el
#: juego seguia siendo el chiptune de `crear_sonidos.py`.
DUELO = {
    "origen": r"E:\AI\ACE-Step-1.5\pruebas_musica_duelo_cartas"
              r"\duelo_el_destino_de_las_cartas_v01.wav",
    "destino": "musica_duelo",
}

#: Codec de salida. `libvorbis -q 4`(~128 kbps) es lo que ya usan los OGG
#: existentes y no se nota la diferencia en musica de fondo.
VORBIS = ["-c:a", "libvorbis", "-q:a", "4"]

#: Segundos de crossfade para cerrar el bucle. Las pistas chiptune se
#: construyen con compases enteros y repitiendo el primero (`_fundir_bucle`),
#: asi que enlazan solas; un render de ACE-Step termina en silencio y al
#: repetir se oye el hueco. Aqui la cola se funde sobre la cabeza, que es el
#: modo normal de cerrar un bucle en un editor. Con 2 s el solape es invisible
#: y la pista acorta 2 s.
CROSSFADE = 2.0

#: Por debajo de este nivel se considera silencio al medir cabeza y cola.
#: No es un valor arbitrario: es el mismo que usa
#: `tests.test_assets.TestAudio.test_el_bucle_de_la_musica_no_tiene_corte`, que
#: cuenta como silencio cualquier sample por debajo de 300/32767 (-41 dBFS).
#: Si aqui se recortara mas bajo, quedarían pistas cuya costura el test marca
#: como cortada (pasó con musica_umbral a -45 dBFS en ambos extremos).
UMBRAL_SILENCIO_DB = -42.0
#: Cuanto silencio seguido hace falta para recortar (s). Menos que esto suele
#: ser una respiracion entre notas, no una cola.
MIN_SILENCIO_S = 0.4
#: Se deja este margen tras la ultima nota audible para no cortar en pleno
#: sustain (s).
MARGEN_INICIO = 0.25
#: Frecuencia de trabajo al medir. Es la misma que usa el mixer de pygame.
SR_REF = 44100


def _a_db(amplitud, tope=32767.0):
    import math
    if amplitud <= 0:
        return -120.0
    return 20.0 * math.log10(amplitud / tope)


def _recortar_silencios(ffmpeg, origen, destino):
    """Quita el silencio de entrada y de salida. Devuelve los segundos de sobra.

    Un render de ACE-Step se apaga al final y ademas entra en silencio: la cola
    suele caer por debajo de -60 dBFS y la cabeza fadea desde muy bajo. Si esas
    zonas se quedan, el punto donde el bucle cierra cae ya en silencio y al
    repetir se oye un hueco (medido: 100 ms a -63 dBFS en musica_duelo y
    musica_torneo, frente a 1 ms de silencio dentro de la pista). El Umbral
    faila por lo mismo pero mas suave: 100 ms a -45 dBFS.

    Las pistas chiptune no tienen el problema porque se construyen con compases
    enteros y repitiendo el primero, asi que enlazan solas.

    Solo se recorta lo que este por debajo del umbral al menos durante
    `MIN_SILENCIO_S` seguidos, y se deja un margen para que el corte no caiga
    en plena nota.
    """
    umbral = 10 ** (UMBRAL_SILENCIO_DB / 20.0) * 32767.0
    largo_silencio = int(SR_REF * MIN_SILENCIO_S)

    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-i", origen, "-ar", str(SR_REF), "-ac", "2",
                    "-c:a", "pcm_s16le", destino], check=True)

    with wave.open(destino) as w:
        total = w.getnframes()
        crudo = w.readframes(total)
    muestras = array.array("h")
    muestras.frombytes(crudo)
    if sys.byteorder != "little":
        muestras.byteswap()
    picos = [max(abs(muestras[i]), abs(muestras[i + 1]))
             for i in range(0, len(muestras) - 1, 2)]

    # Primer y ultimo frame por encima del umbral.
    primero = total
    for i, pico in enumerate(picos):
        if pico > umbral:
            primero = i
            break
    ultimo = 0
    for i in range(total - 1, -1, -1):
        if picos[i] > umbral:
            ultimo = i
            break

    inicio = primero
    if primero >= largo_silencio:
        # Margen por delante: el corte no debe caer en plena nota.
        inicio = max(0, primero - int(SR_REF * MARGEN_INICIO))
    fin = total
    if (total - 1 - ultimo) >= largo_silencio:
        fin = min(total, ultimo + int(SR_REF * MARGEN_INICIO))

    if inicio == 0 and fin == total:
        return 0.0, destino

    # ffmpeg no puede leer y escribir el mismo fichero: hace falta otro temporal.
    recortado_wav = os.path.join(DESTINO, "_tmp_recortado.wav")
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-i", destino, "-af",
                    f"atrim={inicio / SR_REF:.4f}:{fin / SR_REF:.4f},"
                    f"asetpts=PTS-STARTPTS",
                    "-c:a", "pcm_s16le", recortado_wav], check=True)
    os.replace(recortado_wav, destino)
    return (total - (fin - inicio)) / SR_REF, destino


def cerrar_bucle(ffmpeg, origen, destino_wav, crossfade=CROSSFADE):
    """Escribe el WAV con la cola fundida sobre la cabeza (bucle sin corte).

    Primero recorta los silencios de entrada y salida, luego funde los ultimos
    `crossfade` segundos sobre la cabeza. Devuelve la duracion resultante.
    """
    os.makedirs(DESTINO, exist_ok=True)
    _, intermedio = _recortar_silencios(ffmpeg, origen,
                                       os.path.join(DESTINO, "_tmp.wav"))
    duracion = float(_duracion(ffmpeg, intermedio))
    if duracion <= crossfade:
        os.replace(intermedio, destino_wav)
        return duracion

    corte = duracion - crossfade
    filtro = (
        f"[0:a]atrim=0:{corte:.3f},asetpts=PTS-STARTPTS[cabeza];"
        f"[0:a]atrim={corte:.3f}:{duracion:.3f},asetpts=PTS-STARTPTS[cola];"
        f"[cola][cabeza]acrossfade=d={crossfade}:curve1=tri:curve2=tri"
    )
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-i", intermedio, "-filter_complex", filtro,
                    "-c:a", "pcm_s16le", destino_wav], check=True)
    os.remove(intermedio)
    return corte


def _duracion(ffmpeg, ruta):
    salida = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", ruta],
        capture_output=True, text=True).stderr
    for linea in salida.splitlines():
        if "Duration:" in linea:
            marca = linea.split("Duration:")[1].split(",")[0].strip()
            horas, minutos, segundos = marca.split(":")
            return int(horas) * 3600 + int(minutos) * 60 + float(segundos)
    raise SystemExit(f"No puedo leer la duracion de {ruta}")


def _ffmpeg(ffmpeg):
    if ffmpeg and os.path.exists(ffmpeg):
        return ffmpeg
    if os.path.exists(FFMPEG_POR_DEFECTO):
        return FFMPEG_POR_DEFECTO
    encontrado = shutil.which("ffmpeg")
    if encontrado:
        return encontrado
    raise SystemExit(
        "No encuentro ffmpeg. Pasa la ruta con --ffmpeg, o deja una copia en\n"
        f"  {FFMPEG_POR_DEFECTO}")


def _un_wav(carpeta):
    """El WAV de la carpeta, o None. Se toma el mas reciente por si hay varios."""
    hallados = glob.glob(os.path.join(carpeta, "*.wav"))
    if not hallados:
        return None
    return max(hallados, key=os.path.getmtime)


def convertir(ffmpeg, origen, destino_wav, bucle=True):
    """Escribe el WAV nativo y su OGG. Devuelve (bytes_wav, bytes_ogg).

    `bucle=False` deja la pista como sale del modelo: es lo que quiere el
    apagón, que es un golpe puntual y no se repite.
    """
    os.makedirs(DESTINO, exist_ok=True)
    destino_ogg = os.path.splitext(destino_wav)[0] + ".ogg"

    if bucle:
        cerrar_bucle(ffmpeg, origen, destino_wav)
    else:
        # 44100/16-bit/estereo: lo que espera el mixer de pygame.
        subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                        "-i", origen,
                        "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le",
                        destino_wav], check=True)

    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-i", destino_wav] + VORBIS + [destino_ogg], check=True)

    return os.path.getsize(destino_wav), os.path.getsize(destino_ogg)


def integrar(ffmpeg, nombre_origen, destino, subtitulo="", bucle=True,
             origen_raiz=None):
    origen = _un_wav(os.path.join(origen_raiz or ORIGEN, nombre_origen))
    if origen is None:
        print(f"  - {nombre_origen}: no hay WAV en la carpeta, me salto")
        return False
    destino_wav = os.path.join(DESTINO, f"{destino}.wav")
    wav, ogg = convertir(ffmpeg, origen, destino_wav, bucle=bucle)
    cola = "" if bucle else "  (sin cerrar: golpe puntual)"
    print(f"  + {destino}.wav  {wav / 1024:.0f} KiB   "
          f"{destino}.ogg  {ogg / 1024:.0f} KiB  {subtitulo}{cola}")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", help="ruta a ffmpeg.exe")
    parser.add_argument("--solo", nargs="*",
                        help="integrar solo estas carpetas de origen")
    parser.add_argument("--solo-facciones", action="store_true",
                        help="saltar el menu y las diez facciones")
    parser.add_argument("--con-duelo", action="store_true",
                        help="integrar tambien la pista del duelo ya validada")
    args = parser.parse_args()

    ffmpeg = _ffmpeg(args.ffmpeg)

    print("Pistas del prologo:")
    integradas = 0
    for carpeta, (destino, bucle) in PISTAS.items():
        if args.solo and carpeta not in args.solo:
            continue
        if integrar(ffmpeg, carpeta, destino, bucle=bucle):
            integradas += 1

    if not args.solo_facciones:
        print("\nMenu y facciones:")
        for carpeta, destino in FACCIONES.items():
            if args.solo and carpeta not in args.solo:
                continue
            if integrar(ffmpeg, carpeta, destino,
                        origen_raiz=ORIGEN_FACCIONES):
                integradas += 1

    if args.con_duelo:
        origen = DUELO["origen"]
        if not os.path.exists(origen):
            print(f"  - duelo: no encuentro {origen}")
        else:
            destino_wav = os.path.join(DESTINO, f"{DUELO['destino']}.wav")
            wav, ogg = convertir(ffmpeg, origen, destino_wav, bucle=True)
            print(f"  + {DUELO['destino']}.wav  {wav / 1024:.0f} KiB   "
                  f"{DUELO['destino']}.ogg  {ogg / 1024:.0f} KiB  (referencia)")
            integradas += 1

    print(f"\n{integradas} pistas integradas en assets/musica/.")
    if not args.con_duelo:
        print("El duelo NO se toco. Usa --con-duelo para integrarlo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())