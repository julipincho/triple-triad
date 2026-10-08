"""Tests de las mini campanas: estructura, rivales, guardado y flujo.

    python -m unittest tests.test_mini -v
"""

import asyncio
import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests_mini")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import campana  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
from partida import Resultado  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


MINIS = ["elfo_nocturno", "hombre_pantera", "hombre_lagarto"]


def setUpModule():
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))


class RelojFalso:
    def tick(self, fps=60):
        return 16


class TestMiniEstructura(unittest.TestCase):
    def test_nueva_mini_es_corta_y_en_memoria(self):
        for f in MINIS:
            estado = campana.nueva_mini_campana(f)
            self.assertTrue(estado["mini"])
            self.assertEqual(estado["nodo"], "mini_senda")
            self.assertEqual(len(estado["cartas"]), 10)
            self.assertIn("semilla", estado)
            self.assertIsNone(estado["_archivo"])

    def test_rivales_mini_nunca_son_la_propia(self):
        for f in MINIS:
            estado = campana.nueva_mini_campana(f)
            vistos = set()
            for nodo_id in ("mini_senda", "mini_nudo", "mini_trono"):
                rival = campana.rival_de_nodo(estado, nodo_id)
                self.assertNotEqual(rival, f)
                self.assertIn(rival, facciones.FACCIONES)
                vistos.add(rival)
            self.assertEqual(campana.rival_de_nodo(estado, "mini_trono"),
                             facciones.rival_final(f))

    def test_sorteo_funciona_en_mini(self):
        estado = campana.nueva_mini_campana("hombre_pantera")
        self.assertEqual(len(campana.cartas_duelo(estado, "mini_senda")), 5)
        self.assertEqual(len(campana.mazo_rival(estado, "mini_senda")), 5)

    def test_la_mini_no_pisa_campana_json(self):
        ruta = campana.ruta_partida()
        if os.path.exists(ruta):
            os.remove(ruta)
        estado = campana.nueva_mini_campana("hombre_lagarto")
        campana.registrar_victoria(estado, 3)
        campana.mejorar_carta(estado, 0)
        self.assertFalse(os.path.exists(ruta),
                         "la mini escribio campana.json y piso la principal")

    def test_desbloqueo_y_final(self):
        perfil = campana.cargar_perfil()
        perfil["finales"] = {}
        perfil["mini_finales"] = {}
        campana.guardar_perfil(perfil)
        self.assertFalse(campana.mini_desbloqueada())
        campana.registrar_final_perfil("humano", "caos")
        self.assertTrue(campana.mini_desbloqueada())
        self.assertTrue(campana.registrar_mini_final("elfo_nocturno"))
        self.assertFalse(campana.registrar_mini_final("elfo_nocturno"))
        self.assertIn("elfo_nocturno", campana.mini_finales_desbloqueados())


class TestMiniFlujo(unittest.TestCase):
    def _simular(self, faccion, victorias=True):
        import main

        registro = {"duelos": 0, "final": None}
        originales = {}

        async def ara(*args, **kwargs):
            return None

        async def elegir(*args, **kwargs):
            return faccion

        async def mapa(*args, **kwargs):
            return "seguir"

        async def duelo(screen, clock, juego, test_mode=False, guia=None):
            registro["duelos"] += 1
            if registro["duelos"] > 6:
                raise AssertionError("bucle infinito en la mini")
            return Resultado(victorias, 2, 5, (5, 4), False, 1)

        async def recompensa(*args, **kwargs):
            return "entrenamiento"

        async def cartel(*args, **kwargs):
            return None

        reemplazos = {
            "pantallas.elegir_faccion": elegir,
            "pantallas.mapa_mini": mapa,
            "pantallas.recompensa": recompensa,
            "pantallas.aplicar_recompensa": ara,
            "pantallas.derrota": ara,
            "pantallas.cartel": cartel,
            "cinematicas.reproducir": ara,
            "main.partida": duelo,
        }
        for ruta, fn in reemplazos.items():
            modulo, nombre = ruta.split(".")
            originales[ruta] = getattr(sys.modules[modulo], nombre)
            setattr(sys.modules[modulo], nombre, fn)
        try:
            asyncio.run(main._mini_campana(pygame.display.get_surface(), RelojFalso()))
        finally:
            for ruta, fn in originales.items():
                modulo, nombre = ruta.split(".")
                setattr(sys.modules[modulo], nombre, fn)
        return registro

    def test_mini_completa_tres_duelos_y_final(self):
        # aplicar_recompensa real no corre (mock), pero el entrenamiento
        # necesita cartas: se simula con la pantalla mockeada arriba
        registro = self._simular("hombre_pantera")
        self.assertEqual(registro["duelos"], 3)
        self.assertIn("hombre_pantera", campana.mini_finales_desbloqueados())

    def test_mini_abandonada_no_registra_final(self):
        import main

        async def elegir(*args, **kwargs):
            return "hombre_lagarto"

        async def mapa(*args, **kwargs):
            return "salir"

        originales = {}
        for ruta, fn in (("pantallas.elegir_faccion", elegir),
                         ("pantallas.mapa_mini", mapa)):
            modulo, nombre = ruta.split(".")
            originales[ruta] = getattr(sys.modules[modulo], nombre)
            setattr(sys.modules[modulo], nombre, fn)
        try:
            asyncio.run(main._mini_campana(pygame.display.get_surface(), RelojFalso()))
        finally:
            for ruta, fn in originales.items():
                modulo, nombre = ruta.split(".")
                setattr(sys.modules[modulo], nombre, fn)
        self.assertNotIn("hombre_lagarto", campana.mini_finales_desbloqueados())


class TestMiniEnMenu(unittest.TestCase):
    def _menu_con(self, eventos):
        import pantallas

        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        original = pygame.event.get
        cola = list(eventos)

        def get():
            return [cola.pop(0)] if cola else []

        pygame.event.get = get
        try:
            return asyncio.run(pantallas.menu(pantalla, RelojFalso(), None))
        finally:
            pygame.event.get = original

    def _clic(self, x, y):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(x, y), button=1)

    def _tecla(self, key):
        return pygame.event.Event(pygame.KEYDOWN, key=key, unicode="")

    def test_bloqueada_no_responde_y_volver_si(self):
        perfil = campana.cargar_perfil()
        perfil["finales"] = {}
        campana.guardar_perfil(perfil)
        centro = (ANCHO // 2 - 340 + 150, 428 + 27)
        accion = self._menu_con([self._clic(*centro), self._tecla(pygame.K_ESCAPE)])
        self.assertEqual(accion, "salir")

    def test_desbloqueada_devuelve_mini(self):
        campana.registrar_final_perfil("orco", "dominio")
        centro = (ANCHO // 2 - 340 + 150, 428 + 27)
        accion = self._menu_con([self._clic(*centro)])
        self.assertEqual(accion, "mini")


if __name__ == "__main__":
    unittest.main()
