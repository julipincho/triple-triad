# Continuidad para agentes — versión 2.1

Actualizar este documento al terminar cada bloque. No requiere reconstruir la conversación.

## Encargo y estado

El usuario pidió mejorar el juego por bloques sencillos, con informes y auditorías visuales que expliquen qué cambió, para qué y por qué. Trabajar en **`v2.1`**. Plan autorizado en [plan_principal_v2_1.md](plan_principal_v2_1.md). Sin agregar funcionalidades ni sistemas.

El bloque 01 implementa una primera pasada de los apartados **1, 2 y 3**: intención de los duelos principales, entrada al torneo y legibilidad de efectos. Ver [informe](informe_v2_1_bloque_01.md). No confundir la numeración solicitada con el orden 3, 2, 4 sugerido previamente: el apartado 4 no se ha trabajado en esta pasada.

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

## Próximo bloque recomendado

1. Recorrer las dos variantes de ruta hasta el trono y revisar las previas nuevas contra las respuestas posteriores; comprobar que ninguna promesa exceda el efecto real. Las minicampañas todavía conservan su redacción original.
2. Revisar el resto del prólogo: despertar, explicación de Nara y elección de mazo. Conservar la promesa de volver a casa, el motivo del dragón histórico y la posibilidad de reintentar; las pruebas de `test_guion_cierre.py` protegen esos puntos.
3. Probar interactivamente efectos del jugador y del rival, incluyendo último movimiento, pausa, historial y movimiento reducido. El rival espera para no pisar el cartel del jugador; no se ha bloqueado la entrada del jugador durante un cartel del rival.
4. Exportar a una carpeta de desarrollo distinta de `ver2SubirV2` y comprobar Chrome/iframe antes de preparar la entrega 2.1. No atribuir a esta pasada medidas de rendimiento de la entrega anterior.

Después de esa validación, avanzar al apartado 4 (personalidad de los rivales) sin mezclar cambios de balance con correcciones de lectura. Guardar el siguiente informe como `docs/informe_v2_1_bloque_02.md` y enlazarlo desde aquí y desde el plan.
