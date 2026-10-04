"""Mazos iniciales: Goblins contra Elfos."""

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

TODOS = {
    "goblin": GOBLINS,
    "elfo": ELFOS,
    "hombre_lobo": HOMBRES_LOBO,
    "vampiro": VAMPIROS,
    "dragon": DRAGONES,
}

NOMBRES_BANDO = {
    "goblin": "Goblins",
    "elfo": "Elfos",
    "hombre_lobo": "Hombres Lobo",
    "vampiro": "Vampiros",
    "dragon": "Dragones",
}
