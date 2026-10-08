## Coherencia con la ficha

*(Nota: Como la hoja de contactos muestra un lote completo de cartas individuales y no variantes de una misma carta, evaluaremos cada retrato según su fidelidad a la ficha de estilo).*

1. **hombre_lagarto_curandero_viejo:** 8/10. Muy buena paleta y claroscuro, aunque el encuadre es ligeramente más lateral de lo especificado.
2. **hombre_pantera_acechador:** 7/10. Buena atmósfera, pero el tramado en el hocico oscurece demasiado los detalles del primer plano.
3. **orco_pantera_noche_de_caza:** 6/10. Excesivamente oscuro; el brillo medio cae por debajo del objetivo, perdiendo definición en las sombras.
4. **orco_trol_de_ceniza:** 9/10. Excelente uso de la paleta gris/tierra, iluminación de tres cuartos perfecta y silueta contundente.
5. **hombre_lobo_luna_llen:** 8/10. Buen contraste con la luna de fondo, aunque la textura del pelaje roza el límite del dithering sucio.
6. **vampiro_sangre_joven:** 5/10. **Incumplimiento crítico**: Las facciones y el sombreado rozan la pintura digital suave; faltan los bordes de píxel afilados y abusa de degradados.
7. **hombre_lagarto_cola_acorazada:** 9/10. Excelente textura de escamas, paleta fiel y contraste óptimo con el negro abisal.
8. **orco_puno_del_cráter:** 8/10. Sólido, expresión severa muy lograda y encuadre de busto correcto.
9. **vampiro_murcielago:** 4/10. **Incumplimiento crítico**: Encuadre totalmente abierto (plano entero/lejano), rompiendo por completo la norma de busto en primer plano.
10. **humano_arquera_de_torre:** 3/10. **Incumplimiento crítico**: Plano general de trono lejano; el personaje es diminuto y pierde toda legibilidad como retrato.
11. **dragon_cola_ferrea:** 9/10. Gran uso del rojo terracota y luces altas; el detalle en los cuernos cumple perfectamente con el canon.
12. **goblin_madre_rata:** 8/10. Expresión amenazante bien capturada, buen contraste y texturas rugosas acertadas.
13. **humano_ariete_del_alba:** 8/10. Simetría y encuadre correctos, paleta sobria bien aplicada.
14. **elfo_arco_corto:** 5/10. Plano demasiado abierto para una carta de este tamaño; el personaje queda relegado al fondo.
15. **hombre_lobo_madre_luna:** 8/10. Impactante, buen uso de luces de recorte y paleta oscura equilibrada.
16. **goblin_mordedor:** 9/10. De lo mejor del lote: rostros afilados, alto contraste y perfecta densidad de píxel.
17. **dragon_fuego:** 7/10. El foco de fuego frontal satura un poco la zona izquierda, pero respeta la paleta general.
18. **elfo_nocturno_susurro:** 8/10. Los acentos azules abismo y gris arena funcionan muy bien para definir la silueta.

---

## Legibilidad en juego

* **Se distingue el personaje?:** En la gran mayoría sí, gracias al fuerte contraste de las siluetas. Sin embargo, en cartas con planos abiertos (`vampiro_murcielago`, `humano_arquera_de_torre`, `elfo_arco_corto`), el personaje desaparece por completo a tamaño real en tablero.
* **Se pierde el rostro en el tramado?:** Ocurre puntualmente en los retratos más oscuros (`orco_pantera_noche_de_caza`, `hombre_pantera_acechador`), donde el dithering densificado funde los ojos y facciones con las sombras profundas.
* **Los scanlines ayudan o estorban?:** Ayudan enormemente a unificar la estética CRT retro y tapan la aspereza de la IA, salvo en las cartas con rostros más suaves (`vampiro_sangre_joven`), donde chocan con la falta de píxeles nativos duros.

---

## Problemas concretos

1. **Planos demasiado abiertos:** Múltiples cartas (`vampiro_murcielago`, `humano_arquera_de_torre`, `elfo_arco_corto`) ignoran la regla del busto y muestran cuerpos enteros o arquitectura lejana.
2. **Pérdida de definición facial:** El tramado excesivo en personajes de tonos oscuros (`orco_pantera_noche_de_caza`) traga los ojos y expresiones.
3. **Inconsistencia de estilo:** `vampiro_sangre_joven` presenta un acabado de pintura digital suave que contradice la textura pixelada rugosa del resto del set.

---

## Recomendacion

* **Mejor variante global:** `goblin_mordedor` (o `orco_trol_de_ceniza`). Porque clavan el encuadre de busto, mantienen la paleta oscura sin perder legibilidad, tienen un tramado excelente y una iluminación dramática sobresaliente.
* **Cambios concretos de parámetros:** 
  * Forzar en el prompt de generación un peso mayor para los términos de encuadre (`close-up bust portrait, head and shoulders`).
  * Elevar ligeramente el brillo (+5%) en los personajes de pelaje negro/pantera para recuperar los ojos.
  * Mantener el checkpoint actual pero aplicar un filtro de posterización más duro para evitar los suavizados tipo `vampiro_sangre_joven`.
* **Cartas que NO deberían usarse:** `vampiro_murcielago`, `humano_arquera_de_torre` y `elfo_arco_corto`. Incumplen frontalmente el encuadre obligatorio de busto y son injugables a 56x79 píxeles.

---

vampiro_murcielago, humano_arquera_de_torre, elfo_arco_corto
