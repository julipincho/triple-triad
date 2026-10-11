"""La opcion "de la que elijas" tiene que preguntar de verdad.

`ENCUENTROS.mercader.pagar` anuncia "+1 a la carta que elijas". Si la pantalla
no abre el selector, el codigo cae a "la carta mas debil" (que es un valor por
defecto correcto) y el texto sigue mintiendo: el jugador creyo que eligio y no
eligio. Ese fallo no lo ve ningun otro test, porque `aplicar_encuentro` con
`idx=None` funciona.

Este test recorre la pantalla de encuentro de verdad, pulsa la opcion del
mercader y comprueba que se pide una carta antes de aplicar el efecto. No
copia la implementacion: observa lo que la pantalla LE PIDE al juego.
"""

import asyncio
import os
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tests"))

import pygame  # noqa: E402

import campana  # noqa: E402
import pantallas  # noqa: E402


class _RelojFalso:
    def tick(self, fps=60):
        return 16


def _nodo_del_mercader():
    """Nodo al que le toca el encuentro 'mercader'."""
    for nodo in ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono"):
        if campana.encuentro_para(nodo).get("id") == "mercader":
            return nodo
    return None


class TestEncuentroMercaderPideCarta(unittest.TestCase):

    def setUp(self):
        directorio = tempfile.TemporaryDirectory(prefix="tt_enc_flujo_")
        self.addCleanup(directorio.cleanup)
        env = patch.dict(os.environ, {"TRIPLETRIAD_DATA": directorio.name})
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(random.setstate, random.getstate())
        pygame.init()
        self.screen = pygame.display.set_mode((1280, 800))
        pygame.mouse.set_pos((0, 0))
        campana.guardar_perfil({})
        random.seed(11)
        self.estado = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        campana.guardar(self.estado)

    def _pulsar_opcion(self, efecto):
        """Abre el encuentro y pulsa la opcion con ese efecto.

        Devuelve (llamadas_al_selector, cartas_devueltas_por_el_selector).
        """

        nodo = _nodo_del_mercader()
        self.assertIsNotNone(nodo, "no se encuentra el nodo con el mercader")
        enc = campana.encuentro_para(nodo)
        opciones = enc["opciones"]
        i = next(k for k, o in enumerate(opciones) if o["efecto"] == efecto)
        # El foco se mueve con las flechas y se confirma con ENTER. No se
        # calculan coordenadas: hay DOS layouts de opciones (retrato a la
        # izquierda y fila horizontal) segun haya retrato del encuentro, y
        # acertar una pulsacion por coordenadas es fragile.
        teclas = ([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT,
                                      unicode="d")] * i
                  + [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN,
                                        unicode=chr(13))])
        llamadas = []
        original_selector = pantallas.elegir_carta_para_mejorar
        original_cartel = pantallas.cartel

        async def selector_falso(screen, clock, estado):
            llamadas.append("selector")
            return 0

        async def cartel_falso(screen, clock, titulo, mensaje):
            llamadas.append(f"cartel:{mensaje[:40]}")

        pantallas.elegir_carta_para_mejorar = selector_falso
        pantallas.cartel = cartel_falso
        # La cinematica previa se queda con el primer evento (el clic) y la
        # pantalla nunca lo ve. Este test va de la eleccion de opcion, no de la
        # escena, asi que la escena se aparta.
        original_cine = pantallas.cinematicas.reproducir

        async def cine_falso(*a, **k):
            return None

        pantallas.cinematicas.reproducir = cine_falso
        try:
            self._correr_con_teclas(teclas)
        finally:
            pantallas.elegir_carta_para_mejorar = original_selector
            pantallas.cartel = original_cartel
            pantallas.cinematicas.reproducir = original_cine
        return llamadas

    def _correr_con_teclas(self, teclas):
        """Corre `encuentro` inyectando una lista de teclas ya hechas.

        No se usa `auditoria_visual.correr_pantalla` porque sustituye
        `pygame.event.get` por lo suyo y se comia los eventos del test: con
        el arnés puesto el clic nunca llegaba y el test pasaba sin comprobar
        nada.
        """
        nodo = _nodo_del_mercader()
        pendientes = list(teclas)
        real_get = pygame.event.get

        def get_evt():
            if pendientes:
                return [pendientes.pop(0)]
            # Sin eventos: un QUIT sintetico hace que `Cinematica.ejecutar`
            # lance SystemExit y el test mide un cierre, no una pulsacion.
            return []

        async def correr():
            tarea = asyncio.ensure_future(
                pantallas.encuentro(self.screen, _RelojFalso(), self.estado, nodo))
            for _ in range(80):
                await asyncio.sleep(0)
                if tarea.done():
                    break
            if not tarea.done():
                tarea.cancel()
                try:
                    await tarea
                except asyncio.CancelledError:
                    pass
                self.fail("El encuentro no termino tras confirmar la opcion")
            await tarea  # Los errores del juego deben hacer fallar la prueba.

        pygame.event.get = get_evt
        try:
            asyncio.run(correr())
        finally:
            pygame.event.get = real_get

    def test_el_mercader_es_reachable(self):
        """Control previo: sin esto los de mas no probarian nada."""
        nodo = _nodo_del_mercader()
        self.assertIsNotNone(nodo, "el encuentro 'mercader' no aparece en ningun nodo")
        efectos = {o["efecto"] for o in campana.encuentro_para(nodo)["opciones"]}
        self.assertIn("mejorar", efectos)

    def test_elegir_la_opcion_del_mercador_abre_el_selector(self):
        """'+1 a la carta que elijas' tiene que abrir una pantalla de eleccion."""
        llamadas = self._pulsar_opcion("mejorar")
        self.assertIn("selector", llamadas,
                      f"la pantalla aplico el efecto sin preguntar nada: {llamadas}")
        self.assertTrue(llamadas[1].startswith("cartel:Su consejo:"), llamadas)

    def test_el_efecto_sin_selector_no_pregunta(self):
        """Sustituto: 'robo' no promete eleccion, asi que no abre nada.

        Sin este control, el test anterior pasaria igual si la pantalla
        abriera el selector para todas las opciones.
        """
        llamadas = self._pulsar_opcion("robo")
        self.assertNotIn("selector", llamadas,
                         "una opcion que no promete eleccion abrio el selector")
        self.assertTrue(any(c.startswith("cartel:") for c in llamadas),
                        f"la opcion no llego a mostrar su cartel: {llamadas}")

    def test_el_texto_de_la_opcion_no_usa_jargon(self):
        nodo = _nodo_del_mercader()
        for op in campana.encuentro_para(nodo)["opciones"]:
            for palabra in ("pool", "pity"):
                self.assertNotIn(palabra, op["texto"].lower(),
                                 f"jargon {palabra!r} en {op['texto']!r}")


if __name__ == "__main__":
    unittest.main()
