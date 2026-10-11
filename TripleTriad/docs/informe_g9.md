# G9 - Validacion de candidata de produccion

> Estado parcial. Lo que esta aqui se ha **ejecutado y medido**. Lo que no se
> ha hecho dice explicitamente porque y no se da por bueno.

> Revision final: consultar `docs/cierre_candidata.md` para el estado consolidado.
> Este documento conserva resultados historicos; no todos son una validacion
> actual ni una prueba de extremo a extremo del ejecutable.

## Recorridos integrados (hechos)

`tools/recorridos_g9.py` recorre el juego con la campana real y comprueba que
no se pierde progreso. Tambien corre dentro de la suite
(`tests/test_recorridos_g9.py`), para que un recorrido roto pare el build.

| recorrido | comprueba |
|---|---|
| nuevo jugador | sin partida, el menu ofrece empezar de cero |
| reanudacion | guardar y reabrir conserva nodo y mazo; se puede continuar |
| derrota y reintento | perder no avanza el nodo; la moneda es la del contrato (base + capturas, + victoria si se gana) |
| abandonar | abandonar NO avanza nodo, NO cuenta derrota, NO toca el perfil |
| compra y equipar | cobrar exactamente el precio, entregar, llegar a la coleccion, cobrar igual la segunda vez |
| mejorar carta | sube el lado mas debil, se refleta en el mazo, no cambia la carta |
| hasta el final | la campana se completa sin repetir nodo ni bloque |

Resultado: **7 de 7 sin problemas**.

### Lo que este recorrido destapo

El primer montaje fallaba en seis de siete, y **cinco de los fallos eran del
propio arnes, no del juego**. Se cuenta porque es el riesgo real de estas pruebas:

- Se afirmaba que perder no debe dar moneda. **Es falso a proposito**: un duelo
  *completado* paga base + capturas, gane o pierda, y el desglose se lo enseña
  al jugador. Lo que no debe pagar es **abandonar**, que es lo que comprueba
  otro recorrido.
- Se media el valor de un lado supuesto en vez del lado que devuelve
  `mejorar_carta` (el mas debil).
- Se media la mejora sobre la base cruda, pero las mejoras son **deltas**: viven
  en `estado["mejoras"]` y se aplican en `cartas_jugador`.
- Se mezclaron claves de carta en mayusculas (`reglas.LADOS`) con las del
  guardado en minusculas.

Ninguno era un fallo del juego. Se deja constancia porque un recorrido integrado
que falla por el arnes es peor que no tener ninguno: entrena a ignorar el
veredicto.

## Texto ampliado: dos desbordes que la auditoria normal no veía

G7 pide "texto y botones legibles **sin recorte** ... con texto ampliado". La
auditoria visual mide los rects a tamano normal, asi que todo pasaba. Con la
escala al 125% (lo que hace el jugador al activar TEXTO GRANDE) aparecieron
**dos fallos reales** en `tools/auditar_texto_ampliado.py`:

1. **Portada**: las dos lineas del titulo se solapaban. La separacion estaba
   fija en 48 px y la linea crece con la fuente; ahora se calcula con la escala.
2. **Coleccion**: la etiqueta de estado de la ultima fila de cartas caia
   **encima del boton `<`** de paginacion. La etiqueta va `rect.bottom + 32` y
   la rejilla acababa en y=550, dejando la etiqueta en 582, dentro de la fila
   de botones (574-606). Se subió la rejilla para que respire.

Ninguno se veía a tamano normal: el solapamiento era de 2 px y la tolerancia
de la auditoria no lo reportaba. `tests/test_texto_ampliado.py` ejecuta ahora
la misma auditoria con el texto al 125% dentro de la suite. Comprobado que
detecta las dos regresiones si se revierten los arreglos.

## El techo del modo lectura estaba sin auditar (160%)

G7 pide "texto y botones legibles **sin recorte** ... con texto ampliado". Se
auditaba al 125%, que es lo que pone el ajuste TEXTO GRANDE, pero
`ui.fijar_escala_texto` admite hasta **1.6**. Al 160% aparecieron fallos que
el 125% no detectaba:

1. **Portada**: las dos lineas del titulo se solapaban. El hueco estaba
   estimado con `tam * 1.28`, o sea sobre el tamano *pedido*, no sobre el
   *dibujado*: a 160% una linea pedida a 40 px se pinta a 64 px y el hueco
   estimado se quedaba a medias. Ahora se mide con `ui.alto_texto()`.
2. **Ficha de faccion** (`14_elegir_faccion`): el bloque HABILIDADES se
   montaba encima de los chips de rivales y estos caian fuera del panel, sobre
   el boton ELEGIR Y EMPEZAR. Los rivales se anclan ahora al pie del panel y
   las habilidades se recortan al espacio que sobra.
3. **Lineas de parrafo**: `ui.parrafo` avanzaba en pixeles fijos mientras la
   linea crecia con la escala. Medido: a tamano 7 y escala 1.6 la linea se
   dibuja a 12 px de alto pero avanzaba 11, y las lineas se tocaban. El
   interlinea escala ahora con la tipografia.

### Punto ciego de la propia auditoria

Al revisar lo anterior salio algo peor: `tests/auditoria_visual.py` **nunca
comparaba dos textos del mismo panel** (`if c1 is None or c1 != c2`). El
motivo declarado eran los parrafos envueltos, pero un parrafo cuyas lineas se
pisan es justo el defecto que hay que ver. Con la comparacion siempre activa
aparecieron dos mas, ambos al 160%:

- `12_nombre`: el parrafo de ayuda se montaba sobre el campo de texto. El
  panel tenia 340 px de alto fijos y el campo estaba en un offset fijo que
  suponia una sola linea por parrafo; ahora el alto y la posicion del campo se
  calculan con el texto que va a caber de verdad.
- `19_coleccion`: el nombre de la faccion se montaba sobre las marcas
  `[X] [ ] [ ]` del panel de finales. El nombre se ajusta al hueco que dejan
  las marcas.

Y con la ficha lateral auditada **faccion por faccion** (antes solo se
auditaba la primera, y el lema, el arco y las habilidades cambian en cada una)
salieron cuatro mas, todos al 160%:

- `hombre_lobo`, `hombre_pantera`, `hombre_lagarto`, `elfo_nocturno`: el paso
  de linea del nombre dentro de la ficha no escalaba, y al crecer el bloque se
  montaba sobre `jefe:` / `mejor racha:`.
- `elfo_nocturno` ademas: `+15 mas en el mazo` caia encima de `TUS RIVALES`.
- `14b_elegir_faccion_rapida`: la pista "Pulsa ELEGIR Y EMPEZAR para confirmar"
  media 468 px centrada en el boton y **se salia por la derecha** de la
  pantalla (856..1324 en un lienzo de 1280).

Al cerrarlo, **0 solapamientos en las tres escalas** para las 22 pantallas,
las 10 fichas de faccion y el modo duelo rapido.

### Dos cambios acoplados, y como se comprueban

El nombre de la faccion (paso de linea) y `jefe:` (anclaje al pie) se
arreglaron juntos, y son **acoplados**. La afirmacion anterior de que ambos
valores originales no producian solapamiento contradecia el resultado del
par descrito abajo. No se usa esa afirmacion como evidencia de cobertura.

La comprobacion que si vale es la del par: con los dos a su estado original
(`ly += 16` y `rect.bottom - 34`) la auditoria reporta 12 problemas en 4
facciones al 160%, y `test_techo_de_escala_no_rompe_ninguna_pantalla` falla.
Queda anotado en el propio codigo para que no se "simplifique" uno solo.

### Lo que estos tests detectan y lo que no

Comprobado revirtiendo cada arreglo:

| Regresion reintroducida | Test que la detecta |
|---|---|
| interlinea sin escala | `test_lineas_de_un_parrafo_no_se_pisan` |
| recorte de habilidades desactivado | `test_ajuste_texto_grande_no_rompe_ninguna_pantalla` |
| nombre de faccion sin ajustar (panel de finales) | `test_techo_de_escala_no_rompe_ninguna_pantalla` |
| pista larga de duelo rapido | `test_techo_de_escala_no_rompe_ninguna_pantalla` |
| parrafo de ayuda sobre el campo (nombre) | `test_techo_de_escala_no_rompe_ninguna_pantalla` |
| nombre + `jefe:` a su estado original (par) | `test_techo_de_escala_no_rompe_ninguna_pantalla` |
| "Seis duelos" escrito a mano | `test_portada_pinta_los_datos_reales` |
| chip de ancho fijo (200) | `test_los_chips_caben_dentro_de_su_panel` |
| bifurcacion contada como duelo | `test_duelos_por_campana_coincide_con_el_grafo` |

Dos aprendizajes de este turno, en la linea de los cinco anteriores:

- El interlinea **no** lo detectaba la auditoria de pantallas (su tolerancia
  son 2 px y el solapamiento era de 1). Hizo falta una prueba que midiera la
  propiedad de verdad: dos lineas consecutivas no deben montarse.
- `ui.MEDIDO` no estaba: un solapamiento devolvia dos coordenadas y habia que
  buscar el texto a mano entre miles de draws. Ahora la auditoria nombra el
  texto culpable (`'HABILIDADES'`, `'nombre.'`, `'jefe: Vampiros'`...). Ese
  detalle fue lo que permitio localizar el resto en vez de adivinar.
- Auditar solo el estado inicial de una pantalla no basta cuando su contenido
  depende de datos: la ficha de faccion es un caso, y solo se vio al iterar
  por las diez.

## Un dato falso en la portada: "Seis duelos"

Mirando la portada ya corregida se ve que el chip decia **"Seis duelos"**.
Recorriendo `campana.NODOS` de verdad (senda -> bifurcacion -> aldea|ruinas ->
fortaleza -> asalto -> trono) son **cinco**. El "seis" salia de contar los
nodos del grafo, contando la bifurcacion como si fuera un duelo; el "cinco"
anterior se habia cambiado a "seis" justamente por esa cuenta.

No se ha vuelto a escribir el numero a mano: `campana.duelos_por_campana()`
recorre el grafo y devuelve el numero, y el chip lo saca de ahi junto con el
de facciones. `tests/test_chips_portada.py` comprueba tres cosas:

- que el helper coincide con un recorrido independiente del grafo por **las dos
  ramas** (aldea y ruinas), que es donde un calculo mal hecho se esconderia;
- que `duelos_por_campana()` es menor que el numero de nodos, que es lo que
  impide volver a contar la eleccion como duelo;
- que lo que **se pinta** en pantalla es lo que dicen los datos, no una copia.

Al medir el chip aparecio otro fallo: el ancho era 200 fijos y "Un final por
faccion" mide 209 al 125%, o sea que ya se salia de su propio borde. Ahora el
chip se dimensiona con `ui.ancho_texto` del texto que lleva dentro.

## El duelo no estaba auditado, y la propia auditoria se estaba callando

Al intentar meter **el duelo** en `tools/auditar_texto_ampliado.py` (la pantalla
principal del juego, y no estaba en la lista) salieron dos cosas:

1. **Un solapamiento real**: la pista "M: movimiento reducido NO" terminaba
   exactamente en el borde de la etiqueta "ELEGIDA" de la carta seleccionada.
   A tamano normal se tocaban; al 125% se solapaban de verdad (4 px medidos).
   Las pistas se anclan ahora a `MANO_Y`, no a coordenadas sueltas.
2. **La auditoria daba "OK" a una pantalla que no se habia dibujado.** Al
   anadir el duel rapido, la ayuda, el cartel de error, la pantalla de error,
   el epilogo y la comparacion de reemplazo, dos de ellas fallaban al
   construirse y `correr_pantalla` se comia la excepcion: sin frames no hay
   rects que auditar, y `auditar_rects` devolvia una lista vacia que se leia
   como "cero defectos". El fallo mas grave posible se camuflaba como aprobado.

Comprobado: con una pantalla rota inyectada a proposito, el test **sin** la
guarda pasa y **con** la guarda falla.

## Y debajo de eso: dos herramientas se peleaban `pygame.display.flip`

Al arreglar lo anterior, la suite entera empezo a fallar con las 32 pantallas
"sin frames". La causa no era el cambio del duelo:

- `tests/auditoria_visual.py` y `tools/auditar_contraste.py` reescribian los dos
  `pygame.display.flip` por su cuenta. Como es el **mismo** atributo, la ultima
  en engancharse se comia el hook de la otra: la segunda en ejecutarse se
  quedaba sin frames y auditaba cero.
- `tools/auditar_contraste.py` **no midio ninguna pantalla** en cuanto se
  arreglo eso, y lo Wrapaba en un "0 de 0, todo correcto".

Solucion: `ui` es el unico dueno del enganche. `ui.activar_medicion()` lo
instala (y lo repone si alguien lo replaces) y `ui.observar_flip(fn)` entrega a
cada observador **el frame exacto** de ese flip, asi que rects y colores van de
la mano sin depender de cuando se lea la lista compartida.

De paso:

- `_volcar_frame` estaba **definido dos veces** en `ui.py`; la segunda perdia la
  guarda `if not MEDIR` y era la que mandaba.
- La herramienta de contraste **no era reproducible**: dos ejecuciones seguidas
  daban 6 y 10 textos con algun pixel desfavorable. Los fondos tienen estrellas
  y velos animados. El veredicto se apoya en la media de la zona (estable); la
  columna de "peor pixel" es el minimo individual y lo mueve el fondo. Ahora la
  herramienta lo dice en su propia salida.
- `_pintar_un_frame` cortaba en el primer `reloj.n >= 2`, y `encuentro` primero
  lanza una cinematica: se quedaba **sin un solo texto** y pasaba por medida.
  Con la espera de un par de vueltas mas, `encuentro` mide (contraste medio
  16.7).
- Medir cero textos ahora se cuenta como **fallo** (`SIN_MEDIR`, codigo de
  salida 1), no como aprobado.

Y una correccion propia: `fijar_escala_texto` encendia la medicion cuando la
escala era > 1. El modo lectura lo activa el jugador en el juego normal, asi
que eso era pagar una instrumentacion de diagnostico (un rect por texto y
panel, mas la busqueda de su panel contenedor) en produccion. Ahora la medicion
la encienden solo las herramientas.

`tests/test_instrumentacion.py` fija las tres cosas. Revertidas una a una:
quitar la guarda de errores, devolver el enganche multiple o volver a encender
la medicion desde el modo lectura, y el test correspondiente falla.

### Resultado

`tools/auditar_contraste.py` mide ahora **11 pantallas, 198 textos**, sin
avisos y sin pantallas sin medir, y todas pasan el criterio documentado
(contraste medio >= 4.5). Antes media 10 pantallas con el emparejamiento
rect/color desincronizado, y una de ellas sin medir nada.

## Las herramientas de G8 median cosas que no eran

El balance de campana sale de `tools/simular_g8.py` y `tools/economia_g8.py`.
Al pasarles parametros imposibles, ninguno se quejo: todos devolvieron un
informe con aspecto de evidencia.

| Entrada | Que hacia antes |
|---|---|
| `--nodos papel` | Media `senda` y rotulaba la columna **"papel"**: 62.5%-81.2% con etiqueta inventada |
| `--rival 0` | `0` es falsy, asi que caia al valor por defecto y media 5 cartas |
| `--refuerzo -5` | Se ignoraba en silencio |
| `--duelos 0` | "victorias del jugador: **0.0%**", promediado sobre cero partidas |
| `--cartas 3` / `--cartas 99` | Mazos que el juego no puede jugar (el mazo va de 5 a 10) |
| `TT_SEMILLAS=0` | `ZeroDivisionError` dentro del informe |

Un numero asi es peor que no dar numero, porque **parece una medida**. Ahora
todo eso sale con codigo 2 y un mensaje que dice que nodos y rangos son validos,
y `tests/test_herramientas_medida.py` lo comprueba. Ademas hay un test de que
un nodo valido **sigue** midiendose: una validacion que cierra la puerta a la
medicion legitima tambien seria un fallo.

Comprobado retirando cada validacion una a una: las 6 spots fallan.

Se retira la comparacion numerica antes escrita aqui: citaba `--nodos senda`
pero atribuía sus resultados al trono, sin un comando reproducible completo.
La validacion de argumentos la cubre `tests/test_herramientas_medida.py`;
las medidas de balance y sus supuestos se documentan en `informe_g8.md`.

## El informe de este mismo documento estaba corrupto

Leyendo el informe para otra cosa aparecio una frase de relleno pegada **70
veces**, partiendo frases y palabras:

```
"| cero bloque es lo que valeos o perdidas ..."    -> "bloqueos"
"que es lo que valeda pendiente"                   -> "queda pendiente"
"asi que es lo que vale **no se da porvalidada**" -> "por validada"
"cuando hay que no lo haria"                      -> "cuando no deberia"
```

Setenta frases rotas en el documento que es la evidencia de cierre de G9, y
nadie lo habia leido porque el fichero existia y tenia el tamano esperado.
**Estar no es estar bien.**

Reparado con `tools/reparar_informe_g9.py`, por sustituciones explicitas y no
por regexp: la frase se habia pegado dentro de palabras, y una limpieza de
espacios a pelo se comia la sangria de las listas de Markdown (3 espacios
convertidos en 2) y dos espacios al final, que son saltos de linea. Las dos
cosas se notaron comparando linea a linea el antes y el despues, y se
arreglaron; tambien se miro si las comillas del enunciado seguian intactas
("sin recorte** ... con texto ampliado"), porque una regla de limpieza se las
habia comido en la primera pasada.

`tests/test_documentacion.py` vigila las formas **rotas** (no las reparadas):
frases pegadas, palabras partidas, sangria de lista, salto de linea a mitad de
frase, ASCII y secciones obligatorias del informe. Ejecutado sobre el fichero
tal como estaba, falla; sobre el reparado, pasa.

## Una promesa mecanica que no hacia nada (G6)

Auditando las ocho opciones de encuentro contra su codigo, una no cumplia lo
que decia:

```
Mercader Errante - "Pagar con una carta (+1 a un lado de la que elijas)"
                  -> el juego contestaba "recibiste un punto mas de fuerza"
                  -> el mazo NO cambia. Medido: delta 0.
```

Las dos mitades de la promesa eran falsas: no se cobraba ninguna carta y no se
subia ninguna. G6 pide que "cada promesa mecanica del texto tiene efecto
verificable o se reescribe como narrativa".

Reparado en las dos direcciones a la vez:

- El texto ya no promete un pago que no ocurre: dice **"Aceptar su consejo
  (+1 a la carta que elijas)"**.
- El efecto `mejorar` ahora **mejora de verdad**, y la pantalla **pregunta**
  cual, encadenando el selector de carta que ya existia para la recompensa de
  entrenamiento. Sin `idx` (llamadas sin eleccion, como los tests) cae a la
  carta mas debil, que es un valor por defecto sensato.

De paso: la otra opcion decia "ganas una carta **del pool**", y "pool" es
justo la jerga que G5 pidio quitar. La revision final precisa "de tu faccion
o de tus aliados", que es el catalogo usado por `cartas_del_pool`.

### Los tests, y uno que no hacia falta

`tests/test_promesas_encuentros.py` mide el mazo antes y despues de **cada**
opcion y comprueba que el texto y el efecto coinciden. Y
`tests/test_encuentro_efecto.py` recorre la pantalla de verdad, mueve el foco
con las flechas y confirma con ENTER, para comprobar que la pantalla pregunta.

Ese segundo test existe por un motivo concreto: cuando solo existe el primero,
**quitar el selector de la pantalla no lo detecta nada**, porque
`aplicar_encuentro(estado, "mejorar")` sin indice funciona (usa la mas debil) y
el texto seguiria diciendo "la que elijas". Es el hueco de siempre entre "la
logica funciona" y "la pantalla hace lo que promete".

Montarlo llevo tres intentos y los tres fallaron de forma instructiva:

1. `auditoria_visual.correr_pantalla` **sustituye `pygame.event.get`** por el
   suyo y se come los eventos del test: el clic nunca llegaba y el test pasaba
   sin comprobar nada. Conduzco el bucle a mano.
2. Un `pygame.QUIT` sintetico hace que `Cinematica.ejecutar` lance
   `SystemExit`: el test midia un cierre, no una pulsacion.
3. Hay **dos layouts** de opciones (retrato a la izquierda, fila horizontal)
   segun haya retrato del encuentro. Mis coordenadas de la fila pulsaban la
   opcion 0 al querer la 1, y el test "pasaba" probando otra cosa. Ahora se
   navega con el teclado, que ademas es lo que G7 pide que funcione.

Comprobado: devuelto el efecto a no hacer nada, fallan dos tests; quitado el
selector de la pantalla, falla el que recorre la pantalla.

## Estabilidad de la suite

Una suite que a veces esta verde no es una suite. La de este proyecto se ha
ejecutado **mas de 20 veces completas** en busca de instabilidad:

- El test de `debilitar` fallaba en ~1 de cada 4 suite completas. Ya esta
  arreglado (semilla fija) y se verifico con 12 vueltas del modulo mas 3 de la
  suite entera.
- Los 25 tests candidatos a fragility se ejecutaron 15 veces seguidas: 0 fallos.

Conteo historico de esta comprobacion: **933 pruebas**. El conteo de la
revision final figura en `cierre_candidata.md`.

## Capturas actuales (hechas)

`tools/capturas_g9.py` compone las pantallas de verdad, con el codigo de ahora,
y cubre los estados que el cierre pide revisar: normal, **foco de teclado**,
**texto ampliado** y **error real**. No se toca ningun asset.

Salen 13 PNG en `capturas/`, incluyendo `g9_07..09` con el foco visible (borde
cian **y galon**, indicador por forma y no solo por color) y `g9_10..12` con el
modo lectura al 125%.

### Defecto que SOLO se vio mirando la captura

En modo lectura, el diario dejaba lineas **salidas del panel por la derecha**.
El ancho de envoltura estaba fijado para el tamano base de fuente, asi que al
agrandar la tipografia el texto se salia. Ningun test lo habria detectado: la
pantalla no revienta, dibuja texto, y solo el ancho del panel delata el fallo.

Corregido en `pantallas.diario_dialogos` (el ancho de envoltura se divide por la
escala real) y atado en `tests/test_accesibilidad.py::TestModoLecturaNoDesborda`.

## Propiedad de las cartas: comprobada por forma, y un test que mentia

G2 pide "propio/rival distinguibles sin depender del color". Las marcas son
cuadrado (propia), rombo (rival) y circulo (libre). Para comprobarlo de verdad
hice `tools/verificar_propiedad.py`, que mide la silueta de la marca y la
compara. Captura: `capturas/g9_14_propiedad_cartas.png`.

**El primer test no comprobaba nada.** Convirtiendo las tres marcas en circulos
-que es exactamente "la propiedad vuelve a depender solo del color"- el test
seguia pasando. La causa: la carta entera se tine por dueno (azul, roja,
dorada), asi que las tres siluetas difieren por el FONDO y nunca por la forma.

El arreglo fue medir lo que no depende del color por construccion: cada marca
se pinta sobre una base oscura fija `(8, 8, 12)` que lleva la forma, y esa base
es identica en las tres propiedades. Midiendo la base y restando el arco del
borde (comun a las tres), la comparacion es de forma pura.

Comprobado: con las tres marcas en circulo, la herramienta responde
`FALLO: estas marcas son IDENTICAS en gris: [('PROPIA', 'RIVAL')]` y
`tests/test_propiedad_forma.py` falla. Sin la regresion, pasa.

Se deja constancia porque un test verde que no detecta la regresion que dice
detectar es peor que no tener test: entrena a confiar en el.

## Auditoria de tests fragiles

El test inestable de `debilitar` no era un caso aislado: es el patron "comprobar
una cifra sobre datos que el juego sortea". Escribi `tools/buscar_tests_fragiles.py`
para encontrar el resto.

Marca los tests que consumen azar (`nueva_campana`, `abrir_sobre`,
`draft_aleatorio`, `mazo_rival`...) **y** comprueban una magnitud numerica.
Salen **27**, de los que 25 no fijan la semilla.

**Comprobado empiricamente que no fallan:** esos 25 se ejecutaron 15 veces
seguidas y no hubo ni un fallo. La mayoria son falsos positivos del detector:
`test_valores_nunca_pasan_de_diez` comprueba un tope duro que se cumple con
cualquier mazo, y `test_sobre_da_tres_distintas_del_pool` es una propiedad del
sorteo, no una cifra de suerte.

El detector queda como filtro, no como veredicto. Y el propio detector tuvo dos
fallos al escribirse, que es lo de un script casero:

- Buscaba solo operadores `>` en expresiones y se escapaba de todas las
  aserciones `assertGreater(a, b)`: daba cero hallazgos con la suite llena de
  candidatos.
- Miraba solo llamadas `nombre()` y no `modulo.nombre()`, que es como se llama
  practicamente todo el juego (`campana.mazo_rival`). Volvia a dar cero.

Un detector que dice "no hay nada" cuando no deberia: hay que
comprobarlo contra un caso que se sepa positivo.

## Integridad de la version web

`asyncificar.py` convierte en `async` las pantallas con bucle de render porque
pygbag exige `await asyncio.sleep(0`: sin eso la pagina se congela. Su lista
`PANTALLAS_ASYNC` es una lista **nombrada**, y anadir una pantalla nueva no la
actualiza: nadie avisa de la que se cuela.

`tests/test_web_async.py` no se fia de esa lista. Comprueba la propiedad
directamente sobre el codigo: una funcion sincrona que ademas tenga un bucle y
dibuje frames congela la version web. Verificado metiendo una pantalla sync
falsa: el test falla y la nombra.

Matiz que salio al escribirlo: `Cinematica.ejecutar_un_frame` pinta un frame y
es sync **a proposito** (demos y tests, sin eventos). La comprobacion pide bucle,
no solo pintar, precisamente para no marcar ese helper legitimo como error.

## Un test inestable, encontrado por casualidad

Una ejecucion de la suite fallo cuando las anteriores pasaban. Era
`test_debilitar_se_sigue_notando_en_el_tercer_encuentro`, **escrito por mi**.

La causa: `campana.mazo_rival` sortea con `estado["semilla"]`, y
`nueva_campana` la genera al azar. El test afirmaba una cifra (>30 de diferencia
de fuerza) sobre un mazo **aleatorio**: depender de la suerte es la definicion
de un test inestable. Fallaba en ~1 de cada 4 suite completas, y al aislarlo
pasaba siempre, que es justo el sintoma.

Arreglado fijando la semilla antes de crear la campana. Comprobado con 12
vueltas seguidas del modulo y 3 de la suite entera: cero fallos.

Se deja constancia porque una suite que falla de vez en cuando entrena a
reintentar en lugar de a mirar.

## Escalado de pantalla (G7)

El juego esta disenado a 1280x800 y **todo** el dibujo usa esas constantes.
Adaptarlo a un monitor de otra resolucion es lo que pedia G7 ("presentacion
1280x800 a pantallas objetivo con escalado y coordenadas de entrada coherentes"),
y no estaba hecho: `set_mode((1280,800), flags)` sin mas.

Ahora la ventana se pide con `pygame.SCALED`: pygame escala al tamano real de la
ventana y **traduce las coordenadas del raton** a la superficie logica, de modo
que ni el dibujo ni la entrada cambian. El redimensionado se reaplica solo
interceptando `VIDEORESIZE` en `pygame.event.get`, igual que `ui` intercepta
`display.flip` para las auditorias (desde un solo sitio: antes lo hacian dos
herramientas por su cuenta y se pisaban).

**Riesgo encontrado y cerrado:** `set_mode` con `SCALED` lanza
`pygame.error: failed to create renderer` donde no hay renderer rapido. Sin un
guardia, eso habria impedido **arrancar el juego** en esos sistemas. Ahora se
prueba una vez, se recuerda el resultado y se cae a una ventana normal. Que no
escale en una maquina rara es molesto; que no arranque es inaceptable.
Cubierto por `tests/test_accesibilidad.py::TestEscaladoDePantalla`.

**Lo que NO se ha verificado:** en este entorno no hay ventana real, asi que no
se ha podido comprobar de forma visual que el escalado se ve bien ni medir la
correspondencia real del raton. Lo verificado es el invariante comprobable: la
superficie logica sigue siendo 1280x800 al abrir, al cambiar a pantalla
completa y tras un `VIDEORESIZE`. **Queda pendiente mirarlo en un equipo
real.**

## Rendimiento en el ejecutable

El ejecutable de `dist/` se recompila con PyInstaller. `--check` comprueba
recursos y `--test` entra directamente en un duelo y sale solo. Son pruebas
de arranque empaquetado; no ejecutan los siete recorridos de campana ni miden
rendimiento en el dispositivo objetivo.

## Lo que NO se ha hecho

- **Version web.** Existe un artefacto antiguo en `build/web/`, con
  `index.html`, `tripletriad.apk` y `tripletriad.tar.gz`. No incorpora la
  revision actual ni esta validado. Queda pendiente confirmar si es entrega;
  en ese caso hay que reconstruirlo y probarlo en navegador.
- **Playtest con cinco personas nuevas.** Requiere participantes externos, que no
  estan disponibles. El objetivo dice que al menos cuatro deben poder completar
  el primer duelo, entender la captura, comprar y equipar una carta y reanudar
  sin asistencia.
  **Se registra como pendiente. No se inventa evidencia ni se sustituye por
  simulacion**: el simulador es maquina contra maquina con una IA de dificultad
  fija, y un humano novel juega peor que esa IA. Las cifras de G8 **no**
  predicen como lo vivira un jugador.
- **Rendimiento real en dispositivo objetivo.** Se puede medir el arranque del
  ejecutable, pero el objetivo avisa de no equiparar un benchmark aislado a la
  experiencia final. Sin ejecutarlo en el equipo de destino, queda pendiente.

## Estado por criterio de cierre

| criterio | estado |
|---|---|
| cero bloqueos o perdidas de progreso en los recorridos automatizados | **7/7 en codigo fuente**; no equivale a playtest |
| capturas actuales de normal/error/foco/texto ampliado | **cumplido**: 13 |
| recorrido en el ejecutable | **parcial**: recursos y arranque de duelo (`--check` y `--test`); campana completa pendiente |
| documentacion de limites de soporte | **cumplido**: `docs/limites_soporte.md` |
| playtest con 5 personas | **pendiente: bloqueado por falta de participantes** |

## Partida danada: hueco encontrado y cerrado

Al probar los limites de soporte aparecio un problema real: un `campana.json`
corrupto hacia que `cargar()` devolviera `None` y el menu ofreciera "NUEVA
CAMPANA" como si fuera la primera partida. **El jugador perdia su campana sin
que nadie le dijera nada.**

Ahora `campana.partida_danada()` distingue "no has jugado nunca" de "tenias
algo y se ha roto", y el juego lo dice al entrar al menu indicando donde esta el
archivo y que se puede renombrar o borrar. El juego sigue arrancando.
Cubierto por `tests/test_partida_danada.py` (7 casos).

## Advertencia sobre este mismo documento

Al escribir `docs/limites_soporte.md` escribi dos afirmaciones **incorrectas**
que solo aparecieron al verificar:

- Decia que empezar de cero "pisa la partida sin preguntar" sin mencionar que
  `_archivar_partida()` deja una copia con fecha. Ese archivo ya existia y yo no
  lo habia conectado con la documentacion.
- Decia que los datos caen junto al ejecutable sin explicar la cadena de
  directorios: `dir_datos()` prueba ejecutable, codigo, directorio de trabajo y
  **solo entonces** `~/TripleTriad`.

Se corrigieron comprobando el codigo y ejecutandolo. Se deja constancia porque
documentacion escrita de memoria es exactamente donde se cuelan las promesas
que el juego no cumple.
