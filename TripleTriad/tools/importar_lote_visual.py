"""Importador ZIP con activación atómica y evidencia separada de los assets."""
import argparse
from contextlib import contextmanager
import hashlib
import html
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import zipfile

from PIL import Image

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from lotes_visuales import clave_escena

INCOMING = Path('E:/AI/CartonesMazmorrasVisual/incoming')
ID = re.compile(r'[a-z0-9][a-z0-9_-]{0,63}')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def guardar(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporal = path.with_suffix('.tmp')
    temporal.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    os.replace(temporal, path)


def catalogo():
    import prologo
    resultado = {}
    for bloque in ('pre_duelo', 'post_duelo', 'carta_umbral', 'transporte', 'despertar',
                   'encuentro_hostil', 'nara', 'explicacion', 'cierre'):
        for i, datos in enumerate(getattr(prologo, 'escenas_' + bloque)()):
            resultado[f'prologo.{bloque}.{i}'] = datos
    return resultado


class Importador:
    def __init__(self, root=BASE, incoming=INCOMING, escenas=None):
        self.root, self.incoming = Path(root), Path(incoming)
        self.base = self.root / 'assets/lotes_visuales'
        self.file = self.base / 'registro.json'
        self.escenas = catalogo() if escenas is None else escenas

    @contextmanager
    def bloqueo(self):
        self.base.mkdir(parents=True, exist_ok=True)
        lock = self.base / '.lock'
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise ValueError('Hay otra importación o un bloqueo pendiente: ' + str(lock))
        try:
            os.close(fd)
            yield
        finally:
            lock.unlink()

    def iniciar(self):
        self.incoming.mkdir(parents=True, exist_ok=True)
        if self.file.exists():
            return self.verificar()
        protegidos = {}
        for patron in ('assets/cinematicas_hd/*.png', 'assets/avatar_*.png',
                       'assets/fondos/*.png', 'assets/escenas/*.png',
                       'assets/pixel_anime/**/*.png', 'assets/pixel_anime/manifest.json'):
            for p in self.root.glob(patron):
                protegidos[p.relative_to(self.root).as_posix()] = digest(p.read_bytes())
        historicos = []
        auditoria = self.root / 'auditoria/consolidacion_20261014/proteccion.json'
        if auditoria.exists():
            previo = json.loads(auditoria.read_text(encoding='utf-8'))
            historicos = previo['lotes']
            for lote in historicos:
                for item in lote['recursos']:
                    p = Path(item['runtime'])
                    esperado = next(x['sha256'] for x in previo['archivos'] if x['ruta'] == str(p))
                    if digest(p.read_bytes()) != esperado:
                        raise ValueError('HD protegido alterado: ' + str(p))
        data = {'version': 1, 'historicos': historicos, 'protegidos': protegidos,
                'lotes': {}, 'eventos': []}
        guardar(self.file, data)
        self.exportar_catalogo()
        return data

    def exportar_catalogo(self):
        guardar(self.incoming / 'catalogo_destinos.json', {
            'escenas': {k: {'texto': v.get('texto'), 'protegida': bool(v.get('fondo_hd')),
                            'clave': clave_escena(v)} for k, v in self.escenas.items()},
            'personajes': sorted(p.stem.removeprefix('avatar_') for p in self.root.glob('assets/avatar_*.png'))})

    def verificar(self):
        data = json.loads(self.file.read_text(encoding='utf-8'))
        for ruta, esperado in data['protegidos'].items():
            p = self.root / ruta
            if not p.is_file() or digest(p.read_bytes()) != esperado:
                raise ValueError('Recurso protegido ausente/alterado: ' + ruta)
        for lote in data['lotes'].values():
            for ruta, esperado in lote['archivos'].items():
                p = self.root / ruta
                if not p.is_file() or digest(p.read_bytes()) != esperado:
                    raise ValueError('Lote inmutable alterado: ' + ruta)
        return data

    def preparar(self, paquete):
        data = self.iniciar()
        raw = Path(paquete).read_bytes()
        paquete_hash = digest(raw)
        for nombre, lote in data['lotes'].items():
            if lote['zip_sha256'] == paquete_hash:
                return nombre  # Idempotencia; no volver a extraer.
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            nombres = set()
            total = 0
            for info in z.infolist():
                nombre = info.filename
                p = PurePosixPath(nombre)
                normal = nombre.rstrip('/').casefold()
                if (p.is_absolute() or '..' in p.parts or '\\' in nombre or ':' in nombre
                        or normal in nombres or (info.external_attr >> 16) & 0o170000 == 0o120000):
                    raise ValueError('Ruta ZIP insegura/duplicada: ' + nombre)
                if any(part.endswith(('.', ' ')) for part in p.parts):
                    raise ValueError('Ruta ZIP ambigua: ' + nombre)
                nombres.add(normal)
                total += info.file_size
                if info.file_size > 32 * 1024 * 1024 or total > 256 * 1024 * 1024 or len(nombres) > 500:
                    raise ValueError('ZIP excede límites: 32 MB/archivo, 256 MB, 500 entradas')
            if z.testzip():
                raise ValueError('CRC ZIP inválido')
            contenido = {i.filename: z.read(i) for i in z.infolist() if not i.is_dir()}
        if 'manifest.json' not in contenido:
            raise ValueError('Falta manifest.json en la raíz del ZIP')
        manifest = json.loads(contenido['manifest.json'].decode('utf-8-sig'))
        nombre = manifest.get('lote', '')
        if manifest.get('version') != 1 or not isinstance(nombre, str) or not ID.fullmatch(nombre):
            raise ValueError('Se requiere version=1 y lote alfanumérico minúsculo')
        if nombre in data['lotes'] or (self.base / nombre).exists():
            raise ValueError('Identificador de lote ya reservado; usar otro, nunca sobrescribir')
        recursos = manifest.get('recursos')
        if not isinstance(recursos, list) or not recursos:
            raise ValueError('recursos debe ser una lista no vacía')
        ids, usados, destinos = set(), set(), set()
        registros = []
        for item in recursos:
            ident, tipo = item.get('id', ''), item.get('tipo')
            if not isinstance(ident, str) or not ID.fullmatch(ident) or ident in ids:
                raise ValueError('ID inválido o duplicado')
            ids.add(ident)
            if tipo not in ('fondo', 'retrato') or not isinstance(item.get('nombre'), str) or not item['nombre'].strip():
                raise ValueError('Recurso requiere nombre y tipo fondo/retrato')
            archivo = item.get('archivo')
            if archivo not in contenido or not archivo.lower().endswith('.png') or archivo in usados:
                raise ValueError('PNG ausente/duplicado: ' + str(archivo))
            usados.add(archivo)
            png = contenido[archivo]
            h = digest(png)
            if item.get('sha256') is not None and item['sha256'] != h:
                raise ValueError('SHA-256 incorrecto: ' + archivo)
            esperado = (1280, 720) if tipo == 'fondo' else (256, 256)
            with Image.open(io.BytesIO(png)) as im:
                if im.format != 'PNG' or im.size != esperado or im.mode not in ('RGB', 'RGBA') or getattr(im, 'n_frames', 1) != 1:
                    raise ValueError('Formato/resolución inválidos: ' + archivo)
                im.verify()
            with Image.open(io.BytesIO(png)) as im:
                im.load()
            if item.get('dimensiones') != list(esperado):
                raise ValueError('Dimensiones declaradas incorrectas: ' + archivo)
            razon, claves = [], []
            escenas = item.get('escenas', [])
            if not isinstance(escenas, list) or not all(isinstance(s, str) for s in escenas):
                raise ValueError('escenas debe ser lista de IDs')
            personaje = item.get('personaje')
            if tipo == 'fondo':
                if not escenas:
                    razon.append('Sin asignación narrativa')
                for escena in escenas:
                    datos = self.escenas.get(escena)
                    if datos is None:
                        razon.append('Escena desconocida: ' + escena)
                    elif datos.get('fondo_hd'):
                        razon.append('Asignación HD protegida: ' + escena)
                    else:
                        claves.append(clave_escena(datos))
                if personaje:
                    razon.append('Un fondo no asigna personajes')
            else:
                if not isinstance(personaje, str) or not re.fullmatch(r'[a-z0-9_]+', personaje) or not (self.root / f'assets/avatar_{personaje}.png').is_file():
                    razon.append('Personaje ausente/desconocido')
                if escenas:
                    razon.append('Retrato: asignar personaje, no escenas')
            targets = [(tipo, c) for c in (claves if tipo == 'fondo' else [personaje])]
            if not razon and any(t in destinos for t in targets):
                raise ValueError('Dos recursos compiten por el mismo destino')
            if not razon:
                destinos.update(targets)
            carpeta = 'fondos' if tipo == 'fondo' else 'retratos'
            registros.append({**item, 'ruta': f'assets/lotes_visuales/{nombre}/{carpeta}/{ident}.png',
                              'sha256': h, 'hash_proporcionado': item.get('sha256') is not None,
                              'claves': claves, 'personaje': personaje,
                              'estado': 'pendiente' if razon else 'listo', 'motivos': razon})
        # Imágenes sin declarar se preservan en el ZIP, jamás se asignan automáticamente.
        extras = sorted(n for n in contenido if n.lower().endswith('.png') and n not in usados)
        temp = Path(tempfile.mkdtemp(prefix='.preparando_', dir=self.base))
        try:
            (temp / 'paquete_original.zip').write_bytes(raw)
            (temp / 'manifest_original.json').write_bytes(contenido['manifest.json'])
            for item in registros:
                target = temp / Path(item['ruta']).relative_to(f'assets/lotes_visuales/{nombre}')
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(contenido[item['archivo']])
            guardar(temp / 'revision.json', {'recursos': registros, 'png_no_declarados': extras})
            tarjetas = []
            for r in registros:
                ruta = Path(r['ruta']).relative_to(f'assets/lotes_visuales/{nombre}').as_posix()
                tarjetas.append(f'<section><h2>{html.escape(r["nombre"])}</h2><p>{html.escape(r["estado"] + " / " + "; ".join(r["motivos"]))}</p><img class="{r["tipo"]}" src="{ruta}"><p>{html.escape(str(r.get("escenas") or r.get("personaje")))}</p></section>')
            (temp / 'preview.html').write_text('<!doctype html><meta charset="utf-8"><title>Previsualización de lote</title><style>body{background:#151d2c;color:#d8ceb9;font:16px sans-serif}section{margin:24px}img{image-rendering:pixelated;max-width:100%}.fondo{width:1280px}.retrato{width:256px}</style><h1>Candidatos — validación técnica, no aprobación artística</h1>' + ''.join(tarjetas), encoding='utf-8')
            archivos = {f'assets/lotes_visuales/{nombre}/' + p.relative_to(temp).as_posix(): digest(p.read_bytes())
                        for p in temp.rglob('*') if p.is_file()}
            os.rename(temp, self.base / nombre)
            data['lotes'][nombre] = {'activo': False, 'zip_sha256': paquete_hash,
                                    'recursos': registros, 'archivos': archivos, 'png_no_declarados': extras}
            data['eventos'].append({'accion': 'preparar', 'lote': nombre})
            guardar(self.file, data)
        finally:
            if temp.exists():
                shutil.rmtree(temp)
        return nombre

    def activar(self, nombre, activo=True):
        data = self.verificar()
        if nombre not in data['lotes']:
            raise ValueError('Lote desconocido')
        lote = data['lotes'][nombre]
        if activo:
            if not any(r['estado'] == 'listo' for r in lote['recursos']):
                raise ValueError('Todo el lote está pendiente; nada se activa')
            ocupados = set()
            for otro, previo in data['lotes'].items():
                if otro == nombre:
                    continue
                # Los destinos de lotes integrados quedan reservados aun tras revertir.
                if not previo.get('integrado_alguna_vez'):
                    continue
                for r in previo['recursos']:
                    if r['estado'] == 'listo':
                        ocupados.update((r['tipo'], c) for c in (r['claves'] if r['tipo'] == 'fondo' else [r['personaje']]))
            actuales = {clave_escena(e) for e in self.escenas.values() if not e.get('fondo_hd')}
            for r in lote['recursos']:
                if r['estado'] != 'listo':
                    continue
                claves = r['claves'] if r['tipo'] == 'fondo' else [r['personaje']]
                if r['tipo'] == 'fondo' and not set(claves) <= actuales:
                    raise ValueError('El guion cambió desde la preparación; revisar asignaciones')
                if any((r['tipo'], c) in ocupados for c in claves):
                    raise ValueError('Destino reservado por un lote ya integrado')
            lote['integrado_alguna_vez'] = True
        lote['activo'] = activo
        data['eventos'].append({'accion': 'activar' if activo else 'revertir', 'lote': nombre})
        guardar(self.file, data)

    def siguiente(self):
        data = self.iniciar()
        for p in sorted(self.incoming.glob('*.zip'), key=lambda p: (p.stat().st_mtime_ns, p.name)):
            h = digest(p.read_bytes())
            previo = next((v for v in data['lotes'].values() if v['zip_sha256'] == h), None)
            if previo is not None:
                continue
            nombre = self.preparar(p)
            self.activar(nombre)
            return nombre
        raise ValueError('No hay ZIP nuevos; los preparados se activan por nombre')

    def previsualizar(self, nombre):
        """Renderer real antes/candidato; no activa el registro en disco."""
        import copy
        from unittest.mock import patch
        import pygame
        import cinematicas
        import lotes_visuales
        import ui
        data = self.verificar()
        lote = data['lotes'][nombre]
        escenas = set()
        for r in lote['recursos']:
            if r['estado'] != 'listo':
                continue
            if r['tipo'] == 'fondo':
                escenas.update(r.get('escenas', []))
            else:
                escenas.update(k for k, e in self.escenas.items()
                               if (e.get('retrato') or cinematicas.retrato_hablante(e.get('hablante'))) == r['personaje'])
        salida = self.root / 'auditoria/lotes_visuales' / nombre
        salida.mkdir(parents=True, exist_ok=True)
        pygame.init()
        screen = pygame.display.set_mode((1280, 800))
        original_recurso = ui.recurso
        def resolver(ruta):
            if str(ruta).replace('\\', '/').startswith('assets/lotes_visuales/'):
                return str(self.root / ruta)
            return original_recurso(ruta)
        try:
            for etiqueta in ('antes', 'candidato'):
                vista = copy.deepcopy(data)
                vista['lotes'][nombre]['activo'] = etiqueta == 'candidato'
                if etiqueta == 'candidato':
                    candidato = vista['lotes'].pop(nombre)
                    vista['lotes'] = {nombre: candidato, **vista['lotes']}
                with patch.object(lotes_visuales, 'registro', return_value=vista), \
                        patch.object(lotes_visuales, 'recurso', side_effect=resolver), \
                        patch.object(ui, 'recurso', side_effect=resolver):
                    lotes_visuales._buscar.cache_clear()
                    ui.REC.imagenes.clear()
                    for ident in sorted(escenas):
                        cine = cinematicas.Cinematica([self.escenas[ident]], nombre_jugador='El duelista')
                        escena = cine.escena()
                        escena.mostrado = len(escena.texto)
                        cine._dibujar(screen, escena, 2.0)
                        pygame.image.save(screen, str(salida / f'{ident}_{etiqueta}.png'))
        finally:
            lotes_visuales._buscar.cache_clear()
            ui.REC.imagenes.clear()
            ui.REC.fuentes.clear()
            pygame.quit()
        return salida


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion', choices=['iniciar', 'preparar', 'previsualizar', 'activar', 'revertir', 'siguiente', 'verificar', 'catalogo'])
    parser.add_argument('valor', nargs='?')
    parser.add_argument('--incoming', type=Path, default=INCOMING)
    args = parser.parse_args()
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    with tempfile.TemporaryDirectory(prefix='tt_import_', dir='C:/Users/julip/AppData/Local/Temp/opencode') as temporal:
        os.environ['TRIPLETRIAD_DATA'] = temporal
        imp = Importador(incoming=args.incoming)
        with imp.bloqueo():
            if args.accion in ('preparar', 'previsualizar', 'activar', 'revertir') and not args.valor:
                parser.error('Falta ZIP o identificador de lote')
            if args.accion == 'preparar':
                print(imp.preparar(args.valor))
            elif args.accion == 'previsualizar':
                print(imp.previsualizar(args.valor))
            elif args.accion in ('activar', 'revertir'):
                imp.activar(args.valor, args.accion == 'activar')
            elif args.accion == 'siguiente':
                print(imp.siguiente())
            elif args.accion == 'catalogo':
                imp.exportar_catalogo()
            else:
                getattr(imp, args.accion)()
            print('OK. Reiniciar el juego tras activar/revertir. Revisar preview.html y revision.json del lote.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as error:
        sys.exit('ERROR: ' + str(error))
