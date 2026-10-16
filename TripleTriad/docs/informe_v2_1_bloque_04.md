# Versión 2.1 — bloque 04: Chrome, pausa y cierre de jugadas

Fecha: 16 de octubre de 2026. Rama: `v2.1`. Base: `9f1c926`.

Se preparó un build de desarrollo en `build/v2_1_auditoria/cartones-mazmorras/build/web`. No se reemplazaron los ZIP estables, los ejecutables 2.0 ni la publicación en itch.io.

## Problemas reproducidos y cambios

| Problema confirmado en Chrome | Cambio | Para qué |
| --- | --- | --- |
| Pulsar L durante pausa abría un historial oculto, que requería cerrar antes de reanudar. | El atajo de historial respeta la misma restricción de pausa que el clic. | Mantener coherente la navegación. |
| Same desaparecía mientras se leía pausa o historial. | Se congela el reloj de presentación y se desplazan los tiempos de los anuncios al reanudar. El historial oculta el anuncio mientras está abierto. | Conservar el tiempo disponible para leer la jugada. |
| El resultado tapaba Same en la última jugada. | Se programa el resultado para después del anuncio; su sonido y la opción de continuar esperan esa presentación. | Mostrar efecto y resultado en orden. |
| Un tooltip de carta se dibujaba encima del resultado. | Tooltips y preview por hover se reservan a la interacción normal, fuera de pausa, historial, efecto y resultado. | Evitar que el puntero tape el texto que se está leyendo. |
| El resultado inmóvil seguía recomponiéndose en WASM y rondaba 32 FPS en la prueba. | Tras concluir las animaciones se reutiliza un fotograma opaco del resultado. Pausa, historial, escala de texto y movimiento reducido invalidan la caché. Las partículas y sacudida pueden terminar después del último movimiento. | Reducir el trabajo repetido de la pantalla estática y recuperar el objetivo de 60 FPS. |

No se alteraron las reglas, la IA, los mazos, la propiedad de las cartas ni sus imágenes. El juego sigue actualizando eventos y presentando frames a 60 FPS; las esperas de lectura no usan bloqueos ni `sleep` síncrono.

## Evidencias y pruebas

Se usó Chrome headless con un perfil temporal, servido dentro de un iframe local desplazado y con las mismas proporciones del juego. El host de prueba termina en `.itch.zone` para usar la carga APK del exportador. No equivale a probar la página remota publicada ni sus permisos. La automatización permite autoplay; la política de inicio de audio de un navegador normal requiere su gesto de usuario.

La repetición general del build final midió FPS reales mediante `web_diagnostico.py`: menú **62,45**, duelo **62,47** y **57,04** en la ventana de muestreo posterior al arrastre. Se comprobaron 12 posiciones del puntero en cuatro combinaciones de tamaño/DPR, con desviación máxima de dos píxeles, clic en colección y duelo, arrastre y finalización de un duelo rápido con regreso al menú verificado. La música avanzó con estado listo 4 y sin error. No hubo excepciones JavaScript registradas. El registro inicial anterior a las correcciones también se conserva en `perf_iframe_inicial.json`.

Los casos de efectos usan `fixture_web.py`, inyectado únicamente en `/tmp` del navegador de prueba. Se preparan estados controlados en memoria, pero las jugadas del jugador se realizan con clics CDP y las capturas las calcula el motor real. La fixture no se importa ni se incluye en el juego exportado. Estas pruebas no son recorridos completos de campaña contra la IA.

Los registros antes/después incluyen Same del jugador, Quema, Same del rival, pausa, historial, movimiento reducido y efecto del último movimiento. Se añadió un caso explícito de Plus a la repetición posterior. Los resultados están en [antes/resultados.json](../auditoria/v2_1_bloque_04/antes/resultados.json) y [despues/resultados.json](../auditoria/v2_1_bloque_04/despues/resultados.json). La medición intermedia del resultado sin caché quedó en [resultado_sin_cache.json](../auditoria/v2_1_bloque_04/resultado_sin_cache.json).

Referencias visuales: [comparativa antes/después](../auditoria/v2_1_bloque_04/comparativa.png), [efecto final anterior](../auditoria/v2_1_bloque_04/antes/final_efecto.png), [efecto final corregido](../auditoria/v2_1_bloque_04/despues/final_efecto.png), [resultado corregido](../auditoria/v2_1_bloque_04/despues/final_resultado.png) y [reanudar Same](../auditoria/v2_1_bloque_04/despues/reanudado.png).

La repetición final de efectos terminó con código 0 y midió **62,47 FPS** en el resultado estable, frente a **32,49 FPS** en la etapa anterior sin caché. Pasaron las **1088 pruebas** de la suite completa, resultado `OK` y código 0, registradas en [tests.log](../auditoria/v2_1_bloque_04/tests.log). Las seis regresiones añadidas cubren conservación del anuncio, orden del resultado, tooltip, L durante pausa, caché e invalidación y fin de las animaciones. Las medidas corresponden a este entorno local; no certifican 60 FPS en cualquier dispositivo o situación.

Se verificaron 1221 imágenes protegidas sin modificaciones y se contrastaron las fuentes `partida.py`, `prologo.py` y `ui.py` dentro del APK contra el árbol actual. La fixture de pruebas está excluida del APK. Resumen en [verificacion.json](../auditoria/v2_1_bloque_04/verificacion.json).

## Reproducir y continuar

1. Preparar con `python tools/preparar_web_release.py --v21-audit` y compilar con pygbag usando la plantilla del staging. Nunca usar el APK antiguo de R2 como evidencia de esta rama.
2. Ejecutar **por separado** `node auditoria/v2_1_bloque_04/iframe_check.mjs` y `node auditoria/v2_1_bloque_04/efectos_check.mjs despues`. Comparten los puertos 8765 y 9225: no ejecutarlos en paralelo.
3. La opción `antes` del script de efectos solo selecciona la carpeta de evidencias; no cambia el código servido. La captura anterior se obtuvo antes de corregir `partida.py`, con el build de base 9f1c926. Para recrearla, preparar un staging y colocar allí la versión antigua de `partida.py`, nunca sobre las fuentes actuales; después reconstruir el staging actual para la fase posterior.
4. Las huellas de builds y fuentes están en los JSON de esta auditoría. La cadena pública de versión continúa en 2.0; identificar este build por su código y su hash, no solo por ese rótulo.

Comandos desde `E:/openCode/TripleTriad`:

```powershell
python tools/preparar_web_release.py --v21-audit
python -m pygbag --build --no_opt --disable-sound-format-error --template E:/openCode/TripleTriad/build/v2_1_auditoria/cartones-mazmorras/plantilla_index.tmpl E:/openCode/TripleTriad/build/v2_1_auditoria/cartones-mazmorras
node auditoria/v2_1_bloque_04/efectos_check.mjs despues
node auditoria/v2_1_bloque_04/iframe_check.mjs
python -m unittest discover -s tests -v
```

Pendientes para el siguiente agente: recorrer interactivamente las dos rutas de campaña y el prólogo, revisar la variante de revancha 1 y comprobar el comportamiento en la página real después de una futura publicación autorizada. No declarar esos recorridos completados por los casos controlados de este bloque. Directivas en [continuidad_v2_1.md](continuidad_v2_1.md).
