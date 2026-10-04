"""Comprueba que todos los assets referenciados existen y cargan.

    python -m unittest tests.test_assets

Evita el error clasico de produccion: una carta sin arte, un sonido que no
existe o una pista de musica que pygame no puede abrir.
"""

import os
import sys
import tempfile
import unittest

# No escribir en los datos reales del jugador
os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import audio  # noqa: E402
import cartas as crt  # noqa: E402
import cinematicas  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
from paths import recurso  # noqa: E402
from reglas import HABILIDADES  # noqa: E402

FONDOS_ESPERADOS = ["ceniza", "camino", "aldea", "ruinas", "fortaleza", "trono",
                    "campamento", "asalto"]

SFX = [
    audio.COLOCAR, audio.CAPTURAR, audio.CADENA, audio.VICTORIA, audio.DERROTA,
    audio.MENU, audio.MENU_MOV, audio.MENU_OK, audio.MENU_BACK, audio.CARD,
    audio.DRAG, audio.INVALIDO, audio.CINEMA, audio.RECOMPENSA, audio.TORNEO,
]


def setUpModule():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass


class TestArte(unittest.TestCase):
    def test_cada_carta_tiene_imagen(self):
        faltan = []
        for bando, cartas in mazos.TODOS.items():
            for carta in cartas:
                ruta = os.path.join("cartas", f"{bando}_{crt._slug(carta.nombre)}.png")
                if not os.path.exists(recurso(ruta)):
                    faltan.append(ruta)
        self.assertEqual(faltan, [], f"cartas sin arte: {faltan}")

    def test_cada_faccion_tiene_avatar(self):
        faltan = [f for f in facciones.orden_facciones()
                  if not os.path.exists(recurso(os.path.join("assets", f"avatar_{f}.png")))]
        self.assertEqual(faltan, [])

    def test_todos_los_fondos_de_cinematica_existen(self):
        faltan = [n for n in FONDOS_ESPERADOS
                  if not os.path.exists(recurso(os.path.join("assets", "fondos", f"{n}.png")))]
        self.assertEqual(faltan, [])

    def test_fondo_del_juego(self):
        self.assertTrue(os.path.exists(recurso(os.path.join("assets", "fondo.png"))))

    def test_fuente(self):
        self.assertTrue(os.path.exists(recurso(os.path.join("assets", "PressStart2P.ttf"))))

    def test_las_imagenes_se_cargan_de_verdad(self):
        for f in facciones.orden_facciones():
            img = crt.REC.imagen(f"assets/avatar_{f}.png", (96, 96))
            self.assertEqual(img.get_size(), (96, 96), f)
            fondo = crt.REC.imagen("assets/fondos/trono.png")
            self.assertGreater(fondo.get_width(), 100, f)


class TestDiagnostico(unittest.TestCase):
    """El chequeo de main.py --check no debe encontrar nada."""

    def test_no_falta_ningun_recurso(self):
        import diagnostico

        self.assertEqual(diagnostico.verificar_recursos(), [])

    def test_el_informe_se_puede_imprimir(self):
        import diagnostico

        texto = diagnostico.informe()
        self.assertIn("Todo correcto", texto)
        self.assertIn("Facciones: 7", texto)


class TestAudio(unittest.TestCase):
    def test_todos_los_efectos_existen(self):
        faltan = [s for s in SFX if not os.path.exists(recurso(os.path.join("assets", s)))]
        self.assertEqual(faltan, [])

    def test_siete_pistas_una_por_faccion(self):
        faltan = []
        for f in facciones.orden_facciones():
            nombre = audio.musica_de_faccion(f)
            ruta = recurso(os.path.join("assets", "musica", f"{nombre}.wav"))
            if not os.path.exists(ruta):
                faltan.append(nombre)
        self.assertEqual(faltan, [])

    def test_las_pistas_de_tema_existen(self):
        """El duelo tiene su propia musica: no reutiliza la del rival."""
        import diagnostico

        for tema in diagnostico.TEMAS:
            nombre = f"musica_{tema}"
            ruta = recurso(os.path.join("assets", "musica", f"{nombre}.wav"))
            self.assertTrue(os.path.exists(ruta), f"falta {nombre}")
            self.assertGreater(os.path.getsize(ruta), 50000, f"{nombre} demasiado corta")

    def test_el_duelo_no_usa_la_musica_del_rival(self):
        self.assertNotEqual(audio.musica_de_duelo(), audio.musica_de_faccion("humano"))
        for f in facciones.orden_facciones():
            self.assertNotEqual(audio.musica_de_duelo(), audio.musica_de_faccion(f))

    def test_los_nombres_de_tema_son_distintos_de_las_facciones(self):
        self.assertNotIn("duelo", facciones.orden_facciones())
        self.assertNotIn("explora", facciones.orden_facciones())

    def test_los_controles_de_volumen_no_revientan(self):
        """El deslizador de Ajustes llama a esto: si falla, se cae la pantalla."""
        try:
            for v in (0.0, 0.5, 1.0):
                audio.volumen_sfx(v)
                audio.volumen_musica(v)
        except Exception as e:  # noqa: BLE001
            self.fail(f"cambiar de volumen lanza excepcion: {e!r}")
        finally:
            audio.volumen_sfx(0.55)
            audio.volumen_musica(0.35)

    def test_las_pistas_son_wav_validos(self):
        if pygame.mixer.get_init() is None:
            self.skipTest("sin dispositivo de audio")
        for f in facciones.orden_facciones():
            nombre = audio.musica_de_faccion(f)
            ruta = recurso(os.path.join("assets", "musica", f"{nombre}.wav"))
            try:
                pista = pygame.mixer.music.load(ruta)
            except pygame.error as e:  # noqa: PERF203
                self.fail(f"{nombre}.wav no se puede cargar: {e}")
            finally:
                pygame.mixer.music.unload()

    def test_la_pista_se_reproduce_sin_error(self):
        if pygame.mixer.get_init() is None:
            self.skipTest("sin dispositivo de audio")
        audio.musica(audio.musica_de_faccion("humano"))
        audio.musica(audio.musica_de_duelo())
        audio.musica(audio.musica_de_menu())
        audio.pausar_musica()
        audio.reanudar_musica()
        audio.detener_musica()


class TestReferencias(unittest.TestCase):
    def test_las_abilidades_usadas_estan_documentadas(self):
        usadas = {c.habilidad for cartas in mazos.TODOS.values() for c in cartas if c.habilidad}
        self.assertTrue(usadas)
        self.assertTrue(usadas <= set(HABILIDADES))

    def test_las_aperturas_existen_para_todas_las_facciones(self):
        for f in facciones.orden_facciones():
            escenas, musica = cinematicas.apertura(f)
            self.assertGreaterEqual(len(escenas), 3, f)
            self.assertTrue(musica)
            for e in escenas:
                self.assertTrue(e["texto"].strip(), f)

    def test_cada_nodo_tiene_previa_y_escena(self):
        import campana

        for nodo_id, datos in campana.NODOS.items():
            self.assertTrue(datos["titulo"], nodo_id)
            if datos["tipo"] != "eleccion":
                self.assertTrue(datos.get("previa"), nodo_id)
                self.assertIn(datos.get("escena"), FONDOS_ESPERADOS, nodo_id)

    def test_los_duelistas_de_todas_las_facciones_tienen_texto(self):
        import campana

        for f in facciones.orden_facciones():
            d = campana.DUELISTAS[f]
            for clave in ("nombre", "titulo", "entrada", "captura_player",
                          "captura_cpu", "win", "lose"):
                self.assertTrue(d.get(clave), f"{f}.{clave}")

    def test_los_finales_de_todas_las_facciones(self):
        import campana

        for f in facciones.orden_facciones():
            for variante in ("dominio", "equilibrio", "caos"):
                final = campana.FINALES[f][variante]
                self.assertTrue(final["titulo"], f"{f}.{variante}")
                self.assertGreaterEqual(len(final["lineas"]), 3, f"{f}.{variante}")

    def test_los_encuentros_tienen_efecto_conocido(self):
        import campana

        efectos = {"mejorar", "robo", "mas_debil", "debilitar", "celebrar", "sigilo"}
        for enc in campana.ENCUENTROS:
            for op in enc["opciones"]:
                self.assertIn(op["efecto"], efectos, enc["id"])

    def test_las_recompensas_cubren_las_ramas(self):
        import campana

        for nodo_id in ("senda", "aldea", "ruinas", "fortaleza", "asalto"):
            recompensas = campana.recompensas_de(nodo_id)
            self.assertTrue(recompensas, nodo_id)
            for r in recompensas:
                self.assertIn(r, campana.TEXTO_RECOMPENSA, nodo_id)


if __name__ == "__main__":
    unittest.main()