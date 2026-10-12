"""Coordinacion entre procesos para la generacion de imagenes con ComfyUI.

Este modulo es la pieza compartida por los cuatro scripts de generacion
(`generar_cartas_comfyui.py`, `generar_escenas.py`, `generar_variantes.py`,
`generar_avatares_local.py`). No genera imagenes ni arranca servicios por si
solo: solo coordina. El juego NUNCA importa este modulo.

Aporta tres cosas, sin dependencias externas (solo biblioteca estandar):

1. **Bloqueo entre procesos** para que dos scripts no arranquen ComfyUI a la
   vez. En Windows usa un *mutex con nombre* del kernel; si no estuviera
   disponible, un bloqueo por rango de bytes en un archivo. En ambos casos el
   sistema operativo libera el bloqueo solo si el proceso muere: no quedan
   bloqueos permanentes.
2. **Lectura del estado real de la cola** de ComfyUI (`GET /queue`), que
   distingue `vacia`, `ocupada` y `desconocida`.
3. **Registro minimo de trabajos** (id, estado, tiempos, prompt_id) en un
   JSONL. Sin prompts, sin credenciales y sin rutas de usuario.

Politica de arranque
--------------------
`arrancar_con_bloqueo` primero comprueba el servidor sin bloquear; si esta
caido, toma el bloqueo, **vuelve a comprobar** (por si otro script lo arranco
mientras esperaba) y solo entonces lanza el `.bat`. El bloqueo cubre unicamente
el arranque, no toda la generacion: ComfyUI ya tiene su propia cola interna y
serializa los trabajos.

LIMITACIONES (ver tambien `E:\\AI\\stop_comfyui.ps1`)
----------------------------------------------------
- ComfyUI 0.39 no expone un endpoint de apagado ordenado (solo `/interrupt` y
  `/free`). Por eso la detencion de ComfyUI queda **deshabilitada** por
  politica: sin exclusion fiable de nuevas tareas ni apagado ordenado no se
  detiene nada. Este modulo no ofrece ninguna funcion de apagado.
- Un timeout de generacion **NO** cancela el trabajo en ComfyUI: queda
  registrado como `timeout` y puede seguir vivo. Nunca se envia cancelacion.

La funcion pura `evaluar_parada` es el espejo en Python de la politica que
aplica `stop_comfyui.ps1`; las dos deben coincidir y `evaluar_parada` esta
cubierta por `tests/test_coord_comfyui.py`.
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid

# --------------------------------------------------------------- constantes ---

BASE = os.path.dirname(os.path.abspath(__file__))

#: Nombre del mutex de arranque compartido por todos los scripts.
NOMBRE_MUTEX = r"Local\CartonesComfyArranque"
#: Archivo de bloqueo alternativo (solo si el mutex no estuviera disponible).
RUTA_BLOQUEO_TEMP = os.path.join(tempfile.gettempdir(), "cartones_comfy_arranque.lock")
#: Registro minimo de trabajos (fuera de assets: no lo consume el juego).
RUTA_REGISTRO = os.path.join(BASE, "auditoria", "trabajos_comfyui.jsonl")

#: Estados de un trabajo. `timeout` NO significa cancelado.
ESTADOS_TRABAJO = ("pendiente", "en_ejecucion", "finalizado", "fallido",
                   "desconocido", "timeout")
#: Estados que pueden seguir activos en ComfyUI (incluido el timeout).
ESTADOS_ACTIVOS = ("pendiente", "en_ejecucion", "timeout")

ACCION_NADA = "nada"
ACCION_RECHAZAR = "rechazar"
ACCION_DETENER = "detener"

_ESTADO_COLA_VACIA = "vacia"
_ESTADO_COLA_OCUPADA = "ocupada"
_ESTADO_COLA_DESCONOCIDA = "desconocida"


# ----------------------------------------------------------------- bloqueo ---

class _MutexWindows:
    """Mutex con nombre de Windows: exclusion real entre procesos.

    Es un objeto del kernel: si el proceso muere sin liberarlo, Windows lo
    marca como abandonado y el siguiente que espere lo recibe igualmente, asi
    que no quedan bloqueos permanentes. La propiedad es por hilo, por eso el
    mismo hilo puede re-adquirirlo (no se usa asi) y otro hilo/proceso espera.
    """

    WAIT_OBJECT_0 = 0x00000000
    WAIT_ABANDONED = 0x00000080
    WAIT_TIMEOUT = 0x00000102
    INFINITE = 0xFFFFFFFF

    def __init__(self, nombre=NOMBRE_MUTEX):
        import ctypes
        from ctypes import wintypes

        self.nombre = nombre
        self._k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._k32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL,
                                           wintypes.LPCWSTR]
        self._k32.CreateMutexW.restype = wintypes.HANDLE
        self._k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._k32.WaitForSingleObject.restype = wintypes.DWORD
        self._k32.ReleaseMutex.argtypes = [wintypes.HANDLE]
        self._k32.ReleaseMutex.restype = wintypes.BOOL
        self._k32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._k32.CloseHandle.restype = wintypes.BOOL
        self._handle = None
        self._poseido = False

    def adquirir(self, timeout=30):
        handle = self._k32.CreateMutexW(None, False, self.nombre)
        if not handle:
            return False
        if timeout is None:
            ms = self.INFINITE
        else:
            ms = int(max(0.0, timeout) * 1000)
        rc = self._k32.WaitForSingleObject(handle, ms)
        if rc in (self.WAIT_OBJECT_0, self.WAIT_ABANDONED):
            self._handle = handle
            self._poseido = True
            return True
        self._k32.CloseHandle(handle)
        return False

    def liberar(self):
        if self._handle and self._poseido:
            try:
                self._k32.ReleaseMutex(self._handle)
            finally:
                self._k32.CloseHandle(self._handle)
        self._handle = None
        self._poseido = False


class _BloqueoArchivo:
    """Bloqueo por rango de bytes en un archivo (alternativa al mutex).

    Se libera solo al cerrar el descriptor o al morir el proceso: tampoco deja
    bloqueos permanentes tras un cierre inesperado.
    """

    def __init__(self, ruta=RUTA_BLOQUEO_TEMP):
        self.ruta = ruta
        self._fd = None

    def _abrir(self):
        fd = os.open(self.ruta, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            os.write(fd, str(os.getpid()).encode("ascii"))
        except OSError:
            pass
        return fd

    def _intentar(self, fd):
        os.lseek(fd, 0, os.SEEK_SET)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def adquirir(self, timeout=30):
        limite = None if timeout is None else time.monotonic() + max(0.0, timeout)
        fd = self._abrir()
        while True:
            try:
                self._intentar(fd)
                self._fd = fd
                return True
            except OSError:
                if limite is not None and time.monotonic() >= limite:
                    os.close(fd)
                    return False
                time.sleep(0.05)

    def liberar(self):
        if self._fd is not None:
            try:
                os.lseek(self._fd, 0, os.SEEK_SET)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self._fd, fcntl.LOCK_UN)
            except OSError:
                pass
            os.close(self._fd)
            self._fd = None


def crear_bloqueo(nombre=NOMBRE_MUTEX, ruta=RUTA_BLOQUEO_TEMP):
    """Devuelve un bloqueo nuevo con `.adquirir(timeout)` y `.liberar()`."""
    if os.name == "nt":
        try:
            return _MutexWindows(nombre)
        except Exception:  # noqa: BLE001 - sin mutex, se usa el archivo
            return _BloqueoArchivo(ruta)
    return _BloqueoArchivo(ruta)


# ------------------------------------------------------------ HTTP de Comfy ---

def _get(url, timeout=15):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read()


def comprobar_servidor(servidor, timeout=5):
    """Devuelve la version de ComfyUI o None si no responde."""
    try:
        datos = json.loads(_get(f"{servidor}/system_stats", timeout=timeout).decode("utf-8"))
        return datos.get("system", {}).get("comfyui_version", "desconocida")
    except Exception:  # noqa: BLE001 - sin servidor o apagado
        return None


def clasificar_cola(payload):
    """Clasifica la respuesta de `GET /queue`. Pura, para poder probarla.

    Devuelve `{estado, en_ejecucion, pendientes}` con estado `vacia`, `ocupada`
    o `desconocida`. Cualquier forma inesperada es `desconocida` (nunca se
    asume vacia por omision).
    """
    if not isinstance(payload, dict):
        return {"estado": _ESTADO_COLA_DESCONOCIDA, "en_ejecucion": None, "pendientes": None}
    corriendo = payload.get("queue_running")
    pendientes = payload.get("queue_pending")
    if not isinstance(corriendo, list) or not isinstance(pendientes, list):
        return {"estado": _ESTADO_COLA_DESCONOCIDA, "en_ejecucion": None, "pendientes": None}
    estado = _ESTADO_COLA_OCUPADA if (corriendo or pendientes) else _ESTADO_COLA_VACIA
    return {"estado": estado, "en_ejecucion": len(corriendo), "pendientes": len(pendientes)}


def estado_cola(servidor, timeout=5):
    """Lee `GET /queue` y lo clasifica. Devuelve estado `desconocida` si falla."""
    try:
        payload = json.loads(_get(f"{servidor}/queue", timeout=timeout).decode("utf-8"))
    except Exception:  # noqa: BLE001 - cola inaccesible
        return {"estado": _ESTADO_COLA_DESCONOCIDA, "en_ejecucion": None, "pendientes": None}
    return clasificar_cola(payload)


def esperar_servidor(servidor, espera, pausa=2.0, dormir=time.sleep, chequeo=None):
    """Espera hasta `espera` segundos a que ComfyUI responda. Version o None."""
    chequeo = chequeo or comprobar_servidor
    inicio = time.monotonic()
    while True:
        version = chequeo(servidor)
        if version:
            return version
        if time.monotonic() - inicio >= espera:
            return None
        dormir(pausa)


# --------------------------------------------------------------- arranque ----

class ResultadoArranque:
    """Resultado de `arrancar_con_bloqueo` (booleano segun `ok`)."""

    def __init__(self, ok, version=None, arrancado=False, motivo=None, segundos=0.0):
        self.ok = ok
        self.version = version
        self.arrancado = arrancado
        self.motivo = motivo
        self.segundos = segundos

    def __bool__(self):
        return bool(self.ok)

    def __repr__(self):
        return (f"ResultadoArranque(ok={self.ok!r}, version={self.version!r}, "
                f"arrancado={self.arrancado!r}, motivo={self.motivo!r}, "
                f"segundos={self.segundos!r})")


def _lanzar_bat(bat):
    """Abre el bat de arranque en una consola nueva (mismo comando de siempre)."""
    nueva_consola = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)
    mas_nueva = nueva_consola | getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0x01000000)
    try:
        subprocess.Popen(f'cmd.exe /c "{bat}"', creationflags=mas_nueva)
    except OSError:
        subprocess.Popen(f'cmd.exe /c "{bat}"', creationflags=nueva_consola)


def arrancar_con_bloqueo(servidor, bat, espera, pausa=2.0, espera_bloqueo=30.0,
                         chequeo=None, lanzador=None, bloqueo_factory=crear_bloqueo,
                         dormir=time.sleep, log=None):
    """Arranca ComfyUI a lo sumo una vez, serializando entre procesos.

    - Comprueba el servidor sin bloquear (si ya responde, no toca nada).
    - Toma el bloqueo de arranque; si no lo consigue, **no lanza**: espera a que
      el otro proceso que lo tiene termine de arrancar el servidor.
    - Con el bloqueo tomado, **vuelve a comprobar** el servidor antes de lanzar.
    - `chequeo`, `lanzador`, `bloqueo_factory` y `dormir` son inyectables para
      poder probar sin arrancar nada real.
    """
    avisar = log or (lambda *a, **k: None)
    chequeo = chequeo or comprobar_servidor
    lanzador = lanzador or _lanzar_bat

    version = chequeo(servidor)
    if version:
        return ResultadoArranque(True, version, arrancado=False)

    if not os.path.exists(bat):
        return ResultadoArranque(False, motivo="bat_ausente")

    candado = bloqueo_factory()
    if not candado.adquirir(espera_bloqueo):
        # Otro proceso esta arrancando: esperar sin lanzar una segunda ventana.
        version = esperar_servidor(servidor, espera, pausa, dormir, chequeo)
        if version:
            return ResultadoArranque(True, version, arrancado=False, motivo="bloqueo_ajeno")
        return ResultadoArranque(False, motivo="bloqueo")

    inicio = time.monotonic()
    try:
        # Recomprabar DESPUES de adquirir: evita el doble arranque.
        version = chequeo(servidor)
        if version:
            return ResultadoArranque(True, version, arrancado=False)
        avisar(f"ComfyUI no esta en marcha: arrancando {bat}")
        avisar("  esperando a que este listo (ha abierto una ventana de ComfyUI)...")
        try:
            lanzador(bat)
        except Exception as e:  # noqa: BLE001 - no se pudo abrir la consola
            avisar(f"  no pude arrancarlo: {e}")
            return ResultadoArranque(False, motivo="no_lanza")
        version = esperar_servidor(servidor, espera, pausa, dormir, chequeo)
        segundos = time.monotonic() - inicio
        if version:
            return ResultadoArranque(True, version, arrancado=True, segundos=segundos)
        return ResultadoArranque(False, motivo="no_responde", segundos=segundos)
    finally:
        candado.liberar()


# ------------------------------------------------------- registro de trabajos --

def nuevo_id():
    """Identificador unico de un trabajo (sin datos del usuario)."""
    return uuid.uuid4().hex


class RegistroTrabajos:
    """Registro minimo append-only (JSONL) de trabajos de generacion.

    Cada linea es `{ts, job_id, estado, [prompt_id], [motivo]}`. No guarda
    prompts, credenciales ni rutas de usuario. Pensado para detectar trabajos
    que puedan seguir activos.
    """

    def __init__(self, ruta=None):
        self.ruta = ruta or RUTA_REGISTRO

    def registrar(self, job_id, estado, motivo="", prompt_id=None):
        if estado not in ESTADOS_TRABAJO:
            raise ValueError(f"estado desconocido: {estado}")
        registro = {"ts": time.time(), "job_id": job_id, "estado": estado}
        if prompt_id:
            registro["prompt_id"] = prompt_id
        if motivo:
            registro["motivo"] = motivo
        carpeta = os.path.dirname(self.ruta)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with open(self.ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

    def sucesos(self):
        """Lista de sucesos leidos; tolera lineas corruptas."""
        if not os.path.exists(self.ruta):
            return []
        salida = []
        with open(self.ruta, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    salida.append(json.loads(linea))
                except ValueError:
                    continue
        return salida

    def ultimo_estado(self, job_id):
        """Ultimo suceso de un trabajo, o None si no aparece."""
        ultimo = None
        for suceso in self.sucesos():
            if suceso.get("job_id") == job_id:
                ultimo = suceso
        return ultimo

    def activos(self):
        """Trabajos cuyo ultimo estado puede seguir activo en ComfyUI."""
        ultimo = {}
        for suceso in self.sucesos():
            ultimo[suceso.get("job_id")] = suceso
        return [s for s in ultimo.values() if s.get("estado") in ESTADOS_ACTIVOS]


# --------------------------------------------------- politica de detencion ---

def evaluar_parada(hay_proceso, identidad, estado_cola_actual,
                   exclusion_fiable=False, apagado_ordenado=False):
    """Politica conservadora de detencion. Pura, para poder probarla.

    Espejo en Python de la que aplica `stop_comfyui.ps1`. Devuelve
    `{"accion", "motivo"}` con accion `nada`, `rechazar` o `detener`.

    Reglas:
      - Sin proceso: `nada` (no hay nada que detener).
      - Identidad no inequivoca: `rechazar`.
      - Cola ocupada: `rechazar`.
      - Cola desconocida: `rechazar`.
      - Cola vacia: NO basta por si sola. Solo se detiene si hay exclusion
        fiable de nuevas tareas **y** apagado ordenado; hoy ninguno existe, asi
        que se rechaza.
    """
    if not hay_proceso:
        return {"accion": ACCION_NADA, "motivo": "sin_proceso"}
    if identidad != "inequivoca":
        return {"accion": ACCION_RECHAZAR, "motivo": "identidad_no_inequivoca"}
    if estado_cola_actual == _ESTADO_COLA_OCUPADA:
        return {"accion": ACCION_RECHAZAR, "motivo": "cola_ocupada"}
    if estado_cola_actual != _ESTADO_COLA_VACIA:
        return {"accion": ACCION_RECHAZAR, "motivo": "cola_desconocida"}
    if not (exclusion_fiable and apagado_ordenado):
        return {"accion": ACCION_RECHAZAR,
                "motivo": "cola_vacia_sin_exclusion_ni_apagado_ordenado"}
    return {"accion": ACCION_DETENER, "motivo": "seguro"}


if __name__ == "__main__":  # pragma: no cover - utilidad manual
    objetivo = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8188"
    print("version :", comprobar_servidor(objetivo))
    print("cola    :", estado_cola(objetivo))
    print("activos :", len(RegistroTrabajos().activos()))
