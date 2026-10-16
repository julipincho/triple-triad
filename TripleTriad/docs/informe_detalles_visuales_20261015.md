# Detalles visuales: escenas, mapa y cartas

## Cambios

- «Escena ya vista»: nuevo archivo de memorias del Umbral, con piedra azul, portal de carta, magia cian/violeta y detalles dorados inspirados en el logo. Panel legible sobre el fondo; mismos controles para saltar o repetir.
- Derrota: nueva ilustración del duelista joven con gorra sentado junto a sus cartas y un portal apagándose. Conserva las acciones y posiciones de los botones.
- Amistad de Nara antes del último duelo: fondo propio de bosque otoñal, camino y señal de madera. Se aplica solo a esta secuencia; no cambia los otros caminos ni los fondos aprobados.
- Mapa de campaña: hitos para aldea, ruinas, fortaleza, asalto, bifurcación y portales; conexiones violetas con marcas doradas y recorrido activo cian. Indicador del nodo actual y señales de visita. Conserva nodos, decisiones, posiciones, navegación y menús.
- Cartas: «EMBESTIDA» usa una fuente local de 5 px que cabe en su placa, independiente de la ampliación del texto de interfaz. Las otras habilidades y la etiqueta «INACTIVA» conservan su renderizado.
- El cuadrado/rombo era una señal de propietario, no de afinidad. Se reubica en la esquina superior derecha; se elimina el punto sin propietario. La franja inferior queda libre para la facción. Se conservan arte, valores, marcos y composición restante.

## Recursos nuevos

Generados con la herramienta integrada `image_gen`, usando el logo, el arte aprobado y el retrato activo del duelista como referencias. Prompts completos: `auditoria/detalles_visuales_20261015/prompts.json`.

- `assets/pixel_anime/detalles/escena_vista_v2.png`
- `assets/pixel_anime/detalles/derrota_v2.png`
- `assets/cinematicas_hd/amistad_nara_camino_v2.png` (1280 × 720)

Los archivos originales se conservan. Los hitos del mapa se dibujan en Pygame; no se modifica el logo.

## Verificación

`tools/auditar_detalles_visuales.py` usa datos temporales y captura mapa inicial, mapa avanzado, derrota, escena vista y amistad de Nara con texto al 100%, 125% y 160%, además de cartas con Embestida y diferentes propietarios. Las 15 capturas de pantallas no presentan desbordes o colisiones de texto según la instrumentación existente. Se revisaron visualmente las capturas principales.

Se verificó por SHA-256 que las 1.221 imágenes del inventario anterior siguen idénticas. Esto incluye los recursos de cartas y los fondos ya aprobados. Resultados y capturas: `auditoria/detalles_visuales_20261015/`.

Las mediciones corresponden al lienzo lógico de 1280 × 800; no sustituyen una comprobación en todos los tamaños físicos de monitor.

La suite completa pasó sus 1.074 pruebas. La comprobación de propiedad por forma se actualizó para inspeccionar la esquina superior derecha y conserva los criterios de visibilidad y distinción en escala de grises. Registro completo: `auditoria/detalles_visuales_20261015/tests.log`.

## Ejecutable

Actualizado `E:/openCode/TripleTriad.exe` y su copia en `dist/TripleTriad.exe`. La primera compilación presentó una entrada comprimida dañada; se descartó y se reconstruyó desde cero. La versión final supera `--check` con salida 0: se descomprimieron correctamente las 769 entradas y se compararon las 472 imágenes incluidas con sus archivos fuente. Evidencia: `auditoria/detalles_visuales_20261015/ejecutable.json`.

SHA-256 final: `8ce63ce648983621c5e4ad8417b499ba547a0b60e35a6200a1996e303e5f02f7`.
