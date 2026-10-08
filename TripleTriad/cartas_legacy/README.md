# cartas_legacy

Arte de cartas **anterior** al overhaul de pixel art (fase "pixelArtDiffusionXL + IP-Adapter").

## Contenido

- **251 PNG** (`{faccion}_{slug}.png`, 112×158): las cartas viejas ya post-procesadas
  con el estilo CRT de la fase anterior (copy de `cartas_crt/`). Es la dirección
  de arte que estaba vigente antes del pixel art y la que se veía en las
  comparaciones A/B (hojas de contactos).
- **`_crudo_original/vampiro_sombra_del_umbral.png`** (768×960): la única carta
  original cruda que sobrevivió `Vampiro Sombra del Umbral`, una carta huérfana
  que no está en `mazos.py` y nunca fue regenerada.

## Aviso importante

Las 250 cartas crudas originales (768×960) que ocupaban `cartas/` quedaron
**sobrescritas** al instalar el arte nuevo y **nunca estuvieron en git**
(`git log -- TripleTriad/cartas` no tiene commits), por lo que solo se conservan
en su versión procesada CRT (estas 251 PNG). El juego no usa esta carpeta:
`cartas.py` carga el arte activo desde `cartas/`.