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
import opciones
import ui
from reglas import (
    CPU,
    DELTA,
    OPUESTO,
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
    alto_texto,
    mano_rect,
    MANO_Y,
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
RECT_HISTORIAL = pygame.Rect(24, 132, 340, 34)

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
    "same": ("SAME", "dos igualdades; caen las vecinas enemigas"),
    "plus": ("PLUS", "dos sumas iguales; caen las vecinas enemigas"),
    "quema": ("QUEMA", "captura al empatar; no inicia cadena"),
}

#: Tiempos del cartel, en segundos. Entrada rapida para que se lea al instante,
#: cuerpo largo para que se pueda leer entero, y salida mas lenta que la
#: entrada: si se fuera tan rapido como aparece, el ojo soloeria el parpadeo.
ENTRADA_EFECTO = 0.22
DURACION_EFECTO = 2.0
SALIDA_EFECTO = 0.5


def _sonido_de_efecto(resumen):
    """Que sonido suena al capturar. Prioridad: regla rara > cadena > basica.

    Antes sonaba `CADENA` si habia cadena y `CAPTURAR` si no, asi que un same o
    un plus se oian igual que una captura simple, mientras el cartel de al lado
    si decia SAME o PLUS. El sonido va atras del cartel: lo primero que se oye
    es un tono y solo despues se lee que regla era.

    La prioridad copia la de `_anunciar_efecto`: si hay same o plus, manda el
    mas frecuente; a igualdad, plus, que es el mas ancho de los dos. La cadena
    solo aparece si no hubo regla, porque `_anunciar_efecto` tampoco la nombra
    en ese caso (una cadena con same se anuncia como SAME).
    """
    candidatos = [k for k in ("same", "plus") if resumen.get(k)]
    if candidatos:
        return {"plus": audio.PLUS, "same": audio.SAME}[
            max(candidatos, key=lambda k: resumen[k])]
    if resumen.get("cadena"):
        return audio.CADENA
    return audio.CAPTURAR


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
    def __init__(self, victoria, capturas, jugadas, marcador, empate=False, racha=0,
                 abandonado=False):
        self.victoria = victoria
        self.capturas = capturas
        self.jugadas = jugadas
        self.marcador = marcador
        self.empate = empate
        self.racha = racha
        self.abandonado = abandonado

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
            c.repartir(USUARIO)
        for c in self.mano_c:
            c.repartir(CPU)

        self.board = [[None] * 3 for _ in range(3)]
        self.turno_cpu = False
        self.cpu_en_curso = False
        self.cpu_en_cola = 0.0
        self.mensaje = "Tu turno: elige carta y casilla con clic o ENTER. Tambien puedes arrastrar"
        self.arrastrando = None
        self.seleccionada = None
        self.indice_mano = 0
        self.celda_foco = (0, 0)
        self.modo_teclado = False
        self.historial = []
        self.historial_abierto = False
        self.indice_historial = 0
        self.pos_arrastre = (0, 0)
        self.fin = False
        self.pausa = False
        self._presentacion_suspendida_desde = None
        self._resultado_frame = None
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
        self.avatar_jugador = crt.REC.imagen("assets/avatar_duelista.png", (96, 96))
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
        # En un duelo espejo (incluido el prologo) la faccion no distingue
        # propietarios. None activa el marco azul/rojo de cartas.crear.
        if self.bando == self.bando_cpu:
            return None
        if carta.dueno == USUARIO:
            return self.bando
        if carta.dueno == CPU:
            return self.bando_cpu
        return None

    def super_cartas(self, carta, posicion=None):
        valores = ({lado: valor_efectivo(carta, *posicion, lado, self.board)
                    for lado in LADOS} if posicion is not None else None)
        return crt.crear(carta, carta.dueno, valores=valores,
                         bando_dueno=self._bando_dueno(carta))

    def _color_dueno(self, dueno):
        """Color de la baraja que domina cada bando: el duelo habla en
        los colores de los dos mazos, no en azul/rojo fijos."""
        if self.bando == self.bando_cpu:
            return {USUARIO: AZUL, CPU: ROJO}.get(dueno, DORADO)
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
        previo = copy.deepcopy(self.board)
        caps, eventos = cascada(self.board, r, c)
        self.historial.append({"titulo": ("TU: " if dueno == USUARIO else "RIVAL: ") + carta.nombre,
                               "lineas": self.explicar_eventos(previo, (r, c), eventos)})
        self.historial = self.historial[-9:]
        self.indice_historial = len(self.historial) - 1
        ahora = time.time()
        self.ultima_jugada = (r, c, ahora)
        for (cr, cc) in caps:
            if not opciones.obtener("movimiento_reducido"):
                self.flash.append((cr, cc, ahora, dueno))
                self._explosion(cr, cc, dueno)
        audio.sfx(audio.COLOCAR)
        self.capturas += len(caps)
        self.jugadas += 1
        if caps:
            resumen = resumen_efectos(eventos, (r, c))
            audio.sfx(_sonido_de_efecto(resumen), canal="cap")
            if resumen["cadena"]:
                self.cadena_max = max(self.cadena_max,
                                      resumen["cadena"] + resumen.get("same", 0) + resumen.get("plus", 0))
            if len(caps) >= 3 and not opciones.obtener("movimiento_reducido"):
                self.sacudida = min(0.55, 0.18 + len(caps) * 0.06)
            self._anunciar_efecto(resumen, ahora, dueno)
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
        # Quema conserva su nombre aunque no coincida con Same o Plus.
        # El sonido va antes del retorno de una captura sin regla especial.
        if resumen.get("quema"):
            audio.sfx("assets/sfx_stable_audio3/ability.wav", 0.7, canal="habilidad")
            if not candidatos and not resumen.get("cadena"):
                candidatos = ["quema"]

        if not candidatos:
            # Varias capturas directas tampoco son una cadena.
            if resumen.get("cadena"):
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
        if resumen.get("quema") and "quema" not in candidatos:
            reparto.append("%d por quema" % resumen["quema"])
        self.efecto = (titulo, ahora, color,
                       "%s.  %d %s: %s" % (sub, total, "carta" if total == 1 else "cartas", ", ".join(reparto)),
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
    def sincronizar_presentacion(self, ahora):
        """Conserva el tiempo de lectura al abrir pausa o historial."""
        if self.pausa or self.historial_abierto:
            if self._presentacion_suspendida_desde is None:
                self._presentacion_suspendida_desde = ahora
        elif self._presentacion_suspendida_desde is not None:
            demora = max(0.0, ahora - self._presentacion_suspendida_desde)
            for atributo in ('efecto', 'banner'):
                anuncio = getattr(self, atributo)
                if anuncio:
                    setattr(self, atributo, (anuncio[0], anuncio[1] + demora, *anuncio[2:]))
            if self.fin:
                self.tiempo_fin += demora
            self._presentacion_suspendida_desde = None

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

        if self.pausa or self.historial_abierto:
            return

        # turno del rival
        if not self.fin and self.turno_cpu and not self.cpu_en_curso:
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
        self.mensaje = f"{(self.rival or {}).get('nombre', 'Rival')} juega {carta.nombre}"
        if caps:
            self.mensaje += f" y captura {len(caps)}"
        self.turno_cpu = False
        self.cpu_en_curso = False
        self.comprobar_fin()
        if not self.fin:
            self.mensaje += " - tu turno"
            self.racha = 0
            # El cambio de turno era visible (el mensaje) y mudo. Se anade el
            # sonido justo al pasar el turno, no antes, para que no pise la
            # captura que acaba de sonar.
            audio.sfx("assets/sfx_stable_audio3/turn_change.wav", 0.55, canal="turno")

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
            ahora = time.time()
            self.tiempo_fin = max(ahora, self.efecto[1] + DURACION_EFECTO if self.efecto else ahora)
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
    def cancelar_seleccion(self):
        self.arrastrando = None
        self.seleccionada = None
        self._arrastre_valido = False

    def confirmar_jugada(self, celda, guia=None):
        carta = self.arrastrando[0] if self.arrastrando else self.seleccionada
        if (carta not in self.mano_u or celda not in self.celdas_libres()
                or self.turno_cpu or self.fin or self.pausa):
            return False
        if guia is not None:
            ok, motivo = guia.validar_colocacion(self, carta, *celda)
            if not ok:
                self.mensaje = motivo
                audio.sfx(audio.INVALIDO, 0.5)
                return False
        self.cancelar_seleccion()
        caps = self.colocar(carta, self.mano_u, USUARIO, *celda)
        self.indice_mano = min(self.indice_mano, max(0, len(self.mano_u) - 1))
        if guia is not None:
            guia.tras_colocar(self, carta, celda[0], celda[1], caps)
        else:
            self.mensaje = f"Juegas {carta.nombre} - {len(caps)} capturas. Turno del rival"
            self.turno_cpu = True
            # El rival no debe borrar el anuncio antes de que pueda leerse.
            # Las jugadas normales conservan su ritmo; Same/Plus/Quema esperan
            # solo hasta terminar su cartel, sin bloquear el bucle de 60 FPS.
            restante = max(0.0, self.efecto[1] + DURACION_EFECTO - time.time()) if self.efecto else 0.0
            self.cpu_en_cola = max(0.85, restante)
            self.cpu_en_curso = False
            self.comprobar_fin()
        return True

    def entrada_jugada(self, ev, guia=None):
        """Raton, arrastre y teclado comparten la misma confirmacion."""
        if self.fin or self.pausa or self.turno_cpu:
            return
        if ev.type == pygame.KEYDOWN:
            self.modo_teclado = True
            if ev.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                if self.seleccionada is None and self.mano_u:
                    paso = -1 if ev.key in (pygame.K_LEFT, pygame.K_UP) else 1
                    self.indice_mano = (self.indice_mano + paso) % len(self.mano_u)
                else:
                    r, c = self.celda_foco
                    dr, dc = {pygame.K_LEFT: (0, -1), pygame.K_RIGHT: (0, 1),
                              pygame.K_UP: (-1, 0), pygame.K_DOWN: (1, 0)}[ev.key]
                    self.celda_foco = ((r + dr) % 3, (c + dc) % 3)
                    self.pos_arrastre = celda_rect(*self.celda_foco).center
            elif ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                if self.seleccionada is None and self.mano_u:
                    self.seleccionada = self.mano_u[self.indice_mano % len(self.mano_u)]
                    self.celda_foco = self.celdas_libres()[0]
                    self.pos_arrastre = celda_rect(*self.celda_foco).center
                elif self.celda_foco not in self.celdas_libres():
                    self.mensaje = "Casilla ocupada: elige una libre o ESC para cancelar"
                else:
                    self.confirmar_jugada(self.celda_foco, guia)
            elif ev.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                self.cancelar_seleccion()
            return
        if ev.type == pygame.MOUSEBUTTONDOWN:
            self.modo_teclado = False
            if ev.button == 3:
                self.cancelar_seleccion()
            elif ev.button == 1:
                for i, carta in enumerate(self.mano_u):
                    if mano_rect(i, len(self.mano_u)).inflate(0, 40).collidepoint(ev.pos):
                        self.indice_mano = i
                        self.seleccionada = carta
                        self.arrastrando = (carta, None)
                        self.pos_arrastre = ev.pos
                        audio.sfx(audio.DRAG, 0.5)
                        break
        elif ev.type == pygame.MOUSEMOTION:
            self.modo_teclado = False
            if self.seleccionada is not None or self.arrastrando:
                self.pos_arrastre = ev.pos
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            celda = self.celda_bajo_mouse(ev.pos)
            if celda is not None and (self.seleccionada is not None or self.arrastrando):
                self.confirmar_jugada(celda, guia)
            # Soltar sobre la mano selecciona, no juega ni consume turno.
            self.arrastrando = None

    def preview_capturas(self):
        """Casilla objetivo y cartas que se capturarian al soltar."""
        objetivo, caps, _ = self.detalle_preview()
        return objetivo, set(caps)

    def detalle_preview(self):
        carta = self.arrastrando[0] if self.arrastrando else self.seleccionada
        if carta is None:
            return None, [], []
        for (r, c) in celdas_vacias(self.board):
            if celda_rect(r, c).collidepoint(self.pos_arrastre):
                nb = copy.deepcopy(self.board)
                nueva = carta.copia()
                nueva.dueno = USUARIO
                nb[r][c] = nueva
                previo = copy.deepcopy(nb)
                caps, eventos = cascada(nb, r, c)
                return (r, c), caps, self.explicar_eventos(previo, (r, c), eventos)
        return None, [], []

    @staticmethod
    def explicar_eventos(previo, origen, eventos):
        """Explica eventos del motor; no inventa otra logica de capturas."""
        def casilla(pos):
            return f"F{pos[0] + 1} C{pos[1] + 1}"

        lineas = []
        for regla, pos, desde in eventos:
            motivo = "Cadena" if desde != origen else {
                None: "Basica", "same": "Same", "plus": "Plus", "quema": "Quema"
            }.get(regla, str(regla))
            if desde == origen and regla in (None, "quema"):
                dr, dc = pos[0] - origen[0], pos[1] - origen[1]
                lado = next(l for l, delta in DELTA.items() if delta == (dr, dc))
                atacante, defensora = previo[origen[0]][origen[1]], previo[pos[0]][pos[1]]
                a = valor_efectivo(atacante, *origen, lado, previo)
                b = valor_efectivo(defensora, *pos, OPUESTO[lado], previo)
                lineas.append(f"{motivo}: {casilla(pos)} ({a} {'>' if a > b else '='} {b})")
            else:
                lineas.append(f"{motivo}: {casilla(pos)} desde {casilla(desde)}")
        if any(regla == "same" for regla, _, _ in eventos):
            lineas.append("Same: dos o mas igualdades.")
        if any(regla == "plus" for regla, _, _ in eventos):
            lineas.append("Plus: dos o mas sumas iguales.")
        r, c = origen
        carta = previo[r][c]
        for lado, (dr, dc) in DELTA.items():
            nr, nc = r + dr, c + dc
            if not (0 <= nr < 3 and 0 <= nc < 3):
                continue
            vecina = previo[nr][nc]
            if vecina is None or vecina.dueno == carta.dueno:
                continue
            if OPUESTO[lado] in vecina.lados_muro():
                lineas.append(f"Muro: bloquea {casilla((nr, nc))}")
            elif not eventos:
                a = valor_efectivo(carta, r, c, lado, previo)
                b = valor_efectivo(vecina, nr, nc, OPUESTO[lado], previo)
                lineas.append(f"{lado}: {a} contra {b}; sin captura")
        return lineas or ["Sin capturas: solo colocacion."]

    def desglose_captura(self, carta, lado, r_ataque, c_ataque, r_defensa, c_defensa):
        """Por que esta comparacion captura o no, con numeros a la vista.

        Compara base y valor efectivo, incluida la carta que se va a colocar.
        El tablero muestra efectivos; la mano muestra sus valores base.

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
        tablero = [fila[:] for fila in self.board]
        tablero[r_ataque][c_ataque] = carta
        return (carta.valores[lado],
                vecina.valores[opuesta],
                valor_efectivo(carta, r_ataque, c_ataque, lado, tablero),
                valor_efectivo(vecina, r_defensa, c_defensa, opuesta, tablero))

    def cartas_en_mano(self):
        return self.mano_u

    def celda_bajo_mouse(self, mouse):
        for (r, c) in celdas_vacias(self.board):
            if celda_rect(r, c).collidepoint(mouse):
                return (r, c)
        return None

    # ------------------------------------------------------------------ dibujo
    def dibujar(self, screen):
        ahora = self._presentacion_suspendida_desde if self._presentacion_suspendida_desde is not None else time.time()
        # Tras acabar las animaciones el resultado es estático. Reutilizar un
        # fotograma opaco evita volver a componer tablero y velos alfa en WASM.
        # Pausa/historial invalidan la imagen; el puntero no genera tooltips
        # durante el resultado, así que no hay contenido dinámico que perder.
        estable = (self.fin and not (self.pausa or self.historial_abierto or self.efecto
                                    or self.banner or self.flash or self.particulas)
                   and self.sacudida <= 0 and ahora - self.tiempo_fin >= 0.8)
        clave = (screen.get_size(), ui.escala_texto(), self.tiempo_fin,
                 opciones.obtener('movimiento_reducido'))
        if estable and self._resultado_frame is not None and self._resultado_frame[0] == clave:
            screen.blit(self._resultado_frame[1], (0, 0))
            return
        if not estable:
            self._resultado_frame = None
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
        if self.fin and not self.historial_abierto and ahora >= self.tiempo_fin:
            self._dibujar_resultado(lienzo, ahora)

        # los tooltips van los ultimos: por encima de cartas, tablero y cartel
        dibujar_tooltips(lienzo)
        fundido_entrada(lienzo, self.t_entrada, 0.35)

        if dx or dy:
            screen.blit(lienzo, (dx, dy))
        if estable:
            self._resultado_frame = (clave, screen.copy().convert())

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
            texto(screen, "DUELO RÁPIDO", 10, DORADO, x=24, y=16)
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
        pygame.draw.rect(screen, TEXTO, (badge_t.x + 5, badge_t.centery - 4, 8, 8))
        cx, cy = badge_c.x + 9, badge_c.centery
        pygame.draw.polygon(screen, TEXTO, [(cx, cy - 5), (cx + 5, cy),
                                            (cx, cy + 5), (cx - 5, cy)])

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
        panel(screen, pygame.Rect(ANCHO // 2 - 300, 84, 600, 44), (16, 17, 26, 200), None, radio=8)
        for i, linea in enumerate(envolver(self.mensaje, 9, 576)[:2]):
            texto(screen, linea, 9, TEXTO, centro=(ANCHO // 2, 98 + i * 16))
        turno = "FINALIZADO" if self.fin else ("TURNO RIVAL" if self.turno_cpu else "TU TURNO")
        texto(screen, turno, 9, ui.AVISO if self.turno_cpu else ui.FOCO,
              x=ANCHO - 160, y=14)
        # El desglose de la captura: por que un 5 voltea a un 5, o por que un
        # 9 no voltaa a un 8. Sin esto el numero de la carta parece mentira.
        self._dibujar_desglose(screen)

    def _dibujar_desglose(self, screen):
        """Explicacion lateral de la prevision o de una jugada del historial."""
        panel(screen, RECT_HISTORIAL, (18, 19, 28, 245), ui.FOCO, radio=6)
        texto(screen, "L: CERRAR HISTORIAL" if self.historial_abierto else "L: VER JUGADAS",
              9, TEXTO, centro=RECT_HISTORIAL.center)
        # Las tres pistas se anclan a la mano, no a coordenadas sueltas. La
        # etiqueta "ELEGIDA"/"ENTER" de la carta seleccionada va justo encima
        # de la mano (MANO_Y - 10) y antes esta tercera pista terminaba
        # exactamente en su borde: a tamano normal se tocaban y con el modo
        # lectura al 125% se solapaban de verdad (4px medidos).
        _alto_pista = alto_texto("M: movimiento reducido NO", 8)
        _y_pista = MANO_Y - 26 - _alto_pista
        texto(screen, "Flechas / ENTER: elegir y colocar", 8, TEXTO_TENUE,
              x=24, y=_y_pista - 2 * _alto_pista - 6)
        texto(screen, "ESC / clic derecho: cancelar", 8, TEXTO_TENUE,
              x=24, y=_y_pista - _alto_pista - 3)
        texto(screen, "M: movimiento reducido " +
              ("SI" if opciones.obtener("movimiento_reducido") else "NO"),
              8, TEXTO_TENUE, x=24, y=_y_pista)
        carta = self.arrastrando[0] if self.arrastrando else self.seleccionada
        objetivo, caps, lineas = self.detalle_preview()
        if self.historial_abierto:
            if self.historial:
                entrada = self.historial[self.indice_historial]
                titulo = entrada["titulo"]
                lineas = [f"Jugada {self.indice_historial + 1}/{len(self.historial)}",
                          "Izquierda / derecha: recorrer"] + entrada["lineas"]
            else:
                titulo, lineas = "HISTORIAL", ["Todavia no se ha jugado ninguna carta."]
        elif objetivo is not None:
            titulo = f"PREVISION: {len(caps)} CAPTURAS"
            ra, ca = objetivo
            for lado, (dr, dc) in DELTA.items():
                nd = self.desglose_captura(carta, lado, ra, ca, ra + dr, ca + dc)
                if nd is not None and (nd[0] != nd[2] or nd[1] != nd[3]):
                    va, vd, ea, ed = nd
                    lineas.append(f"{lado}: {va}/{vd} -> {ea}/{ed} efectivos")
        elif carta is not None:
            titulo, lineas = "CARTA ELEGIDA", [carta.nombre, "Elige una casilla libre."]
        else:
            return
        contenido = envolver(titulo, 9, 308)
        contenido += [parte for linea in lineas for parte in envolver(linea, 8, 308)]
        panel(screen, pygame.Rect(24, 178, 340, 30 + len(contenido) * 16),
              (18, 19, 28, 245), BORDE, radio=8)
        for i, linea in enumerate(contenido):
            texto(screen, linea, 8, ui.FOCO if i == 0 else TEXTO,
                  x=40, y=194 + i * 16)

    def _lineas_tooltip(self, carta, dueno_extra=None):
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
            if carta.dueno is not None and not carta.habilidad_activa():
                lineas.append("INACTIVA: se reactiva al volver a su propietario inicial")
        else:
            lineas.append("Sin habilidad especial")
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
                if carta:
                    sup = self.super_cartas(carta, posicion=(r, c))
                    # Pasar el raton por una carta del tablero enseña lo mismo
                    # que la mano: nombre, bando, los cuatro lados y la
                    # habilidad. Se encola y se pinta al final del frame, como
                    # los de la mano, para que el tablero no lo tape.
                    if (carta.dueno in (USUARIO, CPU) and rect.collidepoint(mouse)
                            and not (self.fin or self.pausa or self.historial_abierto or self.efecto)):
                        dueno_txt = "TUYA" if carta.dueno == USUARIO else "DEL RIVAL"
                        crt.resplandor_carta(screen, rect, carta, carta.dueno, 110,
                                             bando_dueno=self._bando_dueno(carta))
                        # En la fila de arriba el tooltip va DEBAJO: arriba se
                        # va al HUD y tapa el marcador de los dos bandos, que es
                        # justo lo que se mira mientras se elige donde colocar.
                        tooltip(
                            screen,
                            self._lineas_tooltip(carta, dueno_txt) +
                            "\nVALORES EN MESA: " + " / ".join(
                                f"{l} {val(valor_efectivo(carta, r, c, l, self.board))}"
                                for l in LADOS),
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
                # Dibujar DESPUES de la carta: su superficie tapaba el preview.
                if (r, c) in caps_preview:
                    pygame.draw.rect(screen, ui.EXITO, rect, 3, border_radius=7)
                    pygame.draw.lines(screen, TEXTO_ON, False,
                                      [(rect.x + 6, rect.y + 10),
                                       (rect.x + 10, rect.y + 14),
                                       (rect.x + 17, rect.y + 5)], 2)
                elif objetivo == (r, c):
                    pygame.draw.rect(screen, ui.FOCO, rect, 4, border_radius=7)
                    texto(screen, "COLOCAR", 8, ui.FOCO, centro=rect.center)
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
        # El jugador comparte la columna del rival, fuera del tablero y la mano.
        jugador = pygame.Rect(ANCHO - 116, 652, 96, 96)
        screen.blit(self.avatar_jugador, jugador)
        pygame.draw.rect(screen, ui.FOCO, jugador, 2)
        nombre_jugador = self.info.get("nombre_jugador") or "Tú"
        for i, linea in enumerate(envolver(nombre_jugador, 8, 112)):
            texto(screen, linea, 8, TEXTO, centro=(jugador.centerx, 760 + i * 14))
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
            hover = rect.collidepoint(mouse) and not (
                self.turno_cpu or self.fin or self.pausa or self.historial_abierto or self.efecto)
            foco = (self.modo_teclado and i == self.indice_mano
                    and not self.turno_cpu and not self.fin)
            if hover:
                self._hover_mano = carta
                preview = carta
            y = rect.y - (18 if hover else 0)
            destino = pygame.Rect(rect.x, y, rect.w, rect.h)
            sup = self.super_cartas(carta)
            if hover:
                crt.resplandor_carta(screen, destino, carta, USUARIO, 110, bando_dueno=self._bando_dueno(carta))
            _sombra_carta(screen, destino)
            screen.blit(sup, (destino.x, destino.y))
            if carta is self.seleccionada or foco:
                pygame.draw.rect(screen, ui.FOCO, destino, 3, border_radius=7)
                texto(screen, "ELEGIDA" if carta is self.seleccionada else "ENTER",
                      8, ui.FOCO, centro=(destino.centerx, destino.y - 10))
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
            screen.blit(self.super_cartas(carta),
                        (x - CARD_W // 2, y - CARD_H // 2))

    def _dibujar_preview(self, screen, mouse, carta):
        """Carta ampliada de la carta señalada.

        Se pinta fuera del bucle de la mano y antes de la carta que se esta
        arrastrando, para que se vea entera y la arrastrada quede encima.
        """
        grande = crt.crear(carta, USUARIO, escala=1.35,
                            bando_dueno=self._bando_dueno(carta))
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
        if not self.efecto or self.historial_abierto:
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
        clave = (titulo, sub, color, ui.escala_texto())
        if self._efecto_sup is not None and self._efecto_sup[0] == clave:
            return self._efecto_sup[1]

        # Mantener el anuncio lejos de los retratos laterales, también en
        # modo lectura; envolver el subtítulo antes de ensanchar el panel.
        ancho_maximo = ANCHO - 400
        lineas = envolver(sub, 11, ancho_maximo - 96) if sub else []
        ancho_titulo = ancho_texto(titulo, 40)
        ancho_lineas = max((ancho_texto(l, 11) for l in lineas), default=0)
        # Los 40 px de mas no son adorno: el filete de abajo tiene que ser mas
        # ancho que el titulo, y si el ancho saliese justo del texto el
        # filete quedaria asomando por los lados.
        ancho = max(ancho_titulo + 40, ancho_lineas)
        w = min(ancho_maximo, max(260, ancho + 96))
        alto_titulo = alto_texto(titulo, 40)
        alto_linea = alto_texto(sub or " ", 11)
        interlinea = max(17, alto_linea + 6)
        y_filete = 18 + alto_titulo + 8
        y_sub = y_filete + 16 + alto_linea // 2
        h = y_sub + max(0, len(lineas) - 1) * interlinea + alto_linea // 2 + 20

        sombra = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 130),
                         pygame.Rect(0, 0, w - 8, h - 8), border_radius=14)

        caja = pygame.Surface((w, h), pygame.SRCALPHA)
        caja.blit(sombra, (8, 8))
        pygame.draw.rect(caja, (11, 12, 20, 232), caja.get_rect(), border_radius=14)
        pygame.draw.rect(caja, con_alpha(color, 170), caja.get_rect(), 2,
                         border_radius=14)

        cx = w // 2
        texto(caja, titulo, 40, con_alpha(color, 255), centro=(cx, 18 + alto_titulo // 2))
        # El filete separa el nombre del efecto de su explicacion. Sin el, las
        # dos lineas se leen como un solo bloque y el nombre se pierde.
        pygame.draw.rect(caja, con_alpha(color, 110),
                         pygame.Rect(cx - ancho_titulo // 2 - 20, y_filete,
                                     ancho_titulo + 40, 2))
        y = y_sub
        for linea in lineas:
            texto(caja, linea, 11, con_alpha(TEXTO, 240), centro=(cx, y))
            y += interlinea
        self._efecto_sup = (clave, caja)
        return caja

    def _dibujar_banner(self, screen, ahora):
        if not self.banner or self.historial_abierto:
            return
        cadena, t0, color, sub = self.banner
        if ahora < t0:
            return
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
            texto(screen, "ENTER: continuar / L: ver jugadas", 8, DORADO,
                  centro=(ANCHO // 2, caja.y + 244))
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
            if not juego.pausa and ((ev.type == pygame.KEYDOWN and ev.key == pygame.K_l) or (
                    ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
                    and RECT_HISTORIAL.collidepoint(ev.pos))):
                juego.historial_abierto = not juego.historial_abierto
                juego.cancelar_seleccion()
                continue
            if juego.historial_abierto:
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        juego.historial_abierto = False
                    elif ev.key in (pygame.K_LEFT, pygame.K_RIGHT) and juego.historial:
                        paso = -1 if ev.key == pygame.K_LEFT else 1
                        juego.indice_historial = (juego.indice_historial + paso) % len(juego.historial)
                continue
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_m:
                opciones.alternar("movimiento_reducido")
                juego.sacudida = 0
                juego.flash.clear()
                juego.particulas.clear()
                continue
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if juego.seleccionada is not None or juego.arrastrando:
                        juego.cancelar_seleccion()
                        audio.sfx(audio.MENU_BACK)
                        continue
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
                    return Resultado(False, juego.capturas, juego.jugadas, (0, 0),
                                     abandonado=True)
            if guia is not None and guia.confirmar_salida:
                continue
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_h and not juego.turno_cpu:
                juego.mensaje = guia.pista() if guia is not None else "Consejo: Same y Plus voltean al vuelo"
            if juego.pausa:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if _pausa_clic(screen, ev.pos):
                        return Resultado(False, juego.capturas, juego.jugadas, (0, 0),
                                         abandonado=True)
                    juego.pausa = False
                elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                    juego.pausa = False
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
            juego.entrada_jugada(ev, guia)
        # OJO: Resultado.__bool__ devuelve `victoria`. Si el duelo se ha
        # perdido, `if resultado:` es False y el bucle no se rompia nunca:
        # el jugador se quedaba en el cartel de DERROTA sin poder continuar.
        if resultado is not None:
            break

        juego.sincronizar_presentacion(time.time())
        if (juego.fin and juego._sfx_fin and not (juego.pausa or juego.historial_abierto)
                and time.time() >= juego.tiempo_fin):
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
    juego.dibujar(screen)
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    capa.fill((0, 0, 0, 180))
    screen.blit(capa, (0, 0))
    texto(screen, "PAUSA", 22, DORADO, centro=(ANCHO // 2, ALTO // 2 - 60))
    texto(screen, "clic o ESC para continuar", 10, TEXTO, centro=(ANCHO // 2, ALTO // 2))
    rect = pygame.Rect(ANCHO // 2 - 130, ALTO // 2 + 30, 260, 44)
    panel(screen, rect, (24, 24, 34, 230), ROJO, radio=8)
    texto(screen, "ABANDONAR DUELO", 11, TEXTO_ON, centro=(rect.centerx, rect.centery))
