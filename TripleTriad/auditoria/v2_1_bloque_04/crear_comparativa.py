"""Compone las capturas de Chrome del bloque 04; no modifica arte del juego."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
image = Image.new('RGB', (1280, 1260), '#0e0f16')
draw = ImageDraw.Draw(image)
for row, name in enumerate(('final_efecto', 'reanudado', 'final_resultado')):
    for col, phase in enumerate(('antes', 'despues')):
        x, y = col * 640, row * 420
        draw.text((x + 12, y + 3), f'{phase.upper()} / {name}', fill='#f0c85a')
        capture = Image.open(ROOT / phase / (name + '.png')).convert('RGB')
        capture.thumbnail((640, 400))
        image.paste(capture, (x + (640-capture.width)//2, y + 20))
image.save(ROOT / 'comparativa.png')
