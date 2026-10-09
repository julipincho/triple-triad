"""Genera el arte de cartas, avatares y fondos con Pollinations.

Uso:
    python generar_cartas.py            # solo lo que falta
    python generar_cartas.py --fuerza   # regenera todo
"""

import argparse
import os
import random
import re
import time
import urllib.parse
import urllib.request

from mazos import TODOS

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cartas")
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

RAZA = {
    "humano": "human knight",
    "orco": "orc warrior",
    "goblin": "goblin",
    "elfo": "elf",
    "hombre_lobo": "werewolf",
    "vampiro": "vampire",
    "dragon": "dragon",
    "elfo_nocturno": "dark elf",
    "hombre_pantera": "panther warrior",
    "hombre_lagarto": "lizardman warrior",
}

#: Sufijo comun a los avatares.
#:
#: MODELO DE LOS AVATARES. No es el de las cartas.
#:
#: Hay dos idiomas artista en el juego y son distintos a proposito:
#:
#:   - Cartas (251) y fondos (39): pixel art de 16 bits con paleta calida
#:     limitada, de `pixelArtDiffusionXL_spriteShaper` + IP-Adapter con el
#:     moodboard. Es el arte del mundo del juego.
#:   - Los diecisiete avatares que estan bien: anime ilustrado a mano, de
#:     Pollinations con `model=flux`, que ya no esta disponible (HTTP 402).
#:
#: `hombre_lobo` y `hombre_pantera` se hacen en el PRIMER idioma, no en el
#: segundo. Se intento lo segundo cuatro veces (con prompts de ilustracion pintada,
#: y con IP-Adapter usando un avatar bueno como ancla) y nunca llego: `animagine`
#: y `flux` no comparten el sombreado ni el pelo, y siempre se nota al lado.
#: Como los avatares se ven a 80 px pegados a las cartas, prima que el par se
#: note entre ellos antes que que un par no cuadre con las cartas.
#:
#: El truco que si funciona, y que es lo que fija la receta: el ancla NO es el
#: moodboard sino LA CARTA DEL PROPIO BANDO. `cartas/hombre_lobo_garras_de_luna
#: .png` ya es un lobo en el estilo exacto. Con el moodboard salian gatos y
#: hienas con cara de mascara; con la carta del bando salen lobo y pantera.
#:
#: Ojo al peso: 0.6. Con 0.35 el ancla no llega a imponer la criatura.
MODELO_AVATAR = "pixelArtDiffusionXL_spriteShaper.safetensors"
PESO_ANCLA_AVATAR = 0.6
#:
#: El sufijo describe lo que hacen los avatares que ya estaban bien. Y aqui hay
#: unaLesson que ha costado tres rondas de 24 imagenes cada una, asi que
#: conviene no deshacerla por descuido:
#:
#: Los dieciseis buenos NO son cel shading. Son ilustracion PINTADA A MANO, con
#: gradientes blandos y huella de pincel. Dos terminos del prompt empujaban
#: justo hacia lo contrario y habia que quitar los dos:
#:
#:   - `cel shading` -> campos de color planos y contorno duro. Es lo que mas
#:     se nota al lado de `orco`, `goblin` o `dragon`.
#:   - `vibrant colors` -> saturacion de poster.
#:
#: En su lugar: `painterly illustration, hand-painted, soft brushwork, textured
#: shading, detailed fur`. Y `cel shading` va ademas en el NEGATIVO, porque
#: quitarlo del positivo no basta: el modelo lo pone igual.
#:
#: Y una segunda trampa, mas sutil: quitar `cel shading` lleva al otro extremo,
#: a arte de fauna. Las bestias salian bonitas pero como fotografia de naturaleza
#: (cielo naranja, hierba) en vez de retrato de personaje. Se ata con
#: `fantasy character portrait` en el positivo y `wildlife photography, nature
#: scene, grass, sunset, dramatic sky` en el negativo.
#:
#: Lo que mas pesa al final no es el estilo: es la LUZ. Fondo claro, luz suave
#: y busto a tres cuartos. Con luna, fondo oscuro o frontal simetrico se nota
#: aunque la criatura y la pincelada sean exactas.
#:
#: Cuatro cosas mas que hay que guardar si se regeneran:
#:
#:   - 30 pasos y CFG 6.5 con esta receta; con la anterior (28 y 6.0) hay que
#:     comprobar que no colapse en manchas.
#:   - el negativo de `generar_cartas_comfyui.NEGATIVO` MAS el de abajo. Sin
#:     estos terminos, `animagine` mete marcos y cuadritos: de siete lobos
#:     generados, tres salian con marco de foto y uno partido en cuatro
#:     paneles. `gold collar` es especialmente magnetico para el marco.
#:   - la palabra `beast` hace que `animagine` entienda "hoja de personaje" y
#:     saque una rejilla de nueve vistas de la misma cabeza. Con la misma
#:     raza, colmillos y orejas, pero sin `beast`, sale un retrato normal. Y
#:     `character sheet / sprite sheet / grid` en el negativo es lo que
#:     cierra esa puerta: sin eso, uno de cada cuatro salia con dos cabezas
#:     enfrentadas y simetricas.
#:
#: Y una diferencia de fondo con los dieciseis buenos, que no se arregla desde
#: el prompt: esos se hicieron con Pollinations y `model=flux`, y Pollinations
#: devuelve HTTP 402 sin credito. Con `animagine-xl` se aproximan, no se igualan.
#:
#: Para cerrar la brecha se probo IP-Adapter con un recorte de uno de los
#: avatares buenos como ancla de estilo, que es lo mas parecido que hay a un
#: LoRA con lo que hay instalado. NO APORTA NADA y sale caro, asi que conviene
#: saberlo antes de volver a intentarlo: IP-Adapter Plus con un retrato de
#: personaje transfiere CONTENIDO, no solo estilo, y el peso es un filo.
#:
#:   - 0.15 -> sombreado suave, sin dano colateral
#:   - 0.25 -> pinta el lobo de naranja: el ancla impone su paleta
#:   - 0.35 -> con el lagarto no trae correa, pero mete borde decorativo
#:   - 0.40 -> le pone al lobo la correa del hocico del orco
#:
#: Con el orco, que tiene mandibula marcada, los cuatro lobos salieron con
#: bozal, correa o aro. Con la elfa nocturna, el lobo salia lavanda y sin
#: hocico. Es decir: un ancla de CARA no sirve para trasplantar estilo a otra
#: cara. Los dos avatares que hay instalados se hicieron SIN ancla: la receta
#: entera esta en el prompt, que es lo unico que queda escrito aqui.
NEGATIVO_AVATAR = (
    "multiple views, character sheet, reference sheet, sprite sheet, grid, "
    "wildlife photography, photograph, nature scene, grass, field, forest, "
    "sunset, dramatic sky, outdoor scenery, "
    "cel shading, flat color, flat vector art, thick outline, poster art, "
    "logo, neon, digital art, "
    "human face, person in a costume, fursuit, mask, hood, "
    "chibi, cute, deformed, blurry, "
    "picture frame, ornate frame, border, text, watermark, "
    "dark background, vignette"
)

SUFIJO_AVATAR = (
    "fantasy character portrait, painterly illustration, hand-painted, "
    "masterpiece, best quality, highly detailed, anime style, "
    "soft brushwork, textured shading, detailed fur, detailed eyes, "
    "warm natural palette, bust shot, three-quarter view, "
    "upper body, shoulders and chest visible, "
    "plain light cream background, studio lighting, "
    "no text, no watermark"
)

#: Prompt Y CARACTERISTICAS DE LA CRIATURIDAD.
#:
#: "panther warrior portrait" sale un humano con capucha contra una ciudad neon,
#: y "werewolf alpha portrait" sale un chico anime de pelo azul. A `animagine-xl`
#: hay que darle los rasgos uno a uno y en su idioma (etiquetas de Danbooru),
#: no una frase de fantasy: el modelo responde a `wolf ears, muzzle, fangs` y
#: pasa por alto `unmistakably a panther`.
AVATARES = {
    "humano": "1boy, human knight, plate armour, beard, heraldic surcoat, "
              "serious expression, " + SUFIJO_AVATAR,
    "orco": "1boy, orc, heavy brow, tusks, broken nose, battle scars, "
            "iron shoulder plates, " + SUFIJO_AVATAR,
    "goblin": "1boy, goblin, huge pointed ears, wide grin, warts, "
              "crown of twisted iron, " + SUFIJO_AVATAR,
    "elfo": "1girl, elf, long pointed ears, sharp cheekbones, braided hair, "
            "circlet, " + SUFIJO_AVATAR,
    "hombre_lobo": (
        "1boy, werewolf, full wolf head, no human features, long grey wolf "
        "muzzle, bared fangs, pricked wolf ears, thick shaggy grey fur, "
        "burning amber eyes, ruff of fur over the shoulders, powerful neck, "
        + SUFIJO_AVATAR),
    "vampiro": "1girl, vampire, pale skin, high cheekbones, dark hair, "
               "parted lips, fangs, high collar, " + SUFIJO_AVATAR,
    "dragon": "1boy, dragon, horned reptilian skull, scales, slit pupils, "
              "horned crown, smoke, " + SUFIJO_AVATAR,
    "elfo_nocturno": "1girl, dark elf, obsidian skin, long pointed ears, "
                     "violet eyes, hollow gaze, black circlet, "
                     + SUFIJO_AVATAR,
    "hombre_pantera": (
        "1girl, black panther, full panther head, no human features, "
        "short black muzzle, bared canine fangs, rounded feline ears, "
        "sleek black fur, glowing amber slit eyes, thick neck, "
        + SUFIJO_AVATAR),
    "hombre_lagarto": "1boy, lizardman, long scaly muzzle, jaw frill, "
                      "crocodile eyes, green scales, " + SUFIJO_AVATAR,
}

#: Los personajes con cara propia (no bandos) van aparte: son gente del guion,
#: pero el mismo estilo les viene bien.
AVATARES_PERSONAJES = {
    "nara": "1girl, woman chronicler, hooded cloak, ink-stained fingers, "
            "calm watchful face, " + SUFIJO_AVATAR,
    "pik": "1boy, scared peasant, dirt on cheeks, torn shirt, wide eyes, "
           + SUFIJO_AVATAR,
    "dara": "1girl, village woman holding a lamp, plain shawl, weathered face, "
            + SUFIJO_AVATAR,
    "jefe_arco": "1boy, armoured commander, beard, scar, plumed helm, "
                + SUFIJO_AVATAR,
    "gobernante": "1boy, weary old ruler, hooded, long beard, sorrowful, "
                  + SUFIJO_AVATAR,
    "revancha": "1boy, ruined man in a torn cloak, bitter stare, ash on his "
                "shoulders, " + SUFIJO_AVATAR,
    "presentador": "1boy, crooked showman, painted grin, ruff collar, "
                   + SUFIJO_AVATAR,
    "rajoy": "1boy, middle aged man in a cheap suit, uncomfortable smile, "
             + SUFIJO_AVATAR,
}

#: Avatares que ya salen bien y NO hay que rehacer. Los dos que fallaban
#: (hombre_lobo y hombre_pantera) NO estan aqui a proposito: con `--fuerza` se
#: regeneran solo los que faltan de esta lista.
AVATARES_BIEN = (
    "humano", "orco", "goblin", "elfo", "vampiro", "dragon",
    "elfo_nocturno", "hombre_lagarto",
    "nara", "pik", "dara", "jefe_arco", "gobernante", "revancha",
    "presentador", "rajoy",
)

# Fondos de las cinematicas: (nombre, prompt)
FONDOS = {
    "ceniza": "dark fantasy kingdom covered in grey ash, burning horizon, ruined towers, cinematic, pixel art style, no text",
    "camino": "ash covered road through dead forest at dusk, fantasy, cinematic wide shot, pixel art style, no text",
    "aldea": "small medieval fantasy village at night with warm lantern light, hope, cinematic, pixel art style, no text",
    "ruinas": "ancient underground ruins glowing with embers, fantasy, cinematic, pixel art style, no text",
    "fortaleza": "fortress on a cliff above a valley of ash, fantasy, cinematic, pixel art style, no text",
    "trono": "throne room of ash and broken pillars, dragon silhouette in the background, fantasy, cinematic, pixel art style, no text",
    "campamento": "fantasy war camp at night with campfire and banners, cinematic, pixel art style, no text",
    "asalto": "fantasy night assault, burning banners and stone stairs, cinematic, pixel art style, no text",
    "amanecer": "dawn breaking over a peaceful fantasy valley with villages and forests, warm hopeful light, calm before the storm, cinematic wide shot, pixel art style, no text",
    "umbral": "colossal cracked stone portal floating above an ashen plain, violet light spilling out, tiny silhouettes watching from below, dark fantasy, cinematic wide shot, pixel art style, no text",
    "estandartes": "war banners of rival fantasy factions gathered before a battlefield of ash, huge dragon shadow overhead, epic standoff, cinematic wide shot, pixel art style, no text",
}


def slug(nombre):
    s = nombre.lower().strip()
    for a, b in (("á", "a"), ("à", "a"), ("é", "e"), ("è", "e"), ("í", "i"),
                 ("ì", "i"), ("ó", "o"), ("ò", "o"), ("ú", "u"), ("ù", "u"),
                 ("ñ", "n"), ("ü", "u"), ("ç", "c")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def cargar_key():
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), encoding="utf-8") as f:
            for linea in f:
                if linea.startswith("POLLINATIONS_API_KEY="):
                    return linea.split("=", 1)[1].strip()
    except OSError:
        pass
    return os.environ.get("POLLINATIONS_API_KEY")


def _pedir(prompt, destino, key, ancho, alto, modelo="flux", intentos=3):
    if os.path.exists(destino):
        print(f"  ya existe: {os.path.basename(destino)}")
        return True
    url = (
        f"https://gen.pollinations.ai/image/{urllib.parse.quote(prompt)}"
        f"?model={modelo}&width={ancho}&height={alto}&nologo=true&private=true"
    )
    req = urllib.request.Request(url)
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    for intento in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                datos = resp.read()
            if len(datos) < 2000:
                raise ValueError("respuesta demasiado pequena")
            with open(destino, "wb") as f:
                f.write(datos)
            print(f"  generada: {os.path.basename(destino)}")
            return True
        except Exception as e:  # noqa: BLE001 - red intermitente
            print(f"  fallo ({e}), reintento {intento + 1}/{intentos}")
            time.sleep(4)
    return False


def generar_cartas(key, solo_nuevas=True):
    os.makedirs(CARPETA, exist_ok=True)
    print("Cartas:")
    for bando, cartas in TODOS.items():
        for carta in cartas:
            estilo = (
                f"{carta.nombre}, fantasy {RAZA[bando]} character portrait, pixel art style, "
                "16-bit retro video game card illustration, dark fantasy, no text, no words, "
                "no letters, no watermark, no signature, no border"
            )
            destino = os.path.join(CARPETA, f"{bando}_{slug(carta.nombre)}.png")
            _pedir(estilo, destino, key, 256, 320)
            time.sleep(1.2)


#: Modelo de los avatares que NO son un bando (Nara, Piks, el presentador...).
#: Es el mismo con el que estan los diecisiete que salen bien. Los de bando van
#: en pixel art: `MODELO_AVATAR`.
AVATAR_MODELO = "animagine-xl-4.0.safetensors"

#: El `.bat` que arranca ComfyUI en una ventana nueva. Vive fuera del repo
#: (es la instalacion local del jugador), asi que `arrancar_servidor` avisa si
#: no esta en vez de fallar: los avatares se pueden generar a mano desde la
#: interfaz de ComfyUI y el juego no se entero.
COMFY_BAT = r"E:\AI\start-comfyui.bat"


def generar_avatar_comfyui(nombre, prompt, servidor="http://127.0.0.1:8188",
                           pasos=28, cfg=7.0, lado=256, destino=None,
                           modelo=None, ancla=None, peso=0.35):
    """Un avatar por ComfyUI. Devuelve True si se genero.

    `modelo` y `ancla` decides el idioma visual: pixel art del juego para los
    bandos que tienen carta, anime para el resto. Se generan a 256, que es el
    tamano final: escalar pixel art despues funde los pixeles y deja de leerse.
    """
    import generar_cartas_comfyui as comfy

    if comfy.arrancar_servidor(servidor, COMFY_BAT, 180) is None:
        print("  ComfyUI no respondio en %s" % servidor)
        return False
    if destino is None:
        destino = os.path.join(ASSETS, f"avatar_{nombre}.png")
    negativo = ", ".join(p for p in (comfy.NEGATIVO, NEGATIVO_AVATAR) if p)
    return bool(comfy.generar_imagen(
        servidor, prompt, negativo, destino, random.randrange(2 ** 32),
        lado, lado, pasos, cfg, modelo or MODELO_AVATAR,
        ancla=ancla, peso_ipadapter=peso if ancla else 0.4))


def ancla_de_bando(bando):
    """La carta del bando sirve de ancla de estilo para su avatar.

    Es el truco que hace que esto salga bien: la carta ya ES esa criatura en el
    estilo exacto del juego, asi que en vez de DESCRIBIR el estilo con palabras
    (que es donde se fallaba, cuatro rondes seguidas) se le enseña una imagen
    que ya lo tiene. Con el moodboard como ancla salian gatos y hienas con cara
    de mascara; con la carta del bando salen lobo y pantera.

    Devuelve None si el bando no tiene carta, y entonces toca el moodboard.
    """
    cartas = [c for c in TODOS.get(bando, []) if os.path.exists(
        os.path.join(CARPETA, f"{bando}_{slug(c.nombre)}.png"))]
    if not cartas:
        return None
    # La primera basta: son todas del mismo bando y del mismo estilo.
    return os.path.join(CARPETA, f"{bando}_{slug(cartas[0].nombre)}.png")


def generar_avatares(key, solo=None, fuerza=False, comfyui=False):
    """Genera los avatares. `solo` limita a una lista de nombres.

    Con `--fuerza` se rehacen SOLO los que no estan en `AVATARES_BIEN`: los
    demas ya salian bien y regenerarlos seria gastar peticiones para obtener
    algo peor o simplemente distinto.

    `comfyui` usa ComfyUI en vez de Pollinations, que esta muerto: la key de
    `.env` no tiene credito y devuelve HTTP 402.
    """
    print("Avatares:")
    os.makedirs(ASSETS, exist_ok=True)
    objetivo = dict(AVATARES_PERSONAJES)
    objetivo.update(AVATARES)

    if solo:
        faltan = [n for n in solo if n in objetivo]
        if not faltan:
            raise SystemExit(
                "ninguno de %s es un avatar conocido; conocidos: %s"
                % (", ".join(solo), ", ".join(sorted(objetivo))))
    elif fuerza:
        faltan = [n for n in objetivo if n not in AVATARES_BIEN]
        print("  con --fuerza solo se rehacen los que no estan en "
              "AVATARES_BIEN: %s" % ", ".join(faltan))
    else:
        faltan = list(objetivo)

    for nombre in faltan:
        destino = os.path.join(ASSETS, f"avatar_{nombre}.png")
        ancla = ancla_de_bando(nombre)
        if comfyui:
            if ancla:
                # Pixel art del juego, no anime: el prompt es el de las cartas.
                generar_avatar_comfyui(
                    nombre,
                    f"fantasy {RAZA.get(nombre, 'fantasy warrior')} character portrait, "
                    f"{nombre}, pixel art style, 16-bit retro video game "
                    f"illustration, dark fantasy, no text, no watermark, "
                    f"no signature, no border",
                    destino=destino, modelo=MODELO_AVATAR, ancla=ancla,
                    peso=PESO_ANCLA_AVATAR)
            else:
                # Sin carta de este bando (los personajes con nombre propio no
                # son un bando): se usa el prompt de siempre con el modelo que
                # hizo los demas.
                generar_avatar_comfyui(nombre, objetivo[nombre], destino=destino,
                                       modelo="animagine-xl-4.0.safetensors",
                                       ancla=None)
        else:
            _pedir(objetivo[nombre], destino, key, 256, 256)
        time.sleep(1.2)


def generar_fondos(key, solo_nuevos=True):
    print("Fondos de cinematicallyas:")
    destino_carpeta = os.path.join(ASSETS, "fondos")
    os.makedirs(destino_carpeta, exist_ok=True)
    for nombre, prompt in FONDOS.items():
        destino = os.path.join(destino_carpeta, f"{nombre}.png")
        _pedir(prompt, destino, key, 640, 360)
        time.sleep(1.5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fuerza", action="store_true", help="regenera tambien lo existente")
    parser.add_argument("--solo", choices=["cartas", "avatares", "fondos"], default="todo")
    parser.add_argument("--avatar", nargs="+", metavar="NOMBRE",
                        help="genera solo estos avatares (por ejemplo: "
                             "hombre_lobo hombre_pantera)")
    parser.add_argument("--comfyui", action="store_true",
                        help="los avatares van por ComfyUI con animagine-xl en "
                             "vez de Pollinations, que devuelve HTTP 402 sin "
                             "credito")
    args = parser.parse_args()

    key = cargar_key()
    if not key:
        print("Sin key en .env: usando modo anonimo (muy limitado).")

    if args.fuerza:
        # Los avatares NO se borran aqui: los que ya salen bien (los de
        # `AVATARES_BIEN`) se perderian y luego hay que pagar peticiones para
        # regenerarlos. `generar_avatares` decide por su cuenta cuales rehacer.
        carpetas = ["cartas"]
        if args.solo in ("fondos", "todo"):
            carpetas.append(os.path.join("assets", "fondos"))
        if args.solo == "cartas":
            carpetas = ["cartas"]
        for carpeta in carpetas:
            ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), carpeta)
            for f in os.listdir(ruta) if os.path.isdir(ruta) else []:
                if f.endswith(".png"):
                    os.remove(os.path.join(ruta, f))

    if args.solo in ("cartas", "todo"):
        generar_cartas(key)
    if args.solo in ("avatares", "todo"):
        generar_avatares(key, solo=args.avatar, fuerza=args.fuerza,
                         comfyui=args.comfyui)
    if args.solo in ("fondos", "todo"):
        generar_fondos(key)
    print("Listo.")


if __name__ == "__main__":
    main()