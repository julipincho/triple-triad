"""Pruebas de la coordinacion de ComfyUI (bloqueo, cola, registro y arranque).

    python -m unittest tests.test_coord_comfyui

No arranca servicios, no genera imagenes y no cierra procesos reales: usa
respuestas HTTP simuladas, un servidor falso, bloqueos reales del sistema
operativo y un registro en una carpeta temporal.
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
from types import SimpleNamespace
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import comfy_coord  # noqa: E402
import generar_cartas_comfyui as comfy  # noqa: E402


class _CandadoFalso:
    """Bloqueo inyectable para probar el arranque sin tocar el sistema."""

    def __init__(self, cerrojo=None, resultado=True):
        self.cerrojo = cerrojo
        self.resultado = resultado
        self.tomado = False

    def adquirir(self, timeout=30):
        if not self.resultado:
            return False
        if self.cerrojo is None:
            self.tomado = True
            return True
        self.tomado = self.cerrojo.acquire(timeout=timeout)
        return self.tomado

    def liberar(self):
        if self.tomado and self.cerrojo is not None:
            self.cerrojo.release()
        self.tomado = False


class _ServidorFalso:
    """ComfyUI simulado: arranca tras la primera llamada al lanzador."""

    def __init__(self):
        self.up = False
        self.launches = 0
        self._lock = threading.Lock()

    def chequeo(self, servidor):
        with self._lock:
            return "0.39.0" if self.up else None

    def lanzar(self, bat):
        with self._lock:
            self.launches += 1
        time.sleep(0.05)
        with self._lock:
            self.up = True


class TestClasificarCola(unittest.TestCase):
    def test_ocupada_si_hay_trabajo(self):
        info = comfy_coord.clasificar_cola({"queue_running": [{}], "queue_pending": []})
        self.assertEqual(info["estado"], "ocupada")
        self.assertEqual(info["en_ejecucion"], 1)
        self.assertEqual(info["pendientes"], 0)

    def test_ocupada_si_solo_hay_pendientes(self):
        info = comfy_coord.clasificar_cola({"queue_running": [], "queue_pending": [{}, {}]})
        self.assertEqual(info["estado"], "ocupada")
        self.assertEqual(info["pendientes"], 2)

    def test_vacia_solo_con_las_dos_listas_vacias(self):
        info = comfy_coord.clasificar_cola({"queue_running": [], "queue_pending": []})
        self.assertEqual(info["estado"], "vacia")

    def test_desconocida_con_formas_inesperadas(self):
        for payload in (None, {}, {"queue_running": []},
                        {"queue_running": [], "queue_pending": None},
                        {"queue_running": "x", "queue_pending": []},
                        [1, 2, 3]):
            with self.subTest(payload=payload):
                self.assertEqual(comfy_coord.clasificar_cola(payload)["estado"], "desconocida")


class TestEvaluarParada(unittest.TestCase):
    def test_sin_proceso_no_hay_nada_que_hacer(self):
        r = comfy_coord.evaluar_parada(False, "inequivoca", "vacia")
        self.assertEqual(r["accion"], comfy_coord.ACCION_NADA)

    def test_proceso_desconocido_se_rechaza(self):
        r = comfy_coord.evaluar_parada(True, "ambigua", "vacia")
        self.assertEqual(r["accion"], comfy_coord.ACCION_RECHAZAR)
        self.assertEqual(r["motivo"], "identidad_no_inequivoca")

    def test_cola_ocupada_se_rechaza(self):
        r = comfy_coord.evaluar_parada(True, "inequivoca", "ocupada")
        self.assertEqual(r["motivo"], "cola_ocupada")

    def test_cola_desconocida_se_rechaza(self):
        r = comfy_coord.evaluar_parada(True, "inequivoca", "desconocida")
        self.assertEqual(r["motivo"], "cola_desconocida")

    def test_cola_vacia_no_basta_por_si_sola(self):
        r = comfy_coord.evaluar_parada(
            True, "inequivoca", "vacia", exclusion_fiable=False, apagado_ordenado=False)
        self.assertEqual(r["accion"], comfy_coord.ACCION_RECHAZAR)
        self.assertEqual(r["motivo"], "cola_vacia_sin_exclusion_ni_apagado_ordenado")

    def test_cola_vacia_con_exclusion_y_orden_permite_detener(self):
        r = comfy_coord.evaluar_parada(
            True, "inequivoca", "vacia", exclusion_fiable=True, apagado_ordenado=True)
        self.assertEqual(r["accion"], comfy_coord.ACCION_DETENER)


class TestBloqueoArchivo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ruta = os.path.join(self.tmp, "arranque.lock")

    def test_excluye_a_un_segundo_bloqueo(self):
        a = comfy_coord._BloqueoArchivo(self.ruta)
        b = comfy_coord._BloqueoArchivo(self.ruta)
        self.assertTrue(a.adquirir(1.0))
        self.assertFalse(b.adquirir(0.2))
        a.liberar()
        self.assertTrue(b.adquirir(1.0))
        b.liberar()

    def test_no_queda_bloqueo_tras_cierre_inesperado(self):
        a = comfy_coord._BloqueoArchivo(self.ruta)
        self.assertTrue(a.adquirir(1.0))
        # Simula un cierre inesperado: se suelta el descriptor sin "liberar".
        os.close(a._fd)
        a._fd = None
        c = comfy_coord._BloqueoArchivo(self.ruta)
        self.assertTrue(c.adquirir(1.0))
        c.liberar()


@unittest.skipUnless(os.name == "nt", "mutex con nombre: solo Windows")
class TestMutexWindows(unittest.TestCase):
    def setUp(self):
        self.nombre = "Local\\CartonesTest_" + str(os.getpid()) + "_" + str(id(self))

    def test_contiende_entre_hilos(self):
        candado = comfy_coord._MutexWindows(self.nombre)
        listo = threading.Event()
        soltar = threading.Event()

        def tenedor():
            self.assertTrue(candado.adquirir(5))
            listo.set()
            soltar.wait(5)
            candado.liberar()

        hilo = threading.Thread(target=tenedor)
        hilo.start()
        self.assertTrue(listo.wait(5))

        otro = comfy_coord._MutexWindows(self.nombre)
        self.assertFalse(otro.adquirir(0.2))

        soltar.set()
        hilo.join(5)
        self.assertTrue(otro.adquirir(1.0))
        otro.liberar()

    def test_mutex_abandonado_no_bloquea(self):
        candado = comfy_coord._MutexWindows(self.nombre)
        listo = threading.Event()

        def tenedor():
            self.assertTrue(candado.adquirir(5))
            listo.set()
            # Termina el hilo sin liberar: el mutex queda abandonado.

        hilo = threading.Thread(target=tenedor)
        hilo.start()
        self.assertTrue(listo.wait(5))
        hilo.join(5)

        otro = comfy_coord._MutexWindows(self.nombre)
        self.assertTrue(otro.adquirir(1.0))
        otro.liberar()


class TestArranque(unittest.TestCase):
    def _args(self, **extra):
        base = dict(servidor="http://127.0.0.1:8188",
                    bat="E:\\AI\\start-comfyui.bat", espera=3, pausa=0.01,
                    espera_bloqueo=2, dormir=lambda s: None,
                    log=lambda *a, **k: None)
        base.update(extra)
        return base

    def test_ya_en_marcha_no_arranca_ni_bloquea(self):
        lanzamientos = []
        llamadas_bloqueo = []

        def factory():
            llamadas_bloqueo.append(1)
            return _CandadoFalso()

        resultado = comfy_coord.arrancar_con_bloqueo(
            chequeo=lambda s: "0.39.0", lanzador=lambda bat: lanzamientos.append(bat),
            bloqueo_factory=factory, **self._args())
        self.assertTrue(resultado.ok)
        self.assertFalse(resultado.arrancado)
        self.assertEqual(lanzamientos, [])
        self.assertEqual(llamadas_bloqueo, [])

    def test_arranca_y_queda_listo(self):
        servidor = _ServidorFalso()
        resultado = comfy_coord.arrancar_con_bloqueo(
            chequeo=servidor.chequeo, lanzador=servidor.lanzar,
            bloqueo_factory=lambda: _CandadoFalso(), **self._args())
        self.assertTrue(resultado.ok)
        self.assertTrue(resultado.arrancado)
        self.assertEqual(servidor.launches, 1)

    def test_dos_arranques_simultaneos_solo_lanzan_uno(self):
        servidor = _ServidorFalso()
        cerrojo = threading.Lock()
        resultados = [None, None]

        def intento(i):
            resultados[i] = comfy_coord.arrancar_con_bloqueo(
                chequeo=servidor.chequeo, lanzador=servidor.lanzar,
                bloqueo_factory=lambda: _CandadoFalso(cerrojo), **self._args())

        hilos = [threading.Thread(target=intento, args=(i,)) for i in (0, 1)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join(10)

        self.assertTrue(all(r is not None and r.ok for r in resultados))
        self.assertEqual(servidor.launches, 1)

    def test_fallo_al_adquirir_bloqueo_no_lanza(self):
        lanzamientos = []
        resultado = comfy_coord.arrancar_con_bloqueo(
            chequeo=lambda s: None, lanzador=lambda bat: lanzamientos.append(bat),
            bloqueo_factory=lambda: _CandadoFalso(resultado=False),
            espera=0.01, log=lambda *a, **k: None, dormir=lambda s: None,
            servidor="http://127.0.0.1:8188", bat="E:\\AI\\start-comfyui.bat",
            espera_bloqueo=0.01)
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.motivo, "bloqueo")
        self.assertEqual(lanzamientos, [])

    def test_bat_ausente(self):
        resultado = comfy_coord.arrancar_con_bloqueo(
            chequeo=lambda s: None, lanzador=lambda bat: None,
            bloqueo_factory=lambda: _CandadoFalso(),
            servidor="http://127.0.0.1:8188", bat="Z:\\no\\existe.bat",
            espera=1, log=lambda *a, **k: None, dormir=lambda s: None)
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.motivo, "bat_ausente")

    def test_servidor_no_responde(self):
        resultado = comfy_coord.arrancar_con_bloqueo(
            chequeo=lambda s: None, lanzador=lambda bat: None,
            bloqueo_factory=lambda: _CandadoFalso(),
            servidor="http://127.0.0.1:8188", bat="E:\\AI\\start-comfyui.bat",
            espera=0.01, log=lambda *a, **k: None, dormir=lambda s: None,
            espera_bloqueo=1)
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.motivo, "no_responde")

    def test_fallo_al_lanzar_no_aborta(self):
        def lanzador_roto(bat):
            raise OSError("no se pudo abrir la consola")

        resultado = comfy_coord.arrancar_con_bloqueo(
            chequeo=lambda s: None, lanzador=lanzador_roto,
            bloqueo_factory=lambda: _CandadoFalso(),
            servidor="http://127.0.0.1:8188", bat="E:\\AI\\start-comfyui.bat",
            espera=0.01, log=lambda *a, **k: None, dormir=lambda s: None,
            espera_bloqueo=1)
        self.assertFalse(resultado.ok)
        self.assertEqual(resultado.motivo, "no_lanza")


class TestGenerarImagen(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.registro = comfy_coord.RegistroTrabajos(
            os.path.join(self.tmp, "trabajos.jsonl"))
        self.destino = os.path.join(self.tmp, "salida.png")
        # Aisla la observacion: escribe en una carpeta temporal DENTRO de la
        # raiz del coordinador y jamas toca el registro real
        # `E:/AI/GPU-Coordinator/var/observados.jsonl`.
        self._obs_prev = comfy._observador
        self._var_obs = None
        try:
            from gpu_coordinator.config import Config as _Config
            from gpu_coordinator.observador import Observador as _Observador
            from gpu_coordinator.seguridad import RAIZ as _RAIZ
            self._var_obs = os.path.join(
                str(_RAIZ), "var", "_tests",
                "juego_" + os.path.basename(self.tmp))
            comfy._observador = _Observador(_Config(dir_var=self._var_obs))
        except Exception:  # noqa: BLE001 - sin GPU-Coordinator no hay nada que aislar
            comfy._observador = None
        # El portero queda inerte: tipo por defecto "imagen" y sin coordinador.
        self._coord_prev = comfy._coordinador
        comfy._coordinador = None

    def tearDown(self):
        comfy._observador = self._obs_prev
        comfy._coordinador = self._coord_prev
        if self._var_obs:
            shutil.rmtree(self._var_obs, ignore_errors=True)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _llamar(self, espera=10, **kw):
        return comfy.generar_imagen(
            "http://127.0.0.1:8188", "positivo", "negativo", self.destino,
            1234, 64, 64, 4, 6.0, "modelo.safetensors",
            espera=espera, ancla=None, registro=self.registro, **kw)

    def _ultimo_suceso(self):
        sucesos = self.registro.sucesos()
        self.assertTrue(sucesos)
        return sucesos[-1]

    def test_timeout_no_cancela_el_trabajo(self):
        llamadas = []

        def fake_post(url, payload, timeout=30):
            llamadas.append(url)
            return {"prompt_id": "p1"}

        def fake_get(url, timeout=15):
            raise AssertionError("no deberia consultar con espera=0")

        with mock.patch.object(comfy, "_post_json", fake_post), \
                mock.patch.object(comfy, "_get", fake_get):
            ok = self._llamar(espera=0)

        self.assertFalse(ok)
        ultimo = self._ultimo_suceso()
        self.assertEqual(ultimo["estado"], "timeout")
        self.assertEqual(ultimo["motivo"], "no_cancelado_en_comfyui")
        self.assertEqual(ultimo["prompt_id"], "p1")
        # Nunca se llama a cancelar/interrumpir ni a la cola.
        self.assertTrue(all("/prompt" in u for u in llamadas))

    def test_finalizado_escribe_el_png(self):
        def fake_post(url, payload, timeout=30):
            return {"prompt_id": "p1"}

        def fake_get(url, timeout=15):
            if "/history/" in url:
                return json.dumps({"p1": {
                    "status": {"status_str": "success"},
                    "outputs": {"9": {"images": [
                        {"filename": "x.png", "subfolder": "", "type": "output"}]}},
                }}).encode("utf-8")
            if "/view?" in url:
                return b"\x89PNG\r\n\x1a\n" + b"datos"
            raise AssertionError(url)

        with mock.patch.object(comfy, "_post_json", fake_post), \
                mock.patch.object(comfy, "_get", fake_get):
            ok = self._llamar()

        self.assertTrue(ok)
        self.assertTrue(os.path.exists(self.destino))
        self.assertEqual(self._ultimo_suceso()["estado"], "finalizado")

    def test_error_de_comfyui_es_fallido(self):
        def fake_post(url, payload, timeout=30):
            return {"prompt_id": "p1"}

        def fake_get(url, timeout=15):
            return json.dumps({"p1": {"status": {"status_str": "error"}}}).encode("utf-8")

        with mock.patch.object(comfy, "_post_json", fake_post), \
                mock.patch.object(comfy, "_get", fake_get):
            ok = self._llamar()

        self.assertFalse(ok)
        self.assertEqual(self._ultimo_suceso()["estado"], "fallido")

    def test_cierre_inesperado_es_desconocido(self):
        def fake_post(url, payload, timeout=30):
            return {"prompt_id": "p1"}

        def fake_get(url, timeout=15):
            raise urllib.error.URLError("ComfyUI se cerro")

        with mock.patch.object(comfy, "_post_json", fake_post), \
                mock.patch.object(comfy, "_get", fake_get):
            ok = self._llamar()

        self.assertFalse(ok)
        self.assertEqual(self._ultimo_suceso()["estado"], "desconocido")

    def test_error_de_conexion_es_desconocido(self):
        def fake_post(url, payload, timeout=30):
            raise urllib.error.URLError("sin servidor")

        with mock.patch.object(comfy, "_post_json", fake_post):
            ok = self._llamar()

        self.assertFalse(ok)
        self.assertEqual(self._ultimo_suceso()["estado"], "desconocido")

    def test_el_registro_no_guarda_prompts(self):
        def fake_post(url, payload, timeout=30):
            return {"prompt_id": "p1"}

        def fake_get(url, timeout=15):
            raise urllib.error.URLError("se cerro")

        with mock.patch.object(comfy, "_post_json", fake_post), \
                mock.patch.object(comfy, "_get", fake_get):
            self._llamar()

        permitidas = {"ts", "job_id", "estado", "prompt_id", "motivo"}
        for suceso in self.registro.sucesos():
            self.assertTrue(set(suceso).issubset(permitidas), suceso)

    def test_activos_incluye_timeout(self):
        self.registro.registrar("a", "pendiente")
        self.registro.registrar("a", "timeout", motivo="no_cancelado_en_comfyui")
        self.registro.registrar("b", "finalizado")
        activos = self.registro.activos()
        self.assertEqual([s["job_id"] for s in activos], ["a"])
        self.assertEqual(self.registro.ultimo_estado("a")["estado"], "timeout")

    # ------------------------------------------------------ portero v0.3 -----
    def test_abrir_portero_solo_afecta_a_cartas(self):
        # Con un coordinador que denegaria "carta", los otros tipos jamas
        # llegan a el: `_abrir_portero` devuelve un no-op para escena/variante/
        # avatar (los otros tres scripts siguen en modo observador).
        class _CoordFalso:
            def portero(self, tipo):
                raise comfy.AdmisionDenegada("trabajo previo", [])

        prev = comfy._coordinador
        comfy._coordinador = _CoordFalso()
        try:
            for tipo in ("escena", "variante", "avatar", "imagen"):
                with self.subTest(tipo=tipo):
                    self.assertFalse(comfy._abrir_portero(tipo).activo)
            with self.assertRaises(comfy.AdmisionDenegada):
                comfy._abrir_portero("carta")
        finally:
            comfy._coordinador = prev

    def test_portero_denegado_aborta_sin_postear(self):
        class _CoordFalso:
            def portero(self, tipo):
                raise comfy.AdmisionDenegada("trabajo previo", [])

        llamadas = []

        def fake_post(url, payload, timeout=30):
            llamadas.append(url)
            return {"prompt_id": "p1"}

        prev = comfy._coordinador
        comfy._coordinador = _CoordFalso()
        try:
            with mock.patch.object(comfy, "_post_json", fake_post):
                ok = self._llamar(espera=0, tipo="carta")
        finally:
            comfy._coordinador = prev

        self.assertFalse(ok)
        self.assertEqual(llamadas, [])  # ni siquiera se envia el workflow
        self.assertEqual(self._ultimo_suceso()["motivo"], "portero_denego")

    def test_carta_con_portero_apagado_genera_igual_que_v0_2(self):
        # Por defecto el portero esta apagado: una carta se genera exactamente
        # como en v0.2 (envuelta en un no-op).
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 32

        def fake_post(url, payload, timeout=30):
            return {"prompt_id": "p1"}

        def fake_get(url, timeout=15):
            if "/history/" in url:
                return json.dumps({"p1": {
                    "status": {"status_str": "success"},
                    "outputs": {"9": {"images": [
                        {"filename": "x.png", "subfolder": "", "type": "output"}]}},
                }}).encode("utf-8")
            with open(self.destino, "wb") as f:
                f.write(png)
            return png

        with mock.patch.object(comfy, "_post_json", fake_post), \
                mock.patch.object(comfy, "_get", fake_get):
            ok = self._llamar(tipo="carta")
        self.assertTrue(ok)
        self.assertEqual(self._ultimo_suceso()["estado"], "finalizado")

    # ------------------------------------------------------ salida CLI -------
    def test_salida_png_es_el_archivo_exacto(self):
        ruta = os.path.join(self.tmp, "directo.png")
        carpeta, destino = comfy._resolver_destino_salida(
            ruta, "humano", "Test Carta")
        self.assertEqual(destino, os.path.abspath(ruta))
        self.assertEqual(carpeta, os.path.dirname(os.path.abspath(ruta)))

    def test_salida_carpeta_conserva_nombre_generado(self):
        carpeta = os.path.join(self.tmp, "salida")
        os.makedirs(carpeta)
        _, destino = comfy._resolver_destino_salida(
            carpeta, "humano", "Test Carta")
        self.assertEqual(os.path.dirname(destino), os.path.abspath(carpeta))
        self.assertTrue(destino.lower().endswith("humano_test_carta.png"))

    def test_carpeta_existente_terminada_en_png_sigue_siendo_carpeta(self):
        carpeta = os.path.join(self.tmp, "coleccion.png")
        os.makedirs(carpeta)
        _, destino = comfy._resolver_destino_salida(
            carpeta, "humano", "Test Carta")
        self.assertEqual(os.path.dirname(destino), os.path.abspath(carpeta))

    def test_salida_png_existente_no_se_sobrescribe_sin_fuerza(self):
        ruta = os.path.join(self.tmp, "protegido.png")
        contenido = b"no sobrescribir"
        with open(ruta, "wb") as f:
            f.write(contenido)
        args = SimpleNamespace(
            negativo="", salida=ruta, solo_prompt=False, fuerza=False,
            ancho=512, alto=512, steps=20, cfg=7.0,
            modelo="modelo.safetensors", espera=1, ancla=None,
            peso_ipadapter=0.35, peso_tipo="style transfer")
        ficha = {"nombre": "Test Carta", "faccion": "humano", "seed": 1}
        with mock.patch.object(comfy, "generar_imagen") as generar:
            resultado = comfy.procesar(ficha, args, "http://127.0.0.1:8188")
        self.assertEqual(resultado, "omitida")
        generar.assert_not_called()
        with open(ruta, "rb") as f:
            self.assertEqual(f.read(), contenido)


if __name__ == "__main__":
    unittest.main()
