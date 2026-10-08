# Ficha de estilo — Triple Triad

Fuente: `E:\AI\moodboard.png` (moodboard). Extraida con gemini-3.5-flash.
Este archivo manda sobre el prompt, el post-proceso y cualquier checkpoint.

> Retratos de fantasía oscura en pixel art de alta densidad con estética retro de monitor CRT y marcadas líneas de escaneo horizontales.

## Medicion del PNG

| Metrica | Valor |
|---|---|
| Brillo medio | 59/255 |
| Saturacion media | 33/255 |
| Scanlines | si (autocorr lag2 = -0.813) |
| Tamano | 1983x793 |

## Medio
Pixel art detallado de estilo retro de 16/32 bits, simulando la pantalla de un monitor CRT analógico. Presenta un patrón alterno de scanlines horizontales muy definido y sombreado mediante dithering (tramado de píxeles).

## Luz
Iluminación dramática de tres cuartos (claroscuro) con alto contraste. Se observan luces secundarias de colores (azul, violeta, rojo fuego) que perfilan las siluetas y crean una atmósfera mística.

## Encuadre
Plano medio corto (busto), con el sujeto centrado mirando ligeramente hacia tres cuartos. El fondo muestra paisajes temáticos (castillos, bosques, lunas) con menor contraste para dar profundidad.

## Textura
Textura pixelada rugosa y definida. Presencia de scanlines horizontales de 2 píxeles de grosor y tramado (dithering) para las transiciones de color, evitando degradados suaves modernos.

## Detalle
Alto nivel de detalle concentrado en los rostros, ojos expresivos y texturas del primer plano (escamas, pelaje, metal pulido), simplificándose hacia el fondo.

## Mood
Siniestro, heroico, melancólico y nostálgico. Evoca la atmósfera de los videojuegos de rol clásicos de los años 90.

## Sujetos
Personajes de fantasía con expresiones severas, orgullosas o amenazantes. Siluetas bien definidas, rasgos faciales afilados y ojos intensos o brillantes.

## Paleta

| Hex | Nombre | Uso |
|---|---|---|
| `#101114` | Negro Abisal | Sombras más profundas, contornos de personajes y marcos de interfaz. |
| `#3A393B` | Gris Ceniza | Tonos medios neutros, texturas metálicas y fondos de piedra. |
| `#725B4D` | Marrón Tierra Quemada | Pelajes, cuero, sombras de piel cálidas y detalles de vestimenta. |
| `#8B7561` | Beige Pergamino | Luces altas en pelajes, cabello y reflejos de piel clara. |
| `#794131` | Rojo Terracota | Escamas de dragón, luces de fuego y acentos cálidos en la indumentaria. |
| `#4B2422` | Rojo Sangre Oscuro | Capas de vampiro, cielos crepusculares y sombras cálidas. |
| `#141A21` | Azul Abismo | Sombras frías, telas oscuras y cielos nocturnos. |
| `#AD9883` | Gris Arena | Brillos metálicos en armaduras y reflejos de luz ambiental fría. |

## Bloque de prompt SDXL

**Positivo:**
```
pixel art portrait, dark fantasy style, highly detailed 16-bit retro game graphics, visible horizontal scanlines, CRT monitor texture, dithered shading, dramatic chiaroscuro lighting, sharp pixel edges, muted color palette with deep shadows, centered portrait, atmospheric background
```

**Negativo:**
```
smooth digital painting, 3D render, vector art, blurry, anti-aliased, modern graphics, high-definition photo, soft brushstrokes, bright pastel colors, white background, modern UI, smooth gradients
```

## Prohibiciones
- No usar degradados de color suaves o aerografiados.
- No incluir elementos de interfaz de usuario modernos o futuristas.
- No suavizar los bordes de los píxeles con filtros de desenfoque.
- No mostrar personajes sonrientes o en poses alegres.
- No usar colores extremadamente saturados o neón fuera de los puntos de luz.
