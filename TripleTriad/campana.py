"""Modo campana: historia por faccion, ramas, recompensas y finales.

La faccion que eliges al empezar decide:
  - contra quien te puedes enfrentar (nunca contra tu propia faccion)
  - el arco narrativo, las recompensas tematicas y el final que obtienes

Grafo de la campana (5 duelos con una bifurcacion real):

    intro -> senda -> bifurcacion -> fortaleza -> asalto -> trono
                                /       \\
                          aldea           ruinas
"""

import json
import os
import random
import time

import facciones
import mazos
from paths import archivo
from reglas import Carta

VERSION = 3
ARCHIVO_PARTIDA = "campana.json"
ARCHIVO_PERFIL = "perfil.json"

# ---------------------------------------------------------------- duelistas

DUELISTAS = {
    "goblin": {
        "nombre": "Grix el Mugroso",
        "titulo": "Rey de los Goblins",
        "entrada": "Hehe! A por tu mazo, viajero!",
        "captura_player": "Aargh! Mis cartas!",
        "captura_cpu": "Todas para Grix!",
        "win": "Nadie le gana a los goblins! Hehe!",
        "lose": "Bien jugado... esta vez.",
    },
    "elfo": {
        "nombre": "Lyra",
        "titulo": "Dama del Bosque",
        "entrada": "Que la luz guie mi mazo.",
        "captura_player": "Oh... el bosque atiende.",
        "captura_cpu": "La naturaleza provee.",
        "win": "La gracia elfica triunfa.",
        "lose": "Bien jugado, viajero.",
    },
    "hombre_lobo": {
        "nombre": "Fenris",
        "titulo": "Alfa de la Manada",
        "entrada": "Grrr... prepara tus cartas.",
        "captura_player": "Arrgh! la manada resiste!",
        "captura_cpu": "La manada domina!",
        "win": "La manada siempre gana.",
        "lose": "Mal me dejaste, viajero.",
    },
    "vampiro": {
        "nombre": "Condesa Sanguinaria",
        "titulo": "Dama de la Noche",
        "entrada": "Tus cartas son mias.",
        "captura_player": "Insolente...",
        "captura_cpu": "Como la sangre por las venas.",
        "win": "La noche es mia.",
        "lose": "Te doy mi respeto.",
    },
    "dragon": {
        "nombre": "Ignarok",
        "titulo": "El Rey Oscuro",
        "entrada": "QUEMARE. TU MAZO ARDE.",
        "captura_player": "Grrr... arde en furia!",
        "captura_cpu": "QUEME TODO!",
        "win": "NINGUN HUMANO PUEDE CONMIGO.",
        "lose": "...ha sido una buena quema.",
    },
    "humano": {
        "nombre": "Capitan Aldric",
        "titulo": "Senor de la Torre Rota",
        "entrada": "Alza el escudo. Hoy no dormimos.",
        "captura_player": "Cedemos terreno... por ahora.",
        "captura_cpu": "Una linea mas y la fas se sostiene.",
        "win": "La corona sigue en pie.",
        "lose": "Buen golpe, forastero.",
    },
    "orco": {
        "nombre": "Vorg",
        "titulo": "Senor de la Guerra",
        "entrada": "NAKA! Hoy la tierra es nuestra!",
        "captura_player": "GARR! Somos el precio, no el regalo!",
        "captura_cpu": "NAKA NAKA! Sigamos!",
        "win": "Orcos al Umbral!",
        "lose": "Grrr... caes hoy, no el ultimo.",
    },
}

# Titulos alternativos por nodo para que los rivales no repitanPresentacion.
TITULOS_NODO = {
    "senda": "",
    "aldea": "Guardianes de la Aldea",
    "ruinas": "Lo que Desperto Bajo la Ceniza",
    "fortaleza": "Campeon de la Fortaleza",
    "asalto": "El Que Vuelve",
    "trono": "Soberano del Umbral",
}

# ------------------------------------------------------------- grafo de nodos

NODOS = {
    "senda": {
        "tipo": "duelo",
        "titulo": "El Camino de Ceniza",
        "escena": "camino",
        "dificultad": 0,
        "previa": [
            "El camino esta sembrado de ceniza y nadie sabe de donde viene.",
            "Un rival espera en la primera encrucijada con la guardia alta.",
        ],
        "siguiente": "bifurcacion",
    },
    "bifurcacion": {
        "tipo": "eleccion",
        "titulo": "Dos Caminos",
        "siguiente": "fortaleza",
        "opciones": {
            "aldea": {
                "titulo": "Ir a la Aldea",
                "resumen": "Gente que pide proteccion: enemigo breve, recompensa segura.",
                "previa": ["Las luces de una aldea resisten la oscuridad."],
            },
            "ruinas": {
                "titulo": "Entrar en las Ruinas",
                "resumen": "Tesoros y trampas: enemigo mas duro, mejor recompensa.",
                "previa": ["Bajo la ceniza hay una ciudad que nadie recordaba."],
            },
        },
    },
    "aldea": {
        "tipo": "duelo",
        "titulo": "La Aldea que Respira",
        "escena": "aldea",
        "dificultad": 1,
        "previa": ["Al defender la aldea, la gente te dara lo que tiene."],
        "siguiente": "fortaleza",
    },
    "ruinas": {
        "tipo": "duelo",
        "titulo": "Las Ruinas Ardientes",
        "escena": "ruinas",
        "dificultad": 2,
        "previa": ["Lo que guardan las ruinas no se lo quedo nadie, y por algo es."],
        "siguiente": "fortaleza",
    },
    "fortaleza": {
        "tipo": "duelo",
        "titulo": "La Fortaleza que No Cede",
        "escena": "fortaleza",
        "dificultad": 2,
        "previa": ["Quien controla la fortaleza controla el mapa."],
        "siguiente": "asalto",
    },
    "asalto": {
        "tipo": "duelo",
        "titulo": "El Que Vuelve",
        "escena": "asalto",
        "dificultad": 2,
        "previa": ["Creiste que estaba derrotado. No lo estaba."],
        "siguiente": "trono",
    },
    "trono": {
        "tipo": "final",
        "titulo": "El Umbral del Trono",
        "escena": "trono",
        "dificultad": 3,
        "previa": ["Aqui termina el camino. Aqui se decide de quien es el mundo."],
        "siguiente": None,
    },
}

# Escaleras de rivales: una por faccion, sin incluir su propio bando.
ESCALERAS = {
    "humano": ["orco", "goblin", "elfo", "hombre_lobo", "vampiro"],
    "orco": ["goblin", "humano", "hombre_lobo", "vampiro", "elfo"],
    "elfo": ["orco", "hombre_lobo", "goblin", "vampiro", "humano"],
    "goblin": ["orco", "hombre_lobo", "vampiro", "elfo", "humano"],
    "hombre_lobo": ["orco", "vampiro", "goblin", "elfo", "humano"],
    "vampiro": ["humano", "goblin", "hombre_lobo", "elfo", "orco"],
    "dragon": ["humano", "elfo", "orco", "hombre_lobo", "vampiro"],
}

# ------------------------------------------------------------------ recompensas

RECOMPENSAS = {
    "senda": ["entrenamiento", "recluta"],
    "aldea": ["entrenamiento", "recluta", "sigilo"],
    "ruinas": ["recluta", "sigilo", "aliado"],
    "fortaleza": ["entrenamiento", "sigilo", "aliado"],
    "asalto": ["entrenamiento", "recluta", "sigilo"],
    "trono": [],
}

TEXTO_RECOMPENSA = {
    "entrenamiento": "Entrenamiento: +1 a un lado de la carta que elijas.",
    "recluta": "Recluta: elige una de las tres cartas ofrecidas.",
    "sigilo": "Sigilo de guerra: +1 permanente al lado mas bajo de todas tus cartas.",
    "aliado": "Pacto: desbloquea el mazo de esa faccion para el draft.",
}

# -------------------------------------------------------------------- encuentros

ENCUENTROS = [
    {
        "id": "mercader",
        "titulo": "Mercader Errante",
        "escena": "campamento",
        "texto": "Un mercador que no ensena bandera. - Tengo una oferta y se acaba con la noche.",
        "opciones": [
            {
                "id": "pagar",
                "texto": "Pagar con una carta (+1 a un lado de la que elijas)",
                "efecto": "mejorar",
            },
            {
                "id": "robar",
                "texto": "Tomarle la bolsa (ganas una carta del pool)",
                "efecto": "robo",
            },
        ],
    },
    {
        "id": "anciano",
        "titulo": "El Anciano del Umbral",
        "escena": "ruinas",
        "texto": "Un viejo encapuchado. - Te veo venir. Te dejo un consejo. Esta vez no cobro.",
        "opciones": [
            {
                "id": "escuchar",
                "texto": "Escucharlo (+1 a tu carta mas debil)",
                "efecto": "mas_debil",
            },
            {
                "id": "desconfiar",
                "texto": "Desconfiar (el rival llegara -1 en el proximo duelo)",
                "efecto": "debilitar",
            },
        ],
    },
    {
        "id": "hermandad",
        "titulo": "Hermandad de Armas",
        "escena": "campamento",
        "texto": "Guerreros que combatieron a tu lado. - Nuestra victoria sera tu victoria.",
        "opciones": [
            {
                "id": "celebrar",
                "texto": "Celebrar con ellos (+1 a tus dos cartas mas debiles)",
                "efecto": "celebrar",
            },
            {
                "id": "descansar",
                "texto": "Descansar (+1 permanente a todas tus cartas)",
                "efecto": "sigilo",
            },
        ],
    },
]

ENCUENTRO_POR_NODO = {
    "senda": "mercader",
    "aldea": "hermandad",
    "ruinas": "anciano",
    "fortaleza": "mercader",
    "asalto": "hermandad",
}

# ----------------------------------------------------------------------- finales

FINALES = {
    "humano": {
        "dominio": {
            "titulo": "EL REY RECONSTRUIDO",
            "lineas": [
                "El Umbral calla y la corona vuelve a ser de bronce y no de ceniza.",
                "No hay hambre en las fronteras: hay escuelas y campanas que suenan temprano.",
                "La historia no dira que los humanos fueron los mas fuertes.",
                "Dira que fueron los que se quedaron.",
            ],
        },
        "equilibrio": {
            "titulo": "LA PAZ CONGELADA",
            "lineas": [
                "Ganaste el trono y el derecho a conservarlo: eso es justo lo que ellos querian.",
                "El bosque respira otra vez, la manada vuelve al bosque, la noche se aquieta.",
                "Nadie recuerda ya que hubo una guerra. Eso, en el fondo, tambien es una victoria.",
            ],
        },
        "caos": {
            "titulo": "UNA CORONA FRAGIL",
            "lineas": [
                "Ganaste, pero por poco, y el reino lo sabe.",
                "Los elfos cuentan otra version. Los orcos, otra. Nadie coincide.",
                "La paz que lograste durara lo que dura un invierno sin pan.",
            ],
        },
    },
    "orco": {
        "dominio": {
            "titulo": "EL TRONO DE CENIZA",
            "lineas": [
                "Los portones ceden y el trono del Umbral es tuyo para quien lo alcance.",
                "El bosque envejece mil anos en una sola noche.",
                "No eres un rey: eres el primer orco que no pide permiso para existir.",
            ],
        },
        "equilibrio": {
            "titulo": "LA TRIBU REUNIDA",
            "lineas": [
                "No arrasaste el mundo: lo tomaste en fracciones justas.",
                "Los elfos exiliados al norte y un pacto que nadie se atreve a romper.",
                "Es poco. Para tu pueblo, es todo.",
            ],
        },
        "caos": {
            "titulo": "NADA DE ESO QUEDA",
            "lineas": [
                "Quemaste el trono, pero no lo tomaste. Ya hubo otros que lo intentaron.",
                "El bosque crece sobre tus banderas y los elfos tocan la ceniza con reverencia.",
                "Tu pueblo sobrevive. Es la unica victoria que no puedes negociar.",
            ],
        },
    },
    "goblin": {
        "dominio": {
            "titulo": "EL BOTIN DE TODO",
            "lineas": [
                "El rey dragon no deja tronos: deja tesoros, y eso os basta.",
                "Grix duerme sobre una montana de oro y ronca como un jabali.",
                "Hehe.",
            ],
        },
        "equilibrio": {
            "titulo": "UN GRIJON CON CASA",
            "lineas": [
                "Osaron los goblins con casa propia y un muro de quince centimetros.",
                "Los elfos no approve el uso de la palabra goblin con mayuscula, pero no pueden atacaros.",
                "Nadie recuerda que hubo una guerra por una montana de oro.",
            ],
        },
        "caos": {
            "titulo": "SIN BOTIN, CON HAMBRE",
            "lineas": [
                "Perdisteis el rastro del rey dragon y el banquete de la victoria.",
                "Grix os culpa a todos menos a si mismo. Es tradicion.",
                "La montana de oro se la llevan los elfos, que no comparten ni el sonido.",
            ],
        },
    },
    "elfo": {
        "dominio": {
            "titulo": "EL BOSQUE RESPONDE",
            "lineas": [
                "Las raices de mil anos sostienen por fin una corona elfica.",
                "El fuego se apaga en el Claro y los elfos cantan tu nombre muy alto.",
                "Fue la primera vez en cuatrocientos anos que el bosque eligio bando.",
            ],
        },
        "equilibrio": {
            "titulo": "EL BOSQUE EN PAZ",
            "lineas": [
                "No tomaste el trono: lo dejaste entre las ramas, como se debe.",
                "Lyra firma la paz y las raices cubren los campos de batalla.",
                "Los elfos cuelgan su bandera blanca de los arboles y la ciudad respira.",
            ],
        },
        "caos": {
            "titulo": "HOJAS SECAS",
            "lineas": [
                "El bosque se levanto contigo y ya no sabe a quien obedecer.",
                "Los elfos caminan por un reino que ya no reconoce la bandera del bosque.",
                "Hasta los arboles han dejado de responder a la bandera del bosque.",
            ],
        },
    },
    "hombre_lobo": {
        "dominio": {
            "titulo": "LA MANADA CORONA",
            "lineas": [
                "La luna miro a la ciudad y esta vez no aparto la cara.",
                "La manada duerme en los auditorios que fueron palacios.",
                "Nadie cierra las puertas de noche y nadie lo echa de menos.",
            ],
        },
        "equilibrio": {
            "titulo": "LUNAR PARADO",
            "lineas": [
                "No eres rey: eres el guardio que decide cuando empieza la luna.",
                "La ciudad abre las puertas de noche y nadie registra por que.",
                "El bosque y la ciudad comparten ahora el mismo reloj lunar.",
            ],
        },
        "caos": {
            "titulo": "SIN LUNA, SIN MANADA",
            "lineas": [
                "La manada se ha dispersado por un mapa que ya no reconoce sus huellas.",
                "Alfa sin manada es solo un lobo muy cansado.",
                "Los pueblos de la frontera ya no cuentan manadas: cuentan silencios.",
            ],
        },
    },
    "vampiro": {
        "dominio": {
            "titulo": "LA NOCHE CORONA",
            "lineas": [
                "El pacto antiguo se ha roto y tu linaje lo ha escrito con sangre nueva.",
                "Tres ciudades arden antes del amanecer y en todas se abre la ventana para ti.",
                "Los humanos descubren que la noche tiene ahora un gobierno.",
            ],
        },
        "equilibrio": {
            "titulo": "EL PACTO REESCRITO",
            "lineas": [
                "No destruiste a la manada: negociaste con ella.",
                "Hay dos poderes ahora y los dos saben leer el mismo contrato.",
                "Las criaturas de la noche se reparten el mapa en una paz que huele a ironia.",
            ],
        },
        "caos": {
            "titulo": "CRIPTA ABIERTA",
            "lineas": [
                "Perdiste el pacto y la corona en la misma noche.",
                "Los nobles de la noche empiezan a cazarse entre si y el amanecer no llega a tiempo.",
                "El amanecer llega puntual, y la ciudad cree que es una victoria.",
            ],
        },
    },
    "dragon": {
        "dominio": {
            "titulo": "EL REY DEL CIELO",
            "lineas": [
                "La ceniza que nacio en lo dragonico se ha vuelto tu corona.",
                "Los humanos que te desafiaron son ahora hogueras, no ejercitos.",
                "El cielo arde y esta vez lo enciendes tu.",
            ],
        },
        "equilibrio": {
            "titulo": "DOS CORONAS",
            "lineas": [
                "No aplastaste a los humanos: les hiciste una oferta y la aceptaron.",
                "El reino de Aldric sigue en pie y ahora te escucha.",
                "Los dos tronos comparten una sola hoguera y un solo guardian.",
            ],
        },
        "caos": {
            "titulo": "EL UMBRAL VACIO",
            "lineas": [
                "Tu propia fuerza te ha dejado solo en el Umbral, como un rey de piedra.",
                "No hay a quien quemar. Solo ceniza, y ceniza.",
                "La ceniza no sabe a quien pertenece. Ya no queda nadie que lo pregunte.",
            ],
        },
    },
}

# ---------------------------------------------------------------------- estado


def _semilla(faccion):
    """Semilla estable por faccion: cada quien tiene siempre su misma escalera."""
    return sum(ord(ch) for ch in faccion) * 7919


def escalera_de(faccion):
    """Escalera de rivales garantizada sin la faccion del jugador."""
    base = [f for f in ESCALERAS.get(faccion, []) if f != faccion]
    for f in facciones.orden_facciones():
        if f != faccion and f not in base:
            base.append(f)
    rng = random.Random(_semilla(faccion))
    rng.shuffle(base)
    return base


def _duelista_de(rival, nodo_id):
    d = dict(DUELISTAS.get(rival, {}))
    extra = TITULOS_NODO.get(nodo_id, "")
    if extra:
        d["titulo"] = extra
    return d


def nueva_campana(faccion="humano"):
    return {
        "version": VERSION,
        "faccion": faccion,
        "nodo": "senda",
        "ruta": [],
        "eleccion": None,
        "cartas": [c.a_dict() for c in mazos.TODOS[faccion]],
        "racha": 0,
        "mejor_racha": 0,
        "victorias": 0,
        "derrotas": 0,
        "capturas": 0,
        "aliados": [],
        "debilitar": 0,
        "sigilos": 0,
        "completada": False,
        "final": None,
        "creada": time.time(),
    }


# ---------------------------------------------------------------- persistencia


def ruta_partida():
    return archivo(ARCHIVO_PARTIDA)


def ruta_perfil():
    return archivo(ARCHIVO_PERFIL)


def guardar(estado):
    try:
        with open(ruta_partida(), "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def cargar():
    try:
        with open(ruta_partida(), encoding="utf-8") as f:
            return _migrar(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, OSError, AttributeError):
        return None


def borrar_partida():
    try:
        os.remove(ruta_partida())
    except OSError:
        pass


def _migrar(datos):
    """Convierte partidas viejas (lineales, 5 bandos) al grafo actual."""
    if not isinstance(datos, dict):
        return None
    if datos.get("version") == VERSION:
        return datos
    faccion = datos.get("mazo_jugador", "humano")
    if faccion not in facciones.FACCIONES:
        faccion = "humano"
    nuevo = nueva_campana(faccion)
    if datos.get("cartas"):
        nuevo["cartas"] = datos["cartas"]
    etapa = int(datos.get("etapa", 0) or 0)
    orden = ["senda", "bifurcacion", "fortaleza", "asalto", "trono"]
    nuevo["nodo"] = orden[min(etapa, len(orden) - 1)]
    nuevo["mejor_racha"] = int(datos.get("racha", 0) or 0)
    if etapa >= 5 and datos.get("completada"):
        nuevo["completada"] = True
    return nuevo


def progreso(estado):
    """0..1 segun los duelos superados."""
    return min(1.0, len(estado.get("ruta", [])) / 5.0)


# ------------------------------------------------------------------- recorrido


def nodo_actual(estado):
    return estado.get("nodo") or "senda"


def nodo(nodo_id):
    return NODOS.get(nodo_id, NODOS["senda"])


def nodo_siguiente(estado):
    actual = nodo_actual(estado)
    datos = nodo(actual)
    if datos["tipo"] == "eleccion":
        return estado.get("eleccion")
    return datos.get("siguiente")


def opciones_bifurcacion():
    return list(NODOS["bifurcacion"]["opciones"].keys())


def elegir_bifurcacion(estado, opcion):
    if opcion in opciones_bifurcacion():
        estado["eleccion"] = opcion
        estado["nodo"] = opcion
        guardar(estado)


def _rival_de_escalera(estado, indice):
    escalera = escalera_de(estado["faccion"])
    return escalera[indice % len(escalera)]


def rival_de_nodo(estado, nodo_id=None):
    """Faccion rival del nodo. Nunca es la faccion del jugador."""
    faccion = estado["faccion"]
    nodo_id = nodo_id or nodo_actual(estado)
    if nodo_id == "senda":
        rival = _rival_de_escalera(estado, 0)
    elif nodo_id in ("aldea", "ruinas"):
        rival = _rival_de_escalera(estado, 1 if nodo_id == "aldea" else 2)
    elif nodo_id == "fortaleza":
        rival = _rival_de_escalera(estado, 3)
    elif nodo_id == "asalto":
        ya_vistos = [
            _rival_de_escalera(estado, 0),
            _rival_de_escalera(estado, 1 if estado.get("eleccion") == "aldea" else 2),
        ]
        rival = ya_vistos[int(estado.get("revancha", 0) or 0) % len(ya_vistos)]
    else:
        rival = facciones.rival_final(faccion)
    if rival == faccion:
        rival = _rival_de_escalera(estado, 4)
    return rival


def info_duelo(estado, nodo_id=None):
    """Datos completos del duelo que toca jugar."""
    nodo_id = nodo_id or nodo_actual(estado)
    datos = nodo(nodo_id)
    rival = rival_de_nodo(estado, nodo_id)
    duelo = _duelista_de(rival, nodo_id)
    return {
        # nodo
        "nodo": nodo_id,
        "titulo": datos["titulo"],
        "escena": datos.get("escena", "campamento"),
        "previa": datos.get("previa", []),
        "tipo": datos["tipo"],
        "dificultad": int(datos.get("dificultad", 0)),
        # rival
        "bando": rival,
        "nombre_faccion": facciones.nombre(rival),
        "nombre": duelo.get("nombre", facciones.nombre(rival)),
        "titulo_duelo": duelo.get("titulo", ""),
        "entrada": duelo.get("entrada", ""),
        "captura_player": duelo.get("captura_player", ""),
        "captura_cpu": duelo.get("captura_cpu", ""),
        "win": duelo.get("win", ""),
        "lose": duelo.get("lose", ""),
    }


def mazo_rival(estado, nodo_id=None, dificultad_extra=0):
    """Mazo rival con las cartas potenciadas segun la dificultad del nodo.

    El efecto `debilitar` de los encuentros resta: el rival llega mas flojo.
    """
    info = info_duelo(estado, nodo_id)
    nivel = info["dificultad"] + dificultad_extra - int(estado.get("debilitar", 0) or 0)
    cartas = [c.copia() for c in mazos.TODOS[info["bando"]]]
    rng = random.Random((_semilla(estado["faccion"]) + sum(ord(c) for c in info["nodo"])) % 999983)
    for c in cartas:
        for lado in ("N", "S", "E", "O"):
            if c.valores[lado] < 10 and nivel > 0 and rng.random() < 0.7:
                c.valores[lado] += min(nivel, 10 - c.valores[lado])
    return cartas


def cartas_jugador(estado):
    return [Carta.desde_dict(d, estado["faccion"]) for d in estado["cartas"]]


# -------------------------------------------------------------------- progreso


def registrar_victoria(estado, capturas=0):
    estado["victorias"] = estado.get("victorias", 0) + 1
    estado["racha"] = estado.get("racha", 0) + 1
    estado["capturas"] = estado.get("capturas", 0) + int(capturas)
    estado["mejor_racha"] = max(estado.get("mejor_racha", 0), estado["racha"])
    estado["debilitar"] = 0
    estado.setdefault("ruta", []).append(nodo_actual(estado))
    siguiente = nodo_siguiente(estado)
    if siguiente is None:
        estado["completada"] = True
    else:
        estado["nodo"] = siguiente
    guardar(estado)


def registrar_derrota(estado):
    estado["derrotas"] = estado.get("derrotas", 0) + 1
    estado["racha"] = 0
    guardar(estado)


def variante_final(estado):
    """'dominio', 'equilibrio' o 'caos' segun como se termino la campana."""
    derrotas = estado.get("derrotas", 0)
    if derrotas <= 1 and estado.get("mejor_racha", 0) >= 4:
        return "dominio"
    if derrotas <= 3:
        return "equilibrio"
    return "caos"


def final_de(estado):
    """(variante, titulo, lineas) del final segun faccion y rendimiento."""
    faccion = estado["faccion"]
    variante = variante_final(estado)
    datos = FINALES.get(faccion, FINALES["humano"])[variante]
    return variante, datos["titulo"], list(datos["lineas"])


def completar(estado):
    variante, titulo, _ = final_de(estado)
    estado["final"] = {"variante": variante, "titulo": titulo, "faccion": estado["faccion"]}
    estado["completada"] = True
    estado["nodo"] = "trono"
    guardar(estado)
    nuevo = registrar_final_perfil(estado["faccion"], variante)
    estado["final"]["nuevo"] = nuevo
    guardar(estado)
    return estado["final"]


# ------------------------------------------------------------------- recompensas


def recompensas_de(nodo_id):
    return list(RECOMPENSAS.get(nodo_id, ["entrenamiento", "recluta"]))


def aplicar_sigilo(estado):
    """+1 permanente al lado mas bajo de cada carta."""
    for d in estado["cartas"]:
        lado = min(("n", "s", "e", "o"), key=lambda l: d[l])
        d[lado] = min(10, d[lado] + 1)
    estado["sigilos"] = estado.get("sigilos", 0) + 1
    guardar(estado)


def mejorar_carta(estado, id_carta, lado=None):
    """Sube +1 (max 10) en el lado indicado o, si no cabe, en el mas bajo."""
    d = estado["cartas"][id_carta]
    if lado and d[lado] < 10:
        d[lado] += 1
        guardar(estado)
        return lado
    candidatos = [l for l in ("n", "s", "e", "o") if d[l] < 10]
    if not candidatos:
        return None
    elegido = min(candidatos, key=lambda l: d[l])
    d[elegido] += 1
    guardar(estado)
    return elegido


def cartas_del_pool(estado, facciones_extra=None):
    """Pool de draft: faccion del jugador mas aliados desbloqueados."""
    permitidas = {estado["faccion"]}
    permitidas.update(estado.get("aliados", []))
    if facciones_extra:
        permitidas.update(facciones_extra)
    return [c for bando, cartas in mazos.TODOS.items() if bando in permitidas for c in cartas]


def draft_aleatorio(estado, cantidad=3, facciones_extra=None):
    """Ofertas de draft ponderadas por rareza (mas comun, menos comun)."""
    from reglas import rareza

    pool = cartas_del_pool(estado, facciones_extra)
    pesos = {"LEGENDARIA": 2, "RARA": 5, "COMUN": 10}
    ofertas = []
    intentos = 0
    while len(ofertas) < cantidad and intentos < 80:
        intentos += 1
        c = random.choices(pool, weights=[pesos[rareza(c)[0]] for c in pool], k=1)[0]
        if c.nombre not in {o.nombre for o in ofertas}:
            ofertas.append(c.copia())
    return ofertas


def desbloquear_aliado(estado, faccion):
    if faccion in facciones.FACCIONES and faccion != estado["faccion"] and faccion not in estado.get("aliados", []):
        estado.setdefault("aliados", []).append(faccion)
        guardar(estado)
        return True
    return False


def sustituto_aliado(estado):
    """Faccion para pactar: rival ya derrotado, nunca la propia."""
    candidatos = [
        rival_de_nodo(estado, "senda"),
        rival_de_nodo(estado, estado.get("eleccion") or "aldea"),
        rival_de_nodo(estado, "fortaleza"),
    ] + escalera_de(estado["faccion"])
    for f in candidatos:
        if f and f != estado["faccion"] and f not in estado.get("aliados", []):
            return f
    for f in facciones.orden_facciones():
        if f != estado["faccion"] and f not in estado.get("aliados", []):
            return f
    return None


def draft_reemplazo(estado, carta, reemplazo):
    estado["cartas"][reemplazo] = carta.a_dict()
    guardar(estado)


def anadir_carta(estado, carta, reemplazo=None):
    """Anade una carta; si el mazo esta lleno sustituye la mas debil."""
    from reglas import total_carta

    cartas = estado["cartas"]
    if len(cartas) < 5:
        cartas.append(carta.a_dict())
    else:
        idx = (
            min(range(len(cartas)), key=lambda i: total_carta(Carta.desde_dict(cartas[i])))
            if reemplazo is None
            else reemplazo
        )
        cartas[idx] = carta.a_dict()
    guardar(estado)


# ------------------------------------------------------------------- encuentros


def encuentro_para(nodo_id):
    objetivo = ENCUENTRO_POR_NODO.get(nodo_id, "mercader")
    for enc in ENCUENTROS:
        if enc["id"] == objetivo:
            return enc
    return ENCUENTROS[0]


def aplicar_encuentro(estado, efecto):
    """Aplica una opcion de encuentro. Devuelve (titulo, texto)."""
    if efecto == "mejorar":
        return ("Mercader", "Pagaste con una carta y recibiste un punto mas de fuerza.")
    if efecto == "robo":
        carta = draft_aleatorio(estado, 1)[0]
        anadir_carta(estado, carta)
        return ("Mercader", f"Te llevas {carta.nombre} sin pagar nada.")
    if efecto == "mas_debil":
        cartas = cartas_jugador(estado)
        if cartas:
            idx = min(range(len(cartas)), key=lambda i: sum(cartas[i].valores.values()))
            lado = mejorar_carta(estado, idx)
            return ("Anciano", f"Su consejo: {cartas[idx].nombre} mas fuerte en {lado.upper()}.")
    if efecto == "debilitar":
        estado["debilitar"] = int(estado.get("debilitar", 0) or 0) + 1
        guardar(estado)
        return ("Anciano", "Murmura una maldicion: el rival llegara mas debil.")
    if efecto == "celebrar":
        cartas = cartas_jugador(estado)
        for i in sorted(range(len(cartas)), key=lambda i: sum(cartas[i].valores.values()))[:2]:
            mejorar_carta(estado, i)
        return ("Hermandad", "Cantan contigo: tus dos cartas mas debiles suben un punto.")
    if efecto == "sigilo":
        aplicar_sigilo(estado)
        return ("Hermandad", "Una noche junto al fuego: todas tus cartas suben un punto.")
    return ("Encuentro", "No ocurre nada.")


# -------------------------------------------------------------------- perfil


def perfil_por_defecto():
    return {
        "version": 1,
        "finales": {},
        "mejor_racha": {},
        "duelos": 0,
        "victorias": 0,
        "cinematicas": [],
    }


def cargar_perfil():
    try:
        with open(ruta_perfil(), encoding="utf-8") as f:
            datos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return perfil_por_defecto()
    base = perfil_por_defecto()
    if isinstance(datos, dict):
        base.update(datos)
    return base


def guardar_perfil(perfil):
    try:
        with open(ruta_perfil(), "w", encoding="utf-8") as f:
            json.dump(perfil, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def registrar_final_perfil(faccion, variante):
    perfil = cargar_perfil()
    variantes = set(perfil["finales"].get(faccion, []))
    nuevo = variante not in variantes
    variantes.add(variante)
    perfil["finales"][faccion] = sorted(variantes)
    guardar_perfil(perfil)
    return nuevo


def registrar_duelo_perfil(victoria, faccion=None, racha=0):
    perfil = cargar_perfil()
    perfil["duelos"] = perfil.get("duelos", 0) + 1
    if victoria:
        perfil["victorias"] = perfil.get("victorias", 0) + 1
    if faccion:
        if racha > perfil.setdefault("mejor_racha", {}).get(faccion, 0):
            perfil["mejor_racha"][faccion] = racha
    guardar_perfil(perfil)


def marcar_cinematica(cid):
    perfil = cargar_perfil()
    vistos = perfil.setdefault("cinematicas", [])
    nuevo = cid not in vistos
    if nuevo:
        vistos.append(cid)
    guardar_perfil(perfil)
    return nuevo


def cinematicas_vistas():
    return set(cargar_perfil().get("cinematicas", []))


def finales_desbloqueados():
    return cargar_perfil().get("finales", {})


def hay_campana():
    estado = cargar()
    return bool(estado) and not estado.get("completada")