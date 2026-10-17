"""Cierra evidencia solo si terminaron todos los recorridos reales."""
import hashlib
import json
from pathlib import Path
import sys
import re
import os
import subprocess
import zipfile

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'auditoria/v2_1_bloque_07'
data = json.loads((OUT / 'recorridos.json').read_text(encoding='utf-8'))
if '--merge-minis' in sys.argv:
    assert all(r.get('terminado') for r in data['recorridos'][:2]) and len(data['recorridos']) >= 2
    (OUT / 'recorridos_sesion_principal.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    data['recorridos'] = data['recorridos'][:2]
    for label in ('mini_nocturno', 'mini_pantera', 'mini_lagarto'):
        mini = json.loads((OUT / label / 'recorridos.json').read_text(encoding='utf-8'))
        assert len(mini['recorridos']) == 1 and mini['recorridos'][0]['terminado']
        data['recorridos'].append(mini['recorridos'][0])
    data['minicampanas_en_perfiles_independientes'] = True
    (OUT / 'recorridos.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
routes = data['recorridos']
assert len(routes) == 5 and all(r.get('terminado') and not r.get('error') for r in routes)
retry_count, games = 0, 0
for index, route in enumerate(routes):
    duels = [d for d in route['duelos'] if d['nodo'] != 'prologo']
    assert all(d.get('jugadas') == 9 for d in duels)
    assert all(len(d['mano_u']) == len(d['mano_c']) == 5 for d in duels)
    assert route['estado']['completada']
    wins = [d for d in duels if d.get('ganador') != 'C']
    expected = ['senda', 'aldea' if index == 0 else 'ruinas', 'fortaleza', 'asalto', 'trono'] if index < 2 else ['mini_senda', 'mini_nudo', 'mini_trono']
    assert [d['nodo'] for d in wins] == expected
    for previous, current in zip(duels, duels[1:]):
        if previous['ganador'] == 'C':
            assert (previous['nodo'], previous['rival']) == (current['nodo'], current['rival'])
            retry_count += 1
    games += len(route['duelos'])
assert retry_count > 0
assert routes[1]['estado']['revancha'] == 1
second = routes[1]['duelos']
assert next(d['rival'] for d in second if d['nodo'] == 'ruinas') == next(d['rival'] for d in second if d['nodo'] == 'asalto')
assert any(p['nombre'] == 'armar_mazo' for p in routes[0]['pantallas'])
assert routes[0]['duelos'][0]['nodo'] == 'prologo'
assert len(routes[0]['escenas']) >= 63
protected = json.loads((BASE / 'auditoria/uiux_saneamiento_20261015/proteccion_imagenes.json').read_text(encoding='utf-8'))
changed = [p for p, sha in protected.items() if hashlib.sha256((BASE / p).read_bytes()).hexdigest() != sha]
assert not changed
web = json.loads((OUT / 'chrome/editor_resultados.json').read_text(encoding='utf-8'))
assert web['final']['mazo'] and len(web['final']['mazo']) == 10
assert len(web['vacio']['seleccion']) == 0 and '10' in web['guardado_invalido']['motivo']
assert web['editorDiag']['fps'] >= 55
if '--tests' in sys.argv:
    with (OUT / 'tests_final.log').open('w', encoding='utf-8') as stream:
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                                cwd=BASE, stdout=stream, stderr=subprocess.STDOUT,
                                env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    assert result.returncode == 0
test_log = (OUT / 'tests_final.log').read_text(encoding='utf-8')
test_count = int(re.search(r'Ran (\d+) tests', test_log).group(1))
assert test_count == 1094 and re.search(r'^OK$', test_log, re.MULTILINE)
apk = BASE / 'build/v2_1_auditoria/cartones-mazmorras/build/web/cartones-mazmorras.apk'
with zipfile.ZipFile(apk) as archive:
    for module in ('pantallas.py', 'partida.py'):
        name = next(n for n in archive.namelist() if n.endswith('/' + module))
        assert archive.read(name) == (BASE / module).read_bytes()
    assert not any('fixture' in n for n in archive.namelist())
result = dict(campanas_principales=2, minicampanas=3, duelos_reales=games,
              reintentos_mismo_rival=retry_count, escenas_completas=sum(len(r['escenas']) for r in routes),
              imagenes_protegidas=len(protected), imagenes_modificadas=changed,
              apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest(), tests=test_count,
              fps_editor=web['editorDiag']['fps'],
              metodo=data['metodo'], limite=data['limite'])
(OUT / 'verificacion.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=True))
