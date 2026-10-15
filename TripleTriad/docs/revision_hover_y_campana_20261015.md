# Revision de cartas, sonido y cinematicas de campana

## Cambios aplicados

- El render normal de cartas ya no dibuja el nombre sobre la ilustracion.
  Mano/tablero y coleccion utilizan sus tooltips externos existentes; se
  agregaron etiquetas al apuntar en seleccion de mazo, entrenamiento,
  recompensas y sustitucion de reclutas. Las fichas de detalle conservan
  su informacion externa. Las miniaturas tampoco llevan placa de nombre.
- Mascara de esquinas redondeadas: radio 5 en el arte de carta normal y 3
  en miniaturas. No se modifico ningun PNG de cartas.
- `faccion_confirmar_cristal.wav`: copia exacta del candidato elegido, usado
  exclusivamente al confirmar faccion con Enter, doble seleccion o boton.
  Los sonidos de navegacion y la banda sonora conservan sus asignaciones.
- Planos 6, 12 y 14 del indice ANTERIOR: publico -> salon_torneo_lleno;
  camino tras Pik -> camino_lluvioso; cierre simbolico -> campamento de Nara.
  Son asignaciones locales, no reemplazos de claves compartidas.

## Revision ampliada: por que aun aparecia arte antiguo

La primera auditoria excluia las previas y posteriores de nodos. Esas
secuencias tambien se reproducen con Cinematica durante una partida real.
Se incluyeron ahora senda, aldea, ruinas, fortaleza, asalto y trono, con
previas, victorias y derrotas de las diez facciones.

Se renderizaron **1623 escenas** con datos temporales. No es una partida
manual: se enumeran ramas y se dibujan sus escenas con el reproductor real.
No se ejecutaron duelos ni se cambio el guardado del usuario. Se usan estados
base de cada faccion, no todas las combinaciones de confianza o historial.

Se detectaron otros seis fondos de estilo anterior: camino, aldea, ruinas,
fortaleza, asalto y algunos dialogos del trono.

Corregidos adicionalmente:
- Senda: continuidad con el camino lluvioso existente.
- Trono: los dialogos de rol se construian fuera de esc() y no recibian HD;
  ahora heredan sala_trono.png solo dentro del nodo trono, incluso tras perder.

**Siguen pendientes cuatro lugares**:

| Nodo | Fondo actual | Motivo |
|---|---|---|
| aldea | assets/pixel_anime/cinematicas/aldea.png | Pueblo de pixel grueso, distinto del lote cinematografico. |
| ruinas | assets/pixel_anime/cinematicas/ruinas.png | Ruinas de pixel grueso y paleta distinta. |
| fortaleza | assets/pixel_anime/cinematicas/fortaleza.png | Fortaleza estilizada de otra serie. |
| asalto | assets/pixel_anime/cinematicas/asalto.png | Interior incendiado de la serie anterior. |

Se necesita un plano adecuado a cada nodo. Las aperturas del pantano/goblin
no son sustitutos intercambiables de unas ruinas genericas. El campamento
orco tampoco confirma la localizacion de la fortaleza. Las variantes de clima
de esos fondos comparten el problema; no se deben reemplazar globalmente.
El Lote 05 permanece pendiente.

## Evidencia

- 95 pruebas OK: hover externo, ausencia de nombre dentro de la carta,
  continuidad HD, render, flujo, presentacion, finales y controles de duelo.
- `auditoria/revision_cinematica_ampliada_20261015/recorrido.json`: rutas
  efectivas de las 1623 escenas despues de las correcciones.
- `indice_cinematicas.png` en esa carpeta: 31 fondos efectivos. Sus numeros
  son nuevos; no deben confundirse con 6/12/14 del indice anterior.
- `comparativa_cartas.png`: referencia, franja superior descartada y nombre
  externo. Es una lamina explicativa; el nombre en el juego depende del hover.
