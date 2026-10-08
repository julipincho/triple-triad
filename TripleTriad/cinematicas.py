"""Motor de cinematicallyas: bandas letterbox, fundidos, maquina de escribir,
retratos, dialogo y cambio de musica.

Las escenas se describen con datos (diccionarios) para que la campana pueda
componer secuencias sin codigo nuevo:

    {"fondo": "ceniza", "hablante": "Aldric", "texto": "...",
     "retrato": "humano", "efecto": "titulo", "musica": "musica_humano"}
"""

import time

import pygame

import audio
import duelistas
import facciones
import narrativa
from ui import (
    ALTO,
    ANCHO,
    DORADO,
    LIMIT_FPS,
    TEXTO,
    TEXTO_ON,
    TEXTO_TENUE,
    REC,
    con_alpha,
    ease,
    envoltura_lineas,
    panel,
    resplandor,
    texto,
)

import asyncio

VELOCIDAD_ESCRITURA = 44.0  # caracteres por segundo
LINEA_BARRA = 46


class Escena:
    """Una escena: fondo, hablante, retrato y dialogo."""

    def __init__(self, datos):
        self.fondo = datos.get("fondo", "ceniza")
        self.hablante = datos.get("hablante")
        self.texto = datos.get("texto", "")
        self.retrato = datos.get("retrato")
        self.efecto = datos.get("efecto", "dialogo")
        self.color = datos.get("color", TEXTO)
        self.musica = datos.get("musica")
        self.mundo = datos.get("mundo", MUNDO_JUEGO)
        self.duracion = datos.get("duracion")
        self.mostrado = 0.0

    @property
    def completa(self):
        return self.mostrado >= len(self.texto)


class Cinematica:
    """Secuencia reproducible de escenas, bloqueante."""

    def __init__(self, escenas, al_terminar=None, musica=None, permitir_saltar=True):
        self.escenas = [e if isinstance(e, Escena) else Escena(e) for e in escenas]
        self.al_terminar = al_terminar
        self.musica = musica
        self.permitir_saltar = permitir_saltar
        self.i = 0
        self._t_escena = time.time()

    # -------------------------------------------------------------- control
    def escena(self):
        return self.escenas[self.i] if self.i < len(self.escenas) else None

    @property
    def ultima(self):
        return self.i >= len(self.escenas) - 1

    def _avanzar(self):
        """Avanza a la escena siguiente. Devuelve False si ya no habia mas.

        El final del recorrido se decide con este retorno y NO con
        `escena() is None`, que nunca se cumple en la ultima escena: ese era
        el bug que dejaba el dialogo sin poder cerrarse.
        """
        if self.ultima:
            return False
        self.i += 1
        self._t_escena = time.time()
        return True

    async def ejecutar(self, screen, clock):
        if not self.escenas:
            if self.al_terminar:
                self.al_terminar()
            return
        self._t_escena = time.time()
        audio.sfx(audio.CINEMA)
        audio.musica(self.escenas[0].musica or self.musica)

        while True:
            clock.tick(LIMIT_FPS)
            await asyncio.sleep(0)
            escena = self.escena()
            if escena is None:
                break
            if escena.musica:
                audio.musica(escena.musica)
            t = time.time() - self._t_escena
            if escena.efecto == "titulo":
                escena.mostrado = len(escena.texto) if t > 0.4 else 0
            else:
                escena.mostrado = min(len(escena.texto), max(0.0, t - 0.3) * VELOCIDAD_ESCRITURA)
                if escena.duracion and t > escena.duracion:
                    escena.mostrado = len(escena.texto)

            self._dibujar(screen, escena, t)
            pygame.display.flip()

            avanzar = False
            saltar = False
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    # ESC siempre cierra la cinematica, incluso en el epilogo:
                    # el jugador no debe quedarse nunca encerrado en una escena.
                    if self.permitir_saltar or escena.completa:
                        saltar = True
                if ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    avanzar = True
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    if not escena.completa:
                        escena.mostrado = len(escena.texto)
                    else:
                        avanzar = True
            if saltar:
                self._terminar()
                return
            if avanzar and not self._avanzar():
                break
        self._terminar()

    def ejecutar_un_frame(self, screen):
        """Avanza y dibuja un frame sin procesar eventos (para demos/tests)."""
        escena = self.escena()
        if escena is None:
            return False
        t = time.time() - self._t_escena
        if escena.efecto == "titulo":
            escena.mostrado = len(escena.texto) if t > 0.4 else 0
        else:
            escena.mostrado = min(len(escena.texto), max(0.0, t - 0.3) * VELOCIDAD_ESCRITURA)
            if escena.duracion and t > escena.duracion:
                escena.mostrado = len(escena.texto)
        self._dibujar(screen, escena, t)
        pygame.display.flip()
        return True

    def _terminar(self):
        if self.al_terminar:
            self.al_terminar()

    # ---------------------------------------------------------------- dibujo
    def _dibujar(self, screen, escena, t):
        # fondo, oscurecido y vineta cacheados (sin reservas por frame).
        # El tinte depende del mundo: el salon del torneo se ve mas claro que
        # el mundo fantastic, y asi se nota en que lado estas.
        tinte, alpha, (vin_a, vin_b) = TRATAMIENTO.get(
            getattr(escena, "mundo", MUNDO_JUEGO), TRATAMIENTO[MUNDO_JUEGO])
        screen.blit(REC.fondo_pantalla(f"assets/fondos/{escena.fondo}.png"), (0, 0))
        screen.blit(REC.capa_oscurita((*tinte, alpha)), (0, 0))
        if vin_a:
            screen.blit(REC.vineta(vin_a, vin_b), (0, 0))

        if escena.efecto == "titulo":
            self._titulo(screen, escena, t)
        else:
            self._dialogo(screen, escena, t)
        self._barras(screen)

    def _titulo(self, screen, escena, t):
        k = min(1.0, t / 1.1)
        if k < 0.15:
            a = int(255 * (k / 0.15))
        else:
            a = int(255 * ease(k))
        tam = 34 if len(escena.texto) < 24 else 26
        # render con alpha directo: evita superficiesSRCALPHA que no admiten set_alpha
        color = (escena.color[0], escena.color[1], escena.color[2], a)
        img = REC.fuente(tam).render(escena.texto, True, color)
        x = (ANCHO - img.get_width()) // 2
        y = ALTO // 2 - 40
        resplandor(screen, pygame.Rect(x - 16, y - 14, img.get_width() + 32, img.get_height() + 28),
                   escena.color, int(60 * a), 3, 8)
        screen.blit(img, (x, y))
        if k >= 1.0:
            texto(screen, "clic para continuar", 8, TEXTO_TENUE,
                  centro=(ANCHO // 2, ALTO - LINEA_BARRA - 24))

    def _dialogo(self, screen, escena, t):
        if escena.retrato:
            self._retrato(screen, escena.retrato, t)
        if escena.hablante:
            ancho_txt = REC.fuente(13).render(escena.hablante, True, DORADO).get_width()
            rect = pygame.Rect(60, LINEA_BARRA + 24, ancho_txt + 40, 32)
            panel(screen, rect, (12, 12, 20, 214), DORADO, radio=6, grosor=1, sombra=False)
            texto(screen, escena.hablante, 13, DORADO, x=rect.x + 16, y=rect.y + 9)

        caja = pygame.Rect(120, ALTO - 212, ANCHO - 240, 152)
        panel(screen, caja, (10, 11, 18, 226), con_alpha(DORADO, 190), radio=8)
        lineas = envoltura_lineas(escena.texto, 12, caja.w - 60)
        restantes = int(escena.mostrado)
        y = caja.y + 26
        for linea in lineas:
            if restantes <= 0:
                break
            trozo = linea[:restantes]
            texto(screen, trozo, 12, escena.color, x=caja.x + 30, y=y)
            restantes -= len(linea) + 1
            y += 26
        if escena.completa:
            pista = REC.fuente(8).render("clic para continuar", True, TEXTO_TENUE)
            screen.blit(pista, (caja.right - pista.get_width() - 24, caja.bottom - 26))

    def _retrato(self, screen, bando, t):
        """Retrato de un bando o de un personaje concreto.

        La clave es el nombre del archivo (`avatar_<clave>.png`), asi que tanto
        `goblin` como `nara` funcionan igual. Lo que cambia es la etiqueta: para
        un bando sale el nombre de la faccion; para un personaje, el suyo.
        """
        entrada = ease(min(1.0, t / 0.5))
        img = REC.imagen(f"assets/avatar_{bando}.png", (150, 150))
        x = ANCHO // 2 + 200
        y = LINEA_BARRA + 76 + int((1 - entrada) * -26)
        marco = pygame.Rect(x, y, 150, 150)
        pygame.draw.rect(screen, (10, 10, 16), marco.inflate(12, 12), 3, border_radius=4)
        screen.blit(img, (x, y))
        resplandor(screen, marco, facciones.acento(bando), int(110 * entrada), 2, 4)
        texto(screen, _etiqueta_retrato(bando), 9, facciones.acento(bando),
              centro=(x + 75, y + 168))

    def _barras(self, screen):
        barra = pygame.Surface((ANCHO, LINEA_BARRA), pygame.SRCALPHA)
        barra.fill((0, 0, 0, 238))
        screen.blit(barra, (0, 0))
        screen.blit(barra, (0, ALTO - LINEA_BARRA))


#: Nombre legible de los retratos. Las facciones usan su propio nombre; los
#: personajes con cara (Nara, Juan, el duelista, los rivales) el suyo.
ETIQUETAS_RETRATO = {
    "nara": "Nara, la Cronista",
    "rajoy": "Juan Rajoy",
    "duelista": "El duelista",
    "pik": "Pik",
    "dara": "Dara",
    "jefe_arco": "Jefe de Arco",
    "revancha": "La Revancha",
    "gobernante": "El Gobernante",
}


def _etiqueta_retrato(clave):
    """Como se llama al dueno del retrato, sea bando o personaje."""
    if clave in ETIQUETAS_RETRATO:
        return ETIQUETAS_RETRATO[clave]
    return facciones.nombre(clave)


# --------------------------------------------------------------- argumento
#: treatment visual de cada mundo. "real" = el salon del torneo de nuestro
#: mundo: luz fria, sin vineta. "juego" = el mundo fantastic: oscuro, con
#: vineta. La diferencia tiene que notarse sin que nadie lo diga.
MUNDO_REAL = "real"
MUNDO_JUEGO = "juego"

#: Tinte y vineta por mundo: (color RGB, alpha de capa, vineta alfa).
TRATAMIENTO = {
    MUNDO_JUEGO: ((6, 7, 14), 168, (50, 80)),
    MUNDO_REAL: ((18, 24, 38), 96, (0, 0)),
}


def esc(linea, hablante=None, fondo="ceniza", retrato=None, efecto="dialogo",
        musica=None, color=TEXTO, mundo=MUNDO_JUEGO):
    return {"texto": linea, "hablante": hablante, "fondo": fondo, "retrato": retrato,
            "efecto": efecto, "musica": musica, "color": color, "mundo": mundo}


APERTURAS = {
    "humano": {
        "musica": "musica_humano",
        "escenas": [
            esc("La noche cae sobre un reino que ya no es un reino: solo ceniza y cuatro murallas."),
            esc("El rey Aldric no tiene ejercito. Tiene una correo, dos espadas y una promesa.",
                hablante="Aldric", retrato="humano"),
            esc("Juegas con el mazo humano. Nadie mas en este mundo juega con el.",
                hablante="Aldric", retrato="humano", color=TEXTO_ON),
            esc("Eres el ultimo attempting de una especie que se niega a desaparecer.", color=DORADO),
        ],
    },
    "orco": {
        "musica": "musica_orco",
        "escenas": [
            esc("Al otro lado de la frontera hay un mundo con un muro y una sola palabra: invasores.",
                fondo="campamento"),
            esc("Vorg no sabe leer. Sabe contar. Y sabe que le deben siete generaciones.",
                hablante="Vorg", retrato="orco", fondo="campamento"),
            esc("Juegas con el mazo orco. No el que te impone el mundo: el que tu pueblo se ha ganado con los dientes.",
                hablante="Vorg", retrato="orco", fondo="campamento", color=TEXTO_ON),
            esc("No fight contra el mundo entero: solo contra lo que se opone.", color=DORADO),
        ],
    },
    "goblin": {
        "musica": "musica_goblin",
        "escenas": [
            esc("Bajo el foso hay una puerta que nadie abrio en doscientos anos. Hoy se abre sola.",
                fondo="ruinas"),
            esc("Grix tiene tres mil goblins y ninguna idea de lo que significa la palabra plan.",
                hablante="Grix", retrato="goblin", fondo="ruinas"),
            esc("Con el mazo goblin no pretendes conquistar un trono. Pretendes llevarte el sofa.",
                hablante="Grix", retrato="goblin", fondo="ruinas", color=TEXTO_ON),
            esc("Todo lo que brilla es tuyo. Tambien todo lo que se mueve.", color=DORADO),
        ],
    },
    "elfo": {
        "musica": "musica_elfo",
        "escenas": [
            esc("El bosque lleva cuatrocientos anos callado. Esta manana ha tirado una hoja distinta."),
            esc("Lyra guarda un arma que solo se saca cuando el bosque entero la pide.",
                hablante="Lyra", retrato="elfo"),
            esc("Juegas con el mazo elfico. No es un privilege: es una deuda con cuatro lados.",
                hablante="Lyra", retrato="elfo", color=TEXTO_ON),
            esc("La gracia no discute con el fuego. Se planta delante.", color=DORADO),
        ],
    },
    "hombre_lobo": {
        "musica": "musica_hombre_lobo",
        "escenas": [
            esc("La luna se levanta antes que el sol y eso, en esta ciudad, nadie se lo toma bien.",
                fondo="asalto"),
            esc("Fenris no quiere un trono. Quiere saber por que la ciudad tiene agua y el bosque tiene hambre.",
                hablante="Fenris", retrato="hombre_lobo", fondo="asalto"),
            esc("Juegas con el mazo hombre lobo: cae con fuerza y levanta la manada a la vez.",
                hablante="Fenris", retrato="hombre_lobo", fondo="asalto", color=TEXTO_ON),
            esc("Cuando aulla la manada, las cartas empiezan a obedecer.", color=DORADO),
        ],
    },
    "vampiro": {
        "musica": "musica_vampiro",
        "escenas": [
            esc("El pacto que unio a la noche con la tierra se rompio en una sola noche.",
                fondo="trono"),
            esc("La Condesa vuelve a la cripta con un mismo nombre: su propia sangre.",
                hablante="Condesa", retrato="vampiro", fondo="trono"),
            esc("Con el mazo vampiro no pezas un ejercito. Pezas una deuda.",
                hablante="Condesa", retrato="vampiro", fondo="trono", color=TEXTO_ON),
            esc("Y las deudas se cobran con intereses.", color=DORADO),
        ],
    },
    "dragon": {
        "musica": "musica_dragon",
        "escenas": [
            esc("El cielo lleva semanas del color de la brasa y los pajaros no han cantado.",
                fondo="trono"),
            esc("Ignarok no envio un reto. El reto fue el silencio del cielo entero.",
                hablante="Ignarok", retrato="dragon", fondo="trono"),
            esc("Juegas con el mazo dragon. Nadie te lo pidio: tu lo tomaste.",
                hablante="Ignarok", retrato="dragon", fondo="trono", color=TEXTO_ON),
            esc("Donde pongas el pie, la ceniza crece.", color=DORADO),
        ],
    },
    "elfo_nocturno": {
        "musica": "musica_elfo_nocturno",
        "escenas": [
            esc("El bosque echo a los que miraban al Umbral sin parpadear. La noche los recogio.",
                fondo="umbral"),
            esc("Sylwen no pide volver: pide lo que le deben con intereses de sombra.",
                hablante="Sylwen", retrato="elfo_nocturno", fondo="umbral"),
            esc("Juegas con el mazo elfo nocturno. La oscuridad tambien tiene filo.",
                hablante="Sylwen", retrato="elfo_nocturno", fondo="umbral", color=TEXTO_ON),
            esc("Donde la luz no llega, llegas tu.", color=DORADO),
        ],
    },
    "hombre_pantera": {
        "musica": "musica_hombre_pantera",
        "escenas": [
            esc("Nadie los vio llegar porque nadie mira al tejado. Ya estaban aqui.",
                fondo="estandartes"),
            esc("Zarkha no ruge: susurra, y el susurro basta para vaciar una calle.",
                hablante="Zarkha", retrato="hombre_pantera", fondo="estandartes"),
            esc("Juegas con el mazo hombre pantera: cae sin ruido y cobra sin prisa.",
                hablante="Zarkha", retrato="hombre_pantera", fondo="estandartes", color=TEXTO_ON),
            esc("La mejor caza es la que nadie oye.", color=DORADO),
        ],
    },
    "hombre_lagarto": {
        "musica": "musica_hombre_lagarto",
        "escenas": [
            esc("El pantano lleva siglos tragando ejercitos sin masticar. Hoy escupe uno.",
                fondo="ruinas"),
            esc("Sskar no tiene prisa: la prisa es para los que se hunden.",
                hablante="Sskar", retrato="hombre_lagarto", fondo="ruinas"),
            esc("Juegas con el mazo hombre lagarto: escamas, paciencia y fango.",
                hablante="Sskar", retrato="hombre_lagarto", fondo="ruinas", color=TEXTO_ON),
            esc("Lo que el pantano traga, el pantano conserva.", color=DORADO),
        ],
    },
}


def apertura(faccion):
    datos = APERTURAS.get(faccion, APERTURAS["humano"])
    return [dict(e) for e in datos["escenas"]], datos.get("musica")


INTRO = {
    "musica": "musica_explora",
    "escenas": [
        esc("EL UMBRAL DEL TRONO", fondo="amanecer", efecto="titulo", color=DORADO),
        esc("Hubo un tiempo en que el mundo amanecia sin ceniza y las cartas eran solo un juego.",
            fondo="amanecer"),
        esc("Entonces el cielo se rajo. Por la grieta asomo el Umbral... y el juego se volvio guerra.",
            fondo="umbral"),
        esc("Siete bandos afilaron sus barajas. El trono no se hereda: se gana carta a carta.",
            fondo="estandartes"),
        esc("Elige tu faccion. Forja tu final.", fondo="trono", color=DORADO),
    ],
}


def intro():
    """Cinematica inicial del juego. Se ve una sola vez (perfil)."""
    return [dict(e) for e in INTRO["escenas"]], INTRO["musica"]


def escenas_nodo(info):
    """Cartel de escenario antes de cada duelo.

    Son tres bloques: la previa de campana.NODOS (el tono del nodo), la previa
    de narrativa (el caracter y la decision), y la presentacion del rival.
    """
    escenas = []
    escena_fondo = info.get("escena", "campamento")
    nodo_id = info.get("nodo", "")
    for previa in info.get("previa", []):
        escenas.append(esc(previa, fondo=escena_fondo))
    # Caracter del nodo: por que estas aqui y que hay que decidir.
    escenas.extend(narrativa.previa_nodo(nodo_id))
    rival = info["bando"]
    # El retrato puede ser el del personaje con nombre (Pik, Dara...) en vez
    # del bando. El color de la musica y del acento sigue siendo el del bando.
    retrato = duelistas.retrato_de(nodo_id, rival)
    musica = audio.musica_de_faccion(rival)
    escenas.append(esc(f"{info['nombre']}, {info['titulo_duelo']}.",
                       hablante=info["nombre"], retrato=retrato,
                       fondo=escena_fondo, musica=musica))
    # El rival ve tu mazo y reacciona: la reaccion del rol tiene prioridad
    # sobre la linea generica de faccion.
    reaccion = info.get("reaccion_rol")
    if reaccion:
        escenas.append(esc(reaccion, hablante=info["nombre"], retrato=retrato,
                           fondo=escena_fondo, color=TEXTO_ON))
    else:
        escenas.append(esc(info.get("entrada", ""), hablante=info["nombre"],
                           retrato=rival, fondo=escena_fondo, color=TEXTO_ON))
    # Dialogo del rol: por que pelea este rival en este nodo.
    for e in info.get("dialogo_pre", []):
        escena = dict(e)
        escena["fondo"] = escena_fondo
        if not escena.get("retrato"):
            escena["retrato"] = retrato
        escenas.append(escena)
    return escenas, musica


def escenas_posterior(info, victoria=True):
    """Escenas de DESPUES del duelo: consecuencia y avance del misterio."""
    nodo = info.get("nodo", "")
    escena_fondo = info.get("escena", "campamento")
    escenas = list(narrativa.posterior_nodo(nodo))
    # Como termino el duelo, en la voz del rival.
    for e in duelistas.dialogo_de(nodo, "win" if victoria else "lose",
                                  info.get("nombre", "")):
        escena = dict(e)
        escena["fondo"] = escena_fondo
        if not escena.get("retrato"):
            escena["retrato"] = duelistas.retrato_de(nodo, info.get("bando"))
        escenas.append(escena)
    faccion = info.get("faccion_jugador")
    if faccion:
        linea = narrativa.reaccion_mazo(faccion)
        if linea:
            escenas.append(esc(linea, fondo=escena_fondo))
    momento = "victoria" if victoria else "derrota"
    linea = narrativa.nara_linea(momento, info.get("confianza_nara", 0))
    if linea:
        escenas.append(esc(linea, hablante="Nara", fondo=escena_fondo, color=TEXTO_ON))
    return escenas


def escenas_final(titulo, lineas, faccion, extra=None):
    """Carta de titulo y el epilogo final."""
    escenas = [esc(titulo, fondo="trono", efecto="titulo", color=DORADO)]
    for linea in lineas:
        escenas.append(esc(linea, fondo="trono"))
    for linea in extra or []:
        escenas.append(esc(linea, fondo="trono", color=TEXTO_TENUE))
    return escenas, audio.musica_de_faccion(faccion)


async def reproducir(screen, clock, escenas, musica=None, al_terminar=None, permitir_saltar=True):
    await Cinematica(escenas, al_terminar=al_terminar, musica=musica,
                     permitir_saltar=permitir_saltar).ejecutar(screen, clock)
