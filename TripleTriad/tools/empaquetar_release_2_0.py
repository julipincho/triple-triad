"""Paquetes separados de Windows y HTML5 para subir a itch.io."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
import argparse

BASE = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=BASE.parent / 'ver2Subir')
OUT = parser.parse_args().output.resolve()
WEB = BASE / 'build/release_2_0/cartones-mazmorras/build/web'
if (BASE / 'build/release_2_0_web_r1/cartones-mazmorras/build/web/index.html').is_file():
    WEB = BASE / 'build/release_2_0_web_r1/cartones-mazmorras/build/web'
if (BASE / 'build/release_2_0_web_r2/cartones-mazmorras/build/web/index.html').is_file():
    WEB = BASE / 'build/release_2_0_web_r2/cartones-mazmorras/build/web'
EXE = BASE / 'dist/TripleTriad.exe'
OUT.mkdir(exist_ok=True)

windows = OUT / 'Cartones-y-Mazmorras-2.0-Windows.zip'
with zipfile.ZipFile(windows, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    archive.write(EXE, 'CartonesYMazmorras.exe')
    archive.writestr('VERSION.txt', '2.0\n')
    archive.writestr('.itch.toml', '[[actions]]\nname = "Jugar"\npath = "CartonesYMazmorras.exe"\n')
    archive.writestr('LEEME.txt', 'Cartones y Mazmorras - Version 2.0\n\nExtrae todo el ZIP y abre CartonesYMazmorras.exe.\nNo necesitas instalar Python.\n\nRaton: seleccionar o arrastrar cartas.\nFlechas y Enter: navegar por los menus.\nEsc: pausa o volver. H: ayuda durante el duelo.\n\nSe crean partidas y perfil al jugar. Conserva tus guardados al actualizar.\n')
web = OUT / 'Cartones-y-Mazmorras-2.0-Web.zip'
with zipfile.ZipFile(web, 'w', zipfile.ZIP_STORED) as archive:
    for name in ('index.html', 'favicon.png', 'cartones-mazmorras.apk'):
        archive.write(WEB / name, name)
    archive.writestr('VERSION.txt', '2.0\n')
with zipfile.ZipFile(web) as archive:
    assert archive.testzip() is None
    info = archive.infolist()
    assert len(info) <= 1000
    assert sum(i.file_size for i in info) <= 500 * 1024**2
    assert max(i.file_size for i in info) <= 200 * 1024**2
    assert all(len(i.filename) <= 240 for i in info)
with zipfile.ZipFile(WEB / 'cartones-mazmorras.apk') as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert not any(Path(n).name in ('perfil.json', 'campana.json', 'crash.log') for n in names)
    version = next(n for n in names if n.endswith('/version.py'))
    assert 'VERSION = "2.0"' in archive.read(version).decode('utf-8')
    for card in (BASE / 'cartas').glob('*.png'):
        name = next(n for n in names if n.endswith('/cartas/' + card.name))
        assert archive.read(name) == card.read_bytes(), card.name
with tempfile.TemporaryDirectory(prefix='tt_zip_2_0_') as temporary:
    with zipfile.ZipFile(windows) as archive:
        assert archive.testzip() is None
        archive.extractall(temporary)
    exe = Path(temporary) / 'CartonesYMazmorras.exe'
    assert exe.read_bytes() == EXE.read_bytes()
    env = os.environ.copy()
    env.update(TRIPLETRIAD_DATA=temporary, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    for flag in ('--check', '--test'):
        process = subprocess.run([str(exe), flag], env=env, capture_output=True,
                                 creationflags=0x08000000, timeout=90)
        assert process.returncode == 0, (flag, process.returncode)
result = {'version': '2.0', 'windows_extraido_check': 0, 'windows_extraido_test': 0,
          'cartas_web_sin_modificar': 250, 'archivos': {}}
for file in OUT.iterdir():
    if file.suffix in ('.zip', '.png'):
        result['archivos'][file.name] = {'bytes': file.stat().st_size,
            'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
(OUT / 'VERIFICACION-2.0.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
