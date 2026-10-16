import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import patch
import pygame
import cartas
import mazos
import prologo
import cinematicas
import campana


class TestRevisionVisual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 800))

    def test_nombre_externo_solo_hover(self):
        carta = mazos.TODOS['humano'][0]
        rect = pygame.Rect(100, 100, 104, 144)
        with patch('pygame.mouse.get_pos', return_value=(0, 0)), patch('ui.tooltip') as tip:
            cartas.nombre_al_pasar(self.screen, carta, rect)
            tip.assert_not_called()
        with patch('pygame.mouse.get_pos', return_value=rect.center), patch('ui.tooltip') as tip:
            cartas.nombre_al_pasar(self.screen, carta, rect)
            self.assertEqual(tip.call_args.args[1], carta.nombre)

    def test_nombre_no_esta_pintado_en_carta(self):
        carta = mazos.TODOS['humano'][0]
        cartas._cache.clear()
        original = cartas._texto_ajustado
        with patch.object(cartas, '_texto_ajustado', wraps=original) as texto:
            imagen = cartas.crear(carta)
            self.assertEqual(imagen.get_size(), (104, 144))
            self.assertNotIn(carta.nombre, [c.args[0] for c in texto.call_args_list])

    def test_dialogos_del_trono_no_vuelven_al_fondo_viejo(self):
        info = campana.info_duelo({'faccion': 'humano'}, 'trono')
        for escenas in (cinematicas.escenas_nodo(info)[0],
                        cinematicas.escenas_posterior(info, True),
                        cinematicas.escenas_posterior(info, False)):
            self.assertTrue(all(e.get('fondo_hd') == 'sala_trono.png'
                                for e in escenas if e['fondo'] == 'trono'))

    def test_planos_del_prologo_reutilizan_hd_por_escenario(self):
        cases = (
            ([e for e in prologo.escenas_pre_duelo() if e['fondo'] == 'publico'],
             'salon_torneo_lleno.png'),
            (prologo.escenas_encuentro_hostil(), 'camino_lluvioso.png'),
            ([e for e in prologo.escenas_cierre() if e['fondo'] in ('umbral', 'campamento')],
             'prologo_campamento_nara.png'),
            ([e for e in prologo.escenas_cierre() if e['fondo'] == 'trono'],
             'sala_trono.png'),
        )
        for scenes, expected in cases:
            with self.subTest(fondo_hd=expected):
                self.assertTrue(scenes, 'La comprobacion no puede aceptar una secuencia vacia')
                self.assertTrue(all(e['fondo_hd'] == expected for e in scenes))
