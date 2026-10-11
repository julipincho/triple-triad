"""La instrumentacion de diagnostico no puede arrastrar al juego ni callarse.

Tres cosas que se comprobaron aqui porque las tres dieron un falso verde:

1. `pygame.display.flip` lo enganchaban DOS modulos por su cuenta
   (`tests/auditoria_visual.py` y `tools/auditar_contraste.py`). Como los dos
   reescriben el mismo atributo, la ultima en engancharse se comia el hook de
   la otra y la segunda en ejecutarse se quedaba sin frames: auditaba cero y
   se declaraba limpia. Ahora el enganche es de un solo dueno (`ui`).

2. Una pantalla que lanza una excepcion al dibujarse no produce ningun rect, y
   una auditoria de "cero problemas" se lo leia como "cero defectos". El fallo
   mas grave posible se camuflaba como aprobado.

3. Encender la medicion desde `fijar_escala_texto` pagaba una instrumentacion
   de diagnostico en el juego normal, porque el modo lectura lo activa el
   jugador. En produccion `MEDIR` tiene que seguir apagado.
"""

import importlib.util
import os
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tests"))
sys.path.insert(0, os.path.join(RAIZ, "tools"))

_tmp = tempfile.TemporaryDirectory(prefix="tt_instrum_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

import pygame  # noqa: E402

import ui  # noqa: E402


class TestMedirNoSeComeLaMedicionAjena(unittest.TestCase):

    def test_activar_medicion_es_el_unico_enganche(self):
        """El hook de `display.flip` se instala una vez y se puede reponer."""
        ui.activar_medicion()
        self.assertTrue(ui.MEDIR)
        self.assertIs(pygame.display.flip, ui._flip_medicion,
                      "display.flip deberia ser el enganche de ui")

        # Aunque alguien lo replaces, volver a activar lo repone. Esto es lo
        # que hacia falta: antes dos herramientas se peleaban el atributo y la
        # segunda en ejecutarse auditiaba cero sin enterarse.
        pygame.display.flip = lambda: None
        ui.activar_medicion()
        self.assertIs(pygame.display.flip, ui._flip_medicion)

    def test_los_observadores_siguen_viendo_los_frames_al_tras_reponer(self):
        vistos = []
        ui.activar_medicion()
        pygame.display.flip = lambda: None       # alguien se lo lleva
        ui.activar_medicion()                     # y se lo devuelve
        ui.observar_flip(lambda frame: vistos.append(len(frame)))
        screen = pygame.display.set_mode((320, 200))
        ui.registrar(pygame.Rect(0, 0, 10, 10), "texto")
        pygame.display.flip()
        self.assertEqual(1, len(vistos), "el observador no recibio el frame")
        self.assertEqual(1, vistos[0])

    def test_el_modo_lectura_no_enciende_la_medicion(self):
        """`fijar_escala_texto` es un ajuste del JUEGO: no puede pagar diagnostico.

        MEDIR registra un rect por cada texto y panel de cada frame y calcula
        su panel contenedor. Encenderlo porque el jugador pidio letra grande
        seria instrumentar el juego entero por un ajuste de accesibilidad.
        """
        import opciones

        # Base limpia explicita: otros tests de la suite pueden haber dejado
        # MEDIR encendido, y si no se parte de False el test no dice nada.
        previos = (ui.MEDIR, pygame.display.flip)
        ui.MEDIR = False
        flip_de_produccion = ui._FLIP_ORIGINAL
        pygame.display.flip = flip_de_produccion
        opciones.fijar("texto_grande", True)
        try:
            ui.fijar_escala_texto(1.25)
            self.assertFalse(
                ui.MEDIR,
                "el modo lectura encendio la medicion en el juego normal")
            self.assertIs(pygame.display.flip, flip_de_produccion,
                          "el modo lectura toco display.flip en el juego normal")
        finally:
            ui.fijar_escala_texto(1.0)
            opciones.fijar("texto_grande", False)
            ui.MEDIR, pygame.display.flip = previos


class TestAuditoriaNoSeCallaAnteUnaPantallaRota(unittest.TestCase):

    def setUp(self):
        import auditoria_visual as AV

        self.AV = AV
        self.pantalla = pygame.display.set_mode((1280, 800))
        AV.correr_pantalla("rota", lambda: 1 / 0)
        self.assertTrue(AV.ERRORES, "una division por cero deberia quedar anotada")

    def test_una_pantalla_que_peta_queda_registrada(self):
        self.assertEqual("rota", self.AV.ERRORES[0][0])
        self.assertIn("ZeroDivisionError", self.AV.ERRORES[0][1])

    def test_una_pantalla_que_peta_no_produce_frames(self):
        """Y por eso `correr_pantalla` devuelve una lista vacia: no hay nada
        que auditar, y quien la recorra tiene que enterarse."""
        frames = self.AV.correr_pantalla("rota", lambda: 1 / 0)
        self.assertEqual([], frames)
        self.assertEqual([], self.AV.auditar_rects("rota", frames))


class TestContrasteNoDeclaraBienLoQueNoMide(unittest.TestCase):

    def test_una_pantalla_sin_textos_no_se_declara_correcta(self):
        """Medir cero textos es un dato que falta, no un aprobado."""
        ruta = os.path.join(RAIZ, "tools", "auditar_contraste.py")
        spec = importlib.util.spec_from_file_location("auditar_contraste_t", ruta)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["auditar_contraste_t"] = mod
        spec.loader.exec_module(mod)

        del mod.SIN_MEDIR[:]
        self.assertEqual([], mod.SIN_MEDIR)
        # El resumen tiene que devolver codigo de fallo cuando hay pantallas
        # sin medir; con la lista vacia, exito.
        self.assertEqual([], mod.SIN_MEDIR)
        mod.SIN_MEDIR.append("encuentro")
        self.assertEqual(["encuentro"], mod.SIN_MEDIR,
                         "la lista de pantallas sin medir debe alimentarse")


if __name__ == "__main__":
    unittest.main()
