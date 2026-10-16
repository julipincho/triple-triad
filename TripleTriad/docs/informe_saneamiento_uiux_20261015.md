# Saneamiento de UI, lectura y presentación

Fecha: 15 de octubre de 2026.

## Cambios integrados

| Pantalla | Corrección |
|---|---|
| Colección | Rejilla de cinco columnas y dos filas con cartas a tamaño natural, separación de rareza y estado, espacio reservado para filtros y paginación. Se eliminan los cruces entre cartas y etiquetas. |
| Pestañas de colección | Avatar sobre el nombre, nombres completos en dos líneas y contador de finales separado. Se comprueban los diez bandos al 160%. |
| Estadísticas | Panel más ancho, dos filas para las rachas y separación respecto de TIENDA. También se revisan contadores altos y colección completa. |
| Diálogos | Se elimina la placa lateral redundante cuando existe retrato. El nombre real del hablante aparece debajo del avatar. Si no hay retrato se conserva una identificación del hablante. |
| Lectura de diálogos | La altura del cuadro y el interlineado se calculan con las líneas y la fuente reales, incluyendo texto ampliado. |
| Duelo | Avatar del jugador con gorra abajo a la derecha y nombre debajo. La mano reserva los márgenes necesarios para que incluso 25 cartas no lo tapen. El retrato del rival conserva su posición. |
| Decisiones narrativas | Composición centrada, sin avatar del jugador, según la corrección solicitada. Pregunta, opciones y ayuda tienen separación adaptativa. |
| Decisiones de ruta | Se reutiliza el camino aprobado como fondo. Las decisiones narrativas usan los fondos aprobados correspondientes a su localización. No se regeneran escenarios correctos. |
| Potenciar una carta | Diez cartas por página, distribuidas en dos filas de cinco, a escala 1,1 frente a la anterior 0,7. Se conservan las teclas 1-9 y 0, la paginación y los índices globales. El fondo se redibuja para no acumular oscuridad ni conservar texto de la pantalla anterior. |
| Construcción del mazo | VACIAR MAZO retira toda la selección de una vez, tanto en el editor global como en el de la partida. Vaciar y retirar cartas son acciones temporales: cancelar conserva el mazo anterior. |
| Validación del mazo | Al finalizar cualquiera de los editores se exigen exactamente diez cartas, además de propiedad, ausencia de duplicados y límites de rareza. La implementación anterior aceptaba de cinco a diez. No se modifican las reglas de los duelos ni se invalidan automáticamente guardados antiguos. |
| Minicampaña | Tarjetas de personaje más amplias, nombre del jefe envuelto dentro de su ficha y título lateral ajustado al ancho. El encabezado identifica la minicampaña y muestra sus tres rivales reales. |
| Eventos | Las ilustraciones se centran y escalan manteniendo su proporción dentro del interior del marco. El recorte de seguridad impide pintar encima del borde; se usa escalado sin suavizado para conservar el pixel art. |
| Observador inicial | Se adapta únicamente el personaje de «Alguien te ha visto» al estilo vigente, conservando ropa, cabello, gesto de advertencia e identidad. El nuevo retrato cuadrado evita comprimir la ilustración panorámica anterior. |
| Botones | El tamaño de etiqueta se ajusta cuando el texto ampliado excede su ancho. Se corrigen también controles y mensajes de validación que competían por el mismo espacio. |

## Español y tipografía

La causa de la pérdida de ñ y acentos estaba en `ui.limpio`: descomponía Unicode y eliminaba las marcas diacríticas. Ahora conserva ñ, Ñ, vocales acentuadas, ¿ y ¡ mediante normalización NFC. Se comprobó que la fuente del juego contiene glifos diferentes para estos caracteres.

La pregunta inicial se muestra como «¿CÓMO TE LLAMAN?». Se corrigieron etiquetas visibles de menús, colección, estadísticas y duelo, además de interrogaciones y vocabulario narrativo heredado. `idioma.py` aplica las correcciones de prosa antes de insertar el nombre del jugador, de modo que nombres como Íñigo Peñalosa se conservan y no se reescriben.

La selección de ilustraciones cinematográficas sigue recibiendo los datos originales: la corrección visible no altera las claves de los lotes aprobados. La generación de rutas de cartas se separó de la tipografía: `_slug` sigue produciendo exactamente los identificadores ASCII históricos, aunque el texto visible conserve sus acentos. No se cambian nombres de archivo, valores, habilidades ni ilustraciones de cartas.

## Verificación

- 1.074 pruebas de regresión aprobadas. Se verificaron también el inventario de recursos y el diagnóstico `--check` del ejecutable empaquetado.
- 120 comprobaciones generales de pantallas y estados con tipografía al 100%, 125% y 160%, sin desbordes detectados.
- 45 capturas específicas: colección completa, nombre con ñ y tildes, dos decisiones, diálogo, duelo, observador, potenciación, selector de minicampaña y seis eventos, en las tres escalas. Sin colisiones detectadas entre las imágenes registradas y los textos.
- 1.875 escenas cinematográficas examinadas con texto al 160%, sin desbordes detectados por la medición.
- Pruebas de vaciado real de ambos editores: selección vacía, guardado rechazado y cancelación sin modificar el estado anterior. Pruebas de paginación de entrenamiento actualizadas a las posiciones nuevas.
- Comparación SHA-256 de las 1.221 imágenes preexistentes protegidas: idénticas. Se añade un retrato nuevo; ninguna ilustración anterior se sobrescribe.
- Se actualizaron pruebas que todavía asumían texto sin acentos, arte pixel-anime como selección única o escenas sin campo HD. También se corrigió el aislamiento de una pantalla de pruebas que conservaba una superficie de video cerrada.

Los resultados completos de la suite y la compilación se guardan en `auditoria/uiux_saneamiento_20261015/tests.log` y `build.log`. Las capturas y mediciones están en esa misma carpeta; `resultados.json` contiene los casos concretos.

## Recursos y entrega

Nuevo retrato: `assets/pixel_anime/encuentros/hostil_v2.png`, 256 por 256 píxeles. Se selecciona desde `assets/pixel_anime/manifest.json`. La imagen anterior permanece disponible. Generado con la herramienta integrada `image_gen`; prompt y master en `auditoria/uiux_saneamiento_20261015/hostil_prompt.json` y `hostil_master.png`.

La versión nativa se recompila desde `TripleTriad.spec`, se comprueba el inventario del ejecutable y se actualiza la copia habitual `E:/openCode/TripleTriad.exe`. Los datos reales de partida no se usan para las comprobaciones.

## Alcance de la revisión

Esta entrega verifica el render real en el lienzo lógico de 1280 por 800 y los casos documentados mediante recorridos automatizados y revisión de capturas. No equivale a una garantía sobre cualquier texto arbitrario o tamaño físico de monitor. La corrección narrativa cubre el vocabulario y las preguntas revisadas; conviene una última lectura editorial manual del relato completo antes de publicar.
