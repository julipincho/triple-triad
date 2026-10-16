"""Instala exclusivamente el lote de avatares y fondos auditados, conservando originales."""
import hashlib
import json
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    evidence = BASE / 'auditoria/migracion_avatares_20261015'
    generated = json.loads((evidence / 'generados.json').read_text(encoding='utf-8'))
    protection = json.loads((evidence / 'proteccion.json').read_text(encoding='utf-8'))
    protection = {p.replace('\\', '/'): h for p, h in protection.items()}
    # Fail before mutation if any original card, avatar or scene has changed.
    for relative, expected in protection.items():
        assert sha(BASE / relative) == expected, relative
    root = BASE / 'assets/lotes_visuales/migracion_20261015'
    root.mkdir(parents=True, exist_ok=True)
    resources = []
    for item in generated:
        kind = item.get('tipo', 'retrato')
        folder = 'retratos' if kind == 'retrato' else 'fondos'
        target = (BASE / 'assets/cinematicas_hd' / ('campana_' + item['id'] + '_20261015.png')
                  if kind == 'fondo' else root / folder / (item['id'] + '.png'))
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(item['path'], target)
        entry = dict(id=item['id'], tipo=kind, ruta=target.relative_to(BASE).as_posix(),
                     sha256=sha(target), estado='listo')
        if kind == 'retrato':
            entry['personaje'] = item['id']
        else:
            # Cinematicas._continuidad_nodo_hd assigns this HD only inside its node.
            entry['estado'] = 'integrado_hd'
        resources.append(entry)
    registry_path = BASE / 'assets/lotes_visuales/registro.json'
    registry = json.loads(registry_path.read_text(encoding='utf-8'))
    backup = evidence / 'registro_antes.json'
    if not backup.exists():
        shutil.copy2(registry_path, backup)
    # Specific new selections take priority; earlier batches stay preserved.
    old = {k: v for k, v in registry['lotes'].items() if k != 'migracion_20261015'}
    registry['lotes'] = {'migracion_20261015': {'activo': True, 'recursos': resources}, **old}
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (root / 'prompts.json').write_text(json.dumps(generated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    changed = [p for p, h in protection.items() if sha(BASE / p) != h]
    assert changed == ['assets/lotes_visuales/registro.json'], changed
    (evidence / 'integridad.json').write_text(json.dumps({
        'archivos_preexistentes_verificados': len(protection),
        'archivos_cartas_intactos': sum(p.split('/')[0].startswith('cartas') for p in protection),
        'unico_archivo_asset_preexistente_actualizado': changed,
        'recursos_nuevos': len(resources),
    }, indent=2), encoding='utf-8')
    print(f'{len(resources)} recursos instalados; originales intactos; solo registro actualizado.')


if __name__ == '__main__':
    main()
