"""G7: el modo lectura (texto ampliado) no puede romper ninguna pantalla.

La auditoria visual de siempre mide los rects a tamano NORMAL, asi que todo
pasaba: el unico sitio donde se vio un problema fue mirando una captura del
diario a ojo. Este test ejecuta la misma auditoria con la escala de tipografia
al 125%, que es lo que hace el jugador al activar TEXTO GRANDE en Ajustes.

Salen dos fallos reales cuando se ejecuta asi:
  - la portada solapaba las dos lineas del titulo,
  - la etiqueta de estado de la ultima fila de la coleccion caia encima del
    boton de pagina.
Los dos pasaban a tamano normal porque el solapamiento era de 2 px y no lo
devolvaba la tolerancia de la auditoria.
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
sys.path.insert(0, os.path.join(RAIZ, "tools"))

RUTA = os.path.join(RAIZ, "tools", "auditar_texto_ampliado.py")


def _juego(bando, rival, seleccionada=False, cpu=False):
    """Juego de duelo en un estado que pinte texto representativo."""
    import partida

    j = partida.Juego(bando, rival)
    if seleccionada:
        j.turno_cpu = True
        j.seleccionada = j.mano_u[0]
        j.mensaje = "Muro bloquea el lado norte: no se puede capturar"
    if cpu:
        j.cpu_en_curso = True
        j.mensaje = "Turno rival. Piensa tu siguiente jugada."
    return j


def _cargar():
    tmp = tempfile.TemporaryDirectory(prefix="tt_texto_amp_")
    os.environ["TRIPLETRIAD_DATA"] = tmp.name
    spec = importlib.util.spec_from_file_location("auditar_texto_ampliado", RUTA)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["auditar_texto_ampliado"] = mod
    spec.loader.exec_module(mod)
    mod._TMP = tmp
    return mod


class TestTextoAmpliadoNoRompelaNada(unittest.TestCase):
    """Cada pantalla se audita por separado para que el fallo diga cual es.

    Se prueban las DOS escalas que importan: 1.25, que es lo que pone el ajuste
    TEXTO GRANDE, y 1.6, que es el techo que admite `ui.fijar_escala_texto`.
    Auditar solo el 125% daba un falso "todo bien": al 160% la portada
    solapaba sus dos lineas de titulo y la ficha de faccion montaba el bloque
    HABILIDADES encima de los chips de rivales.
    """

    ESCALAS = (1.25, 1.6)

    #: (etiqueta, funcion de dibujo) en el mismo formato que usa la herramienta.
    def _pantallas(self, mod):
        import campana
        import facciones
        import mazos
        import narrativa
        import partida

        est = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        campana.guardar(est)
        sc = mod.AV.pantallas
        R = mod.AV.RelojFalso
        return [
            ("portada", lambda: sc.portada(mod.pantalla, R())),
            ("menu", lambda: sc.menu(mod.pantalla, R(), est)),
            ("mapa_campana", lambda: sc.mapa_campana(mod.pantalla, R(), est)),
            ("coleccion", lambda: sc.coleccion(mod.pantalla, R(), est)),
            ("tienda", lambda: sc.tienda(mod.pantalla, R(), est)),
            ("ajustes", lambda: sc.ajustes(mod.pantalla, R())),
            ("recompensa", lambda: sc.recompensa(mod.pantalla, R(), est, "fortaleza")),
            ("encuentro", lambda: sc.encuentro(mod.pantalla, R(), est, "ruinas")),
            ("elegir_faccion", lambda: sc.elegir_faccion(mod.pantalla, R())),
            ("elegir_faccion_rapida", lambda: sc.elegir_faccion(
                mod.pantalla, R(), modo="rapida")),
            # La ficha lateral cambia con la faccion: lema, arco y numero de
            # habilidades. Auditar solo la primera no cubria nada, y al 160%
            # las de nombre largo montaban "jefe:" sobre el nombre.
            *[("ficha_" + f, (lambda ff: lambda: sc.elegir_faccion(
                mod.pantalla, R(), facciones_disponibles=[ff]))(f))
              for f in facciones.orden_facciones()],
            ("elegir_rama", lambda: sc.elegir_rama(mod.pantalla, R(), est)),
            ("draft", lambda: sc.draft(mod.pantalla, R(), est)),
            ("armar_mazo", lambda: sc.armar_mazo(mod.pantalla, R(), "humano")),
            ("revelar_sobre", lambda: sc.revelar_sobre(
                mod.pantalla, R(), [mazos.HUMANOS[1]], [mazos.HUMANOS[0]])),
            ("diario_dialogos", lambda: sc.diario_dialogos(mod.pantalla, R(), est)),
            ("derrota", lambda: sc.derrota(mod.pantalla, R(), est)),
            # El duelo es la pantalla principal y no estaba auditada. Se
            # montan tres estados porque cada uno pinta texto distinto: con
            # carta seleccionada, con el turno de la CPU y con la ayuda.
            ("duelo_seleccion", lambda: partida.partida(
                mod.pantalla, R(), _juego("humano", "orco", seleccionada=True))),
            ("duelo_turno_cpu", lambda: partida.partida(
                mod.pantalla, R(), _juego("humano", "orco", cpu=True))),
            ("pantalla_ayuda", lambda: sc._pantalla_ayuda(mod.pantalla, R())),
            ("cartel_error", lambda: sc.cartel(
                mod.pantalla, R(), "SIN RECURSOS",
                "No se pudo cargar el audio. El juego sigue sin sonido.")),
            ("pantalla_error", lambda: sc.pantalla_error(
                mod.pantalla, R(), RuntimeError("fallo de prueba"),
                "Traceback de prueba", "arranque")),
            ("epilogo", lambda: sc.epilogo(mod.pantalla, R(), est)),
        ]

    def setUp(self):
        import pygame

        self.mod = _cargar()
        pygame.init()
        self.mod.pantalla = pygame.display.set_mode((1280, 800))
        self.mod.opciones.fijar("texto_grande", True)
        self.addCleanup(self.mod.ui.fijar_escala_texto, 1.0)

    def _auditar(self, escala):
        self.mod.ui.fijar_escala_texto(escala)
        fallos = []
        for nombre, fn in self._pantallas(self.mod):
            frames = self.mod.AV.correr_pantalla(nombre, fn)
            if self.mod.AV.ERRORES:
                # Una pantalla que peta no dibuja rects: sin esto se camuflaba
                # como pantalla limpia.
                fallos.append((nombre, [f"ERROR al dibujar: {self.mod.AV.ERRORES}"]))
                continue
            if not frames:
                fallos.append((nombre, ["no se capturo ningun frame"]))
                continue
            problemas = self.mod.AV.auditar_rects(nombre, frames)
            if problemas:
                fallos.append((nombre, problemas[:2]))
        return fallos

    def test_ajuste_texto_grande_no_rompe_ninguna_pantalla(self):
        fallos = self._auditar(1.25)
        self.assertEqual([], fallos, self._detalle(fallos))

    def test_techo_de_escala_no_rompe_ninguna_pantalla(self):
        fallos = self._auditar(1.6)
        self.assertEqual([], fallos, self._detalle(fallos))

    @staticmethod
    def _detalle(fallos):
        if not fallos:
            return ""
        return "desbordes:\n  " + "\n  ".join(f"{n}: {p}" for n, ps in fallos for p in ps)

    def test_alto_texto_mide_la_linea_real(self):
        """`ui.alto_texto` tiene que devolver el alto de verdad, no una guess.

        El interlinea y las separaciones de la portada dependen de este valor.
        Con una aproximacion tipo `tam * 1.28` el hueco se quedaba corto al
        160% y las dos lineas del titulo se solapaban.
        """
        ui = self.mod.ui
        for escala in self.ESCALAS:
            ui.fijar_escala_texto(escala)
            for tam in (7, 8, 10, 12, 40):
                img, _, _ = ui._superficie_texto("MMM", tam, ui.TEXTO, False)
                self.assertEqual(
                    img.get_height(), ui.alto_texto("MMM", tam),
                    f"alto_texto miente a escala {escala}, tam {tam}")
        self.assertGreater(ui.alto_texto("MMM", 40) * 1.5,
                           ui.alto_texto("MMM", 20),
                           "la escala de texto deberia agrandar la linea")

    def test_lineas_de_un_parrafo_no_se_pisan(self):
        """Con el modo lectura, dos lineas consecutivas no deben tocarse.

        El interlinea de `ui.parrafo` se avanza en pixeles fijos mientras la
        linea crece con la escala. Medido: a tamano 7 y escala 1.6 la linea se
        dibuja a 12 px de alto pero avanzaba 11, y las lineas se montaban una
        sobre otra. La auditoria general no lo ve (su tolerancia de 2 px),
        asi que esta mide la propiedad directamente sobre lo dibujado.
        """
        import pygame

        ui = self.mod.ui
        # `ui.MEDIR` lo enciende `auditoria_visual` al importarse, pero otros
        # tests de la suite lo toquen. Aqui se fuerza y se restaura.
        medir_previo = ui.MEDIR
        ui.MEDIR = True
        self.addCleanup(setattr, ui, "MEDIR", medir_previo)
        largo = ("Esta es una descripcion de habilidad deliberadamente larga "
                 "para que se reparta en varias lineas dentro del panel")
        for escala in self.ESCALAS:
            ui.fijar_escala_texto(escala)
            ui.limpiar_medicion()
            ui.parrafo(pygame.display.get_surface(), largo, 7, ui.TEXTO,
                       40, 40, 220, interlinea=11)
            rects = [r for r, rol, _c in ui._REGISTRO if rol == "texto"]
            self.assertGreaterEqual(len(rects), 2,
                                    "el texto deberia partirse en varias lineas")
            for a, b in zip(rects, rects[1:]):
                self.assertFalse(
                    b.top < a.bottom,
                    f"linea {b} se monta sobre la anterior {a} con escala {escala}")