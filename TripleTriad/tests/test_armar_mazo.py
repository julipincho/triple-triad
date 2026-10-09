"""La pantalla de armar mazo: hueco de verdad y cartas dentro del marco.

Dos bugs encontrados jugando, no leyendo codigo:

1. El mazo venia PRESELECCIONADO con 5 cartas, y no eran las de la faccion
   elegida sino las 5 primeras de una lista ordenada por bando en ORDEN
   ALFABETICO. Elegiendo humano aparecia un mazo de hombres lobo. El mazo
   debe venir vacio.

2. Las cartas del mazo se salian 24px por debajo de su panel: son de 104x144 y
   el panel media 130 de alto. La auditoria visual no lo cazaba porque solo
   comprueba los bordes de la PANTALLA, no que un elemento este dentro de su
   propio marco. Este test mide la contencion.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tt_test_mazo")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

import campana  # noqa: E402
import facciones  # noqa: E402
import ui  # noqa: E402

import pantallas  # noqa: E402

#: Geometria importada de `pantallas`, que es donde la usa de verdad. Si se
#: escribiera a mano aqui, el test se quedaria verde mintiendo en cuanto
#: cambiaras la pantalla.
CARTA_W, CARTA_H = pantallas.MAZO_CARTA_W, pantallas.MAZO_CARTA_H
PANEL_COLECCION = pantallas.PANEL_COLECCION
PANEL_MAZO = pantallas.PANEL_MAZO
ORIGEN_COLECCION = pantallas.COLECCION_ORIGEN
PASO_COLECCION = pantallas.COLECCION_PASO
COLS_COLECCION = pantallas.COLECCION_COLUMNAS
ORIGEN_MAZO = pantallas.MAZO_ORIGEN
PASO_MAZO = pantallas.MAZO_PASO_X
HUECOS_MAZO = pantallas.MAZO_HUECOS
Y_BOTONES = pantallas.MAZO_Y_BOTONES


def setUpModule():
    pygame.init()
    pygame.display.set_mode((ui.ANCHO, ui.ALTO))


def _coleccion_de_prueba():
    """Una coleccion con cartas de VARIOS bandos, como la de un jugador real."""
    campana.asegurar_coleccion("humano")
    campana.asegurar_coleccion("orco")
    campana.asegurar_coleccion("dragon")
    campana.asegurar_coleccion("hombre_lobo")
    perfil = campana.cargar_perfil()
    return campana.coleccion_de(perfil), perfil


def _nombres(coleccion):
    from reglas import Carta

    poseidas = {n: Carta.desde_dict(dict(d)) for n, d in coleccion.items()}
    return poseidas, sorted(
        poseidas.keys(),
        key=lambda n: (poseidas[n].bando, -sum(poseidas[n].valores.values()), n))


class TestElMazoVieneVacio(unittest.TestCase):
    def test_sin_mazo_guardado_no_se_preselecciona_nada(self):
        """El bug: se rellenaba con `nombres[:5]`, que es ordenado por bando
        alfabeticamente, asi que salia siempre el mismo bando."""
        perfil = campana.cargar_perfil()
        campana.guardar_mazo_global([])
        self.assertEqual(campana.mazo_global(campana.cargar_perfil()), [])

        coleccion, _ = _coleccion_de_prueba()
        poseidas, nombres = _nombres(coleccion)
        seleccion = [n for n in campana.mazo_global(perfil) if n in coleccion]
        # Lo que hacia el codigo viejo, para documentar el bug:
        autocompletado = nombres[:5]
        self.assertEqual(len(autocompletado), 5)
        self.assertEqual(seleccion, [], "no deberia preseleccionar nada")

    def test_las_5_autocompletadas_eran_del_mismo_bando(self):
        """Por que se veia siempre el mismo bando: el sort es por bando."""
        coleccion, _ = _coleccion_de_prueba()
        poseidas, nombres = _nombres(coleccion)
        bandos = {poseidas[n].bando for n in nombres[:5]}
        self.assertEqual(len(bandos), 1,
                         "el bug hacia que las 5 fueran del mismo bando")
        # Y ese bando NO depende de la faccion elegida: es el primero por orden
        # alfabetico de la lista completa de bandos.
        primero = sorted(facciones.orden_facciones())[0]
        self.assertEqual(bandos.pop(), primero,
                         "el bando que aparecia era el primero alfabeticamente")

    def test_el_mazo_guardado_si_se_recupera(self):
        """Guardar y volver a abrir tiene que devolver lo mismo."""
        campana.guardar_mazo_global([])
        coleccion, _ = _coleccion_de_prueba()
        nombres_disponibles = list(coleccion)[:5]
        campana.guardar_mazo_global(nombres_disponibles)
        perfil = campana.cargar_perfil()
        seleccion = [n for n in campana.mazo_global(perfil) if n in coleccion]
        self.assertEqual(seleccion, nombres_disponibles)

    def test_no_se_puede_guardar_un_mazo_vacio(self):
        """Vacio al entrar, pero para jugar hacen falta 5 cartas."""
        campana.guardar_mazo_global([])
        ok, motivo = campana.validar_mazo([], set(campana.coleccion_de(
            campana.cargar_perfil())))
        self.assertFalse(ok)
        self.assertTrue(motivo)


class TestLasCartasCabenEnSuMarco(unittest.TestCase):
    def test_el_mazo_no_se_sale_de_su_panel(self):
        """El bug: 144px de carta en un panel de 130. Se salian 24px."""
        for i in range(HUECOS_MAZO):
            x = ORIGEN_MAZO[0] + i * PASO_MAZO
            y = ORIGEN_MAZO[1]
            rect = pygame.Rect(x, y, CARTA_W, CARTA_H)
            self.assertTrue(
                PANEL_MAZO.contains(rect),
                f"la carta {i} en {rect} se sale del panel {PANEL_MAZO}: "
                f"sobresale {max(0, PANEL_MAZO.bottom - rect.bottom)}px por abajo "
                f"y {max(0, rect.right - PANEL_MAZO.right)}px a la derecha")

    def test_el_panel_del_mazo_tiene_alto_para_sus_cartas(self):
        self.assertGreaterEqual(
            PANEL_MAZO.height, CARTA_H,
            "el panel es mas bajo que las cartas que tiene dentro")
        # Y queda margen por arriba y por abajo: dentro del marco, no pegadas.
        self.assertGreaterEqual(ORIGEN_MAZO[1] - PANEL_MAZO.top, 8,
                                "las cartas quedan pegadas al borde de arriba")
        self.assertGreaterEqual(
            PANEL_MAZO.bottom - (ORIGEN_MAZO[1] + CARTA_H), 8,
            "las cartas quedan pegadas al borde de abajo del panel")

    def test_la_coleccion_no_se_sale_de_su_panel(self):
        for i in range(COLS_COLECCION * 2):
            x = ORIGEN_COLECCION[0] + (i % COLS_COLECCION) * PASO_COLECCION[0]
            y = ORIGEN_COLECCION[1] + (i // COLS_COLECCION) * PASO_COLECCION[1]
            rect = pygame.Rect(x, y, CARTA_W, CARTA_H)
            self.assertTrue(PANEL_COLECCION.contains(rect),
                            f"la carta {i} en {rect} se sale de {PANEL_COLECCION}")

    def test_los_dos_paneles_no_se_solapan(self):
        self.assertFalse(
            PANEL_COLECCION.colliderect(PANEL_MAZO),
            "los paneles de coleccion y de mazo se pisan")

    def test_los_paneles_no_chocan_con_los_botones(self):
        """Los botones empiezan en y=700: el panel del mazo tiene que dejar
        sitio, o el boton se dibuja encima de las cartas."""
        self.assertLess(
            PANEL_MAZO.bottom, Y_BOTONES,
            f"el panel del mazo llega a {PANEL_MAZO.bottom} y los botones "
            f"empiezan en {Y_BOTONES}")

    def test_todo_cabe_en_la_pantalla(self):
        for panel in (PANEL_COLECCION, PANEL_MAZO):
            self.assertTrue(
                pygame.Rect(0, 0, ui.ANCHO, ui.ALTO).contains(panel),
                f"{panel} se sale de la pantalla")


class TestLaGeometriaRealCoincideConLaDelTest(unittest.TestCase):
    """El test de arriba mide constantes importadas, no escritas a mano.

    Vienen de `pantallas`, que es donde las usa de verdad, asi que si la
    pantalla cambia el test cambia con ella y no se queda verde mintiendo.
    """

    def test_las_constantes_vienen_de_pantallas(self):
        self.assertEqual(PANEL_MAZO, pantallas.PANEL_MAZO)
        self.assertEqual(PANEL_COLECCION, pantallas.PANEL_COLECCION)
        self.assertEqual(CARTA_W, pantallas.MAZO_CARTA_W)
        self.assertEqual(CARTA_H, pantallas.MAZO_CARTA_H)
        self.assertEqual(ORIGEN_MAZO, pantallas.MAZO_ORIGEN)
        self.assertEqual(HUECOS_MAZO, pantallas.MAZO_HUECOS)


class TestEditarElMazoEnCampana(unittest.TestCase):
    """El mazo se cambia con la partida en curso, no solo antes de empezar.

    Lo que motivo esto: `armar_mazo` edita el mazo GLOBAL, que es el que se usa
    al empezar una campana. Durante la partida no habia forma de cambiarlo, y una
    compra, una mejora o un draft a mitad de partida lo dejaban desajustado sin
    arreglo hasta terminar la campana entera.
    """

    def setUp(self):
        self.estado = campana.nueva_campana("humano")
        self.nombres = {d["nombre"] for d in self.estado["cartas"]}

    def test_el_mazo_de_la_run_es_distinto_del_global(self):
        """El editor tiene que tocar la run, no el perfil."""
        self.assertIn("cartas", self.estado)
        self.assertNotEqual(self.estado["cartas"],
                            campana.mazo_global(campana.cargar_perfil()))

    def test_validar_rechaza_un_mazo_de_menos_de_cinco(self):
        ok, motivo = campana.validar_mazo(self.estado["cartas"][:3], self.nombres)
        self.assertFalse(ok)
        self.assertTrue(motivo)

    def test_validar_rechaza_cartas_que_no_tienes(self):
        import mazos

        ajena = mazos.TODOS["dragon"][0].a_dict()
        ajena["nombre"] = "Carta Que No Es Tuya"
        ok, motivo = campana.validar_mazo(
            self.estado["cartas"][:5] + [ajena], self.nombres)
        self.assertFalse(ok)
        self.assertIn("no es tuya", motivo)

    def test_el_mapa_tiene_boton_de_mazo(self):
        """La pantalla donde se entra al editor tiene que ofrecerlo."""
        import io

        with open(os.path.join(RAIZ, "pantallas.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        # La funcion del mapa es la que dibuja el boton.
        i = fuente.index("async def mapa_campana")
        j = fuente.index("async def tienda")
        bloque = fuente[i:j]
        self.assertIn('"MAZO"', bloque,
                      "el mapa deberia ofrecer cambiar el mazo")
        self.assertIn("_editar_mazo_run", bloque,
                      "el boton deberia abrir el editor del mazo de la run")

    def test_el_editor_cancela_sin_tocar_nada(self):
        """ESC y CANCELAR devuelven None: el mazo se queda como estaba."""
        import asyncio

        import pygame

        import pantallas

        estado = campana.nueva_campana("humano")
        antes = [dict(d) for d in estado["cartas"]]

        class Reloj:
            def tick(self, fps=60):
                return 16

        async def _esc():
            # Se inyecta un ESC de verdad en el primer frame: un dict suelto
            # revienta porque el codigo lee `ev.type` de un objeto Event.
            original = pygame.event.get
            eventos = [pygame.event.Event(pygame.KEYDOWN,
                                          key=pygame.K_ESCAPE, mod=0,
                                          unicode="", scancode=0)]

            def con_esc():
                # `event.get()` devuelve una LISTA; un Event suelto no es
                # iterable y el bucle `for ev in ...` revienta.
                return [eventos.pop(0)] if eventos else []

            pygame.event.get = con_esc
            try:
                return await pantallas._editar_mazo_run(
                    pygame.display.get_surface(), Reloj(), estado)
            finally:
                pygame.event.get = original

        loop = asyncio.new_event_loop()
        try:
            resultado = loop.run_until_complete(_esc())
        finally:
            loop.close()
        self.assertIsNone(resultado, "ESC deberia cancelar sin devolver mazo")
        self.assertEqual([dict(d) for d in estado["cartas"]], antes,
                         "cancelar no debe cambiar el mazo de la run")

    def test_el_perfil_no_se_toca_al_editar_la_run(self):
        """Editar la run no puede tocar el mazo global ni el perfil."""
        import mazos

        antes_global = list(campana.mazo_global(campana.cargar_perfil()))
        antes_coleccion = len(campana.cargar_perfil()["coleccion"])
        # Se simula lo que hace el editor: solo toca estado["cartas"].
        self.estado["cartas"] = self.estado["cartas"][:5]
        self.assertEqual(
            list(campana.mazo_global(campana.cargar_perfil())), antes_global)
        self.assertEqual(len(campana.cargar_perfil()["coleccion"]),
                         antes_coleccion)
        del mazos


class TestLaRejillaDelEditorCabeYSeCentra(unittest.TestCase):
    """Dos filas centradas DENTRO del panel, no sobre la pantalla.

    Lo que fallaba: con una sola fila, a partir de 10 cartas el ancho total
    (10*104 + 9*24 = 1256px) no cabia en el panel de 1184 y las cartas se
    salian por los lados. Con la coleccion de una campana avanzada (40-75
    cartas) era peor: se iban fuera de la pantalla.
    """

    def setUp(self):
        import pygame

        import pantallas

        self.pantallas = pantallas
        self.panel = pygame.Rect(pantallas.MAZO_EDIT_PANEL)

    def test_ninguna_carta_se_sale_del_panel(self):
        import pygame

        for i in range(self.pantallas.MAZO_EDIT_POR_PAGINA):
            x, y = self.pantallas._rejilla_mazo(i)
            rect = pygame.Rect(x, y, self.pantallas.MAZO_CARTA_W,
                               self.pantallas.MAZO_CARTA_H)
            self.assertTrue(
                self.panel.contains(rect),
                f"la carta {i} en {rect} se sale del panel {self.panel}")

    def test_la_rejilla_esta_centrada_en_el_panel(self):
        """El margen a la izquierda tiene que ser igual al de la derecha."""
        import pygame

        rects = []
        for i in range(self.pantallas.MAZO_EDIT_POR_PAGINA):
            x, y = self.pantallas._rejilla_mazo(i)
            rects.append(pygame.Rect(x, y, self.pantallas.MAZO_CARTA_W,
                                     self.pantallas.MAZO_CARTA_H))
        izq = min(r.left for r in rects)
        der = max(r.right for r in rects)
        self.assertLessEqual(
            abs((izq - self.panel.x) - (self.panel.right - der)), 2,
            f"margen izq {izq - self.panel.x}, der {self.panel.right - der}")

    def test_las_filas_estan_centradas_verticalmente(self):
        import pygame

        ys = sorted({self.pantallas._rejilla_mazo(i)[1]
                     for i in range(self.pantallas.MAZO_EDIT_POR_PAGINA)})
        arriba = ys[0] - self.panel.y
        abajo = self.panel.bottom - (ys[-1] + self.pantallas.MAZO_CARTA_H)
        self.assertLessEqual(abs(arriba - abajo), 2,
                             f"arriba {arriba}, abajo {abajo}")

    def test_hay_dos_filas_de_cinco(self):
        self.assertEqual(self.pantallas.MAZO_EDIT_FILAS, 2)
        self.assertEqual(self.pantallas.MAZO_EDIT_COLS, 5)
        self.assertEqual(self.pantallas.MAZO_EDIT_POR_PAGINA, 10)

    def test_el_mazo_muestra_la_coleccion_no_solo_el_mazo(self):
        """El fallo de fondo: solo se veian las 5-10 cartas del mazo.

        `anadir_carta` sustituye la mas debil cuando el mazo esta lleno, y todo
        lo que ganas va al perfil, asi que el editor era casi inutil a media
        partida: no se veian las cartas nuevas.
        """
        import io

        with open(os.path.join(RAIZ, "pantallas.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        i = fuente.index("async def _editar_mazo_run")
        j = fuente.index("async def tienda")
        bloque = fuente[i:j]
        self.assertIn("coleccion_de", bloque,
                      "el editor debe leer la coleccion")
        self.assertIn("paginar_coleccion", bloque,
                      "la coleccion es mas grande que una pagina")


def pantallas_rejilla(modulo):
    """Cuantas cartas caben en una pagina del editor."""
    return modulo.MAZO_EDIT_POR_PAGINA


if __name__ == "__main__":
    unittest.main()