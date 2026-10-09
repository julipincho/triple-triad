"""La partida: tablero, HUD, interaccion, efectos e IA.

`partida()` es bloqueante y devuelve un `Resultado` con lo que la campana
necesita para registrar el duelo (victoria, capturas, cartas jugadas).
"""

import copy
import math
import random
import time

import pygame

import audio
import campana
import cartas as crt
import facciones
import ui
from reglas import (
    CPU,
    LADOS,
    USUARIO,
    cascada,
    celdas_vacias,
    capturas,
    contar,
    puntaje_final,
    resumen_efectos,
    simular,
    val,
    valor_efectivo,
)
from ui import (
    ALTO,
    ANCHO,
    AZUL,
    BORDE,
    CARD_H,
    CARD_W,
    DORADO,
    LIMIT_FPS,
    MEDIR,
    REC,
    ROJO,
    TABLERO_H,
    TABLERO_W,
    TABLERO_Y,
    TEXTO,
    TEXTO_ON,
    TEXTO_TENUE,
    VERDE,
    ancho_texto,
    celda_rect,
    con_alpha,
    dibujar_tooltips,
    ease,
    envolver,
    fundido_entrada,
    mano_rect,
    mezcla,
    panel,
    registrar,
    resplandor,
    texto,
    tooltip,
)

import asyncio

SLOT_BG = (28, 30, 40)
SLOT_BORDE = (92, 84, 62)

#: Los efectos con nombre que el cartel enseña: `(titulo, explicacion)`.
#:
#: Los titulos son los mismos que usa `tutorial.py`, en las mismas palabras, para
#: que el cartel y el tutorial no enseñen dos nombres distintos para lo mismo.
#: La explicacion es corta a proposito: cabe en una linea y se lee mientras el
#: tablero sigue moviendose.
#:
#: El cartel sale SIEMPRE, aunque el efecto se haya visto cien veces. La idea
#: es no depender del tutorial, y un cartel que solo aparece las tres primeras
#: veces obliga a recordar las reglas en cuanto deja de hacerlo.
EFECTOS = {
    "same": ("SAME", "caen dos vecinas porque igualan tu numero"),
    "plus": ("PLUS", "caen dos vecinas porque sus sumas coinciden"),
}

#: Tiempos del cartel, en segundos. Entrada rapida para que se lea al instante,
#: cuerpo largo para que se pueda leer entero, y salida mas lenta que la
#: entrada: si se fuera tan rapido como aparece, el ojo soloeria el parpadeo.
ENTRADA_EFECTO = 0.22
DURACION_EFECTO = 2.0
SALIDA_EFECTO = 0.5


def _caja_efecto(rect):
    """Contenedora de la auditoria visual: el cartel no esta dentro de ningun
    panel, asi que se declara aqui para que no se cuente como texto suelto."""
    return "partida"


def _sombra_carta(screen, rect, off=(3, 5), big=False):
    """Sombra oscura y redondeada tras una carta: la misma firma visual
    en tablero, mano, arrastre y preview.

    Solo hay tres tamaños en juego (carta, preview grande, tablero), asi que
    la cache se queda en tres entradas: antes se pintaba una Surface nueva
    por carta y por frame."""
    sombra = ui.superficie(
        ("sombra_carta", rect.w, rect.h, big),
        lambda: _sombra_carta_superficie(rect.w, rect.h, big),
    )
    screen.blit(sombra, (rect.x + off[0], rect.y + off[1]))


def _sombra_carta_superficie(w, h, big):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 140 if big else 110), s.get_rect(), border_radius=8)
    return s


def _tinte_casilla(w, h, halo):
    """Halo del dominio sobre una casilla: relleno tintado + borde."""
    s = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)
    s.fill(con_alpha(halo, 30))
    pygame.draw.rect(s, con_alpha(halo, 150), (2, 2, w + 6, h + 6), 3, border_radius=9)
    return s


def _overlay_captura(alpha_nivel, color):
    """Velillo de color de una captura, cacheado por nivel de alpha."""
    clave = ui.color_cache(color)
    return ui.superficie(
        ("overlay_captura", alpha_nivel) + clave,
        lambda: _overlay_captura_lento(alpha_nivel, clave),
    )


def _overlay_captura_lento(alpha_nivel, color):
    s = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    s.fill(con_alpha(color, alpha_nivel * 8))
    return s


def _caja_llena(w, h, color):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(s, color, s.get_rect(), border_radius=10)
    return s


class Resultado:
    def __init__(self, victoria, capturas, jugadas, marcador, empate=False, racha=0):
        self.victoria = victoria
        self.capturas = capturas
        self.jugadas = jugadas
        self.marcador = marcador
        self.empate = empate
        self.racha = racha

    def __bool__(self):
        return self.victoria


class Juego:
    """Estado y dibujo de un duelo."""

    def __init__(self, bando_jugador, bando_rival=None, mano_u_inicial=None,
                 mano_c_inicial=None, info=None, en_campana=False, dificultad=0):
        import mazos

        self.bando = bando_jugador
        self.bando_cpu = bando_rival or random.choice(
            [b for b in mazos.TODOS if b != bando_jugador]
        )
        self.info = info or {}
        self.en_campana = en_campana
        self.dificultad = dificultad

        # `mano_u_inicial or mazos.TODOS[...]` caia al mazo entero cuando la
        # lista era vacia: `[]` es falsa y `or` tomaba el segundo elemento. El
        # tutorial y el `--test` pasaban a tener 25 cartas en lugar de las que
        # les habian pasado. Ahora se respeta una lista vacia como "sin cartas".
        self.mano_u = [c.copia() for c in (mano_u_inicial if mano_u_inicial is not None
                                            else mazos.TODOS[bando_jugador])]
        self.mano_c = [c.copia() for c in (mano_c_inicial if mano_c_inicial is not None
                                            else mazos.TODOS[self.bando_cpu])]
        for c in self.mano_u:
            c.dueno = USUARIO
        for c in self.mano_c:
            c.dueno = CPU

        self.board = [[None] * 3 for _ in range(3)]
        self.turno_cpu = False
        self.cpu_en_curso = False
        self.cpu_en_cola = 0.0
        self.mensaje = "Tu turno: arrastra una carta al tablero"
        self.arrastrando = None
        self.pos_arrastre = (0, 0)
        self.fin = False
        self.pausa = False
        self.tiempo_fin = 0.0

        self.capturas = 0
        self.jugadas = 0
        self.racha = 0
        self.cadena_max = 0

        self.flash = []          # (r, c, t0, dueno)
        self.particulas = []     # efectos de captura
        self.sacudida = 0.0
        self.ultima_jugada = None
        self.marcador_mostrado = [0, 0]
        self.banner = None       # (titulo, t0, color, subtitulo)
        self.efecto = None       # (nombre, t0, color, subtitulo, regla)
        self._capa_ef = None     # surface de trabajo del cartel
        self._efecto_sup = None  # (clave, cartel ya compuesto)
        self.comentario = None
        self.comentario_t0 = 0.0
        self._sfx_fin = None
        self.ganador = None      # USUARIO, CPU o None (empate)
        self._hover_mano = None
        self._arrastre_valido = False
        self._capa_part = None

        self.rival = self.info or None
        self.comentario = self.rival.get("entrada") if self.rival else None
        self.comentario_t0 = time.time()
        self.t_entrada = time.time()
        # El retrato es del PERSONAJE cuando el info lo trae (Juan, Pik, Vorg...), y
        # de la faccion cuando no. Antes pedia siempre `avatar_<bando>`, asi que
        # en el tutorial se veia un humano en vez de Juan, y en la campana
        # cualquier rival con nombre aparecia como un bando generico.
        clave_retrato = (self.rival.get("retrato") if self.rival else None) \
            or self.bando_cpu
        self.avatar = crt.REC.imagen(f"assets/avatar_{clave_retrato}.png", (96, 96))
        if not self.avatar.get_width():  # sin arte: silueta
            self.avatar = pygame.Surface((96, 96), pygame.SRCALPHA)
            pygame.draw.circle(self.avatar, facciones.acento(self.bando_cpu), (48, 48), 46)
            pygame.draw.circle(self.avatar, (12, 12, 18), (48, 48), 46, 3)

    # ------------------------------------------------------------- utilidades
    def _bando_dueno(self, carta):
        """Que baraja manda ahora sobre la carta, para teñirla de su color.

        Una carta puede haber cambiado de bando mil veces en la partida: lo que
        cuenta es de quien es AHORA, no de quien es por su faccion.
        """
        if carta.dueno == USUARIO:
            return self.bando
        if carta.dueno == CPU:
            return self.bando_cpu
        return None

    def super_cartas(self, carta, synergy=None):
        if synergy is None:
            synergy = crt.tiene_sinergia(carta, self.board)
        return crt.crear(carta, carta.dueno, synergy=synergy,
                         bando_dueno=self._bando_dueno(carta))

    def _color_dueno(self, dueno):
        """Color de la baraja que domina cada bando: el duelo habla en
        los colores de los dos mazos, no en azul/rojo fijos."""
        if dueno == USUARIO:
            return facciones.acento(self.bando)
        if dueno == CPU:
            return facciones.acento(self.bando_cpu)
        return DORADO

    def celdas_libres(self):
        return celdas_vacias(self.board)

    def mejor_celda(self, carta):
        """Mejor casilla para una carta concreta (ayuda visual)."""
        mejor, puntos = None, -1e9
        for (r, c) in celdas_vacias(self.board):
            p = simular(self.board, carta, r, c, USUARIO) + self._bono_posicion(carta, r, c) * 2
            if p > puntos:
                puntos, mejor = p, (r, c)
        return mejor

    def _bono_posicion(self, carta, r, c):
        if carta.habilidad == "embestida" and (r, c) == (1, 1):
            return 1.5
        if facciones.elemento_central(carta.bando) == carta.bando and (r, c) == (1, 1):
            return 1.0
        return 0.0

    def colocar(self, carta, mano, dueno, r, c):
        mano.remove(carta)
        carta.dueno = dueno
        self.board[r][c] = carta
        caps, eventos = cascada(self.board, r, c)
        ahora = time.time()
        self.ultima_jugada = (r, c, ahora)
        for (cr, cc) in caps:
            self.flash.append((cr, cc, ahora, dueno))
            self._explosion(cr, cc, dueno)
        audio.sfx(audio.COLOCAR)
        self.capturas += len(caps)
        self.jugadas += 1
        if caps:
            audio.sfx(audio.CADENA if len(caps) > 1 else audio.CAPTURAR, canal="cap")
            if len(caps) > self.cadena_max:
                self.cadena_max = len(caps)
            if len(caps) >= 3:
                self.sacudida = min(0.55, 0.18 + len(caps) * 0.06)
            self._anunciar_efecto(resumen_efectos(eventos, (r, c)), ahora, dueno)
            clave = "captura_cpu" if dueno == CPU else "captura_player"
            if self.rival and self.rival.get(clave):
                self.comentario = self.rival[clave]
                self.comentario_t0 = ahora
        return caps

    def _anunciar_efecto(self, resumen, ahora, dueno):
        """Nombra el efecto que se acaba de activar.

        Antes de esto, cualquier captura pintaba el mismo texto: `CADENA DE 4`
        tanto si las cuatro cayeron por cadena como si dos cayeron por same y
        dos por plus. El efecto era invisible y no habia forma de aprenderlo
        jugando, solo con el tutorial.

        Se nombra UN efecto, el mas raro, y el resto se cuenta en el subtitulo.
        Enseñar tres nombres a la vez es ruido: el jugador necesita un concepto
        por cartel, no un resumen de la jugada.
        """
        color = self._color_dueno(dueno)
        # El total es la suma de TODO, no solo de `basica` y `cadena`. Sumando
        # solo esas dos, una jugada de 3 por same y 2 por cadena decia
        # "2 cartas" cuando habian caído cinco: el numero que el jugador compara
        # con el tablero de al lado.
        total = sum(v for v in resumen.values() if isinstance(v, int))
        candidatos = [k for k in ("same", "plus") if resumen.get(k)]

        if not candidatos:
            # Sin same ni plus lo unico que puede haber es cadena. Una sola
            # captura no es una cadena: es una captura normal, que ya se ven
            # con el fogonazo y la explosion. Y el numero es el total de cartas
            # que cambiaron de bando, que es lo que mide `cadena_max`, para que
            # el cartel y la pantalla de resultado hablen del mismo numero.
            if total >= 2:
                self.efecto = ("CADENA DE %d" % total, ahora, color,
                               "una carta tumba a las demas por domino",
                               "cadena")
            else:
                self.efecto = None
                self.banner = None
            return

        regla = max(candidatos, key=lambda k: resumen[k])
        titulo, sub = EFECTOS[regla]
        reparto = ["%d por %s" % (resumen[k], EFECTOS[k][0].lower())
                   for k in candidatos]
        if resumen["cadena"]:
            reparto.append("%d por cadena" % resumen["cadena"])
        if resumen["basica"]:
            reparto.append("%d directas" % resumen["basica"])
        self.efecto = (titulo, ahora, color,
                       "%s.  %d cartas: %s" % (sub, total, ", ".join(reparto)),
                       regla)
        # Dos carteles a la vez encima del tablero es ruido, y el efecto raro
        # merece el sitio: una cadena ya se ve sola en las cartas que caen.
        self.banner = None

    def _explosion(self, r, c, dueno):
        rect = celda_rect(r, c)
        color = self._color_dueno(dueno)
        for _ in range(14):
            ang = random.uniform(0, math.tau)
            vel = random.uniform(30, 130)
            self.particulas.append(
                {
                    "x": rect.centerx, "y": rect.centery,
                    "vx": math.cos(ang) * vel, "vy": math.sin(ang) * vel,
                    "vida": random.uniform(0.25, 0.6), "t": 0.0, "color": color,
                    "r": random.choice([2, 2, 3]),
                }
            )

    # ---------------------------------------------------------------- actualizacion
    def actualizar(self, dt):
        ahora = time.time()

        # El marcador y los efectos se apagan siempre, incluso con el duel
        # terminado o en pausa: si no, el ultimo flash de captura se queda
        # en la lista para siempre y se redibuja en cada frame del cartel
        # de resultado.
        t, c = contar(self.board)
        for i, objetivo in enumerate((t, c)):
            actual = self.marcador_mostrado[i]
            if actual == objetivo:
                continue
            # con int() el valor se truncaba y se quedaba corto para siempre
            # (7 -> 7.9 -> 7): el marcador nunca llegaba al total real
            nuevo = actual + (objetivo - actual) * min(1.0, dt * 9)
            if abs(nuevo - objetivo) < 1.0:
                nuevo = objetivo
            self.marcador_mostrado[i] = int(round(nuevo))
        self.flash = [f for f in self.flash if ahora - f[2] < 0.6]

        if self.fin or self.pausa:
            return

        # turno del rival
        if self.turno_cpu and not self.cpu_en_curso:
            self.cpu_en_cola -= dt
            if self.cpu_en_cola <= 0:
                self._jugar_cpu()

        novas = []
        for p in self.particulas:
            p["t"] += dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 190 * dt
            if p["t"] < p["vida"]:
                novas.append(p)
        self.particulas = novas
        self.sacudida = max(0.0, self.sacudida - dt * 1.8)

    def _jugar_cpu(self):
        self.cpu_en_curso = True
        jugada = self._elegir_jugada_cpu()
        if jugada is None:
            self.cpu_en_curso = False
            self.turno_cpu = False
            self.comprobar_fin()
            return
        idx, r, c = jugada
        carta = self.mano_c[idx]
        caps = self.colocar(carta, self.mano_c, CPU, r, c)
        self.mensaje = f"{self.rival.get('nombre', 'Rival')} juega {carta.nombre}"
        if caps:
            self.mensaje += f" y captura {len(caps)}"
        self.turno_cpu = False
        self.cpu_en_curso = False
        self.comprobar_fin()
        if not self.fin:
            self.mensaje += " - tu turno"
            self.racha = 0

    def _elegir_jugada_cpu(self):
        """IA: simula cada jugada posible y puntua con ruido segun dificultad."""
        if not self.mano_c or not celdas_vacias(self.board):
            return None
        mejor, mejor_puntos = None, -1e9
        # el jefe prefiere sus cartas mas fuertes
        ruido = max(0.05, 0.9 - self.dificultad * 0.3)
        for i, carta in enumerate(self.mano_c):
            for (r, c) in celdas_vacias(self.board):
                puntos = simular(self.board, carta, r, c, CPU)
                puntos += self._bono_posicion(carta, r, c) * 2
                if carta.habilidad == "quema":
                    puntos += 0.6
                if carta.habilidad == "furia":
                    puntos += 0.3
                puntos += random.uniform(-ruido, ruido)
                if puntos > mejor_puntos:
                    mejor_puntos, mejor = puntos, (i, r, c)
        return mejor

    def comprobar_fin(self):
        if self.fin:
            return
        if not celdas_vacias(self.board) or (not self.mano_u and not self.mano_c):
            self.fin = True
            self.tiempo_fin = time.time()
            t, c, ganador = puntaje_final(self.board)
            self.ganador = ganador
            if ganador == USUARIO:
                self.racha += 1
                self.mensaje = "Has ganado el duelo"
                self._sfx_fin = audio.VICTORIA
                self.banner = ("VICTORIA", self.tiempo_fin, VERDE, f"{t} - {c}")
            elif ganador == CPU:
                self.mensaje = "Has perdido el duelo"
                self._sfx_fin = audio.DERROTA
                self.banner = ("DERROTA", self.tiempo_fin, ROJO, f"{t} - {c}")
            else:
                self.mensaje = "Empate: cuenta como victoria"
                self._sfx_fin = audio.VICTORIA
                self.banner = ("EMPATE", self.tiempo_fin, DORADO, f"{t} - {c}")
            if self.rival:
                clave = "lose" if ganador == USUARIO else "win"
                if self.rival.get(clave):
                    self.comentario = self.rival[clave]
                    self.comentario_t0 = self.tiempo_fin

    # ------------------------------------------------------------- interaccion
    def preview_capturas(self):
        """Casilla objetivo y cartas que se capturarian al soltar."""
        if not self.arrastrando:
            return None, set()
        carta = self.arrastrando[0]
        for (r, c) in celdas_vacias(self.board):
            if celda_rect(r, c).collidepoint(self.pos_arrastre):
                nb = copy.deepcopy(self.board)
                nueva = carta.copia()
                nueva.dueno = USUARIO
                nb[r][c] = nueva
                return (r, c), set(capturas(nb, r, c))
        return None, set()

    def desglose_captura(self, carta, lado, r_ataque, c_ataque, r_defensa, c_defensa):
        """Por que esta comparacion captura o no, con numeros a la vista.

        El motor NO compara los numeros que se ven: compara el valor efectivo,
        que es el visible mas embestida en el centro, elemento central, furia y
        sinergia. Un jugador ve "5 contra 5", no hay voltaque, y deduce que las
        reglas fallan. Aqui se calcula ese desglose para poder enseñarselo.

        Devuelve `(visible_ataque, visible_defensa, efectivo_ataque,
        efectivo_defensa)` con los cuatro numeros, o `None` si la comparacion
        no aplica (muro, o no son vecinas enemigas).
        """
        if not (0 <= r_defensa < 3 and 0 <= c_defensa < 3):
            return None
        vecina = self.board[r_defensa][c_defensa]
        if vecina is None or vecina.dueno == carta.dueno:
            return None
        opuesta = {"N": "S", "S": "N", "E": "O", "O": "E"}[lado]
        if opuesta in vecina.lados_muro():
            return None  # el muro bloquea: eso si hay que decirlo
        return (carta.valores[lado],
                vecina.valores[opuesta],
                valor_efectivo(carta, r_ataque, c_ataque, lado, self.board),
                valor_efectivo(vecina, r_defensa, c_defensa, opuesta, self.board))

    def cartas_en_mano(self):
        return self.mano_u

    def celda_bajo_mouse(self, mouse):
        for (r, c) in celdas_vacias(self.board):
            if celda_rect(r, c).collidepoint(mouse):
                return (r, c)
        return None

    # ------------------------------------------------------------------ dibujo
    def dibujar(self, screen):
        ahora = time.time()
        dx = dy = 0
        if self.sacudida > 0:
            dx = int(math.sin(ahora * 60) * self.sacudida * 6)
            dy = int(math.cos(ahora * 47) * self.sacudida * 4)
        lienzo = screen
        if dx or dy:
            lienzo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            lienzo.fill((0, 0, 0, 255))
        else:
            lienzo = screen

        self._dibujar_fondo(lienzo)
        self._dibujar_hud(lienzo, ahora)
        self._dibujar_tablero(lienzo, ahora)
        self._dibujar_avatar(lienzo, ahora)
        self._dibujar_mano(lienzo)
        self._dibujar_particulas(lienzo)
        self._dibujar_banner(lienzo, ahora)
        self._dibujar_efecto(lienzo, ahora)
        if self.fin:
            self._dibujar_resultado(lienzo, ahora)

        # los tooltips van los ultimos: por encima de cartas, tablero y cartel
        dibujar_tooltips(lienzo)
        fundido_entrada(lienzo, self.t_entrada, 0.35)

        if dx or dy:
            screen.blit(lienzo, (dx, dy))

    def _dibujar_fondo(self, screen):
        # fondo + velo ya compuestos: un solo blit opaco, nada de 4 MB/frame
        screen.blit(REC.fondo_tocado("assets/fondo.png", (8, 9, 18, 168)), (0, 0))
        # resplandor del color de faccion en el borde inferior
        clave = ("brillo_bando", self.bando)
        brillo = REC.imagenes.get(clave)
        if brillo is None:
            brillo = pygame.Surface((ANCHO, 90), pygame.SRCALPHA)
            for i in range(90):
                brillo.fill(con_alpha(facciones.acento(self.bando), int(40 * (1 - i / 90))),
                             (0, i, ANCHO, 1))
            REC.imagenes[clave] = brillo
        screen.blit(brillo, (0, ALTO - 90))

    def _dibujar_hud(self, screen, ahora):
        # barra superior: fase, marcador y manos
        s = REC.imagenes.get("hud_barra")
        if s is None:
            s = pygame.Surface((ANCHO, 74), pygame.SRCALPHA)
            s.fill((12, 13, 20, 210))
            REC.imagenes["hud_barra"] = s
        screen.blit(s, (0, 0))
        pygame.draw.line(screen, BORDE, (0, 74), (ANCHO, 74), 1)
        t, c = self.marcador_mostrado

        if self.en_campana and self.info:
            texto(screen, self.info.get("titulo", "DUELO").upper(), 10, DORADO, x=24, y=16)
            texto(screen, f"{self.info.get('nombre_faccion', '')} - nivel {self.info.get('dificultad', 0)}",
                  8, TEXTO_TENUE, x=24, y=36)
        else:
            texto(screen, "DUELO RAPIDO", 10, DORADO, x=24, y=16)
            texto(screen, f"{facciones.nombre(self.bando)} vs {facciones.nombre(self.bando_cpu)}",
                  8, TEXTO_TENUE, x=24, y=36)

        # marcador central con escudos del color de cada baraja
        panel(screen, pygame.Rect(ANCHO // 2 - 84, 12, 168, 48), (18, 19, 28, 230), BORDE, radio=8, grosor=1)
        badge_t = pygame.Rect(ANCHO // 2 - 74, 18, 56, 36)
        badge_c = pygame.Rect(ANCHO // 2 + 18, 18, 56, 36)
        for badge, acc in ((badge_t, facciones.acento(self.bando)),
                           (badge_c, facciones.acento(self.bando_cpu))):
            clave = ("badge", acc)
            capa = REC.imagenes.get(clave)
            if capa is None:
                capa = pygame.Surface((badge.w, badge.h), pygame.SRCALPHA)
                pygame.draw.rect(capa, con_alpha(acc, 35), capa.get_rect(), border_radius=6)
                pygame.draw.rect(capa, con_alpha(acc, 120), capa.get_rect(), 1, border_radius=6)
                REC.imagenes[clave] = capa
            screen.blit(capa, badge.topleft)
        texto(screen, f"{t}", 20, mezcla(facciones.acento(self.bando), (255, 255, 255), 0.3), centro=(ANCHO // 2 - 42, 36))
        texto(screen, "-", 14, TEXTO_TENUE, centro=(ANCHO // 2, 36))
        texto(screen, f"{c}", 20, mezcla(facciones.acento(self.bando_cpu), (255, 255, 255), 0.3), centro=(ANCHO // 2 + 42, 36))

        # manos a los lados del marcador. Debajo de cada mano va el nombre:
        # el del rival siempre, y el del jugador solo si ha puesto uno.
        texto(screen, f"TU MANO: {len(self.mano_u)}", 8, TEXTO, centro=(ANCHO // 2 - 150, 30))
        texto(screen, f"SU MANO: {len(self.mano_c)}", 8, TEXTO, centro=(ANCHO // 2 + 150, 30))
        nombre_u = self.info.get("nombre_jugador", "") if self.info else ""
        etiqueta_u = nombre_u if (nombre_u and nombre_u != campana.NOMBRE_POR_DEFECTO) else "TÚ"
        etiqueta_c = self.info.get("nombre", "") if self.info else ""
        texto(screen, etiqueta_u, 8, mezcla(facciones.acento(self.bando), TEXTO_ON, 0.4), centro=(ANCHO // 2 - 150, 52))
        texto(screen, etiqueta_c or "RIVAL", 8, mezcla(facciones.acento(self.bando_cpu), TEXTO_ON, 0.4), centro=(ANCHO // 2 + 150, 52))

        # racha
        if self.racha >= 2:
            texto(screen, f"RACHA x{self.racha}", 9, VERDE, centro=(ANCHO - 80, 36))

        # mensaje
        panel(screen, pygame.Rect(ANCHO // 2 - 300, 84, 600, 30), (16, 17, 26, 200), None, radio=8)
        texto(screen, self.mensaje, 9, TEXTO, centro=(ANCHO // 2, 99))
        # El desglose de la captura: por que un 5 voltea a un 5, o por que un
        # 9 no voltaa a un 8. Sin esto el numero de la carta parece mentira.
        self._dibujar_desglose(screen)

    def _dibujar_desglose(self, screen):
        """Los cuatro numeros de la captura que estas a punto de hacer.

        El motor compara el VALOR EFECTIVO (el que ves mas las bonificaciones),
        no el numero impreso en la carta. Un jugador ve 5 contra 5 y no hay
        voltaque, y sin explicacion parece un fallo. Aqui se teach el numero
        impreso y el que manda, con el signo de quien gana.
        """
        if not self.arrastrando:
            return
        carta = self.arrastrando[0]
        objetivo, _caps = self.preview_capturas()
        if objetivo is None:
            return
        ra, ca = objetivo
        for lado, (dr, dc) in (("N", (-1, 0)), ("S", (1, 0)),
                               ("E", (0, 1)), ("O", (0, -1))):
            nd = self.desglose_captura(carta, lado, ra, ca, ra + dr, ca + dc)
            if nd is None:
                continue
            va, vd, ea, ed = nd
            if va == ea and vd == ed:
                continue  # sin bonificaciones: el numero ya lo explica
            gana = "gana" if ea > ed else ("empata" if ea == ed else "pierde")
            linea = (f"{lado}: {va} contra {vd}"
                     f"   ->   {ea} contra {ed}  ({gana})")
            y = 122 + (("N", "S", "E", "O").index(lado)) * 16
            texto(screen, linea, 8,
                  VERDE if ea > ed else (TEXTO_TENUE if ea == ed else ROJO),
                  centro=(ANCHO // 2, y))

    def _lineas_tooltip(self, carta, synergy=False, dueno_extra=None):
        """Contenido del tooltip de una carta: nombre, bando, lados y habilidad.

        Vive aqui y no en el punto donde se dibuja porque ahora lo usan dos
        sitios: la mano y el tablero. Antes solo lo tenia la mano, asi que las
        cartas del rival no enseñaban su habilidad: era informacion que el juego
        te ocultaba justo cuando mas la necesitas, que es al planning, con el
        rival ya Comprometido en el centro del tablero.
        """
        lineas = [f"{carta.nombre}  ({facciones.nombre(carta.bando)})"]
        if dueno_extra:
            lineas.append(dueno_extra)
        lineas += [f"{l}: {val(carta.valores[l])}" for l in LADOS]
        if carta.habilidad:
            lineas.append(
                f"{crt.ICONO_HABILIDAD.get(carta.habilidad, carta.habilidad)}: "
                f"{crt.descripcion_habilidad(carta.habilidad)}"
            )
        else:
            lineas.append("Sin habilidad especial")
        if synergy:
            # La sinergia depende de cuantas aliadas hay en el tablero AHORA, no
            # de la carta sola: sin esto el jugador ve el +1 en la mano y no
            # entiende por que en el tablero la carta vale mas.
            lineas.append("SINERGIA: esta carta suma +1 a cada lado ahora mismo")
        return "\n".join(lineas)

    def _dibujar_tablero(self, screen, ahora):
        # marco ajustado al tablero real
        primero = celda_rect(0, 0)
        marco = pygame.Rect(primero.x - 12, primero.y - 12, TABLERO_W + 24, TABLERO_H + 24)
        pygame.draw.rect(screen, (44, 38, 26), marco, border_radius=12)
        pygame.draw.rect(screen, BORDE, marco, 2, border_radius=12)

        objetivo, caps_preview = self.preview_capturas()
        mouse = pygame.mouse.get_pos()

        for r in range(3):
            for c in range(3):
                rect = celda_rect(r, c)
                pygame.draw.rect(screen, SLOT_BG, rect, border_radius=7)
                pygame.draw.rect(screen, SLOT_BORDE, rect, 2, border_radius=7)
                carta = self.board[r][c]
                if carta and carta.dueno in (USUARIO, CPU):
                    # halo del dominio: el color de la baraja dueña tintéa
                    # su casilla, misma pista que el marco de la carta
                    halo = self._color_dueno(carta.dueno)
                    key = ("tinte_casilla", rect.w, rect.h, halo)
                    tinte = ui.superficie(key, lambda: _tinte_casilla(rect.w, rect.h, halo))
                    screen.blit(tinte, (rect.x - 5, rect.y - 5))
                if (r, c) in caps_preview:
                    pygame.draw.rect(screen, VERDE, rect, 4, border_radius=7)
                elif objetivo == (r, c):
                    pygame.draw.rect(screen, DORADO, rect, 4, border_radius=7)
                if carta:
                    synergy = crt.tiene_sinergia(carta, self.board)
                    sup = self.super_cartas(carta, synergy=synergy)
                    # Pasar el raton por una carta del tablero enseña lo mismo
                    # que la mano: nombre, bando, los cuatro lados y la
                    # habilidad. Se encola y se pinta al final del frame, como
                    # los de la mano, para que el tablero no lo tape.
                    if carta.dueno in (USUARIO, CPU) and rect.collidepoint(mouse):
                        dueno_txt = "TUYA" if carta.dueno == USUARIO else "DEL RIVAL"
                        crt.resplandor_carta(screen, rect, carta, carta.dueno, 110,
                                             bando_dueno=self._bando_dueno(carta))
                        # En la fila de arriba el tooltip va DEBAJO: arriba se
                        # va al HUD y tapa el marcador de los dos bandos, que es
                        # justo lo que se mira mientras se elige donde colocar.
                        tooltip(
                            screen,
                            self._lineas_tooltip(carta, synergy, dueno_txt),
                            (rect.centerx, rect.y), ancho=300, arriba=r > 0)
                    if self.ultima_jugada and self.ultima_jugada[0] == r and \
                            self.ultima_jugada[1] == c and ahora - self.ultima_jugada[2] < 0.2:
                        k = (ahora - self.ultima_jugada[2]) / 0.2
                        esc = 0.9 + 0.1 * ease(k)
                        sup = pygame.transform.smoothscale(sup, (int(CARD_W * esc), int(CARD_H * esc)))
                        _sombra_carta(screen, pygame.Rect(rect.centerx - sup.get_width() // 2,
                                                          rect.centery - sup.get_height() // 2,
                                                          sup.get_width(), sup.get_height()))
                        screen.blit(sup, (rect.centerx - sup.get_width() // 2,
                                           rect.centery - sup.get_height() // 2))
                    else:
                        _sombra_carta(screen, rect)
                        if self.ultima_jugada and self.ultima_jugada[0] == r and \
                                self.ultima_jugada[1] == c:
                            sup_p = crt._pulsar(sup, self.ultima_jugada[2])
                            if sup_p is not sup:
                                screen.blit(sup_p, (rect.centerx - sup_p.get_width() // 2,
                                                    rect.centery - sup_p.get_height() // 2))
                            else:
                                screen.blit(sup, rect.topleft)
                        else:
                            screen.blit(sup, rect.topleft)
                # casilla elemental central
                if (r, c) == (1, 1):
                    pygame.draw.circle(screen, (255, 150, 60), (rect.right - 12, rect.bottom - 12), 5)
                    pygame.draw.circle(screen, (20, 14, 8), (rect.right - 12, rect.bottom - 12), 5, 1)

        # glow de la ultima jugada
        if self.ultima_jugada:
            r, c, t0 = self.ultima_jugada
            if ahora - t0 < 1.0:
                resplandor(screen, celda_rect(r, c), (255, 230, 120), int(140 * (1 - (ahora - t0))), 3, 8)

        # flashes de captura
        for (r, c, t0, dueno) in self.flash:
            k = (ahora - t0) / 0.6
            alpha = min(18, int(150 * (1 - k)) // 8)
            color = self._color_dueno(dueno)
            screen.blit(_overlay_captura(alpha, color), celda_rect(r, c).topleft)

        # consejo: mejor casilla para la carta resaltada
        if objetivo is None and not self.turno_cpu and not self.fin:
            carta = self._hover_mano or (self.arrastrando[0] if self.arrastrando else None)
            if carta:
                mejor = self.mejor_celda(carta)
                if mejor:
                    rect = celda_rect(*mejor)
                    pulso = 0.5 + 0.5 * math.sin(ahora * 5)
                    resplandor(screen, rect, DORADO, int(50 + 70 * pulso), 2, 7)

    def _dibujar_avatar(self, screen, ahora):
        if self.avatar is None:
            return
        x, y = ANCHO - 116, 132
        screen.blit(self.avatar, (x, y))
        pygame.draw.rect(screen, facciones.acento(self.bando_cpu), (x, y, 96, 96), 2)
        pygame.draw.rect(screen, (12, 12, 20), (x, y, 96, 96), 1)
        # nombre del rival
        nombre = self.rival.get("nombre") if self.rival else facciones.nombre(self.bando_cpu)
        if nombre:
            texto(screen, nombre, 8, TEXTO, centro=(x + 48, y + 106))
        # bocadillo: encima del avatar, para no taparlo.
        # Al terminar el duelo lo muestra el cartel de resultado, no aqui.
        if self.comentario and not self.fin and ahora - self.comentario_t0 < 3.6:
            lineas = envolver(self.comentario, 8, 230)[:3]
            ancho = max(70, max(ancho_texto(l, 8) for l in lineas) + 20)
            alto = len(lineas) * 16 + 14
            caja = pygame.Rect(min(x + 96 - ancho, ANCHO - ancho - 10), y - alto - 10, ancho, alto)
            panel(screen, caja, (12, 12, 20, 230), DORADO, radio=6, grosor=1)
            ly = caja.y + 7
            for linea in lineas:
                texto(screen, linea, 8, TEXTO_ON, x=caja.x + 10, y=ly)
                ly += 16

    def _dibujar_mano(self, screen):
        mouse = pygame.mouse.get_pos()
        total = max(1, len(self.mano_u))
        self._hover_mano = None
        preview = None
        for i, carta in enumerate(self.mano_u):
            if self.arrastrando and self.arrastrando[0] is carta:
                continue
            rect = mano_rect(i, total)
            hover = rect.collidepoint(mouse) and not self.turno_cpu and not self.fin
            if hover:
                self._hover_mano = carta
                preview = carta
            y = rect.y - (18 if hover else 0)
            destino = pygame.Rect(rect.x, y, rect.w, rect.h)
            sup = self.super_cartas(carta, synergy=False)
            if hover:
                crt.resplandor_carta(screen, destino, carta, USUARIO, 110, bando_dueno=self.bando)
            _sombra_carta(screen, destino)
            screen.blit(sup, (destino.x, destino.y))
            # descripciones: se encolan y se pintan al final del frame, para
            # que ni las cartas siguientes ni el tablero las tapen
            if hover:
                # Mismo contenido que el tablero, via la misma funcion: si
                # anaden una linea a una y no a la otra, se desincronizan.
                tooltip(screen, self._lineas_tooltip(carta),
                        (destino.centerx, destino.y), ancho=300, arriba=True)

        # el preview ampliado va despues del bucle, no dentro: si se pintara
        # aqui, las cartas siguientes de la mano lo taparian
        if preview is not None:
            self._dibujar_preview(screen, mouse, preview)

        if self.arrastrando:
            carta, _ = self.arrastrando
            x, y = self.pos_arrastre
            _sombra_carta(screen, pygame.Rect(x - CARD_W // 2, y - CARD_H // 2, CARD_W, CARD_H), off=(6, 6))
            screen.blit(self.super_cartas(carta, synergy=False),
                        (x - CARD_W // 2, y - CARD_H // 2))

    def _dibujar_preview(self, screen, mouse, carta):
        """Carta ampliada de la carta señalada.

        Se pinta fuera del bucle de la mano y antes de la carta que se esta
        arrastrando, para que se vea entera y la arrastrada quede encima.
        """
        grande = crt.crear(carta, USUARIO, synergy=False, escala=1.35,
                           bando_dueno=self.bando)
        gx = min(ANCHO - grande.get_width() - 10, mouse[0] + 18)
        gy = max(80, min(ALTO - grande.get_height() - 10, mouse[1] - 40))
        _sombra_carta(screen, pygame.Rect(gx, gy, grande.get_width(), grande.get_height()), big=True)
        screen.blit(grande, (gx, gy))
        return pygame.Rect(gx, gy, grande.get_width(), grande.get_height())

    def _dibujar_particulas(self, screen):
        """Las particulas viven en una capa propia que se reutiliza.

        Antes se creaba una Surface SRCALPHA de 1280x800 por frame (4 MB de
        basura) para pintar unas pocas docenas de circulos."""
        if not self.particulas:
            self._capa_part = None
            return
        if self._capa_part is None:
            self._capa_part = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        s = self._capa_part
        s.fill((0, 0, 0, 0))
        for p in self.particulas:
            k = 1 - p["t"] / p["vida"]
            pygame.draw.circle(s, con_alpha(p["color"], int(220 * k)), (int(p["x"]), int(p["y"])),
                               max(1, int(p["r"] * k)))
        screen.blit(s, (0, 0))

    def _dibujar_efecto(self, screen, ahora):
        """El cartel del efecto: SAME, PLUS o CADENA DE n.

        Se compone una sola vez por efecto y se pinta con `set_alpha` sobre un
        Surface propio. Lo contrario, ir pintando el texto con `font.render` en
        cada frame, es justo lo que el handoff marca: una fuente por frame y
        por texto mientras el cartel esta en pantalla. Aqui no se renderiza
        nada, solo se mueve y se cambia el alpha.
        """
        if not self.efecto:
            return
        titulo, t0, color, sub, _regla = self.efecto
        transcurrido = ahora - t0
        if transcurrido >= DURACION_EFECTO:
            self.efecto = None
            return

        caja = self._superficie_efecto(titulo, sub, color)
        # Entrada rapida, cuerpo quieto, salida lenta: es la curva que hace que
        # un cartel parezca un cartel y no un parpadeo.
        if transcurrido < ENTRADA_EFECTO:
            k = ease(transcurrido / ENTRADA_EFECTO)
            a = int(255 * k)
            desliza = int((1 - k) * 16)
        elif transcurrido < DURACION_EFECTO - SALIDA_EFECTO:
            a = 255
            desliza = 0
        else:
            k = ease((transcurrido - (DURACION_EFECTO - SALIDA_EFECTO)) / SALIDA_EFECTO)
            a = int(255 * (1 - k))
            desliza = -int(k * 12)

        x = (ANCHO - caja.get_width()) // 2
        # Encima del tablero, no en el borde: la jugada acaba de ocurrir ahi y
        # el ojo sigue ahi. Centrado en el tercio alto del tablero, que es por
        # donde cae la carta que el jugador acaba de soltar.
        y = TABLERO_Y + 150 - caja.get_height() // 2 + desliza
        capa = self._capa_efecto(caja.get_width(), caja.get_height())
        # Se limpia antes de blitear: el fondo del cartel es semitransparente
        # (232 de 255) y la capa se reutiliza. Sin limpiar, dos efectos seguidos
        # del mismo tamaño dejaban el titulo del anterior asomando debajo.
        capa.fill((0, 0, 0, 0))
        capa.blit(caja, (0, 0))
        capa.set_alpha(a)
        # El halo late despues de la entrada: da la sensacion de que el tablero
        # sigue reaccionando a la jugada mientras el cartel ya se va.
        if ENTRADA_EFECTO <= transcurrido < DURACION_EFECTO - SALIDA_EFECTO:
            pulso = 0.5 + 0.5 * math.sin((ahora - t0) * 7.0)
            resplandor(screen, pygame.Rect(x - 3, y - 3,
                                          caja.get_width() + 6,
                                          caja.get_height() + 6),
                       color, alpha=int(70 + 70 * pulso), grosor=2, radio=12)
        screen.blit(capa, (x, y))
        if MEDIR:
            registrar(pygame.Rect(x, y, caja.get_width(), caja.get_height()),
                      "texto", _caja_efecto)

    def _capa_efecto(self, w, h):
        """Surface de trabajo del cartel, del tamano justo.

        Se reutiliza en vez de crear una por frame: crear una SRCALPHA de
        pantalla completa son 4 MB por frame, que es de lo que avisa el
        handoff. Con el tamano del cartel (unos 700x120) no se nota.
        """
        if self._capa_ef is None or self._capa_ef.get_size() != (w, h):
            self._capa_ef = pygame.Surface((w, h), pygame.SRCALPHA)
        return self._capa_ef

    def _superficie_efecto(self, titulo, sub, color):
        """El cartel ya compuesto: titulo grande, filete y reparto de cartas.

        Se cachea en la partida y no en `ui.superficie` a proposito: en pantalla
        solo hay un cartel, asi que una entrada por partida no deja nada viejo
        acumulado, mientras que la cache global creceria con cada titulo
        distinto que saliera en toda la sesion.
        """
        clave = (titulo, sub, color)
        if self._efecto_sup is not None and self._efecto_sup[0] == clave:
            return self._efecto_sup[1]

        lineas = envolver(sub, 11, ANCHO - 220) if sub else []
        ancho_titulo = ancho_texto(titulo, 40)
        ancho_lineas = max((ancho_texto(l, 11) for l in lineas), default=0)
        # Los 40 px de mas no son adorno: el filete de abajo tiene que ser mas
        # ancho que el titulo, y si el ancho saliese justo del texto el
        # filete quedaria asomando por los lados.
        ancho = max(ancho_titulo + 40, ancho_lineas)
        w = min(ANCHO - 80, max(260, ancho + 96))
        h = 30 + 46 + len(lineas) * 17 + 26

        sombra = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 130),
                         pygame.Rect(0, 0, w - 8, h - 8), border_radius=14)

        caja = pygame.Surface((w, h), pygame.SRCALPHA)
        caja.blit(sombra, (8, 8))
        pygame.draw.rect(caja, (11, 12, 20, 232), caja.get_rect(), border_radius=14)
        pygame.draw.rect(caja, con_alpha(color, 170), caja.get_rect(), 2,
                         border_radius=14)

        cx = w // 2
        texto(caja, titulo, 40, con_alpha(color, 255), centro=(cx, 38))
        # El filete separa el nombre del efecto de su explicacion. Sin el, las
        # dos lineas se leen como un solo bloque y el nombre se pierde.
        pygame.draw.rect(caja, con_alpha(color, 110),
                         pygame.Rect(cx - ancho_titulo // 2 - 20, 66,
                                     ancho_titulo + 40, 2))
        y = 92
        for linea in lineas:
            texto(caja, linea, 11, con_alpha(TEXTO, 240), centro=(cx, y))
            y += 17
        self._efecto_sup = (clave, caja)
        return caja

    def _dibujar_banner(self, screen, ahora):
        if not self.banner:
            return
        cadena, t0, color, sub = self.banner
        k = min(1.0, (ahora - t0) / 1.2)
        if k >= 1:
            self.banner = None
            return
        a = int(255 * (1 - k))
        # cartel flotante: sin caja oscura gigante, solo japon/halo suave
        texto(screen, cadena, 30, con_alpha(color, a), centro=(ANCHO // 2, ALTO // 2 - 60))
        if sub:
            texto(screen, sub, 10, con_alpha(TEXTO, a), centro=(ANCHO // 2, ALTO // 2 - 24))

    def _dibujar_resultado(self, screen, ahora):
        k = min(1.0, (ahora - self.tiempo_fin) / 0.5)
        screen.blit(ui._capa_negra(int(170 * k)), (0, 0))
        caja = pygame.Rect(ANCHO // 2 - 230, ALTO // 2 - 140, 460, 280)
        sombra = ui.superficie(
            ("caja_sombra", caja.w, caja.h),
            lambda: _caja_llena(caja.w, caja.h, (0, 0, 0, 150)),
        )
        screen.blit(sombra, (caja.x + 6, caja.y + 6))
        relleno = ui.superficie(
            ("caja_relleno", caja.w, caja.h),
            lambda: _caja_llena(caja.w, caja.h, (20, 20, 30, 240)),
        )
        screen.blit(relleno, caja.topleft)
        pygame.draw.rect(screen, DORADO, caja, 3, border_radius=10)

        if self.ganador == USUARIO:
            titulo, color = "VICTORIA", VERDE
        elif self.ganador == CPU:
            titulo, color = "DERROTA", ROJO
        else:
            titulo, color = "EMPATE", DORADO
        # entrada animada del cartel
        entrada = ease(min(1.0, (ahora - self.tiempo_fin) / 0.35))
        texto(screen, titulo, int(16 + 8 * entrada), color, centro=(ANCHO // 2, caja.y + 42))
        t, c = contar(self.board)
        texto(screen, f"{t} - {c}", 26, TEXTO_ON, centro=(ANCHO // 2, caja.y + 92))
        texto(screen,
              f"Capturas: {self.capturas}    Cartas: {self.jugadas}    Cadena maxima: {self.cadena_max}",
              8, TEXTO_TENUE, centro=(ANCHO // 2, caja.y + 128))
        if self.rival:
            nombre = self.rival.get("nombre", facciones.nombre(self.bando_cpu))
            texto(screen, nombre, 9, facciones.acento(self.bando_cpu), centro=(ANCHO // 2, caja.y + 166))
            if self.comentario:
                texto(screen, self.comentario, 8, TEXTO, centro=(ANCHO // 2, caja.y + 190))
        if now_clickable(ahora, self.tiempo_fin):
            texto(screen, "clic para continuar", 9, DORADO, centro=(ANCHO // 2, caja.y + 244))
        else:
            texto(screen, ". . .", 9, con_alpha(DORADO, 90), centro=(ANCHO // 2, caja.y + 244))


def now_clickable(ahora, t0):
    return ahora - t0 > 0.6


# --------------------------------------------------------------------- bucle
async def partida(screen, clock, juego, test_mode=False, guia=None):
    """Bucle bloqueante del duelo. Devuelve Resultado.

    Con `guia=` (tutorial) la colocacion se valida paso a paso, no hay
    turno de CPU ni fin por tablero lleno: la guia cierra la practica.
    Sin guia el comportamiento es el de siempre.
    """
    # El enfrentamiento tiene su propia musica: no la del rival
    audio.musica(audio.musica_de_duelo())
    audio.sfx(audio.MENU)

    frames = 0
    resultado = None
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        await asyncio.sleep(0)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if guia is not None and not juego.fin:
                        # En el tutorial ESC pide salir (con confirmacion),
                        # nunca pausa: el jugador no debe quedarse encerrado.
                        guia.confirmar_salida = not guia.confirmar_salida
                        audio.sfx(audio.MENU_BACK if guia.confirmar_salida else audio.MENU)
                    elif guia is None and not (juego.fin and now_clickable(time.time(), juego.tiempo_fin)):
                        juego.pausa = not juego.pausa
                        audio.sfx(audio.MENU_BACK if juego.pausa else audio.MENU)
                elif guia is not None and guia.confirmar_salida and ev.key in (
                        pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                    juego.abandonado = True
                    audio.sfx(audio.MENU_BACK)
                    return Resultado(False, juego.capturas, juego.jugadas, (0, 0))
            if guia is not None and guia.confirmar_salida and ev.type not in (
                    pygame.KEYDOWN, pygame.QUIT):
                continue
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_h and not juego.turno_cpu:
                juego.mensaje = guia.pista() if guia is not None else "Consejo: Same y Plus voltean al vuelo"
            if juego.pausa:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if _pausa_clic(screen, ev.pos):
                        return Resultado(False, juego.capturas, juego.jugadas, (0, 0))
                continue
            # continuar el duel terminado: clic, ESC, Intro o espacio
            continuar = (
                ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
            ) or (
                ev.type == pygame.KEYDOWN
                and ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER)
            ) or (
                # en el tutorial ESC tambien continua (nunca pauso ahi)
                guia is not None and ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE
            )
            if continuar and juego.fin and now_clickable(time.time(), juego.tiempo_fin):
                resultado = Resultado(
                    juego.ganador in (USUARIO, None),
                    juego.capturas, juego.jugadas,
                    contar(juego.board), juego.ganador is None, juego.racha,
                )
                break
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if guia is not None and not juego.fin and guia.clic_salir(ev.pos):
                    # boton SALIR de la practica: pide confirmacion
                    guia.confirmar_salida = True
                    audio.sfx(audio.MENU_BACK)
                    continue
                if not juego.fin and not juego.turno_cpu:
                    mouse = pygame.mouse.get_pos()
                    for i, carta in enumerate(juego.mano_u):
                        rect = mano_rect(i, max(1, len(juego.mano_u)))
                        if rect.inflate(0, 40).collidepoint(mouse):
                            juego.arrastrando = (carta, None)
                            juego.pos_arrastre = mouse
                            audio.sfx(audio.DRAG, 0.5)
                            break
            if ev.type == pygame.MOUSEMOTION and juego.arrastrando:
                juego.pos_arrastre = ev.pos
                anterior = juego._arrastre_valido
                nueva = juego.celda_bajo_mouse(ev.pos) is not None
                if nueva != anterior:
                    juego._arrastre_valido = nueva
                    audio.sfx(audio.INVALIDO if not nueva else audio.CARD, 0.35, canal="hover")
            if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and juego.arrastrando:
                carta = juego.arrastrando[0]
                juego.arrastrando = None
                celda = juego.celda_bajo_mouse(ev.pos)
                if celda:
                    if guia is not None:
                        # practica: se valida el objetivo, sin turno de CPU
                        # ni fin por tablero (la guia cierra la practica)
                        ok, motivo = guia.validar_colocacion(juego, carta, *celda)
                        if not ok:
                            juego.mensaje = motivo
                            audio.sfx(audio.INVALIDO, 0.5)
                        else:
                            caps = juego.colocar(carta, juego.mano_u, USUARIO, *celda)
                            guia.tras_colocar(juego, carta, celda[0], celda[1], caps)
                    else:
                        caps = juego.colocar(carta, juego.mano_u, USUARIO, *celda)
                        juego.mensaje = f"Juegas {carta.nombre}"
                        if caps:
                            juego.mensaje += f" y capturas {len(caps)}"
                        juego.turno_cpu = True
                        juego.cpu_en_cola = 0.85
                        juego.cpu_en_curso = False
                else:
                    audio.sfx(audio.INVALIDO, 0.5)
                if guia is None:
                    juego.comprobar_fin()
        # OJO: Resultado.__bool__ devuelve `victoria`. Si el duelo se ha
        # perdido, `if resultado:` es False y el bucle no se rompia nunca:
        # el jugador se quedaba en el cartel de DERROTA sin poder continuar.
        if resultado is not None:
            break

        if juego.fin and juego._sfx_fin:
            audio.sfx(juego._sfx_fin)
            juego._sfx_fin = None

        if not juego.pausa:
            juego.actualizar(dt)
        if juego.pausa:
            _dibujar_pausa(screen, juego)
        else:
            juego.dibujar(screen)
            if guia is not None:
                guia.dibujar_extra(screen, juego)
        pygame.display.flip()
        frames += 1
        if test_mode and frames > 40:
            return Resultado(True, 0, 0, (0, 0))
        if resultado is not None:
            break
    audio.sfx(audio.MENU_BACK)
    return resultado


def _pausa_clic(screen, pos):
    """True si se ha pulsado 'Salir' en el menu de pausa."""
    rect = pygame.Rect(ANCHO // 2 - 130, ALTO // 2 + 30, 260, 44)
    return rect.collidepoint(pos)


def _dibujar_pausa(screen, juego):
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    capa.fill((0, 0, 0, 180))
    screen.blit(capa, (0, 0))
    texto(screen, "PAUSA", 22, DORADO, centro=(ANCHO // 2, ALTO // 2 - 60))
    texto(screen, "clic o ESC para continuar", 10, TEXTO, centro=(ANCHO // 2, ALTO // 2))
    rect = pygame.Rect(ANCHO // 2 - 130, ALTO // 2 + 30, 260, 44)
    panel(screen, rect, (24, 24, 34, 230), ROJO, radio=8)
    texto(screen, "ABANDONAR DUELO", 11, TEXTO_ON, centro=(rect.centerx, rect.centery))