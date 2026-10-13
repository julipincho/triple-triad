# Cartones y Mazmorras — informe de historia y cinemáticas

**Alcance:** auditoría estática del código, datos, documentación y archivos de arte existentes. No se ejecutó el juego, no se modificaron assets/código ni se usó GPU. Las dimensiones se leyeron de los PNG en disco. Este informe describe el estado encontrado, no propone diseños de arte.

## Resumen ejecutivo

La historia de prólogo e isekai está implementada: un duelista anónimo gana una clasificatoria de Cartones y Mazmorras, presencia la apertura de una carta/Umbral y despierta en el mundo que creyó ficticio. Nara le explica que debe ganar cinco duelos y el trono para regresar. La campaña ofrece una rama, dos decisiones morales acotadas, relación variable con Nara y tres desenlaces. Un ciclo posterior de diez facciones revela al Maestro de la Mesa y desbloquea un duelo secreto.

Las cinemáticas son secuencias de datos consumidas por un reproductor común. El fondo se elige por clave y se dibuja aparte de texto y retrato; los fondos usados son PNG de 512×256 y los retratos de avatar son PNG de 256×256 (se muestran a 150×150). Por tanto, sustituir únicamente el arte de fondo es técnicamente viable sin tocar guion, retratos, eventos ni flujo, siempre que se mantengan las claves/rutas y proporciones compatibles. Hay desajustes narrativo-visuales ya observables: los epílogos que dicen ocurrir en el salón real usan `campamento`, y varios episodios del prólogo reutilizan un mismo bosque/camino o el escenario del torneo.

## 1. Historia del juego

### Premisa e inicio

- **Protagonista:** “el duelista”, avatar del jugador, anónimo por intención. El nombre introducido al iniciar puede insertarse en algunos textos; no se fija biografía, edad ni apariencia canónica. Se representa por `assets/avatar_duelista.png` cuando hay hablante explícito; buena parte del prólogo es narración en segunda persona. [ `prologo.py` líneas 15–24, 82–96; `main.py` 168–181; `cinematicas.py` 376–397; `estilo/escenas.json` 69–73 ]
- **Situación inicial:** participa en la última ronda clasificatoria de un torneo real de Cartones y Mazmorras contra Juan Rajoy. Lleva cinco legendarias (una de humano, elfo, vampiro, dragón y goblin); el tutorial es el duelo y no una lección separada. [ `prologo.py` 38–45, 87–128; `main.py` 102–143 ]
- **Cruce isekai:** los organizadores presentan una carta sin facción llamada “El Umbral”. Los símbolos remiten a cartas antiguas; aparece brevemente una figura en un trono, sobreviene un apagón y el protagonista despierta en bosque lluvioso, sin señal telefónica, con sus cartas intactas. **La causa última de la selección/transporte no se explica en el prólogo.** [ `prologo.py` 148–202 ]
- **Mundo de llegada:** mundo de fantasía oscura con ceniza, diez facciones enfrentadas en una “guerra con reglas de duelo”, Juicio como nombre local de las cartas y un Umbral vinculado al trono. Las cartas parecen anticipar o reflejar una realidad que no coincide plenamente con los libros locales. [ `prologo.py` 244–305; `narrativa.py` 183–290; `fragmentos.py` 27–106 ]
- **Objetivo inmediato:** volver a casa. Nara dice que el Umbral ya estaba allí, lo abre una persona y lo guarda quien ocupa el trono; se requieren cinco duelos, con el último en el trono. Perder un duelo permite reintentar. La sangre de dragón legitimó históricamente el trono, pero el guardián actual es quien ganó el último Juicio, no necesariamente un dragón. [ `prologo.py` 244–305 ]

### Conflicto, personajes y facciones

- **Nara, la Cronista:** reconoce que las cartas vienen “de otro lado”, investiga quién las escribió y acompaña al protagonista. La confianza cambia algunos diálogos y su actitud; antes del duelo del trono confiesa que el protagonista dejó de ser solo un dato. [ `prologo.py` 221–305; `narrativa.py` 150–176, 346–386 ]
- **Pik:** goblin que encuentra primero al protagonista y advierte que no debería poseer esas cartas. No está establecido como acompañante permanente. [ `prologo.py` 183–202 ]
- **Juan Rajoy:** rival humano de la clasificatoria en el mundo real; no es el antagonista de la campaña. [ `prologo.py` 82–96 ]
- **Antagonistas:** dependen de la facción elegida; el jefe final es una facción/personaje rival. Ejemplos: Ignarok contra humanos/goblins/elfos/elfos nocturnos; Lyra contra orcos; la Condesa contra hombres lobo; Fenris contra vampiros/panteras; Vorg contra hombres lagarto; Aldric contra dragones. [ `facciones.py` 17–127 ]
- **Diez facciones:** humanos, orcos, elfos, goblins, hombres lobo, vampiros, dragones, elfos nocturnos, hombres pantera y hombres lagarto. Cada una tiene arco y rival final; la elección altera rival y color del final, no el esqueleto de cinco duelos. [ `facciones.py`; `README.md` 50–67 ]
- **Maestro de la Mesa / Cartógrafo:** autor de las cartas, ajeno a las facciones. El trasfondo dice que el duelista fue seleccionado, pero ese dato se revela en el contenido de la campaña secreta, no en el prólogo. Quiere que el Umbral no se cierre y que la historia termine de leerse. [ `fragmentos.py` 119–167 ]

### Progresión implementada

1. **Intro opcional de primera visita:** cuenta la aparición del Umbral y el paso del juego a la guerra. [ `cinematicas.py` 592–609; `main.py` 520–529 ]
2. **Prólogo en el mundo real:** clasificatoria/tutorial; encuentro con la carta-Umbral; apagón/transporte; despertar, Pik, amenaza de una persona de la aldea y encuentro con Nara; explicación y selección de facción. El duelo tutorial debe ganarse para seguir, con reintento o salida. [ `prologo.py`; `main.py` 102–165, 168–197 ]
3. **Campaña principal:** cinco duelos: `senda` → elección `aldea` o `ruinas` → `fortaleza` → `asalto` → `trono`. La rama converge. Cada nodo tiene previa/posterior y rivales determinados por el estado y la facción. [ `campana.py` 172–241; `main.py` 333–447 ]
4. **Decisiones:** en `senda`, ayudar o ignorar a un herido; en `fortaleza`, permitir o no que el capitán examine una carta. Cambian confianza/conocimiento/revelación, no la ruta de cinco duelos. También existen encuentros aleatorios con dos opciones y efectos de juego. [ `narrativa.py` 89–143; `encuentros.py`; `main.py` 378–381, 433–435 ]
5. **Final principal:** cada una de diez facciones posee resultados de campaña para dominio/equilibrio/caos; se complementan con tres variantes comunes del Umbral y tres epílogos de regreso al mundo real. [ `campana.py` 423 en adelante; `finales.py` 44–180; `pantallas.py` 3236–3263 ]
6. **Contenido posterior:** mini-campañas de tres duelos para elfo nocturno, hombre pantera y hombre lagarto; al completar campañas de facción se obtiene un fragmento. Los diez fragmentos desbloquean al Cartógrafo y su duelo secreto. [ `campana.py` 243–289; `fragmentos.py` 27–240; `main.py` 200–266, 269–324 ]

### Finales y estado de definición

Los tres resultados son **dominio** (forzar el Umbral; algo cruza y aparece una carta con el rostro del protagonista), **equilibrio** (abrir lo justo, regreso casi imperceptible y Nara en una expansión nueva) y **caos** (se mezclan ambos mundos en el salón y una carta se mueve). Los finales de facción describen consecuencias políticas locales; no equivalen por sí solos a estos epílogos. [ `finales.py` 48–141; `campana.py` 423 en adelante ]

| Estado | Elementos |
|---|---|
| **Implementado en código** | Prólogo jugable, diálogo de Nara, selección de facción, grafo de campaña, rama, decisiones indicadas, encuentros, confianza, finales, mini-campañas, fragmentos, desbloqueo y duelo del Cartógrafo. |
| **Documentado como intención/diseño** | Biblia/cronología referida por comentarios de `prologo.py`; comentarios de `narrativa.py` y `finales.py` describen la intención de arcos, revelación progresiva y tres finales. El comentario acredita intención; no es evidencia de una biblia externa completa disponible. |
| **No definido o no aclarado por los archivos revisados** | Biografía/cuerpo del protagonista, mecanismo concreto que lo selecciona y activa la carta, identidad de la figura que aparece fugazmente antes del transporte, reglas físicas completas del otro mundo, consecuencias mecánicas exactas de volver en cada final, y destino posterior del protagonista/Nara más allá del texto mostrado. No completar estos huecos por inferencia. |
| **Inconsistencia/pendiente de continuidad** | El prólogo afirma que son cinco duelos y que ganar el trono devuelve a casa; la campaña final agrega tres maneras de abrir/romper el Umbral y epílogos con repercusiones. Es contenido implementado, pero las reglas completas de elección de variante y su relación causal con la victoria no están explicadas en las escenas citadas. |

## 2. Cinemáticas y escenas narrativas existentes

No hay un inventario de una sola lista cerrada: el motor arma secuencias en tiempo de ejecución desde productores distintos. La siguiente tabla cubre las familias de secuencias/cortes narrativos y sus puntos de entrada. Las cinemáticas de nodo varían con facción, rival, resultado, decisiones, confianza y encuentros; por eso no existe un único diálogo por instancia.

| ID/familia | Cuándo y qué ocurre | Personajes / fondo y recursos | Textos, efectos y estado |
|---|---|---|---|
| `intro` | Tras portada, una vez por perfil; historia condensada del Umbral. | Sin retratos. `amanecer` → `umbral` → `estandartes` → `trono`. | Cinco escenas en `cinematicas.py` 592–609. Título, cambios de fondo, música; implementada y saltable. |
| `prologo_pre_duelo` | Nueva campaña, tras nombre; presentación de torneo y clasificatoria. | Narrador, Presentador/avatar; `salon`, `escenario`, `publico`. Avatares `avatar_presentador.png`, y Juan luego `avatar_rajoy.png`. | `prologo.py` 110–128; previo al duelo real contra Juan. |
| `prologo_post_duelo + carta_umbral` | Después de ganar la clasificatoria; carta, símbolos, trono y apagón. | Juan, Presentador y narración; `salon`, `escenario`, `umbral`; avatares `avatar_rajoy.png`, `avatar_presentador.png`. | `prologo.py` 131–170. Títulos “EL UMBRAL”, “LAS NUEVE CASILLAS”; implementada. |
| `transporte` | Instante del cruce. | Sin retratos; `apagon`. | Tres escenas, una de texto vacío usada como corte/título; `prologo.py` 173–180. |
| `despertar` | Primeros momentos en el mundo de juego. | Protagonista narrado, Pik; `camino` (la clave puede resolver variante lluvia/niebla/etc.); `avatar_pik.png`, `avatar_duelista.png` según hablante. | Bosque/lluvia, mochila/teléfono, torre conocida y cartas; `prologo.py` 183–202. |
| `encuentro_hostil` | Tras salir del primer encuentro con Pik, alguien de la aldea ve las cartas. | Protagonista y “Alguien Te Ha Visto”; `camino`; avatar de encuentro `assets/escenas/hostil.png`. | `prologo.py` 205–218. Amenaza y salida; fondo repetido respecto al despertar. |
| `nara + explicacion + cierre` | Después del encuentro hostil, antes de elegir facción; presenta reglas del Umbral y motivo para luchar. | Protagonista/Nara; `campamento` y cierre `umbral`/`trono`; `avatar_nara.png`. | Secuencia extensa en `prologo.py` 221–320; se llama sin permitir salto (`main.py` 160–164). |
| `apertura_<facción>` (10 variantes) | Inicio de cada campaña, antes del mapa/primer duelo. Arco local, líder, motivo/pacto y relevo. | Líder/avatar de facción; fondos entre `ceniza`, `campamento`, `ruinas`, `asalto`, `trono`, `umbral`, `estandartes`. | `cinematicas.py` 439–589 + `peticiones.py`; 4 escenas base, se incorporan petición y ayuda. Implementadas. Algunas aperturas sin `fondo` explícito usan `ceniza` por defecto. |
| `nodo_<facción>_<nodo>` | Antes de cada duelo de campaña/mini-campaña. Previa de nodo, presentación/reacción del rival y diálogo de rol. | NPC/rival con avatar correspondiente; fondo de `campana.NODOS[nodo].escena`: camino, aldea, ruinas, fortaleza, asalto, trono; mini: umbral/estandartes/trono. | `cinematicas.py` 612–651, `campana.py` 172–269, `duelistas.py`. Títulos/texto y máquina de escribir; saltable. |
| `posterior_<facción>_<nodo>` / derrota | Tras cada duelo. Victoria revela consecuencia/misterio; derrota expresa reintento. | Rival, Nara; mismo fondo del nodo y avatares del hablante. | `narrativa.py` 183–290 + `duelistas.py`; `cinematicas.py` 654–681. Implementadas, diálogos condicionales. |
| `amistad_nara` | Una vez antes del duelo final del trono. Nara deja de ser guía y decide acompañar. | Nara/protagonista; `camino`; `avatar_nara.png`. | 12 escenas (`narrativa.py` 352–386); no saltable por configuración de `main.py` 382–392. |
| Final de campaña / `escenas_final` | Al completar campaña o mini-campaña. Título + líneas del resultado. | Sin retratos explícitos; `trono` en final común; mini usa también `trono`. | Constructor genérico en `cinematicas.py` 684–691; textos de facción en `campana.py`, epílogo en `finales.py`. |
| `umbral_<variante>` | Resolución de dominio/equilibrio/caos, antes del epílogo. | Sin retratos; `umbral`. | `finales.py` 48–79, 164–171; título y 4 líneas por variante; implementada. |
| `epilogo_<variante>` | Regreso al mundo real después del Umbral. | Sin retratos; declarado `mundo="real"`, pero **fondo `campamento` para las tres variantes**. | `finales.py` 86–180. Textos difieren por variante; implementado, con posible discordancia visual notable. |
| `encuentro_<id>` | Ocasionalmente entre victorias y próximo duelo; conversación con NPC, reacción al mazo, opción y efecto. | Mercader, anciano, hermandad, caravana u hostil; escena/fondo por encuentro; retratos en `assets/escenas/*.png` (512×384) para varios NPC. | `encuentros.py` 258–280 y continuaciones; `pantallas.py` escena/opciones. No todos los encuentros son cinemática completa del motor, pero algunos preámbulos sí usan `cinematicas.reproducir`. |
| `fragmento` / desbloqueo Cartógrafo | Al completar una facción por primera vez; con 10/10, revela y abre duelo secreto. | Sin retrato; `umbral`; avatar del Maestro no existe como `avatar_cartografo.png`. | `fragmentos.py` 32–116, 213–240; el duelo aparece en `main.py` 200–266. El texto secreto se presenta como cartel y duelo además de escena de desbloqueo. |

**Avatares disponibles:** `assets/avatar_*.png` incluye duelista, Nara, Pik, Juan Rajoy, Presentador, Gobernante y los diez tipos/facciones indicados por el motor. El repertorio de retratos de encuentro vive en `assets/escenas/` y se escala igualmente a 150×150. No se requiere modificar esos recursos para cambiar fondos. [ `cinematicas.py` 306–324, 361–397; `assets/` ]

## 3. Sistema técnico

1. **Dibujo:** `Cinematica._dibujar` blitea fondo a pantalla lógica de 1280×800, añade tratamiento por mundo y luego título o caja de diálogo/retrato. La UI cachea superficies escaladas y capas. [ `cinematicas.py` 239–254; `ui.py` 402–448 ]
2. **Carga de fondos:** la clave `fondo` se resuelve con `ui.ruta_fondo(nombre)` y `REC.fondo_pantalla`. Hay variantes por semilla para parte de los fondos; las escenas de prólogo real usan `mundo=real`. [ `cinematicas.py` 243–248; `main.py` 336–343; `ui.py` ]
3. **Avatares:** `retrato` se elige explícitamente o por hablante; ruta `assets/avatar_<clave>.png`, o `assets/escenas/<clave>.png` para `encuentro:`. Carga a 150×150. [ `cinematicas.py` 306–324, 376–397 ]
4. **Diálogo:** cada escena lleva texto, hablante, color, efecto, música, mundo y fondo. Texto en panel opaco; máquina de escribir a 44 caracteres/s; título tiene aparición gradual. El nombre `__JUGADOR__` se resuelve al construir la secuencia. [ `cinematicas.py` 45–70, 98–105, 281–305 ]
5. **Avance:** ENTER/ESPACIO o clic avanza; clic puede completar el texto antes de avanzar; ESC salta si la secuencia permite saltar o terminó la escena. Existe opción de saltar toda la cinemática o mostrar texto instantáneo. [ `cinematicas.py` 145–216; `opciones.py` ]
6. **Formatos:** fondos, avatares y retratos verificados en PNG. Fondos 512×256; avatares 256×256; ilustraciones de encuentro 512×384. [ archivos en `assets/fondos/`, `assets/avatar_*.png`, `assets/escenas/`; tamaños leídos en disco ]
7. **Reemplazo sin tocar lógica:** cambiar el PNG que corresponde a una clave en `assets/fondos/`, conservando nombre, formato, proporción/dimensiones esperadas y ausencia de personajes incrustados, deja intactos datos de escena, retratos, textos, eventos, avances y bifurcaciones. La caché se llena desde esos paths al cargar. Si se desea otro nombre, ya requeriría cambiar datos/configuración; no es necesario para una revisión de arte. Los fondos no son capas separadas por evento dentro de una misma imagen; cada escena escoge una clave.

## 4. Inventario visual de fondos

Todos los PNG de fondo listados abajo son **512×256**. El renderer los escala sin deformarlos y puede dejar letterbox; la pantalla lógica es 1280×800. “Problema” identifica oportunidad/desajuste observable en código o significado del fondo, no evaluación estética del PNG.

| Cinemática / uso | Escenario actual | Qué representa narrativamente | Recurso | Dimensiones | Posibles problemas visuales | Prioridad |
|---|---|---|---|---|---|---|
| Prólogo torneo | Salón, escenario, público | Torneo moderno del mundo real y clasificatoria | `assets/fondos/salon.png`, `escenario.png`, `publico.png` | 512×256 c/u | Deben leerse como un mismo recinto y diferenciarse entre planos; otras escenas reutilizan escenario genérico. | Alta |
| Presentación del Umbral | Salón/escenario/umbral | Carta presentada, puerta y trono que aparecen en la visión | `salon.png`, `escenario.png`, `umbral.png` | 512×256 c/u | El texto describe una visión dentro del salón; los cambios de locación pueden sugerir teletransporte literal. | Alta |
| Apagón y cruce | Apagón | Última imagen del mundo real antes de despertar | `assets/fondos/apagon.png` | 512×256 | Recurso único; continuidad temporal importante, transición narrada pero no animada entre mundos. | Alta |
| Despertar + amenaza | Camino (puede variar según variante de campaña) | Bosque lluvioso, torre conocida y amenaza de aldea | `assets/fondos/camino*.png` | 512×256 c/u | La clave camino se comparte para lluvia, torre, Pik y amenaza; el guion nombra lluvia, por lo que otras variantes pueden contradecirlo. | Alta |
| Encuentro de Nara y explicación | Campamento | Encuentro/charla de Nara; Nara es personaje de campamento, el fondo es común a varias escenas | `assets/fondos/campamento*.png` | 512×256 c/u | Escenas largas con la misma clave; variantes climáticas pueden introducir cambios no dictados por el diálogo. | Media |
| Cierre prólogo | Umbral y trono | Relevo hacia elección de facción | `umbral.png`, `trono.png` | 512×256 c/u | El título de selección usa trono antes de entrar al mundo narrativo de campaña; posible uso simbólico. | Baja |
| Intro | Amanecer, Umbral, estandartes, trono | Mundo antes de la ceniza, grieta y guerra de facciones | `amanecer.png`, `umbral.png`, `estandartes.png`, `trono.png` | 512×256 c/u | Secuencia representativa y de alta exposición; hay cambios de fondo por frase, sin animación de cámara. | Alta |
| Aperturas de facción | Ceniza/campamento/ruinas/asalto/trono/umbral/estandartes | Crisis/territorio del bando y su líder | claves en `cinematicas.py` 439–558; PNG bajo `assets/fondos/` | 512×256 c/u | Human/elfo usan `ceniza` por omisión, no un escenario inequívoco de reino/ bosque; algunas escenas finales heredan una sola clave. | Alta |
| Campaña: senda | Camino | Camino de ceniza y herido | `assets/fondos/camino*.png` | 512×256 | Variantes pueden no representar ceniza/herido; clave compartida con prólogo. | Media |
| Campaña: aldea | Aldea | Aldea amurallada y custodios | `assets/fondos/aldea.png` | 512×256 | Fondo único para previa/posterior; no hay cambio de plano entre escenas. | Media |
| Campaña: ruinas | Ruinas | Ciudad enterrada bajo ceniza, cartel/carta | `assets/fondos/ruinas*.png` | 512×256 c/u | Variantes del sitio; texto alude a ciudad intacta/desierta y carta en pared, que deben ser legibles como el mismo lugar. | Media |
| Campaña: fortaleza | Fortaleza | Paso militar que controla el acceso al trono | `assets/fondos/fortaleza.png` | 512×256 | El capitán/camino y el interior posterior se sirven con la misma clave de escena. | Alta |
| Campaña: asalto | Asalto | Revancha/asalto y camino antes del trono | `assets/fondos/asalto*.png` | 512×256 c/u | Narrativa de rival que vuelve y heridas; las variantes amanecer/noche pueden alterar mucho el tono. | Alta |
| Campaña: trono y cierre | Trono | Grieta, trono y duelo final | `assets/fondos/trono*.png` | 512×256 c/u | Es fondo de previa, victoria y final; debe sostener contextos de confrontación y cierre distintos. | Alta |
| Resolución del Umbral | Umbral | Apertura/rotura según variante | `assets/fondos/umbral*.png` | 512×256 c/u | Tres acontecimientos distintos comparten clave; el código no interpola la transformación visual. | Alta |
| Epílogos (todas las variantes) | **Campamento** | Salón del torneo del mundo real, regreso y consecuencias | `assets/fondos/campamento*.png` | 512×256 c/u | **Desajuste directo:** entorno de fantasía usado en escena marcada como mundo real; oportunidad más clara para corregir solo fondo. | Muy alta |
| Mini-campaña | Umbral/estandartes/trono | Desafíos de Elfos Nocturnos, Panteras y Lagartos | `assets/fondos/umbral*.png`, `estandartes.png`, `trono*.png` | 512×256 c/u | Fondos compartidos con campaña principal; guiones de mini finales no identifican un escenario específico. | Media |
| Encuentros | Según `escena_encuentro` | Mercader, anciano, hermandad, caravana, hostil | `assets/fondos/` + `assets/escenas/{mercader,anciano,hermandad,caravana,hostil}.png` | Fondo 512×256; retrato 512×384 | Las imágenes `assets/escenas` son retratos/ilustraciones, no fondos panorámicos; no confundir al revisar inventario. | Media |
| Desbloqueo Cartógrafo | Umbral | Alguien espera al otro lado | `assets/fondos/umbral.png` | 512×256 | No existe avatar del Cartógrafo en `assets/avatar_*.png`; sus escenas no muestran retrato. | Media |

## 5. Recomendación: primeras tres revisiones

1. **Epílogos (`finales.py`, fondo `campamento`)** — máxima prioridad: es el retorno al mundo real y el desajuste con el fondo de fantasía está confirmado en datos. Se puede corregir reemplazando el fondo apuntado por la clave, sin alterar escenas, textos ni avatares. Como esa clave también aparece en otras partes, para preservar allí su imagen actual conviene evaluar una clave distinta; eso ya exigiría un pequeño cambio de datos, por lo que la modalidad estricta de “solo reemplazar imágenes” depende de aceptar el cambio global del campamento.
2. **Prólogo: torneo y cruce** — define visualmente la premisa isekai y el contraste de mundos, se ve antes de la campaña y usa claves locales (`salon`, `escenario`, `publico`, `apagon`). Cada PNG se puede reemplazar conservando identificadores y el retrato de Juan/Presentador. Importancia narrativa alta y cambios de escenario muy aislados.
3. **Despertar/amenaza (`camino`)** — primer establecimiento del mundo de juego y sus reglas; reutiliza fondo de camino tanto en prólogo como en nodos. Fácil de sustituir a nivel de imagen, pero existe riesgo de cambiar la apariencia de varias escenas de campaña y de que variantes climáticas no concuerden con la frase fija “Lluvia”. Revisar esta colisión antes de reemplazar la clave.

**Alternativa de bajo riesgo para revisión solo de imágenes:** `apagon.png` o `amanecer.png`, por ser recursos más acotados y con uso reconocible; tienen menos impacto narrativo que las tres anteriores.

## Referencias principales

- Prólogo y diálogos: `prologo.py`; secuencia y disparadores: `main.py`.
- Motor y composición de cinemáticas: `cinematicas.py`; escalado/cache: `ui.py`; rutas: `paths.py`.
- Campaña, nodos, finales de facción: `campana.py`; facciones y jefes: `facciones.py`; diálogos de rival: `duelistas.py`.
- Arcos, decisiones y confianza: `narrativa.py`; tres cierres: `finales.py`; misterio posterior: `fragmentos.py`.
- Encuentros: `encuentros.py` y `pantallas.py`.
- Guía de arte existente: `estilo/escenas.json`; catálogo/generación declarativa de fondos: `generar_escenas.py`; descripción de uso y limitaciones de recursos: `assets_manifiesto.py` (este manifiesto puede no coincidir con el estado actual de todos los archivos; verificar disco antes de usar sus listas como fuente de inventario).
- Inventario físico verificado: `assets/fondos/*.png`, `assets/avatar_*.png`, `assets/escenas/*.png`.
