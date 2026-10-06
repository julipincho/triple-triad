# Traspaso: versión web (pygbag) para subir a itch.io

> Estado: **optimización terminada y verificada en navegador**. El juego va a
> 48-62 fps en la web (antes iban a 35-42) y el paquete pesa 4,6 MB (antes
> 14 MB). Este documento explica qué se hizo, cómo se midió y qué queda.

---

## 1. Objetivo

Que el juego (Triple Triad — *El Umbral del Trono*, Python + pygame-ce) sea
**jugable desde un link** que se pueda pasar por WhatsApp. La vía elegida es:

**pygbag → build HTML5 → subir a itch.io (juego HTML5 en el navegador).**

---

## 2. Resultado

### 2.1 Cifras medidas en navegador real (Chromium 1440×900, viewport 16:10)

| Pantalla | Antes | Ahora |
|---|---|---|
| Portada | 42,2 fps (23,7 ms) | **62,5 fps (16,0 ms)** |
| Menú | — | **62,5 fps (16,0 ms)** |
| Duelo rápido | — | **62,0 fps (16,1 ms)** |
| Colección | — | **54,3 fps (18,4 ms)** |
| Selector de facción | 35,0 fps (28,6 ms) | **48,5 fps (20,6 ms)** |

Todas por encima del objetivo de ≥45 fps y el objetivo se cumple sin bajar
`LIMIT_FPS`.

### 2.2 Tamaño del paquete

| | Antes | Ahora |
|---|---|---|
| `tripletriad.apk` / `.tar.gz` | 13,9 MB | **2,4 MB** |
| `tripletriad-web.zip` (lo que se sube) | ~14 MB | **4,62 MB** |

---

## 3. Qué se cambió y por qué

### 3.1 Cachés de render (`ui.py`)

El cuello de botella NO era tanto la resolución como **crear `Surface` y
renderizar texto en cada frame**. En WASM/Asyncify eso cuesta varias veces más
que en nativo.

- `ui.superficie(clave, factory)` + `limpiar_cache()`: caché genérica de
  superficies para halos, sombras, viñetas, líneas y cajas.
- `texto()` renderiza **una** vez y cachea por `(cadena, tamaño, color,
  sombra)`; la sombra va pegada en la misma Surface, así que son 1 blit en
  vez de 2. Antes: `font.render` × 2 por llamada, ~22 por frame en el duelo.
- `limpio()` cachea el `unicodedata.normalize` (se llamaba 25 veces por frame).
- `ancho_texto()` usa la caché de texto en vez de renderizar para medir.
- `REC.fondo_tocado(ruta, alpha)`: **pega el velo oscuro al fondo una sola
  vez**. El fondo pasa de 2 blits a pantalla completa (uno de ellos SRCALPHA)
  a 1 blit opaco.
- `Transicion.dibujar` y `fundido_entrada` reutilizan una Surface global
  (`_capa_color`) en vez de crear una de 4 MB por frame.

### 3.2 La trampa de las cachés: colores y alphas animados

Un `Boton` late el hover y el banner del duelo se apaga: si se cachea con el
color exacto, **cada frame deja una entrada nueva** y la cache crece sin
límite (y encima nunca vuelve a acertar).

- `ui.color_cache(color)` agrupa los canales en múltiplos de `PASO_COLOR = 8`.
- `resplandor` agrupa el alpha en 16 niveles; `_overlay_captura` idem.
- Los **textos translúcidos no se cachean** (agruparles el alfa se vería a
  saltos); los opacos sí.
- `tests/test_estabilidad.py` tiene tests que blinda esto: hover continuo,
  banner apagándose y "la cache no crece sola".

### 3.3 Partículas del fondo (`ui.FondoAnimado`)

Era lo más caro con diferencia: 70 `draw.circle` sobre una Surface SRCALPHA
de 1280×800 que además había que **limpiar (4 MB) y pegar entera con alfa**
en cada frame. Ahora son 24 sprites pre-renderizados (8 brillos × 3 radios)
pintados con `BLEND_RGBA_ADD` directamente sobre la pantalla.

Nativo: **1,31 ms → 0,38 ms** por frame. La diferencia visual es de 8.679
píxeles de 1.024.000 (0,85 %) con una media de 0,16 por canal: las motas ahora
tienen brillo en vez de ser planas. `python tests/comparar_fondo.py` genera
las dos capturas para comparar.

### 3.4 Duelo y cartas (`partida.py`, `cartas.py`)

Cacheados: sombra de carta, tinte de casilla, barra del HUD, badges del
marcador, velo de captura, cajas del cartel de resultado, capa de partículas.
`cartas.crear()` ahora **también cachea las variantes escaladas** (antes
hacía `smoothscale` en cada llamada) y hay `cartas.miniatura()`.

### 3.5 Pantallas: `pygbag` leía un JSON 7 veces por frame

`pantallas.elegir_faccion` llamaba a `campana.cargar_perfil()` (abrir +
`json.load`) **una vez por facción y por frame**, y escalaba 12 cartas por
frame. El perfil se lee ahora **una vez** antes del bucle y las miniaturas van
cacheadas. Esa pantalla pasó de 35 a 48,5 fps.

### 3.6 Audio: WAV → OGG

`assets/musica` eran 5,6 MB de WAV. `tests/wav_a_ogg.py` los convierte con
ffmpeg (busca el binario de `imageio-ffmpeg` si no está en el PATH) y
`audio.py` carga el `.ogg` cuando detecta Emscripten (`audio.es_web()`). En
nativo y en el `.exe` se sigue usando el WAV, así que los tests no cambian.

### 3.7 `plantilla_index.tmpl` (plantilla propia de `index.html`)

`pygbag --build --template plantilla_index.tmpl .` — copia de la de pygbag con
cuatro cambios:

1. **`fb_width`/`fb_height` = 1280/800** (lo que realmente dibuja el juego;
   antes ponía 1280×720) y `fb_ar: 1.6`.
2. **`gui_debug: 0`**: con 2, pygbag actualiza el DOM en cada frame.
3. **Canvas centrado con bandas negras** en vez de `width/height: 100%`, que
   deformaba la imagen en pantallas 16:9. Lleva `!important` porque
   `window_resize()` de SDL escribe estilos **inline** en el canvas
   (`position/inset/width/height`) y eso pisa la hoja de estilos.
4. Fondo de la página `#0e0f16` (el gris `#7f7f7f` del template se veía mucho)
   y `<title>` con el nombre del juego.

### 3.8 `pygbag.ini`: un bug de pygbag que costaba 8,9 MB

El filtro de pygbag (`pygbag/filtering.py`) compara con `Path.match()` y con
`startswith("<patrón>/")`. **Un patrón sin barra inicial solo bloquea la
carpeta de primer nivel, no sus subcarpetas**, así que `gravedad/frames/`
(14 PNG de 617 KB) se colaba en el paquete. Hay que escribir `"/gravedad"`
(con la barra delante). Lo mismo con `"/tests"`, `"/auditoria"`, etc.

Además se excluyen los `.wav` (en la web se usa el `.ogg`) y los ficheros de
desarrollo.

### 3.9 Medidor de fps (`depurar.py`)

```bash
python main.py --fps        # escritorio
```

En la web no hay `sys.argv`, así que va por variable de entorno:
`TT_FPS=1`. Dibuja fps / ms medios / p95 en la esquina. Está apagado por
defecto y no toca el juego.

---

## 4. Cómo medirlo (lo importante: **no** optimices a ciegas)

### 4.1 Banco de pruebas nativo — `tests/bench_render.py`

Rápido, determinista y sin navegador. Mide ms/frame reales:

```bash
python tests/bench_render.py              # duelo, fondo, portada, elegir_faccion
python tests/bench_render.py 400          # más muestras
python tests/bench_render.py 40 --perfil  # cProfile ordenado por tottime
```

Usa el driver de video falso, así que no abre ventana. Cifras finales:

```
duelo            : media   1.14 ms   -> techo 875 fps
fondo            : media   0.38 ms   -> techo 2634 fps
portada          : media   1.05 ms   -> techo 954 fps
elegir_faccion   : media   2.41 ms   -> techo 414 fps
```

El ranking de dónde se va el tiempo es el mismo que en el navegador (todo es
~14× más lento en wasm), así que sirve para decidir. `elegir_faccion` se mide
con la pantalla real (`pantallas.py:258`) y un reloj que no espera, cortando
el bucle a N frames.

### 4.2 En navegador — la cifra que manda

1. Build con el medidor dentro (solo para medir): poner
   `if FPS or os.environ.get("TT_FPS") or True:` en `main.py`, construir,
   y **deshacerlo después** para la build final.
2. Servir y abrir con Playwright, esperar ~18 s, hacer clic en el cartel
   verde y capturar pantalla: el medidor sale en la esquina inferior
   izquierda.

Trampas reales:

- El puerto **8000** es obligatorio para el servidor local: pygbag detecta
  `http://localhost:8...` y reescribe el índice de paquetes a
  `http://localhost:8000/cdn/` (`pep0723.py:206`). Con otro puerto, el
  navegador intenta bajar la rueda de pygame de ahí y falla.
- Por eso el zip de itch.io **no lleva `cdn/`**: en itch.io la URL no es
  localhost y se usa el CDN oficial. Para probar el camino de itch.io en local
  hay que servir el zip en **`http://127.0.0.1:<otro puerto>`** (no
  `localhost`), que es justo lo que hace que no se reescriba el CDN.
- La rueda para el servidor local:
  ```
  build/web/cdn/cp312/pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl
  ```
- Errores de consola **esperados**: `PyMain: BrowserFS not found` y
  `MEDIA USER ACTION REQUIRED` (el desbloqueo de audio). Cualquier
  `cross_file.fetch 404` o error de CORS = lo del puerto 8000.
- Playwright MCP se cuelga si el renderer se queda al 100 %; matar el Chrome
  del MCP:
  ```powershell
  Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'chrome.exe' -and $_.CommandLine -like '*ms-playwright-mcp*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
  ```

---

## 5. Comandos

```bash
cd E:\openCode\TripleTriad

# validar
python -m unittest discover tests          # 164 tests
python main.py --check                     # recursos
python tests/demo_pantallas.py             # capturas de todas las pantallas
python tests/demo_capturas.py
python tests/bench_render.py               # ms/frame
python tests/wav_a_ogg.py --check          # ¿hay ogg que falten?

# build web
python -m pygbag --build --disable-sound-format-error --template plantilla_index.tmpl .

# rueda de pygame para el servidor local (solo una vez)
python -c "import urllib.request,os;os.makedirs('build/web/cdn/cp312',exist_ok=True);urllib.request.urlretrieve('https://pygame-web.github.io/cdn/cp312/pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl','build/web/cdn/cp312/pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl')"

# zip para itch.io (index.html en la raiz, sin cdn/)
python tests/empaquetar_itch.py

# servidor de pruebas (puerto 8000 obligatorio)
cd build\web && python -m http.server 8000
```

**Nota:** `pygbag --build` falla con `FileNotFoundError: build/web/tripletriad.apk`
si `build/web` no existe (lo borra `rm -rf`). Crear la carpeta antes.

---

## 6. Subida a itch.io

1. `python tests/empaquetar_itch.py` → `tripletriad-web.zip` (4,62 MB).
2. En itch.io → **Upload new project** → **Uploads**:
   - subir `tripletriad-web.zip`;
   - marcar **"This file will be played in the browser..."**;
   - elegir **"Extract the .zip"**.
   - En **Embed options**: viewport 1280×800 y "Show game at full size"
     (la plantilla ya se encarga de centrar y respectar la proporción).
3. **Game details**: categoría *Web*, *Classification* → *Game*.
4. Dejarlo en **draft** hasta probarlo; para compartir con amigos basta con el
   link de "view".
5. **Probar el link en el móvil antes de mandarlo**: el juego es de arrastrar
   cartas con el ratón; lo táctil suele mapearse a ratón en pygame-ce, pero
   conviene comprobarlo y que el lienzo se vea legible en vertical (con
   `overflow: hidden` y el canvas centrado se ve con bandas, sin scroll).

**Plan B** (si aun así la web no convence): subir `TripleTriad.exe` (o un zip
con el exe) como *downloadable* en la misma página de itch.io. Funciona ya
mismo y no depende del rendimiento en navegador.

---

## 7. Reglas para no romperlo

- **Cero `await asyncio.sleep(0)` fuera de los bucles**: sin él el intérprete
  WASM no devuelve el control y la página se congela (ya se comprobó).
- **Una sola vez por frame**, no más.
- **Toda función que dibuja un frame** debe ser `async def` y ceder una vez
  por frame; quien la llame usa `await`.
- **Nada de `Surface` a pantalla completa dentro de un bucle de dibujado**:
  en la web son 4 MB de basura por frame. Si hace falta, reutilizar una
  Surface global (`ui._capa_color`) o componer una vez y cachear.
- **Nada de `font.render`, `smoothscale`, `rotate` ni lectura de ficheros por
  frame**: todo eso va cacheado. Si metes algo nuevo, `tests/bench_render.py`
  lo enseguida.
- **Al cachear por color, agrupar** (`color_cache`) o la cache crece sin
  parar.
- `tests/test_estabilidad.py` comprueba varias de estas cosas; correrlo
  siempre antes de dar algo por bueno.

---

## 8. Estado de git

Rama `complejidad`. Todo el trabajo web y visual de este árbol está
**committed** (ver §9 del README o `git log`). Ficheros de soporte que no
entran en la build web: `tests/bench_render.py`, `tests/wav_a_ogg.py`,
`tests/comparar_fondo.py`, `tests/empaquetar_itch.py`, `depurar.py`
(sí viaja, 1,9 KB), `plantilla_index.tmpl`, `pygbag.ini`.

## 9. Definido como "terminado"

- [x] ≥45 fps en navegador en todas las pantallas (48,5-62,5 fps).
- [x] 164 tests + `--check` + demos en verde.
- [x] Paquete de 4,62 MB con `index.html` en la raiz y sin `cdn/`.
- [x] Probado el camino de itch.io en local (`127.0.0.1`, CDN oficial).
- [x] Commit.
- [ ] **Subir a itch.io y probar el link en el móvil** (requiere la cuenta
      del usuario).
