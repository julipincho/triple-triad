"""Lo que cada faccion PIDE del trono, y POR QUE te ayuda.

Por que existe
--------------
La cinematica de apertura de cada bando decia que le paso a la faccion y que
significa jugar con ese mazo, pero no contestaba las dos preguntas que el
jugador se hace en ese momento:

    - que quieren del trono?
    - y por que a MI me van a ayudar?

Sin eso el dialogo queda colgado: el bando te habla de vos y de las cartas,
pero nunca del pacto que te esta ofreciendo. Estas dos lineas se agregan al
final de cada apertura, con la voz que ya estaba hablando.

Estan en primera persona a proposito: las dice el bando, no un narrador.

No cambia el grafo, ni los rivales, ni el jefe: esto es solo la explicacion de
que pacta el jugador al elegir. La justificacion del Umbral y del regreso a
casa sigue siendo la del prologo (que lo guarda quien ocupe el trono) y es
comun a las diez.

Texto visible en ASCII, como todo el juego.
"""

#: clave -> (que pide la faccion, por que te ayuda a vos)
PETICION = {
    "humano": (
        "Queremos que el Umbral quede vigilado: que nadie baje mas al "        "mundo de los juegos, y que nadie salga de el.",
        "Te ayudamos porque llegaste con cartas que no son de aca. "        "Nadie te puede usar mejor que nosotros."),

    "orco": (
        "Queremos un lugar en el mundo que nos negaron otra vez. No un "        "trono para tapar una cosa: un sitio en la mesa.",
        "Te ayudamos porque peleas bien y porque no rubs nada. Un orco "        "prefiere a alguien util antes que a alguien educado."),

    "elfo": (
        "Queremos que el Umbral se cierre y que la ceniza deje de caer. "        "No queremos el trono: queremos que no haga falta.",
        "Te ayudamos porque todavia no te odio nadie. Vamos a decidir "        "eso antes de que se nos acabe la paciencia."),

    "goblin": (
        "Queremos el trono entero y sin reparto. Es lo unico que "        "sabemos pedir, y por eso mismo lo pedimos fuerte.",
        "Te ayudamos porque entraste al mundo con cinco cartas "        "imposibles y no preguntaste de donde. Eso, para un goblin, "        "casi es amistad."),

    "hombre_lobo": (
        "Queremos que la ciudad deje de ser el corral. No la queremos "        "para nosotros: queremos que la manada deje de depender de "        "ella.",
        "Te ayudamos porque reconocemos a uno que vuelve a levantarse "        "despues de perder. No miramos la estrategia, miramos el "        "historial."),

    "vampiro": (
        "Queremos que se reponga el pacto antiguo que el rey dragon "        "rompio. No el trono entero: que la deuda que se nos debe "        "vuelva a existir.",
        "Te ayudamos porque tenemos mil anos de practica y vos no le "        "debes nada a nadie. Eso nos hace utiles: no podes reclamar "        "nada."),

    "dragon": (
        "Queremos el trono porque el trono es nuestro por sangre y "        "siempre lo fue. No negociamos: reconocemos.",
        "Te ayudamos porque un dragon no ayuda por bondad. Te ayudamos "        "porque sos la primera cosa en mucho tiempo que nos interesa."),

    "elfo_nocturno": (
        "Queremos volver al bosque del que nos expulsaron por mirar al "        "Umbral sin parpadear. Queremos que la grieta vuelva a ser solo "        "un rumor.",
        "Te ayudamos porque uno de los nuestros ya te vio y no le "        "avisamos. Ayudamos a quien ya tenemos fichado."),

    "hombre_pantera": (
        "Queremos que los tejados sigan siendo de quien los usa. El "        "trono nos importa menos que no perder el unico sitio que "        "tenemos.",
        "Te ayudamos porque camina donde nadie mira, y porque te "        "vigilamos desde que bajaste al bosque. Ayudamos a quien "        "tenemos al lado."),

    "hombre_lagarto": (
        "Queremos que el agua vuelva a ser de todos. El trono es el "        "unico papel que existe para conseguir eso.",
        "Te ayudamos porque tenemos mas paciencia que cualquiera: "        "esperamos mas que el mundo, y esperamos un duelo mas."),

}

ORDEN = list(PETICION)


def peticion(faccion):
    """Que quiere la faccion del trono. Vacio si no hay dato."""
    return PETICION.get(faccion, ("", ""))[0]


def por_que_te_ayudan(faccion):
    """Por que esa faccion te da la espalda. Vacio si no hay dato."""
    return PETICION.get(faccion, ("", ""))[1]
