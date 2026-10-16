"""Integridad del paquete y arranque de su diagnostico, sin ventana visible."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile

from PyInstaller.archive.readers import CArchiveReader

base = Path(__file__).resolve().parents[2]
exe = base / 'dist/TripleTriad.exe'
reader = CArchiveReader(str(exe))
images = 0
for name in reader.toc:
    data = reader.extract(name)
    path = base / name.replace('\\', '/')
    if path.suffix.lower() == '.png' and path.is_file():
        assert hashlib.sha256(data).digest() == hashlib.sha256(path.read_bytes()).digest(), name
        images += 1
with tempfile.TemporaryDirectory(prefix='tt_exe_detalles_') as temporary:
    env = os.environ.copy()
    env['TRIPLETRIAD_DATA'] = temporary
    process = subprocess.run([str(exe), '--check'], capture_output=True,
                             creationflags=0x08000000, env=env, timeout=90)
result = dict(entradas_verificadas=len(reader.toc), imagenes_empaquetadas_identicas=images,
              diagnostico_exit=process.returncode,
              sha256=hashlib.sha256(exe.read_bytes()).hexdigest())
Path(__file__).with_name('ejecutable.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(result)
raise SystemExit(process.returncode)
