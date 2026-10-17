"""Los mazos prestados nunca conceden ni consumen cartas de la aventura."""
import asyncio
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import pygame
import campana
import main
import mazos
import mazos_rapidos
import pantallas
from partida import Resultado
from reglas import rareza, total_carta


class Clock:
    def tick(self, fps):
        return 16


class TestRapidosIndependientes(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(prefix='tt_rapidos_')
        self.addCleanup(folder.cleanup)
        env = patch.dict(os.environ, TRIPLETRIAD_DATA=folder.name)
        env.start()
        self.addCleanup(env.stop)
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 800))

    def rapido(self, jugador='elfo', rival='orco'):
        async def duel(screen, clock, game):
            self.assertEqual(game.bando, jugador)
            self.assertEqual(game.bando_cpu, rival)
            self.assertTrue(all(c.bando == jugador for c in game.mano_u))
            self.assertEqual(len(game.mano_u), 5)
            self.assertEqual(len(game.mano_c), 5)
            self.assertTrue({c.nombre for c in game.mano_u} <= set(mazos_rapidos.PREDEFINIDOS[jugador]))
            self.assertTrue({c.nombre for c in game.mano_c} <= set(mazos_rapidos.PREDEFINIDOS[rival]))
            return Resultado(True, 2, 9, (6, 3))
        with patch('pantallas.elegir_faccion', AsyncMock(side_effect=[jugador, rival])), \
             patch('main.partida', side_effect=duel), patch('pantallas.cartel', AsyncMock()), \
             patch('campana.asegurar_mazo_global', side_effect=AssertionError('No debe reparar ni crear cartas')), \
             patch('pantallas.armar_mazo', side_effect=AssertionError('El rápido no usa el editor global')):
            asyncio.run(main._duelo_rapido(self.screen, Clock()))

    def test_varios_rapidos_nuevos_dejan_coleccion_y_mazo_vacios(self):
        for faction in ('elfo', 'dragon', 'hombre_pantera'):
            self.rapido(faction)
        profile = campana.cargar_perfil()
        self.assertEqual(campana.coleccion_de(profile), {})
        self.assertEqual(campana.mazo_global(profile), [])
        self.assertEqual(profile['duelos'], 3)
        self.assertFalse(Path(campana.ruta_partida()).exists())

    def test_rapido_antes_de_campana_no_contamina_editor_ni_mazo_inicial(self):
        self.rapido('dragon')
        clicks = []
        for i in range(10):
            row, col = divmod(i, pantallas.COLECCION_COLUMNAS)
            pos = (pantallas.COLECCION_ORIGEN[0] + col*pantallas.COLECCION_PASO[0] + 52,
                   pantallas.COLECCION_ORIGEN[1] + row*pantallas.COLECCION_PASO[1] + 72)
            clicks.append([pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)])
        clicks.append([pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(640, 770), button=1)])
        with patch('pantallas.pedir_nombre', AsyncMock(return_value=None)), \
             patch('main._prologo', AsyncMock(return_value=Resultado(True, 0, 9, (5, 4)))), \
             patch('pantallas.elegir_faccion', AsyncMock(return_value='orco')), \
             patch('pygame.event.get', side_effect=clicks), patch('main._campana', AsyncMock()) as start:
            asyncio.run(main._nueva_campana(self.screen, Clock()))
        state = start.await_args.args[2]
        self.assertEqual(len(state['cartas']), 10)
        self.assertTrue(all(c['bando'] == 'orco' for c in state['cartas']))
        self.assertEqual(set(campana.coleccion_de()), set(campana.coleccion_inicial('orco')))
        self.assertEqual(len(campana.mazo_global()), 10)

    def test_campana_rapido_continuar_conserva_guardado_y_mejoras(self):
        state = campana.nueva_campana('humano')
        campana.asegurar_coleccion('humano')
        campana.guardar_mazo_global([c['nombre'] for c in state['cartas']])
        campana.registrar_mejora(state, state['cartas'][0]['nombre'], 'n')
        campana.guardar(state)
        saved = Path(campana.ruta_partida()).read_bytes()
        before = copy.deepcopy(campana.cargar_perfil())
        self.rapido('humano', 'humano')
        after = campana.cargar_perfil()
        for field in ('duelos', 'victorias'):
            before.pop(field, None)
            after.pop(field, None)
        self.assertEqual(before, after)
        self.assertEqual(Path(campana.ruta_partida()).read_bytes(), saved)
        self.assertEqual(campana.cargar()['cartas'], state['cartas'])

    def test_cancelar_cualquiera_de_las_selecciones_no_escribe_perfil(self):
        for choices in ([None], ['humano', None]):
            with patch('pantallas.elegir_faccion', AsyncMock(side_effect=choices)), \
                 patch('main.partida', AsyncMock()) as duel:
                asyncio.run(main._duelo_rapido(self.screen, Clock()))
                duel.assert_not_awaited()
                self.assertFalse(Path(campana.ruta_perfil()).exists())

    def test_presets_cubren_facciones_son_legales_y_entregan_copias(self):
        self.assertEqual(set(mazos_rapidos.PREDEFINIDOS), set(mazos.TODOS))
        for faction in mazos.TODOS:
            with self.subTest(faction=faction):
                deck = mazos_rapidos.mazo(faction)
                self.assertEqual(len({c.nombre for c in deck}), 10)
                self.assertEqual(sum(total_carta(c) for c in deck), 250)
                self.assertEqual(sum(rareza(c)[0] == 'LEGENDARIA' for c in deck), 1)
                self.assertLessEqual(sum(rareza(c)[0] == 'RARA' for c in deck), 3)
                original = deck[0].valores['N']
                deck[0].valores['N'] = 999
                self.assertEqual(mazos_rapidos.mazo(faction)[0].valores['N'], original)
