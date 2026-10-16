# Versión 2.1 — bloque 01: intención, comienzo y lectura de jugadas

Fecha: 16 de octubre de 2026. Rama: `v2.1`. Base anterior: `cf3ccc3`.

Primera pasada acotada de los apartados **1, 2 y 3 por su numeración**. No confundir con el orden de prioridades 3, 2, 4 del plan. No se declara terminada la revisión integral de los tres frentes.

## Cambios y motivo

| Apartado | Problema observado | Cambio | Para qué |
| --- | --- | --- | --- |
| 1. Intención | Varias previas describían el lugar sin conectar el obstáculo con el objetivo del jugador. | Reescritura de una intervención existente en senda, aldea, ruinas, fortaleza, asalto y trono. | Entender por qué se pelea y qué permite conseguir la victoria, sin agregar pantallas. |
| 2. Comienzo | El torneo anunciaba dos veces la clasificatoria e incluía una escena cuyo único texto era «Presentador». | Previa de 8 a 6 escenas: un solo anuncio hablado, identificación de Juan y condición de victoria antes del primer duelo. | Llegar antes a jugar, conservando la ambientación, las cinco legendarias y la clasificación a la Copa. |
| 3. Jugadas | El rival podía actuar a los 0,85 s aunque el cartel de efecto dura 2 s. | La respuesta espera como mínimo lo que resta del cartel especial. Las jugadas normales conservan 0,85 s. | Leer el resultado de la propia jugada antes de que otra lo reemplace. |
| 3. Jugadas | Quema sin Same/Plus retornaba antes de anunciar su habilidad. | Usa el cartel existente para mostrar QUEMA: captura al empatar y no inicia cadena. Se reproduce el sonido de habilidad también en ese caso. | Explicar una captura que por comparación normal parece imposible. |
| 3. Lectura | Al 160 %, el cartel mantenía 17 px de interlineado; sus textos se tocaban. | Altura, separación del título y subtítulo, e interlineado calculados con la fuente real; la caché incluye la escala de lectura. | Mantener legibles los carteles al cambiar el tamaño de texto. |

En narrativa se conservaron las motivaciones de `duelistas.py`: el primer rival no quiere pelear; la aldea protege a su gente; las ruinas guardan un misterio; la fortaleza teme lo que cruza de vuelta; la revancha busca reparar una derrota; el trono conserva el control del Umbral. No se promete una recompensa, atajo o desbloqueo nuevo.

La frase narrativa del trono pasó de `titulo` a diálogo para que se envuelva en líneas y pueda leerse completa. No se cambió su fondo. En la aldea se mantuvo explícito el objetivo de llegar al trono y volver a casa tras detectar una regresión en la prueba de continuidad. El ancho del cartel especial se limita a 880 px y el subtítulo se envuelve dentro de ese ancho para dejar libres los retratos laterales incluso con texto ampliado.

## Auditoría visual

La [comparativa antes/después](../auditoria/v2_1_bloque_01/comparativa.png) muestra ejemplos de fortaleza, cierre de la previa del torneo y anuncio de Quema.

Capturas completas de referencia:

- [Fortaleza al 125 %](../auditoria/v2_1_bloque_01/despues/fortaleza_1.25.png).
- [Previa del torneo al 160 %](../auditoria/v2_1_bloque_01/despues/torneo_1.6.png).
- [Trono al 160 %](../auditoria/v2_1_bloque_01/despues/trono_1.6.png).
- [Quema al 160 %](../auditoria/v2_1_bloque_01/despues/efecto_quema_1.6.png).
- [Same al 160 %](../auditoria/v2_1_bloque_01/despues/efecto_same_1.6.png).
- [Plus al 160 %](../auditoria/v2_1_bloque_01/despues/efecto_plus_1.6.png).

Se generaron 30 capturas anteriores y 30 posteriores: seis previas de campaña, cierre de la previa del torneo y tres carteles, a escalas 1, 1,25 y 1,6. Se usan los renderizadores reales de cinemáticas y duelo, fondos HD asignados por el flujo y datos temporales aislados. Las capturas de efectos usan estados controlados para comparar su presentación, no se presentan como partidas completas.

El medidor general de pantalla no mide automáticamente cada línea dentro de una superficie cacheada. Por eso la revisión manual descubrió el interlineado y el título largo que la medición no denunciaba. Se añadió una prueba específica de geometría del cartel: verifica separación entre las líneas, límites de su superficie y actualización de caché en las tres escalas. La auditoría también rechaza capturas vacías; se corrigió el reloj de captura para no guardar el fundido negro inicial.

Resultados finales en [despues/resultados.json](../auditoria/v2_1_bloque_01/despues/resultados.json): ningún problema geométrico detectado y **1221 imágenes protegidas sin modificación**. Las cartas conservan su arte y composición.

## Comprobaciones

- Suite completa: **1082 pruebas**, resultado `OK`; registro en [tests.log](../auditoria/v2_1_bloque_01/tests.log).
- Cuatro pruebas nuevas resuelven casos con el motor real: espera antes de la respuesta a Same, ritmo normal sin cartel, Quema sin cadena inventada, y geometría/caché con texto ampliado.
- Revisión narrativa final: 29 pruebas `OK`, registro en [tests_narrativa_final.log](../auditoria/v2_1_bloque_01/tests_narrativa_final.log).
- No se modificaron reglas de captura, IA, mazos, valores de cartas, recompensas, guardados ni conversión del puntero. No hay esperas bloqueantes nuevas: sigue actualizándose el bucle de 60 FPS.

## Límites y continuidad

No se ha recorrido interactivamente toda la campaña ni se ha exportado o medido esta pasada en Chrome. Las comprobaciones aquí son nativas, automatizadas y visuales. No se generaron ZIP nuevos ni se actualizó itch.io; `ver2SubirV2` sigue siendo la entrega 2.0 estable.

Pendientes: minicampañas, coherencia de los diálogos posteriores con cada previa, resto del ritmo del prólogo, anuncios superpuestos al resultado final y validación interactiva de los tiempos en navegador. Detalles y comandos en [continuidad_v2_1.md](continuidad_v2_1.md).
