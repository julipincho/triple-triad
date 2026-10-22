# Cinemáticas 2.5D — informe del piloto

**Fecha:** 22 de octubre de 2026.
**Rama:** `v2.1` (trabajo sobre la base publicada 2.0, sin tocar cartas ni texto).
**Estado:** piloto implementado, validado y medido. Listo para revisión humana.

## Qué hace

Las escenas con fondo aprobado (`salon_torneo.png`, `camino_lluvioso.png`,
`sala_trono.png`) dejan de ser una imagen fija: se separan en tres planos
(fondo, medio y frente) y el motor desplaza cada uno a una velocidad distinta,
con lluvia, brasas o polvo superpuestos. El fondo se desplaza más que el
frente, lo que produce el efecto de profundidad.

## Pipeline de producción

1. **Profundidad** con `depth-anything/Depth-Anything-V2-Small-hf`.
2. **Segmentación** con `nvidia/segformer-b0-finetuned-ade-512-512`.
3. **Inpainting** con `simple-lama-inpainting` (modelo `big-lama`, 196 MB)
   sobre la unión de los planos medio y frente. Las zonas rellenadas quedan
   ocultas bajo las capas y solo se ven en la banda de desplazamiento.
4. **Capas** a 1328×744 con 24×12 px de margen (`assets/cinematicas_25d/`).
5. **Manifiesto** `assets/cinematicas_25d/manifest.json` con hashes, bboxes,
   amplitudes y períodos.

Herramienta: `tools/producir_cinematicas_25d.py`. Requiere el venv visual
(`E:\AI\CartonesMazmorrasVisual\venv-sdxl`), no el del juego.

## Runtime

- Módulo `cinematicas_25d.py`: carga las capas con caché (12 entradas) y
  pinta con `screen.set_clip` al área cinematográfica (0, 40, 1280, 720).
- Flag `TRIPLETRIAD_CINEMATICAS_25D` (por defecto `1`). Con `0` o sin
  manifiesto, `dibujar_fondo` devuelve `False` y se usa el fondo HD o
  clásico sin error.
- `Escena.fondo_25d` permite forzar un conjunto por escena; si no viene,
  se deduce de `fondo_hd` o del lote visual.
- Partículas deterministas (posición = f(t)), semilla por conjunto. Lluvia,
  brasas y polvo. Desactivadas con movimiento reducido.
- El movimiento se desactiva con `opciones.movimiento_reducido()`.

## Rendimiento

Medido con `tools/auditar_cinematicas_25d.py` (120 frames, SDL dummy):

| Escena | 2.5D (ms/frame) | Clásico (ms/frame) | Equiv. (FPS) |
|---|---:|---:|---:|
| salón del torneo | 2,38 | 1,92 | 421 |
| bosque lluvioso | 3,33 | 1,88 | 300 |
| sala del trono | 2,61 | 1,88 | 383 |

Presupuesto de 60 FPS: 16,6 ms. El 2.5D queda muy por debajo.

## Validación

- Suite completa: **1108 pruebas, OK** (incluye 8 pruebas nuevas del módulo).
- Auditoría visual: `auditoria/cinematicas_25d_20261022/` con capturas a
  t=0/4/8 para las tres escenas, con 2.5D activado y desactivado, más
  máscaras, profundidad y contactos.
- Los hashes de las 1221 imágenes protegidas no se han tocado.

## Limitaciones

- Solo tres escenas. El resto de las 394 escenas del juego sigue con el
  fondo estático (HD o clásico).
- La segmentación es `segformer-b0` (ADE20K); las máscaras son aproximadas y
  se han corregido por región en el perfil. Calidad suficiente para el piloto.
- El inpainting de LaMa rellena de forma plausible pero no idéntica al estilo
  del fondo; como las zonas rellenadas quedan ocultas bajo las capas, solo se
  ven en la banda de desplazamiento (máximo 12 px).
- No se ha probado en web (pygbag). Pendiente: build y medición en Chrome.

## Archivos nuevos o modificados

- `cinematicas_25d.py` (nuevo): runtime.
- `cinematicas.py`: `Escena.fondo_25d`, `_dibujar` resuelve el 2.5D antes
  del HD.
- `tools/producir_cinematicas_25d.py` (nuevo): pipeline de producción.
- `tools/auditar_cinematicas_25d.py` (nuevo): auditoría visual y de tiempo.
- `tests/test_cinematicas_25d.py` (nuevo): 8 pruebas.
- `tests/test_arte_pixel_anime.py`: `test_prioridad_del_hd_aprobado` adaptado
  y `test_prioridad_del_25d` añadido.
- `assets/cinematicas_25d/`: manifiesto y 9 capas (3 escenas × 3 planos).
- `auditoria/cinematicas_25d_20261022/`: evidencias.

## Siguiente paso

1. Revisar las capturas del piloto y decidir si el efecto gusta.
2. Si gusta, extender a las 10 facciones (30 finales) con el mismo pipeline.
3. Medir en Chrome (web) y ajustar si hace falta.
4. Opcional: entrenar el LoRA de estilo (el smoke test sigue pendiente) para
   unificar el estilo de los fondos futuros.
