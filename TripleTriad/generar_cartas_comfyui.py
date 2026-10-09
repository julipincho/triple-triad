"""Genera ilustraciones de cartas con el ComfyUI local (herramienta de desarrollo).

Habla por HTTP con el servidor ComfyUI en http://127.0.0.1:8188, construye un
prompt de dark fantasy coherente a partir de los datos de la carta y guarda el
resultado como un PNG normal dentro de los assets del juego (carpeta `cartas/`
por defecto, con el mismo nombre `{faccion}_{slug}.png` que usa `cartas.py`).

El pipeline por defecto (validado en la hoja de contactos) usa el checkpoint
Pixel Art Diffusion XL (Sprite Shaper) + IP-Adapter Plus con la imagen ancla
del moodboard en modo "style transfer" con peso 0.35, para que el ancla de
paleta, textura y luz sin imponer la cara del personaje. Despues hay que pasar
los PNG por `postprocesar_cartas.py` (rejilla 56x79, scanlines, dither).

El juego NUNCA importa este modulo: ComfyUI es solo una herramienta para crear
assets. Si ComfyUI no esta arrancado, el juego funciona igual y esta
herramienta lo arranca sola en una consola nueva (o falla sin generar nada
con --no-arrancar).

Uso:
    python generar_cartas_comfyui.py --nombre "Conde Nocturno" --faccion vampiro \
        --raza vampiro --clase nigromante --rareza LEGENDARIA \
        --descripcion "levanta un calis de sangre sobre el trono roto" \
        --estilo carta --seed 1234

    python generar_cartas_comfyui.py ... --solo-prompt   # solo imprime el prompt
    python generar_cartas_comfyui.py --lote nuevas.json  # muchos personajes
    python generar_cartas_comfyui.py --peso-ipadapter 0.8 --peso-tipo linear \
        ...   # para comparar variantes en la hoja de contactos

Sin `--seed` la semilla es aleatoria (se imprime para poder repetirla).
Solo usa la biblioteca estandar: sin dependencias, sin claves de API.
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_CARTAS = os.path.join(BASE, "cartas")
COMFY_URL = "http://127.0.0.1:8188"
CHECKPOINT = "pixelArtDiffusionXL_spriteShaper.safetensors"
PESO_IPADAPTER_DEFECTO = 0.35
PESO_TIPO_DEFECTO = "style transfer"
CLIP_VISION = "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"
IPADAPTER_FILE = "ip-adapter-plus_sdxl_vit-h.safetensors"
ANCLA_DEFECTO = os.path.join(BASE, "estilo", "ancla.png")
COMFY_INPUT = r"E:\AI\ComfyUI\input"

# Las facciones aportan color de acento; si no se pueden importar, no pasa nada.
try:
    from facciones import FACCIONES
except Exception:  # noqa: BLE001 - el script debe funcionar suelto
    FACCIONES = {}

# La biblia de estilo (bloque fijo, negativo, paleta y traducciones) vive en
# `estilo.py`, alimentada por el moodboard. Si no esta, el script sigue vivo.
try:
    import estilo as estilo_biblia
except Exception:  # noqa: BLE001 - degradar a los valores de siempre
    estilo_biblia = None

# ---------------------------------------------------------------- prompts ----

if estilo_biblia is not None:
    FIJO = estilo_biblia.FIJO
    NEGATIVO = estilo_biblia.NEGATIVO
    RAZA_EN = estilo_biblia.RAZA_EN
    CLASE_EN = estilo_biblia.CLASE_EN
    FACCION_VISUAL = estilo_biblia.FACCION_VISUAL
    RAREZA_EN = estilo_biblia.RAREZA_EN
    ESTILOS = estilo_biblia.ESTILOS
    ESTILO_DEFECTO = estilo_biblia.ESTILO_DEFECTO
    paleta_txt = estilo_biblia.paleta_txt
else:
    FIJO = (
        ", dark fantasy medieval trading card illustration, dramatic cinematic "
        "lighting, gothic atmosphere, single full-body character, centered "
        "composition, highly detailed"
    )
    NEGATIVO = (
        "text, watermark, signature, logo, letters, words, numbers, border, frame, "
        "UI elements, low quality, lowres, blurry, jpeg artifacts, deformed, "
        "disfigured, extra limbs, extra fingers, bad anatomy, modern clothing, "
        "sci-fi, cheerful bright colors, cropped, multiple characters, crowd"
    )
    RAZA_EN = {}
    CLASE_EN = {}
    FACCION_VISUAL = {}
    RAREZA_EN = {}
    ESTILOS = {"carta": "painterly semi-realistic fantasy art"}
    ESTILO_DEFECTO = "carta"
    paleta_txt = lambda: ""  # noqa: E731


def _norm(texto):
    """minusculas y sin acentos, para mirar en los diccionarios."""
    s = (texto or "").lower().strip()
    for a, b in (("á", "a"), ("à", "a"), ("é", "e"), ("è", "e"), ("í", "i"),
                 ("ì", "i"), ("ó", "o"), ("ò", "o"), ("ú", "u"), ("ù", "u"),
                 ("ñ", "n"), ("ü", "u"), ("ç", "c")):
        s = s.replace(a, b)
    return s


def slug(nombre):
    return re.sub(r"[^a-z0-9]+", "_", _norm(nombre)).strip("_")


def construir_prompt(nombre, faccion, raza, descripcion="", clase="",
                     rareza="COMUN", estilo="carta"):
    """Compone (positivo, negativo) a partir de los datos de la carta."""
    faccion_l = _norm(faccion)
    raza_l = _norm(raza)
    clase_l = _norm(clase)
    rareza_l = _norm(rareza)
    estilo_l = _norm(estilo)

    raza_en = RAZA_EN.get(raza_l, raza.strip())
    clase_en = CLASE_EN.get(clase_l, clase.strip())
    sujeto = " ".join(x for x in (raza_en, clase_en) if x)

    partes = [f"{nombre.strip()}, {sujeto}".rstrip(",")]
    if descripcion.strip():
        partes.append(descripcion.strip())
    partes.append(FACCION_VISUAL.get(faccion_l, f"the {faccion_l} faction"))
    if rareza_l in RAREZA_EN:
        partes.append(RAREZA_EN[rareza_l])
    elif rareza.strip():
        partes.append(rareza.strip())
    variante = ESTILOS.get(estilo_l, estilo.strip())
    if variante:
        partes.append(variante)
    color = paleta_txt()
    if color:
        partes.append(color)

    meta = FACCIONES.get(faccion_l)
    if meta and meta.get("acento"):
        r, g, b = meta["acento"][:3]
        partes.append(f"dominant accent color #{r:02x}{g:02x}{b:02x}")

    if estilo_biblia is not None:
        encuadre = estilo_biblia.ENCUADRE_EXTRA.get(faccion_l)
        if encuadre:
            partes.append(encuadre)

    base = ", ".join(p for p in partes if p)
    positivo = ", ".join(p for p in (base, FIJO) if p)
    return positivo, NEGATIVO


# ------------------------------------------------------- API de ComfyUI ------

def _get(url, timeout=15):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


def _post_json(url, payload, timeout=30):
    datos = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=datos, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def comprobar_servidor(servidor):
    """Devuelve la version de ComfyUI o None si no responde."""
    try:
        datos = json.loads(_get(f"{servidor}/system_stats", timeout=5).decode("utf-8"))
        return datos.get("system", {}).get("comfyui_version", "desconocida")
    except Exception:  # noqa: BLE001 - sin servidor o apagado
        return None


def arrancar_servidor(servidor, bat, espera):
    """Arranca ComfyUI en una consola nueva y espera a que responda.

    Devuelve la version o None. La ventana nueva queda visible para el
    usuario (se para con Ctrl+C ahi o con E:\\AI\\stop-comfyui.bat).

    ES IDEMPOTENTE, y tiene que serlo: si ComfyUI ya esta en marcha se
    devuelve tal cual y NO se abre ninguna ventana. Antes no lo comprobaba y
    abria una consola nueva en CADA llamada, que al llamar desde un bucle de
    24 variantes dejo trece ventanas de ComfyUI abiertas de golpe.
    """
    version = comprobar_servidor(servidor)
    if version:
        return version

    if not os.path.exists(bat):
        print(f"No existe {bat}: no puedo arrancar ComfyUI automaticamente.")
        return None
    print(f"ComfyUI no esta en marcha: arrancando {bat}")
    nueva_consola = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)
    mas_nueva = nueva_consola | getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000)
    try:
        subprocess.Popen(f'cmd.exe /c "{bat}"', creationflags=mas_nueva)
    except OSError:
        try:
            subprocess.Popen(f'cmd.exe /c "{bat}"', creationflags=nueva_consola)
        except OSError as e:
            print(f"  no pude arrancarlo: {e}")
            return None
    print("  esperando a que este listo (ha abierto una ventana de ComfyUI)...")
    inicio = time.time()
    while time.time() - inicio < espera:
        version = comprobar_servidor(servidor)
        if version:
            print(f"  listo tras {time.time() - inicio:.0f} s")
            return version
        time.sleep(2)
    print(f"  no respondio en {espera} s: mira la ventana de ComfyUI.")
    return None


def _workflow(positivo, negativo, seed, ancho, alto, steps, cfg, modelo,
              ancla=None, peso_ipadapter=0.8, peso_tipo="linear"):
    """Workflow en formato API (mismos nodos/params con los que ya se ha probado).

    Si `ancla` existe, se intercala IP-Adapter Plus: la estetica del moodboard
    (imagen ancla) condiciona el resultado ademas del prompt.
    """
    flujo = {
        "3": {"class_type": "KSampler", "inputs": {
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
            "latent_image": ["5", 0], "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": "euler", "scheduler": "normal", "denoise": 1.0,
        }},
        "4": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": modelo}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": ancho, "height": alto, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode",
              "inputs": {"text": positivo, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode",
              "inputs": {"text": negativo, "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0],
                                                    "filename_prefix": "comfyui"}},
    }
    if ancla and os.path.exists(ancla):
        flujo["10"] = {"class_type": "LoadImage",
                       "inputs": {"image": os.path.basename(ancla)}}
        flujo["11"] = {"class_type": "CLIPVisionLoader",
                       "inputs": {"clip_name": CLIP_VISION}}
        flujo["12"] = {"class_type": "IPAdapterModelLoader",
                       "inputs": {"ipadapter_file": IPADAPTER_FILE}}
        flujo["13"] = {"class_type": "IPAdapterAdvanced", "inputs": {
            "model": ["4", 0], "ipadapter": ["12", 0], "image": ["10", 0],
            "clip_vision": ["11", 0], "weight": peso_ipadapter,
            "start_at": 0.0, "end_at": 1.0, "weight_type": peso_tipo,
            "combine_embeds": "concat", "embeds_scaling": "V only",
        }}
        flujo["3"]["inputs"]["model"] = ["13", 0]
    return flujo


def _copiar_ancla_a_input(ancla):
    """Copia el ancla a ComfyUI/input (LoadImage solo lee de ahi)."""
    if not ancla or not os.path.exists(ancla):
        return False
    destino = os.path.join(COMFY_INPUT, os.path.basename(ancla))
    try:
        os.makedirs(COMFY_INPUT, exist_ok=True)
        if (not os.path.exists(destino)
                or os.path.getmtime(ancla) > os.path.getmtime(destino)):
            import shutil
            shutil.copy2(ancla, destino)
        return True
    except OSError:
        return False


def generar_imagen(servidor, positivo, negativo, destino, seed,
                   ancho, alto, steps, cfg, modelo, espera=300,
                   ancla=None, peso_ipadapter=0.8, peso_tipo="linear"):
    """Ejecuta el workflow y escribe el PNG en `destino`. Devuelve True/False."""
    if ancla and not _copiar_ancla_a_input(ancla):
        print(f"  aviso: no puedo copiar el ancla a {COMFY_INPUT}; genero sin IP-Adapter")
        ancla = None
    flujo = _workflow(positivo, negativo, seed, ancho, alto, steps, cfg, modelo,
                      ancla=ancla, peso_ipadapter=peso_ipadapter,
                      peso_tipo=peso_tipo)
    try:
        r = _post_json(f"{servidor}/prompt", {"prompt": flujo})
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", "replace")
        try:
            err = json.loads(cuerpo)
            msg = err.get("error") or cuerpo
            nodos = err.get("node_errors") or {}
            detalle = "; ".join(
                json.dumps(v, ensure_ascii=False) for v in nodos.values()
            )
            if detalle:
                msg = f"{msg} | {detalle}"
        except ValueError:
            msg = cuerpo
        print(f"  ComfyUI rechazo el workflow ({e.code}): {msg}")
        return False
    except Exception as e:  # noqa: BLE001
        print(f"  error de conexion: {e}")
        return False

    prompt_id = r.get("prompt_id")
    if not prompt_id:
        print(f"  respuesta inesperada: {r}")
        return False

    inicio = time.time()
    while time.time() - inicio < espera:
        hist = json.loads(_get(f"{servidor}/history/{prompt_id}").decode("utf-8"))
        entrada = hist.get(prompt_id)
        if entrada:
            estado = (entrada.get("status") or {}).get("status_str")
            if estado == "error":
                print("  fallo durante la ejecucion, mira la consola de ComfyUI")
                return False
            salidas = entrada.get("outputs") or {}
            imagenes = next(
                (v["images"] for v in salidas.values() if v.get("images")), None
            )
            if imagenes:
                img = imagenes[0]
                consulta = urllib.parse.urlencode({
                    "filename": img["filename"],
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output"),
                })
                datos = _get(f"{servidor}/view?{consulta}", timeout=60)
                if not datos.startswith(b"\x89PNG\r\n\x1a\n"):
                    print("  la respuesta no es un PNG valido")
                    return False
                with open(destino, "wb") as f:
                    f.write(datos)
                return True
        time.sleep(1.5)

    print("  timeout: ComfyUI no termino a tiempo")
    return False


# ------------------------------------------------------------------ CLI ------

def _ficha_desde_args(args):
    return {
        "nombre": args.nombre, "faccion": args.faccion, "raza": args.raza,
        "descripcion": args.descripcion, "clase": args.clase,
        "rareza": args.rareza, "estilo": args.estilo, "seed": args.seed,
    }


def procesar(ficha, args, servidor):
    nombre = (ficha.get("nombre") or "").strip()
    faccion = (ficha.get("faccion") or "").strip()
    if not nombre or not faccion:
        print("  ficha incompleta: hacen falta nombre y faccion")
        return "fallo"

    raza = (ficha.get("raza") or faccion).strip()
    descripcion = ficha.get("descripcion") or ""
    clase = ficha.get("clase") or ""
    rareza = (ficha.get("rareza") or "COMUN").strip()
    estilo = (ficha.get("estilo") or ESTILO_DEFECTO).strip()
    seed = ficha.get("seed")
    seed = int(seed) if seed not in (None, "") else random.randrange(2**32)

    positivo, negativo = construir_prompt(
        nombre, faccion, raza, descripcion, clase, rareza, estilo
    )
    # `--negativo` ANADE al negativo de la biblia, no lo sustituye: asi una
    # correccion puntual (por ejemplo "sin tríptico") no se pierde el resto.
    if args.negativo:
        negativo = ", ".join(p for p in (negativo, args.negativo) if p)

    salida = os.path.join(BASE, args.salida) if not os.path.isabs(args.salida) else args.salida
    destino = os.path.join(salida, f"{_norm(faccion)}_{slug(nombre)}.png")

    if args.solo_prompt:
        print(f"--- {nombre} (seed {seed}) ---")
        print(f"positivo : {positivo}")
        print(f"negativo : {negativo}")
        print(f"destino  : {destino}")
        return "prompt"

    if os.path.exists(destino) and not args.fuerza:
        print(f"  ya existe: {os.path.relpath(destino, BASE)} (usa --fuerza para regenerar)")
        return "omitida"

    print(f"  {nombre} | seed {seed} | {args.ancho}x{args.alto} | {args.steps} pasos")
    os.makedirs(salida, exist_ok=True)
    ok = generar_imagen(
        servidor, positivo, negativo, destino, seed,
        args.ancho, args.alto, args.steps, args.cfg, args.modelo,
        espera=args.espera,
        ancla=args.ancla, peso_ipadapter=args.peso_ipadapter,
        peso_tipo=args.peso_tipo,
    )
    if ok:
        print(f"  guardada: {os.path.relpath(destino, BASE)}")
        return "generada"
    return "fallo"


def main():
    parser = argparse.ArgumentParser(
        description="Genera ilustraciones de cartas con el ComfyUI local."
    )
    parser.add_argument("--nombre", help="nombre del personaje")
    parser.add_argument("--faccion", help="id de faccion (goblin, vampiro, ...)")
    parser.add_argument("--raza", help="raza (por defecto: la faccion)")
    parser.add_argument("--descripcion", default="", help="escena o pose del personaje")
    parser.add_argument("--negativo", default="",
                        help="anade terminos al prompt negativo de la biblia "
                             "(por ejemplo: 'grid, triptych, panels')")
    parser.add_argument("--clase", default="", help="clase (guerrero, nigromante, ...)")
    parser.add_argument("--rareza", default="COMUN",
                        choices=["COMUN", "RARA", "LEGENDARIA", "comun", "rara", "legendaria"],
                        help="rareza de la carta")
    parser.add_argument("--estilo", default=ESTILO_DEFECTO,
                        help="variante de encuadre: crt (la del moodboard, por "
                             "defecto), carta, pixel, concept, retrato, grabado, "
                             "cinematic o texto libre")
    parser.add_argument("--seed", "--semilla", type=int, default=None,
                        dest="seed", help="semilla opcional (si falta, aleatoria)")
    parser.add_argument("--salida", default="cartas",
                        help="carpeta de destino relativa al proyecto (por defecto: cartas)")
    parser.add_argument("--fuerza", action="store_true",
                        help="regenera aunque el PNG ya exista")
    parser.add_argument("--ancho", type=int, default=768)
    parser.add_argument("--alto", type=int, default=960)
    parser.add_argument("--steps", type=int, default=25)
    parser.add_argument("--cfg", type=float, default=7.0)
    parser.add_argument("--modelo", default=CHECKPOINT,
                        help=f"checkpoint (por defecto: {CHECKPOINT})")
    parser.add_argument("--ancla", default=None,
                        help=f"imagen ancla para IP-Adapter (por defecto: {ANCLA_DEFECTO} "
                             "si existe; pasar '' para desactivar)")
    parser.add_argument("--peso-ipadapter", type=float, default=PESO_IPADAPTER_DEFECTO,
                        help=f"peso del IP-Adapter ({PESO_IPADAPTER_DEFECTO} validado "
                             "en la hoja de contactos; 0.8 impone la cara del ancla)")
    parser.add_argument("--peso-tipo", default=PESO_TIPO_DEFECTO,
                        choices=["linear", "style transfer", "composition",
                                 "strong style transfer", "ease in", "ease out"],
                        help=f"tipo de peso del IP-Adapter ('{PESO_TIPO_DEFECTO}' "
                             "transfiere textura/paleta/luz sin imponer la "
                             "estructura del ancla; 'linear' impone la identidad)")
    parser.add_argument("--servidor", default=COMFY_URL)
    parser.add_argument("--no-arrancar", action="store_true",
                        help="no arranca ComfyUI si no responde (falla directamente)")
    parser.add_argument("--bat-arranque", default=r"E:\AI\start-comfyui.bat",
                        help="bat usado para arrancar ComfyUI si hace falta")
    parser.add_argument("--espera-arranque", type=int, default=60,
                        help="segundos maximos a esperar el arranque automatico")
    parser.add_argument("--espera", type=int, default=300,
                        help="segundos maximos de espera por imagen")
    parser.add_argument("--solo-prompt", action="store_true",
                        help="imprime el prompt y sale sin tocar ComfyUI")
    parser.add_argument("--lote", help="ruta a un JSON con una lista de fichas")
    parser.add_argument("--sin-ipadapter", action="store_true",
                        help="genera sin IP-Adapter (solo prompt)")
    args = parser.parse_args()

    # por defecto el ancla se usa si existe; --sin-ipadapter la quita
    if args.sin_ipadapter:
        args.ancla = None
    elif args.ancla is None and os.path.exists(ANCLA_DEFECTO):
        args.ancla = ANCLA_DEFECTO

    if args.lote:
        with open(args.lote, encoding="utf-8") as f:
            datos = json.load(f)
        fichas = datos if isinstance(datos, list) else datos.get("cartas", [])
        if not fichas:
            print(f"El lote {args.lote} no contiene ninguna ficha.")
            sys.exit(2)
    else:
        if not args.nombre or not args.faccion:
            parser.error("hacen falta --nombre y --faccion (o --lote)")
        fichas = [_ficha_desde_args(args)]

    version = None
    if not args.solo_prompt:
        version = comprobar_servidor(args.servidor)
        if version is None and not args.no_arrancar:
            version = arrancar_servidor(args.servidor, args.bat_arranque,
                                        args.espera_arranque)
        if version is None:
            print(f"ComfyUI no responde en {args.servidor}.")
            print("Arrancalo con E:\\AI\\start-comfyui.bat y vuelve a intentarlo.")
            print("(El juego no necesita ComfyUI: es solo para generar assets.)")
            sys.exit(3)
        print(f"ComfyUI {version} en {args.servidor}")

    conteo = {"generada": 0, "omitida": 0, "fallo": 0, "prompt": 0}
    for ficha in fichas:
        nombre = (ficha.get("nombre") or "?").strip()
        print(f"- {nombre}")
        clave = procesar(ficha, args, args.servidor)
        conteo[clave] = conteo.get(clave, 0) + 1

    print(
        f"Listo: {conteo['generada']} generadas, {conteo['omitida']} omitidas, "
        f"{conteo['fallo']} fallos."
    )
    sys.exit(1 if conteo["fallo"] else 0)


if __name__ == "__main__":
    main()
