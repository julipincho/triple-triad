# Primera entrega — consolidación visual, 14/10/2026

**Estado: base protegida y renovación especificada; producción artística pendiente.**
Rama: `arte/consolidacion-primer-arco-20261014`, desde `96e9ec1`.
Cartas intactas. Sin cambios de runtime, asignaciones, diálogos, música ni mecánicas.

## 1. Referencias oficiales y protección

La integración real identifica estos dos lotes, no el lote local posterior:

| Lote / commit | PNG bajo `assets/cinematicas_hd/` | Uso vigente |
|---|---|---|
| 01 / `21be366` | `salon_torneo.png` | Regresos al mundo real; el torneo activo pasó al Lote 02 |
| 01 / `21be366` | `camino_lluvioso.png` | Despertar y Pik |
| 01 / `21be366` | `sala_trono.png` | Cierre, introducción y campaña, según callsites existentes |
| 02 / `4229c2e` | `salon_torneo_lleno.png` | Torneo activo, Juan y entrada de organizadores |
| 02 / `4229c2e` | `revelacion_carta_torneo.png` | Cambio sobrenatural; continuidad corregida en `96e9ec1` |
| 02 / `4229c2e` | `portal_umbral_torneo.png` | Último instante de la visión, antes del apagón |

`proteccion.json` registra rutas, SHA-256, commits y referencias por archivo/línea.
Los seis exports coinciden con los manifiestos y con sus copias runtime.
Los masters NO están extraídos en staging: están dentro de
`E:/AI/CartonesMazmorrasVisual/CartonesMazmorras_Lote01_1280x720.zip`
y `CartonesMazmorras_Lote02_1280x720.zip`. Se verificaron los seis hashes de sus
miembros originales. Se respaldaron ambos ZIP completos, exports y estado visual
actual en `C:/Users/julip/AppData/Local/Temp/opencode/consolidacion_20261014_estado_visual.zip`.
Su hash está en el manifiesto. Es un respaldo local, no almacenamiento externo permanente.

La rama conserva los cambios previos sin commit, incluidos música y selector
visual. El respaldo incluye el diff binario previo y los recursos visuales
activos; no es un commit ni una copia íntegra del repositorio.

**Discrepancia de aprobación:** `assets/pixel_anime/manifest.json` activa 19
avatares, 36 fondos y 6 encuentros de una producción local posterior. Estar
seleccionados por ese manifiesto no demuestra aprobación del usuario. Se
conservan tal como estaban; no se certifican como nueva referencia oficial.
Tampoco se desactiva globalmente el selector, porque afectaría trabajo previo.

## 2. Inventario operativo del primer arco

Fuente: `docs/biblia_visual_maestra_v1.md` (dirección artística),
`auditoria/informe_historia_cinematicas.md`, `docs/integracion_cinematicas_hd.md`
y datos actuales de `prologo.py`. Las secciones históricas de entrenamiento no
forman parte de este encargo. `escenas_runtime.json` registra las 81 escenas
renderizadas, texto, retrato y fondo efectivo. Índices siguientes: **base cero**.

| Prioridad / recurso propuesto | Escenas existentes | Diagnóstico y especificación |
|---|---|---|
| Conservado: torneo general | `pre_duelo[0]`, `post_duelo[0:5]`, `carta_umbral[0]` | Lote 02 aprobado. Mantener salón lleno, orientación, luces y arquitectura. |
| P0 `escenario_torneo_continuidad.png` | `pre_duelo[1:5]`, `carta_umbral[1:4]` | Actual `assets/pixel_anime/cinematicas/escenario.png`: bloqueado grueso y paleta violeta/cian ajenos al salón. Nuevo plano medio del mismo escenario: cerchas metálicas, cortinas azules, paneles cálidos, mesa y público ambiental. Organizadores como figuras secundarias; Presentador sigue siendo retrato separado. Sin magia anticipada. |
| P0 `publico_torneo_continuidad.png` | `pre_duelo[5:8]` | Actual `publico.png` del lote local. Contraplano de asistentes del mismo recinto, mesas y escala humana compatibles; focos cálidos/fríos del salón. Sin inventar otra arena. El duelo clasificatorio sigue siendo la partida existente. |
| P0 detalle escénico previo al fenómeno | `carta_umbral[3:6]` | El escenario genérico no explica la observación detallada. Encuadre próximo de presentación/caja dentro del salón, sin luz sobrenatural. **No producir, redibujar ni editar ninguna carta ni sus símbolos.** Cualquier detalle que requiera arte de carta queda bloqueado por esa exclusión; usar únicamente lo ya aprobado cuando corresponda. |
| P0 `inicio_fenomeno_salon.png` | `carta_umbral[6:8]` | Actual `umbral.png` local es un arco de piedra exterior: rompe la localización. Nuevo plano del recinto real con primeras alteraciones de luz y reacción ambiental, todavía sin portal culminante. Conservar elementos estructurales del Lote 02. No diseñar cartas. |
| Conservado: revelación y ruptura | `carta_umbral[8:11]` | Lote 02 ya cubre revelación y portal final. No sustituir ni añadir filtros. La figura sin facción es deliberadamente no identificada; no inventar su rostro, especie o soberano. |
| P1 `reaccion_publico_salon.png` | Candidato para fase sobrenatural, sin callsite nuevo autorizado | Necesidad documentada, pero no hay escena textual autónoma de reacción. Preparar contraplano de asistentes ante la alteración del mismo salón. No insertar escena, reordenar prólogo ni desplazar las tres asignaciones HD aprobadas. Requiere acordar ubicación antes de integrar. |
| P0 `apagon_salon_continuidad.png` | `transporte[0:3]` | Actual `apagon.png` local muestra otro recinto. Imagen nueva del mismo salón oscurecido, coherente con el portal anterior, focos apagados; sin bosque. Especificar estado oscuro, no implementar una transición animada nueva. |
| Conservado: despertar | `despertar[0:12]` | Camino lluvioso aprobado. La torre y Pik permanecen en el contexto fantástico. |
| P2 `despertar_punto_de_vista.png` | Posible `despertar[0:2]`, sin reasignar ahora | Variante opcional, no carencia bloqueante: barro y lluvia a baja altura, misma vegetación/torre del camino; mochila y teléfono según texto. No mostrar cartas ni inventar anatomía del protagonista. |
| P1 continuidad posterior | `encuentro_hostil`, `nara`, `explicacion` | Fuera del arco estricto hasta despertar, pero necesario para el piloto Nara. Camino y campamento locales muy saturados/gruesos; producir campamento húmedo con niebla moderada, fuego focal y sombras azul pizarra, sin convertirlo en biblioteca. |

### Contrato común de fondos nuevos

PNG RGB/RGBA 8 bits, **1280×720**, sin texto, diálogos, logos o interfaz.
Anime pixel art cinematográfico detallado: agrupaciones de píxeles deliberadas,
anatomía/arquitectura coherentes, profundidad por planos y fuentes de luz claras.
El salón aprobado fija ventanas laterales, columnas, cerchas, escenario, telas,
mesas y temperatura de iluminación. Cambiar cámara, no inventar otro recinto.
Paleta del bosque diferenciada, húmeda y contenida. No fotorrealismo, 3D,
plasticidad, desenfoque, filtros globales ni pixelado de fotografía.
Los PNG aprobados son referencias de consulta, nunca lienzos para repintar.

Canvas lógico vigente: 1280×800; imagen 1:1 en `(0,40)`.
Panel de diálogo: `(120,588,1040,152)` en pantalla: reservar en el PNG la región
equivalente desde y=548. Retrato aproximadamente `(840,120,150,150)`:
evitar focos narrativos detrás de esa zona. Revisar también los títulos centrados.

## 3. Avatares que requieren armonización

Evaluación visual del catálogo activo y de las capturas reales. Es un diagnóstico
artístico, no una autorización de reemplazo. Los archivos se llaman
`assets/pixel_anime/avatares/avatar_<clave>.png`; sus anteriores siguen en
`assets/avatar_<clave>.png`. Todos los pilotos finales deben seguir en 256×256;
el renderer los muestra a 150×150 con vecino más cercano.

| Prioridad | Claves | Desajuste observado |
|---|---|---|
| P0 piloto | `pik` | Verde muy luminoso, figura hasta cintura; cara pequeña sobre el bosque sobrio. |
| P0 piloto | `nara` | Encuadre incluye escritorio/manos y biblioteca: pierde rostro y trae otra localización al campamento. |
| P0 piloto | `rajoy` | Rostro reconocible y buen encuadre de partida; sombreado limpio/plano y fondo uniforme se separan de la iluminación cinematográfica del salón. Renovación sutil, sin cambiar actor. |
| P1 | `presentador` | Mismo contraste entre retrato plano claro y escenario; coordinar con Juan tras validar pilotos. |
| P1 | `goblin`, `orco`, `hombre_lagarto` | Verdes intensos; el lagarto añade paisaje y ocupa mucho torso. Conservar anatomía goblin, orca y reptiliana, respectivamente. |
| P1 | `dragon`, `elfo`, `elfo_nocturno` | Acentos rojo/naranja, turquesa y violeta muy dominantes; requieren sombreado ambiental menos uniforme. No igualar colores de especies. |
| P1 | `duelista` | Figura amplia encapuchada: no convertirlo en rostro canónico inventado. Mantener anonimato. |
| P2 | `humano`, `gobernante`, `dara`, `jefe_arco`, `revancha`, `vampiro` | Revisar dureza de luces, fondo y agrupaciones frente a referencias; no rediseñar identidades ni vestuario gratuitamente. |
| P2 | `hombre_lobo`, `hombre_pantera` | Siluetas animales ya legibles; conservar hocicos y anatomía, afinar acabado sin humanizarlas. |

Las diez facciones continúan siendo Humanos, Orcos, Elfos, Goblins, Hombres Lobo,
Vampiros, Dragones, Elfos Nocturnos, Hombres Pantera y Hombres Lagarto.
Para una fase posterior consultar `facciones.py`, las aperturas de
`cinematicas.py` y `duelistas.py`: Aldric, Vorg, Lyra, Grix, Fenris, Condesa,
Ignarok, Sylwen, Zarkha y Sskar no son personajes intercambiables.

## 4. Tres propuestas de retratos — especificaciones, NO imágenes terminadas

No hay una herramienta de generación disponible con calidad de referencia
verificada. Se entregan briefs de producción; no se ejecutan modelos locales,
entrenamientos, filtros ni fusiones. Estado de los tres: **pendiente de imagen y
aprobación visual**. No hay candidatos nuevos que integrar.

### Nara — «La Cronista, atención contenida»

- Canon textual: mujer, cronista, libreta y tinta en los dedos; investiga y
  reconoce la procedencia extraña. Fuentes: `prologo.py:247–330`, informe de
  historia §1. No asignarle una facción, edad exacta o biografía nueva.
- Continuidad de diseño, tomada del retrato anterior: piel morena, ojos verdes,
  cabello oscuro recogido con trenzas, pendientes dorados, cuello claro,
  vestuario violeta con acentos turquesa/dorados. Estos son anclas visuales,
  no afirmaciones de canon textual.
- Ilustración independiente desde hombros, tres cuartos hacia la izquierda,
  rostro dominante; expresión atenta, entre curiosidad y cautela. La actividad
  de cronista se conserva por identidad/vestuario; no forzar manos o libreta
  dentro del busto. Sin escritorio ni biblioteca dentro del retrato.
- Luz principal cálida lateral discreta y relleno azul pizarra, sombras
  profundas legibles. Fondo simple oscuro, sin paisaje. Rostro trabajado en
  grupos de píxeles, no suavizado fotográfico. Conservar nariz, ojos y peinado
  reconocibles, evitando caricatura o rejuvenecimiento arbitrario.
- Entrega futura: `nara_candidata_v01.png`, 256×256; master independiente
  opcional. Validar en `nara[4]` y diálogo largo de `explicacion`.

### Pik — «La advertencia del bosque»

- Canon: goblin que encuentra al protagonista y advierte «No deberías tener
  eso». No está establecido como acompañante permanente.
  Fuente: `prologo.py:202–228`, informe de historia §1.
- Anclas del original: piel verde, orejas largas puntiagudas con interior
  cálido, nariz goblin, grandes ojos, mechón oscuro verdoso, chaleco marrón
  sobre camisa azul. No volverlo humano con orejas ni mezclarlo con Grix.
- Hombros y cabeza, tres cuartos leve; orejas completas sin cortarlas,
  rostro grande y gesto serio/desconfiado, boca cerrada. Conservar asimetrías
  características sin deformación anatómica.
- Luz difusa fría de lluvia, verdes oliva en sombra y reflejos contenidos;
  referencia cromática `camino_lluvioso.png`, sin recolorear ese fondo.
  Fondo sencillo azul gris oscuro, sin árboles dentro de su silueta.
- Entrega futura: `pik_candidato_v01.png`, 256×256. Validar en
  `despertar[10]`: ojos, nariz y advertencia deben leerse a 150×150.

### Juan Rajoy — «Respeto después del duelo»

- Canon: rival humano contemporáneo de la clasificatoria, aficionado al juego;
  no antagonista fantástico. Fuentes: `prologo.py:96–110,145–161`.
- Anclas del original: cabello castaño ondulado con raya, gafas rectangulares
  oscuras, piel clara, polo azul. Conservar forma facial y proporciones;
  no sustituirlo por un personaje público ni añadir armadura o insignias.
- Hombros hacia arriba, tres cuartos suave, mirada hacia interlocutor,
  pequeña sonrisa de reconocimiento. Gafas completas y ojos visibles;
  evitar brillos que los oculten.
- Luz cálida del recinto y relleno frío tenue; azules profundos del polo,
  piel natural, píxeles estructurados en mejillas y pelo. Fondo discreto
  azul pizarra, sin salón incrustado y sin dobles exposiciones.
- Entrega futura: `rajoy_candidato_v01.png`, 256×256. Validar en
  `post_duelo[0]` y en la interfaz del duelo usando el mismo recurso.

### Aprobación de los pilotos

Comparar original, activo actual y candidato **en columnas independientes**,
nunca superpuestos. Revisar a 256×256 y a 150×150: identidad reconocible,
anatomía, encuadre hombros/cabeza, detalle compatible con los seis fondos,
iluminación, legibilidad y ausencia de artefactos. No mezclar rostros,
especies, máscaras, transparencias o paisajes dentro de siluetas.
Solo tras aprobación se agregarán rutas nuevas y hashes, con los anteriores
preservados. No publicar un lote completo de avatares a partir de tres briefs.

## 5. Integración y validación efectuada

- Los seis recursos aprobados disponibles **ya estaban integrados**. No hay
  aprobados adicionales identificados que requieran importación.
- 81 escenas renderizadas con el reproductor pygame real en SDL dummy,
  guardado temporal aislado. No equivale a una partida manual completa.
- 73 pruebas existentes aprobadas: `test_arte_pixel_anime`, `test_assets`,
  `test_prologo`, `test_flujo_prologo`.
- 1199 archivos registrados/verificados, incluyendo originales, arte activo,
  fuentes runtime y archivos de las carpetas de cartas. Ninguna carta editada.
- El selector conserva prioridad de `fondo_hd`, fallback y viewport 1280×720
  sobre 1280×800. La prueba existente confirma presentación 1:1 sin deformación.
- Revisión de capturas: el panel permite leer los diálogos; Pik queda demasiado
  pequeño; la biblioteca del retrato Nara y el pixelado del campamento rompen
  coherencia; escenario y Umbral temprano requieren los recursos P0 descritos.
  No se certifica continuidad visual completa mientras falten esos recursos.

## 6. Capturas

`capturas_estado_actual/` contiene capturas nuevas, reales, del estado recibido,
incluyendo todos los pasos de escenario, revelación y apagón, más los tres
pilotos actuales y el camino/trono aprobados.

- `post_duelo_00.png`: Juan sobre salón aprobado.
- `despertar_10.png`: Pik sobre camino aprobado.
- `nara_04.png`: Nara actual sobre campamento local.
- `pre_duelo_03.png`: discontinuidad del escenario.
- `carta_umbral_06.png`: portal de piedra ajeno al recinto real.

**Escenas modificadas en esta entrega: ninguna.** Por eso no se presentan
capturas «antes/después» ficticias. Las comparativas de cambios quedan
pendientes de recibir, validar e integrar las imágenes definitivas.

Para repetir la verificación de integridad: ejecutar
`tools/consolidar_identidad_visual.py` con el Python del juego. La opción
`--capturas` vuelve a generar la evidencia del renderer, sin editar assets.
