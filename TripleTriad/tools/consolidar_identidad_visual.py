"""Auditoría de solo lectura del arte runtime; escribe evidencia separada."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'auditoria' / 'consolidacion_20261014'
STAGING = Path('E:/AI/CartonesMazmorrasVisual/exports/approved')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    baseline = OUT / 'proteccion.json'
    if baseline.exists():
        data = json.loads(baseline.read_text(encoding='utf-8'))
        for entry in data['archivos']:
            assert sha(Path(entry['ruta'])) == entry['sha256'], entry['ruta']
        print(f"Verificados {len(data['archivos'])} archivos sin cambios")
        if '--capturas' in sys.argv:
            capturar()
        return

    files = {}
    batches = []
    for batch, commit in [('lote_01', '21be366'), ('lote_02', '4229c2e')]:
        root = STAGING / batch
        package = STAGING.parent.parent / f'CartonesMazmorras_Lote{batch[-2:]}_1280x720.zip'
        archive = zipfile.ZipFile(package)
        files[str(package)] = sha(package)
        manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
        entries = []
        for e in manifest.get('entries', manifest.get('assets', [])):
            relative = e.get('file', e.get('filename'))
            original = root / e.get('master', e.get('original'))
            export = root / relative
            runtime = BASE / 'assets' / relative
            expected = e.get('export_sha256', e.get('sha256'))
            member = e.get('master', e.get('original'))
            original_hash = hashlib.sha256(archive.read(member)).hexdigest()
            assert original_hash == e.get('source_sha256', e.get('original_sha256'))
            assert sha(export) == sha(runtime) == expected
            for p in (export, runtime):
                files[str(p)] = sha(p)
            refs = []
            for source in BASE.glob('*.py'):
                for number, line in enumerate(source.read_text(encoding='utf-8').splitlines(), 1):
                    if runtime.name in line:
                        refs.append({'archivo': source.name, 'linea': number, 'texto': line.strip()})
            assert refs, runtime
            entries.append({'id': e['id'], 'original': str(package) + '::' + member,
                            'original_sha256': original_hash,
                            'export': str(export), 'runtime': str(runtime), 'referencias': refs})
        batches.append({'lote': batch, 'commit_integracion': commit, 'recursos': entries})
        archive.close()
        files[str(root / 'manifest.json')] = sha(root / 'manifest.json')

    # Cartas: únicamente lectura de hashes; nunca abrir/guardar con un editor de imagen.
    for folder in BASE.glob('cartas*'):
        if folder.is_dir():
            for p in folder.rglob('*'):
                if p.is_file():
                    files[str(p)] = sha(p)
    for pattern in ('assets/avatar_*.png', 'assets/pixel_anime/**/*.png',
                    'assets/fondos/*.png', 'assets/escenas/*.png'):
        for p in BASE.glob(pattern):
            files[str(p)] = sha(p)
    for p in BASE.glob('*.py'):
        files[str(p)] = sha(p)
    files[str(BASE / 'assets/pixel_anime/manifest.json')] = sha(BASE / 'assets/pixel_anime/manifest.json')

    backup = Path('C:/Users/julip/AppData/Local/Temp/opencode/consolidacion_20261014_estado_visual.zip')
    with zipfile.ZipFile(backup, 'x', zipfile.ZIP_DEFLATED) as z:
        for path in files:
            p = Path(path)
            if p.is_relative_to(STAGING):
                z.write(p, 'aprobados/' + p.relative_to(STAGING).as_posix())
            elif p.suffix == '.zip':
                z.write(p, 'paquetes/' + p.name)
            elif p.is_relative_to(BASE) and not p.relative_to(BASE).parts[0].startswith('cartas'):
                z.write(p, 'TripleTriad/' + p.relative_to(BASE).as_posix())
        z.writestr('cambios_previos.patch', subprocess.check_output(['git', 'diff', '--binary'], cwd=BASE))
        z.writestr('estado_previo.txt', subprocess.check_output(['git', 'status', '--short', '--branch'], cwd=BASE))
    data = {'rama': subprocess.check_output(['git', 'branch', '--show-current'], cwd=BASE, text=True).strip(),
            'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=BASE, text=True).strip(),
            'respaldo': str(backup), 'respaldo_sha256': sha(backup), 'lotes': batches,
            'archivos': [{'ruta': p, 'sha256': h} for p, h in sorted(files.items())]}
    baseline.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(batches)} lotes verificados; {len(files)} archivos registrados. Respaldo: {backup}')
    capturar()


def capturar():
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    os.environ['TRIPLETRIAD_DATA'] = tempfile.mkdtemp(prefix='tt_consolidacion_', dir='C:/Users/julip/AppData/Local/Temp/opencode')
    sys.path.insert(0, str(BASE))
    import pygame
    import prologo
    import cinematicas
    import ui
    import arte_visual
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    scenes = []
    captures = OUT / 'capturas_estado_actual'
    captures.mkdir(exist_ok=True)
    for name in ('pre_duelo', 'post_duelo', 'carta_umbral', 'transporte', 'despertar',
                 'encuentro_hostil', 'nara', 'explicacion', 'cierre'):
        for index, scene in enumerate(getattr(prologo, 'escenas_' + name)()):
            cine = cinematicas.Cinematica([scene], nombre_jugador='El duelista')
            actual = cine.escena()
            actual.mostrado = len(actual.texto)
            cine._dibujar(screen, actual, 2.0)
            fallback = ui.ruta_fondo(actual.fondo)
            resolved = ('assets/cinematicas_hd/' + actual.fondo_hd if actual.fondo_hd
                        else arte_visual.alternativa(fallback, 'fondo') or fallback)
            scenes.append({'bloque': name, 'indice_base_0': index, 'texto': actual.texto,
                           'fondo_runtime': resolved, 'retrato': actual.retrato})
            if name in ('pre_duelo', 'carta_umbral', 'transporte') or (name, index) in (
                    ('post_duelo', 0), ('despertar', 0), ('despertar', 10), ('nara', 4), ('cierre', 3)):
                pygame.image.save(screen, str(captures / f'{name}_{index:02}.png'))
    pygame.quit()
    (OUT / 'escenas_runtime.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(scenes)} escenas renderizadas')


if __name__ == '__main__':
    main()
