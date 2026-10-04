"""Comprueba que todos los assets referenciados existen y cargan.

    python -m unittest tests.test_assets

Evita el error clasico de produccion: una carta sin arte, un sonido que no
existe o una pista de musica que pygame no puede abrir.
"""

import io
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
import ui  # noqa: E402
from paths import recurso  # noqa: E402
from reglas import HABILIDADES  # noqa: E402

FONDOS_ESPERADOS = ["ceniza", "camino", "aldea", "ruinas", "fortaleza", "trono",
                    "campamento", "asalto"]

SFX = [
    audio.COLOCAR, audio.CAPTURAR, audio.CADENA, audio.VICTORIA, audio.DERROTA,
    audio.MENU, audio.MENU_MOVE, audio.MENU_OK, audio.MENU_BACK, audio.CARD,
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

    def test_cada_cambio_de_pista_recarga_el_canal(self):
        """pygame.mixer.music tiene un solo canal.

        El flujo real lo usa asi: cartel de escenario con la pista del rival,
        combate con musica_duelo, y al siguiente duelo otra vez el mismo
        rival. Volver a una pista ya vista tiene que recargar el canal: si se
        cacheara el WAV, al pedirla otra vez el canal seguiria teniendo la
        anterior y sonaria la pista equivocada.

        Ojo: mixer.music.load() devuelve None, asi que un cache de "WAV
        cargados" nunca funcionaba (None se leia como "no cacheado") y
        recarga de mas. El cache solo guarda los fallos.
        """
        if pygame.mixer.get_init() is None:
            self.skipTest("sin dispositivo de audio")

        cargadas = []
        original = pygame.mixer.music.load

        def espia(ruta):
            cargadas.append(os.path.basename(ruta))
            return original(ruta)

        pygame.mixer.music.load = espia
        try:
            audio.musica(audio.musica_de_faccion("humano"))
            audio.musica(audio.musica_de_duelo())
            audio.musica(audio.musica_de_faccion("humano"))
        finally:
            pygame.mixer.music.load = original
            audio.detener_musica()

        self.assertEqual(cargadas, ["musica_humano.wav", "musica_duelo.wav",
                                    "musica_humano.wav"],
                         "cada cambio de pista debe recargar el canal")
        # y el cache solo guarda fallos, no WAV
        self.assertNotIn("musica_humano", audio._cache_musica,
                         "no se cachean los WAV: el canal de musica es unico")

    def test_pedir_la_misma_pista_la_reanuda(self):
        """El bug de la musica trabada: pausar_musica() no borra el nombre de
        la pista actual, asi que pedirla otra vez era un no-op y el silencio
        duraba hasta que se pidiera una pista DISTINTA."""
        audio.musica(audio.musica_de_faccion("humano"))
        audio.pausar_musica()
        self.assertTrue(audio._musica_pausada)
        # el juego pide la misma pista (nada cambio): deberia reanudar
        audio.musica(audio.musica_de_faccion("humano"))
        self.assertFalse(audio._musica_pausada,
                         "pedir la pista en pausa la deja en pausa: musica trabada")

    def test_detener_limpia_el_estado(self):
        """Si no, la siguiente peticion de la misma pista se ignoraba."""
        audio.musica(audio.musica_de_faccion("humano"))
        audio.detener_musica()
        self.assertIsNone(audio._musica_actual)
        self.assertFalse(audio._musica_pausada)
        audio.musica(audio.musica_de_faccion("humano"))
        self.assertEqual(audio._musica_actual, "musica_humano",
                         "tras detener, la pista debe volver a sonar")

    def test_el_bucle_de_la_musica_no_tiene_corte(self):
        """Las pistas se reproducen con play(-1). Con un fundido en los
        extremos, al repetir se oia un hueco de ~160 ms: eso era la musica
        trabada al terminar el dialogo."""
        import struct
        import wave

        def silencio(muestras, sr, umbral=300):
            mejor = actual = 0
            for v in muestras:
                if abs(v) < umbral:
                    actual += 1
                    mejor = max(mejor, actual)
                else:
                    actual = 0
            return mejor / sr * 1000

        for nombre in ("musica_duelo", "musica_explora",
                       "musica_humano", "musica_orco"):
            ruta = recurso(os.path.join("assets", "musica", f"{nombre}.wav"))
            with wave.open(ruta) as w:
                n = w.getnframes()
                sr = w.getframerate()
                muestras = struct.unpack(f"<{n}h", w.readframes(n))
            # la costura son los ultimos 100 ms: si estan mudos, se oye un corte
            corte = silencio(muestras[-int(sr * 0.1):], sr)
            # ...salvo que la pista ya tenga silencios de esa longitud dentro
            interior = silencio(muestras[int(n * 0.2):int(n * 0.8)], sr)
            self.assertLessEqual(
                corte, max(interior * 1.4, 40),
                f"{nombre}.wav se corta al repetir: {corte:.0f} ms de silencio "
                f"en la costura frente a {interior:.0f} ms dentro de la pista")


class TestReferencias(unittest.TestCase):
    def test_el_selector_de_faccion_sobrevive_al_raton(self):
        """ Reproduce el crash exacto: mover el raton por las facciones.

        elegir_faccion llama a audio.sfx(audio.MENU_MOVE) en cada cambio de
        seleccion. Con el nombre mal escrito, AttributeError y pantalla
        muerte: no se podia empezar una partida nueva.
        """
        import pantallas

        pantalla = pygame.display.set_mode((ui.ANCHO, ui.ALTO))
        original = pygame.event.get

        class Reloj:
            def tick(self, fps=0):
                return 16

        orden = facciones.orden_facciones()
        # pasar el raton por varias casillas: cada una cambia la seleccion
        secuencia = []
        for i in range(1, min(4, len(orden))):
            x = 160 + i * 190
            secuencia.append(pygame.event.Event(
                pygame.MOUSEMOTION, pos=(x, 250), rel=(1, 0), buttons=(0, 0, 0)))
        secuencia.append(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_RIGHT, unicode="", mod=0))
        secuencia.append(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_DOWN, unicode="", mod=0))
        # y al final ENTER para confirmar y salir
        secuencia.append(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_RETURN, unicode="", mod=0))
        # el raton sigue moviendose despues, por si el bucle pide otro frame
        for _ in range(20):
            secuencia.append(pygame.event.Event(
                pygame.MOUSEMOTION, pos=(900, 250), rel=(1, 0), buttons=(0, 0, 0)))

        cola = list(secuencia)

        def eventos():
            return [cola.pop(0)] if cola else []

        pygame.event.get = eventos
        try:
            faccion = pantallas.elegir_faccion(pantalla, Reloj())
            self.assertIn(faccion, orden)
        finally:
            pygame.event.get = original

    def test_todo_audio_X_del_juego_existe(self):
        """El bug: pantallas.py usaba audio.MENU_MOVE en 8 sitios pero
        audio.py defines MENU_MOV. Al mover el raton por el selector de
        faccion saltaba un AttributeError y no se podia empezar partida.

        El crash.log lo enseño tres veces (03:45, 11:09 y 16:54) y ni el
        smoke test ni los tests lo detectaban.
        """
        import re

        faltan = {}
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for nombre in sorted(os.listdir(raiz)):
            if not nombre.endswith(".py"):
                continue
            with io.open(os.path.join(raiz, nombre), encoding="utf-8") as f:
                texto = f.read()
            for m in re.finditer(r"\baudio\.([A-Z][A-Z_0-9]*)", texto):
                attr = m.group(1)
                if not hasattr(audio, attr):
                    linea = texto[:m.start()].count("\n") + 1
                    faltan.setdefault(attr, []).append(f"{nombre}:{linea}")
        self.assertEqual(faltan, {},
                         "estos audio.X no existen en audio.py: "
                         f"{ {k: v for k, v in faltan.items()} }")

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