"""Regresiones de progreso con perfiles aislados y los flujos reales."""

import asyncio
import copy
import json
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import campana
import main
import pantallas
import mazos
import persistencia
from partida import Juego, Resultado, partida
from ui import ANCHO, ALTO


class Reloj:
    def tick(self, fps=60):
        return 16


class TestIntegridadProgreso(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory(prefix="tt_integridad_")
        self.addCleanup(self.directorio.cleanup)
        env = patch.dict(os.environ, {"TRIPLETRIAD_DATA": self.directorio.name})
        env.start()
        self.addCleanup(env.stop)
        pygame.init()
        self.screen = pygame.display.set_mode((ANCHO, ALTO))
        self.estado = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        campana.guardar(self.estado)

    def test_guardar_editor_repetidamente_no_duplica_mejoras(self):
        campana.registrar_mejora(self.estado, self.estado["cartas"][0]["nombre"], "n")
        esperadas = [c.a_dict() for c in campana.cartas_jugador(self.estado)]
        perfil = copy.deepcopy(campana.cargar_perfil())
        for _ in range(3):
            eventos = [pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                         button=1, pos=(570, 626))]
            salir = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]
            with patch("pygame.event.get", side_effect=[eventos, salir]):
                cartas = asyncio.run(pantallas._editar_mazo_run(
                    self.screen, Reloj(), self.estado))
            self.assertIsNotNone(cartas, "guardar un mazo valido debe funcionar")
            self.estado["cartas"] = cartas
            campana.guardar(self.estado)
            self.estado = campana.cargar()
            self.assertEqual([c.a_dict() for c in campana.cartas_jugador(self.estado)],
                             esperadas)
        self.assertEqual(campana.cargar_perfil(), perfil)

    def test_buscar_en_editor_filtra_sin_perder_cartas_equipadas(self):
        nombre = self.estado["cartas"][0]["nombre"]
        tecla = lambda k, texto="": pygame.event.Event(pygame.KEYDOWN, key=k, unicode=texto)
        cola = [
            [tecla(pygame.K_SLASH)],
            [tecla(pygame.K_a, nombre), tecla(pygame.K_RETURN)],
            [pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(570, 626))],
        ]
        dibujadas = []
        crear = pantallas.crt.crear

        def registrar(carta, *args, **kwargs):
            dibujadas.append(carta.nombre)
            return crear(carta, *args, **kwargs)

        def eventos():
            if len(cola) == 1:
                self.assertEqual(dibujadas, [nombre])
            dibujadas.clear()
            return cola.pop(0)

        with patch("pygame.event.get", side_effect=eventos), \
             patch("pantallas.crt.crear", side_effect=registrar):
            resultado = asyncio.run(pantallas._editar_mazo_run(self.screen, Reloj(), self.estado))
        self.assertEqual({c["nombre"] for c in resultado},
                         {c["nombre"] for c in self.estado["cartas"]})

    def test_comparacion_rechaza_reemplazo_invalido_y_permite_cancelar(self):
        from reglas import Carta

        bases = {f"Carta {i}": Carta(f"Carta {i}", 2, 2, 2, 2, bando="humano").a_dict()
                 for i in range(10)}
        seleccion = list(bases)
        # Sustituir por una carta que no se posee nunca debe confirmar.
        bases["Ajena"] = Carta("Ajena", 3, 3, 3, 3, bando="humano").a_dict()
        cartas = {n: Carta.desde_dict(d) for n, d in bases.items()}
        antes = copy.deepcopy(bases)
        eventos = [[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
                   [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]]
        with patch("pygame.event.get", side_effect=eventos):
            resultado = asyncio.run(pantallas.comparar_reemplazo(
                self.screen, Reloj(), "Ajena", seleccion, cartas, bases, set(seleccion)))
        self.assertIsNone(resultado)
        with patch("pygame.event.get", return_value=[
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)]):
            resultado = asyncio.run(pantallas.comparar_reemplazo(
                self.screen, Reloj(), "Ajena", seleccion, cartas, bases, set(bases)))
        self.assertEqual(resultado, seleccion[0])
        self.assertEqual(bases, antes)

    def test_abandonar_no_da_moneda_ni_registra_duelo_completado(self):
        resultado = Resultado(False, 0, 0, (0, 0))
        resultado.abandonado = True
        perfil = copy.deepcopy(campana.cargar_perfil())
        with patch("main.partida", AsyncMock(return_value=resultado)), \
             patch("pantallas.mapa_campana", AsyncMock(side_effect=["seguir", "salir"])), \
             patch("pantallas.decision_narrativa", AsyncMock()), \
             patch("pantallas.derrota", AsyncMock(return_value="salir")), \
             patch("cinematicas.reproducir", AsyncMock()):
            asyncio.run(main._campana(self.screen, Reloj(), self.estado))
        self.assertEqual(campana.cargar_perfil(), perfil)
        self.assertEqual(self.estado["derrotas"], 0)
        self.assertEqual(self.estado["nodo"], "senda")

    def test_pausa_devuelve_abandono_explicito(self):
        juego = Juego("humano")
        juego.pausa = True
        clic = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                  pos=(ANCHO // 2, ALTO // 2 + 45))
        with patch("pygame.event.get", return_value=[clic]):
            resultado = asyncio.run(partida(self.screen, Reloj(), juego))
        self.assertTrue(getattr(resultado, "abandonado", False))

    def test_serializacion_fallida_conserva_guardado_anterior(self):
        ruta = campana.ruta_partida()
        with open(ruta, encoding="utf-8") as f:
            anterior = json.load(f)
        invalido = dict(self.estado, dato_no_serializable=object())
        with self.assertRaises(TypeError):
            campana.guardar(invalido)
        with open(ruta, encoding="utf-8") as f:
            self.assertEqual(json.load(f), anterior)

    def test_fallo_de_escritura_se_informa_y_conserva_perfil(self):
        anterior = campana.cargar_perfil()
        nuevo = dict(anterior, moneda=999)
        with patch("os.replace", side_effect=OSError("disco no disponible")):
            with self.assertRaises(OSError):
                campana.guardar_perfil(nuevo)
        self.assertEqual(campana.cargar_perfil(), anterior)

    def test_sobre_describe_valores_reales_y_duplicada_al_maximo(self):
        cartas = mazos.TODOS["humano"][:3]
        perfil = campana.cargar_perfil()
        for carta in cartas:
            perfil["coleccion"][carta.nombre] = dict(carta.a_dict(), n=10, s=10, e=10, o=10)
        perfil["coleccion"][cartas[0].nombre]["e"] = 8
        campana.guardar_perfil(perfil)
        with patch("campana.random.choices", side_effect=[[c] for c in cartas]):
            nuevas, duplicadas = campana.abrir_sobre(None)
        self.assertEqual(nuevas, [])
        detalles = campana.cargar_perfil()["ultimo_sobre_detalles"]
        self.assertEqual(detalles[cartas[0].nombre], "E: 8 -> 9")
        self.assertEqual(detalles[cartas[1].nombre], "Al maximo: sin cambio")
        mostradas = campana.cartas_por_nombre(None, duplicadas)
        self.assertEqual(mostradas[0].valores["E"], 9)
        self.assertTrue(all(v == 10 for v in mostradas[1].valores.values()))

    def test_fallo_al_generar_sobre_no_cobra(self):
        campana.ganar_moneda(120)
        antes = campana.cargar_perfil()
        with patch("campana._abrir_sobre", side_effect=RuntimeError("interrumpido")):
            with self.assertRaises(RuntimeError):
                campana.comprar_sobre(self.estado)
        self.assertEqual(campana.cargar_perfil(), antes)

    def test_compra_interrumpida_se_recupera_una_sola_vez(self):
        self.estado["cartas"] = self.estado["cartas"][:5]
        campana.guardar(self.estado)
        campana.ganar_moneda(120)
        guardar = persistencia._guardar_atomico

        def interrumpir(ruta, datos):
            if os.path.basename(ruta) == "campana.json":
                raise persistencia.ErrorGuardado("cierre durante commit")
            return guardar(ruta, datos)

        ofertas = mazos.DRAGONES[:3]
        with patch("campana.random.choices", side_effect=[[c] for c in ofertas]), \
             patch("persistencia._guardar_atomico", side_effect=interrumpir):
            with self.assertRaises(persistencia.ErrorGuardado):
                campana.comprar_sobre(self.estado)
        for _ in range(2):
            perfil = campana.cargar_perfil()
            recuperada = campana.cargar()
            self.assertEqual(perfil["moneda"], 60)
            for c in ofertas:
                self.assertIn(c.nombre, perfil["coleccion"])
                self.assertEqual(sum(d["nombre"] == c.nombre
                                     for d in recuperada["cartas"]), 1)

    def test_reanudar_recupera_recompensa_sin_repetir_victoria(self):
        with patch("main.partida", AsyncMock(return_value=Resultado(True, 2, 5, (5, 4)))), \
             patch("pantallas.mapa_campana", AsyncMock(return_value="seguir")), \
             patch("pantallas.decision_narrativa", AsyncMock()), \
             patch("pantallas.recompensa", AsyncMock(side_effect=SystemExit)), \
             patch("cinematicas.reproducir", AsyncMock()):
            with self.assertRaises(SystemExit):
                asyncio.run(main._campana(self.screen, Reloj(), self.estado))
        recuperada = campana.cargar()
        self.assertEqual(recuperada.get("recompensa_pendiente"), "senda")
        perfil = campana.cargar_perfil()
        with patch("main.partida", AsyncMock()) as duelo, \
             patch("pantallas.mapa_campana", AsyncMock(return_value="salir")), \
             patch("pantallas.recompensa", AsyncMock(return_value="entrenamiento")), \
             patch("pantallas.elegir_carta_para_mejorar", AsyncMock(return_value=0)), \
             patch("pantallas.cartel", AsyncMock()), \
             patch("pantallas.encuentro", AsyncMock()), \
             patch("cinematicas.reproducir", AsyncMock()):
            asyncio.run(main._campana(self.screen, Reloj(), recuperada))
        duelo.assert_not_awaited()
        guardada = campana.cargar()
        self.assertFalse(guardada.get("recompensa_pendiente"))
        self.assertEqual(guardada["victorias"], 1)
        self.assertEqual(sum(sum(d.values()) for d in guardada["mejoras"].values()), 1)
        self.assertEqual(campana.cargar_perfil(), perfil)

    def test_cerrar_cartel_de_recompensa_no_permite_cobrarla_dos_veces(self):
        campana.registrar_resultado(self.estado, Resultado(True, 2, 5, (5, 4)))
        with patch("pantallas.elegir_carta_para_mejorar", AsyncMock(return_value=0)), \
             patch("pantallas.cartel", AsyncMock(side_effect=SystemExit)):
            with self.assertRaises(SystemExit):
                asyncio.run(pantallas.aplicar_recompensa(
                    self.screen, Reloj(), self.estado, "entrenamiento", "senda"))
        recuperada = campana.cargar()
        antes = copy.deepcopy(recuperada)
        campana.entregar_recompensa(recuperada, "entrenamiento", "senda", idx=0)
        self.assertEqual(recuperada, antes)
        self.assertFalse(recuperada.get("recompensa_pendiente"))

    def test_premio_de_duelo_guarda_desglose_coherente(self):
        campana.registrar_resultado(self.estado, Resultado(True, 3, 5, (6, 3)))
        premio = self.estado["ultimo_premio"]
        self.assertEqual(premio["total"],
                         campana.MONEDA_POR_DUELO + campana.MONEDA_VICTORIA
                         + campana.MONEDA_POR_CAPTURA * 3)
        self.assertEqual(sum(v for _, v in premio["partes"]), premio["total"])
        self.assertEqual([etiqueta for etiqueta, _ in premio["partes"]][0],
                         "Duelo completado")
        self.assertEqual(campana.moneda(), premio["total"])
        # El cartel de recompensa muestra el desglose sin reventar.
        self._pintar_recompensa()

    def _pintar_recompensa(self):
        import pantallas

        self.estado["recompensa_pendiente"] = "senda"
        with patch("pygame.event.get", return_value=[
                pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(0, 0)),
                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]):
            clave = asyncio.run(pantallas.recompensa(
                self.screen, Reloj(), self.estado, "senda"))
        self.assertIn(clave, campana.recompensas_de("senda"))

    def test_final_interrumpido_sigue_disponible_en_continuar(self):
        self.estado["nodo"] = "trono"
        campana.registrar_resultado(self.estado, Resultado(True, 2, 5, (5, 4)))
        recuperada = campana.cargar()
        self.assertTrue(recuperada["completada"])
        self.assertTrue(campana.puede_continuar(recuperada))
        clic = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(440, 235))
        with patch("pygame.event.get", return_value=[clic]):
            accion = asyncio.run(pantallas.menu(self.screen, Reloj(), recuperada))
        self.assertEqual(accion, "campana")

        async def final(screen, clock, estado):
            campana.completar(estado)

        with patch("pantallas.epilogo", side_effect=final), \
             patch("pantallas.cartel", AsyncMock()), \
             patch("main.partida", AsyncMock()) as duelo:
            asyncio.run(main._campana(self.screen, Reloj(), recuperada))
        duelo.assert_not_awaited()
        self.assertFalse(campana.puede_continuar(campana.cargar()))
        self.assertEqual(campana.progreso_fragmentos()[0], 1)


if __name__ == "__main__":
    unittest.main()
