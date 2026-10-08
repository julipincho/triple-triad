"""Vuelca a formato UI el workflow que usa `generar_escenas.py`.

Por que existe
--------------
El generador habla con ComfyUI por la API (`/prompt`), asi que los nodos NO
aparecen en el canvas de la interfaz: lo que se ve ahi es la plantilla por
defecto y da la sensacion de que no se esta haciendo nada. Este script construye
el MISMO grafo en el formato que la interfaz entiende, para poder cargarlo,
mirarlo y ejecutarlo a mano.

De una sola fuente
------------------
Los nodos se sacan del `_workflow()` de `generar_cartas_comfyui` y de los
mismos valores (prompt, semilla, medidas, checkpoint) que usa `generar_escenas`.
Si uno cambia, el volcado cambia con el: no hay dos verdades.

Uso:
    python volcar_workflow_ui.py --clave nara
    python volcar_workflow_ui.py --clave nara --salida workflow_nara.json
    python volcar_workflow_ui.py --clave duelista --cargar   # lo sube a ComfyUI

Herramienta de desarrollo: el juego no importa este modulo.
"""

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import estilo_escenas as est  # noqa: E402
import generar_cartas_comfyui as comfy  # noqa: E402
import generar_escenas as gen  # noqa: E402

#: Donde ComfyUI guarda los flujos de trabajo del usuario.
API_USERDATA = f"{comfy.COMFY_URL}/api/userdata/workflows"
NOMBRE_FLUJO = "cartones_escenas"

#: Posiciones en el canvas, para que se lea de izquierda a derecha.
POS = {
    4: (60, 120),     # checkpoint
    6: (520, 60),     # prompt positivo
    7: (520, 340),    # prompt negativo
    5: (520, 620),    # latent
    3: (1000, 200),   # ksampler
    8: (1380, 200),   # decode
    9: (1620, 200),   # save
}


def _nodo(nid, tipo, pos, tam, inputs, outputs, widgets, orden):
    """Un nodo en el formato que la interfaz de ComfyUI entiende."""
    return {
        "id": nid,
        "type": tipo,
        "pos": list(pos),
        "size": list(tam),
        "flags": {},
        "order": orden,
        "mode": 0,
        "inputs": inputs,
        "outputs": outputs,
        "properties": {"Node name for S&R": tipo},
        "widgets_values": widgets,
    }


def construir_ui(clave, semilla=None, variante="pixel"):
    """Workflow en formato UI, equivalente al que se manda por la API."""
    entrada = gen.CATALOGO[clave]
    estilo_nombre = dict(gen._variantes(entrada))[variante]
    positivo = est.construir_prompt(
        entrada["sujeto"], encuadre=entrada["encuadre"], estilo=estilo_nombre,
        extra=entrada.get("extra", ""))
    negativo = est.construir_negativo()
    (dw, dh), (gw, gh) = gen._escala(entrada)
    semilla = semilla if semilla is not None else 1234

    # Los mismos ids que usa el _workflow() de la API: 3,4,5,6,7,8,9.
    nodos = [
        _nodo(4, "CheckpointLoaderSimple", POS[4], (420, 100),
              [],
              [{"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
               {"name": "CLIP", "type": "CLIP", "links": [2, 3], "slot_index": 1},
               {"name": "VAE", "type": "VAE", "links": [4], "slot_index": 2}],
              [est.CHECKPOINT], 0),
        _nodo(6, "CLIPTextEncode", POS[6], (430, 200),
              [{"name": "clip", "type": "CLIP", "link": 2}],
              [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [5],
                "slot_index": 0}],
              [positivo], 1),
        _nodo(7, "CLIPTextEncode", POS[7], (430, 160),
              [{"name": "clip", "type": "CLIP", "link": 3}],
              [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [6],
                "slot_index": 0}],
              [negativo], 2),
        _nodo(5, "EmptyLatentImage", POS[5], (320, 110),
              [],
              [{"name": "LATENT", "type": "LATENT", "links": [7], "slot_index": 0}],
              [gw, gh, 1], 3),
        _nodo(3, "KSampler", POS[3], (330, 270),
              [{"name": "model", "type": "MODEL", "link": 1},
               {"name": "positive", "type": "CONDITIONING", "link": 5},
               {"name": "negative", "type": "CONDITIONING", "link": 6},
               {"name": "latent_image", "type": "LATENT", "link": 7}],
              [{"name": "LATENT", "type": "LATENT", "links": [8], "slot_index": 0}],
              [semilla, "fixed", gen.STEPS_DEFECTO, gen.CFG_ANIME,
               "euler", "normal", 1.0], 4),
        _nodo(8, "VAEDecode", POS[8], (220, 50),
              [{"name": "samples", "type": "LATENT", "link": 8},
               {"name": "vae", "type": "VAE", "link": 4}],
              [{"name": "IMAGE", "type": "IMAGE", "links": [9], "slot_index": 0}],
              [], 5),
        _nodo(9, "SaveImage", POS[9], (420, 470),
              [{"name": "images", "type": "IMAGE", "link": 9}],
              [], [f"cartones/{clave}"], 6),
    ]

    # [id_enlace, origen, slot_origen, destino, slot_destino, tipo]
    enlaces = [
        [1, 4, 0, 3, 0, "MODEL"],
        [2, 4, 1, 6, 0, "CLIP"],
        [3, 4, 1, 7, 0, "CLIP"],
        [4, 4, 2, 8, 1, "VAE"],
        [5, 6, 0, 3, 1, "CONDITIONING"],
        [6, 7, 0, 3, 2, "CONDITIONING"],
        [7, 5, 0, 3, 3, "LATENT"],
        [8, 3, 0, 8, 0, "LATENT"],
        [9, 8, 0, 9, 0, "IMAGE"],
    ]

    return {
        "last_node_id": 9,
        "last_link_id": 9,
        "nodes": nodos,
        "links": enlaces,
        "groups": [],
        "config": {},
        "extra": {},
        "version": 0.4,
    }


def cargar_en_comfyui(flujo, servidor=comfy.COMFY_URL):
    """Sube el flujo a la biblioteca del usuario para verlo en la interfaz."""
    import urllib.request
    datos = json.dumps({"workflow": flujo}).encode("utf-8")
    peticion = urllib.request.Request(
        f"{API_USERDATA}/{NOMBRE_FLUJO}", data=datos,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(peticion, timeout=20) as r:
            return r.status in (200, 201)
    except Exception as e:  # noqa: BLE001 - la interfaz puede estar apagada
        print(f"  no pude subir el flujo: {e}")
        return False


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--clave", default="nara", choices=list(gen.CATALOGO))
    p.add_argument("--variante", default="pixel",
                   choices=("pixel", "anime", "pixel_limpio"))
    p.add_argument("--semilla", type=int, default=None)
    p.add_argument("--salida", default=None)
    p.add_argument("--cargar", action="store_true",
                   help="sube el flujo a ComfyUI para verlo en la interfaz")
    args = p.parse_args()

    flujo = construir_ui(args.clave, args.semilla, args.variante)
    destino = args.salida or os.path.join(
        BASE, f"workflow_{args.clave}.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(flujo, f, ensure_ascii=False, indent=2)
    print(f"escrito {destino}")
    print(f"  nodos: {len(flujo['nodes'])} | enlaces: {len(flujo['links'])}")

    if args.cargar:
        if not comfy.comprobar_servidor(comfy.COMFY_URL):
            print("ComfyUI no responde: no se puede cargar.")
            return 1
        if cargar_en_comfyui(flujo):
            print(f"subido como '{NOMBRE_FLUJO}'. En la interfaz: menu Flujos de trabajo.")
            return 0
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
