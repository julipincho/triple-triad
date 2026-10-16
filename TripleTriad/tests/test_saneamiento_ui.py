"""Regresiones de español, identidad del jugador y rutas de arte existentes."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
import asyncio
import copy
from unittest.mock import patch
import pygame
import ui
import cartas
import cinematicas
import pantallas
import campana
from idioma import espanol


class TestSaneamientoUI(unittest.TestCase):
    def test_unicode_y_signos_se_conservan(self):
        self.assertEqual(ui.limpio('Espan\u0303a: ¿qué año? ¡Sí!'), 'España: ¿qué año? ¡Sí!')

    def test_pregunta_heredada_y_dialogo(self):
        self.assertEqual(espanol('- Como te llaman?'), '- ¿Cómo te llaman?')
        self.assertEqual(espanol('- De donde sacas esas cartas?'), '- ¿De dónde sacas esas cartas?')
        self.assertEqual(espanol('No se que paso. Quien acompana al capitan?'),
                         'No sé qué paso. ¿Quién acompaña al capitán?')

    def test_nombre_del_jugador_no_se_reescribe(self):
        cine = cinematicas.Cinematica([{'texto': 'Hola, __JUGADOR__.', 'hablante': '__JUGADOR__'}],
                                      nombre_jugador='Campana')
        self.assertEqual(cine.escena().texto, 'Hola, Campana.')
        self.assertEqual(cine.escena().hablante, 'Campana')

    def test_seleccion_de_arte_recibe_el_guion_original(self):
        data = {'texto': 'Quien acompana al capitan?', 'fondo': 'camino'}
        with patch('lotes_visuales.fondo', return_value='aprobado.png') as fondo:
            scene = cinematicas.Escena(data)
        fondo.assert_called_once_with(data)
        self.assertEqual(data['texto'], 'Quien acompana al capitan?')
        self.assertEqual(scene.fondo_lote, 'aprobado.png')
        self.assertEqual(scene.texto, '¿Quién acompaña al capitán?')

    def test_rutas_historicas_con_acentos(self):
        self.assertEqual(cartas._slug('Puño del Cráter'), 'puno_del_crater')
        self.assertEqual(cartas._slug('Vigía del Muro'), 'vigia_del_muro')

    def test_mano_extensa_reserva_el_avatar(self):
        avatar = pygame.Rect(ui.ANCHO - 116, 652, 96, 96)
        for total in (5, 10, 24, 25):
            for index in range(total):
                self.assertFalse(ui.mano_rect(index, total).colliderect(avatar))

    def test_editor_exige_diez_cartas(self):
        cartas = [c.a_dict() for c in campana.mazo_inicial('humano')]
        poseidas = {c['nombre'] for c in cartas}
        for cantidad in (0, 5, 9):
            self.assertFalse(pantallas._validar_mazo_editor(cartas[:cantidad], poseidas)[0])
        self.assertTrue(pantallas._validar_mazo_editor(cartas, poseidas)[0])

    def test_vaciar_no_guarda_y_cancelar_conserva_ambos_mazos(self):
        pygame.init()
        screen = pygame.display.set_mode((1280, 800))
        cartas = [c.a_dict() for c in campana.mazo_inicial('humano')]
        perfil = {'coleccion': {c['nombre']: c for c in cartas}, 'mazo': [c['nombre'] for c in cartas]}
        class Reloj:
            def tick(self, fps=60):
                return 16
        def clic(pos):
            return [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)]
        for run in (False, True):
            estado = {'faccion': 'humano', 'cartas': copy.deepcopy(cartas), 'mejoras': {}}
            antes = copy.deepcopy(estado)
            eventos = [clic((465, 626) if run else (1100, 720)),
                       clic((635, 626) if run else (640, 770)),
                       [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]]
            with patch('campana.cargar_perfil', return_value=perfil), \
                 patch('campana.guardar_mazo_global') as guardar, \
                 patch('pygame.event.get', side_effect=eventos), \
                 patch('pantallas.texto', wraps=ui.texto) as dibujar:
                fn = pantallas._editar_mazo_run(screen, Reloj(), estado) if run else pantallas.armar_mazo(screen, Reloj(), 'humano')
                self.assertIsNone(asyncio.run(fn))
                guardar.assert_not_called()
                self.assertTrue(any('MAZO 0/10' in str(c.args[1]) for c in dibujar.call_args_list))
            self.assertEqual(estado, antes)
            self.assertEqual(perfil['mazo'], [c['nombre'] for c in cartas])


if __name__ == '__main__':
    unittest.main()
