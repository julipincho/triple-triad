# Entrega itch.io 2.0

Carpeta de subida: `E:/openCode/ver2Subir`.

- Windows: `Cartones-y-Mazmorras-2.0-Windows.zip`, con ejecutable autónomo, instrucciones, versión y acción de inicio para la aplicación de itch.io.
- Navegador: `Cartones-y-Mazmorras-2.0-Web.zip`, con `index.html` en la raíz y el paquete de recursos actualizado. No necesita el TAR de prueba local: en itch.io el cargador usa el APK, que es un ZIP de recursos de pygbag, no una aplicación Android.
- Portada: PNG de 630 × 500 y 1260 × 1000, generada con `image_gen` a partir del logo y el duelista activo. Master y prompt conservados en `auditoria/release_2_0`.
- Instrucciones de publicación y comprobantes: `LEEME-SUBIR-A-ITCHIO.md` y `VERIFICACION-2.0.json`.

La versión visible viene de `version.py`; el ejecutable tiene ProductVersion 2.0 y FileVersion 2.0.0.0. El paquete web se reconstruyó desde un árbol limpio con dependencias locales del juego, cartas originales, fondos, avatares, manifiestos de selección y audio. Excluye partidas, perfiles, auditorías, masters de producción y herramientas. El audio musical OGG se exportó a ese árbol sin modificar los WAV originales.

Verificaciones: integridad de las 769 entradas del ejecutable y comparación de sus 472 imágenes con los archivos fuente; `--check` y `--test` del ejecutable extraído del ZIP, ambos con salida 0; integridad de ambos ZIP y del APK; comparación exacta de las 250 cartas del paquete web; versión 2.0 en el código empaquetado; estructura y límites de archivos de itch.io. También pasaron las pruebas existentes de portada y bucles async web.

Los registros de compilación y la captura de la prueba local en Chrome se conservan en `auditoria/release_2_0`. El navegador se prueba con un host local `.itch.zone` para recorrer la rama de carga APK que utiliza itch.io, usando el CDN HTTPS real. No se ha publicado ni cargado contenido en una cuenta de itch.io; la vista previa de la página final depende de su configuración.

Los dos ZIP son entregas distintas: el ZIP de Windows se ofrece como descarga y el de Web se marca como jugable en navegador. La portada se sube por separado.
