# Corrección — Mazos rápidos independientes

Rama `v2.1`, base `f38bed0`. Petición del usuario: permitir jugar rápidos desde el primer inicio sin introducir cartas ajenas en la colección o el mazo de campaña.

## Causa y solución

`main._duelo_rapido` llamaba a `campana.asegurar_mazo_global`. Con una colección vacía, esto ejecutaba el ritual de cinco cartas aleatorias y completaba un mazo inicial humano. El rápido dependía así de cartas poseídas y modificaba los datos que encontraba después la campaña.

Ahora el rápido tiene dos pasos: **elegir tu mazo prestado** y **elegir rival**. El jugador y el rival reciben cinco cartas sorteadas de sus respectivos mazos predefinidos de diez. Las diez cartas de la vista previa son las mismas que pueden aparecer en ese duelo. Se permite enfrentar la misma facción.

`mazos_rapidos.py` define diez listas fijas, una por facción, y entrega copias nuevas del catálogo original. Cada mazo tiene diez cartas distintas, una legendaria, hasta tres raras y una suma total de valores de 250. Se incluyen habilidades existentes de cada facción; esos criterios ofrecen un presupuesto comparable, no una certificación de balance competitivo. No se modificó ningún valor ni arte del catálogo. Las listas son explícitas: no se regeneran al arrancar el juego.

El rápido ya no llama al ritual, al reparador del mazo global ni al editor de cartas poseídas. Al terminar conserva las estadísticas generales de duelos/victorias que ya registraba. Colección, mazo global, mejoras, moneda, recompensas y archivo de campaña quedan como estaban. Cancelar cualquiera de los dos selectores no crea un perfil.

Los perfiles antiguos conservan todas sus cartas. No hay una procedencia fiable que permita retirar automáticamente las concedidas por rápidos anteriores sin arriesgar cartas obtenidas durante la aventura. La campaña mantiene su entrega inicial y su editor de diez cartas.

## Comprobaciones

- `tests/test_rapidos_independientes.py`: varios rápidos desde un perfil nuevo; rápido seguido de nueva campaña con editor real; campaña con mejora, rápido y continuación; cancelación en ambos selectores; presets legales y copias independientes. Los resultados del duelo se sustituyen en estas pruebas para aislar la persistencia. El prólogo se omite en la prueba de transición, pero el editor se opera con sus eventos reales.
- [Auditoría visual y mazos](../auditoria/rapidos_independientes_20261017/visual_y_mazos.json): ambos selectores a escalas 100 %, 125 % y 160 %, sin desbordes o solapamientos detectados. Se retiró una indicación redundante de confirmación que podía tocar el texto de habilidades al 125 %; el pie ya explica ENTER.
- [Elegir mazo](../auditoria/rapidos_independientes_20261017/chrome/elegir_mazo.png) y [elegir rival](../auditoria/rapidos_independientes_20261017/chrome/elegir_rival.png): pantallas del build actual en Chrome dentro de un iframe local.
- [Aislamiento en Chrome](../auditoria/rapidos_independientes_20261017/chrome/aislamiento.json): perfil temporal vacío antes del rápido, manos procedentes de los presets, colocación real por arrastre, duelo completo con regreso al menú y colección/mazo todavía vacíos. No se inyectan victorias, cartas ni modificaciones al flujo: la sonda solo lee el estado.
- [Suite completa final](../auditoria/rapidos_independientes_20261017/tests_final.log) y [verificación de entrega local](../auditoria/rapidos_independientes_20261017/verificacion.json): resumen de pruebas, recursos protegidos, fuentes incluidas en el APK y mediciones locales.

La prueba del navegador usa un perfil de Chrome temporal. No actualiza itch.io ni los paquetes estables de 2.0. No se repitieron las campañas completas del bloque 07: esta corrección no modifica su motor ni sus transiciones.

Cierre: **1099 pruebas, OK y código 0**. Chrome completó el rápido, colocó una carta mediante arrastre y regresó al menú con colección y mazo vacíos. Menú: 62,52 FPS; duelo: 62,44 FPS; cero excepciones JavaScript. Las 1221 imágenes protegidas siguen intactas. Son mediciones locales, no una garantía de rendimiento para cualquier equipo o para la versión publicada.

## Reproducir y continuar

```powershell
python -m unittest discover -s tests -p test_rapidos_independientes.py -v
python -m unittest discover -s tests -v
python tools/auditar_rapidos_independientes.py
python tools/preparar_web_release.py --v21-audit
python -m pygbag --build --no_opt --disable-sound-format-error --template E:/openCode/TripleTriad/build/v2_1_auditoria/cartones-mazmorras/plantilla_index.tmpl E:/openCode/TripleTriad/build/v2_1_auditoria/cartones-mazmorras
node auditoria/rapidos_independientes_20261017/browser_check.mjs
```

Ejecutar desde `E:/openCode/TripleTriad`. El navegador comparte puertos 8765 y 9225 con las auditorías anteriores; ejecutar una a la vez. `probe.py` se carga únicamente en `/tmp` del navegador de prueba y no forma parte del export.

Conservar la separación entre presets y cartas obtenidas. No reintroducir `asegurar_mazo_global` en el camino del rápido. Para cambiar un preset, editar su lista y repetir las pruebas de legalidad y aislamiento; no añadir sus cartas a la colección. Esto corrige los modos, no completa el apartado 4 de personalidad de rivales en campaña, que sigue siendo el siguiente bloque del plan.
