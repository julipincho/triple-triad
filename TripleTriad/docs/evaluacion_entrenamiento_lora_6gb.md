# Evaluación técnica: estrategia de entrenamiento LoRA con RTX 2060 6 GB

**Fecha de consulta:** 12 de octubre de 2026.  
**Estado:** análisis y propuesta; experimento pendiente de autorización.  
**Decisión recomendada:** entrenar el LoRA **SDXL en GPU externa dedicada**, manteniendo ComfyUI, los entornos locales y la aplicación de juego sin cambios. No se lanzó entrenamiento, no se descargaron modelos ni se hicieron pruebas de GPU.

## Resumen para decisión

La RTX 2060 local tiene 6,144 MiB de VRAM y Windows/desktop compartía alrededor de 1.1 GiB durante la inspección de `nvidia-smi`. Una LoRA SDXL de U-Net a resolución menor puede ser posible con optimizaciones, pero el margen es muy estrecho, dependiente del software/driver y propenso a OOM. La documentación actual de `kohya-ss/sd-scripts` recomienda SDXL LoRA desde 8 GB (10 GB sugeridos) y advierte de OOM incluso con 24 GB en algunas configuraciones. Por tanto, “posible en un caso excepcional” no equivale a “estable para un proceso repetible”.

**Recomiendo una sola estrategia inicial: SDXL LoRA externo, en una GPU de 24 GB o más, con `sd-scripts` fijado a un commit/release y entorno aislado.** Mantiene la misma familia que los modelos SDXL ya instalados y conserva una base de capacidad alta para los escenarios panorámicos 16:9 de la Biblia. La GPU externa protege estabilidad y disponibilidad de los servicios locales. Es una recomendación de calidad/estabilidad, no una afirmación de que SDXL no pueda funcionar localmente.

El experimento de esta propuesta es un smoke test pequeño en la GPU externa: 4–6 imágenes con derechos claros, resolución de entrenamiento reducida y pocos pasos, seguido de prueba de exportación/inferencia. Su objetivo es comprobar compatibilidad, aprendizaje del token y consistencia básica, **no** aprobar el LoRA definitivo ni reemplazar los fondos. No debe ejecutarse hasta aprobación expresa.

## 1. Hardware y entornos locales verificados

La inspección local no cambió ni cargó modelos. Consultas de metadatos de Python y `nvidia-smi` solamente:

| Componente | Resultado observado |
|---|---|
| GPU | NVIDIA GeForce RTX 2060, WDDM |
| VRAM física | 6,144 MiB (6 GB nominales) |
| VRAM en uso al consultar | 1,137 MiB; disponibles en ese instante ~5,007 MiB. La cifra cambia según los procesos del escritorio y no es capacidad reservada para el trainer. |
| Driver / CUDA reportada por driver | NVIDIA 610.88; CUDA UMD 13.3 en salida `nvidia-smi`. El toolkit CUDA del sistema no está instalado según `E:\AI\README_COMFYUI.md`. |
| Entorno `E:\AI\ComfyUI\venv` | Python 3.12.10; PyTorch 2.14.0+cu130; torchvision 0.29.0+cu130 según metadatos locales/documentación. Tiene ComfyUI y modelos SDXL para inferencia. No tiene Diffusers, Accelerate, PEFT, bitsandbytes ni xFormers en el inventario consultado. |
| Entorno `TripleTriad\.sd_env` | Python 3.12.10; PyTorch 2.5.1+cu121; torchvision 0.20.1+cu121; Diffusers 0.32.1; Transformers 4.48.0; Accelerate 1.15.0; safetensors 0.8.0; Pillow 12.3.0. No hay PEFT, bitsandbytes, xFormers ni herramienta de entrenamiento LoRA SDXL instalada. |
| Modelos locales | **ComfyUI** (`E:\AI\ComfyUI\models\checkpoints`): SDXL Base 1.0, Animagine XL 4.0, Sprite Shaper; `models\loras` solo contiene marcador vacío. **Workspace de evaluación separado** (`E:\AI\CartonesMazmorrasVisual`): SD 1.5 `models\sd15\v1-5-pruned-emaonly.safetensors`, SHA-256 `6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa`; registro de inferencia exitosa en `evals\sd15_lora_eval_v001`. No confundir que ComfyUI no tenga SD 1.5 con ausencia de un checkpoint SD 1.5 en la máquina. |

La versión de CUDA embebida en una rueda PyTorch, el toolkit CUDA y la versión CUDA indicada por el driver son conceptos distintos. No concluir compatibilidad total a partir del “CUDA 13.3” de `nvidia-smi`; el trainer debe probarse con su propia matriz PyTorch/CUDA en un entorno aparte. No se ejecutó `torch.cuda` ni cálculo CUDA en esta evaluación.

## 2. Viabilidad SDXL LoRA con 6 GB en Windows

### Qué reduce VRAM y qué no

| Técnica | Efecto esperado | Coste/limitación | Para este caso |
|---|---|---|---|
| Mixed precision FP16 | Reduce memoria de pesos/activaciones y suele acelerar NVIDIA. | FP16 tiene rango menor; VAE SDXL puede producir NaN según configuración. El trainer documenta `no_half_vae` para estabilidad cuando aplica. | Base obligatoria de una prueba local. No usar BF16 sin verificar soporte eficiente de la arquitectura y trainer. |
| Gradient checkpointing | Reduce activaciones retenidas, recomputándolas durante backward. | Más tiempo por paso y cómputo adicional. | Es una palanca importante para SDXL, pero no elimina memoria de pesos, optimizer, buffers ni reserva del escritorio. |
| Batch size 1 | Evita multiplicar memoria de activaciones por lote. | Menor throughput; no equivale a batch efectivo mayor sin acumulación. | Obligatorio para la RTX 2060 local. |
| Gradient accumulation | Simula batch efectivo mayor sin mantener simultáneamente todas las muestras. | Más pasos/tiempo; no reduce memoria de un paso individual por debajo del batch 1. | 1–4 en el piloto, según duración/estabilidad; empezar en 1. |
| Cache latents (CPU/disco) | Evita volver a calcular VAE; puede reducir carga de proceso y tiempo. | `sd-scripts` advierte que cache latents desactiva augmentations como random crop/flip/color; cache puede ocupar espacio/RAM. No garantiza una gran reducción del pico del U-Net backward. | Útil en dataset pequeño y fijo. Usar cache a disco si la RAM es limitada; no hacer augmentations incompatibles. |
| Cache text encoder outputs | Evita mantener/ejecutar text encoders durante training y libera VRAM significativa. | Hace necesario entrenar U-Net only; caption dropout/shuffle ya no aplica. | Adecuado para LoRA de estilo con captions estables y token consistente. No entrenar text encoders al inicio. |
| 8-bit optimizer | Reduce estado del optimizer. | Requiere `bitsandbytes`; Windows/versión de wheel/arquitectura pueden ser punto de fallo; no arregla activaciones o carga base. | No depender de este componente en primer experimento. Usar solo si el trainer da soporte verificable en la imagen elegida. |
| Adafactor | Puede reducir estado de optimizer, hay soporte específico en sd-scripts. | Ajustes/learning rate difieren de AdamW; calidad/estabilidad deben validarse. Algunas funciones fusionadas son experimentales y tienen incompatibilidades con gradient accumulation. | Opción alternativa reproducible si optimizer memory fuera cuello de botella; no usar fused experimental como primera línea. |
| xFormers / memoria eficiente | Puede ahorrar memoria de atención/tiempo. | Paquetes binarios deben coincidir con PyTorch, CUDA, Python y GPU; no está instalado localmente. PyTorch SDPA también puede estar disponible, según trainer. | No es requisito de diseño. No instalar en entorno actual para probarlo. |
| `full_fp16`, FP8 | Puede reducir uso adicional en algunas rutas. | Entrenamiento total en media precisión puede ser inestable; el propio sd-scripts marca full precision/FP8 y fused pass con cautelas/experimentalidad. | Excluir del primer test. FP8 no se debe asumir adecuado para Turing/RTX 2060. |
| CPU/RAM offload | Reduce VRAM trasladando carga. | Rendimiento puede caer mucho; transferencias y soporte del trainer varían. RAM del equipo no se auditó en esta tarea. | No asumir que “memoria compartida” soluciona el margen; no es mi opción inicial. |

### Resolución de entrenamiento

SDXL fue desarrollado alrededor de la clase 1024; la guía oficial de `sd-scripts` recomienda mantener una resolución alta y usar aspect-ratio buckets con pasos múltiplos de 32 para SDXL. Sin embargo, 1024 nativo impone carga de memoria/tiempo importante y no es necesario probar el comportamiento inicial del token. La salida final 1280×720 no obliga a entrenar a 1280×720: usar un bucket horizontal menor para prueba y entrenamiento y generar/posprocesar a entrega final es válido, siempre que el modelo conserve composición panorámica.

Para el smoke test propuesto: bucket de referencia **768×448** (ratio ~1.71; bucket cercano a 16:9 y múltiplos de 32), no recorte cuadrado. Para producción SDXL, evaluar posteriormente 1024×576 o bucket SDXL próximo a 16:9, condicionado a memoria y política de resize/crop del trainer. Esas dimensiones no son por sí solas una garantía de compatibilidad: la guía del dataset del trainer elegido manda. La reducción de resolución puede cambiar fidelidad de agrupaciones de píxeles; validar la rejilla 640×360→2× y el nearest-neighbor al final por separado.

### Viabilidad específica en 6 GB

**Conclusión: marginal y no recomendada como ruta productiva.** `sd-scripts` documenta 8 GB como realizable y 10 GB recomendados para SDXL LoRA, con UNet-only, checkpointing, cache de latentes/encoders y optimizer eficiente; su guía general advierte que SDXL puede agotar incluso 24 GB con settings concretos. La RTX 2060 tiene menos VRAM que ese piso, y el sistema gráfico consume una parte. Historias de usuarios que encajan en 6 GB con modelos/configs concretos son evidencia anecdótica, no criterio de estabilidad.

El entorno local de ComfyUI está configurado para inferencia low-VRAM y reserva alrededor de 1 GB de VRAM en su launcher documentado. Esa configuración no se traslada automáticamente al entrenamiento y modificarla incumpliría el objetivo de no tocar el servicio estable. Si se quisiera probar local, tendría que ser un entorno distinto, sin servicio ComfyUI activo, con aprobación específica y una posibilidad real de OOM/tiempo excesivo.

## 3. Comparación de las tres alternativas

| Alternativa | Calidad potencial para la Biblia | Viabilidad/estabilidad | Privacidad/coste | Juicio |
|---|---|---|---|---|
| **SDXL LoRA local (RTX 2060 6 GB)** | La misma familia de modelos que está instalada; mejor techo esperado para paisaje amplio, arquitectura compleja, iluminación y composición cinematográfica que un modelo antiguo de 512. Permite entrenar la identidad común de escenarios. | Puede llegar a funcionar en settings comprimidos; 6 GB está por debajo de la recomendación documentada de 8 GB. Alta sensibilidad a memoria del escritorio, resolución, optimizer, VAE y versiones. Riesgo alto de OOM/depuración; mucho más lento que tarjeta moderna. No tocar ComfyUI actual implica sandbox adicional. | Dataset y modelo permanecen local; sin alquiler. Puede exigir espacio/RAM/tiempo local aún no medidos. | No escoger como primer entrenamiento estable; solo como experimento local posterior si se prioriza privacidad/coste y se acepta el riesgo. |
| **SD 1.5 LoRA local** | Mejor posibilidad de entrenar y iterar con 6 GB; ecosistema maduro y resolución típica 512. Pero la identidad de una obra SD 1.5 no se transfiere directamente a SDXL; composición horizontal, detalle de escenarios y seguimiento de prompts puede quedar por debajo del objetivo. Convertir/escalar a 1280×720 no recupera detalle estructural ni hace 16:9 nativo. | Mucho más viable que SDXL en 6 GB. Sigue necesitando un trainer/entorno aislado, dependencias, dataset y validación; no está el trainer en los entornos revisados. | Local/privado, sin coste de GPU externa; más rápida iteración. | Buen fallback para aprender el procedimiento o producir una versión deliberadamente SD1.5; no elige la familia adecuada al pipeline SDXL actual si la prioridad es el techo de calidad. |
| **SDXL LoRA con GPU externa** | Conserva SDXL; permite usar resolución/clase de entrenamiento y buckets panorámicos menos comprometidos, más contexto de atención y revisiones de muestras. No garantiza consistencia por sí misma: captions, dataset balanceado, base y prompts fijos siguen siendo críticos. | La opción más estable si se exige GPU dedicada **24 GB+**; 16 GB puede bastar para LoRA UNet-only con checkpointing pero tiene menos margen; recomendamos no basar primera prueba en un mínimo muy justo. Entorno efímero/aislado, pin de commit, sin cambios al PC local. | Alquiler/cupo y transferencia de dataset; evaluar derechos, política de retención y privacidad del proveedor. Datos no públicos deben cifrarse y eliminarse/verificarse al terminar. | **Recomendada** por mejor equilibrio de fidelidad SDXL y estabilidad del entorno de desarrollo local. |

## 4. Herramientas candidatas mantenidas

Estado consultado en documentación pública actual el 12-oct-2026. “Mantenida” significa que el repositorio/docs muestran desarrollo y soporte actuales al momento de consulta; las versiones y requisitos pueden cambiar, hay que fijar commit antes de prueba.

| Herramienta | Soporte/modelos | Ventajas | Limitaciones / requisitos relevantes | Idoneidad |
|---|---|---|---|---|
| **kohya-ss/sd-scripts** — [repo](https://github.com/kohya-ss/sd-scripts), [advanced SDXL LoRA](https://github.com/kohya-ss/sd-scripts/blob/main/docs/train_network_advanced.md), [Windows setup](https://github.com/kohya-ss/sd-scripts#installation) | Scripts CLI para SD 1.x/2.x/SDXL y varios modelos; LoRA vía `sdxl_train_network.py`/`train_network.py`; actualizaciones de código/documentación a 2026. | Control claro del config y dataset TOML, scripts especializados, cache latents/encoder, bucket, checkpointing, mixed precision, optimizer options, salida safetensors. Buen ajuste para una receta reproducible/externa. | Requiere entorno Python/PyTorch compatible; docs actuales piden PyTorch 2.6+ y sus instrucciones ofrecen Python 3.10, indican 3.11/3.12 también puede funcionar. xFormers es opcional pero binariamente delicado. Bitsandbytes es dependencia opcional/optimizer y compatibilidad Windows debe verificarse; la misma documentación dice SDXL LoRA 8 GB piso práctico / 10 GB sugeridos. FP8/fused-backward se identifican experimentales. | **Primera opción técnica recomendada**, en entorno nuevo y GPU externa. También mejor candidato de un test local aislado posterior si se autoriza. |
| **Hugging Face Diffusers examples** — [LoRA](https://huggingface.co/docs/diffusers/main/en/training/lora), [SDXL](https://huggingface.co/docs/diffusers/main/en/training/sdxl) | Proyecto oficial Hugging Face; ejemplos de entrenamiento LoRA con PEFT y SDXL. | Código fuente/documentación de primera parte, fácil de adaptar, configuración transparente, familiar si se desea integrar scripts Python. SDXL recomienda mixed precision, gradient checkpointing, acumulación y optimizador 8-bit si está disponible. | Es un ejemplo de referencia, no una GUI/wizard; exige instalar versiones compatibles de Diffusers, Transformers, Accelerate, PEFT y extras del ejemplo. La guía señala gran presión de memoria para SDXL incluso en GPU de consumo y precomputación/cache text/latents tiene efectos en captions/entrenamiento. Requiere más ingeniería y validación que sd-scripts para este flujo. | Alternativa sólida si el equipo quiere mantener un pipeline Python propio; no la elijo para primera evaluación por carga de integración. |
| **OneTrainer** — [repo](https://github.com/Nerogar/OneTrainer), [documentación](https://github.com/Nerogar/OneTrainer/tree/master/docs) | Herramienta GUI/CLI multiarquitectura; lista SD 1.5 y SDXL LoRA. Repositorio consultado con actividad en 2026. | GUI para dataset/concepts, entrenamiento, muestras, backups y LoRA; ayuda a operador sin preparar tantas CLI. Python soportado por README actual es >=3.10 y <3.14 (verificar revisión concreta). | Proyecto más amplio y con su propio stack/config. Instalador puede crear/alterar su entorno, cosa que debe hacerse fuera de `E:\AI\ComfyUI` y `.sd_env`. La información pública promociona “desde 8 GB”; no valida 6 GB en este sistema. Debe fijarse commit/revisión y verificar rollback/export antes de producción. | Candidato alternativo para facilidad de uso; no aporta ventaja de calidad sobre trainer y no elimina el límite de VRAM. |

**Nota sobre Windows:** entrenamiento SDXL no es una función estándar del ComfyUI que ya está en la máquina. ComfyUI carga/aplica LoRAs mediante nodos, pero `E:\AI\ComfyUI\models\loras` está vacío salvo un marcador. ComfyUI contiene módulos/nodos LoRA internos, pero no se encontró un flujo de entrenamiento LoRA SDXL mantenido/instalado. No instalar custom nodes en el ComfyUI existente.

## 5. Recomendación técnica única

### Elegir SDXL LoRA externo + `sd-scripts` en entorno efímero pinneado

Fundamentos:

1. **Fidelidad de base:** el objetivo es escenario anime pixel art panorámico, con arquitectura, profundidad y luz. SDXL permite conservar contexto compositivo más amplio que la ruta SD1.5 de 512; la salida final 1280×720 se compone y remuestrea al formato final sin obligar al entrenamiento a 1280×720.
2. **Continuidad de generación:** la biblioteca local contiene SDXL Base, Animagine XL y Sprite Shaper; un LoRA SDXL es aplicable a la familia/checkpoint compatible de su entrenamiento. Una LoRA SD1.5 no sirve directamente en SDXL.
3. **Estabilidad del entorno:** entrenamiento fuera de la RTX compartida con ComfyUI/escritorio, sin tocar servicios, CUDA ni entornos existentes.
4. **Reproducibilidad:** `sd-scripts` ofrece CLI/config TOML, gestión de dataset y argumentos explícitos para precision, checkpointing, caches y checkpoints/samples. Registrar commit y versiones aporta una ruta de repetición.
5. **Capacidad con margen:** 24 GB o más para un primer smoke test reduce el riesgo operativo respecto de 6 GB. No significa que toda config/resolución quepa automáticamente.

**Riesgos:** coste/cupo, subir dataset a tercero, retención de arte, términos del servicio, disponibilidad de GPU/driver, diferencia de versiones ComfyUI vs trainer, variabilidad de licencia del checkpoint, sobreajuste por solo 40–60 imágenes y pérdida de detalle por resolución baja. Mitigar con entorno temporal, no publicar dataset, comprobar borrado, fijar base/commit, snapshots/prompt seeds y comparación ciega de muestras. Si la privacidad impide GPU externa, la segunda decisión sería evaluar SD1.5 local como prueba de proceso o pedir acceso a hardware local de 12+ GB; no recomendaría asumir SDXL training estable en los 6 GB actuales.

## 6. Experimento mínimo propuesto (no ejecutar sin autorización)

### Propósito y límite

Comprobar que el toolchain puede leer el checkpoint, cachear imágenes/captions, entrenar algunas decenas de pasos sin OOM/NaN, guardar una LoRA y cargarla para generar muestras. No se usa para juzgar calidad definitiva ni se integra al juego.

### Preparación del piloto

- **Ejecutor:** máquina GPU externa temporal, Linux o Windows según imagen/compatibilidad del trainer; GPU dedicada 24 GB VRAM recomendada. 16 GB es alternativa condicional si se mantiene U-Net-only y resolución reducida. No usar la GPU local ni el venv local en esta primera propuesta.
- **Herramienta:** checkout aislado de `kohya-ss/sd-scripts`, commit exacto fijado en manifiesto; venv propio desechable; versiones de Python/PyTorch/CUDA/dependencias conforme a la revisión elegida. No usar `pip install`/upgrade global. No ejecutar ComfyUI en esa máquina simultáneamente.
- **Modelo:** SDXL Base 1.0 u otro checkpoint con licencia aprobada, idéntico en entrenamiento e inferencia; registrar SHA-256 y procedencia. Para primer control, preferir base estándar antes de evaluar Animagine/Sprite Shaper como otro experimento separado.
- **Dataset piloto:** 4–6 imágenes propias/con licencia de los tipos salón de torneo, bosque lluvioso y sala del trono, con variación ambiental. Verificar derechos antes de cualquier upload. Usar captions manuales cortos, token `cmd_pixelanime_bg`, sin retratos/personajes principales/cartas ni scanlines horneadas. No usar capturas del juego como fuente sin aprobación.
- **Resolución:** bucket horizontal 768×448 (si la documentación/config del commit lo admite y el tamaño exacto se mapea a bucket). Una futura prueba de producción compara con bucket SDXL cercano a 1024×576. No generar 1280×720 durante el smoke test.
- **Entrenamiento:** LoRA de U-Net solamente; text encoders frozen y cache de embeddings si se habilita compatible con captions fijos; FP16 mixed precision; batch size 1; gradient checkpointing; cache latents a disco; bucket de aspect ratio; rank 4 u 8, alpha igual o half rank según prueba; sin full-fp16, FP8, fused backward, DreamBooth ni entrenamiento de text encoder. Para optimizer: empezar con AdamW estándar solo si cabe; de lo contrario Adafactor integrado (config documentada y registrada). No presuponer bitsandbytes/xFormers; se pueden activar solo si ya están disponibles, validados en esa imagen y se registra el cambio.
- **Duración acotada:** 50–100 optimizer steps con interrupción automática/cupo máximo; guardar LoRA inicial y final, log y muestra. El paso corto prueba la tubería, no la convergencia estética.
- **Muestras fijas:** prompts para los 3 escenarios + una cuarta ubicación no presente en el piloto, siempre con mismo sampler/steps/CFG/seed y settings base/LoRA al mismo peso. Evaluar grilla de píxel, coherencia, composición, estilo común, fidelidad del lugar, artefactos y legibilidad con una caja/avatar de prueba separado (sin modificar archivos del juego).

### Estimaciones de consumo — hipótesis, no benchmark

Los requisitos dependen de checkpoint, backend de atención, bucket real, optimizer, proceso gráfico y versiones. No hay cifra exacta fiable hasta medir en la instancia elegida.

| Configuración hipotética | Pico que presupuestaría | Lectura |
|---|---:|---|
| SDXL LoRA externo, 768×448, batch 1, UNet only, FP16 + checkpointing + cache | aproximadamente **9–16 GiB** VRAM, con picos temporales al cargar/modelar/muestrear | Rango de planificación amplio; no promesa de que cualquier trainer/config quepa. Recomiendo GPU de 24 GiB para holgura y evitar out-of-memory de escritorio. |
| Igual en GPU externa 16 GiB | podría caber con configuración reducida, pero el margen es menor | Medir pico y dejar reserva para SO/driver. Evitar sample generation simultánea en la misma tarjeta si provoca pico combinado. |
| SDXL local en RTX 2060 6 GB, escritorio activo | 6 GiB totales, con solo ~5 GiB libres en la foto de `nvidia-smi` | **No hay margen confiable**; probable OOM al cargar/backward/sampling. Aun con 512/640px debe tratarse como experimento riesgoso, no plan de producción. |
| SD 1.5 LoRA local, 512px, batch 1, FP16/optimizer pequeño | por diseño significativamente menor que SDXL, a menudo dentro de la clase 4–6 GiB | Puede aproximarse al límite por escritorio/modelo/optimizer; no se midió aquí. La menor VRAM no compensa automáticamente la diferencia de calidad/formato. |

No se presupuestó RAM o disco porque no se midieron. Antes de aprobar la prueba deben confirmarse RAM disponible, espacio temporal/checkpoints/dataset y coste/cupo máximo de la GPU externa. La generación de muestras puede provocar picos separados y debe ejecutarse luego de entrenamiento o en otra GPU.

### Criterios de éxito

1. El trainer reconoce la GPU externa, modelo y configuración sin modificar el checkpoint ni instalar en otra máquina de desarrollo.
2. Pre-cache y al menos 50 steps terminan sin CUDA OOM, NaN/Inf persistentes ni errores de dataloader.
3. El archivo LoRA se guarda en safetensors y el hash/config/commit/base/dataset/captions quedan asociados.
4. LoRA carga en una copia de inferencia compatible del mismo checkpoint y produce salida distinta del baseline sin romper generación.
5. Los prompts de prueba retienen ambientes concretos y al menos una señal visible de lenguaje común de pixel art anime entre los 3 pilotos; no aparece personaje protagonista, texto/UI ni CRT/scanline agresiva no pedida.
6. Una escena nueva no vista no colapsa en la composición de una sola imagen de entrenamiento. Si sí colapsa, revisar diversidad/captions antes de ampliar dataset.
7. Se exportan muestras/logs y se verifica el borrado de datos de la instancia/proveedor. No se integra el LoRA ni los fondos en el juego.

El criterio 5–6 requiere revisión humana, no solo automatización. 50–100 steps no permiten aprobar el estilo final; únicamente justifican pasar a curación del dataset completo y una primera corrida de ajuste controlada.

### Recuperación ante OOM / error

1. Guardar log, último estado/checkpoint si existe y configuración exacta; no reanudar con settings cambiados como si fueran equivalentes.
2. Confirmar que no hay otros procesos usando GPU; cerrar generación de muestras simultánea y reiniciar worker solo si la instancia está aislada. No cerrar ni modificar ComfyUI local.
3. Reintentar en GPU externa, desde un estado limpio, con batch 1 (ya debe estar), gradient checkpointing, solo U-Net y cache a disco. Confirmar attention backend sin xFormers si no está validado.
4. Reducir bucket 768×448 a **640×384** o siguiente bucket horizontal cercano permitido por SDXL/trainer; conservar aspect ratio y comparar si aún mantiene estructura de pixel art. No cambiar a cuadrado como solución por defecto.
5. Bajar rank 8→4 y desactivar generación de muestras durante los pasos; mantener una muestra final después. Si optimizer es el cuello, Adafactor documentado/estable antes que optimización fused experimental.
6. Si aún falla, detener prueba. No continuar reduciendo silenciosamente a resoluciones que ya no sirven al objetivo. Cambiar a 24–48 GB GPU externa o abrir decisión aparte para SD1.5/local. Preservar artefactos de error y cerrar/eliminar instancia después de recuperar logs permitidos.

## 7. Procedimiento para decisión/aprobación

Antes de ejecutar, solicitar aprobación separada para:

1. proveedor/región/tarifa y techo de gasto/cupo; 2) compartir temporalmente el dataset seleccionado; 3) modelo base y licencia; 4) trainer/commit; 5) entorno externo desechable; 6) prueba de 4–6 imágenes/50–100 pasos y política de borrar datos; 7) revisión de outputs. Esta respuesta no autoriza ninguno de esos pasos.

## Fuentes y alcance

### Fuentes primarias consultadas

- [`kohya-ss/sd-scripts`: guía avanzada SDXL LoRA](https://github.com/kohya-ss/sd-scripts/blob/main/docs/train_network_advanced.md) — flags, cache, optimizer, mixed precision, checkpointing y advertencia VRAM.
- [`kohya-ss/sd-scripts`: guía de entrenamiento SDXL LoRA](https://github.com/kohya-ss/sd-scripts/blob/main/docs/sdxl_train_network.md) — U-Net only, buckets y memoria.
- [`kohya-ss/sd-scripts`: README / instalación Windows](https://github.com/kohya-ss/sd-scripts) — matriz de versiones y dependencias; fijar revisión al iniciar.
- [Hugging Face Diffusers — entrenamiento LoRA](https://huggingface.co/docs/diffusers/main/en/training/lora) y [SDXL](https://huggingface.co/docs/diffusers/main/en/training/sdxl) — PEFT, scripts de referencia y optimizaciones SDXL.
- [`Nerogar/OneTrainer`](https://github.com/Nerogar/OneTrainer) — soporte de modelos/métodos y requisitos actuales de Python; revisar los requisitos de GPU del commit concreto.
- Evidencia local del proyecto anterior: `docs/preparacion_visual_lora_y_cinematicas.md`; `E:\AI\README_COMFYUI.md`; `E:\openCode\.gitignore`; `generar_escenas.py`; `estilo_escenas.py`; `estilo/escenas.json`; `estilo/ESTILO.md`; `cinematicas.py`; `ui.py`.

### Límites de la evaluación

Las cifras de VRAM para el piloto se declaran como hipótesis de planificación, no como benchmarks. No se inspeccionó el estado de RAM/disco/coste de proveedores ni se validó que una versión concreta de OneTrainer/sd-scripts funcione en una VM determinada. Esos puntos son puertas del procedimiento de prueba y deberán verificarse antes de gastar o subir datos.
