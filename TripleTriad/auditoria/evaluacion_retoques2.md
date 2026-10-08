## Coherencia con la ficha

- **Variante "retoques" (Nota: 5/10):** Paleta y textura CRT acordes a la norma, pero los encuadres son excesivamente abiertos (planos medios y enteros con atrezo) en lugar de bustos cerrados.
- **Variante "anterior" (Nota: 6/10):** Respeta mejor el primer plano dramático y el claroscuro en dos de las tres cartas, aunque el orco falló en escala y silueta.

## Legibilidad en juego

A escala de 56x79 píxeles:
- **retoques:** Los personajes pierden protagonismo al incluir tronos, escaleras y mesas; los rostros de humano y orco quedan reducidos a pocos píxeles y se confunden con el dithering. Las scanlines son correctas, pero la escala del sujeto perjudica la lectura.
- **anterior:** El alabardero y la vampiresa presentan rostros grandes y lectura inmediata; el orco fracasa totalmente al ser una masa oscura de cuerpo entero.

## Problemas concretos

- **Encuadre no corregido en orco:** `orco_aplastador` sigue mostrándose de cuerpo completo (en cuclillas sobre escalones).
- **Apertura de plano innecesaria:** `humano_alabardero` y `vampiro_alas_negras` pasaron a plano medio con atrezo (trono, mesa, vela), restando píxeles vitales al rostro.
- **Pérdida de foco facial:** Rostros de menos de 12 píxeles de alto en `alabardero` y `aplastador`, empastados por el tramado.

## Recomendacion

- **Evaluación de las 3 cartas:** 
  - *Sin marcos parásitos:* **Cumple** (se eliminaron con éxito).
  - *Busto cerrado:* **No cumple** (las 3 siguen en plano medio o entero).
  - *Rostro legible a 56x79:* **Cumple parcial** (solo la vampira retiene legibilidad mínima; humano y orco no).
- **Mejor variante global:** Ninguna de las dos filas resuelve el trío al completo; la fila "anterior" ofrecía mejor escala de retrato (salvo el orco), mientras que "retoques" solventa artefactos pero aleja la cámara.
- **Ajustes:** Forzar en prompt `extreme close-up face portrait, head and shoulders only`, descartando términos de entorno (`sitting`, `throne`, `steps`, `table`).
- **Veredicto para compilar el .exe:** **No autorizar la compilación**. Si las 250 cartas presentan la inconsistencia de plano de la fila "retoques", el juego perderá impacto visual en mesa. Requiere forzar busto cerrado estricto.
