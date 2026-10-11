"""Escritura atomica: un fallo conserva el ultimo JSON completo."""

import json
import os
import tempfile
from contextlib import contextmanager
from contextvars import ContextVar


_lote = ContextVar("guardado_en_lote", default=None)
_DIARIO = ".progreso_pendiente.json"


class ErrorGuardado(OSError):
    """El progreso nuevo no pudo confirmarse en disco."""


def _guardar_atomico(ruta, datos):
    # Serializar antes de abrir archivos: un dato invalido no trunca el save.
    contenido = json.dumps(datos, ensure_ascii=False, indent=2)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=os.path.dirname(os.path.abspath(ruta)),
                prefix=".guardado_", suffix=".tmp", delete=False) as f:
            temporal = f.name
            f.write(contenido)
            f.flush()
            os.fsync(f.fileno())
        # Mismo directorio/volumen: nunca se expone un archivo a medio escribir.
        os.replace(temporal, ruta)
    except OSError as exc:
        raise ErrorGuardado(f"No se pudo guardar {os.path.basename(ruta)}. "
                            "Se conserva el ultimo guardado completo.") from exc
    finally:
        if temporal and os.path.exists(temporal):
            try:
                os.remove(temporal)
            except OSError:
                pass


def recuperar(directorio):
    """Termina un commit interrumpido antes de exponer perfil o campana."""
    diario = os.path.join(directorio, _DIARIO)
    if not os.path.exists(diario):
        return
    with open(diario, encoding="utf-8") as f:
        archivos = json.load(f)["archivos"]
    for nombre, datos in archivos.items():
        if os.path.basename(nombre) != nombre or not nombre.endswith(".json"):
            raise ErrorGuardado("El diario de progreso contiene una ruta invalida.")
        _guardar_atomico(os.path.join(directorio, nombre), datos)
    try:
        os.remove(diario)
    except OSError as exc:
        raise ErrorGuardado("No se pudo confirmar el guardado de progreso.") from exc


def guardar_json(ruta, datos):
    ruta = os.path.abspath(ruta)
    lote = _lote.get()
    if lote is not None:
        # Una instantanea, no una referencia que el caller pueda modificar.
        lote[ruta] = json.loads(json.dumps(datos, ensure_ascii=False))
        return
    recuperar(os.path.dirname(ruta))
    _guardar_atomico(ruta, datos)


def leer_json(ruta):
    ruta = os.path.abspath(ruta)
    lote = _lote.get()
    if lote is not None and ruta in lote:
        return json.loads(json.dumps(lote[ruta], ensure_ascii=False))
    if lote is None:
        recuperar(os.path.dirname(ruta))
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


@contextmanager
def transaccion(directorio):
    """Agrupa perfil y campana; el diario permite completar ambos al reabrir."""
    if _lote.get() is not None:
        yield  # las operaciones anidadas pertenecen al mismo commit
        return
    directorio = os.path.abspath(directorio)
    recuperar(directorio)
    lote = {}
    token = _lote.set(lote)
    try:
        yield
        archivos = {}
        for ruta, datos in lote.items():
            if os.path.dirname(ruta) != directorio:
                raise ErrorGuardado("El progreso debe guardarse en un mismo directorio.")
            archivos[os.path.basename(ruta)] = datos
        if archivos:
            _guardar_atomico(os.path.join(directorio, _DIARIO), {"archivos": archivos})
            recuperar(directorio)
    finally:
        _lote.reset(token)
