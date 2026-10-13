# CARTONES Y MAZMORRAS
## Biblia Visual Maestra — V1.0
**Proyecto:** Entrenamiento de LoRA de estilo y producción de fondos cinematográficos.

**Objetivo:** Construir una identidad artística original, coherente y reproducible para los escenarios de todo el videojuego.

### 1. Identidad artística

**Estilo principal:** Anime Pixel Art cinematográfico.

**Género:** Fantasía medieval oscura, aventura isekai y misterio sobrenatural.

**Referencias estéticas:** RPG japoneses de los años noventa y principios de los 2000, fondos anime tradicionales, pixel art detallado y presentación visual de consolas retro.

**Sensación buscada:** El jugador debe percibir que está dentro de un mundo de fantasía antiguo, misterioso, hermoso y peligroso.

El arte debe transmitir nostalgia por los videojuegos clásicos sin parecer técnicamente anticuado ni perder legibilidad.

### 2. Lenguaje visual

- Pixel art elaborado, con píxeles reconocibles y bordes intencionales.
- Siluetas arquitectónicas y naturales claramente definidas.
- Sombreado mediante agrupaciones de píxeles, sin depender de degradados fotográficos.
- Iluminación dramática, con fuentes luminosas identificables.
- Profundidad por superposición de planos, niebla y contraste.
- Detalle ambiental medio-alto, especialmente en arquitectura y paisajes.
- Composiciones cinematográficas propias de un RPG narrativo.
- Acabado anime retro, evitando trazos excesivamente modernos o realistas.

**Evitar:** Imágenes 3D, pintura digital hiperrealista, aspecto de arte generado genérico, superficies plásticas, fondos excesivamente suaves, pixelización artificial sin estructura y elementos visuales que parezcan pertenecer a estilos diferentes.

### 3. Resolución y estructura técnica

**Resolución de entrega obligatoria:** 1280 × 720 píxeles.

**Relación de aspecto:** 16:9.

**Formato:** PNG sin pérdida.

**Profundidad:** RGB/RGBA de 8 bits por canal.

**Resolución artística de referencia recomendada:** 640 × 360, ampliada exactamente 2× mediante nearest-neighbor cuando se utilice el tratamiento de cuadrícula de píxeles.

La generación y el entrenamiento del LoRA podrán trabajar con otras resoluciones. La resolución de entrenamiento no determina por sí sola la resolución final.

Los fondos deberán conservar una escala de píxel visualmente consistente. No se utilizarán escalados bilineales que difuminen el pixel art.

**Importante:** El motor actual trabaja con una superficie lógica de 1280 × 800. La integración deberá adaptar la presentación de cinemáticas a un encuadre 16:9 de 1280 × 720, sin deformar los escenarios ni modificar involuntariamente la interfaz del juego.

### 4. Color y atmósfera

La paleta será coherente entre escenarios, pero no idéntica en todas las localizaciones.

**Colores estructurales recomendados:**

| Color | Código | Función |
|---|---|---|
| Azul medianoche | #151D2C | Sombras y profundidad |
| Azul pizarra | #34465B | Arquitectura, piedra y entornos |
| Azul lluvia | #54748A | Bosques, niebla y ambientes fríos |
| Dorado antiguo | #C59A57 | Antorchas, reinos y luces cálidas |
| Granate oscuro | #763B4F | Peligro, guerra y corrupción |
| Violeta arcano | #8066B8 | Magia, Umbral y fenómenos sobrenaturales |
| Marfil envejecido | #D8CEB9 | Reflejos y elementos destacados |

Estos colores son una propuesta inicial, no una limitación absoluta.

**Principio de color:** Usar sombras profundas, luces focalizadas y colores controlados. Evitar saturación elevada en toda la imagen.

### 5. Iluminación

La iluminación deberá comunicar la situación narrativa.

**Mundo real:** Iluminación artificial, focos de escenario, reflejos y contrastes propios de un torneo contemporáneo.

**Mundo fantástico:** Antorchas, luna, amanecer, luz atravesando árboles, niebla iluminada y fuentes mágicas.

**Umbral:** Luz antinatural, reflejos violetas o azulados, contraste extremo y sensación de ruptura dimensional.

**Finales:** Tratamientos luminosos diferenciados según dominio, equilibrio y caos, manteniendo la misma identidad artística.

Se evitará utilizar efectos de glow intensos en todos los escenarios.

### 6. Composición cinematográfica

- Cámara horizontal de encuadre amplio.
- Escenarios con profundidad perceptible.
- Elemento narrativo principal visible y reconocible.
- Horizonte y perspectiva controlados.
- Composición equilibrada entre espacios vacíos y detalle.
- Reservar aproximadamente el tercio inferior para la superposición de diálogos, ajustándolo a la interfaz real.
- Evitar información narrativa imprescindible detrás de retratos o paneles.
- No incorporar tipografía, indicadores, marcos o elementos de interfaz dentro de los fondos.
- Evitar personajes principales incrustados en el escenario.

Se permitirán siluetas lejanas o multitudes ambientales cuando el lugar lo requiera, como en el público del torneo, siempre que no sustituyan los retratos del juego.

### 7. Diferenciación entre mundos

**A. Mundo real**

Debe transmitir contemporaneidad mediante arquitectura, dispositivos de iluminación, pantallas y elementos del torneo, pero conservar la misma técnica de pixel art anime.

El mundo real no debe parecer un videojuego completamente distinto.

**B. Mundo fantástico**

Ambientación medieval de fantasía oscura. Bosques húmedos, asentamientos, ruinas, ceniza, fortalezas, banderas y arquitectura monumental.

La magia debe estar integrada al entorno, no colocada como un efecto decorativo arbitrario.

**C. Umbral y espacio sobrenatural**

El Umbral tendrá un lenguaje reconocible: geometría de nueve casillas cuando corresponda, símbolos arcanos, luz dimensional y una atmósfera distinta a la magia ordinaria.

Su representación deberá seguir lo establecido por la narrativa y no anticipar revelaciones futuras.

### 8. Tratamiento CRT

El efecto de televisión de tubo será parte de la identidad de presentación, preferentemente como postprocesamiento configurable.

Características:
- Scanlines sutiles.
- Ligera suavidad luminosa.
- Bloom moderado en luces.
- Aberración cromática mínima, si se utiliza.
- Conservación de la lectura de los píxeles.

**Regla:** El entrenamiento aprenderá principalmente la identidad anime pixel art. No se incorporarán scanlines pronunciadas a cada imagen del dataset, para evitar artefactos y permitir exportaciones limpias.

### 9. Entrenamiento de IA

**Familia inicial propuesta:** SDXL.

**Tipo:** LoRA de estilo de escenarios.

**Token identificador:** `cmd_pixelanime_bg`.

**Dataset piloto:** 40–60 imágenes curadas con derechos de uso adecuados.

El dataset debe incluir escenarios variados, tanto modernos como fantásticos, representados mediante la misma técnica visual.

El LoRA deberá aprender:
- Estilo y estructura del pixel art.
- Acabado anime retro.
- Tratamiento del color.
- Iluminación.
- Densidad del detalle.
- Profundidad ambiental.
- Consistencia estilística entre localizaciones.

No se entrenarán personajes, retratos ni cartas en esta primera versión.

### 10. Reglas para producir fondos

Cada escenario deberá:
1. Mantener la identidad artística.
2. Respetar el mundo narrativo al que pertenece.
3. Mostrar correctamente la localización descrita.
4. Dejar espacio para la interfaz.
5. Evitar texto o personajes protagonistas incrustados.
6. Mantener la escala de pixel art.
7. Entregarse a 1280 × 720.
8. Pasar una revisión visual antes de integrarse.
9. Contar con un prompt y una semilla registrados.
10. Poder regenerarse utilizando la versión correspondiente del modelo y del LoRA.

### 11. Pruebas de consistencia

**Escenarios piloto:**
- Salón del torneo.
- Bosque lluvioso del despertar.
- Sala del trono.

Los tres deben sentirse como parte del mismo videojuego, aunque uno pertenezca al mundo real.

**Criterios de aprobación:**
- Fidelidad al pixel art anime.
- Coherencia entre escenarios.
- Calidad de composición.
- Integración con diálogos y retratos.
- Fidelidad narrativa.
- Ausencia de artefactos de IA.
- Capacidad de reproducir el estilo con nuevas ubicaciones.

### 12. Principio de sostenibilidad

La identidad del juego no dependerá de un prompt aislado.

Se conservarán versiones del dataset, captions, configuración de entrenamiento, modelo base, LoRA, prompts de generación, semillas y fondos finales.

Los modelos nuevos deberán superar las mismas pruebas de referencia antes de reemplazar una versión estable.

**Regla final:** La consistencia artística de Cartones y Mazmorras tiene prioridad sobre la espectacularidad individual de una imagen.
