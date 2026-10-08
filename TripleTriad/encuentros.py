"""Encuentros: la parte que revela mundo.

Idea de la biblia: un encuentro no es solo "comprar carta / marcharte". Cada
uno revela algo del mundo, del misterio o del protagonista, ademas de dar (o
quitar) la recompensa mecanica.

Por que un modulo aparte
------------------------
`campana.ENCUENTROS` ya existe con sus 4 tipos, sus opciones y sus efectos, y
`aplicar_encuentro` ya sabe aplicar esos efectos. Eso NO se toca: es la parte
funcional que los tests y el balance ya cubren.

Lo que faltaba era la voz: que el mercader reconozca que tus cartas son
imposibles, que el anciano sepa mas de lo que dice, que la hermandad tenga una
razon para estar ahi. Eso vive aqui, como datos.

El encuentro REVELA al elegir: `revela_encuentro` se llama desde la pantalla
y suma una revelacion al estado, ademas del efecto mecanico.

`campana` y `pantallas` importan este modulo; este no importa ninguno de los
dos.

Texto visible en ASCII, como todo el juego.
"""

# --------------------------------------------------------------- revelaciones
# id -> que se aprende del mundo al pasar por ahi.
#
# Estas son las semillas del Compendio dual (incremento 7): cada encuentro
# apunta a una entrada que despues se pode ampliar a las 250 cartas.

LORE = {
    "mercader": {
        "encuentro": "Mercader Errante",
        "escena": "campamento",
        "revelacion": "enc_mercader_falsificacion",
        "titulo": "Falsificacion",
        "linea": [
            "- Bonita falsificacion.", "- No es falsa.",
            "- Muchacho... esa carta tiene cuatrocientos anos.",
        ],
        "reaccion": {
            # el mercador reacciona a la faccion del jugador
            "humano": "- Un humano. La corona de un rey que murio antes de tu abuelo.",
            "orco": "- Un orco comprando. Anoto el dia en la agenda.",
            "elfo": "- Un elfo. No se lo vendo. Se lo presto. Hay diferencia.",
            "goblin": "- Un goblin. Al menos un goblin no pregunta por el precio.",
            "hombre_lobo": "- Un lobo. De dia. Caro el dia.",
            "vampiro": "- Un vampiro. No acepto billetes. Acepto acero.",
            "dragon": "- Un dragon. Todo lo que tengo es tuyo. Todo.",
            "elfo_nocturno": "- Un nocturno. Cierra antes de que salga el sol.",
            "hombre_pantera": "- Una pantera. No mire. Yo no miro.",
            "hombre_lagarto": "- Un lagarto. Paga cuando puede. Siempre puede.",
        },
    },
    "anciano": {
        "encuentro": "El Anciano del Umbral",
        "escena": "ruinas",
        "revelacion": "enc_anciano_origen",
        "titulo": "El Que Sabe Demasiado",
        "linea": [
            "- Veo que llevas cartas raras. No deberian existir.",
            "- No son raras. Son nuevas. El mundo las todavia no escribio.",
            "- Eso no tiene sentido. - Aqui todo tiene sentido, muchacho.",
        ],
        "reaccion": {
            "humano": "- Un humano mirando un libro que no es un libro.",
            "orco": "- Un orco. Poca gente lee. Tu lees. Bien.",
            "elfo": "- Un elfo. Entonces no viste nuestra version.",
            "goblin": "- Un goblin leyendo. Esto si es una sorpresa.",
            "hombre_lobo": "- Un lobo. De noche se lee mejor.",
            "vampiro": "- Un vampiro. Sabe cosas que yo todavia no.",
            "dragon": "- Un dragon. El te mira y no le tiembla la voz.",
            "elfo_nocturno": "- Un nocturno. Nosotros tambien lo expulsamos.",
            "hombre_pantera": "- Una pantera. No hace ruido al escuchar.",
            "hombre_lagarto": "- Un lagarto. Los lagartos recuerdan mejor.",
        },
    },
    "hermandad": {
        "encuentro": "Hermandad de Armas",
        "escena": "campamento",
        "revelacion": "enc_hermandad_pacto",
        "titulo": "Pacto",
        "linea": [
            "- Nuestra victoria sera tu victoria. No es generosidad: es cuentas.",
            "- En el libro del bando, tu nombre ya estaba escrito. Antes de llegar.",
        ],
        "reaccion": {
            "humano": "- Un humano. Nos cuadra. Sumate.",
            "orco": "- Un orco. Bien. Uno mas que no se asusta.",
            "elfo": "- Un elfo. Con lo que dijiste del bosque, casi te dejamos ir.",
            "goblin": "- Un goblin. Robanos algo y te aceptamos igual.",
            "hombre_lobo": "- Un lobo. De noche somos mas.",
            "vampiro": "- Un vampiro. No sois muchos, pero sois.",
            "dragon": "- Un dragon. Eso cambia el peso de la conversacion.",
            "elfo_nocturno": "- Un nocturno. Nadie quiere a los de la noche. Nadie.",
            "hombre_pantera": "- Una pantera. :/ Te lo dije: honor o libertad.",
            "hombre_lagarto": "- Un lagarto. Esperamos. Vosotros correis.",
        },
    },
    "caravana": {
        "encuentro": "Caravana de Sobres",
        "escena": "campamento",
        "revelacion": "enc_caravana_sobres",
        "titulo": "Sobres",
        "linea": [
            "- Todo el mundo paga. Casi todo el mundo gana.",
            "- Y si sale una carta de un rey muerto? - Eso no es una carta. Es un documento.",
        ],
        "reaccion": {
            "humano": "- Un humano con un sobre. Suerte.",
            "orco": "- Un orco con un sobre. No me negateis nada.",
            "elfo": "- Un elfo. Si, lo he visto antes.",
            "goblin": "- Un goblin con un sobre. Probemos el doble.",
            "hombre_lobo": "- Un lobo con un sobre. Huelo el sobre.",
            "vampiro": "- Un vampiro con un sobre. Sabe a dinero viejo.",
            "dragon": "- Un dragon con un sobre. Eso vale mas que el sobre.",
            "elfo_nocturno": "- Un nocturno con un sobre. De dia, por una vez.",
            "hombre_pantera": "- Una pantera con un sobre. Sin preguntas.",
            "hombre_lagarto": "- Un lagarto con un sobre. Todos los sobres son iguales.",
        },
    },
    "hostil": {
        "encuentro": "Alguien Te Ha Visto",
        "escena": "camino",
        "revelacion": "enc_hostil_reconocimiento",
        "titulo": "Reconocido",
        "linea": [
            "- De donde sacas esas cartas?",
            "- Son cartas. - No son cartas. Son NOMBRES. Y los nombres todavia no han pasado.",
        ],
        "reaccion": {
            "humano": "- Un humano con eses. Eso es del otro lado.",
            "orco": "- Un orco aqui. Con eses. Que historia.",
            "elfo": "- Un elfo. No.}",
            "goblin": "- Un goblin. Mas te vale que sean de verdad.",
            "hombre_lobo": "- Un lobo. No me gusta esto.",
            "vampiro": "- Un vampiro. Esas cartas tienen dueno y no sos vos.",
            "dragon": "- Un dragon. Que conmigo, con que vienes.",
            "elfo_nocturno": "- Un nocturno. Esas cartas no son nuestras.",
            "hombre_pantera": "- Una pantera. Ocultalas.",
            "hombre_lagarto": "- Un lagarto. Eso no se muestra. Ni a un amigo.",
        },
    },
    "nara": {
        "encuentro": "Nara, la Cronista",
        "escena": "campamento",
        "revelacion": "enc_nara_eleccion",
        "titulo": "Nara Escribe",
        "linea": [
            "- Necesito que entiendas una cosa: aqui esto se llama Juicio.",
            "- Las cartas son ecos. Cuando alguien coloca una, el eco aparece.",
            "- Tuya. Es un eco de otra cosa. De un mundo que ya te conoce.",
        ],
        "reaccion": {
            "humano": "- Con ese mazo. Anotado. Esto no lo leas en voz alta.",
            "orco": "- Con ese mazo. Bien. Nadie va a creerte, y eso nos sirve.",
            "elfo": "- Con ese mazo. Vas a tener que elegir a quien le decis la verdad.",
            "goblin": "- Con ese mazo. Eres el primero que devuelve algo por nada.",
            "hombre_lobo": "- Con ese mazo. La luna va a opinar.",
            "vampiro": "- Con ese mazo. Hay gente aqui que todavia esta viva.",
            "dragon": "- Con ese mazo. Cuidado con quien lo ve.",
            "elfo_nocturno": "- Con ese mazo. Deberiamos hablar de noche.",
            "hombre_pantera": "- Con ese mazo. La verdad no es de nadie.",
            "hombre_lagarto": "- Con ese mazo. Alguien hizo esto hace mucho.",
        },
    },
}

#: El encuentro hostil y el de Nara son opcionales: no estan en
#: `campana.ENCUENTRO_POR_NODO`, se ofrecen aparte. Ver `disponibles`.
OPCIONALES = ("hostil", "nara")

#: Nara solo aparece si ya confias en ella. Antes te observa desde lejos.
ENCUENTRO_NARA = {
    "id": "nara",
    "titulo": "Nara, la Cronista",
    "escena": "campamento",
    "texto": "- Sento antes de verte. Traes cartas que aca no existen.",
    "opciones": [
        {"id": "escuchar", "texto": "Escucharla (+1 a tu carta mas debil)",
         "efecto": "mas_debil"},
        {"id": "preguntar", "texto": "Preguntarle por el Umbral (sube lo que sabes)",
         "efecto": "debilitar"},
    ],
    "confianza_minima": 3,
}

#: El encuentro hostil no da recompensa: cuesta. Verifica que lo entienda.
ENCUENTRO_HOSTIL = {
    "id": "hostil",
    "titulo": "Alguien Te Ha Visto",
    "escena": "camino",
    "texto": "- De donde sacas esas cartas? No es una pregunta.",
    "opciones": [
        {"id": "ocultar", "texto": "Ocultar las cartas (el rival llega -1)",
         "efecto": "debilitar"},
        {"id": "mostrar", "texto": "Mostrarlas (Nara te busca antes)",
         "efecto": "mejorar"},
    ],
    "confianza_minima": 0,
}


def _datos_extra(enc):
    """Definition de los encuentros opcionales, con la misma forma que
    `campana.ENCUENTROS` para que la pantalla los pueda dibujar."""
    return {"hostil": ENCUENTRO_HOSTIL, "nara": ENCUENTRO_NARA}.get(enc, {})


def titulo_encuentro(enc_id):
    """Titulo con el que se presenta el NPC.

    Vive en LORE y no se lee de campana.ENCUENTROS para no importar campana
    desde aca (seria un ciclo). Hay un test que verifica que los dos digan
    exactamente lo mismo.
    """
    return LORE.get(enc_id, {}).get("encuentro", "")


def escena_encuentro(enc_id):
    """Fondo del encuentro. Mismo criterio que `titulo_encuentro`."""
    return LORE.get(enc_id, {}).get("escena", "campamento")


# ------------------------------------------------------------------- publico


def lore_de(enc_id):
    """Revelacion y lineas de un encuentro. Vacio si no aplica."""
    return LORE.get(enc_id, {})


def linea_principal(enc_id):
    """La linea que resume que aprendes. Se muestra tras elegir."""
    datos = LORE.get(enc_id, {})
    lineas = datos.get("linea", [])
    return lineas[-1] if lineas else ""


def titulo_revelacion(enc_id):
    return LORE.get(enc_id, {}).get("titulo", "")


def revelacion_de(enc_id):
    return LORE.get(enc_id, {}).get("revelacion", "")


def reacciones(enc_id):
    """Linea por faccion del jugador."""
    return LORE.get(enc_id, {}).get("reaccion", {})


def reaccion(enc_id, faccion_jugador):
    return LORE.get(enc_id, {}).get("reaccion", {}).get(faccion_jugador, "")


def escena_antes(enc_id, faccion_jugador, musica=None):
    """Como empieza el encuentro: la voz del NPC y su reaccion al mazo.

    Devuelve una escena lista para `cinematicas.reproducir`, o lista vacia.
    """
    from ui import TEXTO_ON

    def esc(linea, hablante=None, fondo=None, retrato=None, color=None, mundo="juego"):
        return {"texto": linea, "hablante": hablante, "fondo": fondo, "retrato": retrato,
                "efecto": "dialogo", "musica": musica, "color": color, "mundo": mundo}

    fondo = escena_encuentro(enc_id)
    escenas = []
    # 1. el NPC se presenta
    titulo = titulo_encuentro(enc_id)
    if titulo:
        escenas.append(esc(titulo.upper(), fondo=fondo))
    # 2. su reaccion al mazo: lo que ve cuando te mira las cartas
    linea = reaccion(enc_id, faccion_jugador)
    if linea:
        escenas.append(esc(linea, hablante=titulo, fondo=fondo, color=TEXTO_ON))
    return escenas
