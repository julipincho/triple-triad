# Proposal Premium - TripleTriad Figma Design System

*Generado a partir de: UI_AUDIT.md + screenshot_fase1.png + identidad visual del juego*
*Objetivo: Propuesta de sistema de diseño en Figma para rediseño premium, sin usar créditos Make prematuremente.*

---

## 1. Identidad Visual Base

### Paleta de Colores (extraída de los assets del juego)
| Nombre | HEX | Uso |
|--------|-----|-----|
| Fondo oscuro principal | `#0a0a0a` | Fondo general, pantallas de menu |
| Fondo cuadro selector | `#1a1a1a` | Fondo de las facciones en selección |
| Texto principal | `#e0e0e0` | Nombres de facción, textos UI |
| Texto secundario | `#a0a0a0` | Texto tenue, descripciones |
| Acento humano | `#4a90e2` | Azul - facción humano |
| Acento orco | `#6b4226` | Marrón/ocado - facción orco |
| Acento elfo | `#2e8b57` | Verde bosque - facción elfo |
| Acento goblin | `#556b2f` | Verde oliva - facción goblin |
| Acento hombre_lobo | `#8b4513` | Marrón - facción hombre_lobo |
| Acento vampiro | `#8b008b` | Púrpura profundo - facción vampiro |
| Acento dragon | `#b8860b` | Oro/ámbar - facción dragon |

### Tipografía
- **Fuente principal**: `PressStart2P` (Google Fonts, estilo retro pixelado)
- **Tamaños**: 
  - Texto grande: 16-18px (en escala de juego 960x540)
  - Texto mediano: 14px
  - Texto pequeño: 12px (siempre legible por estilo)

### estilo visual
- **Época**: Retro años 80/90, estilo chiptune
- **Fondo**: Patterns geométricos cuadriculados (fondo.png en assets)
- **Sombras**: Sombra mínima, estilo "flat" con focus state sutil
- **Animaciones**: Transiciones de 150ms, sin easing complejo (estilo retro)

---

## 2. Estructura de Figma File Recomendada

### File: `TripleTriad Design System`

#### Frame 1: `System Palette`
- Cuadrado con cada color HEX etiquetado
- Valores RGB y HEX copiables
- Preview de cómo se ven en fondos/textos

#### Frame 2: `Typography System`
- Todos los tamaños de texto con PressStart2P
- Ejemplos: menú, títulos, cuerpo, caption
- Línea base y espaciado recomendado

#### Frame 3: `Color Themes by Faction`
- 7 frames, uno por cada facción
- Cada frame: fondo del acento, texto en contraste,
  avatar placeholder, bordes temáticos
- Cómo los colores cambian el "state" de cada facción

#### Frame 4: `Component Library`
| Componente | Descripción | Variantes |
|-----------|-------------|-----------|
| `Button` | Botón rectangular con estados: default, hover, pressed, disabled | 4 variantes |
| `FactionCard` | Carta de facción con avatar, nombre, pequeño texto | default, hover, selected |
| `SelectorItem` | Elemento del selector de facciones (lo que ve el mouse) | default, selected, disabled |
| `MenuDivider` | Línea divisora entre secciones de menú | horizontal, vertical |
| `Badge` | Pequeño indicador de estado (ej. "nuevo", "seleccionado") | 3 tamaños |

#### Frame 5: `Screens` (Mockups basados en screenshot_fase1.png)
- `Frame: Main Menu` - Portada, botones de inicio
- `Frame: Faction Selection` - Las 7 facciones en línea horizontal, hover activo
- `Frame: Game Board` - Campo de juego con área de cartas
- `Frame: In-Game HUD` - Puntuación, capturas, turno actual

---

## 3. Componentes Detallados

### `FactionCard` (Componente principal)
**Propiedades:**
- `factionName`: string (ej. "humano")
- `avatar`: image asset (96x96px)
- `accentColor`: HEX color (tema de facción)
- `isSelected`: boolean
- `isHovered`: boolean

**Estados:**
| Estado | Estilo Visual |
|--------|---------------|
| Default | Fondo `#1a1a1a`, texto `#e0e0e0`, avatar a la izquierda, acento en `#4a90e2` (o color correspondiente) |
| Hover | Fondo `#2a2a2a`, sombra ligera, avatar con ligera ampliación (scale 1.1) |
| Selected | Fondo `#3a3a3a`, borde `2px` en color acento, avatar con borde `4px` white |
| Disabled | Fondo `#0a0a0a`, texto `#707070`, opacidad 0.5 |

**Interacción en Figma:**
- On Hover: cambiar fondo a `#2a2a2a`, reproducir efecto visual
- On Click: disparar evento "select faction" (prototype link a siguiente frame)
- State toggle: animación 150ms fade

### `Button` Componente
**Propiedades:**
- `text`: string
- `variant`: "primary" | "secondary" | "ghost"
- `size`: "small" | "medium" | "large"

**Estados:** Igual que FactionCard (default/hover/pressed/disabled) con variantes de color según `variant`.

---

## 4. Screens Mockup Specifications

### `Faction Selection Screen` (basado en screenshot_fase1.png)
- **Dimensiones**: 960 x 540 px (escala 1:1 con el juego)
- **Distribución horizontal de facciones**:
  - Empiezan en x=160 px
  - Separación de 190 px entre cada facción
  - Posición Y fija: 250 px
  - 7 facciones total: índices 1 a 7 en x = 350, 540, 730, 920, 1110, 1300, 1490
  *(fórmula: x = 160 + i * 190, con i de 1 a 7)*
- **Avatar**: 48x48 px a la izquierda del nombre
- **Nombre**: PressStart2P, color `#e0e0e0`, tamaño calculado para caber en ancho máximo
- **Fondo**: Pattern cuadriculado `#1a1a1a` sobre `#0a0a0a`
- **Hover area**: Cada facción detecta MOUSEMOTION, resalta con acento de facción
- **Teclado navigation**: Flechas LEFT/RIGHT mueven selección, ENTER confirma
- **Accessibility**: Contrast `#e0e0e0` sobre `#1a1a1a` = 4.8:1 (aproximado, pasa test AA normal)

### `Main Menu Screen`
- Portada con título "Triple Triad - El Umbral del Trono"
- 3 botones principales: `Nueva Partida`, `Campana`, `Ajustes`
- Botón secundario: `Colección`
- Fondo animado sutil (FondoAnimado en ui.py)
- Credits o logo en esquina inferior derecha

---

## 5. Recomendaciones de Diseño Premium

### 5.1 Sistemas que mejorarían la experiencia
1. **Sistema de Estados Visibles**: Añadir un pequeño indicador "brillante" o cambio sutil en el borde de la facción seleccionada (no solo hover), para siempre saber cuál es el turno.
2. **Transiciones entre pantallas**: Usar fade-in/out de 200ms en lugar de cambios instantáneos. En Figma prototyping: `Smart Animate` con easing `ease-out`.
3. **Animación de carta placement**: Cuando un jugador coloca una carta, hacer un pequeño "pop" scale 1.0 → 1.1 → 1.0 con sombra desplazada, para dar retroalimentación táctil.
4. **Tema de color dinámico**: En lugar de 7 fondos fijos, usar el acento de la facción seleccionada como color dominante de la pantalla (overlay sutil del color sobre el fondo cuadriculado).

### 5.2 Componentes adicionales para Figma
- `CardComponent`: Cada carta del juego (42 cartas totales) como componente variante, con:
  - Arte de carta (imagen PNG)
  - Números de esquina (valores de ataque/defensa)
  - Símbolo de rareza
  - Estado: jugada, disponible, en mano
- `Dice/Roll Component`: Si hay mecánica de dados o azar
- `Notification Toast`: Para mensajes tipo "¡cadena ganada!", "¡facción derrotada!"

---

## 6. Flujo de Trabajo Propuesto

1. **Setup inicial**: Importar todos los assets del juego a Figma (7 avatares, fondo.png, 42 cartas PNG, sonidos como assets SVG/URL)
2. **Crear componentes base**: Button, FactionCard, FactionSelector usando las propiedades definidas
3. **Construir screens**: Montar los 4 frames principales (Main Menu, Faction Selection, Game Board, HUD) usando los componentes
4. **Prototipar interacciones**: 
   - Facción → siguiente screen (selección de facción o duelo rápido)
   - Botones → acciones (iniciar duelo, abrir campana, ajustes)
   - Hover states en todos los elementos interactivos
5. **Revisar contraste y accesibilidad**: Usar plugin de Figma `Contrast Checker` contra los colores HEX definidos
6. **Exportar especs**: Generar especificación CSS/React para desarrollo

---

## 7. Checklist de "Ready for Development"

- [ ] Todos los colores HEX definidos y documentados
- [ ] Componentes base en Figma con variantes de estado
- [ ] Screens mockup completos (4 frames mínimos)
- [ ] Prototipo con interacciones básicas (click, hover, navegación teclado)
- [ ] Contraste aprobado (4.5:1 mínimo para texto normal)
- [ ] Documentación de propiedades de cada componente
- [ ] Assets exportados (PNG a 1x y 2x, SVG para iconos)
- [ ] Notación de diseño completada (specifications panel relleno en Figma)

---

## 8. Próximos Pasos para Ejecutar de Verdad (con Figma Make)

*Cuando se tenga acceso a Figma Make/credits gratuitos:*

1. **Subir assets a Figma**: Importar `TripleTriad/assets/` como imágenes iniciales
2. **Ejecutar Figma Make con prompt**:
   ```
   "Design a premium version of TripleTriad card game UI based on these specifications:
   - 7 facciones with distinct colors and avatars
   - Retro chiptune aesthetic with PressStart2P typography
   - Faction selection screen with horizontal scroll of 7 cards
   - Main menu with 3 primary buttons
   - Color palette: dark backgrounds (#0a0a0a, #1a1a1a) with faction accent colors
   - Include component library with FactionCard, Button, and Card components
   - Make it responsive for 1080p and 720p displays
   - Add micro-interactions for hover and selection states"
   ```
3. **Revisar y refinar** la salida de Figma Make
4. **Aplicar ajustes** basados en UI_AUDIT.md hallazgos (específicamente los 3 puntos menores: tamaño de avatars consistente, contraste de fondo, indicador de selección)
5. **Exportar** el archivo `.fig` listo para desarrollo y diseño UI/UX

---

*Fin del Proposal Premium. Este documento está listo para ser usado ya sea con Figma Make (cuando haya créditos disponibles) o como especificación de diseño para desarrollo directo.*