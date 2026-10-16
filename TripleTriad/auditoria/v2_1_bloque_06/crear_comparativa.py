from pathlib import Path
from PIL import Image, ImageDraw

base = Path(__file__).resolve().parent
canvas = Image.new('RGB', (1280, 870), '#101019')
draw = ImageDraw.Draw(canvas)
for column, phase in enumerate(('antes', 'despues')):
    draw.text((column * 640 + 16, 12), phase.upper() + ' - lectura 160 %', fill='#ecca72')
    for row, name in enumerate(('tutorial_entrada_1.6.png', 'humano_aldea_1_asalto_entrada_1.6.png')):
        frame = Image.open(base / phase / name).convert('RGB').crop((940, 80, 1280, 400))
        frame = frame.resize((404, 380), Image.Resampling.NEAREST)
        canvas.paste(frame, (column * 640 + 118, 40 + row * 410))
canvas.save(base / 'comparativa.png')
