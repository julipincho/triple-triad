"""Cobertura extra de teclado para elecciones."""

import asyncio
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame
from ui import ALTO, ANCHO

import campana
import pantallas
import opciones


class Reloj:
    def tick(self, fps=60): return 16


class TestNavExtra(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(prefix="tt_nav_")
        self.addCleanup(self.d.cleanup)
        env = patch.dict(os.environ, {"TRIPLETRIAD_DATA": self.d.name})
        env.start()
        self.addCleanup(env.stop)
        opciones.invalidar()
        pygame.init()
        self.screen = pygame.display.set_mode((ANCHO, ALTO))

    def test_encuentro_elige_con_enter(self):
        estado = campana.nueva_campana("humano")
        # "hermandad": la primera opcion (ENTER elige la enfocada, la 0) es
        # "celebrar", que mejora a las dos cartas mas debiles. Es un efecto
        # mecanico comprobable, sin dialogues anadidos.
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        with patch("pygame.event.get", return_value=[enter]), \
             patch("cinematicas.reproducir", new=unittest.mock.AsyncMock()), \
             patch("pantallas.cartel", new=unittest.mock.AsyncMock()):
            asyncio.run(pantallas.encuentro(
                self.screen, Reloj(), estado, "senda", enc_id="hermandad"))
        # "celebrar" dejo mejoras de campana en el mazo.
        self.assertTrue(campana.mejoras_de(estado))

    def test_draft_elige_con_enter(self):
        estado = campana.nueva_campana("humano")
        ofertas = campana.draft_aleatorio(estado, 2)
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        with patch("pygame.event.get", return_value=[enter]):
            elegida = asyncio.run(pantallas.draft(self.screen, Reloj(), estado, ofertas=ofertas))
        self.assertIn(elegida, ofertas)


if __name__ == "__main__":
    unittest.main()
