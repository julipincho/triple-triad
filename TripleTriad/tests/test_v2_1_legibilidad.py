"""Regresiones de presentación con capturas resueltas por el motor real."""
import os
import sys
import unittest
import asyncio
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pygame
import partida
import ui
from reglas import Carta, CPU, USUARIO


class TestLecturaDeJugada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1280, 800))

    def juego(self, habilidad=None):
        card = Carta('Ataque', 5, 1, 3, 1, bando='humano', habilidad=habilidad)
        return partida.Juego('humano', bando_rival='orco', mano_u_inicial=[card],
                             mano_c_inicial=[Carta('Reserva', 1, 1, 1, 1, bando='orco')])

    def test_cpu_no_pisa_el_cartel_same(self):
        game = self.juego()
        game.board[0][1] = Carta('Apoyo', 1, 5, 1, 1, dueno=USUARIO, bando='humano')
        game.board[1][2] = Carta('Rival', 1, 1, 1, 3, dueno=CPU, bando='orco')
        game.seleccionada = game.mano_u[0]
        with patch('partida.time.time', return_value=100.0):
            self.assertTrue(game.confirmar_jugada((1, 1)))
        self.assertEqual(game.efecto[0], 'SAME')
        self.assertEqual(game.board[1][2].dueno, USUARIO)
        with patch.object(game, '_jugar_cpu') as play:
            with patch('partida.time.time', return_value=101.0):
                game.actualizar(1.0)
            play.assert_not_called()
            with patch('partida.time.time', return_value=102.1):
                game.actualizar(1.1)
            play.assert_called_once()

    def test_colocacion_normal_conserva_el_ritmo(self):
        game = self.juego()
        game.seleccionada = game.mano_u[0]
        with patch('partida.time.time', return_value=100.0):
            game.confirmar_jugada((1, 1))
        self.assertIsNone(game.efecto)
        self.assertEqual(game.cpu_en_cola, 0.85)

    def test_quema_se_anuncia_sin_inventar_cadena(self):
        game = self.juego('quema')
        game.board[1][2] = Carta('Rival', 1, 1, 1, 3, dueno=CPU, bando='orco')
        game.board[0][2] = Carta('Otro', 1, 1, 1, 1, dueno=CPU, bando='orco')
        game.seleccionada = game.mano_u[0]
        with patch('partida.time.time', return_value=100.0), patch('audio.sfx') as sound:
            game.confirmar_jugada((1, 1))
        self.assertEqual(game.efecto[0], 'QUEMA')
        self.assertIn('1 por quema', game.efecto[3])
        self.assertIn('1 carta:', game.efecto[3])
        self.assertIn('captura al empatar', game.efecto[3])
        self.assertEqual(game.board[1][2].dueno, USUARIO)
        self.assertEqual(game.board[0][2].dueno, CPU)
        self.assertEqual(game.capturas, 1)
        self.assertTrue(any(call.kwargs.get('canal') == 'habilidad' for call in sound.call_args_list))

    def test_cartel_ampliado_separa_lineas_y_actualiza_cache(self):
        game = self.juego()
        original_scale = ui.escala_texto()
        previous = None
        try:
            for scale in (1.0, 1.25, 1.6):
                ui.fijar_escala_texto(scale)
                rects = []
                def draw(surface, text, size, *args, **kwargs):
                    image = ui.texto(surface, text, size, *args, **kwargs)
                    rect = pygame.Rect(0, 0, ui.ancho_texto(text, size), ui.alto_texto(text, size))
                    rect.center = kwargs['centro']
                    rects.append(rect)
                    return image
                with patch('partida.texto', side_effect=draw):
                    card = game._superficie_efecto('QUEMA',
                        'captura al empatar; no inicia cadena. 1 carta: 1 por quema', ui.DORADO)
                self.assertIsNot(card, previous)
                for rect in rects:
                    self.assertTrue(card.get_rect().contains(rect), (scale, rect))
                for above, below in zip(rects, rects[1:]):
                    self.assertGreaterEqual(below.top - above.bottom, 4, scale)
                previous = card
        finally:
            ui.fijar_escala_texto(original_scale)

    def test_pausa_e_historial_conservan_el_tiempo_del_efecto(self):
        for attribute in ('pausa', 'historial_abierto'):
            with self.subTest(estado=attribute):
                game = self.juego()
                game.efecto = ('SAME', 100.0, ui.DORADO, 'Una captura', 'same')
                setattr(game, attribute, True)
                game.sincronizar_presentacion(100.5)
                with patch('partida.time.time', return_value=120.0):
                    game.dibujar(pygame.display.get_surface())
                self.assertIsNotNone(game.efecto)
                setattr(game, attribute, False)
                game.sincronizar_presentacion(120.0)
                self.assertEqual(game.efecto[1], 119.5)

    def test_resultado_espera_al_efecto_de_la_ultima_jugada(self):
        game = self.juego()
        game.board = [[Carta('Espadachin', 1, 1, 1, 1, dueno=USUARIO,
                             bando='humano') for _ in range(3)] for _ in range(3)]
        game.efecto = ('SAME', 100.0, ui.DORADO, 'Una captura', 'same')
        with patch('partida.time.time', return_value=100.0):
            game.comprobar_fin()
        self.assertEqual(game.tiempo_fin, 102.0)
        with patch.object(game, '_dibujar_resultado') as result:
            with patch('partida.time.time', return_value=100.5):
                game.dibujar(pygame.display.get_surface())
            result.assert_not_called()
            with patch('partida.time.time', return_value=102.1):
                game.dibujar(pygame.display.get_surface())
            result.assert_called_once()
        self.assertFalse(partida.now_clickable(102.5, game.tiempo_fin))
        self.assertTrue(partida.now_clickable(102.7, game.tiempo_fin))

    def test_tooltip_no_tapa_efecto_o_resultado(self):
        game = self.juego()
        game.board[1][1] = Carta('Espadachin', 1, 1, 1, 1, dueno=USUARIO, bando='humano')
        for state in ('efecto', 'fin'):
            game.efecto = ('SAME', 100.0, ui.DORADO, 'Una captura', 'same') if state == 'efecto' else None
            game.fin = state == 'fin'
            with patch('partida.time.time', return_value=100.5), \
                 patch('pygame.mouse.get_pos', return_value=ui.celda_rect(1, 1).center), \
                 patch('partida.tooltip') as tip:
                game.dibujar(pygame.display.get_surface())
            tip.assert_not_called()

    def test_tecla_l_no_abre_historial_durante_pausa(self):
        game = self.juego()
        events = [[pygame.event.Event(pygame.KEYDOWN, key=key)]
                  for key in (pygame.K_ESCAPE, pygame.K_l, pygame.K_RETURN)] + [[]] * 45
        class Clock:
            def tick(self, fps):
                return 16
        with patch('pygame.event.get', side_effect=events), patch.object(game, 'dibujar'), \
             patch('pygame.display.flip'):
            asyncio.run(partida.partida(pygame.display.get_surface(), Clock(), game, test_mode=True))
        self.assertFalse(game.pausa)
        self.assertFalse(game.historial_abierto)

    def test_resultado_estatico_se_reutiliza_y_historial_lo_invalida(self):
        game = self.juego()
        game.fin = True
        game.tiempo_fin = 100.0
        game.t_entrada = 90.0
        screen = pygame.display.get_surface()
        with patch('partida.time.time', return_value=103.0), \
             patch.object(game, '_dibujar_resultado', wraps=game._dibujar_resultado) as draw:
            game.dibujar(screen)
            self.assertIsNotNone(game._resultado_frame)
            game.dibujar(screen)
            self.assertEqual(draw.call_count, 1)
            game.historial_abierto = True
            game.dibujar(screen)
            self.assertIsNone(game._resultado_frame)
            game.historial_abierto = False
            game.dibujar(screen)
            self.assertEqual(draw.call_count, 2)

    def test_animaciones_terminan_despues_del_ultimo_movimiento(self):
        game = self.juego()
        game.fin = True
        game.sacudida = 0.3
        game.particulas = [dict(x=0, y=0, vx=1, vy=1, t=0, vida=0.2)]
        game.actualizar(1.0)
        self.assertEqual(game.sacudida, 0)
        self.assertEqual(game.particulas, [])


if __name__ == '__main__':
    unittest.main()
