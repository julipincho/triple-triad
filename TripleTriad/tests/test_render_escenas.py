"""Tests de RENDER de escenas, no solo de texto.

Por que existe
--------------
El juego se cerraba entero contra cualquier rival: `duelistas._esc` y
`finales.esc` tienenian `color=None` por defecto, y `ui._superficie_texto` hace
`len(color)`. La escena se construia bien, el texto pasaba el chequeo de salto
de linea, y recien al PINTAR la escena reventaba con `len(None)`.

La leccion: medir el texto no es renderizar el texto. Un audit que solo mira
`envoltura_lineas` da verde sobre una pantalla que no se puede ver. Estos tests
pintan cada escena de verdad contra una Surface y fallan si algo revienta.

Con un `color=None` colado, el crash ocurre en el `blit`, no antes, asi que el
test tiene que llegar hasta `_dibujar`.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_render")
)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

from ui import ALTO, ANCHO  # noqa: E402

pygame.init()
pygame.display.set_mode((ANCHO, ALTO))

import campana  # noqa: E402
import cinematicas  # noqa: E402
import duelistas  # noqa: E402
import finales  # noqa: E402
import narrativa  # noqa: E402
import prologo  # noqa: E402

SUPERFICIE = pygame.Surface((ANCHO, ALTO))
NODOS = ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono")


def pintar(escenas):
    """Pinta cada escena de verdad. Devuelve la lista de fallos."""
    cine = cinematicas.Cinematica(escenas)
    fallos = []
    for i, escena in enumerate(cine.escenas):
        escena.mostrado = 999  # texto entero, no la animacion de escritura
        try:
            cine._dibujar(SUPERFICIE, escena, 1.0)
        except Exception as ex:  # noqa: BLE001 - aca el fallo es el dato
            fallos.append((i, escena.texto[:40], repr(ex)))
    return fallos


class TestNingunColorLlegaComoNone(unittest.TestCase):
    """La causa raiz: dos constructores de escena con `color=None`."""

    def _revisar(self, escenas, donde):
        for e in escenas:
            self.assertIsNotNone(
                e.get("color"),
                "%s: escena con color=None -> %r. ui._superficie_texto hace "
                "len(color) y tumba la pantalla." % (donde, e.get("texto", "")[:40]))

    def test_el_rival_siempre_tiene_color(self):
        for nodo in NODOS:
            for momento in ("pre", "win", "lose"):
                self._revisar(duelistas.dialogo_de(nodo, momento, "Gruk"),
                              "duelistas %s/%s" % (nodo, momento))

    def test_los_finales_siempre_tienen_color(self):
        for v in ("dominio", "equilibrio", "caos"):
            self._revisar(finales.escenas_umbral(v), "umbral " + v)
            self._revisar(finales.escenas_epilogo(v), "epilogo " + v)

    def test_escena_normaliza_el_color_igual(self):
        """`cinematicas.Escena` es el cuello de botella: normaliza aunque el
        productor se pase con un None."""
        from ui import TEXTO
        for color in (None, TEXTO, (255, 0, 0)):
            e = cinematicas.Escena({"texto": "x", "color": color})
            self.assertIsNotNone(e.color)
        # Y una escena sin la clave tampoco
        self.assertIsNotNone(cinematicas.Escena({"texto": "x"}).color)

    def test_la_ui_no_revienta_con_un_color_ausente(self):
        from ui import texto
        # No debe lanzar. Este es el piso: la UI no es donde un dato
        # incompleto se convierte en un crash.
        texto(SUPERFICIE, "sigue vivo", 10, None)


class TestTodasLasEscenasSePintan(unittest.TestCase):
    """El test que habria atrapado el crash de la primera vez."""

    def _comprobar(self, nombre, escenas):
        fallos = pintar(escenas)
        self.assertEqual([], fallos, "%s: %d escenas no se pudieron pintar"
                         % (nombre, len(fallos)))

    def test_el_cartel_de_duelo_de_cada_rival(self):
        """Esto es lo que revienta en juego: el cartel antes del duelo."""
        for nodo in NODOS:
            for momento in ("pre", "win", "lose"):
                self._comprobar("duelistas %s/%s" % (nodo, momento),
                                duelistas.dialogo_de(nodo, momento, "Gruk"))

    def test_los_tres_finales_completos(self):
        """La campana no se podia TERMINAR: el umbral y el epilogo pintaban con
        color=None."""
        for v in ("dominio", "equilibrio", "caos"):
            self._comprobar("umbral " + v, finales.escenas_umbral(v))
            self._comprobar("epilogo " + v, finales.escenas_epilogo(v))

    def test_el_prologo_entero(self):
        for nombre in ("escenas_pre_duelo", "escenas_post_duelo",
                       "escenas_carta_umbral", "escenas_transporte",
                       "escenas_despertar", "escenas_encuentro_hostil",
                       "escenas_nara", "escenas_explicacion", "escenas_cierre"):
            self._comprobar("prologo." + nombre, getattr(prologo, nombre)())

    def test_la_narrativa_de_cada_nodo(self):
        for nodo in NODOS:
            self._comprobar("previa " + nodo, narrativa.previa_nodo(nodo))
            self._comprobar("posterior " + nodo, narrativa.posterior_nodo(nodo))

    def test_el_cartel_previo_al_duelo_real_de_cada_nodo_y_faccion(self):
        """Se arma con `campana.info_duelo`, que es lo que pasa en juego."""
        import facciones
        for fac in facciones.orden_facciones():
            estado = campana.nueva_campana(fac)
            for nodo in NODOS:
                info = campana.info_duelo(estado, nodo)
                escenas, musica = cinematicas.escenas_nodo(info)
                # con el cartel del nodo, el dialogo del rival y la voz de Nara
                for e in escenas:
                    e["fondo"] = info.get("escena", "campamento")
                self._comprobar("cartel %s/%s" % (fac, nodo), escenas)
                self._comprobar("posterior %s/%s" % (fac, nodo),
                                cinematicas.escenas_posterior(info, True))
                self._comprobar("posterior-perdida %s/%s" % (fac, nodo),
                                cinematicas.escenas_posterior(info, False))


if __name__ == "__main__":
    unittest.main()