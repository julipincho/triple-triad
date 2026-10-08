"""Ficha de estilo del mundo del juego: anime + pixel art, sin filtro PSX.

Que es y que no es
-----------------
`estilo.py` es la biblia del arte de CARTAS: extraida de `E:\\AI\\moodboard.png`,
paleta apagada, CRT, dithering. Esa cadena queda intacta y este modulo no la
toca para nada.

Esto es lo otro: las imagenes del mundo en el que vive el duelista (encuentros,
retratos, fondos) y las cinematicas. Pide un aire distinto a proposito:

  - estilo anime, no el fantasia oscura con CRT de las cartas
  - pixel art, pero sin scanlines ni dithering forzado
  - colores mas vibrantes que el arte de cartas
  - y por lo tanto tiene que LEERSE distinto al mundo de las cartas

Como no se mezcla con las cartas
--------------------------------
El pipeline de cartas sigue su camino (`estilo.py` -> `generar_cartas_comfyui.py`
-> `postprocesar_cartas.py`). Este modulo alimenta scripts aparte, que importan
el transporte de ComfyUI de `generar_cartas_comfyui` sin modificarlo.

Detalle importante: el IPAdapter esta anclado a `estilo/ancla.png`, que es el
moodboard de las cartas. Si se usara aqui, imponeria el tinte apagado que
queremos quitar. Por eso este set se genera con IPAdapter DESACTIVADO
(`--sin-ipadapter`), y si en algun momento hace falta guia de estilo, se
construye un ancla nueva a partir de las primeras imagenes aceptadas.

Que checkpoint, y por que (medido, no supuesto)
----------------------------------------------
Se probaron los dos checkpoints disponibles, con la misma semilla:

  - Animagine XL 4.0 + prompt de pixel art -> anime POSTERIZADO. No es pixel
    art: son formas suaves con una paleta corta, no bloques de pixel deliberados.
    Bajar y cuantizar no lo arregla, porque el dibujo de origen ya es suave.
  - SpriteShaper (el de las cartas) + prompt anime -> pixel art REAL con
    personaje anime: pixeles cuadrados, cel shading, y respeta los props del
    prompt (trenza, libro abierto, capa).

Asi que el checkpoint de pixel art es el correcto, y el prompt es el que lleva
el anime. Es al reves de lo que se suponia, pero los resultados lo deciden.
El SpriteShaper es el MISMO que usan las cartas: no se toca la cadena de las
cartas, solo se usa el mismo modelo con otra variante de estilo.

Prompt: convencion de tags danbooru. No frases en espanol: la traduccion vive
aqui, en los diccionarios.

Texto visible en ASCII, como todo el juego.
"""

import json
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))
CARPETA_ESTILO = os.path.join(RAIZ, "estilo")
RUTA_FICHA = os.path.join(CARPETA_ESTILO, "escenas.json")

#: Checkpoint de este set: el MISMO de las cartas, por lo medido arriba.
#: Lo que cambia es la variante de estilo y el post-proceso.
CHECKPOINT = "pixelArtDiffusionXL_spriteShaper.safetensors"

#: IPAdapter apagado: el ancla de las cartas impondria el tinte apagado.
USAR_IPADAPTER = False
PESO_IPADAPTER = 0.0


# ------------------------------------------------------------------ ficha ----

def cargar_ficha(ruta=RUTA_FICHA):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


FICHA = cargar_ficha()

#: Paleta vibrante del mundo anime. Deliberadamente MAS saturada y clara que la
#: de las cartas: la diferencia de valor es lo que separa las dos esteticas.
PALETA = [c.get("hex", "") for c in (FICHA.get("paleta") or []) if c.get("hex")]

# ----------------------------------------------------------------- encuadres
# Cada tipo de imagen pide un encuadre distinto. No es un detalle: una escena
# de encuentro en plano busto se ve como un retrato de mas.

ENCUADRES = {
    # Retrato cuadrado para el cuadro de dialogo / retrato de cinematica.
    "retrato": ("upper body portrait, centered, looking at viewer, "
                "plain flat solid color background, empty background, "
                "nothing behind the subject, clean silhouette, "
                "no objects, no scenery"),
    # Retrato de NPC en encuentro, con un poco de aire arriba para el texto.
    "retrato_texto": ("upper body portrait, subject centered slightly low in "
                      "frame, plain background, uncluttered upper area"),
    # Escena de encuentro: el NPC en su sitio, con su entorno.
    "escena": ("full scene, medium wide shot, character placed off-center, "
               "detailed environment around them, clear area for text overlay"),
    # El duelista: de espaldas, sin rostro. El jugador se pone en su lugar.
    # Ojo: el sujeto ya dice "back view"; aqui solo va el encuadre, no se
    # repite o el modelo lo sobreemphasiza.
    "silueta": ("strong back-facing silhouette, no facial features, face not "
                "visible, plain flat solid color background, empty background, "
                "rim light on the outline, no objects, no scenery"),
    # Fondo de cinematica: sin personajes, solo lugar.
    "fondo": ("empty environment, establishing shot, no people, no characters, "
              "wide landscape, depth of field"),
}

# ------------------------------------------------------------------ estilos
# Los tres que se van a generar primero. Se registran en ESTILOS para poder
# pedir uno con `--estilo` si se reutiliza el generador.

ESTILOS = {
    # Anime limpio, con la textura de pixel art Mildy explicitada.
    "anime_pixel": ("anime style, pixel art, crisp square pixels, limited "
                    "palette, clean lineart, vibrant saturated colors, high "
                    "contrast cel shading, retro game aesthetic"),
    # Anime sin nada de pixel: por si el pixel no convive con el checkpoint.
    "anime": ("anime style, vibrant saturated colors, high contrast cel "
              "shading, clean lineart, detailed eyes"),
    # Pixel art sola, para comparar contra las cartas.
    "pixel_limpio": ("pixel art, crisp square pixels, vibrant saturated "
                     "colors, limited palette, clean silhouette, "
                     "no scanlines, no dithering, no CRT"),
}

ESTILO_DEFECTO = "anime_pixel"

#: Bloque comun a todo este set. Animagine rinde mejor con estos tags de calidad.
BASE_ANIME = "masterpiece, best quality, highly detailed"

#: Negativo comun. Quita lo que el anime checkpoint mete de mas (texto, firmas)
#: y lo que arruinaria el pixel art (blur, suavizado, degradados modernos).
NEGATIVO_BASE = (
    "lowres, worst quality, low quality, normal quality, jpeg artifacts, "
    "blurry, anti-aliased, smooth gradients, airbrush, soft brushstrokes, "
    "photorealistic, 3d render, scanlines, CRT screen, dithering, "
    "text, signature, watermark, username, logo, border, frame, ui elements, "
    "extra fingers, bad hands, malformed hands, bad anatomy, deformed"
)

#: SpriteShaper tiene un sesgo fuerte hacia Asia oriental: con cualquier
#: "fantasy village" o "fortress" devuelve pagodas, torii, faroles rojos y
#: carteles con ideogramas. El juego es fantasy europeo de barajas (duelistas
#: humanos, orcos, elfos, dragones, vampiros) y esa arquitectura no encaja.
#: Se vetoa aqui y no por entrada, porque sesguea los once fondos por igual.
NEGATIVO_ARQUITECTURA = (
    "asian architecture, chinese architecture, japanese architecture, "
    "pagoda, pagodas, torii gate, torii, shrine, temple gate, tatami, "
    "red paper lanterns, chopsticks, kimono, samurai, ninja, "
    "chinese characters, japanese characters, kanji, hangul, calligraphy, "
    "zen garden"
)

#: Solo para retratos. Un avatar va sobre un panel de dialogo: si el fondo esta
#: atiborrado, el personaje se pierde contra el cuadro y las cartas de fondo se
#: leen como si fueran parte de la interfaz. Se separa del NEGATIVO_BASE para no
#: aplicarlo a las escenas, donde el entorno SI se quiere.
NEGATIVO_RETRATO = (
    "busy background, cluttered background, detailed background, scenery, "
    "objects behind subject, patterns behind subject, collage, multiple "
    "images, pictures on wall, poster, banner, crowd"
)


# ---------------------------------------------------------- tradacciones ----
# Como en estilo.py, pero para este set. El generador de escenas las usa para
# traducir sujeto/entorno; el prompt va en ingles, en clave de tags.

RAZA_EN = {
    "humano": "human", "orco": "orc", "goblin": "goblin", "elfo": "elf",
    "hombre_lobo": "werewolf", "vampiro": "vampire", "dragon": "dragon",
    "elfo_nocturno": "dark elf", "hombre_pantera": "panther warrior",
    "hombre_lagarto": "lizardman",
}

#: Como se ve cada faccion en el mundo anime. Vibrante, no apagada.
FACCION_VISUAL = {
    "humano": "a ruined human kingdom with warm torchlight and tattered banners",
    "orco": "a harsh orcish frontier camp, dusty amber light, forged scrap",
    "elfo": "a luminous elven forest, teal and jade light, silver leaves",
    "goblin": "a goblin junkyard lair, neon trinkets and scavenged metal",
    "hombre_lobo": "a moonlit forest, cool blue moonlight, wild open ground",
    "vampiro": "a gothic vampire hall, deep crimson light and gold trim",
    "dragon": "a volcanic dragon roost, orange firelight against violet sky",
    "elfo_nocturno": "a twilight dark elf sanctuary, violet and indigo glow",
    "hombre_pantera": "a moonlit rooftop, magenta city glow, high above the street",
    "hombre_lagarto": "a swamp at dusk, green phosphorescent water and reeds",
}


# ------------------------------------------------------------ construccion ---

def paleta_txt():
    if not PALETA:
        return ""
    return f"palette accents ({', '.join(PALETA[:6])})"


def construir_prompt(sujeto, encuadre="retrato", estilo=ESTILO_DEFECTO,
                     faccion=None, extra=""):
    """Compone el prompt de una imagen del mundo del juego.

    `sujeto` va ya en ingles y en clave de tags (quien es).
    `encuadre` es una clave de ENCUADRES.

    El prompt entero va al modelo, que esta entrenado en ingles: si se cuela un
    acento o una tilde se desperdician tokens y la imagen sale peor. Por eso se
    avisa en vez de devolverlo en silencio.
    """
    partes = [BASE_ANIME]
    if sujeto:
        partes.append(sujeto)
    if faccion and faccion in FACCION_VISUAL:
        partes.append(FACCION_VISUAL[faccion])
    variante = ESTILOS.get(estilo, ESTILOS[ESTILO_DEFECTO])
    if variante:
        partes.append(variante)
    encuadre = ENCUADRES.get(encuadre, ENCUADRES["retrato"])
    if encuadre:
        partes.append(encuadre)
    color = paleta_txt()
    if color:
        partes.append(color)
    if extra:
        partes.append(extra)
    positivo = ", ".join(p for p in partes if p)
    _avisar_si_no_ascii(positivo)
    return positivo


def _avisar_si_no_ascii(texto):
    """Avisa si el prompt trae acentos: casi siempre es español colado."""
    import warnings
    malos = {ch for ch in texto if ord(ch) > 127}
    if malos:
        warnings.warn(
            "el prompt trae caracteres no ASCII ("
            + "".join(sorted(malos))
            + "): parece espanol. El modelo esta entrenado en ingles.",
            stacklevel=3)


def construir_negativo(extra="", retrato=False):
    """Negativo del set. `retrato` anade la lista de fondo limpio.

    El veto de arquitectura asiatica va siempre: es un sesgo del checkpoint, no
    una caracteristica de una imagen concreta.
    """
    base = NEGATIVO_BASE + ", " + NEGATIVO_ARQUITECTURA
    if retrato:
        base = base + ", " + NEGATIVO_RETRATO
    if extra:
        base = base + ", " + extra
    return base


# ------------------------------------------------------------ medidas -----
# Medidas reales que espera el juego (verificadas con Pillow):
#   - avatares  : 256x256 (los de las facciones ya son asi)
#   - fondos    : 512x256 (los de cinematica ya son asi), escalados a 1280x800
# Estas medidas son el destino; el generador produce a multipliplo y hace el
# downscale nearest-neighbour para que salga el pixel.

MEDIDAS = {
    "retrato": (256, 256),
    "retrato_texto": (320, 320),
    "escena": (512, 384),
    "silueta": (256, 256),
    "fondo": (512, 256),
}

#: Cuantas veces se genera mas grande que el destino para que el downsample
#: nearest-neighbour sea lo que produce el pixel (no un filtro).
ESCALA_GENERACION = 4


def _validar():
    """Coherencia interna del modulo. La usan los tests."""
    errores = []
    for clave in ENCUADRES:
        if clave not in MEDIDAS:
            errores.append(f"encuadre sin medidas: {clave}")
    for clave in MEDIDAS:
        if clave not in ENCUADRES:
            errores.append(f"medidas sin encuadre: {clave}")
    if USAR_IPADAPTER:
        # Ni con peso 0: si alguien lo enciende, el ancla de las cartas sigue
        # entrando en el grafo. Mejor quejarse aqui que descubrirlo en la imagen.
        errores.append("el ancla de las cartas no debe activarse en este set")
    if ESTILO_DEFECTO not in ESTILOS:
        errores.append("el estilo por defecto no existe")
    return errores
