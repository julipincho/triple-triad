"""Mazos por faccion.

Habilidades disponibles (ver reglas.py):
  - "quema"     captura a cualquier enemigo adyacente, sin importar el valor
  - "muro"      su lado mas alto no puede ser capturado
  - "furia"     +1 a todos sus lados si toca otra carta amiga en el tablero
  - "embestida" +2 a todos sus lados si se coloca en la casilla central
"""

from reglas import Carta

GOBLINS = [
    Carta("Mordedor", 8, 4, 6, 5, bando="goblin"),
    Carta("Brujo Verde", 3, 9, 4, 7, bando="goblin", habilidad="quema"),
    Carta("Lanzasalgo", 6, 5, 9, 4, bando="goblin"),
    Carta("Saqueador", 7, 6, 3, 8, bando="goblin"),
    Carta("Rey Goblin", 10, 7, 8, 6, bando="goblin"),
]

ELFOS = [
    Carta("Arquero", 7, 5, 8, 6, bando="elfo"),
    Carta("Dama Hoja", 5, 8, 4, 9, bando="elfo"),
    Carta("Centinela", 4, 6, 10, 3, bando="elfo"),
    Carta("Sabio del Bosque", 3, 10, 5, 7, bando="elfo"),
    Carta("Elfo Real", 9, 6, 7, 8, bando="elfo"),
]

HOMBRES_LOBO = [
    Carta("Garras de Luna", 8, 5, 6, 4, bando="hombre_lobo"),
    Carta("Mordedor Lunar", 6, 9, 4, 5, bando="hombre_lobo"),
    Carta("Aullador", 5, 7, 8, 4, bando="hombre_lobo"),
    Carta("Piel Gris", 4, 6, 9, 6, bando="hombre_lobo"),
    Carta("Alfa del Bosque", 10, 6, 8, 7, bando="hombre_lobo"),
]

VAMPIROS = [
    Carta("Conde Nocturno", 9, 8, 7, 6, bando="vampiro"),
    Carta("Dama Carmin", 5, 9, 4, 8, bando="vampiro"),
    Carta("Murcielago", 3, 6, 10, 4, bando="vampiro"),
    Carta("Cazadora de Sangre", 7, 7, 5, 8, bando="vampiro"),
    Carta("Vastago", 6, 5, 8, 9, bando="vampiro"),
]

DRAGONES = [
    Carta("Drake", 7, 6, 8, 5, bando="dragon"),
    Carta("Fuego", 5, 8, 4, 9, bando="dragon", habilidad="quema"),
    Carta("Guerrero Rojo", 8, 5, 7, 6, bando="dragon"),
    Carta("Segador Alado", 6, 7, 9, 4, bando="dragon"),
    Carta("Rey Dragon", 10, 9, 8, 8, bando="dragon"),
]

HUMANOS = [
    Carta("Sargento Ferrum", 5, 7, 6, 4, bando="humano", habilidad="muro"),
    Carta("Espadachin", 8, 6, 5, 7, bando="humano"),
    Carta("Arquera de Torre", 6, 5, 9, 5, bando="humano"),
    Carta("Clerigo de la Luz", 4, 6, 5, 9, bando="humano"),
    Carta("Rey Aldric", 10, 8, 7, 8, bando="humano", habilidad="muro"),
]

ORCOS = [
    Carta("Bruto Rasgador", 8, 5, 7, 4, bando="orco", habilidad="furia"),
    Carta("Chaman Karzh", 4, 9, 5, 7, bando="orco", habilidad="quema"),
    Carta("Lancero Gruano", 6, 7, 8, 5, bando="orco"),
    Carta("Trol de Ceniza", 9, 8, 6, 6, bando="orco", habilidad="embestida"),
    Carta("Senor de la Guerra Vorg", 10, 9, 8, 7, bando="orco", habilidad="furia"),
]

TODOS = {
    "humano": HUMANOS,
    "orco": ORCOS,
    "goblin": GOBLINS,
    "elfo": ELFOS,
    "hombre_lobo": HOMBRES_LOBO,
    "vampiro": VAMPIROS,
    "dragon": DRAGONES,
}

NOMBRES_BANDO = {
    "humano": "Humanos",
    "orco": "Orcos",
    "goblin": "Goblins",
    "elfo": "Elfos",
    "hombre_lobo": "Hombres Lobo",
    "vampiro": "Vampiros",
    "dragon": "Dragones",
}

DESCRIPCION_BANDO = {
    "humano": "Muro, guardia y rey. Pierde duelos largos, gana los cortos.",
    "orco": "Furia por acumulacion: cada vecino aliado la hace mas fuerte.",
    "goblin": "Barato y veloz, con un brujo que quema sin mirar valores.",
    "elfo": "Valores altos en cruz: el Same hace mas dano que la fuerza.",
    "hombre_lobo": "Domina la casilla central y las cadenas de captura.",
    "vampiro": "Equilibrio agresivo, bueno para romper la guardia del rival.",
    "dragon": "Rey de la fuerza bruta: el Quemador rompe el tablero entero.",
}