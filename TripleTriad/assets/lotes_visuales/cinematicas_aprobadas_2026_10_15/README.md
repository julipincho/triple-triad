# Cartones y Mazmorras — Cinemáticas aprobadas (15/10/2026)

**Estado: APROBADO POR EL USUARIO.** Contiene 20 fondos PNG RGB de 1280×720 con los IDs exactos pedidos.

- `fondos_1280x720/`: los 20 fondos para mapear por escena.
- `masters_originales/`: cinco imágenes originales sin recortar: tres hojas de referencia y los dos renders individuales corregidos del prólogo.
- `manifest.json`: estado, SHA-256, origen, y mapeo recomendado por ID.
- `hashes_sha256.txt`: huellas digitales de los archivos entregados.
- `previews/indice_aprobados.png`: vista de conjunto actualizada.

## Correcciones finales aprobadas

- `prologo_escenario_presentacion.png`: render individual del escenario de torneo coherente con el salón aprobado, con público, atril cubierto y luces encendidas.
- `prologo_apagon_salon.png`: el mismo salón con las luces apagadas, sin portal ni energía sobrenatural visible.

## Nota de calidad

Los dos fondos corregidos provienen de renders individuales de 1672×941 reducidos a 1280×720. Los otros 18 proceden de recortes de una hoja de referencia y están reescalados; aunque tienen 1280×720 píxeles, no equivalen en detalle a renders nativos de ese tamaño.

## Integración pendiente

El lote está aprobado **visualmente**, pero **no está integrado en el código del juego**. Asignar cada fondo por ID y llamada concreta de cinemática (intro, prólogo, facción, desenlace); no reemplazar claves de uso global. Mantener los seis HD anteriores y no modificar el lote 05. El epílogo real de dominio/equilibrio conserva `salon_torneo.png`; solo el epílogo de caos puede usar `epilogo_caos_salon_invadio.png`.
