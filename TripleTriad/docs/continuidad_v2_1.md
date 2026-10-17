# Continuidad para agentes — versión 2.1

Actualizar este documento al terminar cada bloque. No requiere reconstruir la conversación.

## Encargo y estado

El usuario pidió mejorar el juego por bloques sencillos, con informes y auditorías visuales que expliquen qué cambió, para qué y por qué. Trabajar en **`v2.1`**. Plan autorizado en [plan_principal_v2_1.md](plan_principal_v2_1.md). Sin agregar funcionalidades ni sistemas.

El bloque 01 implementa una primera pasada de los apartados **1, 2 y 3**: intención de los duelos principales, entrada al torneo y legibilidad de efectos. Ver [informe](informe_v2_1_bloque_01.md). El bloque 02 continúa esos apartados con consecuencias de duelos y previas de minicampañas; ver [informe](informe_v2_1_bloque_02.md). El bloque 03 reduce repeticiones del prólogo y aclara la transición al mazo; ver [informe y auditoría](informe_v2_1_bloque_03.md). No confundir la numeración solicitada con el orden 3, 2, 4 sugerido previamente: el apartado 4 todavía no se ha trabajado.

## Restricciones que deben conservarse

- No modificar el arte de las cartas ni las escenas ya correctas.
- No reintroducir afinidades/sinergias de facción eliminadas.
- Conservar los 60 FPS como objetivo y la corrección del puntero web: `BANDERAS_ESCALA = 0` en emscripten, escalado por CSS.
- Conservar la reproducción de música web mediante `audio_web.py`.
- La versión pública sigue siendo 2.0; cambiarla solo al preparar la entrega 2.1.
- No tocar perfiles ni partidas reales. Para pruebas y capturas usar `TRIPLETRIAD_DATA` temporal.
- `E:/openCode` es la raíz de Git; el juego vive en `E:/openCode/TripleTriad`. Los dos archivos ajenos sin seguimiento (`contexto.md` y `ace-step-dashboard-v1.4-validation.png`) se dejaron fuera de los commits.

## Archivos del bloque 01

- `narrativa.py`: una intervención previa por nodo principal; el trono usa diálogo para envolver la frase completa.
- `prologo.py`: previa del torneo de ocho a seis escenas.
- `partida.py`: cartel y sonido de Quema, respuesta del rival tras finalizar el cartel especial, geometría del cartel y caché según escala de lectura.
- `tests/test_v2_1_legibilidad.py`: cuatro pruebas de comportamiento/geométricas.
- `tools/auditar_v2_1_bloque_01.py`: captura antes/después, mide pantalla y compara SHA-256 de imágenes protegidas. El estado anterior se obtiene de las fuentes de `cf3ccc3`; no reemplaza los archivos actuales del juego.
- `auditoria/v2_1_bloque_01/`: capturas a tres escalas, snapshots de escenas, resultados JSON, comparativa y registros de pruebas.

## Reproducir la validación

Desde `E:/openCode/TripleTriad`, Python instalado en `C:/Users/julip/AppData/Local/Programs/Python/Python312/python.exe`:

```powershell
python tools/auditar_v2_1_bloque_01.py antes
python tools/auditar_v2_1_bloque_01.py despues
python -m unittest discover -s tests -p test_v2_1_legibilidad.py -v
python -m unittest discover -s tests -v
```

La auditoría configura SDL dummy y un directorio temporal de datos. Importante: sus estados de efecto son controlados, no partidas completas. Revisar imágenes además del JSON: los textos cacheados requieren inspección de su propia superficie, no solo el medidor general.

En PowerShell 5.1, al redirigir stderr de unittest puede aparecer un resultado de shell engañoso aunque unittest diga `OK`. Capturar el código real con `exit $LASTEXITCODE` al final del comando. Los mensajes de error de ComfyUI o `ZeroDivisionError('division by zero')` al pie del registro forman parte de pruebas deliberadas de fallo; mirar el resumen de unittest.

## Bloque 02: estado y comprobaciones

- `narrativa.py`: consecuencias de victoria en los seis nodos principales; título posterior del trono abreviado para evitar un desborde al 160 %.
- `duelistas.py`: cierres de victoria y derrota coherentes con el obstáculo de cada nodo. No cambia la identidad del rival ni su facción.
- `campana.py`: solo las tres cadenas `NODOS_MINI[*].previa`; no se modificaron transiciones ni recompensas.
- `tools/auditar_v2_1_bloque_02.py`: 20 rutas principales y tres minicampañas; 109 estados de duelo con comprobación de derrota sin avance y victoria con transición. Son resultados simulados, no partidas jugadas contra la IA.
- Capturas y registros en `auditoria/v2_1_bloque_02/`: 63 frames medidos por fase, 27 capturas por fase, un desborde anterior del título frente a cero posteriores; 1221 imágenes protegidas intactas.
- Las minicampañas no llaman a `escenas_posterior` como la campaña principal. No agregar ese flujo bajo el supuesto de que ya existe.
- Suite completa del bloque 02: 1082 pruebas `OK`, código de salida 0. `tests.log` está en UTF-8. Las dos comprobaciones antiguas de ASCII se adaptaron al español soportado y a la cobertura de la fuente.

```powershell
python tools/auditar_v2_1_bloque_02.py antes
python tools/auditar_v2_1_bloque_02.py despues
python -m unittest discover -s tests -v
```

La fase anterior se compara contra `cf2b62f`; carga módulos narrativos aislados y las previas antiguas de minicampaña, sin hacer checkout ni tocar el árbol de trabajo.

## Bloque 03: estado y comprobaciones

- `prologo.py`: despertar 12 a 7 escenas, encuentro hostil 7 a 6, Nara 11 a 8, explicación 19 a 13, cierre 5 a 4. Total del tramo: 54 a 38. No confundir este total con todo el prólogo, que incluye también el torneo y el transporte.
- Se conservan la torre conocida, las legendarias, Pik, la amenaza, la explicación del dragón histórico, la vuelta a casa, cinco duelos y reintentos. La transición final describe el mazo existente de diez cartas y la mano de cinco.
- `tests/test_prologo.py`: la frase Juicio ahora se comprueba con la grafía «Aquí». El orden exigido no se cambió.
- `tests/test_revision_visual_hover.py`: los fondos se comprueban por escenario y con listas no vacías, no por los índices que cambian al condensar escenas. Incluye el trono como caso explícito.
- `tools/auditar_v2_1_bloque_03.py`: base anterior `7689a0f`, todas las escenas de los cinco tramos medidas a tres escalas. 162 frames anteriores y 114 posteriores, 60 capturas comparativas, ningún problema detectado; 1221 imágenes protegidas intactas.
- Evidencias y registros en `auditoria/v2_1_bloque_03/`. Las pruebas específicas del prólogo, su flujo y el cierre narrativo pasan. La suite completa terminó con 1082 pruebas `OK` y código de salida 0, registrada en `tests.log` en UTF-8.

```powershell
python tools/auditar_v2_1_bloque_03.py antes
python tools/auditar_v2_1_bloque_03.py despues
python -m unittest discover -s tests -p test_prologo.py -v
python -m unittest discover -s tests -p test_flujo_prologo.py -v
python -m unittest discover -s tests -p test_guion_cierre.py -v
```

## Bloque 04: Chrome y presentación de efectos

Ver [informe y auditoría](informe_v2_1_bloque_04.md). Se construyó un build aislado con `tools/preparar_web_release.py --v21-audit` en `build/v2_1_auditoria`. `partida.py` corrige L durante pausa, conservación de anuncios al consultar pausa/historial, orden efecto final/resultado, tooltips superpuestos y reutilización del resultado estático. La caché se invalida al abrir pausa/historial o cambiar escala/movimiento reducido; no debe almacenar frames con animaciones pendientes.

Las herramientas y evidencias están en `auditoria/v2_1_bloque_04`. `iframe_check.mjs` y `efectos_check.mjs` usan **los mismos puertos 8765 y 9225**: ejecutar secuencialmente. Chrome usa un perfil temporal. `fixture_web.py` se inyecta en /tmp del navegador para estados controlados, no forma parte del export ni modifica cartas o perfiles reales. No confundir estos estados con una campaña jugada de principio a fin.

La fase `antes` del script de efectos no hace checkout del código antiguo: exige servir un build anterior para recrear la comparación. Las evidencias anteriores corresponden al código base `9f1c926`. Reconstruir siempre el staging actual antes de validar `despues`. La cadena de versión sigue en 2.0; verificar hashes y presencia del prólogo condensado.

La suite completa pasó con **1088 pruebas, OK y código 0**. La repetición de efectos en Chrome pasó: Same, Plus, Quema, rival, pausa, historial, movimiento reducido y orden del resultado final. El resultado estable pasó de 32,49 FPS sin caché a 62,47 FPS con caché en este entorno. Antes de dar por cerrada una nueva pasada, comprobar los resultados JSON y las capturas, no solo que el script termine.

La navegación del build final también pasó: menú 62,45 FPS, duelo 62,47, muestreo tras arrastre 57,04; 12 posiciones de puntero con desviación máxima de 2 px, audio listo sin error y duelo rápido terminado con regreso al menú. Son medidas locales de Chrome headless, no un certificado de rendimiento de la página publicada. Los comandos exactos de reconstrucción y prueba están en el informe 04.

## Bloque 05: resultado y pausa ampliados

Ver [informe y auditoría](informe_v2_1_bloque_05.md). `partida.py` envuelve el resultado y calcula caja/filas con fuentes reales; `_rect_abandonar` comparte geometría entre dibujo y clic. Cero incidencias en 540 estados frente a 361 anteriores; 1091 pruebas OK. Chrome local verificó efectos, pausa y resultado al 125 %/160 %, último Same de CPU seguido de derrota, puntero, arrastre y regreso al menú. Resultado estable: 62,51 FPS. Evidencias nuevas en `auditoria/v2_1_bloque_05`; conservar las del 04.

La herramienta nativa `tools/auditar_v2_1_bloque_05.py antes` sí carga automáticamente `partida.py` de `efaac75`. Los scripts web del bloque 05 usan el staging `v2_1_auditoria` actual y deben ejecutarse secuencialmente; no seleccionan automáticamente una revisión anterior. No se jugaron las campañas completas en este bloque. La captura de resultado web con nombre largo de prueba muestra además un pendiente fuera del panel: la etiqueta del avatar rival puede desbordar a la derecha. Medir nombres reales antes de corregir ese HUD.

## Bloque 06: nombres y bocadillos del duelo

Ver [informe y auditoría](informe_v2_1_bloque_06.md). Se subieron primero los cinco commits pendientes hasta `1b22063` a `origin/v2.1`. `partida.py` envuelve nombres junto a los avatares con márgenes de pantalla e interlineado real. El bocadillo ocupa la columna libre debajo del nombre, calcula su altura y conserva todas las líneas. No mover el arte ni volver al recorte de tres líneas. La duración actual de 3,6 segundos se conserva: evaluar lectura en uso antes de ajustarla.

Auditoría nativa: 1770 estados, 1534 incidencias anteriores frente a cero posteriores; incluye datos de tutorial, dos ramas, revancha 0/1 y minicampañas. No equivale a jugar esos recorridos. La herramienta `tools/auditar_v2_1_bloque_06.py antes` carga `partida.py` de `1b22063`. Evidencias de Chrome y suite en `auditoria/v2_1_bloque_06`; conservar las de bloques anteriores.

## Bloque 07: recorridos completos y editor

Ver [informe y auditoría](informe_v2_1_bloque_07.md). Se cierra la validación automatizada pendiente de la primera pasada de los apartados 1, 2 y 3: humanos por aldea, orcos por ruinas con `revancha=1` y las tres minicampañas. Se ejecutaron los bucles reales con eventos SDL, no resultados sustituidos. Total: 28 duelos, ocho reintentos con el mismo rival y 394 escenas completas; finales de equilibrio y dominio. No se jugaron aquí las veinte combinaciones de facción/ruta, el final de caos ni el arco secreto. La política conoce ambas manos: no usar sus tasas de victoria como medida de dificultad humana.

El prólogo y su duelo se completaron antes de encontrar un fallo del editor. Dos rutas de compatibilidad para tests interceptaban clics reales; se eliminaron. Se reanudó desde el editor conservando solo el perfil temporal y las escenas ya registradas, sin conceder victorias. Las minicampañas se terminaron en perfiles independientes. El registro canónico y la sesión principal original están en `auditoria/v2_1_bloque_07`; los detalles de reanudación y reunión de evidencias están en el informe.

`pantallas.armar_mazo` compone los paneles de cartas en una sola capa local y opaca, invalidada por selección, página, hover, escala y tamaño. Los botones y tooltips quedan fuera de la caché; el fondo exterior sigue animado. `ui.MEDIR` desactiva esa caché para conservar los registros geométricos por frame. No cambiar las claves ni introducir una caché sin límite. El editor lleno pasó de 29,30 a 62,49 FPS en Chrome local. Los clics, vaciado, validación de diez cartas y guardado se repitieron con la fuente final. La suite completa pasó con 1094 pruebas; 1221 imágenes protegidas intactas.

Herramientas: `tools/jugar_v2_1_bloque_07.py` para recorridos reales con datos temporales, `tools/verificar_editor_bloque_07.py` para reproducir antes/después del fallo, y `tools/cerrar_auditoria_bloque_07.py` para comprobar las evidencias. El comando `--tests` del cierre ejecuta y registra la suite completa. No usar `--resume-editor` para una pasada nueva: requiere el checkpoint temporal de esta auditoría. Para repetir Chrome, reconstruir primero el staging actual y ejecutar `node auditoria/v2_1_bloque_07/editor_check.mjs`; comparte puertos con los scripts anteriores.

## Próximo bloque recomendado (08)

1. Avanzar al apartado 4, personalidad de rivales. Medir primero la distribución de habilidades y valores de los mazos que entrega `campana.mazo_rival` y revisar las prioridades existentes en `partida.Juego._elegir_jugada_cpu`. Guardar una base por facción/nodo/semilla antes de cambiar pesos o distribución. No introducir sistemas nuevos ni afinidades.
2. Proponer y aplicar un bloque pequeño sobre perfiles existentes, justificando cómo hace reconocible al rival sin saltos gratuitos de fuerza. Separar cambios de personalidad de la revisión de dificultad del apartado 5. No usar la política omnisciente de esta auditoría como sustituto de un jugador para balancear.
3. El bloque 06 dejó otro caso de UI para una pasada específica: un nombre máximo puede tocar el marcador de la barra superior. Los nombres junto a los retratos sí se corrigieron. No dar por auditada toda la barra superior por las capturas de este bloque, que usan «Auditoría» como nombre.
4. La lectura humana y el tiempo de los bocadillos de 3,6 segundos se pueden evaluar con jugadores; esta pasada demuestra presentación y continuidad automatizada. No afirmar que mide comprensión o emoción. No repetir todos los recorridos largos por cambios ajenos al flujo: escoger pruebas según el cambio.
5. Antes de entregar 2.1, preparar paquetes nuevos de Windows/Web y validar la entrega y la página publicada. Los paquetes públicos siguen en 2.0; estas pruebas locales no certifican una actualización de itch.io.

Atención al empaquetar: `tools/empaquetar_release_2_0.py` selecciona el staging R2 de 2.0, no `v2_1_auditoria`. No usarlo para una entrega 2.1 sin adaptar explícitamente rutas y versionado. Los títulos del preparador, `version.py`, `version_info.txt` y el ejecutable se deben revisar al preparar esa entrega; no basta con renombrar el ZIP.

Guardar el siguiente informe como `docs/informe_v2_1_bloque_08.md` y enlazarlo desde aquí y desde el plan. Conservar los informes y evidencias cerrados de los bloques 01–07.

Para el navegador hay referencias de pruebas reales en `auditoria/web_60fps_20261016/browser_check.mjs` e `iframe_check.mjs` (Node y Chrome mediante CDP). Esos scripts apuntan al build antiguo `release_2_0_web_r2`: copiarlos para el bloque 04 y ajustar el directorio servido y la carpeta de evidencias. No usar sus resultados o su APK como prueba de esta rama. Medir los FPS del juego mediante `web_diagnostico.py` y `window.__ttDiag` con `?auditar=1`, no únicamente los de `requestAnimationFrame`. Usar un perfil temporal de Chrome y preservar las auditorías y paquetes estables anteriores.

Para la validación nativa ejecutar las fuentes actuales con `python main.py` y un `TRIPLETRIAD_DATA` temporal. Los ejecutables existentes en `dist` y las entregas de `ver2SubirV2` siguen siendo 2.0: abrirlos no valida estos cambios de 2.1. No usar el perfil real del jugador para una pasada automatizada.
