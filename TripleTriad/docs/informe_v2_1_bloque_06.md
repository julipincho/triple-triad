# Bloque 06 — Nombres y comentarios junto a los avatares

Rama `v2.1`, base `1b22063`. Continúa la legibilidad del apartado 3 del [plan principal](plan_principal_v2_1.md). Los cinco commits pendientes de los bloques anteriores se subieron a `origin/v2.1` antes de comenzar.

## Qué cambió y por qué

El nombre del rival se dibujaba en una sola línea centrada sobre un avatar próximo al borde derecho. El nombre del jugador usaba un ancho de 112 píxeles e interlineado fijo. El bocadillo del rival se colocaba por encima del retrato, usaba alturas fijas y descartaba todas las líneas posteriores a la tercera. Con texto ampliado, esto producía desbordes, líneas superpuestas y comentarios incompletos.

`partida.py` envuelve los nombres en un ancho de 240 píxeles y desplaza su centro lo necesario para respetar el margen derecho. Las líneas avanzan según la altura real de la fuente. Los avatares conservan su posición y su arte.

El bocadillo pasa a la columna libre debajo del nombre del rival, con un margen de 16 píxeles. Su altura depende de todas las líneas del comentario y de sus medidas reales; ya no se descartan líneas. Esta ubicación evita que una frase ampliada crezca hacia la barra superior del marcador. Se conserva la duración existente de los comentarios; evaluar su tiempo de lectura durante la pasada interactiva pendiente.

## Auditoría

La [herramienta](../tools/auditar_v2_1_bloque_06.py) dibuja el componente real con datos temporales. Revisa tutorial, diez facciones principales, ambas ramas, `revancha=0/1`, los cinco duelos de cada recorrido y las tres minicampañas. Usa entradas y comentarios de captura existentes a escalas 100 %, 125 % y 160 %. El nombre del jugador usa quince letras W, el máximo permitido, como caso de anchura exigente.

- [Antes](../auditoria/v2_1_bloque_06/antes/resultados.json): 1770 estados y 1534 incidencias de desborde, solapamiento o comentario recortado. Son incidencias, no pantallas distintas.
- [Después](../auditoria/v2_1_bloque_06/despues/resultados.json): los mismos 1770 estados, cero incidencias; 1221 imágenes protegidas intactas.
- [Comparación visual](../auditoria/v2_1_bloque_06/comparativa.png): tutorial y revancha al 160 %. Las capturas nativas aíslan el componente sobre fondo oscuro para examinar sus márgenes.
- [Capturas y resultados de Chrome](../auditoria/v2_1_bloque_06/chrome/despues/resultados_web.json): estados controlados de efectos, resultado, pausa y HUD al 100 %, 125 % y 160 %. El caso del HUD usa una revancha real de la rama aldea y verifica que el comentario completo está presente y sus líneas no se superponen.
- [Puntero y arrastre](../auditoria/v2_1_bloque_06/chrome/puntero_iframe.json): repetición de doce posiciones en iframe, clic en colección, arrastre y duelo rápido hasta regresar al menú. Script terminado con código 0.
- [Pruebas completas](../auditoria/v2_1_bloque_06/tests.log) y [verificación del build](../auditoria/v2_1_bloque_06/verificacion.json): resultados del cierre del bloque.

Esta auditoría examina estados del HUD con datos de campaña, no juega las campañas completas. La prueba de Chrome usa un iframe local y un perfil temporal; no modifica la página publicada. El arte, las cartas, los mazos, la dificultad y las recompensas no cambian.

La suite completa terminó con **1091 pruebas, OK y código 0**. La prueba de efectos/HUD de Chrome terminó con código 0, comprobó las tres escalas y conservó música lista sin error informado. El resultado estático se midió en 62,50 FPS antes de preparar las capturas del HUD; esa medida no corresponde a una campaña completa ni garantiza rendimiento en todos los equipos.

La fixture del HUD usa las manos por defecto del constructor para aislar la presentación, por lo que la captura muestra 25 cartas y no una mano de campaña. También expone otro pendiente: el nombre largo de prueba en la barra superior puede tocar el marcador. Este bloque corrige los textos junto a los retratos; la barra superior requiere medición y ajuste aparte. No atribuir la mano de la fixture a un fallo del flujo real.

## Reproducir y continuar

Desde `E:/openCode/TripleTriad`:

```powershell
python tools/auditar_v2_1_bloque_06.py antes
python tools/auditar_v2_1_bloque_06.py despues
python auditoria/v2_1_bloque_06/crear_comparativa.py
python -m unittest discover -s tests -v
python tools/preparar_web_release.py --v21-audit
python -m pygbag --build --no_opt --disable-sound-format-error --template E:/openCode/TripleTriad/build/v2_1_auditoria/cartones-mazmorras/plantilla_index.tmpl E:/openCode/TripleTriad/build/v2_1_auditoria/cartones-mazmorras
node auditoria/v2_1_bloque_06/efectos_check.mjs despues
node auditoria/v2_1_bloque_06/iframe_check.mjs
```

Los scripts de Chrome comparten puertos y se ejecutan secuencialmente. La auditoría nativa carga la fuente anterior desde `1b22063` sin reemplazar el árbol de trabajo. El script web no reconstruye revisiones anteriores: usar `despues` con el staging actual. Las fixtures se inyectan en el navegador para preparar casos, no se incluyen en el export.

El siguiente bloque debe priorizar el recorrido interactivo de las campañas y la lectura del prólogo; sigue pendiente. No cerrar los apartados 1–3 por estas capturas parciales. Tras esa validación, continuar con personalidad de rivales (apartado 4). Ver la [guía de continuidad](continuidad_v2_1.md). No preparar ni publicar 2.1 con los paquetes antiguos de 2.0.
