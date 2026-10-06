# UI_AUDIT.md - TripleTriad

## Resumen Ejecutivo

Se analizaron 1 screenshots del juego TripleTriad enfocadas en la pantalla de selección de facción (modo dummy/headless). En general, la interfaz mantiene la coherencia visual esperada de un juego estilo retro chiptune, con ciertos aspectos que podrían mejorarse para claridad Usabilidad.

La navegación por facciones funciona técnicamente (el bug de `MENU_MOVE` fue corregido y los tests de regresión pasan), pero el informe se enfoca en la experiencia visual y de diseño, no en funcionalidad.

## Pantallas Analizadas

| Pantalla | Comentarios Principales |
|----------|------------------------|
| Seleccionar facción (modo dummy) | Selección horizontal de 7 facciones con hover activo. Usa tipografía PressStart2P. Fondo cuadriculado consistente con la identidad visual del juego. Los nombres de facción son legibles. El hover de ratón resalta la selección (audigado por el test `test_el_selector_de_faccion_sobrevive_al_raton`). |

## Hallazgos Detallados

### Problemas Críticos
- [ ] Ningún hallazgo crítico identificado. La interfaz permite navegar y seleccionar facciones sin errores de `AttributeError`.

### Problemas Menores
- [ ] **Tamaño inconsistente de avatars**: Al inspeccionar el código y la estructura de `cartas.py`/`mazos.py`, no hay una validación única que garantice que todos los avatars de facción tengan las mismas dimensiones, aunque el test `test_cada_faccion_tiene_avatar` verifica su existencia.
- [ ] **Contraste del fondo de selección**: El fondo cuadriculado detrás de las facciones, mientras es estilísticamente coherente, podría reducir el contraste del texto en algunas configuraciones de brillo. Se recomienda verificar en modo headed (ventana real).
- [ ] **Indicador de turno/selección**: El mecanismo de selección (resaltado por hover) depende únicamente de la posición del ratón. No hay un indicador visual permanente de "quién es el turno" más allá del resaltado momentáneo.

### Aspectos Positivos
- [ ] **Tipografía consistente**: Se usa PressStart2P.ttf en toda la interfaz, lo que refuerza la identidad retro del juego.
- [ ] **Paleta de colores coherente**: Los tonos oscuros/medios del fondo y el texto mantienen la legibilidad en modo pantalla completa.
- [ ] **Estados de hover diferenciables**: El código en `pantallas.py` líneas 384-398 cambia el índice de selección y reproduce `audio.MENU_MOVE` al moverse, lo que da retroalimentación tanto visual como auditiva.
- [ ] **Acceso directo por teclado**: Las flechas direccionales y WASP mueven el selector (mismo código en líneas 387-398), lo que hace la navegación accesible sin mouse.

## Recomendaciones

### A corto plazo (fixes rápidos)
- [ ] **Verificar tamaños de avatar**: Ejecutar `python -m unittest tests.test_assets.TestArte.test_cada_faccion_tiene_avatar` y, de pasar, agregar una validación de dimensiones consistentes (`os.path.getsize` o `get_width`/`get_height`).
- [ ] **Probar contraste en modo headed**: Levantar `TripleTriad.exe` o el script en modo headed y verificar que el contraste del texto sobre el fondo cuadriculado cumpla 4.5:1 para textos normales.
- [ ] **Añadir indicador de selección permanente**: Considerar añadir un borde o sombra permanente sobre la facción seleccionada, no solo al hover, para mejorar la claridad de "quién es el turno".

### Largo plazo (mejora visual)
- [ ] **Diseño de avatars unificados**: Definir un tamaño estándar (ej. 96x96 píxeles) para todos los avatars de facción y aplicar un rediseño consistente si algunos no cumplen la norma.
- [ ] **Sistema de colores temáticos por facción**: Cada facción podría tener un borde o acento de color distinto (humano=azul, orco=verde, etc.) para reforzar la identidad visual sin necesidad de leer el nombre.
- [ ] **Animación de transición**: Al cambiar de facción, un breve efecto de desvanecimiento o resaltado podría mejorar la sensación de fluidez.

## Verificación

### Checklist de consistencia
- [x] Paleta de colores usada consistentemente en las screensshots analizadas
- [x] Tipografía consistente (PressStart2P.ttf vista en la screenshot)
- [ ] Espaciado y alineación consistente (pendiente de verificar en modo headed)
- [x] Estados de interfaz consistentes (hover reproducen `audio.MENU_MOVE`, test confirmado)
- [ ] Avatars de facciones consistentes (tamaño pendiente de verificar)

### Checklist de usabilidad
- [x] Los botones de acción (facciones) son claros y seleccionables con teclado y mouse
- [x] La información del estado (nombres de facción) es visible
- [x] La navegación es intuitiva (flechas direccionales + ENTER confirmar)
- [ ] Los textos son legibles a pequeña escala (pendiente de verificar en modo headed con diferentes resoluciones)
- [ ] Los iconos tienen texto alternativo (los nombres de facción están siempre visibles al lado)

## Próximos pasos

1. Ejecutar el test de avatars: `python -m unittest tests.test_assets.TestArte.test_cada_faccion_tiene_avatar`
2. Verificar contraste en modo headed: lanzar el juego con `SDL_VIDEODRIVER=dummy` o real y inspeccionar visualmente
3. Considerar las mejoras de largo plazo en la próxima iteración de diseño
4. Pasar a la **Fase 3** (Figma Make) cuando se tengan los hallazgos resueltos o se decida el scope de redesign

---

*Informe generado por el agente `ux-auditor` (`.opencode/agents/ux-auditor.md`) basado en screenshots de la Fase 1 de automatización.*