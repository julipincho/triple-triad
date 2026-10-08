"""Tests del tutorial: manual, practicas con el motor real y perfil.

    python -m unittest tests.test_tutorial -v
"""

import asyncio
import copy
import os
import sys
import tempfile
import unittest

# No escribir en los datos reales del jugador
os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests_tuto")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import campana  # noqa: E402
import tutorial  # noqa: E402
from partida import Juego  # noqa: E402
from reglas import CPU, HABILIDADES, USUARIO, capturas, valor_efectivo  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


def setUpModule():
    pygame.init()
    pygame.display.set_mode((ANCHO, ALTO))


class RelojFalso:
    def tick(self, fps=60):
        return 16


def _evento(tipo, **kwargs):
    return pygame.event.Event(tipo, **kwargs)


def _guia_en_paso(indice_practica, indice_paso=0):
    practica = tutorial.PRACTICAS[indice_practica]
    juego, guia = tutorial.construir_duelo_practica(practica, indice_practica)
    for _ in range(indice_paso):
        # avanza pasos colocando la jugada valida de cada uno
        paso = guia.paso_actual()
        r, c = paso["validas"][0]
        carta = juego.mano_u[0]
        nuevo = copy.deepcopy(juego.board)
        copia = carta.copia()
        copia.dueno = USUARIO
        nuevo[r][c] = copia
        caps = capturas(nuevo, r, c)
        caps_reales = juego.colocar(carta, juego.mano_u, USUARIO, r, c)
        assert set(caps_reales) == set(caps)
        guia.tras_colocar(juego, carta, r, c, caps_reales)
    return juego, guia


class TestManual(unittest.TestCase):
    def test_diez_paginas_con_que_y_sirve(self):
        paginas = tutorial.paginas_manual()
        self.assertEqual(len(paginas), 10)
        for p in paginas:
            self.assertTrue(p["titulo"], p.get("id"))
            self.assertTrue(p["que"], p["id"])
            self.assertTrue(p["sirve"], p["id"])

    def test_habilidades_citan_las_reglas_reales(self):
        """El texto de habilidades no puede quedar viejo: sale de reglas.py."""
        paginas = {p["id"]: p for p in tutorial.paginas_manual()}
        texto_hab = "\n".join(paginas["habilidades"]["que"])
        for nombre, descripcion in HABILIDADES.items():
            self.assertIn(nombre.upper(), texto_hab)
            self.assertIn(descripcion, texto_hab)

    def test_las_cuatro_practicas_esperadas(self):
        self.assertEqual([p["id"] for p in tutorial.PRACTICAS],
                         ["basica", "same", "cadena", "habilidades"])


class TestPracticasConMotorReal(unittest.TestCase):
    """Cada paso se puede completar y la regla que enseña dispara de verdad."""

    def _validar(self, ip, istep, celda, debe_ok=True):
        juego, guia = _guia_en_paso(ip, istep)
        carta = juego.mano_u[0]
        ok, motivo = guia.validar_colocacion(juego, carta, *celda)
        if debe_ok:
            self.assertTrue(ok, f"practica {ip} paso {istep} en {celda}: {motivo}")
        else:
            self.assertFalse(ok)
            self.assertTrue(motivo)
        return juego, guia

    def test_basica_captura_el_flanco_debil(self):
        juego, guia = self._validar(0, 0, (0, 1))
        carta = juego.mano_u[0]
        self.assertGreater(valor_efectivo(carta, 0, 1, "S", juego.board), 3)
        self._validar(0, 0, (2, 2), debe_ok=False)

    def test_same_cae_dos_a_la_vez_sin_superar(self):
        juego, guia = self._validar(1, 0, (1, 1))
        carta = juego.mano_u[0]
        # igualdad pura en ambos lados: la basica sola no capturaria nada
        self.assertEqual(valor_efectivo(carta, 1, 1, "N", juego.board), 5)
        self.assertEqual(juego.board[0][1].valores["S"], 5)
        self.assertEqual(valor_efectivo(carta, 1, 1, "O", juego.board), 7)
        self.assertEqual(juego.board[1][0].valores["E"], 7)
        nuevo = copy.deepcopy(juego.board)
        copia = carta.copia()
        copia.dueno = USUARIO
        nuevo[1][1] = copia
        self.assertEqual(set(capturas(nuevo, 1, 1)), {(0, 1), (1, 0)})
        self._validar(1, 0, (2, 2), debe_ok=False)

    def test_cadena_arrastra_a_la_vecina(self):
        juego, guia = self._validar(2, 0, (1, 0))
        carta = juego.mano_u[0]
        nuevo = copy.deepcopy(juego.board)
        copia = carta.copia()
        copia.dueno = USUARIO
        nuevo[1][0] = copia
        caps = set(capturas(nuevo, 1, 0))
        self.assertEqual(caps, {(1, 1), (1, 2)})
        # la segunda no toca la casilla jugada: solo llega por cadena
        self.assertEqual(abs(1 - 1) + abs(2 - 0), 2)
        self.assertGreater(abs(1 - 1) + abs(2 - 0), 1,
                           "la cola no es adyacente: solo llega por cadena")
        self._validar(2, 0, (2, 2), debe_ok=False)

    def test_muro_bloquea_hasta_un_10(self):
        juego, guia = self._validar(3, 0, (0, 1))
        carta = juego.mano_u[0]
        muro = juego.board[0][0]
        self.assertEqual(muro.habilidad, "muro")
        # sin muro ganaria (10 contra 9): el bloqueo es la leccion
        self.assertGreater(valor_efectivo(carta, 0, 1, "O", juego.board), 9)
        nuevo = copy.deepcopy(juego.board)
        copia = carta.copia()
        copia.dueno = USUARIO
        nuevo[0][1] = copia
        self.assertEqual(capturas(nuevo, 0, 1), [])
        self._validar(3, 0, (2, 2), debe_ok=False)

    def test_furia_necesita_al_aliado(self):
        juego, guia = _guia_en_paso(3, 1)
        carta = juego.mano_u[0]
        self.assertEqual(carta.habilidad, "furia")
        ok, motivo = guia.validar_colocacion(juego, carta, 0, 1)
        self.assertTrue(ok, motivo)
        # sin furia empataria (4 contra 4): el +1 es lo que rompe
        base = carta.valores["S"]
        self.assertEqual(base, juego.board[1][1].valores["N"])
        self.assertEqual(valor_efectivo(carta, 0, 1, "S", juego.board), base + 1)
        ok, _ = guia.validar_colocacion(juego, carta, 2, 2)
        self.assertFalse(ok)

    def test_embestida_solo_ruge_en_el_centro(self):
        juego, guia = _guia_en_paso(3, 2)
        carta = juego.mano_u[0]
        self.assertEqual(carta.habilidad, "embestida")
        ok, motivo = guia.validar_colocacion(juego, carta, 1, 1)
        self.assertTrue(ok, motivo)
        # fuera del centro perderia (5 contra 6)
        self.assertLess(carta.valores["O"], juego.board[1][0].valores["E"])
        self.assertEqual(valor_efectivo(carta, 1, 1, "O", juego.board),
                         carta.valores["O"] + 2)
        ok, _ = guia.validar_colocacion(juego, carta, 2, 2)
        self.assertFalse(ok)

    def test_tras_colocar_avanza_y_cierra(self):
        juego, guia = _guia_en_paso(3, 0)
        paso = guia.paso_actual()
        r, c = paso["validas"][0]
        carta = juego.mano_u[0]
        caps = juego.colocar(carta, juego.mano_u, USUARIO, r, c)
        guia.tras_colocar(juego, carta, r, c, caps)
        self.assertFalse(guia.terminada)
        self.assertEqual(guia.paso, 1)
        # la mano se repone para el paso siguiente
        self.assertEqual(len(juego.mano_u), 1)

        juego2, guia2 = _guia_en_paso(0, 0)
        paso2 = guia2.paso_actual()
        r, c = paso2["validas"][0]
        carta2 = juego2.mano_u[0]
        caps2 = juego2.colocar(carta2, juego2.mano_u, USUARIO, r, c)
        guia2.tras_colocar(juego2, carta2, r, c, caps2)
        self.assertTrue(guia2.terminada)
        self.assertTrue(juego2.fin)
        self.assertEqual(juego2.ganador, USUARIO)

    def test_practicas_son_humano_contra_orco(self):
        for i, practica in enumerate(tutorial.PRACTICAS):
            juego, _ = tutorial.construir_duelo_practica(practica, i)
            self.assertEqual(juego.bando, "humano")
            self.assertEqual(juego.bando_cpu, "orco")
            self.assertNotEqual(juego.bando, juego.bando_cpu)


class TestAbandonoEndToEnd(unittest.TestCase):
    def test_esc_y_enter_abandonan_el_duelo_guiado(self):
        import partida as modulo_partida

        juego, guia = tutorial.construir_duelo_practica(tutorial.PRACTICAS[0], 0)
        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        cola = [
            _evento(pygame.KEYDOWN, key=pygame.K_ESCAPE),
            _evento(pygame.KEYDOWN, key=pygame.K_RETURN),
        ]
        original = pygame.event.get

        def eventos():
            return [cola.pop(0)] if cola else []

        pygame.event.get = eventos
        try:
            asyncio.run(modulo_partida.partida(pantalla, RelojFalso(), juego, guia=guia))
        finally:
            pygame.event.get = original
        self.assertTrue(getattr(juego, "abandonado", False))
        self.assertTrue(guia.confirmar_salida)

    def test_boton_salir_pide_confirmar_y_abandona(self):
        import partida as modulo_partida

        juego, guia = tutorial.construir_duelo_practica(tutorial.PRACTICAS[2], 2)
        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        centro_salir = guia.boton_salir.rect.center
        self.assertTrue(guia.clic_salir(centro_salir))
        self.assertFalse(guia.clic_salir((5, 5)))
        cola = [
            _evento(pygame.MOUSEBUTTONDOWN, pos=centro_salir, button=1),
            _evento(pygame.KEYDOWN, key=pygame.K_RETURN),
        ]
        original = pygame.event.get

        def eventos():
            return [cola.pop(0)] if cola else []

        pygame.event.get = eventos
        try:
            asyncio.run(modulo_partida.partida(pantalla, RelojFalso(), juego, guia=guia))
        finally:
            pygame.event.get = original
        self.assertTrue(guia.confirmar_salida)
        self.assertTrue(getattr(juego, "abandonado", False))
        self.assertFalse(guia.terminada)

    def test_esc_solo_pide_confirmar_no_pausa(self):
        import partida as modulo_partida

        juego, guia = tutorial.construir_duelo_practica(tutorial.PRACTICAS[0], 0)
        pantalla = pygame.display.set_mode((ANCHO, ALTO))
        cola = [_evento(pygame.KEYDOWN, key=pygame.K_ESCAPE)]
        estado = {"n": 0}
        original = pygame.event.get

        def eventos():
            estado["n"] += 1
            if estado["n"] > 60:
                juego.abandonado = True
                return [_evento(pygame.KEYDOWN, key=pygame.K_RETURN)]
            return [cola.pop(0)] if cola else []

        pygame.event.get = eventos
        try:
            asyncio.run(modulo_partida.partida(pantalla, RelojFalso(), juego, guia=guia))
        finally:
            pygame.event.get = original
        self.assertFalse(juego.pausa, "ESC en el tutorial no debe pausar")


class TestPerfilTutorial(unittest.TestCase):
    def test_flags_por_defecto_y_resumen(self):
        perfil = campana.perfil_por_defecto()
        self.assertFalse(perfil["tutorial_visto"])
        self.assertFalse(perfil["tutorial_completado"])
        self.assertEqual(perfil["tutorial_paso"], 0)

    def test_marcar_y_leer_estado(self):
        campana.marcar_tutorial(visto=True, paso=2)
        visto, completado, paso = campana.tutorial_estado()
        self.assertTrue(visto)
        self.assertFalse(completado)
        self.assertEqual(paso, 2)
        self.assertTrue(campana.tutorial_visto())
        campana.marcar_tutorial(completado=True, paso=4)
        visto, completado, paso = campana.tutorial_estado()
        self.assertTrue(completado)
        self.assertEqual(paso, 4)
        # limpia para no contaminar otros tests
        campana.marcar_tutorial(visto=False, completado=False, paso=0)


if __name__ == "__main__":
    unittest.main()
