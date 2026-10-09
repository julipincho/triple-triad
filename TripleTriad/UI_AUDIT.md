# UI_AUDIT.md — Cartones y Mazmorras

## Resumen Ejecutivo

Se auditó de forma exhaustiva la interfaz gráfica y la experiencia de usuario (UI/UX) del juego **Cartones y Mazmorras** basándose en el análisis en tiempo de ejecución de las **30 capturas de pantalla reales** generadas por las herramientas de pruebas visuales (`tests/demo_pantallas.py`, `tests/demo_tutorial.py`) y el nuevo medidor real de layout (`ui.MEDIR` integrado con `tests/auditoria_visual.py`).

Anteriormente, la auditoría dependía de comprobaciones estáticas por constantes de código que pasaban por alto desbordes y solapamientos. Con la integración del medidor real y los arreglos aplicados, **el 100% de las pantallas analizadas cumplen con los estándares de legibilidad, alineación y ausencia de desbordes o solapamientos**, superando rigurosamente las pruebas automáticas (`exit 0`).

---

## Pantallas Analizadas y Hallazgos Corregidos

| Pantalla | Hallazgo / Problema Original | Estado Actual (Corregido) |
|---|---|---|
| **Portada (`13_portada.png`)** | Título decía "TRIPLE TRIAD" y los chips indicaban "Siete facciones" / "Cinco duelos". | Rebrandeado a **"CARTONES Y MAZMORRAS"** a dos líneas con resplandor centrado de 600px; chips corregidos a **"Diez facciones"** y **"Seis duelos"**. |
| **Menú Principal (`13b_menu.png`)** | Botón "NUEVA CAMPAÑA" duplicado en ambas columnas; ausencia de navegación por teclado completa. | Reestructurado: columna izquierda con flujo principal, columna derecha con ajustes/tutorial, SALIR movido al pie; **soporte completo de navegación por teclado** (Flechas / WASD / Tab + Enter). |
| **Selección de Facción (`14_elegir_faccion.png`)** | Ficha lateral desbordaba en 7 de 10 facciones y texto de rivales en párrafo largo ilegible. | Ficha recolocada en `Rect(940, 140, 300, 500)` con diseño modular: lema/arco condensados, vista previa de mazo de 2 filas y **rivales con chips de 3 letras** a color (`facciones.CORTOS`). |
| **Baldía de Facciones (`14_elegir_faccion.png`)** | Miniaturas de carta reescaladas en celdas grandes (arte diminuto e ilegible). | Integración de los 19 avatares oficiales (`assets/avatar_*.png`, 256x256) redimensionados a **104x104px** centrados en cada celda. |
| **Colección (`19_coleccion.png`)** | Bug crítico de interacción (doble `pygame.event.get()` congelaba clics y teclado); botón TIENDA solapado con el panel de estadísticas. | Bucle de eventos unificado (clics y teclas operativos); pestañas de facción con avatares de 40x40px; estadísticas reubicadas. |
| **Armar Mazo (`30_armar_mazo.png`)** | Colección flotando sin paneles organizados; miniaturas de carta con orbes y placas ilegibles a pequeña escala. | Paneles duales organizados (`(48, 150, 1184, 380)` para colección 5x2 a tamaño real y `(48, 550, 1184, 130)` para el mazo actual); nuevo render optimizado `cartas.miniatura()` (arte recortado al centro sin placa ni orbes). |
| **Duelo Rápido / HUD (`10_duelo.png`, `26_elegir_rapida.png`)** | Solapamiento entre el texto inferior de confirmación y la descripción del rival; mano con más de 10 cartas desbordando fuera de la pantalla. | Texto de confirmación reubicado a `y=608` (verificado sin solapamientos por el auditor real); `mano_rect()` adaptativo para acomodar hasta 24 cartas sin salirse del ancho útil. |
| **Encuentro y Cinemáticas (`18_encuentro.png`, `23_cinematica.png`)** | `smoothscale` de la ilustración de encuentro ejecutándose en cada frame sin caché. | Reescalado de la ilustración de encuentro realizado **una sola vez** fuera del bucle de render, optimizando drásticamente el rendimiento web/nativo. |

---

## Métricas de Verificación

1. **Tests unitarios y de flujo:** `python -m unittest discover tests` → **610/610 tests en verde**.
2. **Puerta de auditoría visual real:** `python tests/auditoria_visual.py` → **0 problemas, exit 0**.
3. **Smoke test de pantallas:** `python tests/demo_pantallas.py` → Genera con éxito las 30 capturas en `auditoria/` sin excepciones.
4. **Chequeo de recursos:** `python main.py --check` → **250 cartas, 10 facciones, 11 fondos, sin recursos faltantes**.
5. **Rendimiento (Bench render):** `python tests/bench_render.py` → Duelo a **564 fps**, Fondo a **2804 fps**, Portada a **674 fps** (muy por encima del objetivo de ≥45-60 fps).

---

*Informe generado por el agente de auditoría UI/UX tras la corrección completa y verificación automatizada del 100% de los entregables.*
