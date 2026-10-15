# Lote 04 — integración

## Escena modificada (1)

| Recurso | Destino | Texto existente |
|---|---|---|
| `apagon_torneo_anomalia` | `prologo.transporte.0` | «La luz se apaga.» |

Motivo de coherencia: el fondo previo mostraba **otro recinto** (sala vieja
oscura con cartas en el suelo), rompiendo el recinto en la última imagen de
nuestro mundo. El guion no exige negro absoluto: «La luz se apaga» y «cuando
vuelve, ya no estás en el salón». El salón con fallo de luces y energía
residual es la lectura compatible y corrige la ruptura de continuidad.

`transporte.1` y `transporte.2` conservan el montaje previo.

## Imágenes pendientes de aprobación (3)

- `vision_trono_sobre_torneo`: trono vacío que anticiparía la magia en
  `carta_umbral.3`; el pasaje de la figura sentada ya tiene HD protegido del
  Lote 02. Sin destino compatible sin alterar el montaje.
- `ruptura_arena_vortice_alternativa`: destrucción física no establecida.
- `transito_umbral_entre_mundos`: viaje dimensional no descrito por el transporte.

Los cuatro PNG quedan en `assets/lotes_visuales/lote_04/fondos/`; solo el
apagón participa del selector. Revisión estática: `preview.html`.

## Integridad

- ZIP fuente SHA-256: `d128c7fe72f136f7555931fa833543d74c5a89e5d5106f2ea08c3e017eaea487`.
- 4 exports 1280×720 y 4 masters: hashes, CRC, PNG RGB verificados.
- Staging: `E:/AI/CartonesMazmorrasVisual/exports/review/lote_04/`.
- Copia compatible: `incoming/lote_04_adaptado.zip` (manifiesto fuente original
  preservado dentro como `docs/manifest_fuente_original.json`).
- Checkpoint 1276 archivos; único previo modificado: `registro.json`.
- Lotes 01/02/03 protegidos; cartas, avatares, diálogos, música y mecánicas intactos.
- Presentación 1280×720 1:1 en viewport 1280×800, sin deformar.
- Rama `arte/consolidacion-primer-arco-20261014`, sin merge a main.

## Pruebas

- 87 pruebas aprobadas (importador, selector, assets, prólogo, flujo).
- 81 escenas renderizadas: 3 del Lote 03 + 1 del Lote 04; el resto sin selección.
- Viewport 1:1 exacto; capturas runtime iguales a previsualización.
- Detalle: `validacion.json`.

## Captura

[Apagón integrado](prologo.transporte.0_integrado.png) ·
[Antes](prologo.transporte.0_antes.png) ·
[Candidato](prologo.transporte.0_candidato.png)

Siguiente plano pendiente del primer arco: un **plano de llegada/despertar
distinto** del camino general (punto de vista del protagonista al llegar al
bosque), o la reacción del público, si se autoriza una escena nueva.

Reversión: `python tools/importar_lote_visual.py revertir lote_04` y reiniciar.
