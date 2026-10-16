# Plan principal — Cartones y Mazmorras 2.1

Plan aprobado el 16 de octubre de 2026. Base: versión 2.0 publicada y corrección web R2 confirmada por el usuario. Desarrollo nuevo en la rama `v2.1`.

## Alcance

Pulir la jugabilidad y la narrativa existentes, sin agregar funcionalidades ni sistemas. Mantener el objetivo de 60 FPS, la alineación del puntero y la estabilidad de Windows y web. Conservar el arte de las cartas y las escenas ya aprobadas. Los cambios de balance se harán sobre valores, efectos y distribución existentes, con justificación y comprobaciones.

## Los 12 frentes

Primera pasada de los apartados 1, 2 y 3 implementada en el bloque 01, ampliada con consecuencias de duelos y minicampañas en el bloque 02 y ritmo del prólogo en el bloque 03; los frentes completos siguen en curso. Ver [bloque 01](informe_v2_1_bloque_01.md), [bloque 02](informe_v2_1_bloque_02.md), [bloque 03 y auditoría](informe_v2_1_bloque_03.md) y [guía de continuidad](continuidad_v2_1.md). Cada frente se cerrará con cambios concretos, comprobación y un informe de lo realizado.

1. **Intención de cada duelo.** Revisar los diálogos previos para expresar qué quiere el rival y qué se juega el protagonista; conectar la victoria con ese conflicto.
2. **Ritmo del comienzo.** Reducir explicaciones repetidas y presentar las reglas cuando se utilizan. Comprobar que el primer duelo sea comprensible y despierte curiosidad.
3. **Legibilidad de las jugadas.** Ajustar pausas, animaciones y mensajes existentes para distinguir colocación, efecto y captura, y entender los cambios del tablero.
4. **Personalidad de los rivales.** Revisar mazos y decisiones para que cada facción tenga una forma de jugar reconocible con las mecánicas actuales.
5. **Progresión de dificultad.** Revisar los saltos entre encuentros: enseñar, exigir y combinar lo aprendido sin picos injustificados.
6. **Peso de las decisiones de ruta.** Comunicar lo que está en juego en cada opción y reconocer después sus consecuencias actuales, sin prometer resultados que no existen.
7. **Voz de los personajes.** Diferenciar vocabulario, humor, longitud de las frases y actitud; hacer reconocibles a Nara y a los rivales por sus intervenciones.
8. **Continuidad emocional del protagonista.** Reforzar su evolución mediante las intervenciones existentes: desconcierto, confianza, dudas y determinación.
9. **Cartas y recompensas poco atractivas.** Revisar valores, efectos y distribución para reducir elecciones obvias y ofrecer alternativas útiles, sin cambiar el arte ni sumar mecánicas.
10. **Derrotas.** Pulir textos y ritmo del regreso para invitar a reintentar y aprovechar la información existente que ayuda a comprender lo ocurrido.
11. **Cierre de encuentros importantes.** Revisar diálogos posteriores para responder a lo ocurrido, avanzar las relaciones y evitar desenlaces genéricos.
12. **Redacción uniforme.** Revisar ortografía, nombres, términos de reglas y longitud de textos; usar una denominación consistente para cada acción.

## Orden de trabajo

Empezar por los frentes 3, 2 y 4: claridad de jugadas, ritmo inicial y personalidad de rivales. Continuar con dificultad y elecciones (5, 9, 6), después continuidad narrativa (1, 7, 8, 10, 11). Revisar redacción (12) durante cada pasada y al cierre.

Antes de modificar cada frente, revisar el comportamiento o texto actual y registrar los problemas observados. Evitar cambios de balance o ritmo basados únicamente en supuestos. Comprobar los recorridos afectados y ejecutar las pruebas pertinentes.

## Punto de partida verificado

- Suite de 1078 pruebas pasada para la entrega 2.0 R2.
- Chrome local: alrededor de 60 FPS, clics y arrastre comprobados dentro de un iframe.
- El usuario confirmó que el problema del puntero quedó resuelto tras reemplazar el paquete publicado.
- Entrega local conservada en `ver2SubirV2`; los ZIP se excluyen de Git por su tamaño. Se conservan las portadas, instrucciones y registros de verificación.

La numeración pública sigue en 2.0 hasta preparar una entrega 2.1; crear la rama no equivale a publicar una nueva versión.
