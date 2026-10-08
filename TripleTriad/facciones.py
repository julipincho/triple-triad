"""Metadatos de facciones: identidad, arcos narrativos y afinidades.

Este modulo no importa nada del juego (ni reglas ni mazos) para poder ser usado
desde cualquier capa sin ciclos de importacion.
"""

# id -> configuracion
#   nombre      : nombre visible de la faccion
#   lema        : frase corta del menu
#   arco        : como se cuenta la campana de esa faccion
#   rival_final : faccion que se enfrenta en el nodo 'trono'
#   elemento    : faccion que recibe +2 en la casilla central (o None)
#   paleta      : (claro, oscuro) para cartas
#   acento      : color de interfaz de la faccion
#   inicial     : letra de reserva cuando falta el arte de una carta
#   jefe        : nombre del antagonista final
FACCIONES = {
    "goblin": {
        "nombre": "Goblins",
        "lema": "Todo es tuyo si se puede robar.",
        "arco": "Una chusma sale del foso y decide que el mundo le pertenece.",
        "rival_final": "dragon",
        "elemento": None,
        "paleta": ((104, 150, 62), (43, 74, 26)),
        "acento": (140, 200, 90),
        "inicial": "G",
        "jefe": "Ignarok, el Rey Oscuro",
    },
    "elfo": {
        "nombre": "Elfos",
        "lema": "El bosque recuerda quien lo ofende.",
        "arco": "Los elfos han visto crecer la ceniza y por primera vez en siglos toman las armas.",
        "rival_final": "dragon",
        "elemento": None,
        "paleta": ((172, 201, 236), (52, 78, 122)),
        "acento": (150, 210, 255),
        "inicial": "E",
        "jefe": "Ignarok, el Rey Oscuro",
    },
    "hombre_lobo": {
        "nombre": "Hombres Lobo",
        "lema": "La luna no negocia: marca la noche.",
        "arco": "La manada despierta hambrienta y debe decidir si muerde a la ciudad o a sus senores.",
        "rival_final": "vampiro",
        "elemento": "hombre_lobo",
        "paleta": ((120, 132, 152), (40, 45, 58)),
        "acento": (170, 185, 205),
        "inicial": "L",
        "jefe": "La Condesa Sanguinaria",
    },
    "vampiro": {
        "nombre": "Vampiros",
        "lema": "Tu sangre ya es nuestra.",
        "arco": "Los nobles de la noche salen de sus criptas porque el rey dragon ha roto el pacto antiguo.",
        "rival_final": "hombre_lobo",
        "elemento": None,
        "paleta": ((150, 52, 72), (66, 20, 32)),
        "acento": (235, 90, 120),
        "inicial": "V",
        "jefe": "Fenris, Alfa de la Manada",
    },
    "dragon": {
        "nombre": "Dragones",
        "lema": "El cielo arde y el suelo obedece.",
        "arco": "El linaje dragonico despierta con hambre y reclama el trono del mundo.",
        "rival_final": "humano",
        "elemento": "dragon",
        "paleta": ((200, 96, 52), (110, 40, 20)),
        "acento": (255, 140, 60),
        "inicial": "D",
        "jefe": "Aldric, Rey de los Humanos",
    },
    "humano": {
        "nombre": "Humanos",
        "lema": "Nadie recuerda quien fundo el reino. Todos recuerdan quien lo salvo.",
        "arco": "El reino humano ha caido en ceniza y una sola corona se levanta para reconstruirlo.",
        "rival_final": "dragon",
        "elemento": None,
        "paleta": ((212, 198, 158), (52, 66, 100)),
        "acento": (240, 205, 120),
        "inicial": "H",
        "jefe": "Ignarok, el Rey Oscuro",
    },
    "orco": {
        "nombre": "Orcos",
        "lema": "Somos el precio que nadie quiso pagar.",
        "arco": "Los orcos, arrojados a las fronteras del mundo, marchan hacia el trono que les negaron.",
        "rival_final": "elfo",
        "elemento": None,
        "paleta": ((158, 132, 84), (48, 42, 26)),
        "acento": (205, 165, 90),
        "inicial": "O",
        "jefe": "Lyra, Dama del Bosque",
    },
    "elfo_nocturno": {
        "nombre": "Elfos Nocturnos",
        "lema": "La sombra tambien florece.",
        "arco": "Expulsados del bosque por mirar al Umbral sin parpadear, los elfos nocturnos vuelven a por lo suyo.",
        "rival_final": "dragon",
        "elemento": None,
        "paleta": ((150, 110, 200), (50, 30, 80)),
        "acento": (190, 140, 255),
        "inicial": "N",
        "jefe": "Ignarok, el Rey Oscuro",
    },
    "hombre_pantera": {
        "nombre": "Hombres Pantera",
        "lema": "La noche caza en silencio.",
        "arco": "Nadie los vio llegar porque nadie mira al tejado. La manada de la sombra reclama su parte del trono.",
        "rival_final": "hombre_lobo",
        "elemento": None,
        "paleta": ((110, 110, 130), (30, 30, 45)),
        "acento": (230, 190, 90),
        "inicial": "P",
        "jefe": "Fenris, Alfa de la Manada",
    },
    "hombre_lagarto": {
        "nombre": "Hombres Lagarto",
        "lema": "El pantano no perdona.",
        "arco": "Del fango salieron con escamas y paciencia. El trono tambien se conquista esperando.",
        "rival_final": "orco",
        "elemento": None,
        "paleta": ((90, 150, 110), (30, 70, 45)),
        "acento": (120, 210, 150),
        "inicial": "S",
        "jefe": "Vorg, Senor de la Guerra",
    },
}

# Facciones que nunca se enfrentan a si mismas en campana.
def rivales_posibles(faccion):
    """Facciones rivales validas para `faccion` (nunca incluye la propia)."""
    return [f for f in FACCIONES if f != faccion]


def rival_final(faccion):
    return FACCIONES[faccion]["rival_final"]


def nombre(faccion):
    return FACCIONES.get(faccion, {}).get("nombre", faccion)


def acento(faccion):
    return FACCIONES.get(faccion, {}).get("acento", (240, 200, 90))


def elemento_central(faccion):
    return FACCIONES.get(faccion, {}).get("elemento")


def orden_facciones():
    """Orden estable de presentacion en menus."""
    return ["humano", "orco", "elfo", "goblin", "hombre_lobo", "vampiro", "dragon",
            "elfo_nocturno", "hombre_pantera", "hombre_lagarto"]


# Etiquetas cortas para el mapa de campana (los circles son pequenos)
CORTOS = {
    "humano": "HUM",
    "orco": "ORC",
    "elfo": "ELF",
    "goblin": "GOB",
    "hombre_lobo": "LOB",
    "vampiro": "VAM",
    "dragon": "DRA",
    "elfo_nocturno": "ENO",
    "hombre_pantera": "PAN",
    "hombre_lagarto": "LAG",
}


def corto(faccion):
    return CORTOS.get(faccion, faccion[:3].upper())