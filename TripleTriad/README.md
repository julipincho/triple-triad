# Triple Triad — El Umbral del Trono

Juego de cartas estilo Triple Triad (Final Fantasy 8) en Python + pygame.
Diez facciones, modo campana con historia, mini campanas, cinematicas,
musica por faccion y un final distinto segun la faccion que elijas.

## Audio

- Diez pistas por facción, generadas con `assets/crear_sonidos.py`.
- **El duelo tiene su propia banda sonora** (`musica_duelo`): no se reutiliza la
  pista del rival, así que cualquier enfrentamiento suena igual de tenso.
- Los menús usan `musica_explora`, más tranquila. Las cinemáticas cambian a la
  pista de la facción que aparece en escena.

## Estabilidad

- **Tope de 60 FPS** en todo el juego. La constante vive en `ui.LIMIT_FPS` y
  ningun bucle puede usar otro valor: lo verifica `tests/test_estabilidad.py`,
  que tambien comprueba que todo `while True` limita los fps (directamente o
  delegando en una pantalla que ya lo hace).
- **Memoria**: los fondos, las capas de oscurecido y las vinetas se escalan y
  cachean una sola vez (`ui.REC.fondo_pantalla`, `capa_oscurita`, `vineta`).
  Antes se reescalaban a pantalla completa en cada frame, que reservaba ~4 MB por
  imagen y cada frame.
- **Ninguna pantalla deja encerrado al jugador**: las cinematicallyas se
  cierran con clic, ENTER o ESC (tambien el epilogo, que antes no admitia ESC).
- **Los errores se enseñan**: si algo falla, aparece un cartel en la ventana
  con el motivo y donde estaba el jugador, en vez de cerrar el proceso. El
  detalle tecnico va a `crash.log`.

## Correr

- Ejecutable: `TripleTriad.exe` (doble click).
- Desde codigo: `python TripleTriad/main.py`
- Modo prueba (entra en un duelo y sale solo): `python TripleTriad/main.py --test`
- Chequeo de recursos (util en el .exe): `python TripleTriad/main.py --check`

## Controles

- **Raton**: arrastra una carta de la mano al tablero. Pasar el raton levanta
  la carta y muestra la mejor casilla posible; clic = continuar en las
  cinematicallyas.
- **ESC**: pausa dentro del duelo / cerrar pantallas.
- **Flechas + ENTER**: navegar por los menus.
- **H**: recordatorio de reglas rapidas durante el duelo.
- En Ajustes: volumen de efectos y musica, pantalla completa y hoja de
  controles.

## Facciones

Diez bandos, cada uno con su mazo de 25 cartas, su paleta, su musica y su arco
narrativo. Elegir faccion **decide contra quien te enfrentas y que final
consigues**: nunca te juegas contra tu propia faccion en campana.

| Faccion | Estilo | Habilidades | Jefe final |
|---|---|---|---|
| Humanos | Muro, guardia y rey | `muro`, `furia` | Ignarok, Rey Oscuro (dragon) |
| Orcos | Fuerza por acumulacion | `furia`, `quema`, `embestida` | Lyra, Dama del Bosque (elfo) |
| Elfos | Valores altos en cruz | — | Ignarok (dragon) |
| Goblins | Barato y veloz | `quema` | Ignarok (dragon) |
| Hombres Lobo | Domina el centro y las cadenas | — | La Condesa (vampiro) |
| Vampiros | Equilibrio agresivo | — | Fenris (hombre lobo) |
| Dragones | Fuerza bruta | `quema`, `muro`, `embestida` | Aldric, Rey de los Humanos |
| Elfos Nocturnos | Sombras precisas | `quema`, `muro` | Ignarok, Rey Oscuro (dragon) |
| Hombres Pantera | Caza en silencio | `furia`, `embestida` | Fenris (hombre lobo) |
| Hombres Lagarto | Paciencia acorazada | `muro`, `quema` | Vorg, Señor de la Guerra (orco) |

### Reparto antes del duelo

Cada faccion tiene 25 cartas, pero a cada duelo **se sortean 5** (tu y el
rival). El sorteo es determinista por campana, nodo e intento: recargar no
re-sortea, pero cada campana e intento varian. Las recompensas mejoran o
amplian tu coleccion entre duelos.

### Habilidades de carta

- `quema`: gana o empata la comparación contra cada vecina (sin Same ni Plus), y el muro de la vecina la protege.
- `muro`: su lado mas alto no puede ser capturado.
- `furia`: +1 a todos sus lados si toca una carta amiga en el tablero.
- `embestida`: +2 a todos sus lados en la casilla central.

## Sobres

- **Sobre**: 3 cartas al azar del pool (tu faccion + aliados) con rareza
  ponderada (LEGENDARIA 2 / RARA 6 / COMUN 12). Se consigue como recompensa
  post-duelo (ruinas, fortaleza, asalto) y en el encuentro de la Caravana.
- **Revelado una a una** con fanfarria en legendarias; ESC sale en cualquier
  momento.
- **Duplicadas dan +1** al lado mas bajo de la carta que ya tienes (max 10).
- **Odds por sobre**: ~10% de legendaria (3.4% por carta × 3), ~57% de
  alguna rara; el pity garantiza una legendaria si 9 sobres seguidos no dan
  ninguna (minimo 6 cada 60 sobres).
- La **coleccion** esta paginada (10 por pagina) con filtros de habilidad
  (tecla F) y rareza (tecla R); clic en una carta abre su ficha ampliada.
  Mejora y reemplazo tambien paginan (flechas o botones).

## Coleccion, moneda y deck building

- Empiezas con las 10 comunes (o casi) de tu faccion; el resto se descubre
  con sobres, draft y tienda. Migrar resetea la coleccion pero conserva nodos.
- Moneda: 5 por duelo + 20 por victoria + 2 por captura. El sobre cuesta 60.
- El mazo de run son 10 poseidas (1 legendaria y 3 raras como maximo) y el
  duelo sortea 5. Las mejoras de campana son temporales: al terminar, tus
  cartas vuelven a su base.

## Tutorial
- **Primer arranque**: tras la portada se ofrece `JUGAR TUTORIAL` o `SALTAR`.
  Saltar también marca el tutorial como visto (`perfil.json`) y no vuelve a
  preguntar. Siempre se puede repasar desde el botón `TUTORIAL` del menú
  o con `T` en la pantalla de ayuda.
- **Manual visual (10 páginas)**: cada regla con su demo en un mini-tablero
  real y dos bloques: *qué es* y *para qué sirve*.
- **4 prácticas guiadas** (básica, Same, cadena y habilidades en 3 pasos:
  muro, furia y embestida) sobre el motor real: la jugada se valida y el
  juego explica por qué vale o no, sin rechazos mudos.
- **ESC o botón SALIR en cualquier momento** (pide confirmación) y el progreso
  por paso (`tutorial_paso`) permite retomar donde se quedó.

## Cinematica de intro

Tras la portada y solo la primera vez, una cinematica de 5 escenas cuenta
como el mundo llego al Umbral (fondos `amanecer`, `umbral`, `estandartes`).
Se puede saltar y queda marcada en el perfil.

## Modo campana

Cinco duelos con una bifurcacion real:

```
apertura -> senda -> bifurcacion -> fortaleza -> asalto -> trono
                          /   \
                     aldea     ruinas
```

- Cada nodo tiene su cartel de escena, su rival y su dificultad (0-3, aplicada
  a las cartas del rival).
- Tras cada victoria eliges una **recompensa**: entrenamiento, recluta (draft
  de 3 cartas), sigilo (mejora permanente) o pacto (desbloquea un mazo ajeno
  para el draft).
- Entre duelos pueden aparecer **encuentros** con dos opciones y consecuencias
  reales (debilitar al rival, mejorar tu carta mas debil, etc.).
- El final depende de como lo completes: **dominio** (pocos reintentos y racha
  alta), **equilibrio** o **caos**. Cada faccion tiene sus tres finales, que se
  desbloquean en el perfil (`perfil.json`).
- La partida se guarda automaticamente en `campana.json` y se puede continuar
  entre sesiones. Las partidas antiguas se migran al formato nuevo (la
  coleccion se rellena con las base que falten).

## Mini campanas

Al completar una campana principal se desbloquea `MINI CAMPANA` en el menu:
3 duelos lineales para Elfos Nocturnos, Hombres Pantera o Hombres Lagarto,
cada uno con su final propio (queda en `perfil.json`). La mini vive solo en
sesion: abandonarla la descarta sin tocar `campana.json`.

## Estructura

- `main.py` — punto de entrada: portada, menu, campana y duelos
- `reglas.py` — reglas (basica, Same, Plus, cadena, habilidades, sinergia, elemento)
- `facciones.py` — identidad, paletas y arcos narrativos de cada bando
- `mazos.py` — los diez mazos (25 cartas por faccion, 250 en total)
- `campana.py` — grafo de nodos, mini campanas, recompensas, encuentros, finales y guardado
- `partida.py` — bucle de duelo, HUD, efectos e IA (acepta `guia=` del tutorial)
- `pantallas.py` — portada, menu, selector, mapa, draft, coleccion, ajustes
- `tutorial.py` — manual visual, 4 prácticas guiadas y puerta de primer arranque
- `cinematicas.py` — motor de cinematicallyas y todos los textos
- `cartas.py` — render de cartas
- `ui.py` — tema, tipografia, botones, transiciones, tooltips
- `audio.py` — mezcla de efectos y musica por faccion
- `paths.py` — rutas de recursos y datos (funciona empaquetado)
- `generar_cartas.py` — regenera arte con Pollinations (cartas, avatares, fondos)
- `assets/crear_sonidos.py` — genera efectos y musica chiptune (sin red)
- `diagnostico.py` — comprueba que no falta ningun asset (`main.py --check`)
- `tests/` — tests de reglas/campana/assets/flujo/tutorial/mini y demos visuales
- `tests/auditoria_visual.py` — puerta visual: falla si hay textos desbordados
  o elementos fuera de pantalla (la usan los tests y el flujo manual)

## Tests y auditoria visual

Cada cambio debe aprobarse asi:

1. **Tests de reglas, campana, tutorial, mini, assets y flujo:**
   ```
   cd TripleTriad
   python -m unittest discover tests -v
   ```
   (245 tests: reglas, habilidades, campana, tutorial, mini campanas,
   intro, auditoria visual y de poder, sobres, coleccion, balance,
   flujo completo y assets)
2. **Demos visuales (screenshots):**
   ```
   python tests/demo_capturas.py     # tablero, capturas y habilidades
   python tests/demo_pantallas.py    # todas las pantallas y cinematicallyas
   python tests/demo_tutorial.py     # las 10 paginas y las 4 practicas
   python tests/auditoria_visual.py  # puerta: 0 problemas, exit 0
   ```
   Genera PNGs en `TripleTriad/auditoria/`. `demo_pantallas.py` devuelve
   codigo 1 si alguna pantalla falla, asi que sirve como smoke test.
3. **Chequeo de recursos:** `python main.py --check`
4. Recompilar el exe tras cambios en codigo o assets:
   ```
   cd TripleTriad
   python -m PyInstaller --noconfirm TripleTriad.spec
   ```

## Assets

- `.env` — API key de Pollinations para regenerar arte (no compartir).
- El arte y el audio se pueden regenerar sin conexion (audio) o con ella
  (imagenes): `python generar_cartas.py`.

### Ilustraciones con ComfyUI (opcional, herramienta de desarrollo)

`generar_cartas_comfyui.py` genera ilustraciones de dark fantasy en estilo
pixel art 16/32-bit con CRT con el ComfyUI local (`http://127.0.0.1:8188`) y
guarda los PNG en `cartas/` (o en la carpeta de `--salida`), con el mismo
nombre `{faccion}_{slug}.png` que usa `cartas.py`.

Pipeline validado en la hoja de contactos (ver `auditoria/evaluacion_*.md`):

- Checkpoint **Pixel Art Diffusion XL (Sprite Shaper)** como base.
- **IP-Adapter Plus** (`ip-adapter-plus_sdxl_vit-h`) con la imagen ancla del
  moodboard (`estilo/ancla.png`, recorte elegido por la direccion de arte),
  peso **0.35** y `--peso-tipo "style transfer"`: da paleta, textura y luz del
  moodboard sin imponer la cara del ancla (a 0.8 todos los personajes salian
  con el mismo rostro humano).
- La biblia de estilo vive en `estilo.py` (la saca `extraer_estilo_moodboard.py`
  del moodboard `E:\AI\moodboard.png`).
- Despues, `postprocesar_cartas.py` lleva cada PNG a la rejilla logica de la
  carta (56x79 -> 112x158 con vecino mas cercano) y aplica brillo objetivo 90,
  saturacion 40, scanlines 0.15, amplitud 14 y dither Bayer.
- El encuadre fijo es busto de carta (`FIJO` en `estilo.py`): primer plano
  cerrado de cabeza y hombros. Las criaturas grandes (dragon, lagarto, lobo,
  pantera) llevan ademas un refuerzo de close-up por faccion
  (`ENCUADRE_EXTRA`).

**Lote actual (oct 2026):** las 250 cartas de `cartas/` estan regeneradas con
este pipeline (semillas deterministas por nombre, escenas auto escritas por
Gemini en `lote_completo.json` via `hacer_lote.py`). El jurado de arte lo
cerro con 8.8/10 en la hoja de contactos (`auditoria/hoja_lote_final2.png`).
Las cartas que escapaban del busto se retocaron a mano (semilla nueva +
descripciones sin entorno) y quedaron aprobadas.

```
python generar_cartas_comfyui.py --nombre "Conde Nocturno" --faccion vampiro \
    --raza vampiro --clase nigromante --rareza LEGENDARIA \
    --descripcion "caliz de sangre sobre el trono roto" --estilo carta
python generar_cartas_comfyui.py --lote lote_ejemplo.json    # muchas fichas
python hacer_lote.py               # reconstruye lote_completo.json (250 fichas)
python postprocesar_cartas.py --entrada cartas_raw_pixel --salida cartas
python hoja_contactos.py           # hoja A/B antes de tocar el/los asset(s)
python evaluar_estilo.py auditoria/hoja_contactos.png   # jurado Gemini
python generar_cartas_comfyui.py --solo-prompt ...       # solo el prompt
```

- Recibe nombre, faccion, raza, descripcion, clase, rareza, estilo y `--seed`
  opcional, y construye el prompt solo: traduce raza/clase/rareza/estilo,
  anade la atmosfera de la faccion y su color de acento, y un sufijo fijo
  de dark fantasy para que toda la serie sea coherente.
- El juego **no** importa este script: ComfyUI es solo para crear assets y
  si no esta arrancado, el juego funciona igual.
- Sin `--seed` la semilla es aleatoria (se imprime para poder repetirla).
  Si el PNG ya existe se omite (`--fuerza` lo regenera).
- **Arranque automatico:** si ComfyUI no responde, el script lo arranca el
  solo (`E:\AI\start-comfyui.bat` en una ventana nueva, listo en ~10 s) y
  sigue generando; `--no-arrancar` lo desactiva y `--bat-arranque` cambia
  la ruta del bat.
- Solo biblioteca estandar, sin dependencias y sin claves de API.