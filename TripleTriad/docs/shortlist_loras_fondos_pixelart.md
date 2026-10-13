# Shortlist: LoRA para prueba de fondos anime pixel art

**Fecha de verificación/evaluación:** 13 de octubre de 2026. **Estado:** se descargaron los dos candidatos aprobados y se completó la comparación individual. Nunca se combinaron. No se entrenó nada ni se modificaron ComfyUI, el juego o sus recursos. Outputs exclusivamente internos, no autorizados para uso comercial.

## Decisión breve

Ambos LoRA son públicos, descargables sin tarifa indicada y utilizables localmente. Ambos son **SD 1.5**, no SDXL. La verificación del workspace separado `E:\AI\CartonesMazmorrasVisual` confirma que ya está disponible el checkpoint compatible `models\sd15\v1-5-pruned-emaonly.safetensors`, SHA-256 `6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa`, y existe entorno/script previamente probado. No descargar otro base. La descarga gratuita de un modelo no equivale a derechos despejados sobre sus datos de entrenamiento ni garantiza que el output esté libre de reclamaciones.

| Candidato (versión fijada) | Archivo exacto / tamaño publicado | Activador | Hash SHA-256 conocido | Licencia y condiciones relevantes |
|---|---|---|---|---|
| Anime Game Backgrounds — Kiktamo, `background_V2` (Civitai model 16151, version 19065) | `background_V2.safetensors`, fp16, 144.12 MB | No requiere activador; el autor indica que reemplaza/transforma fondos. | `E207974E5BEBC46870085429EF021A9DAF7D1498F45962282ECE9DD30F935F43` (AutoV2 corto: `E207974E5B`) | CreativeML Open RAIL-M con restricciones de uso (entre otras, usos ilegales/dañinos). No aparece prohibición comercial específica ni coste/licensingFee. Salidas: la licencia no reclama derechos sobre ellas, sujeto a ley y restricciones. Entrenado con 1,048 fondos de juegos (incluye Arknights, Blue Archive, Girls Frontline, Shadowverse y Neptunia); la licencia del LoRA no licencia esos datos fuente ni resuelve posibles derechos de terceros. |
| A to Zovya RPG Artist's Tools LoRA — Zovya, `V2 Art` (model 8951, version 44086) | `AZovyaRPGArtistToolsLORAV2art.safetensors`, fp16, 281.75 MB | `zrpgstyle` | `6879BBF56E5B8257A6FF1462938CE51415E0293D45E8549F3C545DCD05702703` (AutoV2 corto: `6879BBF56E`) | CreativeML Open RAIL-M + addendum Civitai. Permite output comercial en principio, pero **exige acreditar a Zovya** al usar/distribuir el modelo; prohíbe ofrecer el modelo como servicio de generación monetizado, vender/licenciar el LoRA o su Merge por valor. No usar Civitai Generate. Uso local para crear fondos de un juego comercial no es en sí un servicio de generación: revisar términos si el juego/flujo se convierte en servicio o se redistribuyen los pesos. La licencia no da garantía sobre derechos del material de entrenamiento. |

En ambos casos Civitai informa `usageControl: Download`, `licensingFee: null`, estado público y SafeTensor. Se descargaron gratuitamente desde los endpoints de versión fijados y los SHA-256 calculados localmente coinciden con los metadatos publicados. Manifiesto y archivos aislados: `E:\AI\CartonesMazmorrasVisual\models\loras_pretrained\shortlist_20261013\`.

## Compatibilidad y límites

- Ambos son LoRA SD 1.5. No cargarlos sobre checkpoints SDXL. El checkpoint SD 1.5 local reutilizado fue `E:\AI\CartonesMazmorrasVisual\models\sd15\v1-5-pruned-emaonly.safetensors`, SHA-256 `6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa`.
- Los dos pasaron el preflight de compatibilidad con el checkpoint en CPU: cero claves faltantes/inesperadas. Se aplicó solo el LoRA indicado en su propia corrida; no se combinaron.
- Kiktamo está específicamente entrenado con fondos y excluyó casi todas las personas (salvo alguna multitud), por lo que es el candidato más directo para escenarios sin personajes. No es específicamente pixel art: puede dar ilustración anime convencional, detalles finos, composición influida por fondos comerciales del dataset o crowds ocasionales. Su ficha muestra ejemplos/prompting mayormente 768×512, así que 640×360 es una evaluación de adaptación, no el formato de entrenamiento demostrado.
- Zovya cubre RPG/fantasía (paisajes, ruinas y castillos) pero también personajes/monstruos; su sesgo de fantasía puede introducir medievalismo en el salón moderno. El ejemplo/versionado está asociado con un checkpoint de estilo pictórico, pero es un LoRA y su salida depende del checkpoint SD1.5 elegido. Tampoco es un LoRA dedicado a pixel art ni a fondos sin sujetos; necesita negativos fuertes y revisión de intrusiones humanas.
- **PixelArtRedmond** queda para una segunda etapa, no descargarlo ni incluirlo en esta matriz.

## Diseño fijado para la evaluación (máximo 12 imágenes)

Diseño de **4 condiciones × 3 escenarios × 1 semilla = 12 imágenes**: base y LoRA para cada candidato. Cada LoRA se genera por separado, nunca apilado. Se usa un control base propio por pareja para conservar idéntico el texto de entrada, incluido `zrpgstyle` en ambos brazos de Zovya. Semilla correspondiente igual en control y LoRA.

**Parámetros ejecutados:** 640×360, batch 1, sampler `euler_a`, 25 pasos, CFG 7.0, semillas `101`, `202`, `303`, sin refiner, hires fix, upscale, ControlNet, IP-Adapter, postproceso ni segundo LoRA. Peso fijo: Kiktamo `0.7`; Zovya `0.6`. Mismo checkpoint SD1.5 en las 12 salidas.

**Negativo común:** `person, people, human, character, portrait, crowd, figure, silhouette, face, hands, text, letters, logo, watermark, UI, frame, border, photorealistic, 3d render, smooth gradients, blurry, low detail, cluttered foreground`.

### Resultado ejecutado

Se generaron **12 imágenes** (3 escenas × 4 condiciones: base/Kiktamo prompt, Kiktamo, base/Zovya prompt, Zovya). Una semilla por escena, compartida dentro de cada pareja: 101/202/303. Parámetros efectivos: 640×360, 25 pasos, `euler_a`, CFG 7, fp16, VAE fp32, SDPA; Kiktamo peso 0.7 y Zovya 0.6. En el control de Zovya se conservó `zrpgstyle` para igualar el texto de la pareja. Las solicitudes de generación estuvieron monitorizadas con parada a VRAM usada ≥5,632 MiB.

| Condición | Pico VRAM usado | Estado |
|---|---:|---|
| Base con prompts Kiktamo | 4,999 MiB | OK |
| Kiktamo 0.7 | 5,271 MiB | OK |
| Base con prompts Zovya | 5,097 MiB | OK |
| Zovya 0.6 | 5,391 MiB | OK; 241 MiB por debajo del umbral |

**Lectura visual breve:** Kiktamo cambia claramente la imagen en las tres parejas; destaca la influencia de fondo, pero el salón deriva en bandas/filas repetitivas y la sala del trono en un interior estrecho/corridor. El bosque conserva una composición legible, aunque no queda convertido en pixel art nítido. Zovya produce una sala moderna más pictórica/realista que pixel art; bosque y trono ganan detalle arquitectónico, pero se alejan también del pixel art de píxel agrupado. En general, el checkpoint SD 1.5 base sin LoRA tampoco logró la estética pixel art del brief. No aparece un candidato ganador que cumpla el objetivo completo; Kiktamo parece más adecuado a fondos puros, mientras Zovya tiende a render pictórico.

**Limitación de control:** el log de Zovya advirtió truncamiento de prompt solo en el primer escenario (78 tokens frente a máximo 77). La misma línea truncada se usó en su control base y LoRA, así que la pareja sigue emparejada, pero se debe tener en cuenta al juzgar salón contemporáneo. No se excedió el límite para corregirlo.

Resultados, hoja comparativa, métricas por píxel y registro GPU: `E:\AI\CartonesMazmorrasVisual\evals\shortlist_lora_eval_20261013\` (`comparison_sheet.png`, `difference_metrics.json`, `run_report.json`, `model_manifest.json`). Las diferencias numéricas confirman que los adaptadores modifican outputs; no son una métrica de calidad.

### Prompts por escena

1. **Salón contemporáneo de torneo de cartas — mundo real, cero medieval.** Componer como plano general horizontal de un salón moderno de torneo: mesas largas de juego con tapetes y sillas vacías, escenario pequeño al fondo, focos de evento, arquitectura contemporánea, paneles de vidrio y estructura metálica; sin cartas legibles ni marcas, sin público ni participantes. Paleta cálida y ambiente de evento real actual. Encuadre amplio 16:9, líneas de fuga hacia el escenario, zona inferior relativamente despejada. Estética anime pixel art, píxeles nítidos y agrupados, paleta limitada, sin filtros CRT.
   - **Kiktamo:** `wide empty contemporary real-world trading card tournament hall, modern convention venue, long gaming tables with playmats and empty chairs, small event stage in the distance, glass walls, steel trusses, event spotlights, warm indoor lighting, no fantasy, no medieval architecture, no readable cards, no logos, no people, wide establishing shot, 16:9 landscape composition, clear lower foreground, anime pixel art background, crisp clustered pixels, limited palette, clean pixel clusters`
   - **Zovya:** `zrpgstyle, empty contemporary real-world trading card tournament hall, unmistakably modern convention center, long gaming tables with playmats and empty chairs, small event stage in the distance, glass walls, steel trusses, modern event spotlights, warm indoor lighting, no fantasy, no medieval architecture, no weapons, no readable cards, no logos, no people, wide establishing shot, 16:9 landscape composition, clear lower foreground, anime pixel art background, crisp clustered pixels, limited palette, clean pixel clusters`
2. **Bosque lluvioso de fantasía medieval oscura.** `wide establishing view of a dark medieval fantasy forest in steady rain, ancient dense trees, wet mossy path leading into layered depth, distant ruined stone arch barely visible through mist, rain streaks and reflective puddles, muted deep greens and cold blue-grey light, no buildings in foreground, no people, no creatures, no weapons, horizontal 16:9 composition, clear lower foreground, anime pixel art background, crisp clustered pixels, limited palette, clean pixel clusters, no CRT effects`. En Zovya anteponer `zrpgstyle,`.
3. **Sala del trono monumental de fantasía oscura.** `wide symmetrical establishing view inside a monumental dark fantasy throne hall, immense stone pillars and high vaulted ceiling, long central aisle leading to a distant imposing empty throne, restrained iron details, banners without symbols or writing, dim cold window light with a few warm braziers, dramatic depth, no people, no guards, no creatures, no weapons in foreground, horizontal 16:9 composition, clear lower foreground, anime pixel art background, crisp clustered pixels, limited palette, clean pixel clusters, no CRT effects`. En Zovya anteponer `zrpgstyle,`.

Para la primera escena, agregar explícitamente `no fantasy, no medieval` también al negativo (sin retirar términos del negativo común), para que el control semántico de mundo real sea estricto. Prompts fuente en inglés para reducir diferencias de tokenización entre checkpoints SD1.5.

## VRAM y puerta previa a cualquier ejecución

La ejecución medida para SD1.5 a 640×360, batch 1 y 25 pasos alcanzó entre 4,999 y 5,391 MiB usados. Esto confirma el margen reducido de la RTX 2060 6 GiB; para esta tanda no se activó el límite de parada de 5,632 MiB y no hubo OOM.

La lectura preliminar antes de preparar la corrida fue 4,686 MiB libres; el preflight inmediato registrado en `run_report.json` fue 4,510 MiB libres. Las cuatro corridas terminaron sin OOM ni parada de VRAM. No se alteró ComfyUI.

## Fuentes consultadas

- [Anime Game Backgrounds — ficha Civitai](https://civitai.com/models/16151/anime-game-backgrounds) · [versión 19065 (API: archivo, base, control de descarga y hashes)](https://civitai.com/api/v1/model-versions/19065) · [licencia/addendum](https://civitai.com/models/license/19065)
- [A to Zovya RPG Artist's Tools LoRA — ficha Civitai](https://civitai.com/models/8951/a-to-zovya-rpg-artists-tools-lora) · [versión 44086 (API)](https://civitai.com/api/v1/model-versions/44086) · [licencia/addendum, incluidas obligaciones comerciales](https://civitai.com/models/license/44086)
- Inventario local documentado: [`E:\AI\README_COMFYUI.md`](../../../../AI/README_COMFYUI.md), [`preparacion_visual_lora_y_cinematicas.md`](preparacion_visual_lora_y_cinematicas.md) y [`evaluacion_entrenamiento_lora_6gb.md`](evaluacion_entrenamiento_lora_6gb.md).

**Conclusión:** selección cerrada y evaluación visual completada. Kiktamo es el más pertinente para iterar fondos; Zovya es alternativa para interiores de fantasía no pixelados. Ninguno queda aprobado para integrar: falta alcanzar el estilo pixel art pedido y revisar derechos de outputs/datos antes de cualquier uso fuera de evaluación interna. PixelArtRedmond permanece como posible etapa posterior, no descargado.
