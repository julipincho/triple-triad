"""Tests G1: coleccion bloqueada, moneda y migracion con reset total.

    python -m unittest tests.test_coleccion -v
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests_coleccion")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import campana  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
from reglas import total_carta  # noqa: E402

import pygame  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


def setUpModule():
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))


class TestMazoInicial(unittest.TestCase):
    def test_diez_menores_por_faccion(self):
        for f in facciones.orden_facciones():
            iniciales = campana.mazo_inicial(f)
            self.assertEqual(len(iniciales), 10, f)
            esperados = sorted(mazos.TODOS[f], key=total_carta)[:10]
            self.assertEqual([c.nombre for c in iniciales],
                             [c.nombre for c in esperados])

    def test_dragon_no_llega_a_diez_comunes(self):
        # documenta la excepcion: 9 comunes + la rara mas barata
        from reglas import rareza

        iniciales = campana.mazo_inicial("dragon")
        comunes = [c for c in iniciales if rareza(c)[0] == "COMUN"]
        self.assertEqual(len(comunes), 9)
        self.assertEqual(len(iniciales), 10)


class TestColeccionPerfil(unittest.TestCase):
    def setUp(self):
        # aislamiento: el directorio temporal se comparte con otros tests
        # (test_flujo otorga iniciales de las 10 facciones al simular)
        perfil = campana.cargar_perfil()
        perfil["coleccion"] = {}
        perfil["moneda"] = 0
        campana.guardar_perfil(perfil)

    def test_defecto_y_posee(self):
        perfil = campana.perfil_por_defecto()
        self.assertEqual(perfil["coleccion"], {})
        self.assertEqual(perfil["moneda"], 0)
        self.assertFalse(campana.posee(perfil, "Espadachin"))

    def test_asegurar_es_idempotente(self):
        campana.asegurar_coleccion("orco")
        primera = dict(campana.coleccion_de())
        campana.asegurar_coleccion("orco")
        self.assertEqual(campana.coleccion_de(), primera)
        self.assertEqual(len(primera), 10)
        self.assertTrue(campana.posee(campana.cargar_perfil(), "Muerdehuesos"))

    def test_moneda_exacta(self):
        perfil = campana.cargar_perfil()
        perfil["moneda"] = 0
        campana.guardar_perfil(perfil)
        self.assertEqual(campana.ganar_moneda(25), 25)
        self.assertTrue(campana.gastar_moneda(20))
        self.assertEqual(campana.moneda(), 5)
        self.assertFalse(campana.gastar_moneda(6))
        self.assertEqual(campana.moneda(), 5)

    def test_premio_duelo(self):
        perfil = campana.cargar_perfil()
        perfil["moneda"] = 0
        campana.guardar_perfil(perfil)
        estado = campana.nueva_campana("humano")
        # victoria + 3 capturas: 5 + 20 + 3*2 = 31
        self.assertEqual(campana.premio_duelo(estado, True, 3), 31)
        self.assertEqual(campana.moneda(), 31)
        # derrota sin capturas: 5
        self.assertEqual(campana.premio_duelo(estado, False, 0), 5)
        self.assertEqual(campana.moneda(), 36)


class TestMigracionReset(unittest.TestCase):
    def test_v4_conserva_nodo_y_resetea_cartas(self):
        viejo = {
            "version": 4,
            "faccion": "elfo",
            "nodo": "fortaleza",
            "ruta": ["senda"],
            "cartas": [c.a_dict() for c in mazos.TODOS["elfo"]],
            "victorias": 2,
            "semilla": 12345,
        }
        nuevo = campana._migrar(viejo)
        self.assertEqual(nuevo["version"], campana.VERSION)
        self.assertEqual(nuevo["nodo"], "fortaleza")
        self.assertEqual(nuevo["ruta"], ["senda"])
        self.assertEqual(nuevo["victorias"], 2)
        self.assertEqual(nuevo["semilla"], 12345)
        self.assertEqual([d["nombre"] for d in nuevo["cartas"]],
                         [c.nombre for c in campana.mazo_inicial("elfo")])

    def test_nueva_campana_empieza_con_iniciales(self):
        estado = campana.nueva_campana("vampiro")
        self.assertEqual(len(estado["cartas"]), 10)
        self.assertEqual(estado["version"], campana.VERSION)

    def test_migra_v5_resetea_y_limpia_mejoras(self):
        viejo = {
            "version": 5,
            "faccion": "orco",
            "nodo": "asalto",
            "ruta": ["senda", "aldea"],
            "cartas": [dict(c.a_dict(), n=10) for c in campana.mazo_inicial("orco")],
            "mejoras": {"Muerdehuesos": {"n": 3}},
            "victorias": 2,
            "semilla": 999,
        }
        nuevo = campana._migrar(viejo)
        self.assertEqual(nuevo["version"], campana.VERSION)
        self.assertEqual(nuevo["nodo"], "asalto")
        self.assertEqual(nuevo["mejoras"], {})
        self.assertEqual([d["nombre"] for d in nuevo["cartas"]],
                         [c.nombre for c in campana.mazo_inicial("orco")])
        self.assertTrue(all(d["n"] < 10 for d in nuevo["cartas"]))

    def test_completar_limpia_mejoras(self):
        estado = campana.nueva_campana("goblin")
        campana.registrar_mejora(estado, estado["cartas"][0]["nombre"], "n", 2)
        self.assertTrue(campana.mejoras_de(estado))
        campana.completar(estado)
        self.assertEqual(campana.mejoras_de(estado), {})

    def test_deltas_con_tope_en_duelo(self):
        estado = campana.nueva_campana("elfo")
        nombre = estado["cartas"][0]["nombre"]
        estado["cartas"][0]["n"] = 9
        campana.registrar_mejora(estado, nombre, "n", 5)
        mano = campana.cartas_duelo(estado, "senda")
        self.assertTrue(mano)
        for c in mano:
            for lado in ("N", "S", "E", "O"):
                self.assertLessEqual(c.valores[lado], 10)

    def test_validar_mazo(self):
        from reglas import Carta, rareza

        def rar(nombre, colleccion):
            return rareza(Carta.desde_dict(colleccion[nombre]))[0]

        colleccion = {c.nombre: c.a_dict() for c in campana.mazo_inicial("humano")}
        base = [dict(colleccion[n]) for n in colleccion]
        ok, motivo = campana.validar_mazo(base, set(colleccion))
        self.assertTrue(ok, motivo)
        # 4 cartas no vale (minimo 5)
        ok, motivo = campana.validar_mazo(base[:4], set(colleccion))
        self.assertFalse(ok)
        self.assertIn("5", motivo)
        # 11 cartas no vale (maximo 10)
        ok, motivo = campana.validar_mazo(base + [dict(base[0])], set(colleccion))
        self.assertFalse(ok)
        self.assertIn("10", motivo)
        # carta no poseida no vale
        otra = dict(base[0])
        otra["nombre"] = "Fantasma"
        ok, motivo = campana.validar_mazo(base[:9] + [otra], set(colleccion))
        self.assertFalse(ok)
        self.assertIn("no es tuya", motivo)
        # 2 legendarias no valen (Rey Aldric + Reina Isolde)
        legs = [c.a_dict() for c in mazos.HUMANOS
                if rareza(c)[0] == "LEGENDARIA"][:2]
        self.assertEqual(len(legs), 2)
        for r in legs:
            colleccion[r["nombre"]] = r
        mazo = [dict(colleccion[n]) for n in list(colleccion)[:8]]
        mazo += [dict(r) for r in legs]
        self.assertEqual(len(mazo), 10)
        ok, motivo = campana.validar_mazo(mazo, set(colleccion))
        self.assertFalse(ok)
        self.assertIn("legendaria", motivo)

    def test_validar_mazo_cuatro_raras(self):
        from reglas import Carta, rareza

        base = {c.nombre: c.a_dict() for c in campana.mazo_inicial("orco")}
        raras = [c.a_dict() for c in mazos.TODOS["orco"]
                 if rareza(c)[0] == "RARA"][:4]
        self.assertEqual(len(raras), 4)
        colleccion = dict(base)
        for r in raras:
            colleccion[r["nombre"]] = r
        mazo = [dict(colleccion[n]) for n in list(colleccion)[:6]]
        mazo += [dict(r) for r in raras]
        self.assertEqual(len(mazo), 10)
        ok, motivo = campana.validar_mazo(mazo, set(colleccion))
        self.assertFalse(ok)
        self.assertIn("raras", motivo)


class TestArmarMazo(unittest.TestCase):
    def setUp(self):
        perfil = campana.cargar_perfil()
        perfil["coleccion"] = {}
        perfil["moneda"] = 0
        perfil["mazo"] = []
        campana.guardar_perfil(perfil)

    def _fijar_mazo(self, faccion):
        campana.asegurar_coleccion(faccion)
        starters = [c.nombre for c in campana.mazo_inicial(faccion)]
        campana.guardar_mazo_global(starters)
        return starters
    def _correr(self, faccion, eventos):
        import asyncio

        import pantallas
        import pygame
        from ui import ALTO, ANCHO

        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        original = pygame.event.get
        cola = list(eventos)
        estado = {"n": 0}

        def get():
            estado["n"] += 1
            if cola:
                return [cola.pop(0)]
            if estado["n"] > 400:
                raise AssertionError("el editor no devuelve")
            return []

        pygame.event.get = get
        try:
            return asyncio.run(pantallas.armar_mazo(
                pantalla, TestReloj(), faccion))
        finally:
            pygame.event.get = original

    def _clic(self, x, y):
        import pygame

        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(x, y), button=1)

    def test_guardar_preseleccionados(self):
        starters = self._fijar_mazo("goblin")
        mazo = self._correr("goblin", [self._clic(455, 717)])
        self.assertEqual(len(mazo), 10)
        self.assertEqual(campana.mazo_global(), starters)

    def test_quitar_y_volver_a_poner(self):
        self._fijar_mazo("elfo")
        mazo = self._correr(
            "elfo",
            [self._clic(76, 250), self._clic(76, 250), self._clic(455, 717)])
        self.assertEqual(len(mazo), 10)

    def test_mazo_corto_no_guarda(self):
        import pygame

        self._fijar_mazo("humano")
        clics = [self._clic(76 + i * 120, 250) for i in range(6)]
        mazo = self._correr(
            "humano",
            clics + [self._clic(455, 717),
                     pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
        self.assertIsNone(mazo)

    def test_volver_cancela(self):
        import pygame

        self._fijar_mazo("humano")
        mazo = self._correr(
            "humano",
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)])
        self.assertIsNone(mazo)


class TestReloj:
    def tick(self, fps=60):
        return 16


if __name__ == "__main__":
    unittest.main()
