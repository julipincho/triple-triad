"""Prologo de "Cartones y Mazmorras": el mundo real, el Umbral y el despertar.

El prologo es el pegamento que faltaba entre el juego de cartas de nuestro
mundo y la campana fantastic. Va antes de elegir faccion (ver la cronologia
de la biblia): PROLOGO_MUNDO_REAL -> DESPERTAR -> APERTURA_FACCION -> CAPITULOS.

Estructura de escenas (mismo formato que cinematicas.esc, para poder pasarlas
tal cual al reproductor):

    PROLOGO = {
        "musica": "musica_torneo",
        "escenas": [esc(...), ...],
    }

Reglas de diseno del prologo (de la biblia):
  - El protagonista no tiene nombre. Es "el duelista": el jugador se
    identifica con el. Nunca se lo nombra.
  - El tutorial ES una partida. No se anuncia como tutorial: la mecanica se
    explica mientras se juega.
  - El humor meta es constante: el duelista comenta el mundo como si fuera
    su juego. Funciona en todas las escenas, no solo en los momentos comicos.
  - Las 5 cartas del tutorial son las mas fuertes del juego y solo existen en
    el mundo real. Al llegar al mundo fantastic el mazo es deliberately debil.
"""

import mazos
from cinematicas import MUNDO_REAL as REAL, esc
from reglas import rareza, total_carta
from ui import DORADO, TEXTO_ON

# ------------------------------------------------------------------ musica
# El mundo real tiene que sonar distinto al fantastic: el prologo arranca con
# musica de exploracion (el tournaments es el que ya existe) y cambia a musica
# de faccion cuando ya estamos dentro del juego.
MUSICA_MUNDO_REAL = "musica_explora"


# ------------------------------------------------------- las 5 legendarias
# El duelista lleva su mejor herramienta a un torneo de este nivel: una
# legendaria de cada una de las cinco facciones que usa. Son las cartas mas
# fuertes del juego completo y solo existen aqui.
#
# Nota de diseno: el mazo del mundo fantastic NO usa estas cartas. Ahi el
# jugador arranca con mazo_inicial(), que es deliberadamente mas debil. Ese
# contraste es el que hace que el duelista deje de ser invencible al cruzar.

#: faction -> nombre de su legendaria mas fuerte (la de mayor suma de lados).
TUTORIAL_FACCIONES = ("humano", "elfo", "vampiro", "dragon", "goblin")


def _pool_de(bando):
    return getattr(mazos, {
        "humano": "HUMANOS",
        "elfo": "ELFOS",
        "vampiro": "VAMPIROS",
        "dragon": "DRAGONES",
        "goblin": "GOBLINS",
    }[bando])


def mejor_legendaria(bando):
    """La legendaria mas fuerte de esa faccion (mayor suma de lados).

    Empate se resuelve por nombre para que sea estable entre partidas.
    """
    from reglas import total_carta
    candidatas = [c for c in _pool_de(bando) if rareza(c)[0] == "LEGENDARIA"]
    if not candidatas:
        candidatas = list(_pool_de(bando))
    return max(candidatas, key=lambda c: (total_carta(c), c.nombre))


def mazo_tutorial():
    """Las 5 legendarias del prologo, en orden estable de faccion."""
    return [mejor_legendaria(bando).copia() for bando in TUTORIAL_FACCIONES]


def mazo_tutorial_datos():
    return [c.a_dict() for c in mazo_tutorial()]


# ------------------------------------------------------ duelista: Juan Rajoy
# Un oponente real del torneo. No es un jefe: es el rival de la ronda
# clasificatoria, y por lo tanto el que ensena las mecanicas sin que el
# juego tenga que anunciarlo.

JUAN_RAJOY = {
    "nombre": "Juan Rajoy",
    "titulo": "Amante de Cartones y Mazmorras",
    "bando": "humano",
    "entrada": "Bueno, pues vamos a ello.",
    "captura_player": "Ay, esta partida... esta partida.",
    "captura_cpu": "Toma, toma. Que no se te escape.",
    "win": "Enhorabuena, crack.",
    "lose": "Has ganado tu. Mala sombra me has dejado.",
}

# Frases del duelista durante el tutorial. Se intercalan con las mecanicas:
# el jugador nunca lee "esto es un tutorial", lee a alguien que sabe jugar.
TUTORIAL_FRASES = {
    "same": "Same. Dos iguales se anulan. Lo basico.",
    "plus": "Plus. A la derecha del contrario y no te tocan.",
    "capturas": "Y la tuya cae si miro el flanco debil.",
    "cadena": "Cadena: una cae y la vecina cae con ella.",
    "habilidad": "Ojo con la habilidad. Esta se cura sola.",
    "centro": "El centro manda. Todo lo demas es decorado.",
}


# ------------------------------------------------------------------ escenas
def _escenas_del_duelo():
    """El tutorial no se anuncia: se juega. Estas escenas son el ambiente."""
    return [
        esc("El salon esta lleno: mesas, banners, cronometros y gente que no levanta la vista.",
            fondo="campamento", mundo=REAL),
        esc("ULTIMA RONDA CLASIFICATORIA", fondo="campamento", efecto="titulo", mundo=REAL),
        esc("Presentador", hablante="Presentador", fondo="campamento", mundo=REAL),
        esc("- Ultima ronda clasificatoria.", hablante="Presentador", fondo="campamento", mundo=REAL),
        esc("- Los ocho mejores jugadores avanzaran a la Copa del Trono.",
            hablante="Presentador", fondo="campamento", mundo=REAL),
        esc("Tu nombre no importa aqui. Solo tu mazo.", fondo="campamento", mundo=REAL),
        esc("Sacas tus cartas: cinco legendarias, una de cada faccion. Lo mejor que tienes.",
            fondo="campamento", color=TEXTO_ON, mundo=REAL),
        esc("No es una partida de prueba. Es una clasificatoria. Y el rival frente a ti se "
            "llama...", fondo="campamento", mundo=REAL),
    ]


def _escenas_post_duelo():
    return [
        esc("- Otra vez esa maldita combinacion.", hablante="Juan Rajoy",
            fondo="campamento", mundo=REAL, retrato="rajoy"),
        esc("- Te avise que dejaras libre el centro.", fondo="campamento", mundo=REAL),
        esc("Juan te mira el mazo otra vez. Esta vez con respeto.",
            hablante="Juan Rajoy", fondo="campamento", mundo=REAL, retrato="rajoy"),
        esc("- Buena partida, crack.", hablante="Juan Rajoy", fondo="campamento",
            retrato="rajoy", mundo=REAL),
        esc("Cumpliste. Ahora van a presentar la carta que trajeron.", fondo="campamento", mundo=REAL),
    ]


def _escenas_carta_umbral():
    """La carta que no pertenece a ninguna faccion. Y el apagon."""
    return [
        esc("Los organizadores suben al escenario con una caja que nadie ha visto antes.",
            fondo="campamento", mundo=REAL),
        esc("- Una carta que no tiene faccion. Ni bando. Ni edicion.",
            hablante="Presentador", fondo="campamento", mundo=REAL),
        esc("EL UMBRAL", fondo="umbral", efecto="titulo", mundo=REAL),
        esc("Una puerta enorme. Y detras... un trono vacio.", fondo="umbral", mundo=REAL),
        esc("La reconoces. Los simbolos de los bordes salen en las cartas mas antiguas.",
            fondo="umbral", color=TEXTO_ON, mundo=REAL),
        esc("Esas cartas las viste cientos de veces. Nunca las entendiste del todo.",
            fondo="umbral", color=TEXTO_ON, mundo=REAL),
        esc("Las nueve casillas del tablero empiezan a iluminarse.",
            fondo="umbral", efecto="titulo", mundo=REAL),
        esc("La carta central cambia. Y durante un segundo aparece algo que no",
            fondo="umbral", mundo=REAL),
        esc("deberia existir en ninguna edicion: una decima faccion. O una figura",
            fondo="umbral", mundo=REAL),
        esc("sentada en el trono. Solo un segundo.", fondo="umbral", color=TEXTO_ON, mundo=REAL),
    ]


def _escenas_transporte():
    return [
        esc("La luz se apaga.", fondo="umbral", efecto="titulo"),
        esc("Y cuando vuelve, ya no estas en el salon.", fondo="umbral"),
        esc("", fondo="umbral", efecto="titulo"),
    ]


def _escenas_despertar():
    """El mundo fantastic. Y el primer personaje real: un goblin."""
    return [
        esc("Bosque. Lluvia. Barro hasta los tobillos.", fondo="camino"),
        esc("Tu mochila esta tirada. Tu telefono no tiene senal.", fondo="camino"),
        esc("Pero las cartas siguen ahi. Las cinco legendarias.",
            fondo="camino", color=TEXTO_ON),
        esc("Y es lo primero que notas: una torre.", fondo="camino"),
        esc("La conoces. Esta en el fondo de una carta que viste mil veces.",
            fondo="camino", color=TEXTO_ON),
        esc("- No puede ser.", fondo="camino", color=DORADO),
        esc("Te das vuelta. Y ahi esta.", fondo="camino"),
        esc("Pik", hablante=None, fondo="camino"),
        esc("Un goblin. No una ilustracion. No alguien vestido de goblin.",
            fondo="camino"),
        esc("Pik", hablante="Pik", retrato="pik", fondo="camino"),
        esc("- No deberias tener eso.", hablante="Pik", retrato="pik",
            fondo="camino"),
        esc("Lo dice senalando tus cartas. Y no parece una broma.", fondo="camino"),
    ]


def _escenas_encuentro_hostil():
    """Antes de Nara: alguien te ve con cartas imposibles y no le gusta."""
    return [
        esc("El goblin se va. Tu decides seguir. El bosque no es sitio para quedarse.",
            fondo="camino"),
        esc("Das diez pasos. Y alguien mas tambien te ve.", fondo="camino"),
        esc("No es un goblin. Es de la aldea.", fondo="camino"),
        esc("- De donde sacas esas cartas?", fondo="camino"),
        esc("No es una pregunta. Es una amenaza.", fondo="camino", color=TEXTO_ON),
        esc("Tienes una decision: mostrar las cartas, o no mostrarlas.",
            fondo="camino", color=DORADO),
        esc("Lo que sea que elijas, ya no puedes deshacerlo: las viste. El te vio.",
            fondo="camino"),
    ]


def _escenas_nara():
    """Nara, la Cronista: el otro personaje que entra en juego."""
    return [
        esc("Cuando logras salir, hay alguien esperandote.", fondo="campamento"),
        esc("Una mujer con una libreta abierta y tinta en los dedos.", fondo="campamento"),
        esc("- Ustedes juegan Cartones y Mazmorras?", fondo="campamento"),
        esc("Lo sueltas antes de pensarlo. Es lo unico que sale.", fondo="campamento",
            color=TEXTO_ON),
        esc("- No se que son esos cartones.", hablante="Nara", retrato="nara", fondo="campamento"),
        esc("- Aqui esto se llama Juicio.", hablante="Nara", retrato="nara", fondo="campamento"),
        esc("Mira tus cinco legendarias con los ojos muy abiertos.", hablante="Nara",
            retrato="nara", fondo="campamento"),
        esc("- Eso no son cartas de aqui. Esas cartas son de otro lado.",
            hablante="Nara", fondo="campamento"),
        esc("Y entonces hace la pregunta que lo cambia todo:", hablante="Nara",
            fondo="campamento"),
        esc("- De donde las sacaste?", hablante="Nara", fondo="campamento",
            color=TEXTO_ON),
        esc("Y por primera vez, las cartas pesan mas que el carbon de tu mazo.",
            fondo="campamento"),
    ]


def _escenas_cierre():
    """Cierra el prologo y pasa el turno a la eleccion de faccion."""
    return [
        esc("A partir de aqui ya no sos un invitado.", fondo="umbral"),
        esc("A partir de aqui sos alguien que sabe demasiado.", fondo="umbral",
            color=TEXTO_ON),
        esc("ELIGE TU MAZO PRINCIPAL", fondo="trono", efecto="titulo"),
        esc("No es quien eres. Es el mazo que juegas. Y el mundo lo va a leer.",
            fondo="trono"),
    ]


# ------------------------------------------------------------------ publico


def escenas_pre_duelo():
    """Antes del tutorial. Se reproducen antes de arrancar la partida."""
    return [dict(e) for e in _escenas_del_duelo()]


def escenas_post_duelo():
    """Despues de ganar. Cerran el tutorial con el dialogo de Juan."""
    return [dict(e) for e in _escenas_post_duelo()]


def escenas_carta_umbral():
    return [dict(e) for e in _escenas_carta_umbral()]


def escenas_transporte():
    return [dict(e) for e in _escenas_transporte()]


def escenas_despertar():
    return [dict(e) for e in _escenas_despertar()]


def escenas_encuentro_hostil():
    return [dict(e) for e in _escenas_encuentro_hostil()]


def escenas_nara():
    return [dict(e) for e in _escenas_nara()]


def escenas_cierre():
    return [dict(e) for e in _escenas_cierre()]


def mazo_rival_rajoy():
    """Mazo de Juan: 5 cartas, sin legendarias.

    En un 3x3 cada bando coloca 5 cartas, asi que la mano de Juan debe tener
    5 tambien (igual que `campana.cartas_duelo`). Tomas las comunes mas
    fuertes de su faccion: si tuviera una legendaria el duelo seria un paseo
    y no ensenaria las mecanicas.
    """
    comunes = [c for c in mazos.HUMANOS if rareza(c)[0] != "LEGENDARIA"]
    elegidas = sorted(comunes, key=lambda c: (-total_carta(c), c.nombre))[:5]
    return [c.copia() for c in elegidas]


def rival_rajoy():
    """Datos del duelista para la pantalla de duelo."""
    return dict(JUAN_RAJOY)


def info_duelo_prologo():
    """Bloque `info` con la forma que espera `partida.Juego`.

    El tutorial no es un nodo de campana: no tiene ruta, ni escala, ni
    recompensas. Solo necesita los campos que la UI lee para mostrar el
    nombre del rival, su faccion y la linea de entrada.
    """
    r = rival_rajoy()
    return {
        "nodo": "prologo",
        "titulo": "ULTIMA RONDA CLASIFICATORIA",
        "escena": "campamento",
        "previa": [],
        "tipo": "tutorial",
        "dificultad": 0,
        "bando": r["bando"],
        "nombre_faccion": "Humanos",
        "nombre": r["nombre"],
        "titulo_duelo": r["titulo"],
        "entrada": r["entrada"],
        "captura_player": r["captura_player"],
        "captura_cpu": r["captura_cpu"],
        "win": r["win"],
        "lose": r["lose"],
    }
