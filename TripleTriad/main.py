"""Triple Triad con interfaz gráfica (pygame) - Goblins vs Elfos."""

import copy
import os
import random
import re
import sys
import time
import unicodedata

import pygame

from reglas import CPU, USUARIO, Carta, capturas, celdas_vacias, contar, simular, val
from mazos import ELFOS, GOBLINS


def slug(nombre):
    s = nombre.lower().strip()
    s = re.sub(r"[áà]", "a", s)
    s = re.sub(r"[éè]", "e", s)
    s = re.sub(r"[íì]", "i", s)
    s = re.sub(r"[óò]", "o", s)
    s = re.sub(r"[úù]", "u", s)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def clean(texto):
    """La fuente pixelada no tiene tildes: las quitamos."""
    texto = texto.replace("¡", "!").replace("¿", "?").replace("—", "-")
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


_IMAGENES = {}

ANCHO, ALTO = 1024, 760
CARD_W, CARD_H = 96, 132
PASO_X = CARD_W + 12
PASO_Y = CARD_H + 12
TABLERO_ANCHO = 3 * CARD_W + 2 * 12
TABLERO_ALTO = 3 * CARD_H + 2 * 12
TABLERO_X = (ANCHO - TABLERO_ANCHO) // 2
TABLERO_Y = 150
MANO_Y = ALTO - CARD_H - 16

COLORES = {
    "goblin": ((104, 150, 62), (43, 74, 26)),
    "elfo": ((172, 201, 236), (52, 78, 122)),
    "hombre_lobo": ((110, 120, 140), (40, 45, 58)),
    "vampiro": ((140, 50, 70), (70, 20, 32)),
    "dragon": ((190, 90, 50), (110, 40, 20)),
}
NOMBRES_BANDO_GUI = {
    "goblin": "Goblins",
    "elfo": "Elfos",
    "hombre_lobo": "Hombres Lobo",
    "vampiro": "Vampiros",
    "dragon": "Dragones",
}
AZUL_BORDE = (70, 140, 235)
ROJO_BORDE = (225, 75, 65)
VERDE_PREVIEW = (90, 230, 120)
SLOT_BG = (30, 33, 44)
SLOT_BORDE = (90, 82, 60)
TEXTO = (240, 238, 225)
DORADO = (240, 200, 90)

TEST = "--test" in sys.argv


def recurso(ruta):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, ruta)


_FUENTES = {}


def fuente(tam):
    if tam not in _FUENTES:
        _FUENTES[tam] = pygame.font.Font(
            recurso(os.path.join("assets", "PressStart2P.ttf")), tam
        )
    return _FUENTES[tam]


_SONIDOS = {}


def sonido(nombre):
    if nombre not in _SONIDOS:
        try:
            _SONIDOS[nombre] = pygame.mixer.Sound(recurso(os.path.join("assets", nombre)))
        except Exception:
            _SONIDOS[nombre] = None
    return _SONIDOS[nombre]


def reproducir(nombre):
    s = sonido(nombre)
    if s:
        s.play()


_FONDO = None


def fondo():
    global _FONDO
    if _FONDO is None:
        ruta = recurso(os.path.join("assets", "fondo.png"))
        if os.path.exists(ruta):
            _FONDO = pygame.transform.scale(pygame.image.load(ruta), (ANCHO, ALTO))
        else:
            _FONDO = pygame.Surface((ANCHO, ALTO))
            _FONDO.fill((24, 26, 34))
    return _FONDO


def crear_superficie_carta(carta):
    s = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    fondo_c, borde = COLORES[carta.bando]
    pygame.draw.rect(s, borde, (0, 0, CARD_W, CARD_H), border_radius=6)
    pygame.draw.rect(s, fondo_c, (4, 4, CARD_W - 8, CARD_H - 8), border_radius=4)

    f_nom = fuente(9)
    f_val = fuente(13)

    ruta = os.path.join(
        recurso("cartas"), f"{carta.bando}_{slug(carta.nombre)}.png"
    )
    img_carta = _IMAGENES.get(carta.nombre)
    if img_carta is None and os.path.exists(ruta):
        img_carta = pygame.image.load(ruta)
        img_carta = pygame.transform.scale(img_carta, (CARD_W - 8, CARD_H - 8))
        _IMAGENES[carta.nombre] = img_carta

    if img_carta:
        s.blit(img_carta, (4, 4))
        franja = pygame.Surface((CARD_W - 8, 18), pygame.SRCALPHA)
        franja.fill((0, 0, 0, 170))
        s.blit(franja, (4, 4))
        nom = f_nom.render(clean(carta.nombre), True, (245, 245, 245))
        if nom.get_width() > CARD_W - 10:
            nom = pygame.transform.smoothscale(nom, (CARD_W - 10, nom.get_height()))
        s.blit(nom, (CARD_W // 2 - nom.get_width() // 2, 6))
    else:
        nom = f_nom.render(clean(carta.nombre), True, (15, 15, 15))
        if nom.get_width() > CARD_W - 10:
            nom = pygame.transform.smoothscale(nom, (CARD_W - 10, nom.get_height()))
        s.blit(nom, (CARD_W // 2 - nom.get_width() // 2, 8))
        pygame.draw.circle(s, borde, (CARD_W // 2, CARD_H // 2), 26)
        f_big = fuente(30)
        letra = {"goblin": "G", "elfo": "E", "hombre_lobo": "L", "vampiro": "V", "dragon": "D"}[carta.bando]
        img = f_big.render(letra, True, (245, 245, 245))
        s.blit(img, (CARD_W // 2 - img.get_width() // 2, CARD_H // 2 - img.get_height() // 2))

    if carta.habilidad == "quema":
        # indicador de habilidad: llama roja en la esquina
        pygame.draw.polygon(s, (255, 90, 20), [(CARD_W - 14, CARD_H - 8), (CARD_W - 8, CARD_H - 22), (CARD_W - 4, CARD_H - 8)])

    v = carta.valores
    for texto, pos in [
        (val(v["N"]), (CARD_W // 2, 27)),
        (val(v["S"]), (CARD_W // 2, CARD_H - 27)),
        (val(v["O"]), (14, CARD_H // 2)),
        (val(v["E"]), (CARD_W - 14, CARD_H // 2)),
    ]:
        img = f_val.render(texto, True, (255, 255, 255))
        pygame.draw.circle(s, (10, 10, 10), pos, 10)
        s.blit(img, (pos[0] - img.get_width() // 2, pos[1] - img.get_height() // 2))
    return s


def crear_dorso():
    s = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(s, (90, 66, 120), (0, 0, CARD_W, CARD_H), border_radius=6)
    pygame.draw.rect(s, (55, 38, 80), (6, 6, CARD_W - 12, CARD_H - 12), border_radius=4)
    f = fuente(26)
    img = f.render("?", True, (200, 180, 230))
    s.blit(img, (CARD_W // 2 - img.get_width() // 2, CARD_H // 2 - img.get_height() // 2))
    return s


def celda_rect(r, c):
    return pygame.Rect(TABLERO_X + c * PASO_X, TABLERO_Y + r * PASO_Y, CARD_W, CARD_H)


def mano_rect(i):
    mano_ancho = 5 * CARD_W + 4 * 14
    inicio = (ANCHO - mano_ancho) // 2
    return pygame.Rect(inicio + i * PASO_X, MANO_Y, CARD_W, CARD_H)


def jugada_cpu(board, mano):
    mejor, mejor_puntos = None, -1
    for i, carta in enumerate(mano):
        for r, c in celdas_vacias(board):
            puntos = simular(board, carta, r, c, CPU)
            if carta.bando == "dragon" and (r, c) == (1, 1):
                puntos += 2  # los dragones ambicionan la casilla central
            if puntos > mejor_puntos:
                mejor_puntos, mejor = puntos, (i, r, c)
    return mejor


def panel(screen, rect, alpha=180):
    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    s.fill((10, 10, 16, alpha))
    screen.blit(s, rect.topleft)
    pygame.draw.rect(screen, DORADO, rect, 2, border_radius=6)


class Juego:
    def __init__(self, bando_jugador, bando_rival=None, mano_u_inicial=None):
        self.bando = bando_jugador
        import mazos as _mazos
        if bando_rival is None:
            bando_rival = random.choice([b for b in _mazos.TODOS if b != bando_jugador])
        self.bando_cpu = bando_rival
        if mano_u_inicial is not None:
            self.mano_u = mano_u_inicial
        else:
            self.mano_u = [c.copia() for c in _mazos.TODOS[bando_jugador]]
        self.mano_c = [c.copia() for c in _mazos.TODOS[bando_rival]]
        for c in self.mano_u:
            c.dueno = USUARIO
        for c in self.mano_c:
            c.dueno = CPU
        self.board = [[None] * 3 for _ in range(3)]
        self.turno_cpu = False
        self.cpu_lista = False
        self.mensaje = "Tu turno: arrastra una carta al tablero"
        self.arrastrando = None
        self.pos_arrastre = (0, 0)
        self.fin = False
        self.superficies = {}
        self.flash = []
        self.ultima_jugada = None
        self.gano_sonido = False
        self.tiempo_fin = None
        import campana as _campana
        self.rival = _campana.DUELISTAS.get(bando_rival)
        self.comentario = self.rival["entrada"] if self.rival else None
        self.comentario_t0 = time.time()
        self.avatar = None
        if self.rival:
            ruta = recurso(os.path.join("assets", f"avatar_{bando_rival}.png"))
            if os.path.exists(ruta):
                self.avatar = pygame.transform.scale(pygame.image.load(ruta), (72, 72))

    def sup(self, carta):
        if id(carta) not in self.superficies:
            self.superficies[id(carta)] = crear_superficie_carta(carta)
        return self.superficies[id(carta)]

    def colocar(self, carta, mano, dueno, r, c):
        mano.remove(carta)
        carta.dueno = dueno
        self.board[r][c] = carta
        caps = capturas(self.board, r, c)
        ahora = time.time()
        self.ultima_jugada = (r, c, ahora)
        for (cr, cc) in caps:
            self.flash.append((cr, cc, ahora, dueno))
        reproducir("place.wav")
        if caps:
            reproducir("capture.wav")
            if self.rival:
                clave = "captura_cpu" if dueno == CPU else "captura_player"
                self.comentario = self.rival[clave]
                self.comentario_t0 = time.time()
        return caps

    def actualizar(self):
        if self.fin:
            return
        if self.turno_cpu and self.cpu_lista and time.time() >= self.cpu_lista:
            self.cpu_lista = False
            jugada = jugada_cpu(self.board, self.mano_c)
            if jugada is None:
                self.turno_cpu = False
                self.comprobar_fin()
                return
            idx, r, c = jugada
            carta = self.mano_c[idx]
            caps = self.colocar(carta, self.mano_c, CPU, r, c)
            self.mensaje = f"CPU juega {carta.nombre}"
            if caps:
                self.mensaje += f" y captura {len(caps)}"
            self.turno_cpu = False
            self.comprobar_fin()
            if not self.fin:
                self.mensaje += " - tu turno"

    def comprobar_fin(self):
        if not celdas_vacias(self.board) or (not self.mano_u and not self.mano_c):
            self.fin = True
            t, c = contar(self.board)
            if t > c:
                self.mensaje = f"!Ganaste! {t} - {c}"
            elif c > t:
                self.mensaje = f"CPU gana. {t} - {c}"
            else:
                self.mensaje = f"Empate {t} - {c}"

    def preview_capturas(self):
        """Celdas capturadas si soltara la carta arrastrada en la casilla bajo el mouse."""
        if not self.arrastrando:
            return None, set()
        carta = self.arrastrando[0]
        for r in range(3):
            for c in range(3):
                if celda_rect(r, c).collidepoint(self.pos_arrastre) and self.board[r][c] is None:
                    nb = copy.deepcopy(self.board)
                    nueva = carta.copia()
                    nueva.dueno = USUARIO
                    nb[r][c] = nueva
                    caps = capturas(nb, r, c)
                    return (r, c), set(caps)
        return None, set()

    def dibujar(self, screen):
        screen.blit(fondo(), (0, 0))
        ahora = time.time()

        # HUD superior
        titulo = fuente(20).render(clean("TRIPLE TRIAD"), True, DORADO)
        screen.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 14))
        panel(screen, pygame.Rect(ANCHO // 2 - 340, 48, 680, 34))
        msg = fuente(11).render(clean(self.mensaje), True, TEXTO)
        screen.blit(msg, (ANCHO // 2 - msg.get_width() // 2, 58))

        t, c = contar(self.board)
        panel(screen, pygame.Rect(ANCHO // 2 - 200, 92, 400, 32))
        marcador = fuente(13).render(clean(f"Tu {t} - {c} CPU   |   CPU: {len(self.mano_c)} cartas"), True, TEXTO)
        screen.blit(marcador, (ANCHO // 2 - marcador.get_width() // 2, 104))

        # Marco del tablero
        marco = pygame.Rect(TABLERO_X - 10, TABLERO_Y - 10, TABLERO_ANCHO + 20, TABLERO_ALTO + 20)
        pygame.draw.rect(screen, (52, 44, 30), marco, border_radius=10)
        pygame.draw.rect(screen, DORADO, marco, 3, border_radius=10)

        # Preview de capturas mientras arrastras
        objetivo, caps_preview = self.preview_capturas()

        self.flash = [f for f in self.flash if ahora - f[2] < 0.7]
        for r in range(3):
            for c in range(3):
                rect = celda_rect(r, c)
                pygame.draw.rect(screen, SLOT_BG, rect, border_radius=6)
                pygame.draw.rect(screen, SLOT_BORDE, rect, 2, border_radius=6)
                if (r, c) in caps_preview:
                    pygame.draw.rect(screen, VERDE_PREVIEW, rect, 4, border_radius=6)
                if objetivo == (r, c):
                    pygame.draw.rect(screen, DORADO, rect, 4, border_radius=6)
                carta = self.board[r][c]
                if carta:
                    # animación de llegada
                    if self.ultima_jugada and self.ultima_jugada[0] == r and self.ultima_jugada[1] == c and ahora - self.ultima_jugada[2] < 0.18:
                        esc = 0.9 + (ahora - self.ultima_jugada[2]) / 0.18 * 0.1
                        sup = pygame.transform.scale(self.sup(carta), (int(CARD_W * esc), int(CARD_H * esc)))
                        screen.blit(sup, (rect.centerx - sup.get_width() // 2, rect.centery - sup.get_height() // 2))
                    else:
                        screen.blit(self.sup(carta), rect.topleft)
                    borde = AZUL_BORDE if carta.dueno == USUARIO else ROJO_BORDE
                    pygame.draw.rect(screen, borde, rect, 4, border_radius=6)
                # casilla elemental central marcada en fuego
                if (r, c) == (1, 1):
                    pygame.draw.circle(screen, (255, 140, 40), (rect.right - 10, rect.bottom - 10), 4)

        for (r, c, t0, dueno) in self.flash:
            alpha = max(0, int(170 * (1 - (ahora - t0) / 0.7)))
            overlay = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            color = AZUL_BORDE if dueno == USUARIO else ROJO_BORDE
            overlay.fill((*color, alpha))
            screen.blit(overlay, celda_rect(r, c).topleft)

        if self.ultima_jugada:
            r, c, t0 = self.ultima_jugada
            if ahora - t0 < 1.2:
                alpha = max(0, int(255 * (1 - (ahora - t0) / 1.2)))
                glow = pygame.Surface((CARD_W + 8, CARD_H + 8), pygame.SRCALPHA)
                pygame.draw.rect(glow, (255, 230, 120, alpha), glow.get_rect(), 4, border_radius=8)
                screen.blit(glow, (celda_rect(r, c).x - 4, celda_rect(r, c).y - 4))

        # Avatar del rival + bocadillo
        if self.avatar:
            ax, ay = ANCHO - 90, 140
            screen.blit(self.avatar, (ax, ay))
            pygame.draw.rect(screen, DORADO, (ax, ay, 72, 72), 2)
            if self.comentario and time.time() - self.comentario_t0 < 3.5:
                cb = fuente(9).render(clean(self.comentario), True, TEXTO)
                bw = cb.get_width() + 16
                panel(screen, pygame.Rect(ax - bw - 10, ay + 20, bw, 24))
                screen.blit(cb, (ax - bw - 10 + 8, ay + 27))

        # Mano con elevación al hover
        mouse = pygame.mouse.get_pos()
        for i, carta in enumerate(self.mano_u):
            if self.arrastrando and self.arrastrando[0] is carta:
                continue
            rect = mano_rect(i)
            y = rect.y - 12 if rect.collidepoint(mouse) and not self.turno_cpu else rect.y
            screen.blit(self.sup(carta), (rect.x, y))

        if self.arrastrando:
            carta, sup = self.arrastrando
            x, y = self.pos_arrastre
            sombra = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
            pygame.draw.rect(sombra, (0, 0, 0, 90), sombra.get_rect(), border_radius=6)
            screen.blit(sombra, (x - CARD_W // 2 + 5, y - CARD_H // 2 + 5))
            screen.blit(sup, (x - CARD_W // 2, y - CARD_H // 2))

        if self.fin:
            if not self.gano_sonido:
                reproducir("win.wav")
                self.gano_sonido = True
            overlay = pygame.Surface((ANCHO, 64), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, ALTO // 2 - 32))
            msg2 = fuente(16).render(clean(self.mensaje + "  (ESC salir)"), True, TEXTO)
            screen.blit(msg2, (ANCHO // 2 - msg2.get_width() // 2, ALTO // 2 - 8))


def pantalla_inicio(screen):
    opciones = []
    import mazos as _mazos
    for bando, cartas in _mazos.TODOS.items():
        if bando == "dragon":
            continue
        opciones.append((bando, cartas[-1]))
    escala = 1.3
    w, h = int(CARD_W * escala), int(CARD_H * escala)
    gap = 40
    total = 4 * w + 3 * gap
    x0 = ANCHO // 2 - total // 2
    y_carta = 260
    for i, (bando, carta) in enumerate(opciones):
        surf = pygame.transform.scale(crear_superficie_carta(carta), (w, h))
        rect = pygame.Rect(x0 + i * (w + gap), y_carta, w, h)
        opciones[i] = (bando, carta, surf, rect)

    while True:
        mouse = pygame.mouse.get_pos()
        screen.blit(fondo(), (0, 0))
        t = fuente(30).render(clean("TRIPLE TRIAD"), True, DORADO)
        screen.blit(t, (ANCHO // 2 - t.get_width() // 2, 100))
        sub = fuente(11).render(clean("Elige tu bando: pasa el mouse y haz clic"), True, TEXTO)
        panel(screen, pygame.Rect(ANCHO // 2 - 300, 165, 600, 32))
        screen.blit(sub, (ANCHO // 2 - sub.get_width() // 2, 174))

        for bando, carta, surf, rect in opciones:
            if rect.collidepoint(mouse):
                rect_h = rect.inflate(14, 14)
                glow = pygame.Surface((rect_h.w, rect_h.h), pygame.SRCALPHA)
                pygame.draw.rect(glow, (255, 230, 120, 130), glow.get_rect(), border_radius=10)
                screen.blit(glow, rect_h.topleft)
                screen.blit(pygame.transform.scale(surf, (rect_h.w, rect_h.h)), rect_h.topleft)
            else:
                screen.blit(surf, rect.topleft)
            et = fuente(11).render(clean(NOMBRES_BANDO_GUI[bando]), True, TEXTO)
            panel(screen, pygame.Rect(rect.centerx - 80, rect.bottom + 12, 160, 28))
            screen.blit(et, (rect.centerx - et.get_width() // 2, rect.bottom + 19))

        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for bando, carta, surf, rect in opciones:
                    if rect.collidepoint(ev.pos):
                        return bando


def pantalla_menu(screen):
    while True:
        screen.blit(fondo(), (0, 0))
        t = fuente(26).render(clean("TRIPLE TRIAD"), True, DORADO)
        screen.blit(t, (ANCHO // 2 - t.get_width() // 2, 150))
        botones = [
            ("PARTIDA RAPIDA", pygame.Rect(ANCHO // 2 - 160, 280, 320, 48)),
            ("CAMPANA", pygame.Rect(ANCHO // 2 - 160, 350, 320, 48)),
        ]
        mouse = pygame.mouse.get_pos()
        for texto, rect in botones:
            panel(screen, rect)
            if rect.collidepoint(mouse):
                pygame.draw.rect(screen, DORADO, rect, 4, border_radius=6)
            img = fuente(13).render(clean(texto), True, TEXTO)
            screen.blit(img, (rect.centerx - img.get_width() // 2, rect.centery - 8))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for texto, rect in botones:
                    if rect.collidepoint(ev.pos):
                        return "rapida" if "RAPIDA" in texto else "campana"


def esperar_click(screen, lineas, titulo=None):
    while True:
        screen.blit(fondo(), (0, 0))
        y = 180
        if titulo:
            img = fuente(24).render(clean(titulo), True, DORADO)
            screen.blit(img, (ANCHO // 2 - img.get_width() // 2, y))
            y += 70
        for linea in lineas:
            img = fuente(12).render(clean(linea), True, TEXTO)
            screen.blit(img, (ANCHO // 2 - img.get_width() // 2, y))
            y += 36
        img = fuente(10).render(clean("Haz clic para continuar"), True, (180, 180, 190))
        screen.blit(img, (ANCHO // 2 - img.get_width() // 2, ALTO - 80))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                return


def presentar_duelo(screen, estado, rival):
    import campana as _c
    d = _c.DUELISTAS[rival]
    ruta = recurso(os.path.join("assets", f"avatar_{rival}.png"))
    avatar = None
    if os.path.exists(ruta):
        avatar = pygame.transform.scale(pygame.image.load(ruta), (128, 128))
    while True:
        screen.blit(fondo(), (0, 0))
        etapa = estado["etapa"] + 1
        titulo = fuente(20).render(clean(f"DUELO {etapa}/5"), True, DORADO)
        screen.blit(titulo, (ANCHO // 2 - titulo.get_width() // 2, 90))
        if avatar:
            screen.blit(avatar, (ANCHO // 2 - 64, 150))
            pygame.draw.rect(screen, DORADO, (ANCHO // 2 - 64, 150, 128, 128), 3)
        nombre = fuente(14).render(clean(d["nombre"]), True, TEXTO)
        screen.blit(nombre, (ANCHO // 2 - nombre.get_width() // 2, 300))
        sub = fuente(10).render(clean(d["titulo"]), True, (190, 190, 200))
        screen.blit(sub, (ANCHO // 2 - sub.get_width() // 2, 330))
        panel(screen, pygame.Rect(ANCHO // 2 - 320, 380, 640, 36))
        frase = fuente(11).render(clean(d["entrada"]), True, TEXTO)
        screen.blit(frase, (ANCHO // 2 - frase.get_width() // 2, 390))
        cont = fuente(10).render(clean("Haz clic para luchar"), True, (180, 180, 190))
        screen.blit(cont, (ANCHO // 2 - cont.get_width() // 2, ALTO - 80))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                return


def pantalla_mejora(screen, estado):
    import campana as _c
    elegida = None
    while elegida is None:
        screen.blit(fondo(), (0, 0))
        t = fuente(16).render(clean("Victoria! Elige una carta para mejorar (+1)"), True, DORADO)
        screen.blit(t, (ANCHO // 2 - t.get_width() // 2, 80))
        cartas = _c.cartas_jugador(estado)
        rects = []
        n = len(cartas)
        for i, carta in enumerate(cartas):
            w, h = CARD_W, CARD_H
            x = ANCHO // 2 - (n * (w + 12) - 12) // 2 + i * (w + 12)
            y = 220
            screen.blit(crear_superficie_carta(carta), (x, y))
            rects.append(pygame.Rect(x, y, w, h))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        lado = _c.mejorar_carta(estado, i)
                        _c.guardar(estado)
                        elegida = (i, lado)
        if elegida:
            esperar_click(
                screen,
                [f"{estado['cartas'][elegida[0]]['nombre']} mejoro su lado {elegida[1].upper()}!"],
                titulo="Carta mejorada",
            )


def pantalla_post_victoria(screen, estado):
    import campana as _c
    while True:
        screen.blit(fondo(), (0, 0))
        t = fuente(16).render(clean("Victoria! Elige tu recompensa"), True, DORADO)
        screen.blit(t, (ANCHO // 2 - t.get_width() // 2, 140))
        botones = [
            ("MEJORAR CARTA", pygame.Rect(ANCHO // 2 - 170, 260, 340, 50)),
            ("ROBAR CARTA", pygame.Rect(ANCHO // 2 - 170, 330, 340, 50)),
        ]
        mouse = pygame.mouse.get_pos()
        for texto, rect in botones:
            panel(screen, rect)
            if rect.collidepoint(mouse):
                pygame.draw.rect(screen, DORADO, rect, 4, border_radius=6)
            img = fuente(13).render(clean(texto), True, TEXTO)
            screen.blit(img, (rect.centerx - img.get_width() // 2, rect.centery - 8))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for texto, rect in botones:
                    if rect.collidepoint(ev.pos):
                        if "MEJORAR" in texto:
                            pantalla_mejora(screen, estado)
                        else:
                            pantalla_draft(screen, estado)
                        return


def pantalla_draft(screen, estado):
    import campana as _c
    import mazos as _m
    pool = []
    for bando, cartas in _m.TODOS.items():
        for c in cartas:
            pool.append(c)
    ofertas = random.sample(pool, 3)
    elegida = None
    while elegida is None:
        screen.blit(fondo(), (0, 0))
        t = fuente(14).render(clean("Elige una carta del pool"), True, DORADO)
        screen.blit(t, (ANCHO // 2 - t.get_width() // 2, 90))
        rects = []
        n = len(ofertas)
        for i, carta in enumerate(ofertas):
            w, h = CARD_W, CARD_H
            x = ANCHO // 2 - (n * (w + 16) - 16) // 2 + i * (w + 16)
            screen.blit(crear_superficie_carta(carta), (x, 200))
            rects.append(pygame.Rect(x, 200, w, h))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        elegida = ofertas[i]
    # elegir cuál reemplazar
    while True:
        screen.blit(fondo(), (0, 0))
        t = fuente(14).render(clean(f"{elegida.nombre}! Que carta reemplaza?"), True, DORADO)
        screen.blit(t, (ANCHO // 2 - t.get_width() // 2, 90))
        cartas = _c.cartas_jugador(estado)
        rects = []
        n = len(cartas)
        for i, carta in enumerate(cartas):
            w, h = CARD_W, CARD_H
            x = ANCHO // 2 - (n * (w + 12) - 12) // 2 + i * (w + 12)
            screen.blit(crear_superficie_carta(carta), (x, 220))
            rects.append(pygame.Rect(x, 220, w, h))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, rect in enumerate(rects):
                    if rect.collidepoint(ev.pos):
                        estado["cartas"][i] = {
                            "nombre": elegida.nombre,
                            "n": elegida.valores["N"],
                            "s": elegida.valores["S"],
                            "e": elegida.valores["E"],
                            "o": elegida.valores["O"],
                            "bando": elegida.bando,
                            "habilidad": elegida.habilidad,
                        }
                        _c.guardar(estado)
                        esperar_click(screen, [f"{cartas[i].nombre} fue reemplazada."], titulo="Draft")
                        return


def partida(screen, clock, juego):
    """Loop de juego. Devuelve True si ganaste."""
    frames = 0
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if not juego.fin and not juego.turno_cpu:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    for i, carta in enumerate(juego.mano_u):
                        rect = mano_rect(i)
                        if rect.collidepoint(ev.pos):
                            juego.arrastrando = (carta, juego.sup(carta))
                            juego.pos_arrastre = ev.pos
                            break
                if ev.type == pygame.MOUSEMOTION and juego.arrastrando:
                    juego.pos_arrastre = ev.pos
                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and juego.arrastrando:
                    carta, sup = juego.arrastrando
                    juego.arrastrando = None
                    soltado = False
                    for r in range(3):
                        for c in range(3):
                            if celda_rect(r, c).collidepoint(ev.pos) and juego.board[r][c] is None:
                                caps = juego.colocar(carta, juego.mano_u, USUARIO, r, c)
                                juego.mensaje = f"Juegas {carta.nombre}"
                                if caps:
                                    juego.mensaje += f" y capturas {len(caps)}"
                                juego.turno_cpu = True
                                juego.cpu_lista = time.time() + 0.9
                                soltado = True
                                break
                        if soltado:
                            break
                    juego.comprobar_fin()

        juego.actualizar()
        juego.dibujar(screen)
        pygame.display.flip()
        clock.tick(60)
        frames += 1
        if TEST and frames > 90:
            pygame.quit()
            return True
        if juego.fin:
            if juego.tiempo_fin is None:
                juego.tiempo_fin = time.time()
            if time.time() - juego.tiempo_fin > 2.0:
                return juego.mensaje.startswith("!Ganaste")


def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    screen = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Triple Triad - Goblins vs Elfos")
    clock = pygame.time.Clock()

    modo = "rapida" if TEST else pantalla_menu(screen)
    if modo == "rapida":
        bando = "goblin" if TEST else pantalla_inicio(screen)
        juego = Juego(bando)
        partida(screen, clock, juego)
        return

    # Campaña
    import campana as _c
    estado = _c.cargar() or _c.nueva_campana()
    if estado["completada"]:
        esperar_click(screen, ["Ya completaste la campana! Se reinicio el perfil."], titulo="Victoria")
        estado = _c.nueva_campana()
        _c.guardar(estado)
    while not estado["completada"]:
        rival = _c.rival_actual(estado)
        if rival is None:
            estado["completada"] = True
            _c.guardar(estado)
            break
        presentar_duelo(screen, estado, rival)
        mano = _c.cartas_jugador(estado)
        for c in mano:
            c.dueno = USUARIO
        juego = Juego(estado["mazo_jugador"], bando_rival=rival, mano_u_inicial=mano)
        victoria = partida(screen, clock, juego)
        if victoria:
            estado["etapa"] += 1
            if estado["etapa"] >= len(_c.ORDEN):
                estado["completada"] = True
                _c.guardar(estado)
                esperar_click(screen, ["FELICIDADES! Derrotaste al Rey Dragon.", "Campana completada!"], titulo="Victoria")
            else:
                _c.guardar(estado)
                pantalla_post_victoria(screen, estado)
        else:
            salir = derrota_menu(screen)
            if salir:
                return


def derrota_menu(screen):
    while True:
        screen.blit(fondo(), (0, 0))
        t = fuente(20).render(clean("Derrota..."), True, DORADO)
        screen.blit(t, (ANCHO // 2 - t.get_width() // 2, 200))
        botones = [
            ("REINTENTAR", pygame.Rect(ANCHO // 2 - 160, 300, 320, 48), False),
            ("MENU", pygame.Rect(ANCHO // 2 - 160, 370, 320, 48), True),
        ]
        mouse = pygame.mouse.get_pos()
        for texto, rect, sale in botones:
            panel(screen, rect)
            if rect.collidepoint(mouse):
                pygame.draw.rect(screen, DORADO, rect, 4, border_radius=6)
            img = fuente(13).render(clean(texto), True, TEXTO)
            screen.blit(img, (rect.centerx - img.get_width() // 2, rect.centery - 8))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for texto, rect, sale in botones:
                    if rect.collidepoint(ev.pos):
                        return sale


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        with open("crash.log", "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        raise
