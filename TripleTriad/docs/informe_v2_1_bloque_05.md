# Bloque 05 — Lectura del resultado y pausa

Rama `v2.1`, base `efaac75`. Continúa el apartado 3 del [plan principal](plan_principal_v2_1.md), con mejoras del regreso tras una derrota (apartado 10) y redacción (12).

## Problema observado y cambio

El resultado usaba una caja fija de 460 por 280 píxeles y líneas sin envolver. La auditoría detectó 361 incidencias de texto fuera del panel en 540 estados de resultado a escalas 100 %, 125 % y 160 %. Son incidencias, no 361 pantallas distintas. Las estadísticas ampliadas y algunas frases del rival salían del marco. El botón de abandonar también quedaba pequeño para su etiqueta ampliada.

`partida.py` distribuye ahora el resultado con las medidas de las fuentes reales. La caja crece según la escala de lectura y las líneas completas del rival se envuelven dentro del margen, sin recortarlas. El título conserva su animación; su altura final se reserva desde el primer frame. Las estadísticas muestran «Cadena máxima» y la indicación de continuar reconoce el clic existente. El espacio definitivo de esa indicación se reserva durante la entrada para evitar saltos del panel.

El botón de abandonar mide su etiqueta y comparte un único rectángulo entre dibujo y detección de clic. Se conserva la caché del resultado estático del bloque 04 y la espera del último efecto antes del resultado. No se modifican reglas, mazos, dificultad ni recompensas.

## Auditoría visual y comprobaciones

- [Comparación antes/después al 160 %](../auditoria/v2_1_bloque_05/comparativa.png): estadísticas dentro del marco y botón de abandonar con margen suficiente.
- [Medición anterior](../auditoria/v2_1_bloque_05/antes/resultados.json): 540 estados, 361 incidencias.
- [Medición posterior](../auditoria/v2_1_bloque_05/despues/resultados.json): los mismos 540 estados, cero incidencias. Diez facciones, seis nodos, victoria/derrota/empate y tres escalas. Además, pausa a las tres escalas.
- [Resultado real en Chrome al 160 %](../auditoria/v2_1_bloque_05/chrome/despues/resultado_1.6.png): frase larga íntegra en dos líneas.
- [Último Same del rival](../auditoria/v2_1_bloque_05/chrome/despues/cpu_final_efecto.png) y [derrota posterior](../auditoria/v2_1_bloque_05/chrome/despues/cpu_final_resultado.png): capturas resueltas por el motor real, sin superponer ambos anuncios.
- [Prueba de efectos web](../auditoria/v2_1_bloque_05/chrome/despues/resultados_web.json): Same, Plus, Quema, pausa, historial, movimiento reducido, resultado y lectura ampliada. Resultado estable: 62,51 FPS en Chrome headless local; música lista y sin error informado. No representa el rendimiento de todos los equipos ni de la página publicada.
- [Puntero](../auditoria/v2_1_bloque_05/chrome/puntero_iframe.json): repetición de doce posiciones a cuatro combinaciones de viewport/DPR, clic en colección, arrastre, duelo rápido completo y regreso al menú. El script terminó con código 0.
- [Suite completa](../auditoria/v2_1_bloque_05/tests.log): 1091 pruebas, OK, código 0. Se añadieron tres regresiones: frase completa y separación, área de clic ampliada y último Same del rival antes de derrota.
- [Verificación del build](../auditoria/v2_1_bloque_05/verificacion.json): `partida.py` del APK coincide con la fuente actual; fixture de auditoría excluida. Las 1221 imágenes protegidas siguen intactas.

Las capturas de resultado nativas tienen fondo controlado y marcador de prueba; comprueban geometría, no el desarrollo de una partida. Los estados web también se preparan deliberadamente para reproducir los efectos. Las comprobaciones no equivalen a jugar una campaña completa.

## Reproducir

Desde `E:/openCode/TripleTriad`, con Python 3.12 del proyecto:

```powershell
python tools/auditar_v2_1_bloque_05.py antes
python tools/auditar_v2_1_bloque_05.py despues
python auditoria/v2_1_bloque_05/crear_comparativa.py
python -m unittest discover -s tests -p test_v2_1_legibilidad.py -v
python -m unittest discover -s tests -v
python tools/preparar_web_release.py --v21-audit
python -m pygbag --build --no_opt --disable-sound-format-error --template E:/openCode/TripleTriad/build/v2_1_auditoria/cartones-mazmorras/plantilla_index.tmpl E:/openCode/TripleTriad/build/v2_1_auditoria/cartones-mazmorras
node auditoria/v2_1_bloque_05/efectos_check.mjs despues
node auditoria/v2_1_bloque_05/iframe_check.mjs
```

Ejecutar ambos scripts de Chrome secuencialmente: comparten puertos 8765 y 9225. Usan un perfil temporal y una página local con iframe. Los datos nativos de auditoría también son temporales. La fase `antes` de la herramienta nativa carga `partida.py` desde `efaac75`, sin reemplazar fuentes. El script web no selecciona código anterior: usar únicamente `despues` con el staging reconstruido actual. En este entorno Chrome requirió ejecutar el comando fuera del sandbox para arrancar sus procesos.

## Continuación

El recorrido interactivo completo de las dos rutas, `revancha=1`, el ritmo del prólogo en uso y las minicampañas siguen pendientes. No cerrar los tres primeros apartados por estas comprobaciones parciales. Se cubrieron en este bloque los pendientes de pausa/resultado ampliados y el efecto final del rival que termina en derrota.

La captura web con el nombre de prueba «Guardián de la Fortaleza» también permite observar que una etiqueta larga bajo el avatar rival puede salir del borde derecho; ese HUD requiere una pasada aparte con nombres reales y escalas ampliadas. No confundir el panel de resultado corregido con todo el HUD.

Las instrucciones del siguiente bloque están en la [guía de continuidad](continuidad_v2_1.md). La entrega pública y los ZIP de 2.0 permanecen iguales; este trabajo no publica ni prepara una entrega final 2.1.
