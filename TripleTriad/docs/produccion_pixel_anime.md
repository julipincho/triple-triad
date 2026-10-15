# Produccion pixel anime — 13 octubre 2026

## Resultado activo

61 recursos seleccionados y revisados visualmente:

- 19 avatares (256×256), img2img a partir de sus diseños anteriores.
- 36 fondos cinematográficos (1280×720), incluidas variantes de clima y escenario.
- 6 ilustraciones de encuentros (1280×720).

Rutas runtime ordenadas:
`assets/pixel_anime/avatares/`, `cinematicas/`, `encuentros/`.
`assets/pixel_anime/manifest.json` contiene la selección, hashes, modelos,
semillas y ubicación de las recetas. No se sobrescribió ningún original.

Los seis PNG aprobados de Lotes 01/02 tienen prioridad y permanecen idénticos.
Los fondos nuevos solo se seleccionan en cinemáticas; las cartas conservan
su pipeline, rutas y escalado. Los retratos nuevos se usan donde se solicita
su avatar, también en la interfaz de duelo. Resolución lógica: 1280×800;
fondos nuevos a 1:1 en (0,40), retratos con vecino más cercano.

## Producción y reversión

Se utilizaron únicamente los checkpoints locales ya instalados: Animagine XL 4
para retratos y PixelArtDiffusionXL SpriteShaper para entornos. Se generaron
64 candidatos iniciales y 29 revisiones; la selección no incluye todos los
candidatos. Los primeros pilotos están conservados por separado.

Fuentes, masters, candidatos rechazados y recetas completas:
`E:\AI\CartonesMazmorrasVisual\exports\pixel_anime_20261013_final\`.
Subcarpetas: `originales`, `referencias`, `masters`, `candidatos`, `revision`,
`nuevo`, `masters_revision`, `masters_nuevo`.

Herramientas: `tools/producir_pixel_anime.py`, `tools/publicar_pixel_anime.py`
y `tools/capturar_pixel_anime.py`. La publicación usa una selección explícita.

Para recuperar el arte previo: iniciar con `TRIPLETRIAD_ARTE_PIXEL_ANIME=0`.
Los lotes HD anteriores siguen activos. Para desactivar también los fondos
HD: `TRIPLETRIAD_CINEMATICAS_HD=0`. Un recurso nuevo ausente cae al original.

## Evidencia

- 238 pruebas aprobadas: selección, hashes, fallback, protección de cartas y
  lotes aprobados, encuadre 1:1, variantes, prólogo, finales, flujo, saltos,
  controles, campaña, intro, render y assets.
- Verificación SHA-256 de 1007 archivos bajo carpetas `cartas*` y de los seis
  fondos HD aprobados frente al snapshot previo: sin cambios.
- Verificación de todos los avatares, fondos y encuentros originales: intactos.
- Capturas del renderer real en `capturas/pixel_anime/` (SDL sin ventana,
  directorio temporal de guardado). No constituyen una partida manual completa.
- Catálogos de los 61 recursos seleccionados en esa misma carpeta.

## Pendiente concreto

`trono_guardia` conserva su original: los candidatos no representan claramente
los guardias. Los nuevos candidatos genéricos de salón y trono quedaron fuera
para conservar los planos aprobados. No se alteraron diálogos ni personajes.

Para una revisión artística posterior conviene afinar la continuidad de los
tonos del escenario y del público respecto al salón aprobado, y la densidad
de niebla del campamento. La nueva serie usa colores más vivos y un pixelado
más marcado que los lotes HD anteriores, conservados por solicitud del usuario.
