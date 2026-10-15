# Importación de paquetes visuales

## Uso cotidiano

1. Guardar el ZIP de ChatGPT en `E:\AI\CartonesMazmorrasVisual\incoming\`.
2. Pedir: **«integrá el siguiente lote»**.

El agente prepara el ZIP nuevo más antiguo, genera previsualizaciones, revisa
coherencia visual y activa los recursos con asignación válida. Los dudosos quedan
pendientes. No es necesario instalar nada ni contratar una API. No hay servicio
vigilando carpetas ni generación automática en segundo plano.

Los destinos exactos están en `incoming/catalogo_destinos.json`: IDs del prólogo
con índices base cero y personajes existentes. Las escenas marcadas `protegida`
no admiten reemplazo. Esta primera versión cubre los fondos del prólogo y los
retratos de personajes existentes (estos se usan también en otras pantallas).
Asignaciones de campaña no catalogadas quedan pendientes, nunca se adivinan.

## Formato que debe entregar ChatGPT

ZIP con `manifest.json` en la raíz. Ejemplo completo:

```json
{
  "version": 1,
  "lote": "lote_03_piloto",
  "notas": "Anime pixel art cinematográfico. Referencias Lotes 01 y 02.",
  "recursos": [
    {
      "id": "escenario_torneo",
      "nombre": "Escenario del mismo recinto del torneo",
      "tipo": "fondo",
      "archivo": "fondos/escenario_torneo.png",
      "dimensiones": [1280, 720],
      "escenas": ["prologo.pre_duelo.1", "prologo.pre_duelo.2", "prologo.pre_duelo.3", "prologo.pre_duelo.4"]
    },
    {
      "id": "pik",
      "nombre": "Pik — advertencia del bosque",
      "tipo": "retrato",
      "archivo": "retratos/pik.png",
      "dimensiones": [256, 256],
      "personaje": "pik"
    }
  ]
}
```

- `lote` e `id`: minúsculas, números, guiones o guiones bajos; máximo 64 caracteres.
- Fondos: PNG RGB/RGBA de 1280×720. Retratos: PNG RGB/RGBA de 256×256.
- No se redimensiona, recorta, filtra ni repinta automáticamente ningún PNG.
- `sha256` opcional por recurso: si viene, se verifica. Si falta, se calcula y
  registra al importar. CRC y decodificación se verifican siempre. Un hash
  calculado al recibir no demuestra procedencia ni aprobación artística.
- Notas, referencias y masters pueden incluirse dentro del ZIP: el paquete
  original se conserva completo. Solo los PNG declarados como recursos se
  publican. Los PNG extra se listan en `revision.json`, sin asignarlos.
- Un recurso sin `escenas` (fondo), sin `personaje` conocido (retrato), con destino
  protegido o desconocido queda **pendiente**. Una asignación parcialmente válida
  deja pendiente el recurso completo, para evitar integraciones parciales ambiguas.
- Una imagen con formato/tamaño/hash inválido rechaza todo el paquete; no se
  activa nada. ZIP máximo 256 MB descomprimidos, 32 MB por archivo, 500 entradas.
- Ningún archivo del paquete se ejecuta; no se extraen rutas arbitrarias.

No incluir cartas, música, código ni instrucciones de cambios narrativos como
recursos: solo se admiten tipos `fondo` y `retrato`. Los otros documentos quedan
conservados dentro del ZIP, no se ejecutan ni aplican.

## Comandos disponibles

Desde `E:\openCode\TripleTriad`, con el Python del juego:

```powershell
$python = 'C:\Users\julip\AppData\Local\Programs\Python\Python312\python.exe'
& $python tools/importar_lote_visual.py preparar 'E:\AI\CartonesMazmorrasVisual\incoming\lote_03.zip'
& $python tools/importar_lote_visual.py previsualizar lote_03_piloto
& $python tools/importar_lote_visual.py activar lote_03_piloto
```

Previsualización estática: `assets/lotes_visuales/<lote>/preview.html`.
Capturas del renderer antes/candidato: `auditoria/lotes_visuales/<lote>/`.
Las capturas se generan con guardado temporal, sin tocar la partida.
Un retrato sin escena en el catálogo tiene vista estática, pero no captura
cinemática automática; requiere revisar su pantalla de uso antes de activarlo.

Atajo **solo tras considerar aprobado el contenido del paquete**:

```powershell
& $python tools/importar_lote_visual.py siguiente
```

Este atajo valida y activa técnicamente el ZIP no registrado más antiguo. No
evalúa calidad artística. Un ZIP inválido detiene la cola; no se salta en silencio.
Un lote ya preparado se activa por nombre; uno revertido nunca se reactiva por
el atajo. Los ZIP se conservan en incoming y se reconocen por hash.

Reversión / integridad:

```powershell
& $python tools/importar_lote_visual.py revertir lote_03_piloto
& $python tools/importar_lote_visual.py verificar
& $python tools/importar_lote_visual.py catalogo
```

**Reiniciar el juego después de activar o revertir**, porque las imágenes se
cachean. `TRIPLETRIAD_LOTES_VISUALES=0` desactiva todos estos lotes y devuelve
el selector anterior. No afecta la activación histórica de HD/pixel_anime.

## Protección y reversibilidad

`assets/lotes_visuales/registro.json` contiene los Lotes 01/02 históricos con
sus referencias, hashes de los recursos previos, nuevos lotes y eventos de
preparación/activación/reversión. El contenido previo de pixel_anime se protege
físicamente, sin certificar retrospectivamente su aprobación artística.

- Cada lote ocupa su propia carpeta y conserva ZIP, manifest, PNG y revisión.
- IDs de lote usados nunca se sobrescriben, aunque el lote esté desactivado.
- Fondos HD explícitos siempre ganan prioridad sobre importaciones.
- Los destinos de nuevos lotes integrados quedan reservados incluso tras
  revertir: una futura sustitución deliberada requiere una revisión explícita
  del pipeline, no se hace accidentalmente con otro ZIP.
- Un recurso pendiente puede reenviarse corregido con un nuevo ID de lote.
- Activar/revertir cambia atómicamente el registro, no el código del guion.
- Los fondos se vinculan a una huella del texto/escenario/hablante originales:
  si el guion cambia, la activación se detiene; el runtime deja de seleccionarlos.
- El runtime verifica el hash al cargar cada recurso y cae al arte previo si
  falta o está alterado. Solo consulta rutas internas del pipeline.
- Un bloqueo exclusivo evita importadores simultáneos. Si el proceso termina
  abruptamente, puede quedar `.lock` o una carpeta huérfana: revisar antes de
  recuperarla, no sobrescribirla. No se elimina historial automáticamente.

El sistema no cambia cartas, música, reglas, diálogos ni resolución lógica.
Se mantiene la rama `arte/consolidacion-primer-arco-20261014`, sin merge a main.

## Prueba simulada

`tests/test_importar_lote_visual.py` crea ZIP/PNG sintéticos en carpetas
temporales, activa y revierte allí. Los rectángulos de color son datos de prueba,
**no arte del juego**. No se importó el ZIP simulado al registro de producción.

Evidencia: `auditoria/lotes_visuales/prueba_simulada/`:
`simulado_antes.png`, `simulado_candidato.png`, `simulado_NO_PRODUCCION.zip`.

Se comprueban: hash erróneo, PNG inválido, resolución, rutas ZIP inseguras,
duplicados, destinos protegidos/desconocidos, cambio de guion, inmutabilidad,
idempotencia, reserva tras reversión y render real sin activación.
