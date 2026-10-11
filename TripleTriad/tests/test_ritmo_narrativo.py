"""G6: ritmo narrativo. Resumen al continuar, diario de dialogos, escenas
vistas y consecuencias visibles de las decisiones.

Cada prueba corre con su propio directorio de datos: el diario se escribe en
el perfil y no deben contaminarse unas pruebas con otras.
"""

import asyncio
import os
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402

import campana  # noqa: E402
import cinematicas  # noqa: E402
import main  # noqa: E402
import narrativa  # noqa: E402
import pantallas  # noqa: E402


class Reloj:
    def tick(self, fps=60):
        return 16


class Base(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory(prefix="tt_ritmo_")
        self.addCleanup(self.directorio.cleanup)
        env = patch.dict(os.environ, {"TRIPLETRIAD_DATA": self.directorio.name})
        env.start()
        self.addCleanup(env.stop)
        pygame.init()
        self.screen = pygame.display.set_mode((ANCHO, ALTO))


class TestResumenAlContinuar(Base):
    def test_resumen_orienta_sobre_el_siguiente_objetivo(self):
        estado = campana.nueva_campana("humano")
        info = campana.info_duelo(estado)
        lineas = campana.resumen_campana(estado)
        texto = " ".join(lineas)
        self.assertIn(info["titulo"], texto)
        self.assertIn(info["nombre"], texto)
        self.assertIn("humano", texto.lower())

    def test_resumen_de_campana_completa_no_revienta(self):
        estado = campana.nueva_campana("humano")
        estado["completada"] = True
        lineas = campana.resumen_campana(estado)
        self.assertTrue(any("completa" in l.lower() for l in lineas))

    def test_resumen_de_final_pendiente_avisa(self):
        estado = campana.nueva_campana("humano")
        estado["final_pendiente"] = True
        lineas = campana.resumen_campana(estado)
        self.assertTrue(any("final" in l.lower() for l in lineas))

    def test_resumen_menciona_recompensa_pendiente(self):
        estado = campana.nueva_campana("humano")
        estado["recompensa_pendiente"] = "senda"
        lineas = campana.resumen_campana(estado)
        self.assertTrue(any("recompensa" in l.lower() for l in lineas))


class TestDiarioDeDialogos(Base):
    def test_guardar_y_leer_una_linea(self):
        campana.registrar_dialogo("Nara", "No preguntes de donde salen las cartas.")
        diario = campana.diario_dialogos()
        self.assertEqual(len(diario), 1)
        self.assertEqual(diario[0]["hablante"], "Nara")
        self.assertIn("cartas", diario[0]["texto"])

    def test_lineas_vacias_se_ignoran(self):
        campana.registrar_dialogo("", "   ")
        self.assertEqual(campana.diario_dialogos(), [])

    def test_el_diario_tiene_tope(self):
        for i in range(campana.DIARIO_MAX + 15):
            campana.registrar_dialogo("Nara", f"linea {i}")
        diario = campana.diario_dialogos()
        self.assertEqual(len(diario), campana.DIARIO_MAX)
        # se conservan las mas recientes
        self.assertEqual(diario[-1]["texto"], f"linea {campana.DIARIO_MAX + 14}")

    def test_filtro_por_faccion_conserva_la_narracion_comun(self):
        campana.registrar_dialogo("Voz", "narracion sin faccion")
        campana.registrar_dialogo("Nara", "algo de humano", faccion="humano")
        campana.registrar_dialogo("Nara", "algo de orco", faccion="orco")
        humano = campana.diario_dialogos("humano")
        textos = [e["texto"] for e in humano]
        self.assertIn("narracion sin faccion", textos)
        self.assertIn("algo de humano", textos)
        self.assertNotIn("algo de orco", textos)

    def test_pintar_el_diario_no_revienta_y_sale_con_esc(self):
        campana.registrar_dialogo("Nara", "Una linea larga " * 8)
        ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        with patch("pygame.event.get", return_value=[ev]):
            asyncio.run(pantallas.diario_dialogos(self.screen, Reloj(), None))


class TestEscenasVistas(Base):
    def _escenas(self):
        return [cinematicas.esc("linea uno"), cinematicas.esc("linea dos"),
                cinematicas.esc("linea tres")]

    def test_primera_vez_no_pregunta_y_marca_visto(self):
        escenas = self._escenas()
        self.assertGreaterEqual(len(escenas), 3)
        with patch("cinematicas.Cinematica.ejecutar", AsyncMock()) as ejecutar, \
             patch("cinematicas._preguntar_rever", AsyncMock(return_value=True)) as preg:
            asyncio.run(cinematicas.reproducir(self.screen, Reloj(), escenas,
                                               clave="prueba_vista"))
        preg.assert_not_awaited()
        ejecutar.assert_awaited()
        self.assertIn("prueba_vista", campana.cinematicas_vistas())

    def test_segunda_vez_ofrece_saltar(self):
        escenas = self._escenas()
        campana.marcar_cinematica("prueba_vista2")
        with patch("cinematicas.Cinematica.ejecutar", AsyncMock()) as ejecutar, \
             patch("cinematicas._preguntar_rever", AsyncMock(return_value=True)) as preg:
            asyncio.run(cinematicas.reproducir(self.screen, Reloj(), escenas,
                                               clave="prueba_vista2"))
        preg.assert_awaited()
        ejecutar.assert_not_awaited()

    def test_segunda_vez_se_puede_releer(self):
        escenas = self._escenas()
        campana.marcar_cinematica("prueba_vista3")
        with patch("cinematicas.Cinematica.ejecutar", AsyncMock()) as ejecutar, \
             patch("cinematicas._preguntar_rever", AsyncMock(return_value=False)):
            asyncio.run(cinematicas.reproducir(self.screen, Reloj(), escenas,
                                               clave="prueba_vista3"))
        ejecutar.assert_awaited()

    def test_las_escenas_cortas_no_interrumpen(self):
        cortas = self._escenas()[:2]
        campana.marcar_cinematica("prueba_corta")
        with patch("cinematicas.Cinematica.ejecutar", AsyncMock()) as ejecutar, \
             patch("cinematicas._preguntar_rever", AsyncMock(return_value=True)) as preg:
            asyncio.run(cinematicas.reproducir(self.screen, Reloj(), cortas,
                                               clave="prueba_corta"))
        preg.assert_not_awaited()
        ejecutar.assert_awaited()


class TestConsecuenciasVisibles(Base):
    def test_toda_decision_tiene_titulo_narrativo(self):
        for nodo, decision in narrativa.DECISION.items():
            self.assertTrue(decision.get("titulo"), f"{nodo} sin titulo narrativo")
            self.assertNotEqual(decision["titulo"], decision["id"])

    def test_titulo_decision_nunca_es_el_id(self):
        d = narrativa.decision_de("senda")
        self.assertEqual(narrativa.titulo_decision(d), d["titulo"])

    def test_resumen_efecto_refleja_los_deltas(self):
        efecto = {"confianza": 1, "conocimiento": 2, "revelacion": "x"}
        resumen = narrativa.resumen_efecto(efecto)
        self.assertIn("mas", resumen)
        self.assertIn("+1", resumen)
        self.assertIn("+2", resumen)
        self.assertNotIn("final", resumen.lower())

    def test_resumen_efecto_vacio_es_generico(self):
        self.assertTrue(narrativa.resumen_efecto({}).strip())

    def test_los_textos_no_prometen_mecanicas_inexistentes(self):
        """El sigilo es de campana; ninguna decision promete un reloj."""
        self.assertNotIn("permanente", campana.TEXTO_RECOMPENSA["sigilo"].lower())
        for decision in narrativa.DECISION.values():
            for op in decision["opciones"]:
                bajo = op["texto"].lower()
                self.assertNotIn("pierdes tiempo", bajo)
                self.assertNotIn("llegas antes", bajo)

    def test_la_decision_muestra_titulo_y_consecuencia(self):
        estado = campana.nueva_campana("humano")
        decision = narrativa.decision_de("senda")
        # clic en la primera opcion (rect en y=340..490, x=300..620)
        clic = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                  pos=(400, 400))
        capturado = {}

        async def falso_cartel(screen, clock, titulo, mensaje):
            capturado["titulo"] = titulo
            capturado["mensaje"] = mensaje

        with patch("pantallas.cartel", side_effect=falso_cartel), \
             patch("pygame.event.get", return_value=[clic]):
            asyncio.run(pantallas.decision_narrativa(
                self.screen, Reloj(), estado, decision))
        self.assertEqual(capturado["titulo"], decision["titulo"])
        cuerpo = capturado["mensaje"]
        if isinstance(cuerpo, (list, tuple)):
            cuerpo = " ".join(cuerpo)
        self.assertIn(decision["opciones"][0]["respuesta"], cuerpo)
        self.assertTrue("Nara" in cuerpo or "Umbral" in cuerpo)


class TestAmistadNoSeRepite(Base):
    def _correr_trono(self, estado):
        llamadas = []

        async def falso_reproducir(screen, clock, escenas, **kwargs):
            llamadas.append(list(escenas))

        with patch("main.partida", AsyncMock(return_value=_abandonado())), \
             patch("pantallas.mapa_campana", AsyncMock(return_value="seguir")), \
             patch("pantallas.decision_narrativa", AsyncMock()), \
             patch("cinematicas.reproducir", side_effect=falso_reproducir):
            asyncio.run(main._campana(self.screen, Reloj(), estado))
        return llamadas

    def test_la_escena_de_amistad_solo_sale_una_vez(self):
        estado = campana.nueva_campana("humano")
        estado["nodo"] = "trono"
        esperada = narrativa.escena_amistad()
        primera = self._correr_trono(estado)
        self.assertTrue(any(l == esperada for l in primera),
                        "la escena de amistad no se reprodujo la primera vez")
        self.assertTrue(estado.get("amistad_vista"))
        segunda = self._correr_trono(estado)
        self.assertFalse(any(l == esperada for l in segunda),
                         "la escena de amistad se repitio en el reintento")


class _Resultado:
    abandonado = True
    victoria = False
    capturas = 0
    jugadas = 0
    marcador = (0, 0)


def _abandonado():
    return _Resultado()


if __name__ == "__main__":
    unittest.main()
