"""Tests de los sobres: pesos, nuevas, duplicadas y encuentros.

    python -m unittest tests.test_sobres -v
"""

import os
import sys
import tempfile
import unittest
from unittest import mock

import asyncio

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests_sobres")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import campana  # noqa: E402
import mazos  # noqa: E402
from reglas import Carta  # noqa: E402

import pygame  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


def setUpModule():
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))


class RelojFalso:
    def tick(self, fps=60):
        return 16


def total(estado):
    return sum(d[l] for d in estado["cartas"] for l in "nseo")


class TestSobres(unittest.TestCase):
    def test_pesos_del_sobre(self):
        self.assertEqual(campana.PESOS_SOBRE,
                         {"LEGENDARIA": 2, "RARA": 6, "COMUN": 12})

    def test_sobre_da_tres_distintas_del_pool(self):
        catalogo = {c.nombre for cartas in mazos.TODOS.values() for c in cartas}
        for _ in range(20):
            estado = campana.nueva_campana("orco")
            nuevas, mejoradas = campana.abrir_sobre(estado)
            sacadas = nuevas + mejoradas
            self.assertEqual(len(sacadas), 3)
            self.assertEqual(len(set(sacadas)), 3)
            self.assertTrue(set(sacadas) <= catalogo)

    def test_duplicada_mejora_la_base_no_el_mazo(self):
        estado = campana.nueva_campana("humano")
        perfil = campana.cargar_perfil()
        perfil["coleccion"] = {
            c.nombre: c.a_dict()
            for cartas in mazos.TODOS.values() for c in cartas}
        campana.guardar_perfil(perfil)
        base_antes = {n: dict(d) for n, d in campana.coleccion_de().items()}
        mazo_antes = [dict(d) for d in estado["cartas"]]
        nuevas, mejoradas = campana.abrir_sobre(estado)
        # todo el pool poseido: todo duplica, el mazo no cambia
        self.assertEqual(nuevas, [])
        self.assertEqual(len(mejoradas), 3)
        self.assertEqual(estado["cartas"], mazo_antes)
        despues = campana.coleccion_de()
        self.assertEqual(
            sum(sum(d[l] for l in "nseo") for d in despues.values()),
            sum(sum(d[l] for l in "nseo") for d in base_antes.values()) + 3)

    def test_nueva_entra_en_la_coleccion(self):
        perfil = campana.cargar_perfil()
        perfil["coleccion"] = {}
        campana.guardar_perfil(perfil)
        estado = campana.nueva_campana("goblin")
        pool = campana.cartas_del_pool(estado)
        estado["cartas"] = [pool[0].a_dict()]
        with mock.patch.object(campana.random, "choices",
                               side_effect=[[pool[1]], [pool[2]], [pool[3]]]):
            nuevas, mejoradas = campana.abrir_sobre(estado)
        self.assertEqual(nuevas, [pool[1].nombre, pool[2].nombre, pool[3].nombre])
        self.assertEqual(mejoradas, [])
        self.assertEqual(len(estado["cartas"]), 4)

    def test_sobre_en_recompensas_y_texto(self):
        self.assertIn("sobre", campana.TEXTO_RECOMPENSA)
        for nodo in ("ruinas", "fortaleza", "asalto"):
            self.assertIn("sobre", campana.recompensas_de(nodo))
        self.assertNotIn("sobre", campana.recompensas_de("senda"))

    def test_caravana_da_sobre(self):
        enc = campana.encuentro_para("fortaleza")
        self.assertEqual(enc["id"], "caravana")
        self.assertEqual(len(enc["opciones"]), 2)
        efectos = {op["efecto"] for op in enc["opciones"]}
        self.assertIn("sobre", efectos)

    def test_efecto_sobre_procesa_tres(self):
        estado = campana.nueva_campana("elfo")
        antes = len(estado["cartas"])
        titulo, texto = campana.aplicar_encuentro(estado, "sobre")
        self.assertEqual(titulo, "Caravana")
        self.assertIn("Abres el sobre:", texto)
        # 3 cartas procesadas: nuevas crecen, duplicadas mejoran sin crecer
        self.assertLessEqual(len(estado["cartas"]), antes + 3)


class TestRevelar(unittest.TestCase):
    def _revelar_con(self, nuevas, mejoradas, eventos):
        import pantallas

        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        original = pygame.event.get
        cola = list(eventos)
        estado = {"n": 0}

        def get():
            estado["n"] += 1
            if cola:
                return [cola.pop(0)]
            if estado["n"] > 300:
                return [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]
            return []

        pygame.event.get = get
        try:
            return asyncio.run(pantallas.revelar_sobre(pantalla, RelojFalso(), nuevas, mejoradas))
        finally:
            pygame.event.get = original

    def _clic(self):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(640, 400), button=1)

    def _esc(self):
        return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)

    def _legendaria(self):
        return Carta("Reina Isolde", 9, 9, 8, 8, bando="humano")

    def test_revelar_tres_y_salir(self):
        comun = Carta("Espadachin", 8, 6, 5, 7, bando="humano")
        self._revelar_con([comun, self._legendaria()], [comun],
                          [self._clic()] * 4)

    def test_esc_sale_antes_de_tiempo(self):
        comun = Carta("Espadachin", 8, 6, 5, 7, bando="humano")
        self._revelar_con([comun], [], [self._esc()])

    def test_sobre_vacio(self):
        self._revelar_con([], [], [self._clic()])


class TestColeccionPaginada(unittest.TestCase):
    def test_filtrar_por_habilidad_y_rareza(self):
        import pantallas

        muros = pantallas.filtrar_coleccion(mazos.HUMANOS, "muro", None)
        self.assertTrue(muros)
        self.assertTrue(all(c.habilidad == "muro" for c in muros))
        leg = pantallas.filtrar_coleccion(mazos.HUMANOS, None, "LEGENDARIA")
        self.assertEqual({c.nombre for c in leg},
                         {"Rey Aldric", "Reina Isolde", "Amanecer Blindado", "Sol Naciente"})
        nada = pantallas.filtrar_coleccion(mazos.HUMANOS, "quema", "LEGENDARIA")
        self.assertEqual(nada, [])

    def test_paginar_recorta_y_sujeta(self):
        import pantallas

        pagina, total, idx = pantallas.paginar_coleccion(mazos.HUMANOS, 0)
        self.assertEqual(len(pagina), 10)
        self.assertEqual(total, 3)
        pagina2, total2, idx2 = pantallas.paginar_coleccion(mazos.HUMANOS, 9)
        self.assertEqual(idx2, 2)
        self.assertEqual(len(pagina2), 5)

    def test_navegar_filtrar_y_ficha_sin_colgarse(self):
        import pantallas

        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        original = pygame.event.get
        estado = campana.nueva_campana("humano")
        cola = [
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(890, 590), button=1),
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(135, 279), button=1),
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(640, 400), button=1),
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE),
        ]

        def get():
            return [cola.pop(0)] if cola else []

        pygame.event.get = get
        try:
            asyncio.run(pantallas.coleccion(pantalla, RelojFalso(), estado))
        finally:
            pygame.event.get = original


class TestMejoraPaginada(unittest.TestCase):
    def _correr_con(self, coro, eventos):
        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        original = pygame.event.get
        cola = list(eventos)
        estado = {"n": 0}

        def get():
            estado["n"] += 1
            if cola:
                return [cola.pop(0)]
            if estado["n"] > 300:
                raise AssertionError("la pantalla no devuelve")
            return []

        pygame.event.get = get
        try:
            return asyncio.run(coro(pantalla))
        finally:
            pygame.event.get = original

    def _derecha(self):
        return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)

    def test_mejorar_pagina_dos_devuelve_indice_global(self):
        import pantallas

        estado = campana.nueva_campana("humano")
        estado["cartas"] += [dict(estado["cartas"][0]), dict(estado["cartas"][1])]
        idx = self._correr_con(
            lambda pantalla: pantallas.elegir_carta_para_mejorar(
                pantalla, RelojFalso(), estado),
            [self._derecha(),
             pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(556, 290), button=1)])
        self.assertEqual(idx, 10)

    def test_reemplazo_pagina_dos_devuelve_indice_global(self):
        import pantallas
        import mazos

        estado = campana.nueva_campana("orco")
        estado["cartas"] += [dict(estado["cartas"][0]), dict(estado["cartas"][1])]
        idx = self._correr_con(
            lambda pantalla: pantallas.draft_reemplazo(
                pantalla, RelojFalso(), estado, mazos.HUMANOS[0]),
            [self._derecha(),
             pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(561, 437), button=1)])
        self.assertEqual(idx, 10)


class TestTiendaYPity(unittest.TestCase):
    def _fijar_perfil(self, moneda=0, pity=0):
        perfil = campana.cargar_perfil()
        perfil["moneda"] = moneda
        perfil["pity_sobres"] = pity
        campana.guardar_perfil(perfil)

    def test_pity_garantiza_legendaria_al_decimo(self):
        from reglas import rareza

        self._fijar_perfil(pity=9)
        estado = campana.nueva_campana("humano")
        nuevas, mejoradas = campana.abrir_sobre(estado)
        sacadas = nuevas + mejoradas
        self.assertTrue(sacadas)
        catalogo = {c.nombre: c for cartas in mazos.TODOS.values() for c in cartas}
        self.assertTrue(any(rareza(catalogo[n])[0] == "LEGENDARIA" for n in sacadas))
        self.assertEqual(campana.pity_sobres(), 0)

    def test_pity_cuenta_sin_legendaria(self):
        from reglas import rareza

        self._fijar_perfil(pity=4)
        estado = campana.nueva_campana("orco")
        comun = next(c for c in campana.cartas_del_pool(estado)
                     if rareza(c)[0] == "COMUN")
        with mock.patch.object(campana.random, "choices", return_value=[comun]):
            nuevas, mejoradas = campana.abrir_sobre(estado)
        self.assertEqual(len(nuevas) + len(mejoradas), 1)
        self.assertEqual(campana.pity_sobres(), 5)

    def test_comprar_sin_moneda_no_vende(self):
        self._fijar_perfil(moneda=0, pity=2)
        estado = campana.nueva_campana("elfo")
        self.assertEqual(campana.comprar_sobre(estado), (False, [], []))
        self.assertEqual(campana.moneda(), 0)
        self.assertEqual(campana.pity_sobres(), 2)

    def test_comprar_descuenta(self):
        self._fijar_perfil(moneda=60, pity=0)
        estado = campana.nueva_campana("goblin")
        ok, nuevas, mejoradas = campana.comprar_sobre(estado)
        self.assertTrue(ok)
        self.assertEqual(len(nuevas) + len(mejoradas), 3)
        self.assertEqual(campana.moneda(), 0)

    def _correr_pantalla(self, coro, eventos):
        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        original = pygame.event.get
        cola = list(eventos)
        estado = {"n": 0}

        def get():
            estado["n"] += 1
            if cola:
                return [cola.pop(0)]
            if estado["n"] > 500:
                raise AssertionError("la pantalla no devuelve")
            return []

        pygame.event.get = get
        try:
            return asyncio.run(coro(pantalla))
        finally:
            pygame.event.get = original

    def _clic(self, x, y):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(x, y), button=1)

    def _esc(self):
        return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)

    def test_tienda_compra_y_sale(self):
        import pantallas

        self._fijar_perfil(moneda=60, pity=0)
        estado = campana.nueva_campana("vampiro")
        antes = len(estado["cartas"])
        self._correr_pantalla(
            lambda pantalla: pantallas.tienda(pantalla, RelojFalso(), estado),
            [self._clic(640, 477)] + [self._clic(640, 400)] * 4
            + [self._clic(640, 542)])
        self.assertEqual(campana.moneda(), 0)
        self.assertGreaterEqual(len(estado["cartas"]), antes)

    def test_tienda_sin_moneda_avisa(self):
        import pantallas

        self._fijar_perfil(moneda=0, pity=0)
        estado = campana.nueva_campana("dragon")
        self._correr_pantalla(
            lambda pantalla: pantallas.tienda(pantalla, RelojFalso(), estado),
            [self._clic(640, 477), self._esc()])

    def test_mapa_boton_tienda_ida_y_vuelta(self):
        import pantallas

        self._fijar_perfil(moneda=0, pity=0)
        estado = campana.nueva_campana("humano")
        accion = self._correr_pantalla(
            lambda pantalla: pantallas.mapa_campana(pantalla, RelojFalso(), estado),
            [self._clic(1110, 621), self._esc(), self._esc()])
        self.assertEqual(accion, "salir")


if __name__ == "__main__":
    unittest.main()
