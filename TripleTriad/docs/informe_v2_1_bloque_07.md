# Bloque 07 — Recorridos completos y corrección del editor

Rama `v2.1`, base `9eddb94`. Cierre de la validación automatizada pendiente de la primera pasada de los apartados 1, 2 y 3 del [plan principal](plan_principal_v2_1.md).

## Método y alcance

Se ejecutan los bucles reales de campaña, cinemáticas, duelo, decisiones, recompensas y finales. Una herramienta envía eventos SDL de clic y teclado; el rival mantiene su IA y el motor resuelve las capturas y el resultado. No se sustituyen victorias ni se modifican valores de cartas. Cada partida usa datos temporales.

La política automatizada conoce ambas manos y busca jugadas sobre copias del tablero. Sirve para comprobar continuidad y estabilidad, no para medir dificultad humana. La presentación nativa se renderiza con SDL dummy y reloj normal. Las escenas avanzan cuando el texto está completo, sin activar la opción de saltarlas. Esto verifica el flujo y la disponibilidad de lectura, pero no certifica comprensión o emoción de un jugador.

La ruta principal de aldea usa humanos y la de ruinas usa orcos, esta última con `revancha=1` como variante inicial explícita. Ese selector de identidad no es el contador de derrotas. Las tres minicampañas se prueban con perfiles temporales independientes. No se afirma haber jugado las veinte combinaciones de facción/ruta; aquellas tienen la cobertura de modelo y texto del bloque 02.

## Fallo encontrado y corregido

Al terminar el prólogo, el editor podía seleccionar otra carta al pulsar en el centro de una carta visible. Dos rutas de compatibilidad para pruebas antiguas tenían prioridad sobre la geometría real: una reinterpretaba clics usando posiciones de una fila antigua y otra mantenía una zona invisible de guardar.

Se retiraron ambas rutas de `pantallas.armar_mazo`. Las pruebas antiguas usan ahora las coordenadas actuales. Dos regresiones nuevas comprueban la identidad de la segunda carta y que la posición antigua de guardar no acepte el mazo. Ambas fallan con la fuente anterior y pasan con la actual.

La construcción inicial se interrumpió al detectar ese fallo. Se conservaron el registro de las 63 escenas completas del prólogo, el duelo real contra Juan Rajoy y el perfil temporal; después de corregirlo se reanudó desde el editor, usando la interfaz real para elegir y guardar diez cartas. No se concedieron victorias ni recompensas para saltar encuentros. La segunda ruta comienza con el estado inicial normal de campaña, sin repetir el prólogo ya examinado.

La medición sostenida encontró además que el editor lleno caía a 29,30 FPS en Chrome. Se añadió una única capa local de los paneles de cartas: se recompone al cambiar página, selección, hover, escala de texto o tamaño de pantalla. Los botones y tooltips se dibujan normalmente; el fondo exterior conserva su animación. La zona de fondo bajo esos paneles queda compuesta mientras su contenido no cambia. La caché se desactiva al medir geometría con `ui.MEDIR`, y se descarta al salir del editor. No crece con cada clic. Una regresión comprueba la reutilización entre frames y la recomposición al retirar/reponer una carta.

## Evidencia visual y funcional

- [Antes y después del mismo clic](../auditoria/v2_1_bloque_07/comparativa_editor.png): antes se desmarca la tercera carta; después, la segunda. El arte es idéntico.
- [Regresiones contra ambas fuentes](../auditoria/v2_1_bloque_07/editor_regresiones.json): dos fallos anteriores y cero posteriores.
- [Editor en Chrome](../auditoria/v2_1_bloque_07/chrome/editor_completo.png) y [eventos comprobados](../auditoria/v2_1_bloque_07/chrome/editor_resultados.json): seleccionar la segunda carta, pulsar la zona antigua sin guardar, vaciar todas, rechazar el guardado incompleto, elegir las diez visibles y guardar. También se repitieron doce posiciones de puntero en iframe; código de salida 0. Editor lleno: 62,49 FPS frente a [29,30 sin caché](../auditoria/v2_1_bloque_07/chrome/editor_resultados_sin_cache.json); menú local: 62,47 FPS. No es una medida de la página publicada.
- [Mapa antes del trono, rama aldea](../auditoria/v2_1_bloque_07/principal_aldea_mapa_campana_trono.png): progreso, mazo y estado tras la derrota anterior.
- [Registro de todos los recorridos](../auditoria/v2_1_bloque_07/recorridos.json): pantallas, escenas completas, manos iniciales, rival, marcador y estado final de cada partida.
- [Verificación de cierre](../auditoria/v2_1_bloque_07/verificacion.json): solo se genera si terminan las dos rutas y las tres minicampañas, los reintentos conservan nodo/personaje, asalto reconoce la rama en `revancha=1`, los duelos usan manos de cinco y el build contiene las fuentes actuales.
- [Suite completa final](../auditoria/v2_1_bloque_07/tests_final.log): 1094 pruebas, OK, código 0. Los mensajes de errores deliberados de pruebas no representan fallos de estos recorridos.

## Lectura y continuidad narrativa

En el flujo del prólogo se conservan las cinco legendarias, la llegada a otro mundo, Pik, Nara, el objetivo de volver a casa y el Juicio de cinco duelos. La transición al editor explica una vez el mazo de diez y la mano de cinco. El texto llegó completo antes de avanzar y el duelo contra Juan se resolvió 8–1.

La campaña humana terminó con dos derrotas y el final de equilibrio «LA PAZ CONGELADA», seguido del Umbral y el epílogo en el salón. Las derrotas de aldea y trono regresaron al mismo encuentro y personaje. Los cierres y recompensas se obtuvieron mediante el flujo normal. Las minicampañas alcanzaron sus tres victorias y sus finales; sus derrotas también pasaron por el reintento real.

El cierre verificó **28 duelos reales, ocho reintentos con el mismo rival y 394 escenas completas**. Los resultados fueron:

| Recorrido | Victorias de campaña | Derrotas | Cierre |
| --- | --- | --- | --- |
| Humanos, aldea | 5 | 2 | Equilibrio: LA PAZ CONGELADA |
| Orcos, ruinas, revancha 1 | 5 | 1 | Dominio: EL TRONO DE CENIZA |
| Elfos nocturnos | 3 | 0 | Minicampaña completa |
| Hombres pantera | 3 | 4 | Minicampaña completa |
| Hombres lagarto | 3 | 1 | Minicampaña completa |

El total incluye el duelo del prólogo. No se modificaron diálogos ni finales en este bloque: se comprobaron los cambios narrativos anteriores en funcionamiento. No se atribuye a estos recorridos el final de caos ni el arco secreto, que no se jugaron aquí.

## Reproducir

Desde `E:/openCode/TripleTriad`, con Python 3.12 del proyecto:

```powershell
python tools/verificar_editor_bloque_07.py
python tools/jugar_v2_1_bloque_07.py
python tools/preparar_web_release.py --v21-audit
python -m pygbag --build --no_opt --disable-sound-format-error --template E:/openCode/TripleTriad/build/v2_1_auditoria/cartones-mazmorras/plantilla_index.tmpl E:/openCode/TripleTriad/build/v2_1_auditoria/cartones-mazmorras
node auditoria/v2_1_bloque_07/editor_check.mjs
python tools/cerrar_auditoria_bloque_07.py --tests
```

El recorrido completo tarda varios minutos porque conserva reloj y animaciones. `--case mini_nocturno`, `--case mini_pantera` o `--case mini_lagarto` permiten probar cada minicampaña en su propio perfil y subcarpeta. En la evidencia de este bloque se ejecutaron por separado; `cerrar_auditoria_bloque_07.py --merge-minis` reúne esos registros una vez terminadas las dos campañas principales y conserva la sesión principal original.

El ejecutor principal se detuvo después de completar ambas rutas, evitando repetir las minicampañas ya terminadas por separado. `recorridos_sesion_principal.json` conserva también el comienzo de esa repetición; no se cuenta como una minicampaña adicional. La fuente del editor se optimizó después del recorrido principal: la comprobación de clics/guardado se repitió en Chrome con esa fuente final, además de la suite completa.

`--resume-editor` se reserva para reproducir la reanudación de esta auditoría: requiere su perfil temporal copiado en `build/v2_1_b07_resume`. Para una prueba nueva usar el comando sin esa opción. No copiar perfiles del jugador. Las fixtures web solo existen en el navegador temporal y se excluyen del export. Los puertos del script de Chrome son 8765 y 9225; no ejecutarlo junto a otros scripts que los ocupen.

La entrega pública y los paquetes de 2.0 siguen iguales. No se ha publicado ni empaquetado 2.1. La [guía de continuidad](continuidad_v2_1.md) indica el siguiente bloque y las comprobaciones que no deben atribuirse a esta pasada.
