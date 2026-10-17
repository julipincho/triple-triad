"""Comprueba las dos regresiones contra la fuente anterior y la actual."""
import io
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(BASE), str(BASE / 'tests')]
TEMP = tempfile.TemporaryDirectory(prefix='tt_editor_b07_')
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import pygame
import test_coleccion
import pantallas
import campana

pygame.init()
out = BASE / 'auditoria/v2_1_bloque_07'
out.mkdir(parents=True, exist_ok=True)
source = subprocess.check_output(['git', 'show', '9eddb94:TripleTriad/pantallas.py'], cwd=BASE).decode('utf-8')
previous = types.ModuleType('pantallas_b07_antes')
sys.modules[previous.__name__] = previous
exec(compile(source, str(BASE / 'pantallas.py'), 'exec'), previous.__dict__)
names = ('test_centro_de_segunda_carta_no_selecciona_la_tercera',
         'test_posicion_antigua_de_guardar_no_es_un_boton_invisible')
case = next(cls for cls in vars(test_coleccion).values()
            if isinstance(cls, type) and issubclass(cls, unittest.TestCase)
            and hasattr(cls, names[0]))
results = {}
for phase, module in (('antes', previous), ('despues', pantallas)):
    suite = unittest.TestSuite(case(name) for name in names)
    stream = io.StringIO()
    with patch.dict(sys.modules, pantallas=module):
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (out / f'editor_{phase}.log').write_text(stream.getvalue(), encoding='utf-8')
    results[phase] = dict(pruebas=result.testsRun, fallos=len(result.failures), errores=len(result.errors))
    perfil = campana.cargar_perfil()
    perfil['coleccion'] = campana.coleccion_inicial('humano')
    perfil['mazo'] = list(perfil['coleccion'])
    campana.guardar_perfil(perfil)
    screen = pygame.display.set_mode((1280, 800))
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(332, 242))
    escape = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    flips = [0]
    original = pygame.display.flip
    def flip():
        flips[0] += 1
        if flips[0] == 2:
            pygame.image.save(screen, str(out / f'editor_{phase}.png'))
        original()
    class Clock:
        def tick(self, fps):
            return 16
    with patch('pygame.event.get', side_effect=[[click], [escape]]), patch('pygame.display.flip', side_effect=flip):
        asyncio.run(module.armar_mazo(screen, Clock(), 'humano'))
assert results['antes'] == dict(pruebas=2, fallos=2, errores=0), results
assert results['despues'] == dict(pruebas=2, fallos=0, errores=0), results
(out / 'editor_regresiones.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print(results)
from PIL import Image, ImageDraw
comparison = Image.new('RGB', (1280, 540), '#101019')
draw = ImageDraw.Draw(comparison)
for index, phase in enumerate(('antes', 'despues')):
    draw.text((20, 12 + index * 270), phase.upper() + ': mismo clic en el centro de la segunda carta', fill='#ecca72')
    frame = Image.open(out / f'editor_{phase}.png').crop((40, 150, 1120, 330))
    comparison.paste(frame, (20, 50 + index * 270))
comparison.save(out / 'comparativa_editor.png')
pygame.quit()
