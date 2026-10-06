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
import facciones
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
        # fondo, oscurecido y vineta cacheados (sin reservas por frame)
        screen.blit(REC.fondo_pantalla(f"assets/fondos/{escena.fondo}.png"), (0, 0))
        screen.blit(REC.capa_oscurita((6, 7, 14, 168)), (0, 0))
        screen.blit(REC.vineta(50, 80), (0, 0))

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
        entrada = ease(min(1.0, t / 0.5))
        img = REC.imagen(f"assets/avatar_{bando}.png", (150, 150))
        x = ANCHO // 2 + 200
        y = LINEA_BARRA + 76 + int((1 - entrada) * -26)
        marco = pygame.Rect(x, y, 150, 150)
        pygame.draw.rect(screen, (10, 10, 16), marco.inflate(12, 12), 3, border_radius=4)
        screen.blit(img, (x, y))
        resplandor(screen, marco, facciones.acento(bando), int(110 * entrada), 2, 4)
        texto(screen, facciones.nombre(bando), 9, facciones.acento(bando), centro=(x + 75, y + 168))

    def _barras(self, screen):
        barra = pygame.Surface((ANCHO, LINEA_BARRA), pygame.SRCALPHA)
        barra.fill((0, 0, 0, 238))
        screen.blit(barra, (0, 0))
        screen.blit(barra, (0, ALTO - LINEA_BARRA))


# --------------------------------------------------------------- argumento
def esc(linea, hablante=None, fondo="ceniza", retrato=None, efecto="dialogo",
        musica=None, color=TEXTO):
    return {"texto": linea, "hablante": hablante, "fondo": fondo, "retrato": retrato,
            "efecto": efecto, "musica": musica, "color": color}


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
}


def apertura(faccion):
    datos = APERTURAS.get(faccion, APERTURAS["humano"])
    return [dict(e) for e in datos["escenas"]], datos.get("musica")


def escenas_nodo(info):
    """Cartel de escenario antes de cada duelo."""
    escenas = []
    escena_fondo = info.get("escena", "campamento")
    for previa in info.get("previa", []):
        escenas.append(esc(previa, fondo=escena_fondo))
    rival = info["bando"]
    musica = audio.musica_de_faccion(rival)
    escenas.append(esc(f"{info['nombre']}, {info['titulo_duelo']}.",
                       hablante=info["nombre"], retrato=rival,
                       fondo=escena_fondo, musica=musica))
    escenas.append(esc(info.get("entrada", ""), hablante=info["nombre"],
                       retrato=rival, fondo=escena_fondo, color=TEXTO_ON))
    return escenas, musica


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
