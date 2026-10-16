# Cartones y Mazmorras 2.0 — revisión web 2

Entrega del 16 de octubre de 2026. La versión pública sigue siendo 2.0.

## Archivos para subir

- **Cartones-y-Mazmorras-2.0-Web.zip**: reemplaza el ZIP web anterior en itch.io. Marca «This file will be played in the browser». El proyecto debe ser de tipo HTML. No lo marques como ejecutable de Windows.
- **Cartones-y-Mazmorras-2.0-Windows.zip**: descarga para PC. Tipo Executable, plataforma Windows. Deja desmarcada la opción de ocultar la descarga. Extraer el ZIP y ejecutar CartonesYMazmorras.exe.
- **Portada-2.0-630x500.png**: portada para la página. Se incluye también una copia de 1260×1000.
- **VERIFICACION-2.0.json**: registro local de validaciones y huellas SHA-256; no hace falta subirlo.

## Configuración web recomendada

Embed in page, tamaño manual 1280 × 800 y botón de pantalla completa activado. Dejar desactivados el inicio automático, las barras de desplazamiento y SharedArrayBuffer. La entrega se comprobó en Chrome de PC; la compatibilidad móvil requiere pruebas aparte.

Guarda los cambios de itch.io y abre el juego en una pestaña nueva. Si se conserva una versión anterior, recarga con Ctrl+Shift+R. Prueba también la pantalla completa.

## Cambios y comprobaciones

- Objetivo de 60 FPS restaurado en web. Medidas locales dentro de un iframe: 62,54 FPS en menú, 61,66 durante el duelo y 59,79 tras arrastrar una carta.
- Eliminado el doble escalado del puntero en web; Windows conserva su escalado habitual. Se comprobaron 30 posiciones con distintas dimensiones y densidades de píxeles, con una desviación máxima de 2 píxeles.
- Clic en colección y selección de duelo, arrastre real de una carta y finalización de un duelo comprobados en Chrome.
- Música reproducida mediante el audio del navegador, sin errores detectados en las pruebas locales.
- Suite de 1078 pruebas completada correctamente. ZIP de Windows extraído y comprobado con --check y --test.
- Las 250 imágenes de cartas incluidas en web se compararon con los originales. Esta revisión no cambia el arte.

Windows incluye el ejecutable ya validado de la revisión anterior, que funcionaba a 60 FPS. Las correcciones nuevas se aplican a web.

Las medidas corresponden al entorno local de prueba; no garantizan 60 FPS en cualquier equipo. La carga inicial sigue incluyendo la descarga y preparación de recursos. La página publicada debe comprobarse después de reemplazar el ZIP; estos archivos no se han subido automáticamente.
