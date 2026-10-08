"""Fragmentos de la Verdad y la campana secreta.

La idea de la biblia
--------------------
No conviene contar todo en la primera campana. La primera vez que se termina
Cartones y Mazmorras hay que entender COMO volver a casa, pero no quien
escribio las cartas ni por que los dos mundos estan unidos.

Cada faccion jugada en el NG+ aporta un fragmento. Diez facciones, diez
fragmentos. Al llegar a 10/10 se desbloquea algo que nunca estuvo en las 250
cartas: **El Cartografo**, el que las escribio.

Cada fragmento tiene:
  - id        : identificador estable (se guarda en el perfil)
  - faccion   : que faccion lo aporta
  - quien     : quien te lo cuenta (siempre Nara u otro del mundo)
  - texto     : la linea que revela la pieza que faltaba

Los fragmentos NO se muestran todos de golpe: cada uno completa la respuesta a
una pregunta distinta del misterio central. Juntos apuntan a El Cartografo.

Este modulo no importa campana: lo usa, no al reves.
"""

import facciones

# ------------------------------------------------------------- los 10 fragmentos
# Cada faccion responde una pregunta distinta. Juntos forman la respuesta
# completa: las cartas no son del pasado ni del futuro, son de las dos.


FRAGMENTOS = {
    "humano": {
        "id": "frag_humano",
        "pregunta": "Quien escribio la version oficial?",
        "quien": "Nara",
        "texto": "Los humanos no inventaron la mentira. La conservaron, porque "
                 "les convenia. Alguien se lo entrego ya escrita.",
    },
    "orco": {
        "id": "frag_orco",
        "pregunta": "Por que el juego llama barbarie a una retirada?",
        "quien": "Nara",
        "texto": "Los orcos aparecen en las cartas siempre ganando. Nunca "
                 "huyendo. Alguien decidio que esa era su historia y la "
                 "imprimio doscientas veces.",
    },
    "elfo": {
        "id": "frag_elfo",
        "pregunta": "Que mira un elfo al Umbral?",
        "quien": "Nara",
        "texto": "Los elfos fueron los primeros en ver la grieta. Escribieron "
                 "para avisar y alguien les respondio con una guerra.",
    },
    "goblin": {
        "id": "frag_goblin",
        "pregunta": "Quien decidio que los goblins son monstruos?",
        "quien": "Nara",
        "texto": "Los goblins son la faccion mas repetida en las cartas y la "
                 "que menos aparece en los libros de aqui. Eso no se hace "
                 "por error: se hace a proposito.",
    },
    "hombre_lobo": {
        "id": "frag_lobo",
        "pregunta": "La luna, es leyenda o es un metodo?",
        "quien": "Nara",
        "texto": "La luna no hace nada. Lo que hay son los turnos de la manada, "
                 "y estan escritos. Alguien decidio cuando cambia.",
    },
    "vampiro": {
        "id": "frag_vampiro",
        "pregunta": "Por que los vampiros son los que mas recuerdan?",
        "quien": "Nara",
        "texto": "Porque son los unicos que vivieron lo suficiente para "
                 "comparar. Si el juego dice cosas que aun no pasaron, ellos "
                 "son los primeros en notarlo.",
    },
    "dragon": {
        "id": "frag_dragon",
        "pregunta": "Por que los dragones no hablan con nadie?",
        "quien": "Nara",
        "texto": "Porque si dijeran lo que saben, el Umbral dejaria de "
                 "funcionar. Cada rey dragon que hablo fue reemplazado.",
    },
    "elfo_nocturno": {
        "id": "frag_nocturno",
        "pregunta": "Por que los nocturnos fueron exiliados?",
        "quien": "Nara",
        "texto": "No fueron exiliados por mirar el Umbral. Fueron exiliados "
                 "porque lei el codigo fuente de las cartas. De eso no se "
                 "vuelve.",
    },
    "hombre_pantera": {
        "id": "frag_pantera",
        "pregunta": "Quien escribe cuando dos bandos se contradicen?",
        "quien": "Nara",
        "texto": "Alguien tiene que decidir cual version gana. Ese alguien no "
                 "es de ninguna faccion, y por eso ninguna lo reclama.",
    },
    "hombre_lagarto": {
        "id": "frag_lagarto",
        "pregunta": "Cual es la verdad mas antigua?",
        "quien": "Nara",
        "texto": "Los lagartos recuerdan el momento en que el Umbral se abrio "
                 "por primera vez. No lo hizo un rey: lo hizo un escritor.",
    },
}

# El orden en que conviene investigar: el del NG+, no el alfabetico.
ORDEN_FRAGMENTOS = (
    "goblin", "orco", "humano", "elfo", "hombre_lobo",
    "vampiro", "dragon", "hombre_pantera", "elfo_nocturno", "hombre_lagarto",
)

#: La pregunta que responde cada fragmento, en el orden en que se va encendiendo.
PREGUNTAS = [FRAGMENTOS[f]["pregunta"] for f in ORDEN_FRAGMENTOS]


# ------------------------------------------------------ la campana secreta
# No es contra una faccion. Es contra alguien que no figura en las 250 cartas.

CARTOGRAFO = {
    "id": "cartografo",
    "nombre": "El Maestro de la Mesa",
    "titulo": "El Que Escribio Las Cartas",
    "rol": "cartografo",
    # No tiene faccion: por eso no puede ser rival de ninguna escalera.
    "faccion": None,
    "personalidad": "paciente, antiguo, sin nada que ocultar",
    "motivacion": "No quiere que el Umbral se cierre. Quiere que se termine "
                  "de leer.",
    "historia": "Sus simbolos aparecen en todas las ediciones antiguas del "
                "juego. El duelista no llego al mundo real por azar: fue "
                "seleccionado.",
    "dialogo": {
        "pre": [
            "- Por fin. Me costo mucho traerte.",
            "- No, no soy de aqui. Y ese es justamente el problema.",
            "- Escribi el juego. Todo. Las 250 cartas y la que no esta ahi.",
            "- Vos las viste todas. Y no entendiste ninguna. Eso era lo que "
            "hacia falta.",
        ],
        "win": [
            "- Ganaste. Bien. Ahora entiendes lo que hiciste.",
            "- Las cartas nunca contaron el pasado. Contaron lo que iba a "
            "pasar. Y vos las leiste como si ya hubiera pasado.",
            "- Volve a tu mundo. Y mira bien la carta que no tenias.",
        ],
        "lose": [
            "- No pasa nada. El que tiene que escribir el final sos vos.",
            "- Yo solo escribi el principio. El resto lo escriben las cartas.",
        ],
    },
    "reaccion": {
        "humano": "- Un humano. Escribi muchas de las tuyas. No te caigo bien.",
        "orco": "- Un orco. Tu carta fue la primera que me costo hacer.",
        "elfo": "- Un elfo. Lei lo que escribieron de ti. Seguro me equivoque.",
        "goblin": "- Un goblin. Eras el mas facil de escribir. Por eso te elegi.",
        "hombre_lobo": "- Un lobo. La luna la escribi yo. Lo siento.",
        "vampiro": "- Un vampiro. Dejaste de ser el mas viejo de las cartas.",
        "dragon": "- Un dragon. Tu historia la cerre porque se hacia larga.",
        "elfo_nocturno": "- Un nocturno. Eres el que casi me descubre.",
        "hombre_pantera": "- Una pantera. Escribi las dos versiones y las dos "
                          "son malas.",
        "hombre_lagarto": "- Un lagarto. Te escribiste antes de que existieras.",
    },
}

#: Que hace falta para que aparezca el Cartografo.
FRAGMENTOS_NECESARIOS = len(FRAGMENTOS)


# ------------------------------------------------------------------ publico


def fragmento(faccion):
    return FRAGMENTOS.get(faccion)


def ids_fragmentos():
    return [FRAGMENTOS[f]["id"] for f in ORDEN_FRAGMENTOS]


def fragmentos_de(obtenidos):
    """Los fragmentos ya descubiertos, en el orden en que conviene verlos."""
    if isinstance(obtenidos, dict):
        obtenidos = set(obtenidos)
    else:
        obtenidos = set(obtenidos or [])
    return [FRAGMENTOS[f] for f in ORDEN_FRAGMENTOS
            if FRAGMENTOS[f]["id"] in obtenidos]


def progreso_fragmentos(obtenidos):
    """(n, total). `obtenidos` es la lista de ids ya encontrados."""
    total = len(FRAGMENTOS)
    n = len(fragmentos_de(obtenidos))
    return n, total


def falta_para_el_cartografo(obtenidos):
    """Cuantos fragmentos faltan para desbloquear la campana secreta."""
    _, total = progreso_fragmentos(obtenidos)
    faltan = total - len(fragmentos_de(obtenidos))
    return max(0, faltan)


def secreto_desbloqueado(obtenidos):
    """Con 10/10 fragmentos aparece el que escribio las cartas."""
    return len(fragmentos_de(obtenidos)) >= FRAGMENTOS_NECESARIOS


def escena_desbloqueo(obtenidos):
    """La escena que se juega al conseguir el ultimo fragmento."""
    from ui import TEXTO_ON

    def esc(linea, hablante=None, fondo="umbral", efecto="dialogo", color=None):
        return {"texto": linea, "hablante": hablante, "fondo": fondo,
                "retrato": None, "efecto": efecto, "musica": None, "color": color}

    if secreto_desbloqueado(obtenidos):
        return [
            esc("El Umbral se abre solo. Nadie lo toco.", fondo="umbral"),
            esc("Al otro lado hay alguien esperando. Hace mucho que espera.",
                fondo="umbral"),
            esc(CARTOGRAFO["nombre"], fondo="umbral", efecto="titulo"),
            esc("- Por fin. Me costo mucho traerte.", hablante="El Maestro de la Mesa",
                fondo="umbral", color=TEXTO_ON),
            esc("Y de las 250 cartas, ninguna era suya.", fondo="umbral"),
        ]
    faltan = falta_para_el_cartografo(obtenidos)
    return [
        esc("El Umbral se abre un instante. Y algo mas responde desde el otro lado.",
            fondo="umbral"),
        esc(f"Faltan {faltan} fragmentos para ver quien es.", fondo="umbral"),
    ]


def dialogo_cartografo(momento):
    return list(CARTOGRAFO["dialogo"].get(momento, []))


def reaccion_cartografo(faccion_jugador):
    return CARTOGRAFO["reaccion"].get(faccion_jugador, "")


def es_cartografo(nombre):
    """El Cartografo no pertenece a ninguna faccion: no esta en las 250."""
    return nombre == CARTOGRAFO["nombre"]


def fuera_de_las_cartas():
    """Nombre que nunca figuras entre las 250 cartas. Para el test del NG+."""
    nombres_de_cartas = set()
    try:
        import mazos
        for lista in mazos.TODOS.values():
            nombres_de_cartas.update(c.nombre for c in lista)
    except Exception:  # noqa: BLE001 - si falla mazos, el chequeo sigue
        pass
    return CARTOGRAFO["nombre"] not in nombres_de_cartas


def _validar():
    """Coherencia interna del modulo. La usan los tests."""
    errores = []
    for f in facciones.orden_facciones():
        if f not in FRAGMENTOS:
            errores.append(f"faccion sin fragmento: {f}")
    if set(ORDEN_FRAGMENTOS) != set(FRAGMENTOS):
        errores.append("ORDEN_FRAGMENTOS no cubre todas las facciones")
    if len(set(ORDEN_FRAGMENTOS)) != len(ORDEN_FRAGMENTOS):
        errores.append("ORDEN_FRAGMENTOS tiene facciones repetidas")
    ids = [FRAGMENTOS[f]["id"] for f in ORDEN_FRAGMENTOS]
    if len(set(ids)) != len(ids):
        errores.append("hay ids de fragmento repetidos")
    preguntas = [FRAGMENTOS[f]["pregunta"] for f in ORDEN_FRAGMENTOS]
    if len(set(preguntas)) != len(preguntas):
        errores.append("hay preguntas repetidas: dos fragmentos responden lo mismo")
    return errores
