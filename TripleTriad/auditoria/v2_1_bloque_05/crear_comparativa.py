"""Comparación de los paneles al 160 %, conservando las capturas completas."""
from pathlib import Path
from PIL import Image, ImageDraw

base = Path(__file__).resolve().parent
image = Image.new('RGB', (1280, 870), '#101019')
draw = ImageDraw.Draw(image)
for column, phase in enumerate(('antes', 'despues')):
    draw.text((column * 640 + 16, 12), phase.upper() + ' - lectura 160 %', fill='#ecca72')
    for row, name in enumerate(('humano_trono_C_1.6.png', 'pausa_1.6.png')):
        frame = Image.open(base / phase / name).convert('RGB')
        frame.thumbnail((640, 400))
        image.paste(frame, (column * 640, 40 + row * 410))
image.save(base / 'comparativa.png')
