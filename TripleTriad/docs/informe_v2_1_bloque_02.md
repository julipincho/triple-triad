# Versión 2.1 — bloque 02: consecuencias y minicampañas

Fecha: 16 de octubre de 2026. Rama: `v2.1`. Base anterior: `cf2b62f`.

Continúa los apartados 1–3 del plan, con foco en que el cierre de cada encuentro responda a lo que se planteó antes de jugar. No incorpora mecánicas ni sistemas.

## Qué cambió, para qué y por qué

| Zona | Cambio | Motivo |
| --- | --- | --- |
| Senda | La narración y el rival reconocen que el Juicio terminó y se puede seguir. La derrota explica por qué el paso permanece cerrado. | Cerrar el conflicto del personaje que no quería pelear, sin sugerir que perder permite avanzar. |
| Aldea | Ganar permite pasar, sin convertir automáticamente la desconfianza en amistad. Perder conserva el obstáculo. | Respetar la motivación protectora del custodio y distinguir victoria de confianza. |
| Ruinas | La victoria permite estudiar el dibujo; las reliquias siguen custodiadas. La derrota invita a ordenar las cartas y reintentar. | Conectar el misterio anunciado antes del duelo con su consecuencia, sin prometer una carta o reliquia nueva. |
| Fortaleza | La puerta se abre al ganar, pero permanece la advertencia sobre lo que cruza por el Umbral. | Evitar que vencer borre el motivo legítimo del rival. |
| Revancha | El diálogo distingue expresamente la segunda victoria del jugador de la victoria del rival; el camino queda libre solo en el primer caso. | Hacer que el resultado cierre o prolongue la revancha de forma comprensible. |
| Trono | El vencedor recibe el control del Umbral y su responsabilidad. La derrota recuerda que volver a casa tendrá que esperar otro Juicio. | Cerrar el conflicto y conservar la promesa de regreso, sin adelantar el epílogo. |
| Trono, lectura | El largo título posterior se reemplaza por «EL JUICIO TERMINA». | La auditoría anterior mostraba un rótulo de 1396 px en una pantalla de 1280 px al ampliar texto al 160 %. |
| Minicampañas | Las tres previas explican qué obstáculo se disputa. El último encuentro dice «Solo queda este duelo». | Corregir la contradicción «Tres duelos te separan... Este es el último» y dar intención a los encuentros existentes. |

Se reemplazaron intervenciones existentes: no se agregaron pantallas ni clics obligatorios. Los escenarios, retratos, música, decisiones, mazos, IA, recompensas y transiciones mantienen su comportamiento. Los diálogos nuevos conservan el registro informal y usan signos de apertura y acentos cuando corresponde.

## Recorrido y auditoría visual

Herramienta reproducible: `tools/auditar_v2_1_bloque_02.py`. La fase `antes` obtiene los datos narrativos del commit base sin reemplazar los archivos de trabajo. Ambas fases usan los constructores reales de escenas (`info_duelo`, `escenas_nodo`, `escenas_posterior`) y el reproductor real para capturar.

- **20 rutas principales:** diez facciones por dos bifurcaciones. Cada una conserva cinco duelos y termina en el trono.
- **Tres minicampañas:** cada una conserva sus tres duelos.
- **109 encuentros del modelo:** se comprobó victoria y derrota en cada estado. Las 109 derrotas mantienen el nodo; en campaña principal también se verificó que el reintento conserve nombre, retrato y facción del rival.
- **63 frames medidos por fase:** 21 casos de presentación en escalas 100 %, 125 % y 160 %.
- **54 capturas guardadas:** 27 anteriores y 27 posteriores. Se guarda cada caso al 100 % y tres ejemplos exigentes también al 125 % y 160 %.
- Estado anterior: un desborde de título detectado. Estado posterior: ningún problema detectado en los casos medidos.
- **1221 imágenes protegidas intactas.**

[Comparativa visual antes/después](../auditoria/v2_1_bloque_02/comparativa.png).

Ejemplos completos al 160 %: [custodio tras la victoria](../auditoria/v2_1_bloque_02/despues/aldea_rival_victoria_1.6.png), [cierre del Juicio](../auditoria/v2_1_bloque_02/despues/trono_victoria_1.6.png), [último encuentro de minicampaña](../auditoria/v2_1_bloque_02/despues/mini_trono_previa_1.6.png).

Los registros completos incluyen [recorridos](../auditoria/v2_1_bloque_02/despues/recorridos.json), [escenas generadas](../auditoria/v2_1_bloque_02/despues/escenas.json) y [resultados visuales](../auditoria/v2_1_bloque_02/despues/resultados.json).

## Validación y límites

La suite completa terminó con **1082 pruebas aprobadas**, `OK` y código de salida 0; el resultado está en [tests.log](../auditoria/v2_1_bloque_02/tests.log), guardado en UTF-8. Se actualizaron dos comprobaciones heredadas que prohibían todo carácter no ASCII: ahora admiten el español ya soportado por el juego, rechazan caracteres corruptos y verifican los glifos acentuados de los diálogos con la fuente real.

Los recorridos simulan los resultados de los duelos y ejecutan las transiciones reales del modelo. No son partidas interactivas ni miden el balance de la IA. Las capturas son nativas con SDL dummy; no sustituyen las pruebas en Chrome. El recorrido usa la variante predeterminada de revancha; las variantes adicionales siguen protegidas por las pruebas existentes.

Las minicampañas no reproducen la secuencia posterior de la campaña principal: por eso sus cambios se aplican a las previas que sí muestra `main._mini_campana`, sin agregar un nuevo flujo de escenas.

No se exportó un ejecutable ni un ZIP nuevo y no se alteró la entrega estable `ver2SubirV2` o la publicación en itch.io. Siguiente paso: ritmo de la explicación de Nara y elección de mazo; después validar los tiempos de efectos y la versión web. Ver [continuidad_v2_1.md](continuidad_v2_1.md).
