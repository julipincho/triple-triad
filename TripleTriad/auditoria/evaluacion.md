## Coherencia con la ficha

*   **original (Nota: 3/10):** Incumple la ficha al presentar arte digital moderno con degradados suaves, colores sobresaturados y total ausencia de pixel art o scanlines.
*   **crt (Nota: 7/10):** Excelente fidelidad. Presenta la textura CRT, scanlines horizontales marcadas, paleta de color apagada y el sombreado dramático requerido.
*   **sin_scanlines (Nota: 6/10):** Buena adaptación de paleta y pixelado, pero la ausencia total de scanlines viola un pilar técnico de la ficha.
*   **dither_fs (Nota: 4/10):** El tramado Floyd-Steinberg es demasiado ruidoso y disperso, ensuciando la textura y eliminando la atmósfera de monitor analógico.

## Legibilidad en juego

*   **original:** Alta legibilidad por su naturaleza de alta resolución, pero destruye la coherencia estética en el tablero.
*   **crt:** Legibilidad media-alta. Los personajes se distinguen bien; las líneas de escaneo aportan la textura retro necesaria sin llegar a tapar las facciones principales.
*   **sin_scanlines:** La más legible dentro del estilo pixel art, al no tener la interferencia de las líneas horizontales sobre los ojos.
*   **dither_fs:** Legibilidad baja. El tramado tan disperso hace que los rostros pequeños (como "ala rota" o "archivista") pierdan definición y parezcan sucios.

## Problemas concretos

*   **Pérdida de contraste:** En "aplastador" (variantes pixel), el personaje oscuro se funde excesivamente con el fondo.
*   **Ruido facial:** El tramado en `dither_fs` destruye los ojos y rasgos finos de los personajes femeninos.
*   **Exceso de saturación:** La fila `original` rompe la paleta de la ficha con tonos neón y fondos demasiado brillantes.

## Recomendacion

*   **Mejor variante global:** **crt**. Es la única que cumple simultáneamente con el pixel art, la paleta apagada y la textura de monitor analógico solicitada.
*   **Cambios de parámetros:** Incrementar el brillo general un 10% para compensar la pérdida de luz de las scanlines, y reducir la opacidad de estas últimas un 15% para limpiar los rostros en tamaño miniatura.
*   **Variantes a descartar:** Descartar por completo `original` (fuera de estilo) y `dither_fs` (ruido excesivo no apto para baja resolución).
