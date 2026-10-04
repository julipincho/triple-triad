# Triple Triad — El Umbral del Trono

Juego de cartas estilo Triple Triad (Final Fantasy 8) en Python + pygame.
Siete facciones, modo campana con historia, cinematicas, musica por faccion
y un final distinto segun la faccion que elijas.

## Audio

- Siete pistas por facción, generadas con `assets/crear_sonidos.py`.
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

Siete bandos, cada uno con su mazo de 5 cartas, su paleta, su musica y su arco
narrativo. Elegir faccion **decide contra quien te enfrentas y que final
consigues**: nunca te juegas contra tu propia faccion en campana.

| Faccion | Estilo | Habilidades | Jefe final |
|---|---|---|---|
| Humanos | Muro, guardia y rey | `muro` | Ignarok, Rey Oscuro (dragon) |
| Orcos | Fuerza por acumulacion | `furia`, `quema`, `embestida` | Lyra, Dama del Bosque (elfo) |
| Elfos | Valores altos en cruz | — | Ignarok (dragon) |
| Goblins | Barato y veloz | `quema` | Ignarok (dragon) |
| Hombres Lobo | Domina el centro y las cadenas | — | La Condesa (vampiro) |
| Vampiros | Equilibrio agresivo | — | Fenris (hombre lobo) |
| Dragones | Fuerza bruta | `quema` | Aldric, Rey de los Humanos |

### Habilidades de carta

- `quema`: captura a cualquier carta enemiga adyacente, sin comparar valores.
- `muro`: su lado mas alto no puede ser capturado.
- `furia`: +1 a todos sus lados si toca una carta amiga en el tablero.
- `embestida`: +2 a todos sus lados en la casilla central.

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
  entre sesiones. Las partidas antiguas se migran al formato nuevo.

## Estructura

- `main.py` — punto de entrada: portada, menu, campana y duelos
- `reglas.py` — reglas (basica, Same, Plus, cadena, habilidades, sinergia, elemento)
- `facciones.py` — identidad, paletas y arcos narrativos de cada bando
- `mazos.py` — los siete mazos
- `campana.py` — grafo de nodos, recompensas, encuentros, finales y guardado
- `partida.py` — bucle de duelo, HUD, efectos e IA
- `pantallas.py` — portada, menu, selector, mapa, draft, coleccion, ajustes
- `cinematicas.py` — motor de cinematicallyas y todos los textos
- `cartas.py` — render de cartas
- `ui.py` — tema, tipografia, botones, transiciones, tooltips
- `audio.py` — mezcla de efectos y musica por faccion
- `paths.py` — rutas de recursos y datos (funciona empaquetado)
- `generar_cartas.py` — regenera arte con Pollinations (cartas, avatares, fondos)
- `assets/crear_sonidos.py` — genera efectos y musica chiptune (sin red)
- `diagnostico.py` — comprueba que no falta ningun asset (`main.py --check`)
- `tests/` — tests de reglas/campana/assets/flujo y demos visuales

## Tests y auditoria visual

Cada cambio debe aprobarse asi:

1. **Tests de reglas, campana, assets y flujo:**
   ```
   cd TripleTriad
   python -m unittest discover tests -v
   ```
   (94 tests: reglas, habilidades, campana, flujo completo y assets)
2. **Demos visuales (screenshots):**
   ```
   python tests/demo_capturas.py     # tablero, capturas y habilidades
   python tests/demo_pantallas.py    # todas las pantallas y cinematicallyas
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