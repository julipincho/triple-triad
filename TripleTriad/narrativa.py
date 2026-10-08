"""Narrativa de campana: escenas previas, posteriores, decisiones y dialogo.

Por que un modulo aparte
------------------------
`campana.NODOS` ya existe y el motor (`escenas_nodo`, `info_duelo`) ya lo
consume. Ese grafo no se toca: son 5 duelos con bifurcacion y funciona.

Lo que faltaba era el pegamento de la biblia: cada nodo debe leerse como

    ESCENA_PREVIA -> DUELO -> ESCENA_POSTERIOR

y las escenas deben reaccionar a la faccion del jugador y a cuanto confia en
Nara. Eso vive aqui, como datos, no como logica nueva en el mapa.

Reglas que respetan los textos de este modulo:
  - El duelista no tiene nombre. Nunca se lo nombra.
  - El humor meta es constante, tambien en momentos serios.
  - Reactividad ligera: texto condicional simple. Un nodo tiene, como mucho,
    una decision moral.
  - Aqui las cartas se llaman Juicio. El duelista las sigue llamando cartas.
  - Texto visible en ASCII, como todo el resto del juego (ver campana.py).

`campana` puede importar este modulo; este modulo no importa `campana`.
"""

from ui import DORADO, TEXTO, TEXTO_ON


def esc(linea, hablante=None, fondo="ceniza", retrato=None, efecto="dialogo",
        musica=None, color=None, mundo="juego"):
    """Constructor de escena.

    Copia deliberada de `cinematicas.esc` en vez de importarlo: este modulo
    lo usa `cinematicas`, e importarlo seria un ciclo. Las claves son las
    mismas, asi que las escenas de aqui se pasan tal cual al reproductor.
    """
    return {"texto": linea, "hablante": hablante, "fondo": fondo, "retrato": retrato,
            "efecto": efecto, "musica": musica, "color": color or TEXTO,
            "mundo": mundo}


# --------------------------------------------------------------- reacciones
# Que dice el mundo cuando ve tu mazo. Leve: una linea, no un sermon.


REACCION_MAZO = {
    "humano": [
        "Un humano con la corona de una carta viva. La gente te mira y no sabe si saludarte.",
        "Llevas el rostro de un verdugo en una carta. Aqui eso tiene consecuencias.",
    ],
    "orco": [
        "Un orco en territorio humano. La conversacion se apaga mesa por mesa.",
        "Dicen que incendiaste Liria. Tu no has estado nunca en Liria.",
    ],
    "elfo": [
        "Un elfo. Nadie dice nada, que en el bosque es casi una amenaza.",
        "Tienen tradiciones que no leen a nadie. Tu lees las tuyas en carton.",
    ],
    "goblin": [
        "Un goblin con carta. Los goblins quieren ver esa baraja bien de cerca.",
        "Pik te reconoce del bosque. Eso aqui puede ser bueno o muy malo.",
    ],
    "hombre_lobo": [
        "Hombres lobo. El pueblo calcula si hay luna antes de saludarte.",
        "Cuentan los turnos de la luna mas que las palabras.",
    ],
    "vampiro": [
        "Un vampiro de dia. Alguien pregunta si comes ajo.",
        "Las puertas se abren tarde cuando paseas por el pueblo.",
    ],
    "dragon": [
        "Un dragon. Nadie te mira a los ojos y todos falsean.",
        "El barquero pide el doble sin decir por que.",
    ],
    "elfo_nocturno": [
        "Un elfo nocturno. De noche te reconocen; de dia, no.",
        "Dicen que los nocturnos miran al Umbral sin parpadear.",
    ],
    "hombre_pantera": [
        "Pantera. Nadie sabe si eres presa o peligro, y los dos son malos.",
        "Nadie te ve subir a los tejados. Eso es una cortesia.",
    ],
    "hombre_lagarto": [
        "Un lagarto. La gente tiene miedo al agua y le perdona a uno todo.",
        "El barquero no te cobra. Dice que ya has pagado.",
    ],
}

# --------------------------------------------------------------- decisiones
# Cada nodo tiene, como mucho, una decision moral. El efecto se aplica con
# campana.decidir() y mueve confianza_nara, conocimiento_umbral y revelacion.


DECISION = {
    "senda": {
        "id": "senda_herido",
        "pregunta": "Un vecino sangra en la cuneta. No pide nada. Solo no deja de sangrar.",
        "opciones": [
            {
                "id": "ayudar",
                "texto": "Parar y ayudar (pierdes tiempo)",
                "efecto": {"confianza": 1, "conocimiento": 1,
                           "revelacion": "senda_misericordia"},
                "respuesta": "El hombre no te da las gracias. Te da un nombre, y un "
                             "nombre es peor que un agradecimiento.",
            },
            {
                "id": "seguir",
                "texto": "Seguir caminado (llegas antes)",
                "efecto": {"conocimiento": 1, "revelacion": "senda_pragmatismo"},
                "respuesta": "Aguas arriba alguien grito. Tu ya estabas en otro camino.",
            },
        ],
    },
    "fortaleza": {
        "id": "fortaleza_umbral",
        "pregunta": "El capitan te ofrece algo: te deja pasar si le das una carta. "
                    "Solo una.",
        "opciones": [
            {
                "id": "dar_carta",
                "texto": "Darle una carta (abres el paso)",
                "efecto": {"confianza": -1, "conocimiento": 2,
                           "revelacion": "fortaleza_precio"},
                "respuesta": "Elige una. El capitan elige cual mira menos.",
            },
            {
                "id": "callar",
                "texto": "No dar nada (te cierran el paso)",
                "efecto": {"confianza": 2, "conocimiento": 1},
                "respuesta": "- Pasa con las cinco. - No. Pasa con las cinco o no pasa.",
            },
        ],
    },
}

# ------------------------------------------------------------------ dialogo
# Nara habla distinto segun cuanto confia en el. Bajo 3: te observa.
# Tres o mas: te acompana.


def nara_presentacion(confianza):
    if confianza >= 3:
        return ("- No necesito que me cuentes nada para saber a que atencion. "
                "Voy porque quiero ir. Y eso es raro en mi.")
    return ("- Te conozco poco. Te acompano porque necesito respuestas. "
            "No porque me caigas bien.")


def nara_umbral(confianza):
    if confianza >= 3:
        return ("- Si abrieras el Umbral, algo cruzaria en las dos direcciones. "
                "Tu ya cruzaste. No te lo pregunto por cortesia.")
    return ("- Hay algo del otro lado que todavia no ha cruzado. Cuando cruce, "
            "va a ser tarde.")


def nara_victoria(confianza):
    if confianza >= 3:
        return "- Bien. Y no es por la carta que perdiste: es por lo que entendiste."
    return "- Ganaste. Eso no dice nada todavia."


def nara_derrota(confianza):
    if confianza >= 3:
        return "- No pasa nada. Perder un duelo es lo mas barato que vas a hacer hoy."
    return "- Otra vez. Dime que al menos estabas aprendiendo algo."


# ------------------------------------------------------------------- escenas
# `previa` suma caracter a lo que ya dice campana.NODOS (no lo reemplaza).
# `posterior` se reproduce despues del duelo.


NARRATIVA = {
    "senda": {
        "previa": [
            esc("La senda sube entre pinos negros. En la cuneta hay un hombre que "
                "sangra y no te pide nada.", fondo="camino"),
            esc("Nara mira al hombre. Luego mira tus cartas. Luego decide no decir nada.",
                hablante="Nara", fondo="camino"),
        ],
        "posterior": [
            esc("Adelante, la senda se estrecha y el Umbral se ve desde aqui: una "
                "grieta vertical, quieta, como una puerta que nadie ha empujado.",
                fondo="camino"),
            esc("Lo que el juego nunca dijo: el Umbral no es una puerta. Es una "
                "pregunta que alguien hizo hace mucho y sigue esperando.",
                fondo="camino", color=TEXTO_ON),
            esc("- Cuando llegues al trono vas a tener que elegir.", hablante="Nara",
                fondo="camino"),
        ],
    },
    "aldea": {
        "previa": [
            esc("La aldea vive detras de un muro de piedra y dos custodios que no "
                "preguntan nada porque ya saben la respuesta.", fondo="aldea"),
            esc("Uno de los dos te mira las cartas y despues te mira a ti.",
                fondo="aldea"),
            esc("- Eso es del otro lado. Eso no se trae aqui.", fondo="aldea",
                color=TEXTO_ON),
            esc("- Cinco duelos. El ultimo es el trono. Segui, porque cada uno que "
                "ganas es un paso menos entre vos y tu salon.", hablante="Nara",
                fondo="aldea", color=TEXTO_ON),
        ],
        "posterior": [
            esc("Cuando sales, el custodio te sigue con la mirada hasta el arco. No es "
                "hostilidad: es la mirada de quien sabe que algo viene y no sabe que.",
                fondo="aldea"),
            esc("Nara espera en el camino con la libreta abierta.", hablante="Nara",
                fondo="aldea"),
            esc("- Tu mazo les dijo algo antes de que dijeras nada.", hablante="Nara",
                fondo="aldea", color=TEXTO_ON),
            esc("Y por primera vez entiendes la diferencia: no es un mazo. Es una "
                "declaracion de intenciones.", fondo="aldea"),
        ],
    },
    "ruinas": {
        "previa": [
            esc("Bajo la ceniza hay una ciudad entera. Las calles siguen donde estaban "
                "y las casas siguen teniendo techo.", fondo="ruinas"),
            esc("No hay nadie. Y sin embargo, en una pared hay un cartel: el dibujo de "
                "una carta que reconoces.", fondo="ruinas", color=TEXTO_ON),
            esc("Es una de las tuyas. Esta aqui pintada, en un mundo que no tiene nada "
                "que ver con tus sobres.", fondo="ruinas"),
        ],
        "posterior": [
            esc("Cuando sales de las ruinas, Nara no te pregunta por lo que viste. "
                "Escribe.", hablante="Nara", fondo="ruinas"),
            esc("- El Umbral no invento el mundo. Lo copio. Y lo copio mal.",
                hablante="Nara", fondo="ruinas"),
            esc("- Alguien escribio esas cartas antes de que fueran ciertas.",
                hablante="Nara", fondo="ruinas", color=TEXTO_ON),
        ],
    },
    "fortaleza": {
        "previa": [
            esc("La fortaleza domina el mapa. Quien la tiene, tiene el trono. Y el "
                "trono tiene el Umbral.", fondo="fortaleza"),
            esc("El capitan te espera en la puerta. Ya sabe lo que traes.",
                fondo="fortaleza"),
        ],
        "posterior": [
            esc("Adentro huele a hierro mojado. Aqui se decide quien se queda.",
                fondo="fortaleza"),
            esc("- Ganar no es el problema. El problema es que se abre despues.",
                hablante="Nara", fondo="fortaleza", color=TEXTO_ON),
            esc("- Estas a dos duelos de la vuelta. No aflojes ahora.",
                hablante="Nara", fondo="fortaleza", color=TEXTO_ON),
        ],
    },
    "asalto": {
        "previa": [
            esc("Vuelve. Con las mismas heridas y con la misma pregunta.", fondo="asalto",
                efecto="titulo"),
            esc("- Creiste que estaba derrotado.", fondo="asalto", color=TEXTO_ON),
            esc("- No lo estaba.", fondo="asalto", color=TEXTO_ON),
        ],
        "posterior": [
            esc("Cuando cae, no dice nada. Solo te mira las cartas una ultima vez, como "
                "si quisiera compararlas con un recuerdo.", fondo="asalto"),
            esc("- Esas cartas no son de este mundo.", hablante="Nara", fondo="asalto"),
            esc("- Lo se. Llevo dos dias sin dormir por eso.", hablante="Nara",
                fondo="asalto", color=TEXTO_ON),
            esc("- Falta uno. El ultimo. Y el ultimo te devuelve a casa.",
                hablante="Nara", fondo="asalto", color=TEXTO_ON),
        ],
    },
    "trono": {
        "previa": [
            esc("El trono esta detras de la grieta. Y la grieta detras del trono. No hay "
                "otro orden posible.", fondo="trono"),
            esc("El Umbral te ve llegar. Eso es lo peor: no es una puerta. Te estaba "
                "esperando.", fondo="trono", efecto="titulo"),
        ],
        "posterior": [
            esc("Aqui termina el camino. Y aqui se decide de quien es el mundo.",
                fondo="trono", efecto="titulo"),
            esc("- Si abres el Umbral vas a poder volver. Eso no significa que sea "
                "buena idea.", hablante="Nara", fondo="trono", color=TEXTO_ON),
        ],
    },
}


# ------------------------------------------------------------------ publico


def previa_nodo(nodo_id):
    return [dict(e) for e in NARRATIVA.get(nodo_id, {}).get("previa", [])]


def posterior_nodo(nodo_id):
    return [dict(e) for e in NARRATIVA.get(nodo_id, {}).get("posterior", [])]


def reaccion_mazo(faccion):
    """La primera linea que dice el mundo al ver tu mazo. Ligera."""
    lineas = REACCION_MAZO.get(faccion, [])
    return lineas[0] if lineas else ""


def segunda_reaccion_mazo(faccion):
    """La segunda linea: aparece si el jugador insists (reactividad ligera)."""
    lineas = REACCION_MAZO.get(faccion, [])
    return lineas[1] if len(lineas) > 1 else ""


def decision_de(nodo_id):
    return DECISION.get(nodo_id)


# ------------------------------------------------------- el momento de Nara
# La biblia pide que Nara pase de guia a amiga. NO se puede dejar en manos de
# la confianza: `confianza_nara` solo sube con las dos decisiones de la campana
# (maximo +1 y +2), asi que un jugador que elige frio en las dos se queda en 0
# y `campana.nara_aliada()` jamas daria True. El momento tiene que ocurrir
# siempre; la confianza solo cambia que tan calida es.
AMISTAD_NARA = [
    esc("Antes del ultimo duelo, Nara te espera en el borde del camino.",
        fondo="camino"),
    esc("No esta escribiendo. El libro esta cerrado.", fondo="camino"),
    esc("- Tengo que corregir una cosa. Y corregirme yo.", hablante="Nara",
        retrato="nara", fondo="camino"),
    esc("- El primer dia te dije que te acompanaba porque necesitaba respuestas.",
        hablante="Nara", retrato="nara", fondo="camino"),
    esc("- Era verdad. Y no era todo.", hablante="Nara", retrato="nara",
        fondo="camino", color=TEXTO_ON),
    esc("- Vine a averiguar quien escribio las cartas. Ese era el motivo. Y "
        "segun el motivo, vos eras un dato.", hablante="Nara", retrato="nara",
        fondo="camino"),
    esc("Nara abre el libro por la ultima vez. Esta lleno de flechas y de "
        "preguntas, y de tu nombre repetido cuantas veces pudo.",
        fondo="camino"),
    esc("- No lo encontre. Y en el camino perdi las ganas de que me importara "
        "tanto.", hablante="Nara", retrato="nara", fondo="camino", color=TEXTO_ON),
    esc("Lo cierra otra vez. Esta vez no lo vuelve a abrir.", fondo="camino"),
    esc("- Dejame acompanarte. No por el Umbral. No por las cartas.",
        hablante="Nara", retrato="nara", fondo="camino", color=TEXTO_ON),
    esc("- Porque quiero. Y no me da vergenza decirlo.", hablante="Nara",
        retrato="nara", fondo="camino"),
    esc("El camino sube hacia el trono. Por primera vez no lo camina sola.",
        fondo="camino", color=TEXTO_ON),
]


def escena_amistad():
    """Nara deja de ser una guia y pasa a ser otra cosa.

    Se reproduce antes del duelo del trono, siempre, con independencia de las
    decisiones. Es el punto 6 de la biblia: deja de dar pistas y se queda.
    """
    return [dict(e) for e in AMISTAD_NARA]


def nara_linea(momento, confianza):
    """Dialogo de Nara segun confianza. `momento` in presentacion/umbral/..."""
    fn = {
        "presentacion": nara_presentacion,
        "umbral": nara_umbral,
        "victoria": nara_victoria,
        "derrota": nara_derrota,
    }.get(momento)
    return fn(confianza) if fn else ""
