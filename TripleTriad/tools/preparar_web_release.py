"""Exporta un arbol limpio para pygbag, sin guardados ni material de trabajo."""
import ast
import json
from pathlib import Path
import shutil
import subprocess
import sys
import hashlib

BASE = Path(__file__).resolve().parents[1]
revision = 'release_2_0_web_r2' if '--r2' in sys.argv else ('release_2_0_web_r1' if '--r1' in sys.argv else 'release_2_0')
if '--v21-audit' in sys.argv:
    revision = 'v2_1_auditoria'
DEST = BASE / 'build' / revision / 'cartones-mazmorras'
DEST.mkdir(parents=True, exist_ok=True)

def copiar(path):
    target = DEST / path.relative_to(BASE)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)

# Incluye dependencias locales aun cuando se importen dentro de una funcion.
pending, modules = ['main'], set()
while pending:
    name = pending.pop()
    source = BASE / (name + '.py')
    if name in modules or not source.is_file():
        continue
    modules.add(name)
    copiar(source)
    for node in ast.walk(ast.parse(source.read_text(encoding='utf-8'))):
        if isinstance(node, ast.Import):
            pending.extend(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            pending.append(node.module.split('.')[0])

for path in (BASE / 'cartas').glob('*.png'):
    copiar(path)
for path in (BASE / 'assets').iterdir():
    if path.is_file() and path.suffix.lower() in ('.png', '.ttf', '.ogg'):
        copiar(path)
for directory in ('fondos', 'escenas', 'pixel_anime', 'cinematicas_hd'):
    for path in (BASE / 'assets' / directory).rglob('*'):
        if path.is_file() and path.suffix.lower() in ('.png', '.json'):
            copiar(path)
registry = json.loads((BASE / 'assets/lotes_visuales/registro.json').read_text(encoding='utf-8'))
for batch in registry.get('lotes', {}).values():
    if not batch.get('activo'):
        continue
    for resource in batch.get('recursos', []):
        path = BASE / resource['ruta']
        if path.is_file():
            copiar(path)
copiar(BASE / 'assets/lotes_visuales/registro.json')

# Exporta audio comprimido solo en el arbol web; no modifica los originales.
import imageio_ffmpeg
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
for directory in (BASE / 'assets', BASE / 'assets/musica'):
    for wav in directory.glob('*.wav'):
        target = DEST / wav.relative_to(BASE).with_suffix('.ogg')
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-i', str(wav),
                        '-c:a', 'libvorbis', '-q:a', '4', str(target)], check=True)
# Los efectos web usan OGG con un manifiesto propio de hashes validos.
manifest_path = BASE / 'assets/sfx_stable_audio3/manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
converted = set()
for entry in manifest['mapa'].values():
    source = BASE / entry['archivo']
    target = DEST / Path(entry['archivo']).with_suffix('.ogg')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target not in converted:
        subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-i', str(source),
                        '-c:a', 'libvorbis', '-q:a', '4', str(target)], check=True)
        converted.add(target)
    entry['archivo'] = target.relative_to(DEST).as_posix()
    entry['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
(DEST / 'assets/sfx_stable_audio3/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
template = (BASE / 'plantilla_index.tmpl').read_text(encoding='utf-8')
template = template.replace('lang="en-us"', 'lang="es"')
template = template.replace('<title>Cartones y Mazmorras</title>', '<title>Cartones y Mazmorras 2.0</title>')
template = template.replace('Ready to start ! Please click/touch page', 'Listo para jugar. Hacé clic para comenzar.')
(DEST / 'plantilla_index.tmpl').write_text(template, encoding='utf-8')
(DEST / 'pygbag.ini').write_text('[DEPENDENCIES]\nignoreDirs = ["/build","/__pycache__"]\nignoreFiles = ["plantilla_index.tmpl","pygbag.ini"]\n', encoding='utf-8')
print('Arbol web limpio:', DEST)
print('Modulos:', ', '.join(sorted(modules)))
