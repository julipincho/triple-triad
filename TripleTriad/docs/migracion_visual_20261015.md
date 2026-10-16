# Migración visual de avatares y cinemáticas

Alcance autorizado: conservar todas las cartas y las escenas que ya tenían el estilo correcto. Adaptar los 19 avatares conservando su identidad y sustituir únicamente los fondos cinematográficos antiguos encontrados en campaña.

## Revisión y cambios

Se revisaron 1.875 escenas del reproductor real: 1.623 de introducción, prólogo, aperturas de las diez facciones, previas de los seis nodos, victorias, derrotas, finales de facción, desenlaces del Umbral y epílogos, más 252 escenas de minicampañas e introducciones de encuentros.

En la campaña principal, los fondos antiguos encontrados fueron aldea, ruinas, fortaleza y asalto. Los tres huecos de prólogo descritos por la auditoría anterior ya estaban corregidos antes de esta intervención. Se conservan los 27 fondos restantes y todas sus asignaciones correctas. La revisión secundaria encontró el Umbral y los estandartes antiguos en minicampañas, y campamento, ruinas y camino antiguos en introducciones de encuentros.

Las asignaciones de campaña se limitan a `_continuidad_nodo_hd`: no reemplazan claves globales ni pisan escenas con `fondo_hd` explícito. La minicampaña recibe un Umbral nuevo y reutiliza los estandartes aprobados. Las introducciones de encuentros reutilizan el campamento aprobado, el camino lluvioso y las ruinas nuevas mediante asignaciones locales en `escena_antes`. No cambian guion, mecánicas, música, cartas ni resultados de encuentros.

Los avatares se activan como lote independiente en `assets/lotes_visuales/migracion_20261015/retratos/`. Los originales y el lote pixel-anime anterior se conservan. Se mantienen especie, edad aparente, cabello, indumentaria y atributos reconocibles. La referencia común es el nuevo retrato de Nara, derivado de su identidad anterior y del campamento aprobado: anime pixel art cinematográfico, sombras azul medianoche, iluminación cálida y saturación controlada.

Los cinco fondos nuevos se guardan como `assets/cinematicas_hd/campana_<nodo>_20261015.png`, sin sobrescribir imágenes anteriores. Las exportaciones PNG usan 1280×720 para fondos y 256×256 para avatares, con vecino más cercano y sin filtros de color. Los masters generados se conservan en la carpeta de auditoría.

Generación: herramienta integrada `image_gen`; los prompts y rutas de procedencia se registran en `assets/lotes_visuales/migracion_20261015/prompts.json`.

## Evidencia y límites

`auditoria/migracion_avatares_20261015/` contiene hashes previos, recorrido JSON, índices visuales y campañas automáticas.

La pasada final completó 20 campañas automáticas —dos ramas por cada facción— con 368 duelos usando las reglas reales y guardados temporales. El recorrido integrado existente también pasó sus siete comprobaciones. Esto es una verificación automatizada: no una partida manual por la interfaz ni una evaluación interactiva de todas las decisiones de encuentros aleatorios. Se renderizaron sus introducciones cinematográficas para las diez facciones.

Resultado final: 1.875 escenas renderizadas, 32 fondos efectivos, 1.118 asignaciones antiguas corregidas y las restantes conservadas. Pasaron 142 pruebas de cinemáticas, presentación, flujo, finales, inventario de fondos e importación de lotes. Los 19 avatares se verificaron activos mediante el cargador real; los cinco fondos cumplen 1280×720. El ejecutable se recompiló y se comprobó su arranque con datos temporales.

Integridad SHA-256: 1.323 archivos preexistentes comprobados, incluidos 1.008 archivos de cartas. El único asset preexistente actualizado es `assets/lotes_visuales/registro.json`; todas las imágenes anteriores permanecen idénticas.

Para volver a los avatares previos basta desactivar `migracion_20261015` en el registro de lotes. Para revertir los fondos se retiran las nuevas entradas en `_continuidad_nodo_hd` y el mapa local HD en `encuentros.escena_antes`; los archivos anteriores permanecen disponibles.
