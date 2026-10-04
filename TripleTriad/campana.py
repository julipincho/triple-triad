"""Modo campaña: duelos en cadena, mejora de cartas, jefe final."""

import json
import os
import random

import mazos
from reglas import Carta

ORDEN = ["goblin", "elfo", "hombre_lobo", "vampiro", "dragon"]

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
        "entrada": "QUEMERE. TU MAZOARDERA.",
        "captura_player": "Grrr... arde en furia!",
        "captura_cpu": "QUEME TODO!",
        "win": "NINGUN HUMANO PUEDE CONMIGO.",
        "lose": "...ha sido una buena quema.",
    },
}

GUARDADO = os.path.join(os.getcwd(), "campana.json")


def nueva_campana():
    return {
        "etapa": 0,
        "mazo_jugador": "goblin",
        "cartas": [
            {"nombre": c.nombre, "n": c.valores["N"], "s": c.valores["S"], "e": c.valores["E"], "o": c.valores["O"], "bando": c.bando, "habilidad": c.habilidad}
            for c in mazos.GOBLINS
        ],
        "completada": False,
    }


def guardar(estado):
    with open(GUARDADO, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def cargar():
    try:
        with open(GUARDADO, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def cartas_jugador(estado):
    cartas = []
    for d in estado["cartas"]:
        c = Carta(d["nombre"], d["n"], d["s"], d["e"], d["o"], bando=d.get("bando", estado["mazo_jugador"]), habilidad=d.get("habilidad"))
        cartas.append(c)
    return cartas


def mejorar_carta(estado, id_carta):
    """Sube +1 a un valor aleatorio (max 10) de la carta indicada."""
    d = estado["cartas"][id_carta]
    lados = ["n", "s", "e", "o"]
    random.shuffle(lados)
    for lado in lados:
        if d[lado] < 10:
            d[lado] += 1
            return lado
    return None


def rival_actual(estado):
    if estado["etapa"] >= len(ORDEN):
        return None
    return ORDEN[estado["etapa"]]
