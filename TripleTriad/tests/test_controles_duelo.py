"""Recorridos completos con teclado/clic y prevision del motor real."""

import asyncio
import copy
import os
import tempfile
import time
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import mazos
import opciones
import tutorial
from partida import Juego, partida
from reglas import Carta, CPU, USUARIO
from ui import ANCHO, ALTO, celda_rect, mano_rect


def tecla(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def clic(pos):
    return [pygame.event.Event(tipo, button=1, pos=pos)
            for tipo in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)]


class Reloj:
    def tick(self, fps=60):
        return 1000


class TestControlesDuelo(unittest.TestCase):
    def setUp(self):
        datos = tempfile.TemporaryDirectory(prefix="tt_controles_")
        self.addCleanup(datos.cleanup)
        env = patch.dict(os.environ, {"TRIPLETRIAD_DATA": datos.name})
        env.start()
        self.addCleanup(env.stop)
        opciones.invalidar()
        self.addCleanup(opciones.invalidar)
        pygame.init()
        self.screen = pygame.display.set_mode((ANCHO, ALTO))
        self.juego = Juego("humano", bando_rival="orco",
                           mano_u_inicial=mazos.HUMANOS[:5], mano_c_inicial=mazos.ORCOS[:5])

    def _duelo_completo(self, teclado):
        frames = 0

        def eventos():
            nonlocal frames
            frames += 1
            self.assertLess(frames, 50, "los controles no permiten terminar el duelo")
            if self.juego.fin:
                self.juego.tiempo_fin = time.time() - 1
                return [tecla(pygame.K_RETURN)]
            if self.juego.turno_cpu:
                return []
            if teclado:
                return [tecla(pygame.K_RETURN)]
            if self.juego.seleccionada is None:
                return clic(mano_rect(0, len(self.juego.mano_u)).center)
            return clic(celda_rect(*self.juego.celdas_libres()[0]).center)

        with patch("pygame.event.get", side_effect=eventos):
            resultado = asyncio.run(partida(self.screen, Reloj(), self.juego))
        self.assertFalse(resultado.abandonado)
        self.assertEqual(sum(resultado.marcador), 9)
        self.assertEqual(len(self.juego.historial), 9)

    def test_duelo_completo_solo_con_teclado(self):
        self._duelo_completo(True)

    def test_duelo_completo_con_clic_sin_arrastre(self):
        self._duelo_completo(False)

    def test_arrastre_sigue_colocando_una_sola_carta(self):
        mano = mano_rect(0, 5).center
        destino = celda_rect(1, 1).center
        for ev in [clic(mano)[0], pygame.event.Event(pygame.MOUSEMOTION, pos=destino),
                   clic(destino)[1]]:
            self.juego.entrada_jugada(ev)
        self.assertEqual(len(self.juego.mano_u), 4)
        self.assertIsNotNone(self.juego.board[1][1])
        self.assertTrue(self.juego.turno_cpu)

    def test_cancelar_no_consume_turno_y_las_flechas_cambian_casilla(self):
        self.juego.entrada_jugada(tecla(pygame.K_RETURN))
        self.juego.entrada_jugada(tecla(pygame.K_RIGHT))
        self.assertEqual(self.juego.celda_foco, (0, 1))
        self.juego.entrada_jugada(tecla(pygame.K_ESCAPE))
        self.assertIsNone(self.juego.seleccionada)
        self.assertEqual(len(self.juego.celdas_libres()), 9)
        self.assertFalse(self.juego.turno_cpu)

    def test_clic_en_pausa_reanuda_sin_colocar(self):
        self.juego.pausa = True
        eventos = iter([clic((400, 350)), [tecla(pygame.K_ESCAPE)],
                        clic((ANCHO // 2, ALTO // 2 + 45))])
        with patch("pygame.event.get", side_effect=lambda: next(eventos)):
            resultado = asyncio.run(partida(self.screen, Reloj(), self.juego))
        self.assertTrue(resultado.abandonado)
        self.assertEqual(len(self.juego.celdas_libres()), 9)

    def test_preview_same_y_cadena_coincide_con_jugada_sin_mutar_tablero(self):
        for i, nombre in ((1, "Same"), (2, "Cadena")):
            juego, guia = tutorial.construir_duelo_practica(tutorial.PRACTICAS[i], i)
            carta = juego.mano_u[0]
            destino = guia.paso_actual()["validas"][0]
            juego.seleccionada = carta
            juego.pos_arrastre = celda_rect(*destino).center
            antes = copy.deepcopy([[c.a_dict() | {"dueno": c.dueno} if c else None
                                     for c in fila] for fila in juego.board])
            objetivo, caps, lineas = juego.detalle_preview()
            self.assertEqual(objetivo, destino)
            self.assertTrue(any(nombre in l for l in lineas), lineas)
            self.assertEqual(antes, [[c.a_dict() | {"dueno": c.dueno} if c else None
                                     for c in fila] for fila in juego.board])
            reales = juego.colocar(carta, juego.mano_u, USUARIO, *destino)
            self.assertEqual(set(caps), set(reales))
            self.assertEqual(lineas, juego.historial[-1]["lineas"])

    def test_preview_explica_muro(self):
        self.juego.board[0][1] = Carta("Muro", 1, 1, 1, 10, CPU, "humano", "muro")
        self.juego.seleccionada = self.juego.mano_u[0]
        self.juego.pos_arrastre = celda_rect(0, 0).center
        _, caps, lineas = self.juego.detalle_preview()
        self.assertNotIn((0, 1), caps)
        self.assertIn("Muro: bloquea F1 C2", lineas)

    def test_movimiento_reducido_conserva_captura_sin_flash(self):
        opciones.fijar("movimiento_reducido", True)
        opciones.invalidar()
        self.assertTrue(opciones.obtener("movimiento_reducido"))
        self.juego.board[0][1] = Carta("Debil", 1, 1, 1, 1, CPU, "orco")
        carta = self.juego.mano_u[0]
        caps = self.juego.colocar(carta, self.juego.mano_u, USUARIO, 0, 0)
        self.assertIn((0, 1), caps)
        self.assertEqual(self.juego.flash, [])
        self.assertEqual(self.juego.particulas, [])
        self.assertEqual(self.juego.sacudida, 0)


if __name__ == "__main__":
    unittest.main()
