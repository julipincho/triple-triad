"""Manifiesto de assets: que hay, que falta y por que importa.

La biblia pide que se note cuando estas en nuestro mundo y cuando estas dentro
de Cartones y Mazmorras. Parte de eso se resuelve con codigo (el tinte y la
vineta por mundo, `cinematicas.MUNDO_REAL`) y parte necesita arte que este
incremento no puede authoring: no se puede dibujar un fondo ni componer una
pista desde aca.

Este modulo deja el estado real, verificado contra el disco, para que el
trabajo de arte sea una lista cerrada y no una busqueda a ciegas.

Este modulo no importa nada del juego: solo mira el sistema de archivos.
"""

import os

#: Fonde de la campana principal + cinematicas. Todos existen.
FONDOS_USADOS = (
    "camino", "aldea", "ruinas", "fortaleza", "asalto", "trono", "umbral",
    "campamento", "ceniza", "estandartes", "amanecer",
)

#: Los que usaria el mundo real de nuestro mundo. El salon del torneo es un
#: lugar distinto del campamento del mundo fantastic: si se comparten, el
#: jugador pierde la referencia de en que lado esta.
FONDOS_MUNDO_REAL = ("salon", "apagon")

#: Quien habla y todavia no tiene retrato.
PERSONAJES_SIN_RETRATO = {
    "nara": "Nara, la Cronista: el unico acompanante. Habla en el prologo, en "
            "todos los nodos y en los tres finales.",
    "cartografo": "El Maestro de la Mesa: el rival de la campana secreta. No "
                  "pertenece a ninguna faccion, asi que no hay avatar de bando "
                  "que le sirva.",
    "presentador": "El presentador del torneo, en el prologo.",
    "duelista": "El protagonista. Sin retrato a proposito: es el jugador. Le "
                "pondriamos el rostro del jugador, y no lo hay. El nombre SI "
                "se puede escribir: la pantalla inicial lo pide y se guarda en "
                "el perfil. Vacio significa 'el duelista', el texto de siempre.",
}

#: Pistas que hacen falta para distinguir los dos mundos con el oido.
MUSICA_FALTANTE = {
    "musica_torneo": "El salon del torneo: electronica, tensa, moderna. Hoy el "
                     "prologo usa musica_explora, que tambien suena en el bosque.",
    "musica_umbral": "Un tema propio para cuando la grieta se abre. Hoy se "
                     "reutiliza musica_duelo.",
}

RAIZ = os.path.dirname(os.path.abspath(__file__))


def _existe(*partes):
    return os.path.exists(os.path.join(RAIZ, *partes))


def fondos_existentes():
    base = os.path.join(RAIZ, "assets", "fondos")
    if not os.path.isdir(base):
        return []
    return sorted(f[:-4] for f in os.listdir(base) if f.endswith(".png"))


def avatares_existentes():
    base = os.path.join(RAIZ, "assets")
    return sorted(f[len("avatar_"):-4] for f in os.listdir(base)
                  if f.startswith("avatar_") and f.endswith(".png"))


def pistas_existentes():
    base = os.path.join(RAIZ, "assets", "musica")
    if not os.path.isdir(base):
        return []
    return sorted(f[:-4] for f in os.listdir(base) if f.endswith(".ogg"))


def fondos_faltantes():
    """Fondos que el manifiesto da por usados y no estan en disco."""
    hay = set(fondos_existentes())
    return [f for f in FONDOS_USADOS if f not in hay]


def retratos_faltantes():
    return [p for p in PERSONAJES_SIN_RETRATO if not _existe("assets", f"avatar_{p}.png")]


def musica_faltante():
    hay = set(pistas_existentes())
    return [m for m in MUSICA_FALTANTE if m not in hay]


def resumen():
    """El estado en una linea, para el menu de ajustes o el informe."""
    partes = [
        f"fondos {len(fondos_existentes())}/{len(FONDOS_USADOS)} usados",
        f"retratos pendientes {len(retratos_faltantes())}",
        f"pistas pendientes {len(musica_faltante())}",
    ]
    return " | ".join(partes)
