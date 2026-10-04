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
import cartas as crt
import facciones
from reglas import (
    CPU,
    USUARIO,
    celdas_vacias,
    capturas,
    contar,
    puntaje_final,
    simular,
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
    REC,
    ROJO,
    TABLERO_H,
    TABLERO_W,
    TEXTO,
    TEXTO_ON,
    TEXTO_TENUE,
    VERDE,
    celda_rect,
    con_alpha,
    ease,
    envolver,
    fundido_entrada,
    mano_rect,
    mezcla,
    panel,
    resplandor,
    texto,
    tooltip,
)

SLOT_BG = (28, 30, 40)
SLOT_BORDE = (92, 84, 62)


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

        self.mano_u = [c.copia() for c in (mano_u_inicial or mazos.TODOS[bando_jugador])]
        self.mano_c = [c.copia() for c in (mano_c_inicial or mazos.TODOS[self.bando_cpu])]
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
        self.banner = None       # (texto, t0, color, subtitulo)
        self.comentario = None
        self.comentario_t0 = 0.0
        self._sfx_fin = None
        self.ganador = None      # USUARIO, CPU o None (empate)
        self._hover_mano = None
        self._arrastre_valido = False

        self.rival = self.info or None
        self.comentario = self.rival.get("entrada") if self.rival else None
        self.comentario_t0 = time.time()
        self.t_entrada = time.time()
        self.avatar = crt.REC.imagen(f"assets/avatar_{self.bando_cpu}.png", (96, 96))
        if not self.avatar.get_width():  # sin arte: silueta
            self.avatar = pygame.Surface((96, 96), pygame.SRCALPHA)
            pygame.draw.circle(self.avatar, facciones.acento(self.bando_cpu), (48, 48), 46)
            pygame.draw.circle(self.avatar, (12, 12, 18), (48, 48), 46, 3)

    # ------------------------------------------------------------- utilidades
    def super_cartas(self, carta, synergy=None):
        if synergy is None:
            synergy = crt.tiene_sinergia(carta, self.board)
        return crt.crear(carta, carta.dueno, synergy=synergy)

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
        caps = capturas(self.board, r, c)
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
            self.banner = (
                f"CADENA DE {len(caps)}", ahora, VERDE if dueno == USUARIO else ROJO,
                f"{len(caps)} cartas cambiaron de bando",
            )
            clave = "captura_cpu" if dueno == CPU else "captura_player"
            if self.rival and self.rival.get(clave):
                self.comentario = self.rival[clave]
                self.comentario_t0 = ahora
        return caps

    def _explosion(self, r, c, dueno):
        rect = celda_rect(r, c)
        color = AZUL if dueno == USUARIO else ROJO
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
        if self.fin or self.pausa:
            return

        # marcador animado
        t, c = contar(self.board)
        for i, objetivo in enumerate((t, c)):
            actual = self.marcador_mostrado[i]
            if actual != objetivo:
                self.marcador_mostrado[i] = int(actual + (objetivo - actual) * min(1.0, dt * 9))
                if abs(self.marcador_mostrado[i] - objetivo) < 1:
                    self.marcador_mostrado[i] = objetivo

        # turno del rival
        if self.turno_cpu and not self.cpu_en_curso:
            self.cpu_en_cola -= dt
            if self.cpu_en_cola <= 0:
                self._jugar_cpu()

        # efectos
        self.flash = [f for f in self.flash if ahora - f[2] < 0.6]
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
        if self.fin:
            self._dibujar_resultado(lienzo, ahora)

        fundido_entrada(lienzo, self.t_entrada, 0.35)

        if dx or dy:
            screen.blit(lienzo, (dx, dy))

    def _dibujar_fondo(self, screen):
        # fondo y capas cacheados: nada de reservar 4 MB por frame
        screen.blit(REC.fondo_pantalla("assets/fondo.png"), (0, 0))
        screen.blit(REC.capa_oscurita((8, 9, 18, 168)), (0, 0))
        # resplandor del color de faccion en el borde inferior
        clave = ("__brillo__", self.bando)
        if clave not in REC.imagenes:
            s = pygame.Surface((ANCHO, 90), pygame.SRCALPHA)
            for i in range(90):
                s.fill(con_alpha(facciones.acento(self.bando), int(40 * (1 - i / 90))),
                       (0, i, ANCHO, 1))
            REC.imagenes[clave] = s
        screen.blit(REC.imagenes[clave], (0, ALTO - 90))

    def _dibujar_hud(self, screen, ahora):
        # barra superior: fase, marcador y manos
        s = pygame.Surface((ANCHO, 74), pygame.SRCALPHA)
        s.fill((12, 13, 20, 210))
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

        # marcador central con separador
        panel(screen, pygame.Rect(ANCHO // 2 - 84, 12, 168, 48), (18, 19, 28, 230), BORDE, radio=8, grosor=1)
        texto(screen, f"{t}", 20, mezcla(AZUL, (255, 255, 255), 0.3), centro=(ANCHO // 2 - 42, 36))
        texto(screen, "-", 14, TEXTO_TENUE, centro=(ANCHO // 2, 36))
        texto(screen, f"{c}", 20, mezcla(ROJO, (255, 255, 255), 0.3), centro=(ANCHO // 2 + 42, 36))

        # manos a los lados del marcador
        texto(screen, f"TU MANO: {len(self.mano_u)}", 8, TEXTO, centro=(ANCHO // 2 - 150, 30))
        texto(screen, f"SU MANO: {len(self.mano_c)}", 8, TEXTO, centro=(ANCHO // 2 + 150, 30))
        texto(screen, "TÚ", 8, mezcla(AZUL, TEXTO_ON, 0.4), centro=(ANCHO // 2 - 150, 52))
        texto(screen, "RIVAL", 8, mezcla(ROJO, TEXTO_ON, 0.4), centro=(ANCHO // 2 + 150, 52))

        # racha
        if self.racha >= 2:
            texto(screen, f"RACHA x{self.racha}", 9, VERDE, centro=(ANCHO - 80, 36))

        # mensaje
        panel(screen, pygame.Rect(ANCHO // 2 - 300, 84, 600, 30), (16, 17, 26, 200), None, radio=8)
        texto(screen, self.mensaje, 9, TEXTO, centro=(ANCHO // 2, 99))

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
                if (r, c) in caps_preview:
                    pygame.draw.rect(screen, VERDE, rect, 4, border_radius=7)
                elif objetivo == (r, c):
                    pygame.draw.rect(screen, DORADO, rect, 4, border_radius=7)
                carta = self.board[r][c]
                if carta:
                    sup = self.super_cartas(carta)
                    if self.ultima_jugada and self.ultima_jugada[0] == r and \
                            self.ultima_jugada[1] == c and ahora - self.ultima_jugada[2] < 0.2:
                        k = (ahora - self.ultima_jugada[2]) / 0.2
                        esc = 0.9 + 0.1 * ease(k)
                        sup = pygame.transform.smoothscale(sup, (int(CARD_W * esc), int(CARD_H * esc)))
                        screen.blit(sup, (rect.centerx - sup.get_width() // 2,
                                           rect.centery - sup.get_height() // 2))
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
            alpha = int(150 * (1 - k))
            overlay = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            color = AZUL if dueno == USUARIO else ROJO
            overlay.fill(con_alpha(color, alpha))
            screen.blit(overlay, celda_rect(r, c).topleft)

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
            ancho = max(70, max(REC.fuente(8).render(l, True, TEXTO).get_width() for l in lineas) + 20)
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
        for i, carta in enumerate(self.mano_u):
            if self.arrastrando and self.arrastrando[0] is carta:
                continue
            rect = mano_rect(i, total)
            hover = rect.collidepoint(mouse) and not self.turno_cpu and not self.fin
            if hover:
                self._hover_mano = carta
            y = rect.y - (18 if hover else 0)
            destino = pygame.Rect(rect.x, y, rect.w, rect.h)
            sup = self.super_cartas(carta, synergy=False)
            if hover:
                crt.resplandor_carta(screen, destino, carta, USUARIO, 110)
                # preview ampliado
                grande = crt.crear(carta, USUARIO, synergy=False, escala=1.35)
                gx = min(ANCHO - grande.get_width() - 10, mouse[0] + 18)
                gy = max(80, min(ALTO - grande.get_height() - 10, mouse[1] - 40))
                sombra = pygame.Surface((grande.get_width(), grande.get_height()), pygame.SRCALPHA)
                sombra.fill((0, 0, 0, 130))
                screen.blit(sombra, (gx + 5, gy + 5))
                screen.blit(grande, (gx, gy))
                if carta.habilidad:
                    tooltip(screen, crt.descripcion_habilidad(carta.habilidad), (gx, gy + grande.get_height()))
            screen.blit(sup, (destino.x, destino.y))

        if self.arrastrando:
            carta, _ = self.arrastrando
            x, y = self.pos_arrastre
            sombra = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            pygame.draw.rect(sombra, (0, 0, 0, 110), sombra.get_rect(), border_radius=7)
            screen.blit(sombra, (x - CARD_W // 2 + 6, y - CARD_H // 2 + 6))
            screen.blit(self.super_cartas(carta, synergy=False),
                        (x - CARD_W // 2, y - CARD_H // 2))

    def _dibujar_particulas(self, screen):
        if not self.particulas:
            return
        s = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        for p in self.particulas:
            k = 1 - p["t"] / p["vida"]
            pygame.draw.circle(s, con_alpha(p["color"], int(220 * k)), (int(p["x"]), int(p["y"])),
                               max(1, int(p["r"] * k)))
        screen.blit(s, (0, 0))

    def _dibujar_banner(self, screen, ahora):
        if not self.banner:
            return
        cadena, t0, color, sub = self.banner
        k = min(1.0, (ahora - t0) / 1.2)
        if k >= 1:
            self.banner = None
            return
        a = int(255 * (1 - k))
        # fondo para que el cartel se lea sobre el tablero
        ancho_texto = REC.fuente(30).render(cadena, True, color).get_width()
        fondo = pygame.Surface((ancho_texto + 80, 96), pygame.SRCALPHA)
        pygame.draw.rect(fondo, (8, 8, 14, int(170 * (1 - k))), fondo.get_rect(), border_radius=10)
        screen.blit(fondo, (ANCHO // 2 - fondo.get_width() // 2, ALTO // 2 - 96))
        texto(screen, cadena, 30, con_alpha(color, a), centro=(ANCHO // 2, ALTO // 2 - 60))
        if sub:
            texto(screen, sub, 10, con_alpha(TEXTO, a), centro=(ANCHO // 2, ALTO // 2 - 24))

    def _dibujar_resultado(self, screen, ahora):
        k = min(1.0, (ahora - self.tiempo_fin) / 0.5)
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((0, 0, 0, int(170 * k)))
        screen.blit(capa, (0, 0))
        caja = pygame.Rect(ANCHO // 2 - 230, ALTO // 2 - 140, 460, 280)
        sombra = pygame.Surface(caja.size, pygame.SRCALPHA)
        pygame.draw.rect(sombra, (0, 0, 0, 150), sombra.get_rect(), border_radius=10)
        screen.blit(sombra, (caja.x + 6, caja.y + 6))
        s = pygame.Surface(caja.size, pygame.SRCALPHA)
        s.fill((20, 20, 30, 240))
        screen.blit(s, caja.topleft)
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
def partida(screen, clock, juego, test_mode=False):
    """Bucle bloqueante del duelo. Devuelve Resultado."""
    audio.sfx(audio.MENU)

    frames = 0
    resultado = None
    while True:
        dt = clock.tick(LIMIT_FPS) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    juego.pausa = not juego.pausa
                    audio.sfx(audio.MENU_BACK if juego.pausa else audio.MENU)
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_h and not juego.turno_cpu:
                juego.mensaje = "Consejo: Same y Plus voltean al vuelo"
            if juego.pausa:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if _pausa_clic(screen, ev.pos):
                        return Resultado(False, juego.capturas, juego.jugadas, (0, 0))
                continue
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if juego.fin and now_clickable(time.time(), juego.tiempo_fin):
                    resultado = Resultado(
                        juego.ganador in (USUARIO, None),
                        juego.capturas, juego.jugadas,
                        contar(juego.board), juego.ganador is None, juego.racha,
                    )
                    break
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
                    caps = juego.colocar(carta, juego.mano_u, USUARIO, *celda)
                    juego.mensaje = f"Juegas {carta.nombre}"
                    if caps:
                        juego.mensaje += f" y capturas {len(caps)}"
                    juego.turno_cpu = True
                    juego.cpu_en_cola = 0.85
                    juego.cpu_en_curso = False
                else:
                    audio.sfx(audio.INVALIDO, 0.5)
                juego.comprobar_fin()
        if resultado:
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
        pygame.display.flip()
        frames += 1
        if test_mode and frames > 40:
            return Resultado(True, 0, 0, (0, 0))
        if resultado:
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