"""Regresiones notificadas durante la prueba manual de la candidata."""
import asyncio
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import campana
import cinematicas
import main
import pantallas
import prologo
import ui
from partida import Juego
from reglas import USUARIO, CPU


class Reloj:
    def tick(self, fps=60):
        return 16


class TestRevisionJugador(unittest.TestCase):
    def setUp(self):
        datos = tempfile.TemporaryDirectory(prefix="tt_revision_")
        self.addCleanup(datos.cleanup)
        env = patch.dict(os.environ, {"TRIPLETRIAD_DATA": datos.name})
        env.start()
        self.addCleanup(env.stop)
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 800))
        self.addCleanup(ui.fijar_escala_texto, 1)

    def test_nueva_campana_abre_editor_vacio_aunque_haya_mazo(self):
        campana.asegurar_coleccion("humano")
        campana.asegurar_mazo_global()
        self.assertTrue(campana.mazo_global())
        textos = []
        original = pantallas.texto
        def registrar(screen, cadena, *args, **kwargs):
            textos.append(str(cadena))
            return original(screen, cadena, *args, **kwargs)
        with patch.object(main, "_prologo", AsyncMock(return_value=True)), \
             patch.object(pantallas, "pedir_nombre", AsyncMock(return_value=None)), \
             patch.object(pantallas, "elegir_faccion", AsyncMock(return_value="humano")), \
             patch.object(pantallas, "texto", side_effect=registrar), \
             patch("pygame.event.get", return_value=[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]):
            asyncio.run(main._nueva_campana(self.screen, Reloj()))
        self.assertTrue(any(t.startswith("MAZO 0/10") for t in textos), textos)

    def test_prologo_cambia_color_al_cambiar_propietario(self):
        juego = Juego("humano", bando_rival="humano",
                      mano_u_inicial=prologo.mazo_tutorial(),
                      mano_c_inicial=prologo.mazo_rival_rajoy(),
                      info=prologo.info_duelo_prologo())
        carta = juego.mano_u[0]
        carta.dueno = USUARIO
        propia = juego.super_cartas(carta).get_at((5, 60))
        carta.dueno = CPU
        rival = juego.super_cartas(carta).get_at((5, 60))
        self.assertNotEqual(propia, rival)
        self.assertNotEqual(juego._color_dueno(USUARIO), juego._color_dueno(CPU))

    def test_cada_hablante_conocido_recupera_su_avatar(self):
        escenas = [cinematicas.esc("Hola", hablante=n)
                   for n in ("Nara", "__JUGADOR__", "Juan Rajoy", "Pik")]
        cine = cinematicas.Cinematica(escenas, nombre_jugador="Ana")
        self.assertEqual([e.retrato for e in cine.escenas],
                         ["nara", "duelista", "rajoy", "pik"])
        self.assertEqual(cine.escenas[1].hablante, "Ana")


if __name__ == "__main__":
    unittest.main()
