"""Tutorial jugable: manual visual + 4 practicas guiadas.

Se entra desde la puerta de primer arranque (main) o desde el boton
TUTORIAL del menu. Saltar (ESC o boton) marca `tutorial_visto` en el
perfil y nunca vuelve a preguntar; el boton del menu queda para repasar.

Las practicas usan el motor real (`reglas.py`) dentro de un `Juego` de
`partida.py` con una `Guia` inyectada: el duelo no pone CPU ni comprueba
el fin; cada paso valida la jugada y explica por que vale o no.
"""

import asyncio
import copy
import math
import time

import pygame

import audio
import campana
import cartas as crt
import facciones
import ui
from partida import Juego, partida
from reglas import CPU, HABILIDADES, USUARIO, Carta, capturas
from ui import (
    ALTO,
    ANCHO,
    AZUL,
    BORDE,
    CARD_H,
    CARD_W,
    DORADO,
    LIMIT_FPS,
    PANEL,
    ROJO,
    TEXTO,
    TEXTO_ON,
    TEXTO_TENUE,
    VERDE,
    Boton,
    FondoAnimado,
    celda_rect,
    envolver,
    fundido_entrada,
    panel,
    parrafo,
    resplandor,
    texto,
)


# ------------------------------------------------------------------ datos
def _carta(spec, dueno=None):
    """Carta desde un dict de practica/demo."""
    c = Carta(
        spec["nombre"], spec["n"], spec["s"], spec["e"], spec["o"],
        bando=spec.get("bando", "humano"),
        habilidad=spec.get("habilidad"),
    )
    c.dueno = spec.get("dueno", dueno)
    return c


def _pagina_habilidades():
    """La pagina de habilidades se genera desde reglas.HABILIDADES.

    Asi el texto del tutorial no puede quedar viejo frente al motor:
    lo verifica tests/test_tutorial.py.
    """
    lineas = ["Cada carta puede tener una habilidad. Piden un sitio distinto:"]
    for nombre in ("muro", "furia", "embestida", "quema"):
        lineas.append(f"{nombre.upper()}: {HABILIDADES[nombre]}")
    return lineas


def paginas_manual():
    """Las 10 paginas del manual. Cada una: que es + para que sirve + demo."""
    return [
        {
            "id": "cartas",
            "titulo": "TUS CARTAS",
            "que": [
                "Cada carta tiene 4 lados: N (arriba), S (abajo),",
                "E (derecha) y O (izquierda). El 10 se muestra como A.",
                "Cada orbe solo pelea contra el orbe de enfrente:",
                "tu N contra su S, tu E contra su O, y al reves.",
            ],
            "sirve": "Antes de colocar, mira los 4 orbes: un 9 arriba "
                      "no sirve si atacas por el flanco.",
            "demo": [
                {"nombre": "Espadachin", "n": 8, "s": 6, "e": 5, "o": 7,
                 "bando": "humano", "dueno": USUARIO},
            ],
            "nota": "N 8 - S 6 - E 5 - O 7: cada numero pelea solo contra "
                    "el de enfrente.",
        },
        {
            "id": "basica",
            "titulo": "CAPTURA BASICA",
            "que": [
                "Al colocar, cada lado compara con su vecino.",
                "Si tu lado es MAYOR que el del rival, esa carta cae",
                "y pasa a tu color. Si empatas, no pasa nada.",
            ],
            "sirve": "Gana terreno con fuerza bruta: busca siempre el "
                      "flanco debil del rival.",
            "demo": [
                {"nombre": "Espadachin", "n": 8, "s": 6, "e": 5, "o": 7,
                 "bando": "humano", "dueno": USUARIO},
                {"nombre": "Lancero Gruano", "n": 6, "s": 7, "e": 8, "o": 5,
                 "bando": "orco", "dueno": CPU},
            ],
            "nota": "Tu N (8) contra su S (7): 8 gana y la carta cae.",
        },
        {
            "id": "same",
            "titulo": "SAME",
            "que": [
                "Si DOS vecinos tienen el valor IGUAL al tuyo opuesto,",
                "caen los dos a la vez, aunque no los superes.",
                "Ejemplo: tu N 5 y tu O 7 contra dos 5 y 7 de enfrente.",
            ],
            "sirve": "Los mazos elfos viven del Same: guarda tu carta "
                      "igualadora para el momento con mas vecinos.",
            "demo": [
                {"nombre": "Dama Hoja", "n": 5, "s": 8, "e": 4, "o": 9,
                 "bando": "elfo", "dueno": USUARIO},
                {"nombre": "Arquero", "n": 7, "s": 5, "e": 8, "o": 6,
                 "bando": "elfo", "dueno": CPU},
            ],
            "nota": "Dos valores iguales a los tuyos caen juntos, sin superar.",
        },
        {
            "id": "plus",
            "titulo": "PLUS",
            "que": [
                "Si DOS comparaciones distintas suman LO MISMO, caen las dos.",
                "Ejemplo: tu N 5 + su S 5 (=10) y tu E 6 + su O 4 (=10).",
                "El Plus no necesita igualar ni superar ningun lado.",
            ],
            "sirve": "El Plus dobla una captura sin gastar otra carta "
                      "en el centro.",
            "demo": [
                {"nombre": "Sabio del Bosque", "n": 3, "s": 10, "e": 5,
                 "o": 7, "bando": "elfo", "dueno": USUARIO},
            ],
            "nota": "Dos sumas iguales caen a la vez: 5+5 y 6+4.",
        },
        {
            "id": "cadena",
            "titulo": "CADENA",
            "que": [
                "Toda carta que cae sigue capturando, como un domino.",
                "Una sola captura bien puesta puede volcar medio tablero.",
                "El HUD avisa con CADENA DE 2, DE 3...",
            ],
            "sirve": "Piensa dos jugadas adelante: la primera captura "
                      "es la que manda.",
            "demo": [
                {"nombre": "Saqueador", "n": 7, "s": 6, "e": 3, "o": 8,
                 "bando": "goblin", "dueno": USUARIO},
            ],
            "nota": "Cae una y arrastra a su vecina: 2 de una vez.",
        },
        {
            "id": "habilidades",
            "titulo": "HABILIDADES",
            "que": _pagina_habilidades(),
            "sirve": "Cada habilidad pide un sitio: el muro a defender, "
                      "la furia junto a amigas, la embestida al centro "
                      "y la quema contra debiles.",
            "demo": [
                {"nombre": "Sargento Ferrum", "n": 5, "s": 7, "e": 6, "o": 4,
                 "bando": "humano", "habilidad": "muro", "dueno": USUARIO},
                {"nombre": "Bruto Rasgador", "n": 8, "s": 5, "e": 7, "o": 4,
                 "bando": "orco", "habilidad": "furia", "dueno": USUARIO},
                {"nombre": "Trol de Ceniza", "n": 9, "s": 8, "e": 6, "o": 6,
                 "bando": "orco", "habilidad": "embestida", "dueno": USUARIO},
                {"nombre": "Brujo Verde", "n": 3, "s": 9, "e": 4, "o": 7,
                 "bando": "goblin", "habilidad": "quema", "dueno": USUARIO},
            ],
            "nota": "Muro defiende - Furia ataca en grupo - Embestida manda "
                    "en el centro - Quema remata debiles.",
        },
        {
            "id": "centro",
            "titulo": "CASILLA CENTRAL",
            "que": [
                "La casilla (1,1) da +2 a Hombres Lobo y Dragones",
                "(su elemento) y +2 a cualquier carta con embestida.",
                "El punto naranja del tablero la marca.",
            ],
            "sirve": "Quien pisa el centro con bonus manda: no lo regales "
                      "en la segunda jugada.",
            "demo": [
                {"nombre": "Alfa del Bosque", "n": 10, "s": 6, "e": 8, "o": 7,
                 "bando": "hombre_lobo", "dueno": USUARIO},
            ],
            "nota": "En (1,1): +2 elemental lobo/dragon y +2 embestida.",
        },
        {
            "id": "sinergia",
            "titulo": "SINERGIA",
            "que": [
                "3 o mas cartas de tu bando en el tablero dan +1",
                "a todos tus lados. Se marca con un punto amarillo",
                "en la franja de la carta.",
            ],
            "sirve": "Los mazos de un solo bando escalan: la tercera "
                      "carta amiga vale doble.",
            "demo": [
                {"nombre": "Espadachin", "n": 8, "s": 6, "e": 5, "o": 7,
                 "bando": "humano", "dueno": USUARIO},
                {"nombre": "Arquera de Torre", "n": 6, "s": 5, "e": 9, "o": 5,
                 "bando": "humano", "dueno": USUARIO},
                {"nombre": "Sargento Ferrum", "n": 5, "s": 7, "e": 6, "o": 4,
                 "bando": "humano", "habilidad": "muro", "dueno": USUARIO},
            ],
            "nota": "Tres humanos en mesa: +1 a todo.",
        },
        {
            "id": "final",
            "titulo": "FIN DEL DUELO",
            "que": [
                "El duelo acaba con el tablero lleno o las manos vacias.",
                "Gana quien tenga mas cartas. El empate cuenta",
                "como victoria. La racha x2 sale en el HUD.",
            ],
            "sirve": "Si vas ganando, cierra rapido y guarda la racha "
                      "para la campana.",
            "demo": [],
            "nota": "Mayoria gana. Empate = victoria. Racha x2 en el HUD.",
        },
        {
            "id": "campana",
            "titulo": "CAMPANA",
            "que": [
                "Cada victoria da una recompensa: entrenamiento,",
                "recluta (draft de 3), sigilo (mejora permanente)",
                "o pacto (mazo ajeno para el draft).",
                "Y ojo a los encuentros: tienen consecuencias reales.",
            ],
            "sirve": "Cada victoria te hace mas fuerte: elige la "
                      "recompensa segun tu mazo.",
            "demo": [],
            "nota": "Entrenamiento - Recluta - Sigilo - Pacto.",
        },
    ]


PRACTICAS = [
    {
        "id": "basica",
        "titulo": "CAPTURA BASICA",
        "pasos": [
            {
                "intro": "Arrastra tu Aprendiz junto al novato rival y robaselo.",
                "objetivo": "Coloca en la casilla verde y captura al rival.",
                "pista": "Su lado norte es un 3: entra por arriba con tu S (8).",
                "exito": "Tu S (8) supera su N (3). Asi se roba.",
                "fallo": "Ese lado no supera al rival. "
                         "Entra por arriba, contra su N (3).",
                "tablero": [
                    {"nombre": "Novato", "n": 3, "s": 3, "e": 3, "o": 3,
                     "bando": "orco", "dueno": CPU, "r": 1, "c": 1},
                ],
                "mano": [
                    {"nombre": "Aprendiz", "n": 1, "s": 8, "e": 1, "o": 1,
                     "bando": "humano"},
                ],
                "validas": [(0, 1)],
                "debe": [(1, 1)],
                "nodebe": [],
                "min_caps": 1,
            },
        ],
    },
    {
        "id": "same",
        "titulo": "SAME",
        "pasos": [
            {
                "intro": "Dos rivales te miran con tu mismo numero. Castigalos.",
                "objetivo": "Coloca en el centro: iguala N y O a la vez.",
                "pista": "Iguala su S (5) y su E (7) con tu N (5) y O (7): "
                         "ve al centro.",
                "exito": "Same: 5 contra 5 y 7 contra 7. Caen las dos a la vez.",
                "fallo": "Ahi no hay Same: iguala DOS lados a la vez "
                         "desde el centro.",
                "tablero": [
                    {"nombre": "Alto", "n": 1, "s": 5, "e": 1, "o": 1,
                     "bando": "orco", "dueno": CPU, "r": 0, "c": 1},
                    {"nombre": "Ancho", "n": 1, "s": 1, "e": 7, "o": 1,
                     "bando": "orco", "dueno": CPU, "r": 1, "c": 0},
                ],
                "mano": [
                    {"nombre": "Igualadora", "n": 5, "s": 1, "e": 1, "o": 7,
                     "bando": "humano"},
                ],
                "validas": [(1, 1)],
                "debe": [(0, 1), (1, 0)],
                "nodebe": [],
                "min_caps": 2,
            },
        ],
    },
    {
        "id": "cadena",
        "titulo": "CADENA",
        "pasos": [
            {
                "intro": "La bisagra cae facil... y arrastra a su vecina.",
                "objetivo": "Coloca a la izquierda y vuelca las dos.",
                "pista": "Rompe con tu E (8): la bisagra cae "
                         "y arrastra a la otra.",
                "exito": "Cadena: cae la bisagra y arrastra a su vecina. "
                         "2 de una vez.",
                "fallo": "Ahi no vuelcas nada. Entra por la izquierda "
                         "con tu E (8).",
                "tablero": [
                    {"nombre": "Bisagra", "n": 1, "s": 1, "e": 8, "o": 3,
                     "bando": "orco", "dueno": CPU, "r": 1, "c": 1},
                    {"nombre": "Cola", "n": 1, "s": 1, "e": 1, "o": 5,
                     "bando": "orco", "dueno": CPU, "r": 1, "c": 2},
                ],
                "mano": [
                    {"nombre": "Garfio", "n": 1, "s": 1, "e": 8, "o": 1,
                     "bando": "humano"},
                ],
                "validas": [(1, 0)],
                "debe": [(1, 1), (1, 2)],
                "nodebe": [],
                "min_caps": 2,
            },
        ],
    },
    {
        "id": "habilidades",
        "titulo": "HABILIDADES",
        "pasos": [
            {
                "intro": "Ese muro presume de 9. Atacalo de frente y mira.",
                "objetivo": "Coloca en (0,1) contra su lado 9... y observa.",
                "pista": "Tu O (10) va de frente contra su E (9). "
                         "Deberia ganar... o no.",
                "exito": "Ni un 10 rompe el muro: su lado mas alto no puede "
                         "caer. Rodealo.",
                "fallo": "Ataca de frente en (0,1). Es a proposito: "
                         "mira que pasa.",
                "tablero": [
                    {"nombre": "Muro Demo", "n": 2, "s": 2, "e": 9, "o": 2,
                     "bando": "orco", "habilidad": "muro", "dueno": CPU,
                     "r": 0, "c": 0},
                ],
                "mano": [
                    {"nombre": "Ariete", "n": 1, "s": 1, "e": 1, "o": 10,
                     "bando": "humano"},
                ],
                "validas": [(0, 1)],
                "debe": [],
                "nodebe": [(0, 0)],
                "min_caps": 0,
            },
            {
                "intro": "Tu Escudero espera. Pon la Bruta a su lado y siente la furia.",
                "objetivo": "Coloca en (0,1), junto a tu aliado.",
                "pista": "En (0,1) tocas a tu Escudero: subes de 4 a 5 "
                         "y rompes su 4.",
                "exito": "Furia: junto a tu aliado subes a 5 y rompes su 4.",
                "fallo": "Ahi no usas la furia. Coloca en (0,1), "
                         "junto a tu Escudero.",
                "tablero": [
                    {"nombre": "Escudero", "n": 2, "s": 2, "e": 2, "o": 2,
                     "bando": "humano", "dueno": USUARIO, "r": 0, "c": 0},
                    {"nombre": "Tozudo", "n": 4, "s": 1, "e": 1, "o": 1,
                     "bando": "orco", "dueno": CPU, "r": 1, "c": 1},
                ],
                "mano": [
                    {"nombre": "Bruta", "n": 4, "s": 4, "e": 4, "o": 4,
                     "bando": "humano", "habilidad": "furia"},
                ],
                "validas": [(0, 1)],
                "debe": [(1, 1)],
                "nodebe": [],
                "min_caps": 1,
            },
            {
                "intro": "El Guardia cubre el centro con un 6. Solo la embestida pasa.",
                "objetivo": "Coloca tu Trol en el centro (1,1).",
                "pista": "Fuera del centro tu O es 5 y pierdes. "
                         "En (1,1) sube a 7.",
                "exito": "Embestida: en el centro subes a 7 y rompes su 6.",
                "fallo": "Solo vale el centro: fuera, tu 5 pierde "
                         "contra su 6.",
                "tablero": [
                    {"nombre": "Guardia", "n": 6, "s": 6, "e": 6, "o": 1,
                     "bando": "orco", "dueno": CPU, "r": 1, "c": 0},
                ],
                "mano": [
                    {"nombre": "Trol", "n": 5, "s": 5, "e": 5, "o": 5,
                     "bando": "humano", "habilidad": "embestida"},
                ],
                "validas": [(1, 1)],
                "debe": [(1, 0)],
                "nodebe": [],
                "min_caps": 1,
            },
        ],
    },
]


# ------------------------------------------------------------------ guia
class Guia:
    """Gancho del tutorial para el bucle de `partida.partida`.

    `partida()` la llama solo cuando se le pasa `guia=`; sin guia el
    duelo se comporta exactamente igual que antes.
    """

    def __init__(self, practica, indice):
        self.practica = practica
        self.indice = indice
        self.paso = 0
        self.confirmar_salida = False
        self.terminada = False
        self.boton_salir = Boton(pygame.Rect(ANCHO - 380, 430, 300, 44),
                                "SALIR", 11, sub="Dejar la practica")

    def clic_salir(self, pos):
        """True si el clic cae en el boton SALIR de la practica."""
        return self.boton_salir.clic(pos)

    def paso_actual(self):
        return self.practica["pasos"][self.paso]

    def aplicar_paso(self, juego):
        """Monta el tablero y la mano del paso actual."""
        paso = self.paso_actual()
        juego.board = [[None] * 3 for _ in range(3)]
        for spec in paso["tablero"]:
            juego.board[spec["r"]][spec["c"]] = _carta(spec)
        juego.mano_u = [_carta(spec, dueno=USUARIO) for spec in paso["mano"]]
        juego.mano_c = []
        juego.turno_cpu = False
        juego.cpu_en_curso = False
        juego.arrastrando = None
        juego.mensaje = paso["intro"]

    def validar_colocacion(self, juego, carta, r, c):
        """True si la jugada cumple el objetivo (provado con el motor real)."""
        paso = self.paso_actual()
        if (r, c) not in paso["validas"]:
            return False, paso["fallo"]
        nuevo = copy.deepcopy(juego.board)
        copia = carta.copia()
        copia.dueno = USUARIO
        nuevo[r][c] = copia
        caps = set(capturas(nuevo, r, c))
        if len(caps) < paso.get("min_caps", 0):
            return False, paso["fallo"]
        if not set(paso.get("debe", [])) <= caps:
            return False, paso["fallo"]
        if set(paso.get("nodebe", [])) & caps:
            return False, paso["fallo"]
        return True, ""

    def tras_colocar(self, juego, carta, r, c, caps):
        """Avanza de paso o cierra la practica con victoria."""
        paso = self.paso_actual()
        ahora = time.time()
        if self.paso + 1 < len(self.practica["pasos"]):
            self.paso += 1
            audio.sfx(audio.CAPTURAR if caps else audio.COLOCAR)
            juego.banner = ("¡BIEN!", ahora, VERDE, paso["exito"])
            self.aplicar_paso(juego)
            juego.mensaje = f"{paso['exito']}  -  {self.paso_actual()['intro']}"
        else:
            self.terminada = True
            juego.mensaje = "¡Practica superada! Clic para continuar"
            juego.banner = ("¡SUPERADA!", ahora, VERDE, paso["exito"])
            juego.fin = True
            juego.ganador = USUARIO
            juego.tiempo_fin = ahora
            juego._sfx_fin = audio.VICTORIA

    def pista(self):
        return f"Pista: {self.paso_actual()['pista']}"

    def dibujar_extra(self, screen, juego):
        """Resalta casillas validas, panel de objetivo y confirmacion de salida."""
        paso = self.paso_actual()
        ahora = time.time()
        for (r, c) in paso["validas"]:
            if juego.board[r][c] is None:
                pulso = 90 + int(60 * math.sin(ahora * 5))
                resplandor(screen, celda_rect(r, c), VERDE, pulso, 3, 8)
        caja = pygame.Rect(ANCHO - 400, 250, 340, 280)
        panel(screen, caja, PANEL, BORDE, radio=10)
        texto(screen, f"PRACTICA {self.indice + 1}/4", 11, DORADO,
              centro=(caja.centerx, caja.y + 30))
        texto(screen, self.practica["titulo"], 9, TEXTO_ON,
              centro=(caja.centerx, caja.y + 56))
        texto(screen, f"Paso {self.paso + 1}/{len(self.practica['pasos'])}",
              8, TEXTO_TENUE, centro=(caja.centerx, caja.y + 80))
        parrafo(screen, paso["objetivo"], 9, TEXTO, caja.x + 20, caja.y + 104, 300)
        self.boton_salir.actualizar(1 / 60, pygame.mouse.get_pos())
        self.boton_salir.dibujar(screen)
        texto(screen, "H pista - SALIR o ESC para salir", 8, TEXTO_TENUE,
              centro=(caja.centerx, caja.bottom - 24))
        if self.confirmar_salida:
            screen.blit(ui._capa_negra(170), (0, 0))
            caja2 = pygame.Rect(ANCHO // 2 - 260, ALTO // 2 - 90, 520, 180)
            panel(screen, caja2, PANEL, ROJO, radio=10)
            texto(screen, "¿SALIR DEL TUTORIAL?", 13, TEXTO_ON,
                  centro=(caja2.centerx, caja2.y + 48))
            texto(screen, "ENTER = si, salir   -   ESC = seguir", 9, TEXTO,
                  centro=(caja2.centerx, caja2.y + 100))
            texto(screen, "Se guarda como visto.", 8, TEXTO_TENUE,
                  centro=(caja2.centerx, caja2.y + 134))


def construir_duelo_practica(practica, indice):
    """Juego listo para una practica: humanos contra orcos, sin IA rival."""
    info = {
        "bando": "orco",
        "nombre_faccion": facciones.nombre("orco"),
        "nombre": "Instructor",
        "titulo": f"TUTORIAL: {practica['titulo']}",
        "dificultad": 0,
        "escena": "campamento",
        "previa": [],
        "tipo": "tutorial",
        "nodo": "tutorial",
    }
    juego = Juego("humano", bando_rival="orco", mano_u_inicial=[],
                  mano_c_inicial=[], info=info, en_campana=True, dificultad=0)
    juego.abandonado = False
    guia = Guia(practica, indice)
    guia.aplicar_paso(juego)
    return juego, guia


# ------------------------------------------------------------------ manual
class _Fondo:
    """Fondo animado comun (igual que pantallas.Fondo, sin ciclo de imports)."""

    def __init__(self, faccion="elfo"):
        self.animado = FondoAnimado(
            crt.REC.imagen("assets/fondo.png"),
            facciones.acento(faccion),
            ruta="assets/fondo.png",
        )
        self.t0 = time.time()

    def dibujar(self, screen, dt=0.016):
        self.animado.actualizar(dt)
        self.animado.dibujar(screen)


def _botones_manual(es_ultima):
    atras = Boton(pygame.Rect(80, ALTO - 90, 220, 52), "ATRAS", 11)
    saltar = Boton(pygame.Rect(ANCHO // 2 - 140, ALTO - 90, 280, 52), "SALTAR", 11)
    sig = Boton(pygame.Rect(ANCHO - 300, ALTO - 90, 220, 52),
                "EMPEZAR PRACTICAS" if es_ultima else "SIGUIENTE", 11)
    return atras, saltar, sig


def dibujar_pagina(screen, pagina, indice, total, confirmar=False):
    """Pinta una pagina del manual (reutilizable para las demos visuales)."""
    fondo = _Fondo("elfo")
    fondo.dibujar(screen)
    texto(screen, "COMO SE JUEGA", 12, TEXTO_TENUE, centro=(ANCHO // 2, 44))
    texto(screen, pagina["titulo"], 22, DORADO, centro=(ANCHO // 2, 78))

    izq = pygame.Rect(80, 120, 760, 470)
    panel(screen, izq, PANEL, BORDE, radio=10)
    texto(screen, "QUE ES", 11, DORADO, x=izq.x + 24, y=izq.y + 20)
    y = parrafo(screen, " ".join(pagina["que"]), 10, TEXTO,
                izq.x + 24, izq.y + 52, izq.w - 48)

    demos = pagina.get("demo", [])
    if demos:
        escala = 1.0
        ancho = len(demos) * CARD_W + (len(demos) - 1) * 16
        if y + 30 + CARD_H + 60 > izq.bottom - 10:
            escala = 0.75
        ancho = int(len(demos) * CARD_W * escala + (len(demos) - 1) * 16)
        x = izq.x + (izq.w - ancho) // 2
        y_cartas = min(max(y + 24, izq.y + 250), izq.bottom - int(CARD_H * escala) - 56)
        for spec in demos:
            sup = crt.crear(_carta(spec), spec.get("dueno"), escala=escala)
            screen.blit(sup, (x, y_cartas))
            x += int(CARD_W * escala) + 16
        parrafo(screen, pagina.get("nota", ""), 8, TEXTO_TENUE,
                izq.x + 24, y_cartas + int(CARD_H * escala) + 12, izq.w - 48)

    der = pygame.Rect(880, 120, 320, 470)
    panel(screen, der, PANEL, facciones.acento("elfo"), radio=10)
    texto(screen, "PARA QUE SIRVE", 11, DORADO, centro=(der.centerx, der.y + 32))
    parrafo(screen, pagina["sirve"], 9, TEXTO_ON, der.x + 20, der.y + 64, 280)

    texto(screen, f"pagina {indice + 1} de {total}", 9, TEXTO_TENUE,
          centro=(ANCHO // 2, ALTO - 110))
    if confirmar:
        screen.blit(ui._capa_negra(170), (0, 0))
        caja = pygame.Rect(ANCHO // 2 - 260, ALTO // 2 - 90, 520, 180)
        panel(screen, caja, PANEL, ROJO, radio=10)
        texto(screen, "¿SALTAR EL TUTORIAL?", 13, TEXTO_ON,
              centro=(caja.centerx, caja.y + 48))
        texto(screen, "ENTER = si, saltar   -   ESC = seguir", 9, TEXTO,
              centro=(caja.centerx, caja.y + 100))
        texto(screen, "Se guarda como visto.", 8, TEXTO_TENUE,
              centro=(caja.centerx, caja.y + 134))


async def manual(screen, clock):
    """Manual visual de 10 paginas. Devuelve 'fin' o 'salir' (nunca encierra)."""
    paginas = paginas_manual()
    indice = 0
    confirmar = False
    t0 = time.time()
    atras, saltar, sig = _botones_manual(False)
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        mouse = pygame.mouse.get_pos()
        es_ultima = indice == len(paginas) - 1
        atras, saltar, sig = _botones_manual(es_ultima)
        dibujar_pagina(screen, paginas[indice], indice, len(paginas), confirmar)
        for b in (atras, saltar, sig):
            b.actualizar(dt, mouse)
            b.dibujar(screen)
        fundido_entrada(screen, t0, 0.35)
        pygame.display.flip()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                if confirmar:
                    confirmar = False
                    audio.sfx(audio.MENU_BACK)
                else:
                    confirmar = True
                    audio.sfx(audio.MENU_BACK)
                continue
            if confirmar:
                if ev.type == pygame.KEYDOWN and ev.key in (
                        pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    audio.sfx(audio.MENU_OK)
                    return "salir"
                continue
            if ev.type == pygame.KEYDOWN and ev.key in (
                    pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
                audio.sfx(audio.MENU_MOVE)
                if es_ultima:
                    return "fin"
                indice = min(len(paginas) - 1, indice + 1)
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_LEFT:
                audio.sfx(audio.MENU_MOVE)
                indice = max(0, indice - 1)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if sig.clic(ev.pos):
                    audio.sfx(audio.MENU_OK)
                    if es_ultima:
                        return "fin"
                    indice = min(len(paginas) - 1, indice + 1)
                elif atras.clic(ev.pos):
                    audio.sfx(audio.MENU_OK)
                    indice = max(0, indice - 1)
                elif saltar.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    confirmar = True


# ------------------------------------------------------------------ puerta
async def puerta_primer_arranque(screen, clock):
    """Pantalla de primer arranque. True = jugar, False = saltar (tambien visto)."""
    fondo = _Fondo("dragon")
    t0 = time.time()
    jugar = Boton(pygame.Rect(ANCHO // 2 - 370, 430, 340, 64), "JUGAR TUTORIAL",
                  12, sub="Aprende en 5 minutos")
    saltar = Boton(pygame.Rect(ANCHO // 2 + 30, 430, 340, 64), "SALTAR",
                   12, sub="Ya se jugar")
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        mouse = pygame.mouse.get_pos()
        fondo.dibujar(screen, dt)
        texto(screen, "¿PRIMERA VEZ AQUI?", 24, DORADO, centro=(ANCHO // 2, 200))
        texto(screen, "El tutorial explica cada regla y te deja practicarla.",
              10, TEXTO, centro=(ANCHO // 2, 260))
        texto(screen, "Se puede saltar con ESC en cualquier momento.",
              10, TEXTO_TENUE, centro=(ANCHO // 2, 290))
        for b in (jugar, saltar):
            b.actualizar(dt, mouse)
            b.dibujar(screen)
        texto(screen, "ENTER juega   -   ESC salta", 9, TEXTO_TENUE,
              centro=(ANCHO // 2, ALTO - 120))
        fundido_entrada(screen, t0, 0.35)
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN and ev.key in (
                    pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                audio.sfx(audio.MENU_OK)
                return True
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                audio.sfx(audio.MENU_BACK)
                return False
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if jugar.clic(ev.pos):
                    audio.sfx(audio.MENU_OK)
                    return True
                if saltar.clic(ev.pos):
                    audio.sfx(audio.MENU_BACK)
                    return False


# ------------------------------------------------------------------ orquesta
async def tutorial(screen, clock, desde_practica=None):
    """Tutorial completo: manual + 4 practicas. Devuelve 'completo' o 'salido'.

    Si hay progreso guardado (`tutorial_paso` entre 1 y 3 sin completar),
    se retoma desde esa practica sin repetir el manual.
    """
    import pantallas

    perfil = campana.cargar_perfil()
    paso_guardado = int(perfil.get("tutorial_paso", 0) or 0)
    if desde_practica is None and 0 < paso_guardado < len(PRACTICAS) \
            and not perfil.get("tutorial_completado"):
        inicio = paso_guardado
    elif desde_practica is not None:
        inicio = max(0, min(desde_practica, len(PRACTICAS) - 1))
    else:
        inicio = None

    if inicio is None:
        if await manual(screen, clock) == "salir":
            campana.marcar_tutorial(visto=True)
            return "salido"
        campana.marcar_tutorial(visto=True, paso=0)
        inicio = 0

    for i in range(inicio, len(PRACTICAS)):
        campana.marcar_tutorial(paso=i)
        juego, guia = construir_duelo_practica(PRACTICAS[i], i)
        await partida(screen, clock, juego, guia=guia)
        if getattr(juego, "abandonado", False) or not guia.terminada:
            campana.marcar_tutorial(visto=True, paso=i)
            return "salido"
    campana.marcar_tutorial(visto=True, completado=True, paso=len(PRACTICAS))
    audio.musica(audio.musica_de_menu())
    await pantallas.cartel(
        screen, clock,
        "TUTORIAL COMPLETO",
        "Ya sabes jugar: basica, Same, cadena y habilidades. A por el trono.",
    )
    return "completo"


# Alias para las demos visuales y los tests.
PAGINAS = paginas_manual
