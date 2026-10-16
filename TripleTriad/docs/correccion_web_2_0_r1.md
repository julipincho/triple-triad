# Correccion de carga y audio web — 2.0, revision web 1

Se conserva el versionado publico 2.0. El ZIP web de `E:/openCode/ver2Subir` se reemplaza por la revision corregida; los paquetes anteriores se guardan en `auditoria/release_2_0`.

## Cambios

- Descompresion del APK por bloques con cesion al navegador y porcentaje de preparacion. La descarga inicial sigue siendo grande: no se reduce calidad ni se cambia el arte para disimular ese coste.
- Las imagenes opacas se convierten a superficies opacas, evitando mezcla alfa innecesaria. Se conserva la transparencia de las imagenes que la necesitan.
- Limite web de 30 FPS para reducir la carga de dibujo. Windows mantiene 60 FPS.
- Musica web en `HTMLAudioElement`, con reproduccion, cambio de pista, bucle, pausa, reanudacion y volumen. Deja de compartir el mezclador SDL/WASM usado para efectos. Los cambios de pista descartan errores de cancelacion esperados del reproductor anterior.
- Efectos web exportados a OGG, con hashes propios y conversion unica por archivo compartido. Los WAV nativos y sus manifiestos originales se conservan. El mezclador de efectos web se configura antes de iniciar pygame con un buffer de 2048 muestras.
- Reparacion del mazo global: el ritual historico de cinco cartas se conserva, pero se completa la coleccion si hace falta para permitir un mazo legal de diez. Se respetan limites de rareza y se conserva un mazo valido existente. Evita quedar atrapado en un editor que exige diez cartas cuando solo hay cinco disponibles.

## Evidencia y limites

La suite completa paso 1.076 pruebas; las dos pruebas nuevas de perfil inicial tambien pasaron por separado. Se comprobaron las 1.221 imagenes protegidas: sin cambios. El ejecutable reconstruido supera la comprobacion de integridad de todas sus entradas y recursos.

Los registros `perf_baseline.json` y `perf_r1.json` y las capturas estan en `auditoria/release_2_0`. La prueba usa Chrome real con un host local `.itch.zone`, descarga el entorno HTTPS real y recorre pantallas del juego. El audio se comprueba mediante estado, avance temporal y errores del reproductor: no sustituye una escucha en el equipo del usuario.

El bloqueo de mazo se reprodujo y se reparo. No se reprodujo en esta maquina un congelamiento permanente del render anterior; los cambios de rendimiento y audio deben comprobarse tambien en el Chrome del usuario. Los recorridos de referencia no son identicos y no se presentan como una comparacion controlada de FPS. Las cifras de requestAnimationFrame miden respuesta del navegador, no los FPS internos del juego.

La revision final recorrio portada, introduccion, menu, selector y duelo con entradas de teclado. El reproductor de musica alcanzo `readyState=4`, avanzo el tiempo y permanecio reproduciendo sin error antes, durante y despues del duelo. Hay pausas transitorias de preparacion del entorno y recursos: la prueba registra una tarea inicial de aproximadamente 1,2 segundos, por lo que no se afirma que la carga inicial sea instantanea ni completamente libre de pausas.

## Subida

Reemplazar `Cartones-y-Mazmorras-2.0-Web.zip` en itch.io, mantener la opcion de jugar en navegador y guardar la pagina. Cerrar la ejecucion anterior y volver a abrir el juego; si se ve contenido viejo, recargar con Ctrl+Mayus+R. No cambiar SharedArrayBuffer para aplicar esta correccion.
