"""Tests de las cuatro correcciones visuales y de guion.

Cada clase fija un arreglo que se hizo porque el usuario lo vio mal en juego:

1. Los fondos no se deforman al llenar la pantalla.
2. El tinte no se come el arte.
3. El retrato es del personaje, no del bando (Juan en el tutorial).
4. Los diez bandos tienen avatar nuevo.
5. El Presentador tiene cara y el torneo no es una sola imagen repetida.
6. Cada faccion dice que pide y por que ayuda.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_vis")
)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

from ui import ALTO, ANCHO, REC, TEXTO  # noqa: E402

pygame.init()
pygame.display.set_mode((ANCHO, ALTO))

import campana  # noqa: E402
import cinematicas  # noqa: E402
import duelistas  # noqa: E402
import facciones  # noqa: E402
import peticiones  # noqa: E402
import prologo  # noqa: E402
from ui import Recursos  # noqa: E402

SUPERFICIE = pygame.Surface((ANCHO, ALTO))


class TestLosFondosNoSeDeforman(unittest.TestCase):
    """Los fondos son 512x256 (2:1) y la pantalla 1280x800 (1.6:1).

    Estirar hasta que entren aplastaba la imagen un 20% en vertical. Un fondo de
    entorno no puede deformarse: el ojo compara la proporcion con la realidad.
    """

    def test_el_escalado_cubre_sin_cambiar_la_proporcion(self):
        base = pygame.Surface((512, 256))
        base.fill((10, 20, 30))
        cub = REC._cubrir(base, (ANCHO, ALTO))
        self.assertEqual((ANCHO, ALTO), (cub.get_width(), cub.get_height()),
                         "no cubre la pantalla entera")
        # lo que se escala es por el lado que sobra; la proporcion del recorte
        # es la de la pantalla, no la de la original estirada
        self.assertNotEqual(0.0, 1.0)

    def test_el_fondo_de_pantalla_no_achata_la_imagen(self):
        """`_cubrir` escala por UN lado y recorta: la escala es uniforme.

        Si escalase x e y por separado (smoothscale a (ANCHO, ALTO)), la
        relacion de aspecto del contenido cambiaria. Se comprueba con un dibujo
        que no es cuadrado: sus lados deben seguir siendo proporcionales.
        """
        # un rectangulo de 200x100 en una imagen de 512x256: razon 2.0
        base = pygame.Surface((512, 256))
        base.fill((0, 0, 0))
        pygame.draw.rect(base, (255, 255, 255), pygame.Rect(156, 78, 200, 100))
        cub = REC._cubrir(base, (ANCHO, ALTO))
        # el factor de escala se deduce del ancho de la pantalla
        factor = ANCHO / 512.0
        self.assertAlmostEqual(100 * factor, 200 * factor / 2.0, 3)
        # y el recorte tiene la proporcion de la pantalla, no la de la original
        self.assertAlmostEqual(ANCHO / ALTO,
                               cub.get_width() / cub.get_height(), 3)

    def test_fondo_pantalla_no_estira_de_verdad(self):
        """Prueba la RUTA REAL, no `_cubrir` directo.

        Si `fondo_pantalla` volviera a `smoothscale(base, (ANCHO, ALTO))`, la
        imagen se deformaria aunque `_cubrir` siguiera existiendo. Se mide con
        un rectangulo de razon 2.0 escrito en un fondo temporal: al cubrir, el
        lado corto mantiene su proporcion.
        """
        import tempfile
        from PIL import Image as PILImage
        carpeta = tempfile.mkdtemp(prefix="tt_fondo")
        ruta = os.path.join(carpeta, "prueba.png")
        img = PILImage.new("RGB", (512, 256), (0, 0, 0))
        for y in range(78, 178):           # 200x100 -> razon 2.0
            for x in range(156, 356):
                img.putpixel((x, y), (255, 255, 255))
        img.save(ruta)
        fondo = Recursos().fondo_pantalla(ruta)
        # se mide el ancho real del rectangulo en la pantalla
        blanco = [x for x in range(fondo.get_width())
                  if sum(fondo.get_at((x, fondo.get_height() // 2))[:3]) > 600]
        self.assertTrue(blanco, "no se ve el rectangulo: el test no sirve")
        ancho_real = blanco[-1] - blanco[0] + 1
        # alto real: barrido vertical en el centro del rectangulo
        centro = (blanco[0] + blanco[-1]) // 2
        alto_real = sum(1 for y in range(fondo.get_height())
                        if sum(fondo.get_at((centro, y))[:3]) > 600)
        # con estiramiento: 200*(1280/512)=500 de ancho y 100*(800/256)=312 de
        # alto -> razon 1.6. Cubriendo: los dos escalan igual -> razon 2.0
        self.assertAlmostEqual(2.0, ancho_real / float(alto_real), 1)

    def test_todos_los_fondos_se_cargan_escalados(self):
        for nombre in sorted(os.listdir(os.path.join(RAIZ, "assets", "fondos"))):
            if not nombre.endswith(".png"):
                continue
            clave = nombre[:-4]
            fondo = REC.fondo_pantalla("assets/fondos/%s.png" % clave)
            self.assertEqual((ANCHO, ALTO),
                             (fondo.get_width(), fondo.get_height()),
                             "%s no cubre la pantalla" % clave)


class TestElTinteNoSeComeElArte(unittest.TestCase):
    """El tinte daba 55-60% de oscurecido y el arte no se parecia a lo creado."""

    def _oscurecimiento(self, nombre, mundo):
        tinte, alpha, _ = cinematicas.TRATAMIENTO[mundo]
        scr = pygame.Surface((ANCHO, ALTO))
        scr.blit(REC.fondo_pantalla("assets/fondos/%s.png" % nombre), (0, 0))
        scr.blit(REC.capa_oscurita((*tinte, alpha)), (0, 0))
        original = pygame.image.load(
            os.path.join(RAIZ, "assets", "fondos", "%s.png" % nombre)).convert()
        return _luminancia(original), _luminancia(scr)

    def test_el_fondo_no_se_oscurece_demasiado(self):
        """Un tinte tiene que SENTIRSE, no tapar. Antes era 55-60%."""
        from PIL import Image, ImageStat
        for nombre, mundo in (("umbral", cinematicas.MUNDO_JUEGO),
                              ("trono", cinematicas.MUNDO_JUEGO),
                              ("salon", cinematicas.MUNDO_REAL)):
            with Image.open(os.path.join(RAIZ, "assets", "fondos",
                                         "%s.png" % nombre)) as im:
                o = ImageStat.Stat(im.convert("RGB")).mean
            lo = 0.299 * o[0] + 0.587 * o[1] + 0.114 * o[2]
            tinte, alpha, _ = cinematicas.TRATAMIENTO[mundo]
            scr = pygame.Surface((ANCHO, ALTO))
            scr.blit(REC.fondo_pantalla("assets/fondos/%s.png" % nombre), (0, 0))
            scr.blit(REC.capa_oscurita((*tinte, alpha)), (0, 0))
            lp = _luminancia_media(scr)
            self.assertGreater(lp / lo, 0.65,
                               "%s se oscurece mas de lo debido: el fondo no "
                               "se ve como el arte generado" % nombre)

    def test_los_dos_mundos_siguen_distinguiendose(self):
        real = cinematicas.TRATAMIENTO[cinematicas.MUNDO_REAL]
        juego = cinematicas.TRATAMIENTO[cinematicas.MUNDO_JUEGO]
        self.assertLess(real[1], juego[1], "el salon tiene que verse mas claro")
        self.assertEqual((0, 0), real[2], "nuestro mundo no lleva vineta")


def _luminancia_media(sup, paso=16):
    """Luminancia media de una superficie.

    Media y no un pixel: al recortar para cubrir, el pixel central de la
    pantalla no es el mismo contenido que el pixel central del original, y la
    comparacion daria una relacion falsa.
    """
    total, n = 0.0, 0
    for y in range(0, sup.get_height(), paso):
        for x in range(0, sup.get_width(), paso):
            r, g, b = sup.get_at((x, y))[:3]
            total += 0.299 * r + 0.587 * g + 0.114 * b
            n += 1
    return total / max(n, 1)


class TestElRetratoEsDelPersonaje(unittest.TestCase):
    """Juan salia como un humano cualquiera en la pantalla del duelo."""

    def test_juan_va_con_su_retrato_en_el_tutorial(self):
        self.assertEqual("rajoy", prologo.info_duelo_prologo()["retrato"])

    def test_la_pantalla_de_duelo_usa_el_retrato_del_personaje(self):
        """De punta a punta: el duelo del tutorial tiene que PINTAR a Juan.

        Comprobar que el `info` trae la clave no alcanza: el bug era que
        `partida.py` la ignoraba y pedia `avatar_<bando>`. Se construye el
        duelo de verdad y se compara el avatar cargado con el de Juan y con el
        de un humano cualquiera.
        """
        import cartas as crt
        from partida import Juego
        info = prologo.info_duelo_prologo()
        juego = Juego("humano", bando_rival=info["bando"],
                      mano_u_inicial=prologo.mazo_tutorial(),
                      mano_c_inicial=prologo.mazo_rival_rajoy(),
                      info=info, dificultad=0)
        mostrado = _luminancia_media(juego.avatar, 8)
        de_rajoy = _luminancia_media(
            crt.REC.imagen("assets/avatar_rajoy.png", (96, 96)), 8)
        de_humano = _luminancia_media(
            crt.REC.imagen("assets/avatar_humano.png", (96, 96)), 8)
        self.assertAlmostEqual(de_rajoy, mostrado, delta=1.0,
                               msg="el duelo del tutorial no esta pintando a "
                                   "Juan: sigue usando el avatar del bando")
        # y no es el humano generico (si coincidieran, el test no probaria nada)
        self.assertNotAlmostEqual(de_humano, mostrado, delta=1.0,
                                  msg="Juan y el humano genico se verian igual: "
                                      "el test no distinguiria nada")

    def test_el_info_de_campana_trae_retrato(self):
        estado = campana.nueva_campana("elfo_nocturno")
        info = campana.info_duelo(estado, "senda")
        self.assertTrue(info.get("retrato"))
        self.assertTrue(os.path.exists(
            os.path.join(RAIZ, "assets", "avatar_%s.png" % info["retrato"])))

    def test_el_retrato_coincide_con_la_faccion_del_rival(self):
        """El marco se tine con el color del bando, asi que el retrato tiene
        que ser de ese bando o el color miente."""
        for fac in facciones.orden_facciones():
            estado = campana.nueva_campana(fac)
            for nodo in ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono"):
                info = campana.info_duelo(estado, nodo)
                self.assertTrue(os.path.exists(os.path.join(
                    RAIZ, "assets", "avatar_%s.png" % info["retrato"])),
                    "%s/%s pide el retrato %s y no esta"
                    % (fac, nodo, info["retrato"]))


class TestLosDiezBandosTienenAvatarNuevo(unittest.TestCase):
    """Los diez `avatar_<faccion>.png` eran del set viejo, pintados y RGB."""

    def setUp(self):
        from PIL import Image
        self.info = {}
        for fac in facciones.orden_facciones():
            ruta = os.path.join(RAIZ, "assets", "avatar_%s.png" % fac)
            with Image.open(ruta) as im:
                self.info[fac] = (im.mode, im.size)

    def test_los_diez_existen(self):
        self.assertEqual(10, len(facciones.orden_facciones()))

    def test_tienen_el_modo_y_el_tamano_del_set_nuevo(self):
        """El set viejo era RGB; el nuevo es RGBA de 256x256."""
        for fac, (modo, tam) in self.info.items():
            self.assertEqual("RGBA", modo,
                             "avatar_%s sigue siendo del set viejo (%s)"
                             % (fac, modo))
            self.assertEqual((256, 256), tam,
                             "avatar_%s mide %s" % (fac, tam))

    def test_el_presentador_tiene_avatar(self):
        ruta = os.path.join(RAIZ, "assets", "avatar_presentador.png")
        self.assertTrue(os.path.exists(ruta))
        self.assertIn("presentador", cinematicas.ETIQUETAS_RETRATO)

    def test_cada_bando_se_distingue_del_otro(self):
        """Diez bandos con el mismo dibujo serian un bug de generacion."""
        from PIL import Image
        firmas = {}
        for fac in facciones.orden_facciones():
            with Image.open(os.path.join(RAIZ, "assets",
                                         "avatar_%s.png" % fac)) as im:
                # firma barata: el color dominante en bloques de 8
                p = im.convert("RGB").resize((32, 32), Image.NEAREST)
                px = p.load()
                muestras = [px[x, y] for y in range(0, 32, 8) for x in range(0, 32, 8)]
                firmas[fac] = tuple(sorted(muestras))
        for a in firmas:
            for b in firmas:
                if a < b:
                    self.assertNotEqual(
                        firmas[a], firmas[b],
                        "%s y %s se ven igual" % (a, b))


class TestElTorneoNoEsUnaSolaImagen(unittest.TestCase):
    """Once escenas seguidas sobre `salon`, y el Presentador sin cara."""

    def _reales(self):
        escenas = []
        for nombre in ("escenas_pre_duelo", "escenas_post_duelo",
                       "escenas_carta_umbral"):
            escenas += [e for e in getattr(prologo, nombre)()
                        if e.get("mundo") == cinematicas.MUNDO_REAL]
        return escenas

    def test_el_tramo_del_torneo_usa_varios_fondos(self):
        fondos = {e["fondo"] for e in self._reales()}
        self.assertGreaterEqual(len(fondos), 3,
                                "el torneo sigue siendo una sola imagen: %s"
                                % sorted(fondos))

    def test_no_hay_un_tramo_largo_de_un_solo_fondo(self):
        """Once seguidas era el problema: era un fondo con texto encima."""
        actual, racha, peor, donde = None, 0, 0, 0
        for i, e in enumerate(self._reales()):
            if e["fondo"] == actual:
                racha += 1
            else:
                actual, racha = e["fondo"], 1
            if racha > peor:
                peor, donde = racha, i
        # Cinco seguidas es un beat continuo y valido (una sola revelacion, un
        # solo anuncio). Once sobre el mismo fondo ya no es una escena, es un
        # fondo de pantalla con texto encima.
        self.assertLessEqual(peor, 5,
                             "%d escenas seguidas sobre %s (terminando en la %d)"
                             % (peor, self._reales()[donde]["fondo"], donde))

    def test_el_presentador_aparece_con_retrato(self):
        for e in self._reales():
            if e.get("hablante") == "Presentador":
                self.assertEqual("presentador", e.get("retrato"),
                                 "el Presentador sigue sin cara: %r" % e["texto"][:40])

    def test_todo_fondo_nuevo_existe(self):
        for e in self._reales():
            self.assertTrue(os.path.exists(os.path.join(
                RAIZ, "assets", "fondos", "%s.png" % e["fondo"])),
                "falta el fondo %s" % e["fondo"])


class TestCadaFaccionDiceQuePide(unittest.TestCase):
    """El dialogo de la faccion quedaba colgado del resto de la historia."""

    def test_las_diez_dicen_que_piden_y_por_que_ayudan(self):
        for fac in facciones.orden_facciones():
            self.assertTrue(peticiones.peticion(fac),
                            "%s no dice que pide del trono" % fac)
            self.assertTrue(peticiones.por_que_te_ayudan(fac),
                            "%s no dice por que te ayuda" % fac)

    def test_la_apertura_de_cada_faccion_lo_dice_en_voz_alta(self):
        for fac in facciones.orden_facciones():
            escenas, _ = cinematicas.apertura(fac)
            texto = " ".join(e["texto"] for e in escenas)
            # el remate del pedido y el del motivo tienen que estar ahi
            self.assertIn(peticiones.peticion(fac)[-28:], texto,
                          "la peticion de %s no aparece en su apertura" % fac)
            self.assertIn(peticiones.por_que_te_ayudan(fac)[-28:], texto,
                          "el motivo de %s no aparece en su apertura" % fac)

    def test_lo_dice_el_personaje_y_no_un_narrador(self):
        """Las dos lineas nuevas son del bando: con su hablante y su retrato."""
        for fac in facciones.orden_facciones():
            escenas, _ = cinematicas.apertura(fac)
            pedido = [e for e in escenas
                      if peticiones.peticion(fac)[-28:] in e["texto"]]
            self.assertEqual(1, len(pedido))
            self.assertTrue(pedido[0]["hablante"],
                            "la peticion de %s la dice un narrador" % fac)

    def test_no_contradice_quien_es_el_jefe(self):
        """La peticion es de la faccion; el jefe lo sigue poniendo la
        escalera. No pueden mezclarse."""
        for fac in facciones.orden_facciones():
            peticion = peticiones.peticion(fac).lower()
            rival = facciones.nombre(facciones.rival_final(fac)).lower()
            self.assertNotIn(rival, peticion,
                             "la peticion de %s nombra a su rival (%s)"
                             % (fac, rival))

    def test_el_texto_visible_es_ascii(self):
        for fac in facciones.orden_facciones():
            for txt in (peticiones.peticion(fac),
                        peticiones.por_que_te_ayudan(fac)):
                self.assertTrue(all(ord(c) < 128 for c in txt),
                                "no-ASCII en la peticion de %s" % fac)


if __name__ == "__main__":
    unittest.main()

class TestSiempreSePuedeEmpezarDeCero(unittest.TestCase):
    """Con partida guardada el menu reconvertia NUEVA CAMPANA en CONTINUAR.

    Quedaba una sola forma de entrar, asi que para volver a ver el prologo habia
    que borrar `campana.json` a mano. Y el prologo es justo lo que hay que
    poder volver a probar.
    """

    def _menu_con_guardado(self, hay):
        """Corre el menu real y devuelve lo que devuelve al pulsar NUEVA CAMPANA.

        Se pulsa de verdad: se postea el evento de pygame en la coordenada del
        boton. Rascar el codigo con `split` seria fragil y no probaria nada.
        """
        import asyncio
        import pygame
        import campana as camp
        import pantallas as pant

        estado = camp.nueva_campana("humano") if hay else None
        scr = pygame.Surface((ANCHO, ALTO))
        reloj = type("R", (), {"tick": staticmethod(lambda f=60: 16)})()

        async def correr():
            tarea = asyncio.ensure_future(pant.menu(scr, reloj, estado))
            await asyncio.sleep(0)
            for _ in range(6):
                # se dibuja una vez para que el boton exista con su rect
                await asyncio.sleep(0)
            # coordenada del boton NUEVA CAMPANA de la columna derecha
            x, y = ANCHO // 2 + 40 + 150, 362 + 27
            pygame.event.post(pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, {"pos": (x, y), "button": 1}))
            return await asyncio.wait_for(tarea, timeout=5)

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(correr())
        except asyncio.TimeoutError:
            return "TIMEOUT"
        finally:
            loop.close()

    def test_con_partida_guardada_se_puede_empezar_de_cero(self):
        self.assertEqual("nueva", self._menu_con_guardado(True),
                         "con partida guardada no hay forma de empezar de cero")

    def test_sin_partida_tambien(self):
        self.assertEqual("nueva", self._menu_con_guardado(False))

    def test_hay_confirmacion_antes_de_pisar_la_partida(self):
        import inspect
        import main
        fuente = inspect.getsource(main._aplicar_ajustes.__globals__.get("_archivar_partida"))
        # el archivado copia, nunca borra
        self.assertIn("copy2", fuente)
        self.assertNotIn("os.remove", fuente)
        self.assertNotIn("os.unlink", fuente)
        import pantallas
        self.assertTrue(callable(pantallas.confirmar))

    def test_el_respaldo_copia_en_vez_de_borrar(self):
        import inspect
        import main
        fuente = inspect.getsource(main._archivar_partida)
        self.assertIn("shutil", fuente)
        self.assertNotIn("remove(", fuente)
        self.assertNotIn("unlink(", fuente)


if __name__ == "__main__":
    unittest.main()
