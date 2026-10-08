"""Duelistas: quien pelea y por que pelea.

Idea central de la biblia: ningun rival es malvado. Cada uno tiene una razon
legitima para impedir que el duelista llegue al Umbral, y si pierde, el mundo
no empeora: cambia.

Por que un modulo aparte
------------------------
`campana.DUELISTAS` ya existe y da nombre, titulo y lineas por faccion. Eso
no se toca: es la identidad del rival y la usan el mapa, la musica y los
avatares.

Lo que faltaba era el *rol*: quien es ese rival dentro de la historia. Un
goblin que no quiere pelear (senda), un guardian que protege su aldea
(aldea/ruinas), un jefe con una advertencia legitima (fortaleza), alguien que
vuelve (asalto) y el gobernante del trono.

Se suma por encima, sin reemplazar nada:
    campana._duelista_de -> mezcla DUELISTAS (identidad) + duelistas (rol).

Texto visible en ASCII, como todo el juego. Este modulo no importa campana:
campana lo importa a el.
"""

from ui import TEXTO


def _esc(linea, hablante=None, fondo="ceniza", retrato=None, efecto="dialogo",
         musica=None, color=TEXTO, mundo="juego"):
    """Constructor de escena.

    Copia de `cinematicas.esc`: este modulo lo usa `cinematicas`, e
    importarlo seria un ciclo. Las claves son las mismas.

    `color` arranca en TEXTO y no en None: con None, cada linea de rival sin
    color explicito tumbaba la pantalla del duelo con
    `len(None) has no len()`. Ver `finales.esc`, que tenia el mismo defecto.
    """
    return {"texto": linea, "hablante": hablante, "fondo": fondo, "retrato": retrato,
            "efecto": efecto, "musica": musica, "color": color, "mundo": mundo}


# ------------------------------------------------------------------- el rol
# `reaccion` van por faccion del JUGADOR: lo que el rival dice al ver tu mazo.
# `dialogo` son las lineas pre / win / lose.

ROLES = {
    "senda": {
        "rol": "campesino",
        # Retrato propio del personaje con nombre de este nodo. Si el rival de
        # la escalera resulta ser de otra faccion, se usa el de su faccion: ver
        # `retrato_de`.
        "retrato": "pik",
        "personalidad": "nervioso, parlanchin, cobarde",
        "motivacion": "No quiere pelear. Lo arrastraron al Juicio porque es Juicio.",
        "historia": "Es el primero en decir que las cosas no son como las cartas "
                    "las cuentan.",
        # En la senda no se enfrenta al campeon de la faccion: se enfrenta a un
        # vecino que el Juicio obliga a pelear. Por eso tiene nombre propio, y
        # por eso el titulo no es "Rey Oscuro" ni nada parecido.
        "nombres": {
            "goblin": {"nombre": "Pik", "titulo": "El Que No Queria Jugar"},
            "humano": {"nombre": "Bo", "titulo": "Leñador de la Senda"},
            "orco": {"nombre": "Gruk", "titulo": "El Ultimo Del Foso"},
            "elfo": {"nombre": "Alen", "titulo": "Vigia del Sendero"},
            "hombre_lobo": {"nombre": "Tam", "titulo": "El Que Huia"},
            "vampiro": {"nombre": "Vess", "titulo": "El Que No Duerme"},
            "dragon": {"nombre": "Kor", "titulo": "Ala Que No Levanto"},
            "elfo_nocturno": {"nombre": "Nyx", "titulo": "Sombra De Dia"},
            "hombre_pantera": {"nombre": "Sela", "titulo": "La Que Corre Mal"},
            "hombre_lagarto": {"nombre": "Oldo", "titulo": "El Que Espera"},
        },
        "dialogo": {
            "pre": [
                _esc("- No quiero pelear. De verdad. No quiero.", hablante="__NOMBRE__"),
                _esc("- Si me das el centro me voy y no miro atras."),
            ],
            "win": [
                _esc("- Ganaste. Ya era hora, de verdad.", hablante="__NOMBRE__"),
                _esc("- Aqui nadie muere por un Juicio. Que se note."),
            ],
            "lose": [
                _esc("- Viste? No era necesario ganar.", hablante="__NOMBRE__"),
                _esc("- Perdon. No sabia contra quien tenia."),
            ],
        },
        "reaccion": {
            "humano": "Un humano. Con la corona de un rey que murio en una carta.",
            "orco": "Un orco. Bueno. Peor que los humanos, no va a ser.",
            "elfo": "Un elfo. Nunca tuve un elfo delante. Que cosa mas rara.",
            "goblin": "Un goblin. Voy a necesitar un socio, si no me rompen la cabeza.",
            "hombre_lobo": "Un lobo. Y con luna. Bonito dia para tener miedo.",
            "vampiro": "Un vampiro. De dia. Que aspecto tan raro.",
            "dragon": "Un dragon. Bueno. Supongo que hoy muero.",
            "elfo_nocturno": "Un nocturno. Menos mal. A los otros les tengo mas miedo.",
            "hombre_pantera": "Una pantera. Move los pies, que te veo venir.",
            "hombre_lagarto": "Un lagarto. Tienes cara de que sabes esperar.",
        },
    },
    "aldea": {
        "rol": "guardian",
        "retrato": "dara",
        "personalidad": "estricto, protector, desconfiado",
        "motivacion": "Defiende a su aldea. Le importa mas su gente que tu carta.",
        "historia": "Sabe algo del Umbral y no lo cuenta todo.",
        "dialogo": {
            "pre": [
                _esc("- No entres con eso. Eso no es tuyo.", hablante="__NOMBRE__"),
                _esc("- Aqui las cartas son Juicio, no juguete. Se nota."),
            ],
            "win": [
                _esc("- No deberia haber perdido.", hablante="__NOMBRE__"),
                _esc("- Quien te ensena a jugar asi, te miente en algo."),
            ],
            "lose": [
                _esc("- Bien. La aldea esta a salvo.", hablante="__NOMBRE__"),
                _esc("- Eso es lo unico que importa aqui."),
            ],
        },
        "reaccion": {
            "humano": "Un humano. Bien. Los humanos aqui al menos se presentan.",
            "orco": "Un orco. Como entraste? Nadie te aviso?",
            "elfo": "Un elfo. Alguien viene del bosque, y viene con paso seguro.",
            "goblin": "Un goblin. Espero que no seas como los que vinieron antes.",
            "hombre_lobo": "Un lobo. Con luna llena. No me gustan los presagios.",
            "vampiro": "Un vampiro. No cruces las murallas de noche. No es cortesia.",
            "dragon": "Un dragon. Trajiste fuego o paz? Se nota pronto.",
            "elfo_nocturno": "Un nocturno. Aqui no confimos en los de la noche.",
            "hombre_pantera": "Una pantera. Libre o cazador: no confundas las dos.",
            "hombre_lagarto": "Un lagarto. La memoria dice cuidado con los que esperan.",
        },
    },
    "ruinas": {
        "rol": "custodio",
        "retrato": "dara",
        "personalidad": "cansado, minucioso, casi increible",
        "motivacion": "Guarda lo que quedo bajo la ceniza. Cree que nadie mas lo "
                      "buscara jamas.",
        "historia": "Ahi abajo hay un dibujo de una carta tuya pintado en una pared.",
        "dialogo": {
            "pre": [
                _esc("- Baja despacio. Esto ya estaba roto antes de que llegaras.",
                     hablante="__NOMBRE__"),
                _esc("- Y no, no te lo voy a explicar."),
            ],
            "win": [
                _esc("- Te llevaste una carta y no una reliquia. Curioso.",
                     hablante="__NOMBRE__"),
            ],
            "lose": [
                _esc("- Aqui no hay nada que robar. Solo cosas que alguien borro.",
                     hablante="__NOMBRE__"),
            ],
        },
        "reaccion": {
            "humano": "Un humano. Los humanos siempre llegan tarde a las ruinas.",
            "orco": "Un orco. Rompes cosas al entrar. Como todos.",
            "elfo": "Un elfo. Tu manera de mirar antes de tocar. Tipica.",
            "goblin": "Un goblin. Nunca vi uno tan callado. Eso me asusta.",
            "hombre_lobo": "Un lobo. Huele a lluvia. No a mentira.",
            "vampiro": "Un vampiro. Sabe lo que hay abajo sin que nadie le diga.",
            "dragon": "Un dragon. Quien te dejo este sitio, tendria que estar muerto.",
            "elfo_nocturno": "Un nocturno. Los de la noche leen mejor que nosotros.",
            "hombre_pantera": "Una pantera. Se mueve y yo no me entero. Raro.",
            "hombre_lagarto": "Un lagarto. Escucha el suelo. Escucha mucho.",
        },
    },
    "fortaleza": {
        "rol": "jefe_arco",
        "retrato": "jefe_arco",
        "personalidad": "convencido, serio, protector",
        "motivacion": "Abrir el Umbral tiene un precio que el duelista todavia no "
                      "conoce.",
        "historia": "Sabe del Umbral mas que nadie. Por eso intenta que nadie llegue.",
        "dialogo": {
            "pre": [
                _esc("- No sigas. No por mi. Por lo que hay atras.",
                     hablante="__NOMBRE__"),
                _esc("- Cada vez que los mundos se tocan, algo pasa en los dos lados."),
                _esc("- Vos ya cruzaste. Preguntate que cruza de vuelta."),
            ],
            "win": [
                _esc("- Ganaste. Bien. Ahora descubri lo que yo no pude impedir.",
                     hablante="__NOMBRE__"),
                _esc("- Lo que hay del otro lado ya esta en camino."),
            ],
            "lose": [
                _esc("- No tenias por que ganar. Pero ya que estas, escucha.",
                     hablante="__NOMBRE__"),
                _esc("- El Umbral no es un juego. Y cada mundo cobra."),
            ],
        },
        "reaccion": {
            "humano": "Un humano. Con la bandera de un reino que ya no existe.",
            "orco": "Un orco en la fortaleza. Alguien esta de mal humor.",
            "elfo": "Un elfo. Lei lo que dicen de los elfos. No le crei todo.",
            "goblin": "Un goblin. Nadie me dijo que vendrian tan grandes.",
            "hombre_lobo": "Un lobo. No por la luna. Por lo que trae el Umbral.",
            "vampiro": "Un vampiro. Todos saben lo que hacen los de la noche.",
            "dragon": "Un dragon. Tu sola presencia ya es un problema.",
            "elfo_nocturno": "Un nocturno. Los exiliados tambien buscan el Umbral.",
            "hombre_pantera": "Una pantera. Entre los muros la presa se cree escondida.",
            "hombre_lagarto": "Un lagarto. Sabe esperar. Eso me preocupa.",
        },
    },
    "asalto": {
        "rol": "revancha",
        "retrato": "revancha",
        "personalidad": "amargo, insistente, leal a su propia version",
        "motivacion": "Perdio una vez y no lo ha olvidado. Vuelve por su nombre, no "
                      "por el trono.",
        "historia": "Te conoce de verdad. Sabe que tus cartas no son de este mundo.",
        "dialogo": {
            "pre": [
                _esc("- Otra vez.", hablante="__NOMBRE__"),
                _esc("- Otra vez la misma combinacion. No se si te enorgullece o me "
                     "insulta."),
                _esc("- Yo si me acuerdo. Yo me acuerdo de todo."),
            ],
            "win": [
                _esc("- No te'])) ya. Y eso es peor que perder.", hablante="__NOMBRE__"),
            ],
            "lose": [
                _esc("- Otra vez. Que se note.", hablante="__NOMBRE__"),
                _esc("- Perder un duelo no es perder. Lo importante es otra cosa."),
            ],
        },
        "reaccion": {
            "humano": "Un humano. La corona de un rey. Otra vez.",
            "orco": "Un orco. Todo bien. Todo bien. Otra vez.",
            "elfo": "Un elfo. Que turno has robado hoy.",
            "goblin": "Un goblin. Los unicos que alken las reglas. Otra vez.",
            "hombre_lobo": "Un lobo. La luna cambia y tu tambien.",
            "vampiro": "Un vampiro. La paciencia no se hereda.",
            "dragon": "Un dragon. Y este es mi techo. Otra vez.",
            "elfo_nocturno": "Un nocturno. Nostalgia. No lo digas muy alto.",
            "hombre_pantera": "Una pantera. Te esperaba. Como la primera vez.",
            "hombre_lagarto": "Un lagarto. Una revancha a la que se le tiene paciencia.",
        },
    },
    "trono": {
        "rol": "gobernante",
        "retrato": "gobernante",
        "personalidad": "sobrio, cansado, sabe mas de lo que va a decir",
        "motivacion": "Protege el Umbral porque sabe lo que cruza si se abre.",
        "historia": "Sabe quien es el Cartografo. Sabe por que llegaste tu.",
        "dialogo": {
            "pre": [
                _esc("- No necesitas pelear. De verdad. Eso es lo raro.",
                     hablante="__NOMBRE__"),
                _esc("- Pero si ganas, vas a descubrir la verdad. Y la verdad no es "
                     "lo que esperas."),
                _esc("- Lo prudente es no saber. Eso no lo vas a entender hasta "
                     "que sea tarde."),
            ],
            "win": [
                _esc("- Ganaste. Ahora sos el primero que sabe.", hablante="__NOMBRE__"),
                _esc("- Abre el Umbral si viniste a eso. Y despues no mires atras."),
            ],
            "lose": [
                _esc("- Perdiste. Pero la verdad no la perdiste con el duelo.",
                     hablante="__NOMBRE__"),
                _esc("- Eso es lo que importa. No el trono."),
            ],
        },
        "reaccion": {
            "humano": "Un humano. Entonces eres parte del problema.",
            "orco": "Un orco en el trono. El mundo al reves, entonces.",
            "elfo": "Un elfo. Tradiciones enteras, decididas en una tarde.",
            "goblin": "Un goblin. Nadie le dijo que esto no se podia.",
            "hombre_lobo": "Un lobo. Bestia o persona? No. Decidilo vos.",
            "vampiro": "Un vampiro. Cuanto viviste ya? Al final se nota.",
            "dragon": "Un dragon. Poder sin nadie que te pueda tocar. Eso se paga.",
            "elfo_nocturno": "Un nocturno. Volviste. Nadie que pregunte por que te "
                            "fuiste.",
            "hombre_pantera": "Una pantera. Honor o libertad. No las dos.",
            "hombre_lagarto": "Un lagarto. La verdad mas vieja, y la que menos se "
                              "recuerda.",
        },
    },
}

# Mini campanas (NG+): tres duelos sin mapa, asi que el rol es mas simple.
ROLES_MINI = {
    "mini_senda": "vigilante",
    "mini_nudo": "enjambre",
    "mini_trono": "dueno",
}


# ------------------------------------------------------------------ publico


def rol_de(nodo_id):
    return ROLES.get(nodo_id) or {}


def retrato_de(nodo_id, faccion):
    """Que retrato se dibuja en un nodo.

    El del personaje con nombre si el rival de la escalera es de la faccion que
    le corresponde; si no, el de la faccion del rival. Un goblin que aparece en
    la senda tiene que ser Pik, no "un goblin".
    """
    propio = rol_de(nodo_id).get("retrato")
    if propio and faccion == _FACCION_DEL_RETRATO.get(propio):
        return propio
    return faccion


#: De que faccion es cada retrato con nombre. Si el rival no es de esa faccion,
#: se dibuja el suyo: el retrato tiene que coincidir con el color del bando.
_FACCION_DEL_RETRATO = {
    "pik": "goblin",
    "dara": "humano",
    "jefe_arco": "humano",
    "revancha": "humano",
    "gobernante": "humano",
}


def identidad_rol(nodo_id, faccion):
    """Nombre y titulo propios del rol, si el rol los define.

    Casi todos los nodos usan el campeon de la faccion (Ignarok, Lyra...), pero
    la senda no: ahi pelea un vecino cualquiera, y llamarle "Rey Oscuro"
    mientras dice "no quiero pelear" no tiene sentido.
    """
    nombres = rol_de(nodo_id).get("nombres", {})
    return nombres.get(faccion, {})


def nombre_rol(nodo_id):
    return rol_de(nodo_id).get("rol", "duelista")


def personalidad_de(nodo_id):
    return rol_de(nodo_id).get("personalidad", "")


def motivacion_de(nodo_id):
    return rol_de(nodo_id).get("motivacion", "")


def historia_de(nodo_id):
    return rol_de(nodo_id).get("historia", "")


def dialogo_de(nodo_id, momento, nombre_duelista):
    """Lineas del rival en un momento dado, con el nombre ya resuelto.

    `momento` in ("pre", "win", "lose").
    """
    datos = rol_de(nodo_id).get("dialogo", {}).get(momento, [])
    salida = []
    for e in datos:
        copia = dict(e)
        texto = copia.get("texto", "")
        if "__NOMBRE__" in texto:
            texto = texto.replace("__NOMBRE__", nombre_duelista)
            # con el nombre dentro del texto no hace falta hablante
            copia.pop("hablante", None)
        salida.append(copia)
    return salida


def reaccion_rol(nodo_id, faccion_jugador):
    """Lo que el rival dice al ver tu mazo. Vacio si no aplica."""
    return rol_de(nodo_id).get("reaccion", {}).get(faccion_jugador, "")
