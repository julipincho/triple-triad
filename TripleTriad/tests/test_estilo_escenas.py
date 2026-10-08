"""Tests del set de estilo anime y del generador de escenas.

Dos garantias importantes:
  1. Este set NO toca el pipeline de cartas. Hay tests que lo verifican leyendo
     los archivos: si alguien mete un `postprocesar_cartas` en el camino anime,
     fallan.
  2. El pixel sale de reducir con vecino mas cercano, no de un filtro. Y el
     negativo prohibe explicitamente scanlines y dithering.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests")
)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import estilo
import estilo_escenas as est


class TestNoTocaElPipelineDeCartas(unittest.TestCase):
    """La condicion principal: las cartas siguen por su camino."""

    def test_el_checkpoint_es_el_de_pixel_art(self):
        """Cambio medido: el checkpoint de pixel art es el correcto para este set.

        Se probo tambien Animagine XL 4.0 y devolvia anime posterizado, sin pixel
        art, aunque se lo pidiera en el prompt. El SpriteShaper con prompt anime
        si da pixel art real. Ver el docstring de `estilo_escenas`.
        """
        import generar_cartas_comfyui as comfy
        self.assertEqual(est.CHECKPOINT, comfy.CHECKPOINT)
        self.assertEqual(est.CHECKPOINT,
                         "pixelArtDiffusionXL_spriteShaper.safetensors")

    def test_lo_que_se_reutiliza_es_el_modelo_no_el_postproceso(self):
        """Compartir checkpoint es correcto; compartir el filtro CRT no."""
        import generar_cartas_comfyui as comfy
        with open(os.path.join(RAIZ, "generar_escenas.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        for malo in ("postprocesar", "crt", "scanline"):
            for linea in fuente.splitlines():
                limpio = linea.strip()
                if limpio.startswith(("import ", "from ")):
                    self.assertNotIn(malo, limpio.lower(), limpio)

    def test_no_reutiliza_la_ficha_de_las_cartas(self):
        """Cada set tiene su ficha: la de cartas sigue siendo la del moodboard."""
        self.assertNotEqual(est.RUTA_FICHA, estilo.RUTA_FICHA)

    def test_la_paleta_no_es_la_de_las_cartas(self):
        self.assertNotEqual(list(est.PALETA), list(estilo.PALETA))
        self.assertTrue(est.PALETA, "este set deberia traer paleta propia")

    def test_no_importa_el_postproceso_de_cartas(self):
        """`postprocesar_cartas.py` mete scanlines: justo lo que no queremos.

        Se busca el IMPORT, no la palabra: el docstring menciona el archivo a
        proposito, para explicar por que no se usa.
        """
        with open(os.path.join(RAIZ, "generar_escenas.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        for linea in fuente.splitlines():
            limpio = linea.strip()
            if limpio.startswith(("import ", "from ")):
                self.assertNotIn("postprocesar_cartas", limpio, limpio)

    def test_no_importa_el_generador_de_cartas_como_modulo_de_estilo(self):
        """Del pipeline de cartas solo se reusa el TRANSPORTE."""
        with open(os.path.join(RAIZ, "generar_escenas.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        self.assertIn("import generar_cartas_comfyui as comfy", fuente)
        # y no llama a su logica de prompt
        for prohibido in ("comfy.construir_prompt", "comfy.ESTILOS", "comfy.FIJO"):
            self.assertNotIn(prohibido, fuente, prohibido)


class TestIpAdapterApagado(unittest.TestCase):
    """El ancla de las cartas impondría el tinte apagado que hay que quitar."""

    def test_ipadapter_desactivado(self):
        self.assertFalse(est.USAR_IPADAPTER)

    def test_peso_cero(self):
        self.assertEqual(est.PESO_IPADAPTER, 0.0)

    def test_la_validacion_lo_detecta(self):
        """Si alguien lo activa, el modulo se queja en vez de fallar en silencio."""
        self.assertEqual(est._validar(), [])
        est.USAR_IPADAPTER = True
        try:
            errores = est._validar()
            self.assertTrue(any("ancla" in e for e in errores),
                            f"no lo detecto: {errores}")
        finally:
            est.USAR_IPADAPTER = False

    def test_ningun_prompt_recibe_el_ancla(self):
        with open(os.path.join(RAIZ, "generar_escenas.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        self.assertIn("ancla=None", fuente)


class TestEncuadresYMedidas(unittest.TestCase):
    def test_cada_encuadre_tiene_medidas(self):
        for clave in est.ENCUADRES:
            self.assertIn(clave, est.MEDIDAS, clave)

    def test_cada_medida_tiene_encuadre(self):
        for clave in est.MEDIDAS:
            self.assertIn(clave, est.ENCUADRES, clave)

    def test_el_modulo_es_coherente(self):
        self.assertEqual(est._validar(), [])

    def test_las_medidas_son_las_que_usa_el_juego(self):
        """Verificadas con Pillow sobre los assets reales."""
        self.assertEqual(est.MEDIDAS["retrato"], (256, 256))
        self.assertEqual(est.MEDIDAS["fondo"], (512, 256))

    def test_se_genera_a_un_multiplo_del_destino(self):
        self.assertGreaterEqual(est.ESCALA_GENERACION, 2)
        w, h = est.MEDIDAS["retrato"]
        self.assertEqual((w * est.ESCALA_GENERACION) % w, 0)


class TestPrompts(unittest.TestCase):
    def test_el_prompt_no_repite_el_encuadre(self):
        """El sujeto y el encuadre se complementan; no se solapan."""
        sujeto = "1boy, back view, from behind, hooded long coat, face hidden"
        p = est.construir_prompt(sujeto, encuadre="silueta")
        self.assertEqual(p.count("back view"), 1, "back view repetido")
        self.assertEqual(p.count("from behind"), 1, "from behind repetido")

    def test_trae_los_tags_de_calidad_de_animagine(self):
        p = est.construir_prompt("1girl, scholar")
        self.assertIn("masterpiece", p)
        self.assertIn("best quality", p)

    def test_el_encuadre_entra_en_el_prompt(self):
        for clave in est.ENCUADRES:
            p = est.construir_prompt("1girl, scholar", encuadre=clave)
            self.assertIn(est.ENCUADRES[clave], p, clave)

    def test_el_estilo_entra_en_el_prompt(self):
        for clave in est.ESTILOS:
            p = est.construir_prompt("1girl, scholar", estilo=clave)
            self.assertIn(est.ESTILOS[clave], p, clave)

    def test_la_faccion_aporta_ambiente(self):
        for faccion, ambiente in est.FACCION_VISUAL.items():
            p = est.construir_prompt("1girl, scholar", faccion=faccion)
            self.assertIn(ambiente, p, faccion)

    def test_el_extra_se_suma(self):
        p = est.construir_prompt("1girl", extra="warm lantern light")
        self.assertIn("warm lantern light", p)

    def test_encuadre_inesconocido_no_rompe(self):
        p = est.construir_prompt("1girl", encuadre="inventado")
        self.assertTrue(p)
        self.assertIn(est.ENCUADRES["retrato"], p)

    def test_avisa_si_el_prompt_trae_acentos(self):
        """El prompt va al modelo, que esta entrenado en ingles. Un acento
        desperdicia tokens y arruina la imagen: se avisa en vez de colarlo."""
        import warnings
        con_acentos = "luz cálida"
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            est.construir_prompt("1girl", extra=con_acentos)
        mensajes = [str(x.message).lower() for x in w]
        self.assertTrue(mensajes, "no aviso de los acentos")
        self.assertTrue(any("ingles" in m for m in mensajes), mensajes)

    def test_un_prompt_limpio_no_avisa(self):
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            est.construir_prompt("1girl, scholar", faccion="vampiro",
                                 extra="warm lantern light")
        self.assertEqual([str(x.message) for x in w], [])

    def test_los_prompts_del_catalogo_son_ascii(self):
        """La garantia que importa: lo que se manda de verdad esta limpio."""
        import generar_escenas as g
        for clave, e in g.CATALOGO.items():
            p = est.construir_prompt(e["sujeto"], encuadre=e["encuadre"],
                                     extra=e.get("extra", ""))
            for ch in p:
                self.assertLessEqual(ord(ch), 127, f"{clave}: {ch!r}")


class TestElNegativoQuitaLoQueNoQueremos(unittest.TestCase):
    def test_prohibe_lo_psx(self):
        """Sin scanlines, sin CRT, sin dithering: eso es el filtro de cartas."""
        n = est.construir_negativo()
        self.assertIn("scanlines", n)
        self.assertIn("CRT screen", n)
        self.assertIn("dithering", n)

    def test_prohibe_el_suavizado(self):
        n = est.construir_negativo()
        for malo in ("anti-aliased", "smooth gradients", "airbrush"):
            self.assertIn(malo, n, malo)

    def test_prohibe_texto_y_firmas(self):
        """Animagine mete texto y firmas casi siempre."""
        n = est.construir_negativo()
        for malo in ("text", "signature", "watermark"):
            self.assertIn(malo, n, malo)

    def test_el_extra_se_concatena(self):
        n = est.construir_negativo(extra="extra fingers, six fingers")
        self.assertIn("six fingers", n)


class TestCatalogoDeEscenas(unittest.TestCase):
    def setUp(self):
        import generar_escenas as g
        self.g = g

    def test_tiene_los_tres_avatares_primero(self):
        for clave in ("duelista", "nara", "rajoy"):
            self.assertIn(clave, self.g.CATALOGO, clave)
            self.assertEqual(self.g.CATALOGO[clave]["tipo"], "avatar", clave)

    def test_tiene_los_seis_encuentros(self):
        for clave in ("mercader", "anciano", "hermandad", "caravana",
                      "hostil", "nara_encuentro"):
            self.assertIn(clave, self.g.CATALOGO, clave)
            self.assertEqual(self.g.CATALOGO[clave]["tipo"], "escena", clave)

    def test_tiene_los_dos_fondos_del_mundo_real(self):
        for clave in ("salon", "apagon"):
            self.assertIn(clave, self.g.CATALOGO, clave)
            self.assertEqual(self.g.CATALOGO[clave]["tipo"], "fondo", clave)

    def test_toda_entrada_declara_lo_que_el_juego_necesita(self):
        for clave, e in self.g.CATALOGO.items():
            self.assertTrue(e["sujeto"].strip(), clave)
            self.assertTrue(e["archivo"].strip(), clave)
            self.assertIn(e["encuadre"], est.ENCUADRES, clave)
            self.assertIn(e["tipo"], ("avatar", "escena", "fondo"), clave)

    def test_el_duelista_no_tiene_rostro(self):
        """La condicion narrativa: el protagonista es el jugador."""
        sujeto = self.g.CATALOGO["duelista"]["sujeto"].lower()
        self.assertIn("back view", sujeto)
        self.assertIn("no face visible", sujeto)
        self.assertEqual(self.g.CATALOGO["duelista"]["encuadre"], "silueta")

    def test_rajoy_es_un_rival_comun(self):
        """No es un jefe: no debe salir heroico."""
        notas = self.g.CATALOGO["rajoy"]["notas"].lower()
        self.assertIn("no un jefe", notas)

    def test_nara_es_reconocible_entre_avatar_y_escena(self):
        """Es el unico acompanante: tiene que ser LA MISMA en los dos sitios.

        Se comprueban los rasgos distintivos del avatar aprobado (el bun con
        trenza gruesa, los aros dorados, el cuello de pelo y el libro). Si la
        escena los describe distinto, el modelo dibuja otra persona.
        """
        escena = self.g.CATALOGO["nara_encuentro"]["sujeto"].lower()
        for rasgo in ("braid", "gold hoop earrings", "fur collar", "book"):
            self.assertIn(rasgo, escena, f"la escena de Nara pierde: {rasgo}")

    def test_el_salon_no_tiene_personajes_delante(self):
        """Es un fondo: si aparece un duelista dibujado, tapa el menu."""
        self.assertIn("no people in foreground",
                      self.g.CATALOGO["salon"]["extra"])

    def test_las_destinas_caen_dentro_de_assets(self):
        for clave, e in self.g.CATALOGO.items():
            destino = self.g._destino(e)
            relativo = os.path.relpath(destino, RAIZ).replace("\\", "/")
            self.assertTrue(relativo.startswith("assets/"), f"{clave}: {relativo}")


class TestElPixelSaleDelDownscale(unittest.TestCase):
    """El pixel art no sale de un filtro: sale de reducir sin interpolar."""

    def test_el_reductor_usa_vecino_mas_cercano(self):
        with open(os.path.join(RAIZ, "generar_escenas.py"), encoding="utf-8") as fh:
            fuente = fh.read()
        self.assertIn("Image.NEAREST", fuente)
        for malo in ("Image.BILINEAR", "Image.LANCZOS", "Image.BICUBIC"):
            self.assertNotIn(malo, fuente, malo)

    def test_reduce_de_verdad(self):
        """El reductor produce el tamano exacto y guarda un PNG valido."""
        import generar_escenas as g
        from PIL import Image
        origen = os.path.join(tempfile.gettempdir(), "origen_test.png")
        im = Image.new("RGBA", (1024, 1024), (120, 80, 200, 255))
        im.save(origen)
        destino = os.path.join(tempfile.gettempdir(), "destino_test.png")
        try:
            r = g._reducir(origen, destino, (256, 256))
            with Image.open(r) as salida:
                self.assertEqual(salida.size, (256, 256))
                # un color plano se conserva plano: eso es pixel art de verdad
                self.assertEqual(salida.getpixel((10, 10)), (120, 80, 200, 255))
        finally:
            for f in (origen, destino):
                if os.path.exists(f):
                    os.remove(f)

    def test_sin_redimension_si_ya_tiene_el_tamano(self):
        import generar_escenas as g
        from PIL import Image
        origen = os.path.join(tempfile.gettempdir(), "igual_test.png")
        destino = os.path.join(tempfile.gettempdir(), "igual_destino.png")
        Image.new("RGBA", (256, 256), (10, 20, 30, 255)).save(origen)
        try:
            g._reducir(origen, destino, (256, 256))
            with Image.open(destino) as salida:
                self.assertEqual(salida.size, (256, 256))
        finally:
            for f in (origen, destino):
                if os.path.exists(f):
                    os.remove(f)


class TestVariantesParaLaHoja(unittest.TestCase):
    def test_hay_varias_variantes_por_imagen(self):
        import generar_escenas as g
        for clave in ("duelista", "nara", "rajoy"):
            self.assertGreaterEqual(len(g._variantes(g.CATALOGO[clave])), 3, clave)

    def test_las_variantes_cambian_el_estilo(self):
        """Cada fila de la hoja tiene que ser una variable distinta."""
        import generar_escenas as g
        nombres = [n for n, _ in g._variantes(g.CATALOGO["nara"])]
        self.assertEqual(len(set(nombres)), len(nombres))

    def test_los_prompts_de_las_variantes_difieren(self):
        import generar_escenas as g
        prompts = [p for _, p, _ in g._variantes_de_prompt(g.CATALOGO["nara"])]
        self.assertEqual(len(set(prompts)), len(prompts))


class TestTextoAscii(unittest.TestCase):
    def test_el_prompt_y_los_notas_son_ascii(self):
        """El prompt va al modelo: cualquier caracter raro lo confunde."""
        import generar_escenas as g
        for clave, e in g.CATALOGO.items():
            for campo in ("sujeto", "extra", "notas"):
                for ch in e.get(campo, ""):
                    self.assertLessEqual(ord(ch), 127, f"{clave}/{campo}: {ch!r}")

    def test_la_biblia_de_este_set_es_ascii(self):
        for clave, texto in est.ENCUADRES.items():
            for ch in texto:
                self.assertLessEqual(ord(ch), 127, clave)
        for clave, texto in est.ESTILOS.items():
            for ch in texto:
                self.assertLessEqual(ord(ch), 127, clave)
        for ch in est.NEGATIVO_BASE:
            self.assertLessEqual(ord(ch), 127)


if __name__ == "__main__":
    unittest.main()
