# Lote 03 — integración revisada

## Integrado: 2 fondos, 3 escenas existentes

| Recurso | Destino (índice base cero) | Texto existente |
|---|---|---|
| `escenario_carta_cubierta` | `prologo.carta_umbral.1` | «Una carta que no tiene faccion. Ni bando. Ni edicion.» |
| `activacion_carta_plano_cercano` | `prologo.carta_umbral.6` | «LAS NUEVE CASILLAS» |
| mismo plano cercano | `prologo.carta_umbral.7` | «empiezan a iluminarse.» |

Se conserva el objeto cubierto durante el anuncio, no durante la descripción
de la puerta/trono. El primer fenómeno ahora ocurre visualmente en el salón,
en lugar del portal exterior del lote local anterior. El plano cercano conserva
el marco dorado, medallón superior izquierdo y abertura oval de la carta del
Lote 02. No ilustra literalmente una cuadrícula de nueve casillas: muestra la
manifestación mágica asociada, sin añadir ni modificar acontecimientos.

El título centrado cubre temporalmente parte de la carta como en el renderer
existente; el siguiente diálogo deja visible la carta completa. El panel inferior
no tapa el foco narrativo. No se modificaron UI, transiciones ni tratamiento global.

## Pendiente: 3 fondos

- `carta_presentada_sin_activar`: presenta resplandor/energía violeta y una
  cara con rombo central, no la puerta y trono vacío descritos en ese momento.
  No se introduce un giro de la carta ni se anticipa su activación para justificar
  la imagen. Requiere imagen revisada o aprobación específica del montaje.
- `umbral_ruptura_total_alternativa`: alternativa sin asignación, tal como se pidió.
- `publico_reacciona_portal_alternativa`: alternativa sin asignación; no se añadió
  una escena de reacción ni se sustituyó el portal aprobado.

Los cinco PNG están disponibles en `assets/lotes_visuales/lote_03/fondos/`;
solo los dos recursos marcados `listo` participan del selector. Revisión estática:
`assets/lotes_visuales/lote_03/preview.html`. No hay retratos en este lote.

## Integridad y trazabilidad

- ZIP original SHA-256: `c3b6a09cac0e1f0af532048d25043b21af24124379871fdd90daae6d057aa738`.
- CRC, hashes, PNG RGB y dimensiones: 5 exports 1280×720 y 5 masters 1672×941 correctos.
- Staging íntegro: `E:/AI/CartonesMazmorrasVisual/exports/review/lote_03/`.
- Se siguió `docs/PROMPT_OPENCODE.txt`; el esquema del paquete difiere del
  importador. Se adaptó **una copia**, conservando el manifiesto original como
  `docs/manifest_fuente_original.json` dentro del ZIP adaptado. Originales sin editar.
- Copia compatible: `E:/AI/CartonesMazmorrasVisual/incoming/lote_03_adaptado.zip`.
  SHA-256: `a429b5894df1c37894ad26b298b22703ec1296ead1ef153d69b26aea0355bcaf`.
- `manifest_adaptado.json` documenta las asignaciones y razones de pendientes.
- Checkpoint de 1267 archivos: `checkpoint_antes.json`.
  Respaldo de código, registro y HD previos:
  `C:/Users/julip/AppData/Local/Temp/opencode/antes_lote03_20261014.zip`.
- Tras integrar, el único archivo previo modificado fue
  `assets/lotes_visuales/registro.json`. Fuentes, cartas, avatares, música y todos
  los fondos previos conservaron sus hashes. Los nuevos archivos se agregaron
  en carpetas independientes.
- Lotes 01/02 conservan PNG y asignaciones. En particular, `carta_umbral[0]`
  mantiene salón lleno y `[8:11]` mantienen revelación y portal del Lote 02.
- Rama: `arte/consolidacion-primer-arco-20261014`; sin merge a main.

## Validación

- 87 pruebas aprobadas: importador, selector, assets, prólogo y flujo.
- 81 escenas renderizadas en pygame real, con guardado temporal aislado.
- Exactamente tres escenas seleccionan fondos del Lote 03; las otras 78 no.
- Los dos nuevos PNG se presentan 1:1 en el viewport HD, sin estirar ni recortar.
- Capturas posteriores a la activación idénticas a las previsualizaciones.
- Evidencia detallada: `validacion.json`. No equivale a una partida manual completa.

## Capturas reales

| Escena | Antes | Integrada |
|---|---|---|
| Anuncio / carta cubierta | [Antes](prologo.carta_umbral.1_antes.png) | [Integrada](prologo.carta_umbral.1_integrado.png) |
| Título del fenómeno | [Antes](prologo.carta_umbral.6_antes.png) | [Integrada](prologo.carta_umbral.6_integrado.png) |
| Inicio de iluminación | [Antes](prologo.carta_umbral.7_antes.png) | [Integrada](prologo.carta_umbral.7_integrado.png) |

También se capturaron todos los pasos de preduelo, postduelo, carta/Umbral y
transporte, con sufijo `_integrado.png`, para revisar los cortes completos.

Reversión: `python tools/importar_lote_visual.py revertir lote_03` usando el
Python del juego, y reiniciar el juego. No borra imágenes ni historial.
