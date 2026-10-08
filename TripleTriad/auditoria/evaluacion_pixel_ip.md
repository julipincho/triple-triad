## Coherencia con la ficha

*   **Variante `pixel_ip`**: **7/10**. Excelente ejecución técnica de la paleta, iluminación de tres cuartos y tramado impecable, pero incumple la ficha al ignorar la diversidad de los sujetos (todos los personajes comparten el mismo rostro humano).
*   **Variante `crt_viejo`**: **5/10**. Cumple con la variedad de sujetos y siluetas de fantasía, pero la paleta se desvía con tonos demasiado saturados (como el verde del goblin) y el tramado es menos limpio.

---

## Legibilidad en juego

*   **Variante `pixel_ip`**: Los rostros son nítidos y los scanlines no estorban. Sin embargo, la legibilidad en tablero es nula porque el jugador no podrá diferenciar las cartas a primera vista al ser retratos casi idénticos.
*   **Variante `crt_viejo`**: Alta legibilidad por silueta y color. Los personajes se distinguen al instante, aunque el rostro de la pantera y el dragón se pierden ligeramente debido a un tramado más caótico.

---

## Problemas concretos

*   **Monotonía facial (`pixel_ip`)**: El IP-Adapter anula el prompt de sujeto; el orco, la pantera y el brujo tienen la misma cara de guerrero humano.
*   **Saturación prohibida (`crt_viejo`)**: El "brujo verde" rompe la norma de la paleta apagada con un tono verde demasiado brillante.
*   **Ruido visual (`crt_viejo`)**: El dithering en el dragón y la pantera ensucia la lectura del personaje a tamaño real.

---

## Recomendación

*   **Veredicto**: El nuevo pipeline (`pixel_ip`) es un **paso adelante** en calidad técnica (píxel, luz y color excelentes), pero un **paso atrás** en dirección de arte por la pérdida de variedad.
*   **Cambios concretos**: Mantener el nuevo checkpoint (`pixel_ip`) pero **bajar el peso del IP-Adapter de 0.8 a 0.35** para que el prompt vuelva a mandar sobre la morfología del personaje (goblins, orcos, felinos) sin perder la cohesión de color.
*   **Descarte**: No utilizar la fila `pixel_ip` actual con peso 0.8; la falta de variedad de personajes arruina la experiencia de juego.
