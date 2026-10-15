# Integración cinematográfica aprobada — 15/10/2026

## Recursos y preservación

- Paquete: `E:\AI\CartonesMazmorrasVisual\cinematicasCorregidas\cartones_y_mazmorras_cinematicas_20_aprobadas.zip`.
- SHA-256 del ZIP: `ce1a60d379b6b5fc51fa8112066b0a561fd0adeb6c0f0fef08249bc79a90d175`.
- Los 20 PNG se instalaron con sus IDs exactos en `assets/cinematicas_hd/`.
- Copia completa del paquete, manifiesto y cinco masters: `assets/lotes_visuales/cinematicas_aprobadas_2026_10_15/`.
- SHA-256, PNG RGB 1280×720, ZIP CRC y los masters se verificaron contra el manifiesto. Los seis HD anteriores conservaron sus hashes.

## Asignación acotada

- Intro: amanecer antiguo, grieta del Umbral y estandartes, por escena; se conserva `sala_trono.png` en la última escena.
- Prólogo: escenario solo en escenas del escenario; apagón solo en el transporte; campamento solo dentro de las secuencias de Nara, explicación y cierre. El camino lluvioso, salón concurrido, revelación, portal y sala del trono conservan sus asignaciones previas.
- Apertura de cada una de las diez facciones: fondo específico aplicado únicamente a esa secuencia, incluso donde el fondo original comparte claves como `trono`, `ruinas` o `umbral`.
- Finales del Umbral: tres imágenes diferenciadas por variante.
- Epílogos: dominio y equilibrio siguen usando `salon_torneo.png`; solo caos usa `epilogo_caos_salon_invadio.png`.

No se cambió texto, mecánica, carta, avatar ni música. No se reemplazaron las imágenes originales ni se aplicaron redirecciones globales por clave.

## Verificación visual y pruebas

- `tests.test_cinematicas_aprobadas_20261015`, `test_presentacion`, `test_finales`, `test_prologo`, `test_flujo_prologo`, `test_inventario_fondos` y `test_flujo`: **120 pruebas OK**.
- Se renderizaron las 20 cinemáticas con el reproductor real en lienzo lógico 1280×800, fondos 1280×720 centrados sin deformar.
- Capturas individuales e índice: `capturas/cinematicas_aprobadas_20261015/`.

## Nota de origen

Según el README del lote, dos imágenes del prólogo son renders individuales corregidos; los otros 18 son recortes reescalados de hojas de referencia. El lote está aprobado visualmente por el usuario, pero esta diferencia de origen/calidad se deja documentada para futuras revisiones.
