"""Fuente unica de verdad del estilo visual de las cartas.

Este modulo es la biblia de estilo. Lo consumen las herramientas de generacion
(nunca el juego en si: `generar_cartas_comfyui.py` es una herramienta de
desarrollo y el juego sigue funcionando sin ComfyUI ni Pillow).

De donde sale cada cosa:

- El bloque fijo de estilo, la paleta y las prohibiciones vienen de
  `estilo/estilo.json`, que a su vez sale del moodboard
  (`E:\\AI\\moodboard.png`) via `extraer_estilo_moodboard.py`.
- Los diccionarios de traduccion (raza, clase, rareza) y la atmosfera por
  faccion viven aqui para que el generador sea solo mecanica.

Cambio de estilo = cambiar el moodboard y regenerar el JSON. No hace falta
tocar codigo.
"""

import json
import os

RAIZ = os.path.dirname(os.path.abspath(__file__))
RUTA_FICHA = os.path.join(RAIZ, "estilo", "estilo.json")


# ------------------------------------------------------------------ ficha ----

def cargar_ficha(ruta=RUTA_FICHA):
    """Lee la ficha de estilo; devuelve {} si no existe (el script sigue vivo)."""
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


FICHA = cargar_ficha()

# Paleta del moodboard en la posicion en que la usan las promps: texto plano.
_PALETA = [c.get("hex", "") for c in (FICHA.get("paleta") or []) if c.get("hex")]
PALETA = _PALETA

# Bloques de prompt que manda la ficha (en ingles, listos para SDXL).
PROMPT_ESTILO = (FICHA.get("prompts_sdxl") or {}).get("positivo", "").strip()
NEGATIVO_ESTILO = (FICHA.get("prompts_sdxl") or {}).get("negativo", "").strip()


# Lo que no cambia nunca, venga de donde venga el estilo: el encuadre de
# retrato de carta. El bloque de la ficha NO va aqui: va como variante `crt`
# para que `--estilo carta` lo sustituya en vez de contradecirse con el.
FIJO = ("single character extreme close-up face portrait, head and shoulders "
        "only, subject fills the frame, no environment, centered composition, "
        "card illustration")

# Negativo: lo de la ficha + las prohibiciones de la ficha traducidas a
# terminos que entiende SDXL + lo que ya sabiamos que estorba. Sin repetir
# terminos, aunque la ficha ya los traiga.
def _sin_repetir(*frases):
    visto, salida = set(), []
    for frase in frases:
        for termino in frase.split(","):
            termino = termino.strip()
            clave = termino.lower()
            if termino and clave not in visto:
                visto.add(clave)
                salida.append(termino)
    return ", ".join(salida)


NEGATIVO = _sin_repetir(
    NEGATIVO_ESTILO,
    "smooth gradients, airbrushed, soft shading, anti-aliasing, blurred",
    "photorealistic photo, 3d render, cgi, vector art",
    "white background, modern ui, watermark, text, letters, logo, border, frame",
    "smiling, cheerful, cute, chibi, bright neon colors, pastel colors",
    "low quality, lowres, jpeg artifacts, deformed, bad anatomy",
    "extra limbs, extra fingers, cropped, multiple characters, crowd",
    "modern clothing, sci-fi",
)


# --------------------------------------------------------- traducciones ------

RAZA_EN = {
    "humano": "human", "orco": "orc", "goblin": "goblin", "elfo": "elf",
    "hombre_lobo": "werewolf", "vampiro": "vampire", "dragon": "dragon",
    "elfo_nocturno": "dark elf", "hombre_pantera": "panther warrior",
    "hombre_lagarto": "lizardman warrior", "enano": "dwarf",
    "no_muerto": "undead", "esqueleto": "skeleton", "hombre_rata": "ratman",
    "gnomo": "gnome", "centauro": "centaur", "trol": "troll",
}

CLASE_EN = {
    "guerrero": "warrior", "caballero": "knight", "mago": "mage",
    "hechicero": "sorcerer", "nigromante": "necromancer", "arquero": "archer",
    "paladin": "paladin", "berserker": "berserker", "asesino": "assassin",
    "druida": "druid", "chaman": "shaman", "clerigo": "cleric",
    "curandero": "healer", "monje": "monk", "bardo": "bard",
    "invocador": "summoner", "guardian": "guardian", "cazador": "hunter",
    "brujo": "warlock", "oraculo": "oracle", "reliquiario": "reliquary keeper",
    "capitan": "captain", "senor": "lord", "dama": "lady", "rey": "king",
    "reina": "queen", "profeta": "prophet", "heraldo": "herald",
}

# Atmosfera de fondo por faccion: da consistencia visual a toda la serie.
FACCION_VISUAL = {
    "goblin": "a raucous goblin warband lair full of stolen banners and scrap metal",
    "elfo": "an ancient elven forest kingdom, moss, silver leaves and standing stones",
    "hombre_lobo": "a moonlit forest hunt under a blood full moon",
    "vampiro": "a gothic vampire crypt with crimson drapes, candles and old coffins",
    "dragon": "a volcanic dragon domain with floating embers and scorched stone",
    "humano": "a ruined human kingdom, ash-covered throne and broken royal banners",
    "orco": "a harsh orcish frontier camp at the edge of the wilds",
    "elfo_nocturno": "a shadowed dark elf sanctuary bathed in violet gloom",
    "hombre_pantera": "a nocturnal rooftop hunt over a sleeping city, moonless night",
    "hombre_lagarto": "a misty lizardman swamp of green murk, reeds and bones",
}

RAREZA_EN = {
    "comun": "common rarity, practical worn gear, muted earthy tones",
    "rara": "rare, subtle arcane glow, finely crafted ornaments",
    "legendaria": "legendary, radiant golden aura, ornate exquisite regalia",
}

# Criaturas grandes tienden a salir en plano general: refuerzo el busto.
ENCUADRE_EXTRA = {
    "dragon": "close-up of the dragon's head and broad shoulders filling the frame",
    "hombre_lagarto": "close-up of the lizardman's scaled head and shoulders",
    "hombre_lobo": "close-up of the werewolf's snarling head and shoulders",
    "hombre_pantera": "close-up of the panther warrior's face and shoulders",
}

# Variantes de encuadre. La primera (crt) es la que dicta el moodboard; las
# demas se quedan para poder comparar en la hoja de contactos.
ESTILOS = {
    "crt": PROMPT_ESTILO,
    "carta": "painterly semi-realistic fantasy art, smooth brushwork",
    "pixel": "16-bit retro pixel art, crisp pixels, dithered shading",
    "concept": "epic fantasy concept art, digital painting",
    "retrato": "close-up heroic character portrait, dramatic pose",
    "grabado": "gothic ink engraving, etched linework, parchment tones",
    "cinematic": "cinematic still, atmospheric depth of field",
}

# Estilo que se usa si nadie lo dice: el del moodboard.
ESTILO_DEFECTO = "crt"


def paleta_txt():
    """La paleta del moodboard como frase para el prompt (si existe)."""
    if not PALETA:
        return ""
    hexes = ", ".join(PALETA[:6])
    return f"limited color palette ({hexes})"
