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

import compendio
import duelistas
import encuentros
import facciones
import fragmentos
import mazos
from paths import archivo
from reglas import Carta

VERSION = 7
ARCHIVO_PARTIDA = "campana.json"
ARCHIVO_PERFIL = "perfil.json"

# --------------------------------------------------- estado narrativo (v7+)
# La v7 suma el pegamento narrativo de "Cartones y Mazmorras": el viaje desde
# el mundo real, la relacion con Nara y lo que el jugador descubre sobre el
# Umbral. Todo es opcional: una partida v6 migrada arranca en 0.
CAMPOS_NARRATIVOS = (
    "prologo_visto",       # bool: el jugador ya vio el prologo del mundo real
    "confianza_nara",      # 0..5
    "conocimiento_umbral", # 0..5
    "decisiones",          # lista de ids de decisiones morales tomadas
    "revelaciones",        # lista de fragmentos de verdad descubiertos
    "fragmentos",          # 0..10, progreso NG+ (se guarda en el perfil)
    "compendio",           # lista de cartas cuya verdad ya descubrio
)


def _narrativa_inicial():
    """Estado narrativo de partida nueva."""
    return {
        "prologo_visto": False,
        "confianza_nara": 0,
        "conocimiento_umbral": 0,
        "decisiones": [],
        "revelaciones": [],
        "fragmentos": 0,
        "compendio": [],
    }

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
    "elfo_nocturno": {
        "nombre": "Sylwen",
        "titulo": "Voz del Umbral",
        "entrada": "La sombra tambien sabe jugar.",
        "captura_player": "La noche se repliega... por ahora.",
        "captura_cpu": "Ni la luz te avisara.",
        "win": "El Umbral escucha a los suyos.",
        "lose": "Bien jugado. La sombra aprende.",
    },
    "hombre_pantera": {
        "nombre": "Zarkha",
        "titulo": "Cazadora Silente",
        "entrada": "Shh... ya empezo la caza.",
        "captura_player": "Grrr... me rozaste el lomo.",
        "captura_cpu": "Ni me viste venir.",
        "win": "La noche caza en silencio.",
        "lose": "Buena caza, forastero.",
    },
    "hombre_lagarto": {
        "nombre": "Sskar",
        "titulo": "Senor del Pantano",
        "entrada": "El fango te espera, viajero.",
        "captura_player": "El pantano cede... pero traga despacio.",
        "captura_cpu": "Quieto. Ya eres del pantano.",
        "win": "El pantano no perdona.",
        "lose": "Saliste del fango. Por hoy.",
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
    "mini_senda": "El Umbral Respira",
    "mini_nudo": "La Sombra se Cierra",
    "mini_trono": "Dueno del Umbral",
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

# Mini campanas: 3 duelos lineales para las facciones nuevas, sin mapa ni
# encuentros. Se desbloquean al completar la campana principal.
NODOS_MINI = {
    "mini_senda": {
        "tipo": "duelo",
        "titulo": "El Umbral Respira",
        "escena": "umbral",
        "dificultad": 1,
        "previa": ["El Umbral te reconoce: ya no eres un forastero."],
        "siguiente": "mini_nudo",
    },
    "mini_nudo": {
        "tipo": "duelo",
        "titulo": "La Sombra se Cierra",
        "escena": "estandartes",
        "dificultad": 2,
        "previa": ["Los estandartes se juntan. Todos saben tu nombre."],
        "siguiente": "mini_trono",
    },
    "mini_trono": {
        "tipo": "final",
        "titulo": "Dueno del Umbral",
        "escena": "trono",
        "dificultad": 3,
        "previa": ["Tres duelos te separan de ser leyenda. Este es el ultimo."],
        "siguiente": None,
    },
}

MINI_FINALES = {
    "elfo_nocturno": {
        "titulo": "VIGIA DEL UMBRAL",
        "lineas": [
            "Tres duelos y el Umbral ya no ruge: susurra tu nombre.",
            "Sylwen monta guardia donde la luz no llega.",
            "La sombra, por fin, tiene quien la cuide.",
        ],
    },
    "hombre_pantera": {
        "titulo": "LA MEJOR PRESA",
        "lineas": [
            "Tres duelos sin hacer ruido y el Umbral es territorio de caza.",
            "Zarkha no deja huellas: deja precedente.",
            "Cazar el Umbral: nadie lo habia intentado. Nadie lo repetira.",
        ],
    },
    "hombre_lagarto": {
        "titulo": "EL FANGO MANDA",
        "lineas": [
            "Tres duelos y el pantano llega hasta el Umbral.",
            "Sskar espera sentado: todo lo que se hunde, vuelve a el.",
            "El Umbral tambien es fango, solo que mas alto.",
        ],
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
    "elfo_nocturno": ["humano", "orco", "vampiro", "goblin", "elfo"],
    "hombre_pantera": ["goblin", "hombre_lobo", "humano", "orco", "vampiro"],
    "hombre_lagarto": ["orco", "goblin", "elfo", "vampiro", "humano"],
}

# ------------------------------------------------------------------ recompensas

RECOMPENSAS = {
    "senda": ["entrenamiento", "recluta"],
    "aldea": ["entrenamiento", "recluta", "sigilo"],
    "ruinas": ["recluta", "sigilo", "aliado", "sobre"],
    "fortaleza": ["entrenamiento", "sigilo", "aliado", "sobre"],
    "asalto": ["entrenamiento", "recluta", "sigilo", "sobre"],
    "trono": [],
}

TEXTO_RECOMPENSA = {
    "entrenamiento": "Entrenamiento: +1 a un lado de la carta que elijas.",
    "recluta": "Recluta: elige una de las tres cartas ofrecidas.",
    "sigilo": "Sigilo de guerra: +1 permanente al lado mas bajo de todas tus cartas.",
    "aliado": "Pacto: desbloquea el mazo de esa faccion para el draft.",
    "sobre": "Sobre: 3 cartas al azar con rareza ponderada.",
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
    {
        "id": "caravana",
        "titulo": "Caravana de Sobres",
        "escena": "campamento",
        "texto": "Una caravana vende sobres cerrados. - Todo el mundo paga. Casi todo el mundo gana.",
        "opciones": [
            {
                "id": "regatear",
                "texto": "Regatear un sobre (3 cartas al azar)",
                "efecto": "sobre",
            },
            {
                "id": "escoltar",
                "texto": "Escoltarla (+1 a tu carta mas debil)",
                "efecto": "mas_debil",
            },
        ],
    },
]

ENCUENTRO_POR_NODO = {
    "senda": "mercader",
    "aldea": "hermandad",
    "ruinas": "anciano",
    "fortaleza": "caravana",
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
    "elfo_nocturno": {
        "dominio": {
            "titulo": "LA SOMBRA CORONADA",
            "lineas": [
                "El Umbral se abre para quien lo miro sin parpadear.",
                "Sylwen no pide perdon al bosque: le trae un trono envuelto en noche.",
                "Donde antes habia exilio, ahora hay vigilia.",
            ],
        },
        "equilibrio": {
            "titulo": "PACTO DE PENUMBRA",
            "lineas": [
                "Ni luz ni sombra: un acuerdo a media voz con el bosque.",
                "Los elfos diurnos fingen que fue idea suya. Dejalos.",
                "La noche y el dia comparten la misma corona por turnos.",
            ],
        },
        "caos": {
            "titulo": "SIN LUNA QUE VOLVER",
            "lineas": [
                "Ganaste el trono pero la sombra te desconoce.",
                "Ni el bosque ni el Umbral reclaman tu victoria.",
                "Reinas sobre una penumbra que no te nombra.",
            ],
        },
    },
    "hombre_pantera": {
        "dominio": {
            "titulo": "LA CAZA PERFECTA",
            "lineas": [
                "Nadie vio llegar a Zarkha y nadie la vera irse: el trono ya es suyo.",
                "La manada de la sombra patrulla los tejados del mundo.",
                "El silencio, por fin, tiene dueno.",
            ],
        },
        "equilibrio": {
            "titulo": "TERRITORIO COMPARTIDO",
            "lineas": [
                "Fenris y Zarkha acuerdan turnos de luna: nadie muerde fuera de hora.",
                "El bosque aprende a dormir con un ojo abierto y el otro cerrado.",
                "Una tregua felina: dura mientras nadie corra.",
            ],
        },
        "caos": {
            "titulo": "PRESA DEL RUIDO",
            "lineas": [
                "Ganaste haciendo ruido y la selva lo apunta todo.",
                "Cada sombra esconde ahora otra sombra que te debe una.",
                "El trono es tuyo, pero dormir cuesta el doble.",
            ],
        },
    },
    "hombre_lagarto": {
        "dominio": {
            "titulo": "EL PANTANO REINA",
            "lineas": [
                "El fango llego al trono sin prisa y sin pedir permiso.",
                "Sskar no celebra: el pantano tampoco celebra, solo crece.",
                "Lo que el pantano traga, el pantano conserva.",
            ],
        },
        "equilibrio": {
            "titulo": "AGUAS QUIETAS",
            "lineas": [
                "Vorg acepta el pacto del fango: territorio por tributo.",
                "El pantano deja pasar caravanas y cobra peaje en silencio.",
                "La paz mas lenta del mundo tambien es la mas firme.",
            ],
        },
        "caos": {
            "titulo": "FANGO REVUELTO",
            "lineas": [
                "Tomaste el trono chapoteando y el reino lo noto.",
                "Cada faccion cuenta que el pantano los traiciono primero.",
                "Gobiernas, pero con el agua al cuello.",
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
    """Identidad del rival (por faccion) + su rol en la historia (por nodo).

    `DUELISTAS` da nombre, titulo y lineas: eso no se toca. `duelistas.ROLES`
    suma el rol (campesino, guardian, jefe_arco...), la motivacion y el
    dialogo propio del nodo.
    """
    d = dict(DUELISTAS.get(rival, {}))
    extra = TITULOS_NODO.get(nodo_id, "")
    if extra:
        d["titulo"] = extra
    # El rol puede traer su propia identidad (senda: un vecino, no un campeon).
    propia = duelistas.identidad_rol(nodo_id, rival)
    if propia:
        d["nombre"] = propia.get("nombre", d.get("nombre", ""))
        d["titulo"] = propia.get("titulo", d.get("titulo", ""))
        d["bando"] = rival
        d["entrada"] = ""
    rol = duelistas.rol_de(nodo_id)
    if rol:
        d["rol"] = rol.get("rol", "")
        d["personalidad"] = rol.get("personalidad", "")
        d["motivacion"] = rol.get("motivacion", "")
        d["historia"] = rol.get("historia", "")
    return d


def nueva_campana(faccion="humano", mazo=None):
    """Nueva run. Sin mazo dado usa las iniciales (determinista, tests y minis);
    el juego real pasa una copia del mazo global."""
    if mazo is None:
        mazo = [c.a_dict() for c in mazo_inicial(faccion)]
    estado = {
        "version": VERSION,
        "faccion": faccion,
        "nodo": "senda",
        "ruta": [],
        "eleccion": None,
        "cartas": [dict(d) for d in mazo],
        "semilla": random.getrandbits(64),
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
    estado.update(_narrativa_inicial())
    return estado


def nueva_mini_campana(faccion):
    """Mini campana de 3 duelos para las facciones nuevas. Solo vive en memoria."""
    estado = nueva_campana(faccion, [c.a_dict() for c in mazo_inicial(faccion)])
    estado.update({
        "mini": True,
        "nodo": "mini_senda",
        "ruta": [],
        "_archivo": None,
    })
    return estado


# ---------------------------------------------------------------- persistencia


def ruta_partida():
    return archivo(ARCHIVO_PARTIDA)


ARCHIVO_MINI = "mini.json"


def ruta_mini():
    return archivo(ARCHIVO_MINI)


def guardar(estado, ruta=None):
    # Las mini campanas viven solo en memoria (sin continuar entre sesiones):
    # con _archivo None no se escribe nada y no se pisa campana.json.
    ruta = estado.get("_archivo", ruta_partida()) if ruta is None else ruta
    if ruta is None:
        return
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def ruta_perfil():
    return archivo(ARCHIVO_PERFIL)


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
    """Convierte partidas viejas al formato actual (reset total de coleccion)."""
    if not isinstance(datos, dict):
        return None
    if datos.get("version") == VERSION:
        return datos
    if datos.get("version") in (3, 4, 5, 6):
        nuevo = datos
    else:
        faccion = datos.get("mazo_jugador", "humano")
        if faccion not in facciones.FACCIONES:
            faccion = "humano"
        nuevo = nueva_campana(faccion)
        etapa = int(datos.get("etapa", 0) or 0)
        orden = ["senda", "bifurcacion", "fortaleza", "asalto", "trono"]
        nuevo["nodo"] = orden[min(etapa, len(orden) - 1)]
        nuevo["mejor_racha"] = int(datos.get("racha", 0) or 0)
        if etapa >= 5 and datos.get("completada"):
            nuevo["completada"] = True
    nuevo.setdefault("semilla", random.getrandbits(64))
    # v7: pegamento narrativo. Una partida vieja arranca sin prologo visto y
    # con la relacion con Nara en cero.
    for campo, valor in _narrativa_inicial().items():
        nuevo.setdefault(campo, valor)
    # reset total (v5): la coleccion jugable son las 10 iniciales; el resto
    # se descubre con sobres y draft. El progreso de nodos se conserva.
    faccion = nuevo.get("faccion", "humano")
    if faccion not in facciones.FACCIONES:
        faccion = "humano"
        nuevo["faccion"] = faccion
    nuevo["cartas"] = [c.a_dict() for c in mazo_inicial(faccion)]
    nuevo["mejoras"] = {}
    nuevo["version"] = VERSION
    return nuevo


# ------------------------------------------------------- helpers de narrativa


def marcar_prologo_visto(estado):
    """El jugador ya vio el prologo del mundo real."""
    estado["prologo_visto"] = True


def prologo_visto(estado):
    return bool(estado.get("prologo_visto"))


def confianza_nara(estado):
    return int(estado.get("confianza_nara", 0) or 0)


def subir_confianza_nara(estado, delta=1, maximo=5):
    """Suma confianza con tope. Devuelve el valor nuevo."""
    nuevo = max(0, min(maximo, confianza_nara(estado) + delta))
    estado["confianza_nara"] = nuevo
    return nuevo


def nara_aliada(estado):
    """Nara ya no observa: acompaña. A partir de 3 puntos de confianza."""
    return confianza_nara(estado) >= 3


def conocimiento_umbral(estado):
    return int(estado.get("conocimiento_umbral", 0) or 0)


def subir_conocimiento(estado, delta=1, maximo=5):
    """Suma conocimiento del Umbral con tope. Devuelve el valor nuevo."""
    nuevo = max(0, min(maximo, conocimiento_umbral(estado) + delta))
    estado["conocimiento_umbral"] = nuevo
    return nuevo


def registrar_decision(estado, id_decision):
    """Anota una decision moral. No la duplica si ya estaba."""
    decisiones = estado.setdefault("decisiones", [])
    if id_decision not in decisiones:
        decisiones.append(id_decision)
    return decisiones


def decidir(estado, id_decision, efecto=None):
    """Registra una decision y aplica su efecto en las variables narrativas.

    `efecto` es un dict con claves opcionales:
        confianza   -> delta para confianza_nara
        conocimiento -> delta para conocimiento_umbral
        revelacion  -> str, fragmento de verdad descubierto
    """
    registrar_decision(estado, id_decision)
    efecto = efecto or {}
    if "confianza" in efecto:
        subir_confianza_nara(estado, efecto["confianza"])
    if "conocimiento" in efecto:
        subir_conocimiento(estado, efecto["conocimiento"])
    revelacion = efecto.get("revelacion")
    if revelacion:
        revelar(estado, revelacion)
    return efecto


def revelar(estado, id_revelacion):
    """Anota un fragmento de verdad descubierto (para el Compendio)."""
    revelaciones = estado.setdefault("revelaciones", [])
    if id_revelacion not in revelaciones:
        revelaciones.append(id_revelacion)
    return revelaciones


def revelado(estado, id_revelacion):
    return id_revelacion in estado.get("revelaciones", [])


# ------------------------------------------------------------- compendio dual


def compendio_revelar(estado, nombre_carta):
    """Revela la verdad de una carta en la partida. Devuelve la entrada, o None."""
    antes = len(estado.get("compendio") or [])
    entrada = compendio.revelar(estado, nombre_carta)
    if entrada and len(estado["compendio"]) > antes:
        # descubrir una verdad concreta es entender mas del Umbral
        subir_conocimiento(estado, 1)
    return entrada


def compendio_revelada(estado, nombre_carta):
    return compendio.revelada(estado, nombre_carta)


def compendio_progreso(estado):
    """(descubiertas, total). El texto de la pantalla usa esto."""
    return compendio.progreso(estado)


def compendio_historias(estado):
    """Las cartas cuya verdad ya conoce, para la pantalla de coleccion."""
    return list(estado.get("compendio") or [])


def progreso(estado):
    """0..1 segun los duelos superados."""
    return min(1.0, len(estado.get("ruta", [])) / 5.0)


# ------------------------------------------------------------------- recorrido


def nodo_actual(estado):
    return estado.get("nodo") or "senda"


def nodo(nodo_id):
    if nodo_id in NODOS_MINI:
        return NODOS_MINI[nodo_id]
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
    if estado.get("mini"):
        escalera = escalera_de(faccion)
        if nodo_id == "mini_senda":
            rival = escalera[0]
        elif nodo_id == "mini_nudo":
            rival = escalera[1 % len(escalera)]
        else:
            rival = facciones.rival_final(faccion)
    elif nodo_id == "senda":
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
        # pegamento narrativo (v7): lo que necesitan las escenas para reaccionar
        "faccion_jugador": estado.get("faccion"),
        "confianza_nara": int(estado.get("confianza_nara", 0) or 0),
        "conocimiento_umbral": int(estado.get("conocimiento_umbral", 0) or 0),
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
        # rol en la historia (v7): quien es y por que pelea
        "rol": duelo.get("rol", ""),
        "personalidad": duelo.get("personalidad", ""),
        "motivacion": duelo.get("motivacion", ""),
        "historia": duelo.get("historia", ""),
        "reaccion_rol": duelistas.reaccion_rol(nodo_id, estado.get("faccion", "")),
        "dialogo_pre": duelistas.dialogo_de(nodo_id, "pre",
                                            duelo.get("nombre", ""),
                                            nombre_jugador()),
        # Que retrato se dibuja en la PANTALLA del duelo. Antes se usaba
        # siempre el de la faccion y por eso Juan Rajoy salia como un humano
        # cualquiera: `partida.py` pedia `avatar_<bando>`. Con esta clave la
        # pantalla puede mostrar a la persona, no al bando.
        "retrato": duelistas.retrato_de(nodo_id, rival),
        # Como se llama el jugador, ya saneado. Lo leen el HUD del duelo, el
        # cartel previo y las escenas posteriores.
        "nombre_jugador": nombre_jugador(),
    }


def mazo_rival(estado, nodo_id=None, dificultad_extra=0):
    """5 cartas sorteadas del mazo rival, potenciadas segun dificultad.

    El efecto `debilitar` de los encuentros resta: el rival llega mas flojo.
    El sorteo es determinista (semilla + nodo + intentos): recargar no
    re-sortea, pero cada campana e intento varian.
    """
    info = info_duelo(estado, nodo_id)
    nivel = info["dificultad"] + dificultad_extra - int(estado.get("debilitar", 0) or 0)
    cartas = [c.copia() for c in mazos.TODOS[info["bando"]]]
    rng = random.Random((_semilla(estado["faccion"]) + sum(ord(c) for c in info["nodo"])) % 999983)
    for c in cartas:
        for lado in ("N", "S", "E", "O"):
            if c.valores[lado] < 10 and nivel > 0 and rng.random() < 0.7:
                c.valores[lado] += min(nivel, 10 - c.valores[lado])
    if len(cartas) > 5:
        rng_sorteo = _rng_sorteo(estado, info["nodo"], extra=1)
        cartas = [c.copia() for c in rng_sorteo.sample(cartas, 5)]
    return cartas


def cartas_jugador(estado):
    """Toda la coleccion del jugador (10+ cartas, nunca la mano del duelo)."""
    return [Carta.desde_dict(d, estado["faccion"]) for d in estado["cartas"]]


def _rng_sorteo(estado, nodo_id, extra=0):
    """Azar estable por campana, nodo e intento: varia siempre, repite al cargar."""
    base = int(estado.get("semilla", 0) or 0)
    intentos = int(estado.get("victorias", 0) or 0) + int(estado.get("derrotas", 0) or 0)
    semilla = (base + sum(ord(c) for c in str(nodo_id)) * 131
               + intentos * 17 + extra) % (2 ** 63 - 1)
    return random.Random(semilla)


def cartas_duelo(estado, nodo_id=None):
    """Las 5 que tocan en este duelo, sorteadas del mazo con deltas aplicados."""
    pool = cartas_jugador(estado)
    deltas = mejoras_de(estado)
    mano = []
    for c in pool:
        copia = c.copia()
        extra = deltas.get(c.nombre, {})
        for lado in ("N", "S", "E", "O"):
            copia.valores[lado] = min(10, copia.valores[lado] + int(extra.get(lado.lower(), 0) or 0))
        mano.append(copia)
    if len(mano) <= 5:
        return mano
    rng = _rng_sorteo(estado, nodo_id or nodo_actual(estado))
    return [c.copia() for c in rng.sample(mano, 5)]


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
    estado["mejoras"] = {}
    guardar(estado)
    nuevo = registrar_final_perfil(estado["faccion"], variante)
    estado["final"]["nuevo"] = nuevo
    guardar(estado)
    return estado["final"]


# ------------------------------------------------------------------- recompensas


def recompensas_de(nodo_id):
    return list(RECOMPENSAS.get(nodo_id, ["entrenamiento", "recluta"]))


def aplicar_sigilo(estado):
    """+1 temporal al lado mas bajo efectivo de cada carta del mazo."""
    deltas = mejoras_de(estado)
    for d in estado["cartas"]:
        efectivo = {l: min(10, d[l] + int(deltas.get(d["nombre"], {}).get(l, 0) or 0))
                    for l in ("n", "s", "e", "o")}
        candidatos = [l for l in ("n", "s", "e", "o") if efectivo[l] < 10]
        if candidatos:
            registrar_mejora(estado, d["nombre"], min(candidatos, key=lambda l: efectivo[l]))
    estado["sigilos"] = estado.get("sigilos", 0) + 1
    guardar(estado)


def otorgar_base(nombre, datos=None):
    """Registra la carta en la coleccion permanente (valores base)."""
    perfil = cargar_perfil()
    coleccion = perfil.setdefault("coleccion", {})
    if nombre not in coleccion and isinstance(datos, dict):
        coleccion[nombre] = {k: datos[k] for k in ("nombre", "n", "s", "e", "o", "bando", "habilidad") if k in datos}
        guardar_perfil(perfil)
        return True
    return False


def mejorar_base(nombre, puntos=1):
    """+1 permanente al lado mas bajo de la base poseida (duplicadas)."""
    perfil = cargar_perfil()
    d = perfil.get("coleccion", {}).get(nombre)
    if not isinstance(d, dict):
        return False
    lado = min(("n", "s", "e", "o"), key=lambda l: d[l])
    if d[lado] >= 10:
        return False
    d[lado] = min(10, d[lado] + int(puntos))
    guardar_perfil(perfil)
    return True


def registrar_mejora(estado, nombre, lado, puntos=1):
    """Delta temporal de campana: vive en estado["mejoras"], no en la base."""
    deltas = estado.setdefault("mejoras", {}).setdefault(nombre, {})
    deltas[lado] = int(deltas.get(lado, 0) or 0) + int(puntos)
    guardar(estado)
    return lado


def mejoras_de(estado):
    deltas = estado.get("mejoras")
    return dict(deltas) if isinstance(deltas, dict) else {}


def valor_con_mejoras(datos, deltas_nombre):
    """Valores base + deltas con tope 10."""
    return {l: min(10, int(datos[l]) + int(deltas_nombre.get(l, 0) or 0))
            for l in ("n", "s", "e", "o")}


def mejorar_carta(estado, id_carta, lado=None):
    """Sube +1 (max 10) como delta temporal de la campana en curso."""
    d = estado["cartas"][id_carta]
    deltas = mejoras_de(estado).get(d["nombre"], {})
    efectivo = {l: min(10, d[l] + int(deltas.get(l, 0) or 0)) for l in ("n", "s", "e", "o")}
    if lado and efectivo[lado] < 10:
        registrar_mejora(estado, d["nombre"], lado)
        return lado
    candidatos = [l for l in ("n", "s", "e", "o") if efectivo[l] < 10]
    if not candidatos:
        return None
    elegido = min(candidatos, key=lambda l: efectivo[l])
    registrar_mejora(estado, d["nombre"], elegido)
    return elegido


def cartas_del_pool(estado, facciones_extra=None):
    """Pool de draft: faccion del jugador mas aliados desbloqueados."""
    permitidas = {estado["faccion"]}
    permitidas.update(estado.get("aliados", []))
    if facciones_extra:
        permitidas.update(facciones_extra)
    return [c for bando, cartas in mazos.TODOS.items() if bando in permitidas for c in cartas]


MAZO_INICIAL_N = 10

MONEDA_VICTORIA = 20
MONEDA_POR_CAPTURA = 2
MONEDA_POR_DUELO = 5


def mazo_global(perfil=None):
    """El mazo global del jugador (nombres). Solo vive en el perfil."""
    perfil = perfil if perfil is not None else cargar_perfil()
    mazo = perfil.get("mazo")
    return list(mazo) if isinstance(mazo, list) else []


def guardar_mazo_global(nombres, perfil=None):
    perfil = cargar_perfil() if perfil is None else perfil
    perfil["mazo"] = list(nombres)
    guardar_perfil(perfil)
    return perfil["mazo"]


def ritual_inicial():
    """Rito inicial: 5 cartas al azar de todo el catalogo + mazo con ellas."""
    import mazos

    catalogo = [c for cartas in mazos.TODOS.values() for c in cartas]
    elegidas = random.sample(catalogo, 5)
    perfil = cargar_perfil()
    coleccion = perfil.setdefault("coleccion", {})
    for c in elegidas:
        coleccion.setdefault(c.nombre, dict(c.a_dict()))
    perfil["mazo"] = [c.nombre for c in elegidas]
    guardar_perfil(perfil)
    return perfil["mazo"]


def asegurar_mazo_global():
    """Deja coleccion y mazo en estado jugable: ritual si esta vacio,
    repara el mazo si quedo invalido (cartas que ya no posee)."""
    from reglas import rareza, Carta

    perfil = cargar_perfil()
    coleccion = coleccion_de(perfil)
    if not coleccion:
        ritual_inicial()
        return mazo_global()
    mazo = [n for n in mazo_global(perfil) if n in coleccion]
    ok, _ = validar_mazo([dict(coleccion[n]) for n in mazo], set(coleccion)) if mazo else (False, "")
    if not ok:
        ordenadas = sorted(coleccion, key=lambda n: (
            rareza(Carta.desde_dict(coleccion[n]))[0] != "COMUN",
            sum(coleccion[n][l] for l in "nseo"), n))
        mazo = ordenadas[:MAZO_MIN_N]
        guardar_mazo_global(mazo, perfil)
    return mazo_global()


def mazo_inicial(faccion):
    """Las 10 cartas de menor total de la faccion (referencia y minis)."""
    from reglas import total_carta

    return sorted(mazos.TODOS[faccion], key=total_carta)[:MAZO_INICIAL_N]


def coleccion_inicial(faccion):
    """Coleccion base: valores base de las 10 iniciales, listas para mejorar."""
    base = {}
    for c in mazo_inicial(faccion):
        base[c.nombre] = dict(c.a_dict())
    return base


def asegurar_coleccion(faccion):
    """Otorga el mazo inicial de la faccion si falta alguna pieza."""
    perfil = cargar_perfil()
    coleccion = perfil.setdefault("coleccion", {})
    for nombre, datos in coleccion_inicial(faccion).items():
        coleccion.setdefault(nombre, datos)
    guardar_perfil(perfil)
    return coleccion


def coleccion_de(perfil=None):
    perfil = perfil if perfil is not None else cargar_perfil()
    coleccion = perfil.get("coleccion")
    return dict(coleccion) if isinstance(coleccion, dict) else {}


def posee(perfil, nombre):
    return nombre in coleccion_de(perfil)


def moneda(perfil=None):
    perfil = perfil if perfil is not None else cargar_perfil()
    return int(perfil.get("moneda", 0) or 0)


def ganar_moneda(cantidad, perfil=None):
    """Suma moneda al perfil. Devuelve el nuevo total."""
    perfil = cargar_perfil() if perfil is None else perfil
    perfil["moneda"] = int(perfil.get("moneda", 0) or 0) + int(cantidad)
    guardar_perfil(perfil)
    return perfil["moneda"]


def gastar_moneda(cantidad, perfil=None):
    """Resta moneda si alcanza. Devuelve True si se pudo pagar."""
    perfil = cargar_perfil() if perfil is None else perfil
    total = int(perfil.get("moneda", 0) or 0)
    if total < cantidad:
        return False
    perfil["moneda"] = total - int(cantidad)
    guardar_perfil(perfil)
    return True


def premio_duelo(estado, victoria, capturas):
    """Moneda por un duelo completado: base + victoria + capturas."""
    total = MONEDA_POR_DUELO + (MONEDA_VICTORIA if victoria else 0)
    total += MONEDA_POR_CAPTURA * int(capturas or 0)
    ganar_moneda(total)
    return total


LIMITE_LEGENDARIAS = 1
LIMITE_RARAS = 3
MAZO_RUN_N = 10
MAZO_MIN_N = 5


def validar_mazo(lista_dicts, poseidas):
    """Valida un mazo global: de 5 a 10 poseidas, 1 LEG y 3 RARA como maximo."""
    from reglas import rareza, Carta

    if not MAZO_MIN_N <= len(lista_dicts) <= MAZO_RUN_N:
        return False, f"El mazo necesita de {MAZO_MIN_N} a {MAZO_RUN_N} cartas ({len(lista_dicts)})"
    for d in lista_dicts:
        if d.get("nombre") not in poseidas:
            return False, f"{d.get('nombre')} no es tuya"
    rarezas = [rareza(Carta.desde_dict(d))[0] for d in lista_dicts]
    if rarezas.count("LEGENDARIA") > LIMITE_LEGENDARIAS:
        return False, f"Maximo {LIMITE_LEGENDARIAS} legendaria"
    if rarezas.count("RARA") > LIMITE_RARAS:
        return False, f"Maximo {LIMITE_RARAS} raras"
    return True, ""


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


PESOS_SOBRE = {"LEGENDARIA": 2, "RARA": 6, "COMUN": 12}

PRECIO_SOBRE = 60
PITY_SOBRES = 10


def pity_sobres(perfil=None):
    perfil = perfil if perfil is not None else cargar_perfil()
    return int(perfil.get("pity_sobres", 0) or 0)


def abrir_sobre(estado, cantidad=3):
    """Abre un sobre: `cantidad` cartas de TODO el catalogo con los pesos.

    La carta nueva entra en la coleccion (y en el mazo de run si cabe);
    la repetida da +1 a su lado mas bajo (max 10). Pity: cada 9 sobres sin
    legendaria, el siguiente trae una garantizada. `estado` puede ser None
    (tienda del menu): entonces no hay mazo de run que ampliar.
    Devuelve (nuevas, mejoradas) con los nombres.
    """
    import mazos
    from reglas import rareza

    pool = [c for cartas in mazos.TODOS.values() for c in cartas]
    legendarias = [c for c in pool if rareza(c)[0] == "LEGENDARIA"]
    perfil = cargar_perfil()
    pity = pity_sobres(perfil)
    ofertas = []
    intentos = 0
    while len(ofertas) < cantidad and intentos < 80:
        intentos += 1
        c = random.choices(pool, weights=[PESOS_SOBRE[rareza(c)[0]] for c in pool], k=1)[0]
        if c.nombre not in {o.nombre for o in ofertas}:
            ofertas.append(c.copia())
    if pity >= PITY_SOBRES - 1 and legendarias:
        elegida = random.choice(legendarias).copia()
        if elegida.nombre in {o.nombre for o in ofertas}:
            ofertas = [o for o in ofertas if o.nombre != elegida.nombre]
        ofertas = ([elegida] + ofertas)[:cantidad]
    nuevas, mejoradas = [], []
    hay_leg = any(rareza(o)[0] == "LEGENDARIA" for o in ofertas)
    coleccion = coleccion_de(perfil)
    mazo_run = estado["cartas"] if estado is not None else None
    for c in ofertas:
        if c.nombre in coleccion:
            mejorar_base(c.nombre)
            mejoradas.append(c.nombre)
        else:
            otorgar_base(c.nombre, c.a_dict())
            coleccion[c.nombre] = c.a_dict()
            if mazo_run is not None and len(mazo_run) < MAZO_RUN_N:
                mazo_run.append(c.a_dict())
            nuevas.append(c.nombre)
    perfil = cargar_perfil()
    perfil["pity_sobres"] = 0 if hay_leg else pity + 1
    guardar_perfil(perfil)
    if estado is not None:
        guardar(estado)
    return nuevas, mejoradas


def comprar_sobre(estado):
    """Compra un sobre con moneda. Devuelve (ok, nuevas, mejoradas)."""
    if not gastar_moneda(PRECIO_SOBRE):
        return False, [], []
    return True, *abrir_sobre(estado)


def cartas_por_nombre(estado, nombres):
    """Cartas localizadas por nombre (catalogo completo)."""
    import mazos

    pool = {c.nombre: c for cartas in mazos.TODOS.values() for c in cartas}
    return [pool[n].copia() for n in nombres if n in pool]


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
    otorgar_base(carta.nombre, carta.a_dict())
    estado["cartas"][reemplazo] = carta.a_dict()
    guardar(estado)


def anadir_carta(estado, carta, reemplazo=None):
    """Anade una carta; si el mazo esta lleno sustituye la mas debil."""
    from reglas import total_carta

    otorgar_base(carta.nombre, carta.a_dict())
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


def encuentro_para(nodo_id, enc_id=None):
    """Encuentro de un nodo.

    `enc_id` permite pedir uno concreto (los opcionales `hostil` y `nara` no
    estan en el mapa de nodos: se ofrecen aparte).
    """
    objetivo = enc_id or ENCUENTRO_POR_NODO.get(nodo_id, "mercader")
    for enc in ENCUENTROS:
        if enc["id"] == objetivo:
            return enc
    extra = encuentros._datos_extra(objetivo)
    if extra:
        return dict(extra)
    return ENCUENTROS[0]


def revelation_ids():
    """Revelaciones de Compendio que aportan los 6 tipos de encuentro."""
    return [d["revelacion"] for d in encuentros.LORE.values() if d.get("revelacion")]


def revelar_encuentro(estado, enc_id):
    """Registra la revelacion de un encuentro. Devuelve sus datos, o None.

    El encuentro ya dio su recompensa mecanica; esto es la otra mitad: lo que
    el jugador aprende del mundo. No se repite en la misma partida.
    """
    datos = encuentros.lore_de(enc_id)
    revelacion = datos.get("revelacion")
    if not revelacion:
        return None
    if revelado(estado, revelacion):
        return None
    # Descubrir algo del mundo es, ademas, entender mas del Umbral.
    revelar(estado, revelacion)
    subir_conocimiento(estado, 1)
    return {"titulo": datos.get("titulo", ""),
            # `linea` en el LORE es una LISTA de frases y se queda como lista
            # para quien quiera todas. Para pintar hace falta un texto: se
            # entrega ya unida. Antes se devolvia la lista y `pantallas` la
            # pasaba a `cartel`, que reventaba con
            # `TypeError: unhashable type: 'list'` al revealedor el primer
            # encuentro de cada partida.
            "linea": " ".join(datos.get("linea", [])).strip(),
            "lineas": list(datos.get("linea", [])),
            "id": revelacion}


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
    if efecto == "sobre":
        nuevas, mejoradas = abrir_sobre(estado)
        partes = []
        if nuevas:
            partes.append(f"nuevas: {', '.join(nuevas)}")
        if mejoradas:
            partes.append(f"duplicadas (+1): {', '.join(mejoradas)}")
        return ("Caravana", f"Abres el sobre: {'; '.join(partes) or 'vacio'}.")
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


#: Como se llama el jugador cuando no pone nombre. El juego siempre lo ha
#: llamado asi a proposito (el protagonista no tenia nombre); ahora se puede
#: cambiar, pero vacio sigue siendo valido y es el mismo texto que antes.
NOMBRE_POR_DEFECTO = "el duelista"

#: Tope de longitud. A 15 caben las cajas de dialogo de cuatro lineas y el HUD
#: sin que se desborde nada; a mas habria que recortar al pintar.
NOMBRE_MAX = 15


def sanea_nombre(bruto, defecto=NOMBRE_POR_DEFECTO):
    """Limpia lo que el jugador escribe y lo deja presentable.

    - `<`, `>` y las comillas rompen el motor de etiquetas del renderizador.
    - Los saltos de linea y los tabuladores descuadran las cajas de dialogo.
    - Se colapsan los espacios y se recorta a `NOMBRE_MAX`.
    - Si no queda nada usable, se devuelve el defecto, para que nunca salga
      un nombre vacio por ahi.
    """
    if not isinstance(bruto, str):
        return defecto
    limpio = "".join(" " if ch in "<>\n\r\t" else ch for ch in bruto)
    limpio = " ".join(limpio.split())[:NOMBRE_MAX].strip()
    return limpio or defecto


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


def perfil_por_defecto():
    return {
        "version": 1,
        "finales": {},
        "mejor_racha": {},
        "duelos": 0,
        "victorias": 0,
        "cinematicas": [],
        "coleccion": {},
        "moneda": 0,
        "mazo": [],
        "tutorial_visto": False,
        "tutorial_completado": False,
        "tutorial_paso": 0,
        # NG+: fragmentos de la verdad, uno por faccion completada. Vive en el
        # perfil (no en la partida) porque las mini campanas son en memoria.
        "fragmentos": [],
        # Lo que el jugador escribe al empezar. Vacio significa "el duelista",
        # que es como lo llamaba el juego antes de que esto existiera.
        "nombre_jugador": "",
    }


#: Cache del nombre del jugador. `info_duelo` se llama POR FRAME (la pantalla
#: de elegir rama dibuja las dos ramas en cada frame) y leer `perfil.json` cada
#: vez costaba 0,65 ms: dos veces por frame son 1,3 ms, el 8% del presupuesto de
#: 16,67 ms, solo para una cadena que cambia una vez por partida. Se lee una vez
#: y se invalida al escribir.
_NOMBRE_CACHE = None


def invalidar_nombre():
    """Olvida el nombre cacheado. Se llama si el perfil cambia por fuera."""
    global _NOMBRE_CACHE
    _NOMBRE_CACHE = None


def nombre_jugador():
    """El nombre guardado, ya saneado. Nunca devuelve cadena vacia."""
    global _NOMBRE_CACHE
    if _NOMBRE_CACHE is None:
        _NOMBRE_CACHE = sanea_nombre(cargar_perfil().get("nombre_jugador"))
    return _NOMBRE_CACHE


def nombre_guardado():
    """El nombre CRUDO tal como esta en el perfil, o `""` si no hay.

    Es el que hay que pasar a la pantalla de entrada como valor inicial. Usar
    `nombre_jugador()` ahi precargaria "el duelista" en el campo, y con solo
    pulsar ENTER se guardaria como si el jugador se hubiera elegido ese nombre:
    `tiene_nombre()` pasaria a True sin que nadie escribiera nada.
    """
    return str(cargar_perfil().get("nombre_jugador") or "")


def establecer_nombre(bruto):
    """Guarda el nombre en el perfil y devuelve el que ha quedado."""
    global _NOMBRE_CACHE
    perfil = cargar_perfil()
    perfil["nombre_jugador"] = sanea_nombre(bruto, defecto="")
    guardar_perfil(perfil)
    # La cache se rellena con el valor ya saneado de verdad, no con el defecto:
    # `nombre_jugador()` devuelve "el duelista" si esta vacio.
    _NOMBRE_CACHE = perfil["nombre_jugador"] or NOMBRE_POR_DEFECTO
    return perfil["nombre_jugador"]


def tiene_nombre():
    """True si el jugador ha escrito un nombre propio.

    No usa `cargar_perfil`: seria una lectura de disco por llamada, y esto se
    consulta desde menus, no desde un bucle.
    """
    return bool(cargar_perfil().get("nombre_jugador"))


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


def tutorial_estado():
    """(visto, completado, paso) del tutorial. Paso = proxima practica (0-4)."""
    perfil = cargar_perfil()
    return (
        bool(perfil.get("tutorial_visto", False)),
        bool(perfil.get("tutorial_completado", False)),
        int(perfil.get("tutorial_paso", 0) or 0),
    )


def tutorial_visto():
    return tutorial_estado()[0]


def marcar_tutorial(visto=None, completado=None, paso=None):
    perfil = cargar_perfil()
    if visto is not None:
        perfil["tutorial_visto"] = bool(visto)
    if completado is not None:
        perfil["tutorial_completado"] = bool(completado)
    if paso is not None:
        perfil["tutorial_paso"] = int(paso)
    guardar_perfil(perfil)


def finales_desbloqueados():
    return cargar_perfil().get("finales", {})


def mini_desbloqueada():
    """Hay mini campanas si alguna campana principal se completo."""
    return bool(cargar_perfil().get("finales"))


def registrar_mini_final(faccion):
    """Guarda el final de mini campana. Devuelve True si es nuevo."""
    perfil = cargar_perfil()
    conseguidos = perfil.setdefault("mini_finales", {})
    nuevo = faccion not in conseguidos
    conseguidos[faccion] = MINI_FINALES[faccion]["titulo"]
    guardar_perfil(perfil)
    return nuevo


def mini_finales_desbloqueados():
    return cargar_perfil().get("mini_finales", {})


# ------------------------------------------------------ fragmentos de verdad
# El NG+ no se cuenta en la partida: se cuenta en el perfil, porque las mini
# campanas viven solo en memoria y se pierden al cerrar el juego.


def fragmentos_obtenidos(perfil=None):
    """Ids de los fragmentos de la verdad ya encontrados."""
    if perfil is None:
        perfil = cargar_perfil()
    return list(perfil.get("fragmentos", []))


def registrar_fragmento(faccion, perfil=None):
    """Guarda el fragmento de una faccion. Devuelve (nuevo, datos).

    Cada faccion completada aporta un fragmento; con los 10 aparece El
    Cartografo, que nunca estuvo entre las 250 cartas.
    """
    datos = fragmentos.fragmento(faccion)
    if not datos:
        return False, None
    if perfil is None:
        perfil = cargar_perfil()
    lista = perfil.setdefault("fragmentos", [])
    nuevo = datos["id"] not in lista
    if nuevo:
        lista.append(datos["id"])
        guardar_perfil(perfil)
    return nuevo, datos


def progreso_fragmentos(perfil=None):
    """(encontrados, total) para la pantalla de NG+."""
    return fragmentos.progreso_fragmentos(fragmentos_obtenidos(perfil))


def secreto_desbloqueado(perfil=None):
    """Con 10/10 fragmentos, el que escribio las cartas se deja ver."""
    return fragmentos.secreto_desbloqueado(fragmentos_obtenidos(perfil))


def fragmentos_texto(perfil=None):
    """Los fragmentos encontrados, listos para mostrar (en orden de NG+)."""
    return fragmentos.fragmentos_de(fragmentos_obtenidos(perfil))


def mazo_rival_secreto():
    """Mazo de El Cartografo.

    No pertenece a ninguna faccion, asi que no puede salir de una escalera.
    Usa el mejor pool del juego (dragones) con la dificultad al maximo: es el
    duelo mas duro de la partida.
    """
    cartas = [c.copia() for c in mazos.DRAGONES]
    for c in cartas:
        for lado in ("N", "S", "E", "O"):
            if c.valores[lado] < 10:
                c.valores[lado] += 1
    # Se quedan las 5 mas fuertes: el duelo final no puede depender del azar.
    cartas.sort(key=lambda c: (sum(c.valores.values()), c.nombre), reverse=True)
    return cartas[:5]


def hay_campana():
    estado = cargar()
    return bool(estado) and not estado.get("completada")