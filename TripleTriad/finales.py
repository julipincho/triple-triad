"""Los tres finales y el regreso al mundo real.

Que cambia respecto a antes
---------------------------
Los 30 finales por faccion (`campana.FINALES`) no se tocan: son el final del
mundo fantastic, el color de cada bando. Lo que faltaba era lo que la biblia
pide explicitamente: que **todos esos finales sean la misma historia contada
desde el Umbral**.

    mundo fantastic  ->  se abre el Umbral  ->  mundo real

Por eso hay una segunda capa, comun a las diez facciones:

  - `UMBRAL[variante]`   : que pasa al forzar / abrir con cuidado / romper la
                           grieta. Es lo que hace el Umbral en cada caso.
  - `EPILOGO[variante]`  : la escena final, de vuelta en nuestro mundo, donde
                           el duelista descubre que algo cambio.

Los tres finales que pedia la biblia:

  DOMINIO     : fuerza la apertura, vuelve con algo encima.
  EQUILIBRIO  : abre lo justo para regresar; el mundo casi no se entera.
  CAOS        : el Umbral se rompe y los dos mundos se superponen.

Este modulo no importa campana: lo usa.
"""


def esc(linea, hablante=None, fondo="trono", efecto="dialogo", color=None,
        mundo="juego"):
    return {"texto": linea, "hablante": hablante, "fondo": fondo, "retrato": None,
            "efecto": efecto, "musica": None, "color": color, "mundo": mundo}


# --------------------------------------------------------------- el Umbral
# Que le pasa a la grieta en cada final. Es comun a las diez facciones: por eso
# el final de un goblin y el de un humano terminan en la misma puerta.

UMBRAL = {
    "dominio": {
        "titulo": "FORZAS LA APERTURA",
        "musica": "musica_duelo",
        "lineas": [
            "Empujas. No es abrir una puerta: es convencer a algo que no quiere.",
            "El Umbral cede y del otro lado esta tu salon, tus luces, tu torneo.",
            "Y tambien esta la otra cosa: algo cruza en sentido contrario.",
            "No lo ves. Todavia no. Vas a verlo mas tarde, en tu propio mazo.",
        ],
    },
    "equilibrio": {
        "titulo": "LA ABRES LO JUSTO",
        "musica": "musica_explora",
        "lineas": [
            "No la fuerzas. La negocias: el tiempo justo para cruzar y volver.",
            "Alguien sostiene el otro lado. Alguien que se queda esperando.",
            "Cruzas. El Umbral se cierra detras con un ruido pequeno, de puerta.",
            "Para todos los de aqui, en el salon, pasaron tres segundos.",
        ],
    },
    "caos": {
        "titulo": "SE ROMPE",
        "musica": "musica_dragon",
        "lineas": [
            "No se abre. Se rompe. Y romper no es lo mismo que abrir.",
            "Las dos paredes de la realidad se mezclan como un mazo mal barajado.",
            "El bosque entra al salon. El salon entra al bosque. Sin permiso.",
            "Y en el bolsillo te queda una carta que no compraste nunca.",
        ],
    },
}

# Nota sobre la musica: `musica_duelo` y `musica_explora` son las unicas pistas
# que no son de una faccion. El final de equilibrio comparte pista entre el
# Umbral y el epilogo a proposito: en ese final no pasa nada, y la musica tiene
# que seguir sonando igual que antes. El resto de finales si se distinguen.

# ------------------------------------------------------------- los epilogos
# La escena final, de vuelta en nuestro mundo. Aqui se juega el giro: el
# duelista vuelve a casa y algo no encaja.

EPILOGO = {
    "dominio": {
        "titulo": "VOLVISTE CON ALGO",
        "fondo": "campamento",
        "musica": "musica_explora",
        "lineas": [
            "Estas otra vez en el torneo. La misma mesa, las mismas luces.",
            "Miras tu mazo para contar las cartas y te sobran cinco.",
            "Hay una que no compraste. No la viste nunca. No tiene fecha.",
            "Es LEGENDARIA. Y el rostro en el arte... es el tuyo.",
            "- Quien sos? - Alguien que estuvo donde nadie debe estar.",
        ],
    },
    "equilibrio": {
        "titulo": "UNA EXPANSION NUEVA",
        "fondo": "campamento",
        "musica": "musica_explora",
        "lineas": [
            "Para todos, en el salon, pasaron tres segundos. Nada mas.",
            "Buscas en internet los nombres de los que conociste. Nada cambia.",
            "Todo esta igual. Hasta que abris Cartones y Mazmorras.",
            "Hay una expansion nueva. Anunciada esta manana. Nadie sabe de quien.",
            "La portada es el rostro de alguien que te ayudo a volver. Nara.",
            "- Como puede estar en una carta? - Porque ya la viste. En el bosque.",
        ],
    },
    "caos": {
        "titulo": "UNA CARTA QUE SE MUEVE",
        "fondo": "campamento",
        "musica": "musica_duelo",
        "lineas": [
            "El mundo parece exactamente igual. Por eso nadie te cree.",
            "Las cosas de siempre son las mismas. Casi todas.",
            "En tu coleccion hay una carta nueva. No recuerdas comprarla.",
            "La sacas. Y dentro del sobre, la carta se mueve sola.",
            "- Esto se mueve? - ...Para vos no. Ya lo hiciste antes.",
        ],
    },
}

#: El epilogue de "dominio" es el unico que revela tu propia cara. Es el
#: premio del que.forza la puerta.
EPILOGO_LEGENDARIA = "LEGENDARIA"


# ------------------------------------------------------------------ publico


def titulo_umbral(variante):
    return UMBRAL.get(variante, UMBRAL["equilibrio"])["titulo"]


def musica_umbral(variante):
    return UMBRAL.get(variante, UMBRAL["equilibrio"])["musica"]


def musica_epilogo(variante):
    return EPILOGO.get(variante, EPILOGO["equilibrio"])["musica"]


def escenas_umbral(variante, faccion=None):
    """Escenas de la apertura del Umbral, comunes a todas las facciones."""
    datos = UMBRAL.get(variante, UMBRAL["equilibrio"])
    escenas = [esc(datos["titulo"], fondo="umbral", efecto="titulo")]
    for linea in datos["lineas"]:
        escenas.append(esc(linea, fondo="umbral"))
    return escenas


def escenas_epilogo(variante):
    """La escena final en nuestro mundo."""
    datos = EPILOGO.get(variante, EPILOGO["equilibrio"])
    escenas = [esc(datos["titulo"], fondo=datos["fondo"], efecto="titulo",
                   mundo="real")]
    for linea in datos["lineas"]:
        escenas.append(esc(linea, fondo=datos["fondo"], mundo="real"))
    return escenas


def _validar():
    """Coherencia interna. La usan los tests."""
    errores = []
    for clave in ("dominio", "equilibrio", "caos"):
        if clave not in UMBRAL:
            errores.append(f"sin UMBRAL: {clave}")
        if clave not in EPILOGO:
            errores.append(f"sin EPILOGO: {clave}")
        for linea in UMBRAL.get(clave, {}).get("lineas", []):
            if not linea.strip():
                errores.append(f"{clave}: linea vacia en UMBRAL")
        for linea in EPILOGO.get(clave, {}).get("lineas", []):
            if not linea.strip():
                errores.append(f"{clave}: linea vacia en EPILOGO")
    # el Umbral y el epilogo no pueden repetir la misma linea
    for clave in UMBRAL:
        u = set(UMBRAL[clave]["lineas"])
        e = set(EPILOGO.get(clave, {}).get("lineas", []))
        if u & e:
            errores.append(f"{clave}: linea repetida entre Umbral y epilogo")
    return errores
