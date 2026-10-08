"""Compendio dual: lo que dice la carta y lo que realmente paso.

Idea de la biblia
-----------------
Cada una de las 250 cartas tiene DOS descripciones:

    la version del juego   "Kragh, Carnicero de Erdan. Senor orco responsable
                            de la Masculata de Erdan."   <- la mentira

    lo que descubriste     "Kragh llego a Erdan despues del ataque. Sus
                            hombres evacuaron a cientos de civiles."  <- la verdad

Eso convierte la coleccion en 250 historias por descubrir: el progreso deja de
ser "247/250 cartas" y pasa a ser "247/250 historias descubiertas".

Como esta construido
--------------------
Las 250 entradas se generan de las cartas REALES que ya estan en `mazos`
(25 por faccion, 10 facciones = 250), asi que el compendio nunca se
desincroniza del pool jugable: si cambia una carta, cambia su entrada.

La verdad de cada carta no se inventa carta por carta: sale de la faccion y de
la rareza. Es verdad narrativa, no historica: lo que el mundo real habria
contado de esa carta. Cada faccion tiene su propiobia de mentira (de la tabla
de la biblia) y hay revelationes sueltas para las cartas con nombre.

Texto visible en ASCII, como todo el juego. Este modulo no importa campana.
"""

import mazos
from reglas import rareza

# ------------------------------------------------------- las diez mentiras
# De la tabla de la biblia: que aspecto de la mentira descubre cada faccion.

MENTIRA_FACCION = {
    "humano": {
        "tema": "La historia escrita por los vencedores",
        "juego": "El relato oficial: los humanos salvan el mundo.",
        "verdad": "Los humanos escribieron el relato despues de ganar. Lo que "
                  "cuentan es lo que les convenia, no lo que paso.",
        "revelacion": "comp_humano_ganadores",
    },
    "orco": {
        "tema": "Barbarie frente a supervivencia",
        "juego": "Salvajes que revientan_aldeas por diversion.",
        "verdad": "Los orcos fueron empujados a la frontera y reconditionan. "
                  "Lo que llaman massacre suele ser una retirada.",
        "revelacion": "comp_orco_barbarie",
    },
    "elfo": {
        "tema": "Tradicion llevada al extremo",
        "juego": "Arrogantes que cuidan un bosque que les importa poco.",
        "verdad": "Los elfos guardan un conocimiento que nadie quiere oir, y "
                  "pagan porarlo con aislamiento.",
        "revelacion": "comp_elfo_tradicion",
    },
    "goblin": {
        "tema": "Explotacion y prejuicios",
        "juego": "Monstruos_GRATIS para todos. Debiles por naturaleza.",
        "verdad": "Los goblins fueron los primeros habitantes. Nadie los "
                  "escucho y a todos les toca pagar.",
        "revelacion": "comp_goblin_prejuicio",
    },
    "hombre_lobo": {
        "tema": "Identidad y control",
        "juego": "Bestias con forma de hombre. Peligro por instinto.",
        "verdad": "Son personas que luchan contra algo que no eligieron. La "
                  "bestia no es la que muerde: es la que tiene miedo.",
        "revelacion": "comp_lobo_control",
    },
    "vampiro": {
        "tema": "Inmortalidad y decadencia",
        "juego": "Depredadores que beben sangre y no duermen.",
        "verdad": "Son los que recuerdan todo. Y recordar todo los destruye "
                  "mas rapido que el hambre.",
        "revelacion": "comp_vampiro_memoria",
    },
    "dragon": {
        "tema": "Poder y aislamiento",
        "juego": "Destructores que queman por diversion.",
        "verdad": "Saben mas que nadie y no pueden contarlo: si se acercan, "
                  "el resto les tiene miedo y no se quedan.",
        "revelacion": "comp_dragon_soledad",
    },
    "elfo_nocturno": {
        "tema": "Exilio y resentimiento",
        "juego": "Traidores arrojados del bosque.",
        "verdad": "Fueron exiliados por preguntar demasiado, no por traicion. "
                  "El exilio los volvio asi. No al reves.",
        "revelacion": "comp_nocturno_exilio",
    },
    "hombre_pantera": {
        "tema": "Honor frente a libertad",
        "juego": "Salvajes que cazan de noche y no aceptan leyes.",
        "verdad": "Son los que tuvieron que elegir entre dos males. Nadie que "
                  "eligio bien puede parecer libre.",
        "revelacion": "comp_pantera_eleccion",
    },
    "hombre_lagarto": {
        "tema": "Memoria ancestral y verdad",
        "juego": "Primitivos del pantano. Casi no hablan.",
        "verdad": "Guardan la verdad mas antigua que existe. Y la esconden "
                  "porque a nadie le conviene que se sepa.",
        "revelacion": "comp_lagarto_memoria",
    },
}

# -------------------------------------------------- revelationes con nombre
# Las cartas con nombre propio son las que el duelista puede encontrar en el
# mundo: un rey, un ejecutor, alguien que sigue vivo. Estas tienen una verdad
# concreta que se cuenta, no solo la verdad general de la faccion.

VERDADES_NOMBRADAS = {
    # humanos
    "Rey Aldric": "No fundo el reino: lo heredo destrozado. La carta lo llama "
                 "salvador porque el que escribe elige los adjetivos.",
    "Reina Isolde": "Firmo la paz que la dejo sola en un trono. El juego la "
                    "llama soberana. Era una prisionera con corona.",
    # orcos
    "Senor de la Guerra Vorg": "Gano la guerra que le negaron. Cuando se "
                              "leizo la ciudad, perdio dos hijos. El juego no "
                              "lo menciona.",
    # goblins
    "Rey Goblin": "Rey de un foso que nadie le ofrecio. El juego dice que "
                  "robo un trono. Nadie se lo dio: se lo dio el hambre.",
    # elfos
    "Elfo Real": "No pedio un reino: pidio que no se quemara el bosque. El "
                 "juego lo llama heredero. Nadie le agradecio no hacer nada.",
    # dragones
    "Rey Dragon": "Rey Oscuro, si. Pero antes fue el que hacia de puente entre "
                  "dos pueblos. Se quedaron sin poder hablar y le quedo la pena.",
    # vampiros
    "Conde Nocturno": "No robo la noche: la heredo. El juego lo llama ladron "
                      "de sangre. Lleva cuatrocientos anos sin dormir.",
    # hombres lobo
    "Alfa del Bosque": "Alfa por fuerza, no por nacimiento. El juego lo llama "
                       "rey de la manada. La manada todavia no lo sabe.",
    # pantera
    "Cazadora Silente": "Cazadora porque nadie le dejo otra cosa. El juego la "
                        "llama salvaje. Le gusta: le queda mejor que verdad.",
    # lagarto
    "Senor del Pantano": "Espera porque sabe. El juego lo llama eso mismo. "
                         "Nunca tuvo nombre: se lo puso quien lo vio primero.",
    # elfos nocturnos
    "Reina de la Noche": "No traiciono a nadie: pregunto una vez de mas. La "
                         "expulsaron por eso y el juego lo llamo traicion.",
}

# Cartas cuyo nombre tiene una verdad propia y verificada arriba.
def _tiene_verdad(nombre):
    return nombre in VERDADES_NOMBRADAS


def _verdad_de(carta):
    """La verdad de una carta concreta.

    Dos capas: la verdad propia si la carta tiene nombre (reyes, ejecutores,
    alguien que sigue vivo) y, si no, la de su faccion. El matiz de rareza se
    anade siempre, para que dentro de un bando no sean todas iguales.
    """
    faccion = MENTIRA_FACCION.get(carta.bando)
    if _tiene_verdad(carta.nombre):
        base = VERDADES_NOMBRADAS[carta.nombre]
    elif faccion:
        base = faccion["verdad"]
    else:
        base = "Nadie sabe que dice realmente esta carta."
    etiqueta = rareza(carta)[0]
    if etiqueta == "LEGENDARIA":
        return base + " Esta en particular pesa mas que las demas."
    if etiqueta == "RARA":
        return base + " Su historia todavia esta a medio contarse."
    return base


def _juego_de(carta):
    """Lo que dice el juego: su nombre, su faccion y la version oficial."""
    faccion = MENTIRA_FACCION.get(carta.bando)
    oficial = faccion["juego"] if faccion else "Historia sin escribir."
    return f"{carta.nombre}. {oficial}"


# ----------------------------------------------------------------- el indice
# Se construye una sola vez a partir de mazos: 250 entradas garantizadas.


def _construir():
    entradas = {}
    for bando, lista in mazos.TODOS.items():
        for carta in lista:
            entradas[carta.nombre] = {
                "nombre": carta.nombre,
                "faccion": carta.bando,
                "rareza": rareza(carta)[0],
                "juego": _juego_de(carta),
                "verdad": _verdad_de(carta),
                "revelacion": MENTIRA_FACCION.get(bando, {}).get("revelacion", ""),
                "verdad_nombrada": _tiene_verdad(carta.nombre),
            }
    return entradas


ENTRADAS = _construir()


# ------------------------------------------------------------------ publico


def entrada(nombre_carta):
    """Entrada del compendio de una carta, o None si no existe."""
    return ENTRADAS.get(nombre_carta)


def nombres():
    return list(ENTRADAS)


def por_faccion(bando):
    return [e for e in ENTRADAS.values() if e["faccion"] == bando]


def total():
    return len(ENTRADAS)


def revelacion_de(bando):
    """Fragmento de verdad que aporta la faccion en el NG+."""
    return MENTIRA_FACCION.get(bando, {}).get("revelacion", "")


def tema_de(bando):
    return MENTIRA_FACCION.get(bando, {}).get("tema", "")


def version_juego(nombre_carta):
    e = entrada(nombre_carta)
    return e["juego"] if e else ""


def version_verdad(nombre_carta):
    e = entrada(nombre_carta)
    return e["verdad"] if e else ""


def revelada(estado, nombre_carta):
    """Ya descubriste la verdad de esta carta en esta partida?"""
    return nombre_carta in (estado.get("compendio") or [])


def revelar(estado, nombre_carta):
    """Revela la verdad de una carta. Devuelve la entrada, o None."""
    e = entrada(nombre_carta)
    if not e:
        return None
    visto = estado.setdefault("compendio", [])
    if nombre_carta not in visto:
        visto.append(nombre_carta)
    return e


def descubiertas(estado):
    """Cuantas historias ha descubierto el jugador en esta partida."""
    return len(estado.get("compendio") or [])


def progreso(estado):
    """(descubiertas, total) para la pantalla de coleccion."""
    return descubiertas(estado), total()


def_LINEA = " ----------------------------------------------------------------------"
