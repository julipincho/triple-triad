"""Motor de cinematicallyas: bandas letterbox, fundidos, maquina de escribir,
retratos, dialogo y cambio de musica.

Las escenas se describen con datos (diccionarios) para que la campana pueda
componer secuencias sin codigo nuevo:

    {"fondo": "ceniza", "hablante": "Aldric", "texto": "...",
     "retrato": "humano", "efecto": "titulo", "musica": "musica_humano"}
"""

import time
import os

import pygame

import audio
import arte_visual
import duelistas
import ui  # `ruta_fondo`: elige la variante de fondo con la semilla de partida
import facciones
import narrativa
import opciones
from idioma import espanol
import peticiones
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
        import lotes_visuales
        self.fondo_lote = lotes_visuales.fondo(datos)
        self.fondo = datos.get("fondo", "ceniza")
        self.fondo_hd = datos.get("fondo_hd")
        self.hablante = datos.get("hablante")
        self.texto = espanol(datos.get("texto", ""))
        self.retrato = datos.get("retrato") or retrato_hablante(self.hablante)
        self.efecto = datos.get("efecto", "dialogo")
        # `or TEXTO` y no `datos.get("color", TEXTO)`: varios productores de
        # escenas pasan la clave CON valor None (`duelistas._esc` y
        # `finales.esc` tienen `color=None` por defecto), y `get` con defecto
        # no cubre ese caso porque la clave existe. Con None colado,
        # `ui._superficie_texto` revienta en `len(None)` y tumba la pantalla.
        # Toda escena pasa por aca, asi que normalizar aqui cierra el
        # problema para todos los productores, viejos y futuros.
        self.color = datos.get("color") or TEXTO
        self.musica = datos.get("musica")
        self.mundo = datos.get("mundo", MUNDO_JUEGO)
        self.duracion = datos.get("duracion")
        self.mostrado = 0.0

    @property
    def completa(self):
        return self.mostrado >= len(self.texto)


class Cinematica:
    """Secuencia reproducible de escenas, bloqueante."""

    def __init__(self, escenas, al_terminar=None, musica=None, permitir_saltar=True,
                 nombre_jugador="", bucle=True):
        # El nombre del jugador se resuelve UNA VEZ, aqui, al construir la
        # secuencia. Por frame seria un `str.replace` sobre cada linea en cada
        # frame; y leer el perfil seria una lectura de disco por frame.
        self.nombre_jugador = duelistas.DEFECTO_JUGADOR if not nombre_jugador else nombre_jugador
        # Las dos opciones de Ajustes. Se leen UNA vez aqui, al construir la
        # secuencia, para no consultar nada por frame.
        self.saltar_todo = opciones.saltar_cinematica()
        self.sin_texto = opciones.saltar_dialogo()
        propias = [e if isinstance(e, Escena) else Escena(e) for e in escenas]
        for e in propias:
            self._resolver_jugador(e)
        self.escenas = propias
        self.al_terminar = al_terminar
        self.musica = musica
        # Las pistas de fondo se repiten; el apagón del prologo es un golpe
        # puntual y sonaría entero otra vez si se leiese en bucle.
        self.bucle = bucle
        self.permitir_saltar = permitir_saltar
        self.i = 0
        self._t_escena = time.time()
        # Indice de la ultima escena anotada en el diario. Se anota una vez por
        # escena y no por frame: el diario se escribe en disco.
        self._anotado = -1

    def _resolver_jugador(self, escena):
        """Cambia `__JUGADOR__` por el nombre en `texto` y en `hablante`."""
        for campo in ("texto", "hablante"):
            valor = getattr(escena, campo, None)
            if isinstance(valor, str) and duelistas.PLACEHOLDER_JUGADOR in valor:
                setattr(escena, campo,
                        valor.replace(duelistas.PLACEHOLDER_JUGADOR, self.nombre_jugador))

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

    def _anotar(self, escena):
        """Guarda en el diario una escena de dialogo, una sola vez.

        Los rotulos (`efecto == "titulo"`) no son dialogo y no entran. El
        diario es opcional: si el perfil no se puede escribir, la cinematica
        no debe caerse por eso.
        """
        if escena.efecto == "titulo" or not escena.texto:
            return
        if self.i <= self._anotado:
            return
        self._anotado = self.i
        try:
            import campana
            campana.registrar_dialogo(escena.hablante or "", escena.texto)
        except Exception:  # noqa: BLE001 - el diario nunca tumba una escena
            pass

    async def ejecutar(self, screen, clock):
        if not self.escenas:
            if self.al_terminar:
                self.al_terminar()
            return

        # "Saltar cinematica" de Ajustes se lleva por delante TODO, incluida la
        # proteccion de los finales: para eso existe esa opcion, para quien esta
        # probando y no quiere esperar a que un epilogo de 40 escenas termine.
        # Viene desactivada, asi que el juego de verdad no cambia: el epilogo
        # sigue sin poder saltarse con ESC (ver `permitir_saltar`).
        if opciones.saltar_cinematica():
            self.i = len(self.escenas)
            self._terminar()
            return

        self._t_escena = time.time()
        audio.sfx(audio.CINEMA)
        audio.musica(self.escenas[0].musica or self.musica, bucle=self.bucle)

        while True:
            clock.tick(LIMIT_FPS)
            await asyncio.sleep(0)
            escena = self.escena()
            if escena is None:
                break
            self._anotar(escena)
            if escena.musica:
                audio.musica(escena.musica)
            t = time.time() - self._t_escena
            if escena.efecto == "titulo":
                escena.mostrado = (len(escena.texto)
                                   if t > 0.4 or self.sin_texto else 0)
            else:
                # Con "sin texto" el texto sale entero y sin maquina de
                # escribir: las escenas se ven pero se advances con ENTER.
                if self.sin_texto:
                    escena.mostrado = len(escena.texto)
                else:
                    escena.mostrado = min(
                        len(escena.texto),
                        max(0.0, t - 0.3) * VELOCIDAD_ESCRITURA)
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
        fondo_hd = None
        if FONDOS_CINEMATICOS_HD and escena.fondo_hd:
            fondo_hd = REC.fondo_cinematico(
                os.path.join("assets", "cinematicas_hd", escena.fondo_hd))
        if FONDOS_CINEMATICOS_HD and not escena.fondo_hd:
            # La variante se resuelve antes de buscar arte nuevo. Un HD
            # explicito de los lotes aprobados siempre conserva prioridad.
            nueva = escena.fondo_lote or arte_visual.alternativa(ui.ruta_fondo(escena.fondo), "fondo")
            if nueva:
                fondo_hd = REC.fondo_cinematico(nueva)
        if fondo_hd is not None:
            screen.blit(fondo_hd, (0, 0))
        else:
            screen.blit(REC.fondo_pantalla(ui.ruta_fondo(escena.fondo)), (0, 0))
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
        # Un titulo largo se sale de la pantalla: se encoge hasta que entra,
        # con un minimo de 14px. Antes solo se elegia entre 34 y 26 por longitud
        # del texto, asi que cualquier frase de +53 caracteres se salia.
        ancho_max = ANCHO - 100
        while tam > 14 and REC.fuente(tam).size(escena.texto)[0] > ancho_max:
            tam -= 1
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
            self._retrato(screen, escena.retrato, t, escena.hablante)
        elif escena.hablante:
            ancho_txt = REC.fuente(13).render(escena.hablante, True, DORADO).get_width()
            rect = pygame.Rect(60, LINEA_BARRA + 24, ancho_txt + 40, 32)
            panel(screen, rect, (12, 12, 20, 214), DORADO, radio=6, grosor=1, sombra=False)
            texto(screen, escena.hablante, 13, DORADO, x=rect.x + 16, y=rect.y + 9)

        lineas = envoltura_lineas(escena.texto, 12, ANCHO - 300)
        interlinea = max(26, ui.alto_texto("Áñ", 12) + 8)
        alto = max(152, len(lineas) * interlinea + 72)
        caja = pygame.Rect(120, ALTO - 60 - alto, ANCHO - 240, alto)
        panel(screen, caja, (10, 11, 18, 226), con_alpha(DORADO, 190), radio=8)
        restantes = int(escena.mostrado)
        y = caja.y + 26
        for linea in lineas:
            if restantes <= 0:
                break
            trozo = linea[:restantes]
            texto(screen, trozo, 12, escena.color, x=caja.x + 30, y=y)
            restantes -= len(linea) + 1
            y += interlinea
        if escena.completa:
            pista = REC.fuente(8).render("clic para continuar", True, TEXTO_TENUE)
            screen.blit(pista, (caja.right - pista.get_width() - 24, caja.bottom - 26))

    def _retrato(self, screen, bando, t, hablante=None):
        """Retrato de un bando o de un personaje concreto.

        La clave es el nombre del archivo (`avatar_<clave>.png`), asi que tanto
        `goblin` como `nara` funcionan igual. Lo que cambia es la etiqueta: para
        un bando sale el nombre de la faccion; para un personaje, el suyo.
        """
        entrada = ease(min(1.0, t / 0.5))
        ruta = (f"assets/escenas/{bando.split(':', 1)[1]}.png"
                if bando.startswith("encuentro:") else f"assets/avatar_{bando}.png")
        img = REC.imagen(ruta, (150, 150))
        x = ANCHO // 2 + 200
        y = LINEA_BARRA + 76 + int((1 - entrada) * -26)
        marco = pygame.Rect(x, y, 150, 150)
        pygame.draw.rect(screen, (10, 10, 16), marco.inflate(12, 12), 3, border_radius=4)
        screen.blit(img, (x, y))
        resplandor(screen, marco, facciones.acento(bando), int(110 * entrada), 2, 4)
        etiqueta = hablante or _etiqueta_retrato(bando)
        for i, linea in enumerate(ui.envolver(etiqueta, 9, 220)):
            texto(screen, linea, 9, TEXTO_ON, centro=(x + 75, y + 168 + i * 20))

    def _barras(self, screen):
        """Barras cinematograficas: ya no hacen falta.

        Los fondos se escalan con factor entero y dejan su propio letterbox
        (ver `ui.Recursos._escalar_pixelart`): con el factor 3 sobre un fondo
        de 512x256 sobran 16px arriba y 16px abajo. Encima de eso, las barras
        de 46px quitaban un 11% mas de altura sin aportar nada: el negro ya
        esta y la imagen ya viene enmarcada.

        Se conservan solo si el fondo llega a pantalla completa (un asset
        reescalado a 1280x800), donde si son el marco de la escena.
        """
        escena = self.escena()
        nombre = getattr(escena, "fondo", None) if escena else None
        if not nombre:
            return
        # La MISMA ruta que dibuja el fondo, y no la del original: si aqui se
        # midieran las barras del `camino.png` mientras se dibuja
        # `camino_lluvia.png`, las dos imagenes tienen letterbox distinto y se
        # mediria el marco de una sobre la otra.
        ruta = ui.ruta_fondo(nombre)
        REC.fondo_pantalla(ruta)  # asegura que el letterbox esta registrado
        # `barras_de` dice si la imagen escalada traia su propio letterbox.
        # Si lo trae, estas barras de 46px serian un segundo marco encima: no
        # aportan nada y se comen un 11% mas de altura. Solo se pintan cuando
        # la imagen llega justa a pantalla completa.
        v, _h = REC.barras_de(ruta)
        if v or _h:
            return
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
    "presentador": "El Presentador",
}


def retrato_hablante(hablante):
    """Resuelve retratos omitidos sin heredar la cara de quien hablo antes."""
    if not hablante:
        return None
    nombres = {
        "nara": "nara", "nara, la cronista": "nara",
        "__jugador__": "duelista", "el duelista": "duelista",
        "juan rajoy": "rajoy", "presentador": "presentador",
        "el presentador": "presentador", "pik": "pik", "dara": "dara",
        "aldric": "humano", "vorg": "orco", "grix": "goblin",
        "lyra": "elfo", "fenris": "hombre_lobo", "condesa": "vampiro",
        "la condesa": "vampiro", "ignarok": "dragon", "sylwen": "elfo_nocturno",
        "zarkha": "hombre_pantera", "sskar": "hombre_lagarto",
        "mercader errante": "encuentro:mercader",
        "el anciano del umbral": "encuentro:anciano",
        "hermandad de armas": "encuentro:hermandad",
        "caravana de sobres": "encuentro:caravana",
        "alguien te ha visto": "encuentro:hostil",
        # El Cartógrafo / Maestro de la Mesa: usa el avatar de gobernante
        "el maestro de la mesa": "gobernante",
    }
    return nombres.get(hablante.casefold())


def _etiqueta_retrato(clave):
    """Como se llama al dueno del retrato, sea bando o personaje."""
    if clave.startswith("encuentro:"):
        import encuentros
        return encuentros.titulo_encuentro(clave.split(":", 1)[1])
    if clave in ETIQUETAS_RETRATO:
        return ETIQUETAS_RETRATO[clave]
    return facciones.nombre(clave)


# --------------------------------------------------------------- argumento
#: treatment visual de cada mundo. "real" = el salon del torneo de nuestro
#: mundo: luz fria, sin vineta. "juego" = el mundo fantastic: oscuro, con
#: vineta. La diferencia tiene que notarse sin que nadie lo diga.
MUNDO_REAL = "real"
MUNDO_JUEGO = "juego"

# Reversible sin retirar los PNG: `False` vuelve al selector de fondos
# originales, conservando intacta la resolucion global y los assets HD.
FONDOS_CINEMATICOS_HD = os.environ.get("TRIPLETRIAD_CINEMATICAS_HD", "1") != "0"

#: Tinte y vineta por mundo: (color RGB, alpha de capa, vineta alfa).
#:
#: El tinte daba 55-60% de oscurecido en el mundo del juego y 21% en el
#: nuestro, y eso hacia que el fondo se viera como otra cosa y no como el arte
#: que se genero. Un tinte tiene que SENTIRSE, no tapar: la diferencia entre
#: los dos mundos sigue notandose (mas frio y mas claro el nuestro, con
#: vineta el del juego), pero el fondo se ve como es.
#:
#: Bajar esto no afecta la legibilidad: el texto vive en su propio panel
#: oscuro (`panel(screen, caja, (10, 11, 18, 226))`), no sobre el fondo.
TRATAMIENTO = {
    MUNDO_JUEGO: ((8, 10, 20), 86, (46, 72)),
    MUNDO_REAL: ((20, 28, 46), 38, (0, 0)),
}


def esc(linea, hablante=None, fondo="ceniza", retrato=None, efecto="dialogo",
        musica=None, color=TEXTO, mundo=MUNDO_JUEGO, fondo_hd=None):
    # Todas las escenas cuya clave narrativa ya es "trono" pueden usar el
    # interior aprobado. Un callsite que no deba usarlo puede indicar otro
    # fondo narrativo en vez de heredar esta clave.
    if fondo == "trono" and fondo_hd is None:
        fondo_hd = "sala_trono.png"
    return {"texto": linea, "hablante": hablante, "fondo": fondo, "retrato": retrato,
            "efecto": efecto, "musica": musica, "color": color, "mundo": mundo,
            "fondo_hd": fondo_hd}


APERTURAS = {
    "humano": {
        "musica": "musica_humano",
        "escenas": [
            esc("La noche cae sobre un reino que ya no es un reino: solo ceniza y cuatro murallas."),
            esc("El rey Aldric no tiene ejercito. Tiene una correo, dos espadas y una promesa.",
                hablante="Aldric", retrato="humano"),
            esc("Juegas con el mazo humano. Nadie mas en este mundo juega con el.",
                hablante="Aldric", retrato="humano", color=TEXTO_ON),
            esc("Eres el ultimo resto de una especie que se niega a desaparecer.", color=DORADO),
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
    """Cinematica de apertura de la faccion elegida.

    Le agrega las dos escenas que faltaban y que son las que contestan
    "que quieren del trono" y "por que te ayudan a vos". Sin ellas el
    dialogo queda colgado: el bando te habla de vos y de las cartas, pero nunca
    del pacto que te esta ofreciendo. El texto vive en `peticiones.py`, una
    sola vez para las diez.
    """
    datos = APERTURAS.get(faccion, APERTURAS["humano"])
    escenas = [dict(e) for e in datos["escenas"]]
    # Resolver por secuencia/facción: varias aperturas comparten claves como
    # ``trono`` y ``ruinas`` con otras cinemáticas y pantallas.
    fondos_hd = {
        "humano": "apertura_humano_reino_en_cenizas.png",
        "orco": "apertura_orco_frontera_muralla.png",
        "goblin": "apertura_goblin_puerta_bajo_foso.png",
        "elfo": "apertura_elfo_bosque_silencioso.png",
        "hombre_lobo": "apertura_hombre_lobo_ciudad_lunar.png",
        "vampiro": "apertura_vampiro_cripta_pacto_roto.png",
        "dragon": "apertura_dragon_cielo_brasa.png",
        "elfo_nocturno": "apertura_elfo_nocturno_bosque_umbral.png",
        "hombre_pantera": "apertura_pantera_tejados_ciudad.png",
        "hombre_lagarto": "apertura_lagarto_pantano_ruinas.png",
    }
    fondo_hd = fondos_hd.get(faccion, fondos_hd["humano"])
    for escena in escenas:
        escena["fondo_hd"] = fondo_hd
    pide = peticiones.peticion(faccion)
    ayuda = peticiones.por_que_te_ayudan(faccion)
    if not pide or not ayuda:
        return escenas, datos.get("musica")
    # el hablante y el retrato son los de la propia apertura: la misma voz
    voz = next((e for e in escenas if e.get("hablante")), None)
    hablante = voz["hablante"] if voz else None
    retrato = voz.get("retrato") if voz else None
    fondo = escenas[-1]["fondo"]
    # se insertan antes del cierre, que es la frase de relevo del bando
    cierre = escenas.pop() if len(escenas) > 1 else None
    escenas.append(esc("- " + pide, hablante=hablante, retrato=retrato,
                       fondo=fondo, color=TEXTO_ON, fondo_hd=fondo_hd))
    escenas.append(esc("- " + ayuda, hablante=hablante, retrato=retrato,
                       fondo=fondo, fondo_hd=fondo_hd))
    if cierre is not None:
        escenas.append(cierre)
    return escenas, datos.get("musica")


INTRO = {
    "musica": "musica_explora",
    "escenas": [
        esc("EL UMBRAL DEL TRONO", fondo="amanecer", efecto="titulo", color=DORADO,
            fondo_hd="intro_amanecer_mundo_antiguo.png"),
        esc("Hubo un tiempo en que el mundo amanecia sin ceniza y las cartas eran solo un juego.",
            fondo="amanecer", fondo_hd="intro_amanecer_mundo_antiguo.png"),
        esc("Entonces el cielo se rajo. Por la grieta asomo el Umbral... y el juego se volvio guerra.",
            fondo="umbral", fondo_hd="intro_grieta_umbral_cielo.png"),
        esc("Siete bandos afilaron sus barajas. El trono no se hereda: se gana carta a carta.",
            fondo="estandartes", fondo_hd="intro_estandartes_siete_bandos.png"),
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
    retrato = info.get("retrato") or duelistas.retrato_de(nodo_id, rival)
    musica = audio.musica_de_faccion(rival)
    escenas.append(esc(f"{info['nombre']}, {info['titulo_duelo']}.",
                       hablante=info["nombre"], retrato=retrato,
                       fondo=escena_fondo, musica=musica))
    # El rival ve tu mazo y reacciona: la reaccion del rol tiene prioridad
    # sobre la linea generica de faccion.
    reaccion = info.get("reaccion_rol")
    if reaccion:
        escenas.append(esc("El rival senala la figura de tu carta. Le habla como "
                           "si pudiera oirlo.", fondo=escena_fondo))
        escenas.append(esc(reaccion, hablante=info["nombre"], retrato=retrato,
                           fondo=escena_fondo, color=TEXTO_ON))
    else:
        escenas.append(esc(info.get("entrada", ""), hablante=info["nombre"],
                            retrato=retrato, fondo=escena_fondo, color=TEXTO_ON))
    # Dialogo del rol: por que pelea este rival en este nodo.
    for e in info.get("dialogo_pre", []):
        escena = dict(e)
        escena["fondo"] = escena_fondo
        if not escena.get("retrato"):
            escena["retrato"] = retrato
        escenas.append(escena)
    _continuidad_nodo_hd(escenas, nodo_id)
    return escenas, musica


def escenas_posterior(info, victoria=True):
    """Escenas de DESPUES del duelo: consecuencia y avance del misterio."""
    nodo = info.get("nodo", "")
    escena_fondo = info.get("escena", "campamento")
    escenas = (list(narrativa.posterior_nodo(nodo)) if victoria else [
        esc("El paso sigue cerrado. Recoges tus cartas: tendras que volver "
            "a intentarlo.", fondo=escena_fondo)])
    # Como termino el duelo, en la voz del rival. El nombre del jugador llega
    # ya resuelto en `info`: quien arma `info` es `campana.info_duelo`, que lo
    # lee del perfil. Sin el, `__JUGADOR__` vale "el duelista".
    for e in duelistas.dialogo_de(nodo, "win" if victoria else "lose",
                                  info.get("nombre", ""),
                                  info.get("nombre_jugador", "")):
        escena = dict(e)
        escena["fondo"] = escena_fondo
        if not escena.get("retrato"):
            escena["retrato"] = info.get("retrato") or duelistas.retrato_de(nodo, info.get("bando"))
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
    _continuidad_nodo_hd(escenas, nodo)
    return escenas


def _continuidad_nodo_hd(escenas, nodo):
    """Completa solo planos conocidos; incluye dialogos de rol sin esc()."""
    destino = {"senda": ("camino", "camino_lluvioso.png"),
               "aldea": ("aldea", "campana_aldea_20261015.png"),
               "ruinas": ("ruinas", "campana_ruinas_20261015.png"),
               "fortaleza": ("fortaleza", "campana_fortaleza_20261015.png"),
               "asalto": ("asalto", "campana_asalto_20261015.png"),
               "mini_senda": ("umbral", "campana_umbral_20261015.png"),
               "mini_nudo": ("estandartes", "intro_estandartes_siete_bandos.png"),
               "mini_trono": ("trono", "sala_trono.png"),
               "trono": ("trono", "sala_trono.png")}.get(nodo)
    if destino:
        clave, archivo = destino
        for escena in escenas:
            if escena.get("fondo") == clave and not escena.get("fondo_hd"):
                escena["fondo_hd"] = archivo


def escenas_final(titulo, lineas, faccion, extra=None):
    """Carta de titulo y el epilogo final."""
    escenas = [esc(titulo, fondo="trono", efecto="titulo", color=DORADO)]
    for linea in lineas:
        escenas.append(esc(linea, fondo="trono"))
    for linea in extra or []:
        escenas.append(esc(linea, fondo="trono", color=TEXTO_TENUE))
    return escenas, audio.musica_de_faccion(faccion)


async def reproducir(screen, clock, escenas, musica=None, al_terminar=None,
                     permitir_saltar=True, nombre_jugador=None, clave=None,
                     marcar_vista=True, bucle=True):
    """Reproduce una secuencia de escenas.

    `nombre_jugador` es opcional: si no se pasa, se lee del perfil. Resolve el
    marcador `__JUGADOR__` una vez al construir la secuencia, nunca por frame.
    Se lee de `campana` aqui y no en las 20 llamadas porque `campana` no importa
    `cinematicas`, asi que no hay ciclo; y `campana.nombre_jugador()` esta
    cacheado, que es lo que hace que se pueda llamar sin coste.

    `clave` identifica la secuencia para el diario de escenas vistas. Si ya se
    vio y la secuencia es larga, se ofrece saltarla conservando la opcion de
    volver a verla; las escenas cortas (carteles de duelo) no interrumpen.
    """
    if nombre_jugador is None:
        import campana
        nombre_jugador = campana.nombre_jugador()
    escenas = list(escenas)
    ya_vista = False
    if clave:
        import campana
        ya_vista = clave in campana.cinematicas_vistas()
        if marcar_vista and not ya_vista:
            campana.marcar_cinematica(clave)
    # El aviso solo se justifica para escenas de verdad, no para carteles de
    # una o dos lineas que se leen en dos segundos.
    if ya_vista and permitir_saltar and len(escenas) >= 3:
        if await _preguntar_rever(screen, clock):
            return
    await Cinematica(escenas, al_terminar=al_terminar, musica=musica,
                     permitir_saltar=permitir_saltar,
                     nombre_jugador=nombre_jugador, bucle=bucle).ejecutar(screen, clock)


async def _preguntar_rever(screen, clock):
    """Aviso de escena ya vista. True = saltar, False = volver a verla."""
    while True:
        clock.tick(LIMIT_FPS)
        await asyncio.sleep(0)
        screen.blit(REC.fondo_pantalla("assets/pixel_anime/detalles/escena_vista_v2.png"), (0, 0))
        screen.blit(REC.capa_oscurita((8, 8, 18, 80)), (0, 0))
        panel(screen, pygame.Rect(ANCHO // 2 - 350, ALTO // 2 - 104, 700, 172),
              (14, 15, 28, 232), (132, 94, 184), radio=12)
        texto(screen, "ESCENA YA VISTA", 22, DORADO, centro=(ANCHO // 2, ALTO // 2 - 70))
        texto(screen, "ENTER o clic: saltar y seguir", 12, TEXTO,
              centro=(ANCHO // 2, ALTO // 2 - 10))
        texto(screen, "ESPACIO: volver a verla", 12, TEXTO_TENUE,
              centro=(ANCHO // 2, ALTO // 2 + 28))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_SPACE:
                    return False
                return True
            if ev.type == pygame.MOUSEBUTTONDOWN:
                return True
