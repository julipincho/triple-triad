# Preparación visual: LoRA de escenarios y cinemáticas 16:9

**Estado:** análisis/preparación solamente. No se entrenó ni generó nada, no se descargaron/instalaron modelos y no se modificó código funcional ni fondos existentes. La Biblia aportada se conserva completa en [`biblia_visual_maestra_v1.md`](biblia_visual_maestra_v1.md).

## Conclusiones ejecutivas

- Ya existe flujo local de **inferencia SDXL con ComfyUI**, varios checkpoints y scripts propios de producción de arte. Eso no equivale a tener entrenamiento LoRA listo.
- Hardware real verificado por `nvidia-smi`: **NVIDIA GeForce RTX 2060, 6 GB VRAM**. En la consulta había aproximadamente 1.1 GiB en uso y 5.0 GiB disponibles; eso es una medición instantánea y no una garantía de memoria libre durante otro proceso. No hay 32 GB de VRAM.
- No se encontró una herramienta/repositorio de entrenamiento LoRA SDXL instalado. En `.sd_env` hay Diffusers/Accelerate pero faltan PEFT, bitsandbytes y datasets; el venv de ComfyUI tampoco incluye Diffusers/Accelerate/PEFT. Hay que elegir y validar un flujo compatible antes de cualquier entrenamiento.
- Los fondos de cinemática actuales son PNG **512×256 (2:1)**, y la superficie lógica es **1280×800 (16:10)**. El motor escala pixel art con `pygame.transform.scale`/nearest-neighbor y factor entero; no puede mostrar 1280×720 como encuadre 16:9 completo, sin recorte/letterbox ni cambio de área.
- La Biblia nueva y las guías actuales no coinciden por completo: `estilo/ESTILO.md` describe principalmente retratos CRT/dithering; `estilo/escenas.json` describe fondos vibrantes sin scanlines/dithering. La Biblia V1.0 será la referencia propuesta para fondos; no se reemplazó ninguna guía anterior.
- Recomendación: separar entrenamiento y generación de la aplicación, mantener modelos/datasets fuera del repositorio y cambiar el encuadre en un límite exclusivo del reproductor de cinemáticas, una vez aprobado el diseño de pantalla.

## 1. Estructura actual y sistema cinematográfico

### Componentes del proyecto

| Área | Estado observado |
|---|---|
| Reproductor | `cinematicas.py`: secuencias de escenas por datos; dibujo del fondo, tratamiento por mundo, diálogo/títulos, retratos, máquina de escribir, avance, saltos y música. |
| Dimensiones globales | `ui.py`: `ANCHO, ALTO = 1280, 800`; constantes y helpers se usan en muchas pantallas, así que cambiar estas constantes globales impactaría el juego entero. |
| Fondos de runtime | `assets/fondos/*.png`; claves nombradas (camino, aldea, ruinas, salón, etc.) y variantes elegidas por semilla vía `ui.ruta_fondo`. Encontrados 39 PNG de fondo incluyendo variantes. |
| Arte/guion | `prologo.py`, `narrativa.py`, `finales.py`, `encuentros.py`, `duelistas.py`, `campana.py` componen textos y seleccionan claves de fondo. |
| Pipeline de generación | `generar_escenas.py` produce arte mediante ComfyUI; su propio comentario afirma que el juego nunca importa este módulo. Está separado del pipeline de cartas y tiene catálogo, prompts y reducción nearest-neighbor. |
| Configuración visual previa | `estilo_escenas.py`, `estilo/escenas.json`, `estilo/ESTILO.md`; las medidas comentadas todavía son 512×256 para fondos. |
| Modelos inferencia | **ComfyUI** (`E:\AI\ComfyUI\models\checkpoints`): SDXL Base 1.0, Animagine XL 4.0 y Pixel Art Diffusion XL Sprite Shaper; su carpeta `models\loras` solo tiene el marcador. **Workspace separado** (`E:\AI\CartonesMazmorrasVisual`): checkpoint SD 1.5 `models\sd15\v1-5-pruned-emaonly.safetensors`, usado en evaluaciones anteriores. No confundir el inventario local de ComfyUI con todos los modelos instalados en la máquina. |

El reproductor dibuja primero el fondo en la pantalla pasada (`screen.blit(REC.fondo_pantalla(...), (0, 0))`), luego el tinte/vineta y encima texto y retrato. El cuadro de diálogo está en `y=ALTO-212`, tiene 152 px de alto; el avatar va en posición superior derecha. Actualmente fondo y UI comparten coordenadas lógicas 1280×800. Referencias: `cinematicas.py` 239–324; `ui.py` 19, 350–427.

### Imágenes y estilos actuales

- Fondo actual: 512×256; avatares `assets/avatar_*.png`: 256×256; ilustraciones de encuentros `assets/escenas/*.png`: 512×384. La tarea no implica cambiar estos retratos ni avatares.
- `estilo/escenas.json` define fondos sin personajes en primer plano, pixel art anime, sin scanlines ni dithering. `estilo/ESTILO.md` proviene de un moodboard de cartas y propone CRT marcado, scanlines/dithering y retratos. Hay una discrepancia entre documentos y alcance visual: la Biblia V1.0 separa identidad del arte y CRT como postproceso configurable, con scanlines sutiles y sin entrenar scanlines pronunciadas.
- El nuevo lienzo 1280×720 cambia formato, composición, densidad de píxel y área de interfaz; no es únicamente “renderizar más grande” los fondos 512×256.

## 2. Auditoría del entorno local de generación y entrenamiento

### Hardware/runtime — consulta observada el 12-oct-2026

| Elemento | Evidencia de solo lectura | Resultado |
|---|---|---|
| GPU | `nvidia-smi` | NVIDIA GeForce RTX 2060, modelo WDDM; **6,144 MiB VRAM**. En el instante de consulta 1,137 MiB ocupados (~5,007 MiB disponibles), uso GPU 1%. |
| Driver | `nvidia-smi` / `E:\AI\README_COMFYUI.md` | Driver NVIDIA 610.88; CUDA UMD 13.3 según `nvidia-smi`. |
| Python ComfyUI | lectura de metadatos del venv, no ejecución de pipeline | Python 3.12.10 64-bit. |
| PyTorch ComfyUI | metadatos del venv | 2.14.0+cu130, torchvision 0.29.0+cu130 según metadatos. No se ejecutó cómputo CUDA. |
| Otro entorno | `TripleTriad\.sd_env` | Python 3.12.10; PyTorch 2.5.1+cu121, torchvision 0.20.1+cu121. |
| CUDA Toolkit | `E:\AI\README_COMFYUI.md` | La documentación del entorno indica que el toolkit de sistema no está instalado; no es necesariamente requisito para inferencia, pero el método de entrenamiento elegido debe confirmar sus requisitos. |

La prueba de `nvidia-smi` fue una consulta de estado del dispositivo, no una operación de generación/training. No se llamó al modelo ni a `torch.cuda` para hacer cálculo. La VRAM observada confirma una restricción real de 6 GB; el uso de memoria varía y la inferencia SDXL ya puede acercarse al límite según resolución/flujo. Entrenar SDXL LoRA en esa tarjeta debe considerarse **condicionado y de alto riesgo de OOM**, no una tarea que se da por viable por tener CUDA. Requiere un piloto técnico separado, con configuración ajustada a la VRAM real, antes de planificar el dataset completo.

### Software existente

| Componente | `.sd_env` del proyecto | `E:\AI\ComfyUI\venv` | Lectura práctica |
|---|---:|---:|---|
| ComfyUI | No | Aplicación presente (README: 0.39.0) | Sistema de inferencia instalado; ComfyUI no aporta por sí solo pipeline de entrenamiento LoRA SDXL validado. |
| SDXL base/checkpoints | No en repo | SDXL Base 1.0, Animagine XL 4.0, Sprite Shaper presentes | Hay modelos base locales; validar licencia/procedencia/uso específico del checkpoint elegido. |
| SD 1.5 base | No en repo | `E:\AI\CartonesMazmorrasVisual\models\sd15\v1-5-pruned-emaonly.safetensors`; SHA-256 verificado 13-oct-2026: `6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa`. | Base compatible disponible; ya fue usado exitosamente en `evals/sd15_lora_eval_v001`. Reutilizar, no descargar otra copia. |
| PyTorch/CUDA | 2.5.1+cu121 | 2.14.0+cu130 (metadatos) | Existen runtimes separados y versiones distintas; no mezclarlos ni instalar sobre ellos sin una decisión explícita. |
| Diffusers | 0.32.1 | No instalado | Disponible en `.sd_env`, pero no hay evidencia de ejemplos/scripts de entrenamiento integrados/configurados. |
| Transformers | 4.48.0 | 5.19.0 | Presente, pero las versiones son diferentes; se debe fijar matriz compatible del trainer elegido. |
| Accelerate | 1.15.0 | No instalado | Está en `.sd_env`; no hay configuración de Accelerate auditada para entrenamiento. |
| PEFT | No | No | Dependencia habitual para adaptadores LoRA de Diffusers. |
| bitsandbytes | No | No | No instalado; 8-bit optimizers/quantización disponibles no pueden asumirse. Su soporte en Windows debe verificarse según el trainer. |
| xFormers | No | No | No instalado; no asumir atención optimizada por xFormers. |
| safetensors | 0.8.0 | 0.8.0 | Formato runtime disponible, no equivale a entrenamiento. |
| datasets / TensorBoard | No / No | No / No | No están listados en los entornos examinados. |
| Herramienta específica de entrenamiento SDXL LoRA | No hallada | No hallada | No se encontró Kohya/sd-scripts, OneTrainer, script Diffusers SDXL training ni nodos de entrenamiento LoRA instalados. |
| ComfyUI LoRA | Solo nodo cargador estándar | N/A | `models/loras` está vacío salvo marcador. Un nodo Load LoRA aplica uno; no entrena uno. |

Los resultados de esta sección describen entornos distintos. La afirmación anterior de que no había checkpoint SD 1.5 instalado era incompleta: describía el inventario de ComfyUI, pero omitía el workspace externo `E:\AI\CartonesMazmorrasVisual`. Allí también existen `sd-scripts/gen_img.py`, el entorno `venv-sdxl` y registros de inferencia SD 1.5 satisfactoria a 640×360 (`evals/sd15_lora_eval_v001`). Esto no implica que SDXL LoRA training esté instalado ni probado. Se identificó en ComfyUI un `comfy_extras/nodes_train.py`, pero no equivale a un trainer SDXL LoRA de estilo listo y probado; no se debe confundir con nodos de carga/aplicación LoRA.

### Componentes faltantes para entrenar el LoRA propio

1. **Decisión de trainer y compatibilidad de SO/GPU:** seleccionar una implementación SDXL LoRA con soporte Windows/RTX 2060 y fijar sus versiones. Sin instalar nada todavía. Evaluar si cabe el entrenamiento con VRAM de 6 GB; de no ser así, decidir alternativa (entrenamiento en otra máquina/servicio autorizado o posponer), sin cambiar las reglas de no descarga hasta aprobar.
2. **Pipeline de entrenamiento completo:** script/configuración de LoRA SDXL, optimizador soportado, precisión/gradiente, cache latentes y gestión de OOM; configuración reproducible. Diffusers + Accelerate en `.sd_env` es una base potencial, no una instalación lista: faltan PEFT y entrenamiento/configuración específica.
3. **Dataset con derechos documentados:** 40–60 imágenes curadas que abarquen mundo moderno/torneo, bosque, arquitectura, ruinas, fortalezas, Umbral; coherencia de estilo a pesar de locaciones distintas; exclusión de personajes, retratos y cartas según Biblia. Registrar procedencia/licencia y aprobaciones.
4. **Captions/metadatos:** caption individual coherente, token `cmd_pixelanime_bg`, descripción de contenido/iluminación/mundo/encuadre; mantener token de estilo distinguible de atributos de escena. Herramienta y revisión humana no seleccionadas.
5. **Preparación uniforme:** control de duplicados/calidad, dimensiones/aspectos, recortes/agrupación de resoluciones (bucketing si el trainer lo soporta), limpieza de texto y política de augmentations. Evitar recortes que borren composición horizontal.
6. **Modelo base y licencia fijados:** resolver qué checkpoint SDXL será la base de producción (SDXL Base oficial u otro instalado), registrar hash, revisión y licencia. Los checkpoints disponibles no garantizan que todos sean adecuados para un LoRA de fondos.
7. **Validación y muestras:** prompts fijos de prueba para salón, bosque lluvioso, trono y ubicaciones inéditas; semillas registradas; comparación base vs LoRA; criterios visuales de Biblia y prueba con caja de diálogo/avatar real sin editar sus archivos.
8. **Almacenamiento/versionado:** dataset/captions/configs/checkpoints/muestras/resultados y metadatos con manifiestos/versiones; LoRA estable inmutable. Política de backup y capacidad de disco aún no auditadas.

## 3. Estructura de carpetas recomendada

Propuesta de raíz externa a Git: `E:\AI\CartonesMazmorrasVisual\` (el nombre/path es sugerencia; no se creó). Mantener documentación liviana y scripts de orquestación revisables en repo; bytes grandes fuera.

```text
E:\AI\CartonesMazmorrasVisual\
├── README.md                    # rutas, responsables, comandos no secretos
├── manifestos\                 # JSON/CSV de hashes, licencia, origen y estado
├── dataset\
│   ├── source_original\        # originales curados, solo lectura tras aprobación
│   ├── curated\v1\             # selección aprobada 40–60
│   ├── rejected\                # material rechazado, opcional y separado
│   └── captions\v1\            # .txt por imagen + metadata/csv
├── configs\
│   ├── train\                  # config exacta y README de versiones
│   └── generation\             # prompts y parámetros reproducibles
├── models\
│   ├── base\                   # referencias/enlaces/manifest; pesos fuera o gestionados aparte
│   └── lora\cmd_pixelanime_bg\v001\
│       ├── adapter.safetensors
│       └── manifest.json        # base hash, config, dataset hash, versión/toolchain
├── checkpoints\                # checkpoints intermedios, retención temporal
├── samples\v001\               # muestras de validación y hojas de contacto
├── exports\
│   ├── staging\                # fondos candidatos aún no integrados
│   └── approved\               # entrega aprobada con prompt/seed/licencia
└── logs\                        # logs de entrenamiento/generación (sin tokens/secretos)
```

En el proyecto, los fondos de runtime definitivos pueden permanecer en `TripleTriad/assets/fondos/` solo después de aprobación e integración. Recomendación operativa: nunca apuntar una salida de generación directamente a esa carpeta; exportar a staging, revisar y luego copiar bajo control. Las rutas de modelo pueden enlazarse desde ComfyUI solo cuando el trabajo sea aprobado. No guardar datasets, checkpoints base, LoRAs pesados, checkpoints de entrenamiento ni renders exploratorios en Git.

### Separación de Git y archivos pesados

- Los modelos y datos de entrenamiento deben quedar fuera del checkout, idealmente en `E:\AI\CartonesMazmorrasVisual`; ComfyUI ya vive bajo `E:\AI` y los assets propios del juego no necesitan cambiar de ubicación.
- El repo Git actual es `E:\openCode` (no `E:\openCode\TripleTriad`); `.gitignore` está en `E:\openCode\.gitignore`. Ya ignora `TripleTriad/.sd_env/`, resultados/carpeta de auditorías y arte temporal enumerados en líneas 25–68, pero **no define una regla futura general para `TripleTriad/assets/fondos/` ni para una carpeta nueva de dataset/checkpoints**. Como los fondos actuales sí son runtime assets rastreables, no conviene ignorar globalmente `assets/fondos/`; se deben ignorar ubicaciones de entrenamiento/outside-tree y salidas temporales específicas.
- Para ficheros externos, versionar manifiestos de texto pequeños (hash SHA-256, nombre, licencia, procedencia, dimensiones, prompt/seed y estado) y versionar el código/config que defina el proceso, no los blobs. No introducir symlinks con destino a pesos dentro del árbol de juego empaquetable.
- Si en el futuro se decide que ciertos PNG finales van al juego, incluir solo PNG aprobados y necesarios en assets runtime; evitar commitear muestras, originales de dataset y duplicados. Una política de LFS solo sería alternativa explícita para finales grandes; no se necesita para modelos ni dataset si quedan externos.
- Antes de añadir ignore rules, distinguir archivos locales existentes y revisar `git status`; no borrar ni reclasificar trabajo ya presente. Estado observado incluye un informe de auditoría previo no rastreado y archivos untracked hermanos (`ace-step-dashboard...`, `contexto.md`), que deben conservarse.

## 4. Resolución 1280×720: análisis de integración

### Estado geométrico actual

- Superficie lógica global: 1280×800 (16:10), declarada en `ui.py` y usada por todo el juego.
- Los 512×256 (2:1) actuales son escalados con nearest-neighbor y factor entero elegido por `ui.Recursos._escalar_pixelart`; para 1280×800 habitualmente escala 3× (1536×768), recorta 256 px de anchura y mantiene bandas verticales. La política favorece pixel art sin deformación pero recorta la composición lateral.
- Fondo directo a 1280×720 (16:9) **no** tiene que escalarse para pantalla si el viewport de cinemática pasa a ser exactamente esa medida. En el modo 640×360→2×, cada píxel base produce un bloque de 2×2; usar nearest-neighbor sin reducir fraccionalmente. Si el lienzo final 1280×720 se blitea dentro de 1280×800, quedan 80 px de diferencia vertical (por ejemplo 40 arriba/abajo si centrado), o se reserva otra zona; decidirlo explícitamente.
- Los fondos actuales 2:1 no se convierten automáticamente en 16:9: se recortan en vertical o se agregan bandas laterales si se preserva la imagen. La generación 1280×720 debe componer nativamente a 16:9 y con espacio de diálogo en el tercio inferior.

### Cambios a evaluar en el reproductor (no realizados)

1. **Viewport aislado de cinemática:** definir rectángulo 1280×720 para el render cinematográfico sin cambiar `ui.ANCHO/ALTO` globales ni el tablero/menús. Conservar la ventana y superficie lógica actual mientras se dibuja el juego común.
2. **Composición/clipping:** dibujar fondo y tratamiento dentro del viewport; decidir posición de viewport en 1280×800 (centrado o anclado), color de 40-px sobrantes arriba/abajo, y clipping para que caja/retrato no invadan zona ajena. No estirar a 1280×800.
3. **Layout sensible al viewport:** reubicar caja de diálogo, encabezado, avatar, título y pista de continuar usando origen/alto de cinematic viewport, sin alterar tamaños/estilo del resto de UI. Validar el tercio inferior y las colisiones de texto/retrato.
4. **Escalado de imagen:** añadir ruta de fondo cinematográfico 16:9 separada del helper general, nearest-neighbor para assets pixelados 640×360 ampliados 2×. Si se admiten artes 1280×720 con pixel grid ya final, blit 1:1; no aplicar smoothscale. Definir fallback a 512×256 para evitar regresión mientras conviven assets.
5. **Caché/letrero de bandas:** `REC.fondo_pantalla` cachea por ruta usando destino global 1280×800; adaptar/crear caché por ruta + tamaño/viewport para no reutilizar superficies incorrectas. Revisar `_letterbox` y `Cinematica._barras`, que dependen de dimensiones y letterbox actuales.
6. **Tratamiento visual:** tinte/vineta se componen en el viewport, no sobre las bandas externas; conservar la distinción `mundo=real/juego`. La Biblia trata CRT como capa configurable posterior, no como modificación destructiva de los PNG.
7. **Pruebas:** verificar 1280×720 exacto, ratio, no deformación ni blur, ubicación del diálogo, avatars intactos, lectura, clipping, variación de fondos, letterbox/fallback, saltar/avanzar, intro/prólogo/campaña/finales y pantallas no cinematográficas idénticas a baseline.

Una solución de bajo riesgo es renderizar una subsuperficie/viewport para cinemáticas y dejar `ANCHO,ALTO=1280,800` y el resto del juego intactos. La elección definitiva de bandas/centrado y del tamaño de diálogo debe aprobarse con un mockup estático antes de tocar el renderer.

## 5. Incompatibilidades/decisiones antes de implementar

1. Biblia V1.0 será normativa para nuevos fondos. Resolver si actualiza/reemplaza documentalmente `estilo/escenas.json` y `estilo_escenas.py`, y cómo se tratará `estilo/ESTILO.md` (está redactado desde un moodboard de cartas, con CRT pronunciado y retratos). No mezclar el LoRA de fondos con arte de cartas/retratos.
2. Elegir checkpoint base de entrenamiento. En ComfyUI están SDXL Base 1.0, Animagine XL 4.0 y Sprite Shaper; fuera de ComfyUI existe el checkpoint SD 1.5 registrado en la tabla de inventario, ya usado para inferencia. Los LoRA SD 1.5 deben usar esa familia, no los checkpoints SDXL. El pipeline de `generar_escenas.py` usa actualmente ComfyUI y downscale nearest-neighbor. Ningún LoRA propio se detectó en el inventario original.
3. Verificar procedencia/licencia de cada imagen de dataset y del checkpoint seleccionado; no asumir que las imágenes existentes son automáticamente aptas para entrenamiento.
4. Con 6 GB VRAM, cerrar viabilidad práctica del trainer SDXL. No asumir que settings de inferencia `--lowvram` permiten entrenar. La ruta actual de ComfyUI reserva ~1GB según `E:\AI\README_COMFYUI.md`, lo que reduce VRAM libre para otros procesos.
5. Resolver el modelo de salida: recomendado tener maestros de trabajo 640×360 para nearest-neighbor 2× y PNG final 1280×720, validando antes si el color requiere RGB o alpha. Fondos no necesariamente necesitan alpha; la Biblia permite RGB/RGBA.
6. Aclarar si “todos los fondos actuales de las cinemáticas” significa reemplazar los 39 PNG en `assets/fondos/` (incluidas variantes climáticas) o solo cada clave/base efectivamente usada. Auditar todos los paths/variantes y callsites antes de fijar cantidad de entregables. Los fondos incluyen `assets/fondos`, no las ilustraciones/retratos de `assets/escenas` ni `avatar_*.png`.
7. La historia debe mandar sobre composición: el Umbral de nueve casillas puede usarse cuando corresponda pero sin adelantar revelaciones, como prescribe la Biblia; se recomienda mantener el inventario narrativo del informe previo como matriz de brief/validación.

## 6. Plan de implementación propuesto — etapas pequeñas, verificables y reversibles

Cada etapa queda sujeta a aprobación antes de iniciar. Mantener backups/versionado y conservar los fondos vigentes hasta aceptar todo el lote.

| Etapa | Trabajo | Verificación / reversibilidad |
|---|---|---|
| 0. Aprobación de especificación | Aprobar Biblia como fuente normativa, definir alcance de “todos”, trainer/base candidatos y política de datos/almacenamiento. | ADR/decisiones de texto; no cambia juego ni entorno. |
| 1. Inventario congelado | Exportar manifiesto de cada clave y variante, ruta, dimensión, usos narrativos, hash y estado; revisar fondos existentes y rutas. | Reconciliar con 39 PNG y callsites; solo manifiesto, rollback borrando ese documento. |
| 2. Cerrar diseño 16:9 | Prototipo de layout aislado/mockup para 1280×720 dentro de 1280×800, con caja y retrato existentes; acordar letterbox, safe area y pixel grid. | Capturas de diseño/revisión humana; aún sin cambiar productor del juego. |
| 3. Verificar toolchain en sandbox | Elegir una sola implementación; comprobar versiones/Windows/CUDA/VRAM en entorno separado y revisar que carga el base sin actualizar ComfyUI/GPU-Coordinator/ACE-Step. Evaluación de factibilidad sin entrenamiento inicial. | Registro de versiones y prueba de importación/capacidad aprobada; entorno desechable y fuera de repo; no descargar ni entrenar hasta autorización explícita. |
| 4. Dataset y captions v1 | Curar 40–60 imágenes licenciadas y balanceadas, captionar, revisar diversidad y excluir personajes/cartas; congelar conjunto/versionarlo por hash. | Checklist de derechos, captions y cobertura de escenarios; originales no se alteran; rollback manteniendo versión previa. |
| 5. Piloto de entrenamiento | Entrenar LoRA v0 solo con dataset congelado en workspace externo, checkpoint base fijo, settings de bajo consumo y checkpoints/muestras externos. | No OOM, reproducibilidad declarada, comparación base/LoRA en los tres pilotos; conservar base y v0; no integrar. Requiere aprobación específica pues implica entrenamiento GPU. |
| 6. Validación de consistencia | Generar hojas de prueba para salón/torneo, bosque lluvioso, sala del trono y prompts nuevos; probar diálogos/avatar en compositor de prueba. | Scorecard de Biblia, prompt/seed/config/hash; decisión aceptar/iterar. No escribir `assets/fondos` aún. |
| 7. Integración de viewport | Cambio opt-in/feature flag del reproductor para viewport 16:9, con antiguos fondos como fallback; no cambiar superficie global. | Tests visuales/funcionales en todos los tipos de cinemática y no regresión de menús/duelos. Revertible por flag y commit pequeño. |
| 8. Integración de piloto | Copiar solo los 3 escenarios aprobados a staging y luego integrar a rutas dedicadas; no sobrescribir los fondos actuales durante comparación. | Manifiesto + hashes y pruebas; activar/desactivar por selección/config de asset; rollback inmediato al set original. |
| 9. Producción completa por lotes | Completar matriz de fondos restantes, variantes y casos raros en lotes pequeños con revisión humana, conservar seed/prompt/versiones. | Aprobación por lote; los fondos antiguos se retienen como fallback hasta aceptar cobertura total. |
| 10. Cierre/limpieza | Aceptar visualmente todo, fijar versión estable del LoRA, preparar manifiesto y política de archivos pesados. Retirar fallback solo si se autoriza y existe copia externa verificada. | Test final y backups comprobados; cualquier eliminación requiere aprobación separada. |

## 7. Límites respetados y fuentes de evidencia

- No se ejecutó el juego, no se generaron imágenes, no se entrenó, no se instalaron dependencias ni se descargaron pesos.
- No se llamó a ComfyUI, GPU-Coordinator, ACE-Step ni a operaciones de cómputo GPU. `nvidia-smi` se usó únicamente para leer modelo, VRAM y ocupación instantánea.
- No se modificaron fondos, avatares, retratos, historia ni código funcional. Se crearon únicamente los dos documentos de preparación (esta auditoría y la copia de la Biblia).
- Fuentes inspeccionadas: `cinematicas.py`, `ui.py`, `prologo.py`, `narrativa.py`, `finales.py`, `campana.py`, `main.py`, `generar_escenas.py`, `generar_cartas_comfyui.py`, `estilo_escenas.py`, `estilo/escenas.json`, `estilo/ESTILO.md`, `paths.py`, `E:\AI\README_COMFYUI.md`, `.sd_env` y el venv/modelos de `E:\AI\ComfyUI`.
- Inventario runtime: `assets/fondos/*.png` (39 archivos), `assets/avatar_*.png`, `assets/escenas/*.png`; dimensiones documentadas también en `estilo_escenas.py` y medidas leídas anteriormente en disco.
- Aislamiento Git: repositorio raíz `E:\openCode`, reglas `E:\openCode\.gitignore`; el `.sd_env` del juego ya está ignorado. `E:\AI` se encuentra fuera del repo y es la ubicación adecuada para los archivos pesados.
