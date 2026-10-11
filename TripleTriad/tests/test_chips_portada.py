"""Los datos que la portada anuncia tienen que salir de los datos.

La portada muestra "N facciones" y "N duelos" en unos chips. Los tres
numeros que han pasado por ahi estaban escritos a mano y los tres acabaron
mal: "Siete facciones" (hay diez) y, tras un arreglo que empeoro el
anterior, "Seis duelos" (hay cinco: contar nodos del grafo cuenta tambien
la bifurcacion, que no es un duelo). Aqui se comprueba contra el grafo y
contra lo que la pantalla pinta de verdad.
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


def _cargar_herramienta():
    tmp = tempfile.TemporaryDirectory(prefix="tt_chips_")
    os.environ["TRIPLETRIAD_DATA"] = tmp.name
    ruta = os.path.join(RAIZ, "tools", "auditar_texto_ampliado.py")
    spec = importlib.util.spec_from_file_location("auditar_texto_ampliado_chips", ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["auditar_texto_ampliado_chips"] = mod
    spec.loader.exec_module(mod)
    mod._TMP = tmp
    return mod


class TestChipsDePortada(unittest.TestCase):

    def setUp(self):
        import pygame

        self.mod = _cargar_herramienta()
        pygame.init()
        self.mod.pantalla = pygame.display.set_mode((1280, 800))
        self.mod.ui.fijar_escala_texto(1.0)
        self.addCleanup(self.mod.ui.fijar_escala_texto, 1.0)

    def test_duelos_por_campana_coincide_con_el_grafo(self):
        """El numero tiene que salir de recorrer NODOS, no de una cuenta mental."""
        import campana

        self.assertEqual(5, campana.duelos_por_campana())

        # Comprobacion independiente: se recorre el grafo como lo hace el juego
        # (la clave de la opcion ES el nodo siguiente) y se cuentan los nodos
        # de tipo duelo o final. Si los dos caminos no coinciden, el helper
        # miente.
        for rama in sorted(campana.NODOS["bifurcacion"]["opciones"]):
            nodo, ruta = "senda", []
            while nodo:
                d = campana.NODOS[nodo]
                ruta.append((nodo, d["tipo"]))
                if d["tipo"] == "eleccion":
                    nodo = rama
                else:
                    nodo = d["siguiente"]
            reales = [n for n, t in ruta if t in ("duelo", "final")]
            self.assertEqual(len(reales), campana.duelos_por_campana(),
                             f"la rama {rama} tiene {len(reales)} duelos")

    def test_la_bifurcacion_no_cuenta_como_duelo(self):
        import campana

        self.assertEqual("eleccion", campana.NODOS["bifurcacion"]["tipo"])
        # El numero de duelos es menor que el de nodos del grafo: si alguna vez
        # se igualan, es que algo esta contando la eleccion como duelo.
        self.assertLess(campana.duelos_por_campana(), len(campana.NODOS))

    def test_portada_pinta_los_datos_reales(self):
        """Lo que se ve en pantalla, no lo que deberia verse."""
        import campana
        import facciones

        mod = self.mod
        mod.AV.correr_pantalla("portada_chips",
                               lambda: mod.AV.pantallas.portada(mod.pantalla,
                                                                mod.AV.RelojFalso()))
        dibujado = [c for c, _r in mod.AV.textos_de_frame(0)]
        esperados = [
            f"{len(facciones.orden_facciones())} facciones",
            f"{campana.duelos_por_campana()} duelos",
            "Un final por faccion",
        ]
        for chip in esperados:
            self.assertIn(chip, dibujado,
                          f"la portada no pinta {chip!r}; dibuja {dibujado}")

    def test_los_chips_caben_dentro_de_su_panel(self):
        """Cada chip tiene que quedar dentro del panel que lo dibuja.

        El ancho del chip no se escalaba con la tipografia, asi que al 125% el
        texto ya se salia de su borde (209px de texto en un chip de 200). Se
        comprueba contra el panel real que registra la auditoria, no contra un
        ancho fijo en el test.
        """
        mod = self.mod
        for escala in (1.0, 1.25, 1.6):
            mod.ui.fijar_escala_texto(escala)
            frames = mod.AV.correr_pantalla(
                "portada_chips",
                lambda: mod.AV.pantallas.portada(mod.pantalla, mod.AV.RelojFalso()))
            dibujado = mod.AV.textos_de_frame(0)
            # La banda de chips va en y=250 con 40 de alto.
            for cadena, rect in dibujado:
                if not (245 <= rect.centery <= 275):
                    continue
                # Busca el panel mas pequeno que contenga el texto.
                marco = None
                for r2, _rol2, cont in frames[0]:
                    if cont is not None and cont.contains(rect):
                        if marco is None or cont.w * cont.h < marco.w * marco.h:
                            marco = cont
                self.assertIsNotNone(
                    marco,
                    f"el texto {cadena!r} (escala {escala}) no cae dentro de "
                    f"ningun panel: se sale del chip")
                self.assertTrue(
                    marco.contains(rect),
                    f"el texto {cadena!r} se sale de su chip {marco} "
                    f"(escala {escala}, texto {rect.w}px)")


if __name__ == "__main__":
    unittest.main()
