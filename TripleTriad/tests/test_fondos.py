"""Los fondos de pantalla se muestran tal cual los genero la IA.

Los fondos son de 512x256 (2:1) y la pantalla de 1280x800 (1,6:1). Cualquier
escala fraccionaria funde pixeles vecinos y difumina los bordes: el mundo se ve
pixelado y borroso a la vez. Aqui no se inventa ni un solo pixel: se elige el
factor ENTERO que mejor ocupa la pantalla, se escala con vecino mas cercano y
se recorta el sobrante del eje largo.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tt_test_fondo")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

import ui  # noqa: E402

RUTA_FONDO = "assets/fondos/trono.png"


def setUpModule():
    pygame.init()
    pygame.display.set_mode((ui.ANCHO, ui.ALTO))


class TestFactorEntero(unittest.TestCase):
    def test_gana_el_tres_que_es_el_que_menos_desperdicia(self):
        """512x256 en 1280x800: x3 da 1536x768, 32px de letra y nada de lados.

        Con x2 (1024x512) el 49% de la pantalla queda en negro a los lados.
        """
        self.assertEqual(ui.REC._mejor_factor(512, 256, ui.ANCHO, ui.ALTO), 3)

    def test_nunca_deja_mas_de_un_10_de_la_pantalla_vacia(self):
        """Se mide el area REAL cubierta, no la suma de bordes.

        Un fondo cuadrado (256x256) con factor 4 son 1024x1024: cubre toda la
        altura y deja 256px de franja a los lados. Se recorta por alto, que es
        lo barato, y se deja la franja lateral, que es la cara.
        """
        for bw, bh in ((512, 256), (256, 256), (1280, 800), (640, 360)):
            with self.subTest(fondo=(bw, bh)):
                f = ui.REC._mejor_factor(bw, bh, ui.ANCHO, ui.ALTO)
                nw, nh = min(bw * f, ui.ANCHO), min(bh * f, ui.ALTO)
                cubierta = 100.0 * nw * nh / (ui.ANCHO * ui.ALTO)
                self.assertGreaterEqual(
                    cubierta, 90.0,
                    f"factor {f}: solo cubre el {cubierta:.0f}% de la pantalla")

    def test_el_factor_siempre_es_entero_y_al_menos_uno(self):
        for bw in range(32, 1024, 37):
            for bh in range(32, 1024, 53):
                f = ui.REC._mejor_factor(bw, bh, ui.ANCHO, ui.ALTO)
                self.assertIsInstance(f, int)
                self.assertGreaterEqual(f, 1)


class TestEscaladoSinInventarPixeles(unittest.TestCase):
    def test_la_imagen_entra_exacta_en_la_pantalla(self):
        base = pygame.Surface((512, 256))
        base.fill((10, 20, 30))
        out = ui.REC._escalar_pixelart(base, (ui.ANCHO, ui.ALTO))
        self.assertEqual((out.get_width(), out.get_height()), (ui.ANCHO, ui.ALTO))

    def test_el_letterbox_se_recibe_y_nunca_es_negativo(self):
        """`barras_de` es lo que consulta la cinematica para no pintar dos
        marcos encima. Si devuelve negativo, la escena se queda sin marco."""
        v, h = ui.REC.barras_de(RUTA_FONDO)
        self.assertGreaterEqual(v, 0)
        self.assertGreaterEqual(h, 0)

    def test_el_letterbox_no_se_hereda_de_una_imagen_muerta(self):
        """La clave es la RUTA, no `id(imagen)`.

        Con `id()`, CPython reutiliza el identificador de un objeto liberado, y
        una imagen nueva podia heredar el letterbox de otra que ya no existia.
        Se reproducia: `test_una_imagen_ya_a_pantalla_no_deja_letra` fallaba
        segun el orden de los tests, nunca al ejecutarlo solo.
        """
        for _ in range(50):
            basura = pygame.Surface((ui.ANCHO, ui.ALTO))
            del basura
        # Primero se carga: hasta entonces no hay letterbox registrado y la
        # consulta devuelve el valor por defecto, que no es lo que se prueba.
        ui.REC.fondo_pantalla(RUTA_FONDO)
        antes = ui.REC.barras_de(RUTA_FONDO)
        for _ in range(50):
            basura = pygame.Surface((ui.ANCHO, ui.ALTO))
            del basura
        self.assertEqual(antes, ui.REC.barras_de(RUTA_FONDO),
                         "el letterbox cambio al liberar otras superficies")

    def test_una_imagen_ya_a_pantalla_no_deja_letra(self):
        base = pygame.Surface((ui.ANCHO, ui.ALTO))
        out = ui.REC._escalar_pixelart(base, (ui.ANCHO, ui.ALTO))
        self.assertEqual(out.get_size(), (ui.ANCHO, ui.ALTO))
        # La firma real es por ruta; una ruta desconocida no inventa letra.
        self.assertEqual(ui.REC.barras_de("no/existe.png"), (0, 0))

    def test_cada_pixel_original_es_un_bloque_nitido(self):
        """Un unico pixel blanco: con factor 3 sale un bloque de 3x3 limpio.

        Con `smoothscale` el bloque sale degradado por los bordes. Esto mide el
        resultado de verdad, no la manera de escalarlo.

        512x256 con factor 3 son 1536x768. El recorte se lleva (1536-1280)/2 = 128px
        a cada lado, y en vertical la imagen (768) NO llega a 800: se centra con
        16px de letra arriba y abajo. El pixel central del original (256,128)
        ocupa el bloque 640..642 x 400..402 en pantalla: 3x3 exactos.
        """
        base = pygame.Surface((512, 256))
        base.fill((0, 0, 0))
        base.set_at((256, 128), (255, 255, 255))
        out = ui.REC._escalar_pixelart(base, (ui.ANCHO, ui.ALTO))
        ex, ey = 640, 400
        # El pixel original ocupa un bloque de 3x3 entero: los tres pixeles de
        # ancho y los tres de alto, sin borde degradado.
        for dx in (0, 1, 2):
            for dy in (0, 1, 2):
                self.assertEqual(
                    out.get_at((ex + dx, ey + dy)), (255, 255, 255, 255),
                    f"el bloque 3x3 deberia ser blanco entero en ({dx},{dy})")
        # Y justo fuera del bloque ya es negro: borde duro, no difuminado.
        for dx in (-1, 3):
            self.assertEqual(out.get_at((ex + dx, ey)), (0, 0, 0, 255),
                             "el borde del bloque deberia ser duro")

    def test_no_hay_pixeles_intermedios_entre_el_bloque_y_el_fondo(self):
        """Nada de valores intermedios: o blanco o negro, nunca gris.

        Esta es LA prueba de que no se ha reescalado "raro": un interpolador
        siempre deja tonos entre los dos colores del borde del bloque.
        """
        base = pygame.Surface((512, 256))
        base.fill((0, 0, 0))
        base.set_at((256, 128), (255, 255, 255))
        out = ui.REC._escalar_pixelart(base, (ui.ANCHO, ui.ALTO))
        ex, ey = 640, 400
        for dx in range(-6, 7):
            for dy in range(-6, 7):
                v = out.get_at((ex + dx, ey + dy))[:3]
                self.assertIn(v, ((0, 0, 0), (255, 255, 255)),
                              f"pixel ({dx},{dy}) = {v}: esta difuminado")


class TestFondosReales(unittest.TestCase):
    """Sobre los 15 PNG de verdad, no sobre superficies de laboratorio."""

    def test_todos_los_fondos_entran_y_avisan_de_su_letra(self):
        import os as _os
        carpeta = _os.path.join(RAIZ, "assets", "fondos")
        nombres = sorted(n for n in _os.listdir(carpeta) if n.endswith(".png"))
        self.assertGreaterEqual(len(nombres), 11)
        for nombre in nombres:
            with self.subTest(fondo=nombre):
                ruta = f"assets/fondos/{nombre}"
                fondo = ui.REC.fondo_pantalla(ruta)
                self.assertEqual((fondo.get_width(), fondo.get_height()),
                                 (ui.ANCHO, ui.ALTO))
                v, h = ui.REC.barras_de(ruta)
                self.assertGreaterEqual(v, 0)
                self.assertGreaterEqual(h, 0)
                # Ningun fondo puede dejar mas de un 12% de la altura vacia.
                self.assertLessEqual(v, ui.ALTO * 0.12)

    def test_escalar_por_frame_seria_una_catastrofe(self):
        """Por que el escalado va en la cache y no en el bucle.

        `smoothscale` es algo mas rapido que escalar a 1536x768 y recortar, asi
        que el coste por llamada NO es la siguiente nota. La nota siguiente es
        que esto pasa UNA vez: si se hiciera por frame, con 60 fps serian
        ~180ms de CPU por segundo solo en el fondo, y ademas se reservaria una
        Surface de 1280x800 por frame (4 MB, ~240 MB/s).
        """
        base = pygame.Surface((512, 256))
        base.fill((30, 40, 50))

        uno = ui.REC.fondo_pantalla(RUTA_FONDO)
        dos = ui.REC.fondo_pantalla(RUTA_FONDO)
        # ESTA es la invariante real: la segunda llamada no reescala nada.
        # Un test que mida milisegundos y compare con 16,7 es fragil: falla
        # cuando la maquina va cargada y no dice nada del codigo. Este dice
        # exactamente lo que importa y no puede fallar por ir con prisa.
        self.assertIs(uno, dos, "sin cache se reescala en cada frame")
        self.assertEqual((uno.get_width(), uno.get_height()), (ui.ANCHO, ui.ALTO))


if __name__ == "__main__":
    unittest.main()