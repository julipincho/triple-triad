"""Selección optativa de lotes importados; nunca redirige cartas ni HD explícitos."""
import hashlib
import json
import os
import re
from functools import lru_cache

from paths import recurso


def clave_escena(datos):
    campos = ('texto', 'fondo', 'fondo_hd', 'hablante', 'retrato', 'mundo', 'efecto')
    contenido = {k: datos.get(k) for k in campos}
    return hashlib.sha256(json.dumps(contenido, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


@lru_cache(maxsize=1)
def registro():
    if os.environ.get('TRIPLETRIAD_LOTES_VISUALES', '1') == '0':
        return {}
    try:
        with open(recurso('assets/lotes_visuales/registro.json'), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


@lru_cache(maxsize=256)
def _buscar(tipo, clave):
    for lote in registro().get('lotes', {}).values():
        if not lote.get('activo'):
            continue
        for item in lote.get('recursos', []):
            if item.get('estado') != 'listo' or item.get('tipo') != tipo:
                continue
            destinos = item.get('claves', []) if tipo == 'fondo' else [item.get('personaje')]
            if clave not in destinos:
                continue
            ruta = item['ruta']
            if not re.fullmatch(r'assets/lotes_visuales/[a-z0-9_-]+/(fondos|retratos)/[a-z0-9_-]+\.png', ruta):
                continue
            try:
                with open(recurso(ruta), 'rb') as f:
                    if hashlib.sha256(f.read()).hexdigest() == item['sha256']:
                        return ruta
            except OSError:
                pass
    return None


def fondo(datos):
    return None if datos.get('fondo_hd') else _buscar('fondo', clave_escena(datos))


def retrato(ruta):
    match = re.fullmatch(r'assets/avatar_([a-z0-9_]+)\.png', os.fspath(ruta).replace('\\', '/'))
    return _buscar('retrato', match[1]) if match else None
