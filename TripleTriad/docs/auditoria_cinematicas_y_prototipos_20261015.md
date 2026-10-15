# Revision cinematografica y prototipos - 15/10/2026

## Metodo y alcance

Recorrido automatizado de **303 escenas**, renderizadas con Cinematica._dibujar
en pantalla logica 1280x800. Se inspeccionaron las capturas representativas de
los **30 fondos efectivos**. Guardado temporal, sin modificar la partida.

Incluye intro, nueve bloques del prologo, diez aperturas de faccion, treinta
finales de faccion, tres desenlaces del Umbral y tres epilogos. El encuentro
hostil incluido es el bloque fijo cinematografico del prologo, no un evento
aleatorio de campana. Excluye carteles de nodos, duelos y encuentros aleatorios.

Esto es una simulacion de las secuencias del principio al final, no una partida
manual ganada ni una verificacion interactiva de todas las decisiones. Las
73 pruebas de render, flujo, prologo y finales pasaron por separado.

## Hallazgos: tres fondos anteriores, doce escenas

Indices base cero, consultables en `auditoria/revision_cinematica_20261015/recorrido.json`.

| Plano | Escenas exactas | Imagen efectiva | Problema observado |
|---|---|---|---|
| Publico del torneo | prologo.pre_duelo.5-7 | assets/pixel_anime/cinematicas/publico.png | Pixel grueso, magentas saturados y arquitectura distinta al salon moderno aprobado. |
| Camino tras Pik | prologo.encuentro_hostil.0-6 | assets/pixel_anime/cinematicas/camino.png | Bosque verde brillante, pixel grueso; salto desde el camino lluvioso oscuro aprobado. |
| Cierre del prologo | prologo.cierre.1-2 | assets/pixel_anime/cinematicas/umbral.png | Portal de piedra naranja/azul de estilo distinto; las frases son simbolicas, no narran que el jugador cruce una puerta. |

Estos son fondos de la produccion pixel-anime anterior, no archivos ausentes.
No aparecieron otros fondos antiguos en las ramas examinadas con la configuracion
predeterminada. Las variantes aleatorias de camino pueden cambiar el archivo
concreto del segundo caso durante una partida; el hueco de asignacion afecta
al bloque completo, no solo a camino.png.

### Solucion recomendada

1. Publico: nuevo plano `prologo_publico_mesas_torneo.png`, o reutilizar el salon
   aprobado si no se desea otro encuadre. Prompt: plano desde las mesas del
   publico del mismo salon moderno de salon_torneo_lleno.png, luces y estandartes
   coherentes, asistentes como figuras ambientales, sin primeros planos ni
   cartas legibles. PNG RGB 1280x720, mismo lenguaje visual del lote aprobado.
2. Camino: no hace falta generar otra imagen. Reutilizar `camino_lluvioso.png`
   exclusivamente en las siete escenas de prologo.encuentro_hostil para mantener
   el clima y la continuidad tras Pik. No aplicar a la clave camino global.
3. Cierre: conservar el campamento de Nara durante esas dos frases es la opcion
   mas coherente, antes del plano simbolico aprobado del trono. No hace falta
   inventar otra puerta ni una localizacion nueva. No cambiar la clave umbral global.

Las recomendaciones no se aplicaron automaticamente: esta entrega es la auditoria
y las comparativas solicitadas. Lote 05 sigue pendiente.

## Sonido de seleccion de faccion

`pantallas.elegir_faccion` utiliza MENU_MOVE al pasar el mouse o usar flechas,
CARD al seleccionar otra ficha con clic y MENU_OK al confirmar. Los nombres
logicos se resuelven al lote Stable Audio cuando existe; se copiaron los sonidos
efectivos al comparador, no solo los WAV antiguos.

Tres candidatos sintetizados reproducibles (sin IA ni cambios en musica):
- `navegacion_suave.wav`: 65 ms, toque tenue con transitorio de papel.
- `confirmacion_cristal.wav`: 240 ms, dos tonos ascendentes.
- `confirmacion_calida.wav`: 240 ms, intervalo mas suave.

Propuesta: navegacion_suave para hover/flechas/cambio de ficha y confirmacion_calida
solo al aceptar. Usar canal dedicado y limitar repeticiones al mover el mouse
rapidamente. Aun no sustituyen los efectos del juego: escuchar la comparativa
antes de decidir. No se afirma una evaluacion auditiva humana de estos WAV.

## Nombres de cartas

El problema esta en cartas.crear: rect_arte empieza en y=25 y la placa del
nombre en y=26, ocupando 16 o 30 pixeles. Por eso tapa rostros. La miniatura
ya usa una placa inferior y es un render distinto.

Comparativa de seis nombres largos con tres opciones:
- Actual: referencia sin cambios.
- Franja reservada: titulo separado arriba, imagen completa ajustada sin
  deformar. Descubre el rostro, pero reduce demasiado el arte en cartas pequenas.
- Nombre externo: elimina la placa sobre el arte y muestra el nombre debajo
  de la carta en la comparativa. Mantiene el area ilustrada; es la opcion
  recomendada para explorar, pero requiere reservar espacio en mano/tablero y
  comprobar que no invada otras cartas. No esta activada en esas pantallas.

El prototipo es optativo mediante `cartas.crear(nombre_separado=True)` o
`nombre_separado="externo"`. El valor predeterminado False conserva el render
actual. No se modificaron PNG de cartas, valores, nombres, orbes ni reglas.

## Evidencia y uso

- `auditoria/revision_cinematica_20261015/comparativas.html`: sonidos actuales y
  candidatos reproducibles, cartas lado a lado e indice cinematografico.
- `recorrido.json`: escena, texto y ruta efectiva para las 303 escenas.
- `indice_cinematicas.png`: 30 fondos renderizados en contexto.
- `comparativa_cartas.png`: seis nombres largos, tres opciones.
- `tools/auditar_cinematicas_y_prototipos.py`: reconstruye toda la evidencia.
