"""Regresiones de presentación con capturas resueltas por el motor real."""
import os
import sys
import unittest
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


if __name__ == '__main__':
    unittest.main()
