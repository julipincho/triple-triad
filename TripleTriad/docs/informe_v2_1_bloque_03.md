# Versión 2.1 — bloque 03: ritmo del prólogo y elección de mazo

Fecha: 16 de octubre de 2026. Rama: `v2.1`. Base: `7689a0f`.

Continúa el apartado 2 del plan. Esta pasada trabaja el tramo posterior al transporte al otro mundo, desde el despertar hasta la transición a elegir facción y construir el mazo. No cambia el torneo ya revisado en el bloque 01 ni agrega funciones.

## Qué cambió y por qué

| Tramo | Antes | Después | Cambio y propósito |
| --- | --- | --- | --- |
| Despertar | 12 | 7 | Se reúnen la llegada al bosque y la mochila; se conecta la torre con la carta conocida; se eliminan las dos pantallas cuyo único texto era «Pik». Conservar el descubrimiento y llegar antes al diálogo. |
| Encuentro hostil | 7 | 6 | Se une la llegada del segundo observador con su procedencia de la aldea. Conservar la amenaza y la reacción del protagonista sin un avance intermedio. |
| Presentación de Nara | 11 | 8 | Se reúne su entrada, se conecta «cartones» con «Juicio» y se elimina el anuncio previo a su pregunta. Mantener el contraste entre ambos mundos sin explicar dos veces la misma transición. |
| Explicación del Umbral | 19 | 13 | Se reúnen apertura y grieta, y se conecta el control del Umbral con el trono. Se quitan frases que solo anuncian que llegará una explicación o una pregunta. Preservar los hechos del misterio y la voz de Nara. |
| Elección de mazo | 5 | 4 | Se reúnen dos frases de transición y se aclara que el mazo contiene diez cartas y que a cada duelo se llevan cinco. Ayudar a comprender el editor que aparece después. |
| **Total del tramo** | **54** | **38** | **16 escenas menos**, aproximadamente un 30 % menos de pasos si se lee el tramo completo. Esto no es una medición de tiempo de lectura. |

La nueva frase sobre diez y cinco cartas describe el funcionamiento existente de `main._nueva_campana`, el editor de mazo y `campana.cartas_duelo`. No se cambiaron reglas, tamaños de mazo o manos.

## Qué se conservó

- Las cinco legendarias llegan con el protagonista, pero no pasan a ser el mazo inicial de campaña.
- La torre sigue siendo reconocible por una carta; el protagonista conserva su reacción de incredulidad.
- Pik reconoce las cartas como algo que no debería estar ahí. La amenaza de la aldea ocurre antes de conocer a Nara.
- Nara recibe el relato del torneo y explica que los duelos de este mundo se llaman Juicio.
- Quien ocupa el trono guarda el Umbral. La sangre del dragón explica una expresión popular; no impone un rival final de una especie concreta.
- El objetivo sigue siendo volver a casa; el camino tiene cinco duelos y perder permite reintentar.
- Se conservan la pausa de Nara, la intervención «Yo no vine a salvar nada» y el cierre «CASA».
- Fondos, retratos, música y sus asignaciones permanecen. No se generó ni se retocó arte.

## Auditoría visual

Herramienta: `tools/auditar_v2_1_bloque_03.py`. La fase anterior carga solo `prologo.py` del commit base, sin reemplazar fuentes del árbol de trabajo. Usa las funciones públicas de escenas y el reproductor real, con datos temporales aislados.

Se midió **cada escena** a escalas 100 %, 125 % y 160 %: 162 frames anteriores y 114 posteriores. Para comparar se guardaron diez anclas semánticas por escala, **30 capturas por fase, 60 en total**. Las anclas se buscan por contenido y no por el índice que cambia al condensar las secuencias.

La medición de títulos comprueba además el rectángulo real que recibe su resplandor. Las capturas vacías provocan un fallo. Resultado: ningún problema detectado en ambas fases y **1221 imágenes protegidas intactas**. También se comprobó que cada tramo conserve sus conjuntos de fondos, fondos HD, retratos y mundos. Se inspeccionaron las capturas ampliadas de la torre, el diálogo de Nara, la explicación del trono y la transición al mazo.

- [Comparativa antes/después](../auditoria/v2_1_bloque_03/comparativa.png).
- [Reconocimiento de la torre al 160 %](../auditoria/v2_1_bloque_03/despues/despertar_torre_1.6.png).
- [Nara explica el Juicio al 160 %](../auditoria/v2_1_bloque_03/despues/nara_juicio_1.6.png).
- [Trono y Umbral al 160 %](../auditoria/v2_1_bloque_03/despues/explicacion_trono_1.6.png).
- [Diez cartas y mano de cinco al 160 %](../auditoria/v2_1_bloque_03/despues/cierre_mazo_1.6.png).
- [Resultados](../auditoria/v2_1_bloque_03/despues/resultados.json) y [guion completo de este tramo](../auditoria/v2_1_bloque_03/despues/escenas.json).

## Comprobaciones y límites

Pasaron las pruebas específicas de `test_prologo.py`, `test_flujo_prologo.py` y `test_guion_cierre.py`. La comprobación textual del nombre Juicio se actualizó a la grafía española «Aquí», conservando la exigencia de que aparezca después de la amenaza. La prueba de fondos de `test_revision_visual_hover.py` ahora selecciona escenas por escenario en lugar de índices fijos: valida que existan y que tengan su fondo HD correcto, incluido el trono, aunque se condensen diálogos.

La ejecución completa terminó con **1082 pruebas aprobadas**, resultado `OK` y código de salida 0. El registro está en [tests.log](../auditoria/v2_1_bloque_03/tests.log), en UTF-8. También se comprobaron los 17 enlaces locales del informe, el plan y la guía de continuidad.

Las capturas usan SDL dummy y texto completamente revelado. No prueban el ritmo subjetivo de una lectura interactiva ni miden rendimiento en navegador. No se cambió el motor de cinemáticas, el salto de escenas, la persistencia, el puntero, el audio o el límite de FPS. La entrega publicada y `ver2SubirV2` permanecen en 2.0.

El siguiente bloque debe validar interactivamente los efectos y el recorrido en Chrome antes de cerrar los apartados 1–3. Ver [guía de continuidad](continuidad_v2_1.md).
