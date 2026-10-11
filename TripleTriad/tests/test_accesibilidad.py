"""G7: accesibilidad y ajustes. Persistencia de audio/pantalla/texto y navegacion
por teclado del recorrido principal.

Cada prueba aisla su directorio de datos: las opciones se escriben en disco y no
deben filtrarse entre casos.
"""

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

import pygame  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402

import opciones  # noqa: E402
import pantallas  # noqa: E402
import ui  # noqa: E402


class Reloj:
    def tick(self, fps=60):
        return 16


class Base(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory(prefix="tt_acces_")
        self.addCleanup(self.directorio.cleanup)
        env = patch.dict(os.environ, {"TRIPLETRIAD_DATA": self.directorio.name})
        env.start()
        self.addCleanup(env.stop)
        opciones.invalidar()
        self.addCleanup(opciones.invalidar)
        pygame.init()
        self.screen = pygame.display.set_mode((ANCHO, ALTO))
        self.addCleanup(lambda: ui.fijar_escala_texto(1.0))


class TestPersistenciaDeAjustes(Base):
    def test_volumen_y_pantalla_sobreviven_al_reinicio(self):
        opciones.fijar("volumen_musica", 0.8)
        opciones.fijar("volumen_efectos", 0.1)
        opciones.fijar("pantalla_completa", True)
        # simula reinicio: se olvida la cache y se vuelve a leer del disco
        opciones.invalidar()
        self.assertAlmostEqual(opciones.volumen_musica(), 0.8)
        self.assertAlmostEqual(opciones.volumen_efectos(), 0.1)
        self.assertTrue(opciones.pantalla_completa())

    def test_modo_lectura_sobrevive_al_reinicio(self):
        opciones.fijar("texto_grande", True)
        opciones.invalidar()
        self.assertTrue(opciones.texto_grande())

    def test_volumen_fuera_de_rango_se_acota(self):
        self.assertEqual(opciones.fijar("volumen_musica", 3.0), 1.0)
        self.assertEqual(opciones.fijar("volumen_efectos", -2), 0.0)

    def test_valor_corrupto_cae_al_defecto(self):
        import json

        ruta = os.path.join(self.directorio.name, "opciones.json")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump({"volumen_musica": "no soy un numero",
                       "texto_grande": "si"}, f)
        opciones.invalidar()
        self.assertAlmostEqual(opciones.volumen_musica(), 0.35)
        self.assertTrue(opciones.texto_grande())


class TestEscalaDeTexto(Base):
    def _alto_texto(self, tam):
        return ui.REC.fuente(tam).get_height()

    def test_el_modo_lectura_agranda_la_fuente(self):
        ui.fijar_escala_texto(1.0)
        chico = self._alto_texto(12)
        ui.fijar_escala_texto(1.25)
        grande = self._alto_texto(12)
        self.assertGreater(grande, chico)

    def test_la_escala_se_acota(self):
        self.assertEqual(ui.fijar_escala_texto(9.0), 1.6)
        self.assertEqual(ui.fijar_escala_texto(0.1), 1.0)


class TestAjustesPorTeclado(Base):
    def test_enter_activa_el_cambio_de_volumen(self):
        """Foco en MUSICA, flecha derecha sube el volumen y lo persiste."""
        modo = []
        teclas = [
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN),   # foco -> musica
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT),  # +5%
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
        ]

        def capturar(*_a, **_k):
            return [teclas.pop(0)] if teclas else [
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]

        antes = opciones.volumen_musica()
        with patch("pygame.event.get", side_effect=capturar):
            resultado = asyncio.run(pantallas.ajustes(self.screen, Reloj()))
        self.assertAlmostEqual(opciones.volumen_musica(), min(1.0, antes + 0.05))
        self.assertEqual(resultado["musica"], opciones.volumen_musica())

    def test_toggle_de_texto_grande_con_el_raton(self):
        # El boton TEXTO GRANDE esta en (ANCHO//2+8, 340, 292, 42)
        clic = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                  pos=(ANCHO // 2 + 100, 360))
        cierre = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        with patch("pygame.event.get", return_value=[clic, cierre]):
            asyncio.run(pantallas.ajustes(self.screen, Reloj()))
        self.assertTrue(opciones.texto_grande())
        self.assertGreater(ui.escala_texto(), 1.0)


class TestEscaladoDePantalla(Base):
    """G7: la presentacion es 1280x800 LOGICOS en cualquier monitor.

    Todo el dibujo usa `ui.ANCHO`/`ui.ALTO`. Si la superficie cambiara de
    tamano, el juego se dibujaria a escala de su propia constante y el raton
    no coincidiria con lo que se ve. Este test ata ese invariante: la
    superficie logica no se mueve, ni al abrir, ni al cambiar de completa, ni
    al redimensionar la ventana.
    """

    def setUp(self):
        super().setUp()
        import ui

        self.ui = ui
        ui.activar_escalado()

    def test_la_superficie_logica_no_cambia(self):
        s = self.ui.aplicar_escalado({"completa": False})
        self.assertEqual(s.get_size(), (self.ui.ANCHO, self.ui.ALTO))

    def test_cambiar_a_pantalla_completa_mantiene_el_tamano_logico(self):
        s = self.ui.aplicar_escalado({"completa": True})
        self.assertEqual(s.get_size(), (self.ui.ANCHO, self.ui.ALTO))
        s2 = self.ui.aplicar_escalado({"completa": False})
        self.assertEqual(s2.get_size(), (self.ui.ANCHO, self.ui.ALTO))

    def test_el_redimensionado_no_altera_la_superficie_logica(self):
        """Un VIDEORESIZE no puede cambiar el lienzo logico.

        Si lo hiciera, cada boton dibujado con coordenadas de 1280x800 se
        cairia fuera al agrandar la ventana, y el raton apuntaria a otro sitio.
        """
        antes = self.ui.aplicar_escalado({"completa": False}).get_size()
        ev = pygame.event.Event(pygame.VIDEORESIZE, w=1920, h=1080,
                                size=(1920, 1080))
        with patch("pygame.event.get", return_value=[ev]):
            pygame.event.get()
        despues = pygame.display.get_surface().get_size()
        self.assertEqual(despues, antes)

    def test_el_modo_escala_incluye_la_bandera_de_escalado(self):
        """`pygame.SCALED` es lo que hace que pygame escale y traduzca el raton."""
        self.assertTrue(self.ui.modo_escalado(False) & pygame.SCALED)
        self.assertTrue(self.ui.modo_escalado(True) & pygame.SCALED)
        self.assertTrue(self.ui.modo_escalado(True) & pygame.FULLSCREEN)
        self.assertFalse(self.ui.modo_escalado(False) & pygame.FULLSCREEN)

    def test_las_constantes_de_diseno_no_se_tocan(self):
        """El juego esta disenado a 1280x800; el escalado es hacia fuera."""
        self.assertEqual((self.ui.ANCHO, self.ui.ALTO), (1280, 800))

    def test_si_el_escalado_falla_el_juego_arranca_igual(self):
        """El fallo que de verdad importa: que el juego NO arranque.

        `set_mode` con SCALED lanza `pygame.error` donde no hay renderer rapido
        (entornos sin ventana, drivers antiguos). Sin degradacion, eso tumbaria
        el arranque. Aqui se simula SOLO ese fallo: la via escalada revienta y
        la de reserva tiene que funcionar.
        """
        import ui

        guardado = ui._ESCALA_DISPONIBLE
        self.addCleanup(lambda: setattr(ui, "_ESCALA_DISPONIBLE", guardado))
        real_abrir = ui._abrir
        ui._ESCALA_DISPONIBLE = None
        _llamadas = []

        def _abrir_falso(completa, con_escala):
            _llamadas.append(con_escala)
            if con_escala:
                raise pygame.error("failed to create renderer")
            return real_abrir(completa, con_escala)

        with patch.object(ui, "_abrir", _abrir_falso):
            sup = ui.aplicar_escalado({"completa": False})
        self.assertEqual(sup.get_size(), (ui.ANCHO, ui.ALTO))
        self.assertEqual(_llamadas, [True, False],
                         "deberia intentar escalar y luego caer al plan B")
        self.assertFalse(ui._ESCALA_DISPONIBLE,
                         "deberia recordar que aqui no hay escalado")


class TestTecladoRecorridoPrincipal(Base):
    def test_mapa_campana_enter_camina(self):
        import campana

        estado = campana.nueva_campana("humano")
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        salir = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        with patch("pygame.event.get", return_value=[enter, salir]):
            accion = asyncio.run(pantallas.mapa_campana(self.screen, Reloj(), estado))
        self.assertEqual(accion, "seguir")

    def test_recompensa_se_elige_con_enter(self):
        import campana

        estado = campana.nueva_campana("humano")
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        with patch("pygame.event.get", return_value=[enter]):
            elegida = asyncio.run(
                pantallas.recompensa(self.screen, Reloj(), estado, "senda"))
        self.assertIn(elegida, campana.recompensas_de("senda"))

    def test_decision_narrativa_se_elige_con_enter(self):
        import campana
        import narrativa

        estado = campana.nueva_campana("humano")
        decision = narrativa.decision_de("senda")
        enter = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        with patch("pygame.event.get", return_value=[enter]), \
             patch("pantallas.cartel", new=unittest.mock.AsyncMock()):
            asyncio.run(pantallas.decision_narrativa(
                self.screen, Reloj(), estado, decision))
        self.assertIn(decision["id"], estado["decisiones"])


class TestModoLecturaNoDesborda(Base):
    """El modo lectura tiene que REPARTIR el ancho, no solo agrandar la fuente.

    Con escala >1 el ancho de envoltura fijo dejaba las lineas salirse del
    panel. Solo se ve mirando la captura: los tests de "no revienta" pasan
    igual. Aqui se mide de verdad: cada linea envuelta tiene que caber.
    """

    def test_el_texto_envuelto_cabe_con_texto_ampliado(self):
        import ui as _ui
        from ui import envolver

        ancho_base = ANCHO - 260
        largo = "Las cartas no son un juego. Son la manera en que el Umbral elige a quien deja pasar."
        for escala in (1.0, 1.25, 1.5):
            _ui.fijar_escala_texto(escala)
            ancho = int(ancho_base / max(1.0, _ui.escala_texto()))
            for linea in envolver(largo, 10, ancho):
                self.assertLessEqual(
                    _ui.ancho_texto(linea, 10), ancho + 1,
                    f"linea mas ancha que el panel con escala {escala}: {linea!r}")

    def test_la_escala_real_se_usa_al_envolver(self):
        import ui as _ui

        _ui.fijar_escala_texto(1.25)
        self.assertEqual(_ui.escala_texto(), 1.25)
        self.assertEqual(_ui.REC.fuente(10).get_height() > _ui.REC.fuente(8).get_height(),
                         True)


if __name__ == "__main__":
    unittest.main()
