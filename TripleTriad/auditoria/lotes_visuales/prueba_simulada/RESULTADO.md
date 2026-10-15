# Prueba del importador — 14/10/2026

- 87 pruebas aprobadas: 14 del importador y 73 existentes de arte, assets y prólogo.
- Activación y reversión realizadas únicamente en un proyecto temporal.
- Capturas antes/candidato con pygame real a 1280×800; los colores planos son
  datos simulados y no representan producción artística.
- ZIP simulado preservado aquí para reproducción; no está en incoming.
- Registro real: 2 lotes históricos, 132 archivos previos protegidos,
  0 lotes nuevos activados o preparados en producción.
- Comparación con el manifiesto previo: 1147 archivos de imágenes, paquetes y
  cartas sin alteraciones.
- `importar_lote_visual.py verificar`: OK.
- `git diff --check`: sin errores de whitespace.

Reproducción (desde TripleTriad, con Python del juego):

```text
python -m unittest tests.test_importar_lote_visual tests.test_arte_pixel_anime tests.test_assets tests.test_prologo tests.test_flujo_prologo
```

Usar SDL_VIDEODRIVER=dummy, SDL_AUDIODRIVER=dummy y TRIPLETRIAD_DATA apuntando
a un directorio temporal. Para conservar capturas de la simulación, definir
TT_EVIDENCIA_IMPORTADOR=auditoria/lotes_visuales/prueba_simulada.
