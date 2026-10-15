# SFX Lote 01 — candidatos

**Estado: EN REVISION. No integrados.** Ningún WAV sustituye un efecto
existente. La banda sonora no se tocó.

ZIP fuente: `CartonesMazmorras_SFX_Lote01_prototipos.zip`
SHA-256: `08803f2fcefee231222b42de690dfcf9085f6d3cbfbc03a981a9c360583813fe`

## Validación

13/13 WAV verificados: CRC del ZIP, SHA-256 del manifiesto, formato PCM 16 bits
estéreo 48 kHz, duración declarada y pico 0.72 (-2.9 dBFS). Staging íntegro en
`E:/AI/CartonesMazmorrasVisual/exports/review/sfx_lote01/`. `DEMO_escucha_secuencial.wav`
y `generar_sfx.py` viajan en el ZIP pero no se publican como recursos.

## Cómo funciona hoy el mezclador

`audio.py` ya resuelve lo esencial:

- `pygame.mixer.init(44100, -16, 2, 512)` con **24 canales**.
- Volúmenes separados: `volumen_sfx` (0.55) y `volumen_musica` (0.35), ambos
  persistidos en `opciones.json` y re-aplicados al arrancar.
- `audio.sfx(nombre, volumen, canal)`: cachea el `Sound` por nombre, marca
  `False` si falta, y con `canal=` detiene el sonido anterior de ese canal.
- `pygame.mixer.music` es un único canal: solo se cachea el fallo, nunca el WAV.

La música no comparte mixer con los efectos: conviven sin pisarse.

## Eventos y anclaje en las mecánicas

| Evento candidato | ¿Evento de audio ya existe? | Ancla en el código |
|---|---|---|
| `card_place` | Sí | `audio.sfx(audio.COLOCAR)` — `partida.py:347`, en `Juego.colocar` |
| `card_capture` | Sí | `_sonido_de_efecto` → `audio.CAPTURAR` — `partida.py:352`, `canal="cap"` |
| `same_plus` | Sí | `_sonido_de_efecto` → `audio.SAME` / `audio.PLUS` — `partida.py:115-118` |
| `combo_chain` | Sí | `_sonido_de_efecto` → `audio.CADENA` — `partida.py:119-120` |
| `invalid_move` | Sí | `audio.sfx(audio.INVALIDO, 0.5)` — `partida.py:552`, colocación que la guía rechaza |
| `card_flip` | **No** | No hay sonido de giro. El proxy visual es `_explosion` + `flash` (`partida.py:343-346`) |
| `ability_trigger` | **No** | No hay evento al activarse una habilidad. El dato existe: `resumen["quema"]` en `partida.py:401-405` |
| `turn_change` | **No** | No hay evento al pasar el turno. El punto es `partida.py:480-487` («tu turno») |

## Eventos faltantes para sincronizar con animación

1. **`card_flip` sin ancla.** El giro no es un evento de audio: hay que emitirlo
   en el frame de la explosión, no en la decisión lógica, o sonará antes de que
   se vea.
2. **`ability_trigger` sin ancla.** Las habilidades (`quema`, `muro`, `furia`,
   `embestida`) activan efectos en `reglas.cascada` pero nunca suenan. `quema`
   es el único detectable hoy desde `resumen`.
3. **`turn_change` sin ancla.** El cambio de turno es visible (mensaje «tu
   juega») y mudo.
4. **Conflicto de captura.** `card_capture`, `same_plus` y `combo_chain`
   apuntan al mismo instante. Hoy `_sonido_de_efecto` ya prioriza; los candidatos
   no deben apilarse los tres sobre la misma jugada.
5. **`same_plus` es un solo WAV** para dos reglas que el código distingue
   (`audio.SAME` y `audio.PLUS`). Hay que decidir si cubre ambos o sólo uno.

## Conectables directamente a mecánicas actuales

Cinco, sin tocar reglas: `card_place`, `card_capture`, `same_plus`,
`combo_chain`, `invalid_move`. Los tres restantes requieren un hook nuevo
(minor, pero es un cambio de código explícito, no un reemplazo de archivo).

## Integración reversible preparada

`sfx_candidatos.py`:

- **Apagado por defecto** (`TRIPLETRIAD_SFX_LOTE01=0`).
- Volumen propio, aislado de música y del SFX base.
- Cache por WAV; un archivo ausente se marca `False` y no se reintenta.
- Rotación de variantes **determinista** (contador, no `random`): dos partidas
  iguales suenan igual.
- `MAX_SIMULTANEOS = 4`: al superarlo se roba la voz más antigua, para que una
  jugada con muchas capturas no saturen el tablero.
- `canal=` detiene el sonido previo de ese canal, igual que `audio.sfx`.

Los WAV viven en `assets/sfx_candidatos/` (copias, no se mueven los originales)
con `manifest.json` de runtime y `manifest_fuente.json` intacto.

Para escuchar sin integrar:

```powershell
python assets/preescuchar.py --candidatos
```

## Pruebas

`tests/test_sfx_candidatos.py`: 9 pruebas — apagado por defecto, hashes del
manifiesto, caché de ausencias, rotación determinista, límite de simultáneos,
aislamiento de volumen, canal nombrado y reset.

Suite completa: 4 fallos **preexistentes**, idénticos con y sin estos cambios
(`test_documentacion` ×2, `test_narrativa`, `test_visual_y_bando`). El del
torneo cuenta claves lógicas de fondo, no el arte. `test_sobres` agota el tiempo
y se cuelga; también previo.

No modificados: `audio.py`, `partida.py`, `reglas.py`, `cartas.py`, cartas,
cinemáticas, música ni mecánicas. Rama
`arte/consolidacion-primer-arco-20261014`, sin merge.
