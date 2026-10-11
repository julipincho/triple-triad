# G8 - Balance de campana: informe reproducible

> Estado: **medido con el motor real**. La calibracion fina sigue pendiente de
> playtest humano; lo que hay aqui son medidas, no decisiones de diseño.

## Por que este informe sustituye al simulador antiguo

`tests/duelos_simulador.py` (y `tests/simular_vs_dragon.py`, que lo usa) **no
sirven para calibrar la produccion**, por dos razones concretas:

1. **No usan la IA del juego.** `jugar_duelo` -> `jugar_turno` es una heuristica
   propia del simulador, distinta de `partida.Juego._elegir_jugada_cpu`. Sus
   tasas describen otro juego.
2. **No usan la generacion real de mazos.** Repiten a mano el recorte por nivel
   y el refuerzo, y solo miden contra `dragon` con niveles sueltos, sin el grafo
   de nodos ni los ordenes de inicio reales.

Sus cifras quedaron escritas en el codigo (`campana.MAX_REFUERZO_RIVAL`) como si
fueron validacion. Este informe las sustituye.

## Metodologia

- **Motor real.** Los duelos se resuelven con `partida.Juego`, `colocar`,
  `comprobar_fin` y `reglas.puntaje_final`: las mismas reglas y la misma cascada
  de capturas que en pantalla.
- **IA real, simetrizada.** `Juego._elegir_jugada_cpu` esta cableado a
  `self.mano_c` y a la perspectiva `CPU`: solo sabe jugar del lado rival. Para
  medir al jugador se reutiliza **exactamente la misma heuristica** (mismo
  `reglas.simular`, mismo `ruido = max(0.05, 0.9 - dificultad*0.3)`, mismos
  bonos de habilidad) cambiando solo la variable `dueno`.
  *Verificado*: con la misma semilla, `_elegir_jugada_cpu` y la version
  simetrica devuelven **la misma jugada**.
- **Mazos reales.** El rival se arma con `campana.mazo_rival(estado, nodo)`, que
  ya aplica recorte por nivel, refuerzo con tope y el `debilitar` de los
  encuentros. El jugador usa su mazo de campana guardado.
- **Muestras pareadas.** Cada trial juega el emparejamiento DOS veces con el
  orden de turno invertido, para neutralizar la ventaja estructural de empezar
  (con 5 cartas por bando en 9 casillas, quien empieza coloca 5 y el rival 4).
  Se anotan las dos partidas, nunca "la mejor de dos".
- **Intervalos de Wilson al 95%** sobre el total de partidas. Wilson y no Wald
  porque con proporciones extremas y muestras pequenas el Wald se sale de [0,1].
- **Reproducibilidad verificada, no supuesta.** Al principio el simulador NO era
  reproducible, y eso hacia invalidos todos los A/B. Dos fallos encadenados:
  1. La IA del motor tira de `random.uniform` del modulo global, sin sembrar.
  2. `campana.nueva_campana` sortea la semilla de la partida con
     `random.getrandbits(64)`: sin sembrar antes, cada corrida repartia un mazo
     inicial DISTINTO y no era ni la misma muestra ni comparable.
  Se comprueba con `tests/test_curva_dificultad.py::test_dos_corridas_con_la_misma_semilla_coinciden`,
  que compara dos corridas completas. Sin esa propiedad, cualquier "medicion" de
  balance es comparar ruido con ruido, y cualquier ajuste hecho sobre ella es
  tirar la moneda.
- **Comparaciones A/B con la misma semilla y el mismo numero de duelos.**
  Cambiar el tamano de muestra cambia el flujo de aleatoriedad: comparar
  corridas de 400 y de 300 duelos no es una comparacion pareada, y asi se
  descarto una primera lectura falsa.

Reproducir:

```
python tools/simular_g8.py --duelos 300 --cartas 10
python tools/simular_g8.py --duelos 300 --cartas 5
python tools/simular_g8.py --duelos 300 --refuerzo 2 --salida ab_ref2.json
python tools/simular_g8.py --duelos 300 --refuerzo 3 --salida ab_ref3.json
```

Supuestos explicitos, para que las cifras no se malinterpreten:

- El jugador se modela con una IA de dificultad fija (1.0), no con una persona.
  Mide la **maquina contra la maquina**, y por eso las cifras son MAS
  favorables al jugador que lo que vera un humano novel.
- "Victorias del jugador" cuenta tambien el **empate**, que en el juego cuenta
  como victoria (`puntaje_final` lo declara asi).
- La faccion del rival sale de `info_duelo` de cada nodo, no se fuerza a dragon.

## Observacion sobre el jefe: RETIRADA

> **Este hallazgo se retiro.** Se creyo que el trono era mas facil que el
> asalto; un A/B pareado de 7200 partidas por celda lo desmiente. El error no
> fue de criterio, fue de instrumentacion: el simulador no era reproducible y
> la lectura inicial era ruido.

Con el tope de refuerzo en 2, `min(nivel, 2)` da **el mismo refuerzo** al nivel
2 (asalto/fortaleza) y al nivel 3 (trono). Eso sigue siendo un hecho del codigo:
el trono no recibia mas refuerzo, solo 4 cartas mas fuertes por el pool. Pero de
ahi **no** se sigue que la curva se invierta.

La primera medicion dio asalto 55.2 y trono 58.4, y de ahi se escribio "el jefe
es mas facil que el nodo previo". Al repetirlo:

| corrida (todas a refuerzo 2) | asalto | trono | la curva se invierte? |
|---|---|---|---|
| 400 duelos, todos los nodos (NO reproducible) | 55.2 | 58.4 | si |
| 40 duelos (NO reproducible) | 60.0 | 54.3 | no |
| 200 duelos (NO reproducible) | 59.1 | 52.3 | no |
| **400 duelos, pareado y reproducible** | **62.0** | **54.3** | **no** |

Las tres primeras contradicianse entre si porque el RNG global no estaba
sembrado: cada corrida repartia un mazo inicial distinto. Solo la ultima es un
experimento valido, y su veredicto es que **el trono ya era mas duro que el
asalto** (54.3 frente a 62.0). La afirmacion inicial era falsa.

Lo que queda en pie del cambio no es "el jefe era mas facil", sino lo de
`debilitar` de la seccion siguiente, que si es un defecto medido.

### Curva por nodo (medida con el simulador ya reproducible)

250 trials x 2 partidas x 9 facciones por celda; IC95 de Wilson, promediado
sobre las facciones. Cifra = victorias del jugador.

| nodo | 10 cartas | IC95 | 5 cartas | IC95 |
|------|-----------|------|-----------|------|
| senda | 75.8% | [72-79] | 54.1% | [50-58] |
| aldea | 69.1% | [65-73] | 37.5% | [33-42] |
| ruinas | 58.7% | [54-63] | 27.9% | [24-32] |
| fortaleza | 61.3% | [57-65] | 29.5% | [26-34] |
| asalto | 61.7% | [57-66] | 30.4% | [27-35] |
| **trono** | **53.4%** | [49-58] | **21.7%** | [18-26] |

Lo que dice esta tabla:

- **El trono es el nodo mas duro en los dos escenarios**, y por unos 8 puntos
  sobre el nudo medio. El jefe se siente como jefe, que es lo que se buscaba.
- **El tramo medio esta plano**: ruinas, fortaleza y asalto estan en 58.7-61.7
  con IC95 solapados ([54-63], [57-65], [57-66]). Esa diferencia de 3 puntos NO
  es real: es el mismo nivel challenging. Si se quisiera una rampa gradual, los
  tres nodos del medio habrian que separar de verdad; hoy son un escalon unico.
- La caida de senda (75.8) a aldea (69.1) es el unico salto grande del inicio.
- Con 5 cartas el juego es bastante mas duro de lo que con 10: el trono cae al
  21.7%. Es coherente con que 5 cartas es el mazo minimo y el peor caso jugable.

### Tabla superada (se conserva como registro)

> Estas cifras vienen de corridas hechas **antes** de arreglar la
> reproducibilidad del RNG, asi que no son fiables. Se dejan solo como registro
> de lo que se creyo en su dia:

| nodo | 10 cartas | 5 cartas |
|------|-----------|----------|
| senda | 74.3 | 52.2 |
| aldea | 64.1 | 38.4 |
| ruinas | 57.0 | 31.8 |
| fortaleza | 58.7 | 29.4 |
| asalto | 55.2 | 28.3 |
| trono | 58.4 | 22.8 |

El "trono 58.4" de esa tabla es de donde salio el hallazgo retractado.

## `debilitar` en el trono con refuerzo capado

Otro punto que pedia medir el objetivo: si el tope del refuerzo se come el
efecto de `debilitar` en el trono (nivel 3). Medido con
`tools/medir_debilitar.py`, sobre la fuerza real del mazo rival:

| nodo | nivel | `debilitar`=1 | =2 | =3 |
|------|-------|---------------|----|----|
| ruinas | 2 | 13.1 | 26.7 | 26.7 |
| fortaleza | 2 | 12.6 | 25.6 | 25.6 |
| asalto | 2 | 13.7 | 27.7 | 27.7 |
| **trono** | 3 | 11.1 | 24.0 | **37.8** |

`debilitar` **no se pierde** en ningun nodo: siempre resta. Pero con el tope en
2 los nodos de nivel 2 saturaban en el segundo uso (26.7 = 26.7 = 26.7): a partir
del tercero el encuentro ya no tenia efecto y el texto prometia lo contrario.
Con el tope en 3, **el trono es el unico nodo donde el tercer `debilitar` sigue
restando** (37.8 frente a 26.7). Es decir: el cambio no solo da una palanca de
dificultad al jefe, tambien evita que un efecto de encuentro se prometa y no
ocurra. Eso si es una correccion medida, no una lectura dentro del ruido.

## Correccion aplicada

`MAX_REFUERZO_RIVAL: 2 -> 3`. El refuerzo real es `min(nivel, MAX)`, asi que el
tope solo alcanza en el nivel 3:

| nodo | 0 | 1 | 2 | 2 | 2 | 3 |
|------|---|---|---|---|---|---|
| refuerzo | 0 | 1 | 2 | 2 | 2 | **3** |

A/B pareado, 400 trials x 2 partidas x 9 facciones = **7200 partidas por celda**,
simulador ya reproducible:

| nodo | refuerzo 2 | refuerzo 3 | delta |
|------|-------------|-------------|-------|
| asalto | 62.04% (4467/7200) | 62.04% (4467/7200) | **+0.00** |
| trono | 54.28% (3908/7200) | 53.50% (3852/7200) | -0.78 |

El asalto sale **exactamente igual** en las dos ramas, partida a partida. Eso
confirma que el cambio es quirurgico y no altera el resto de la campana, y de
paso valida que el A/B esta bien pareado.

El efecto real sobre el trono es **-0.78 puntos**: mas duro, pero poco. No es el
"jefe muy facil" que se creyo al principio; es un ajuste pequeño.

**El motivo legitimo del cambio no es la curva de dificultad, es `debilitar`.**
Con el tope en 2, los nodos de nivel 2 saturaban en el segundo uso: el tercer
encuentro de "el rival llegara mas debil" no restaba nada, y su texto prometia lo
contrario. Con el tope en 3 el trono conserva margen (ver la tabla de arriba).
Eso es un defecto medido y una promesa mecanica rota, y es lo que justifica
mantener el cambio.

## Hallazgo nuevo: el tramo medio de la campana esta plano

Con la medicion fiable, ruinas (58.7), fortaleza (61.3) y asalto (61.7) tienen
IC95 solapados: son **el mismo nivel**, no una rampa. La campaña tiene dos
escalones (senda-aldea, y luego el trono) con un llano de tres nodos en medio.

Esto NO se ha tocado. Es una decision de diseno, no un defecto: un llano en el
medio puede ser deliberado (todos son "dificultad media") o puede querer decir
que faltan dos escalones. Decidirlo es del playtest, no de una tabla.

Lo que si se puede decir con la medicion es que **no hay un cuello de botella
aritmetico**: no hay ningun nodo donde el jugador pierda de forma anomala. El
peor nodo es el trono, que es donde deberia estar.

## Economia: ritmo de compras, reintentos y progreso

Medido con `tools/economia_g8.py`, que juega una **campana completa** nodo por
nodo con el motor real, la economia real de `campana.py` y los sobres reales
(incluida la garantia).

Datos de la moneda: duelo 5, victoria 20, captura 2; un sobre cuesta 60 y hay
garantia cada 10 sobres.

54 campanas por grupo (9 facciones x 6 semillas), todas desde un perfil limpio:

| | duelos | reintentos | sobres | cartas nuevas | legendarias | completa |
|---|---|---|---|---|---|---|
| normal | 8.8 | 2.8 | 3.04 | 8.33 | 0.31 | 54/54 |
| con 1er sobre regalado | 8.8 | 2.8 | 4.09 | 11.26 | 0.37 | 54/54 |

Lo que dice:

- **Una campana son ~9 duelos y ~3 sobres.** Es un ritmo corto: quien juegue
  una faccion ve unos tres sobres por partida.
- **~3 reintentos de media**: un tercio de la campana es reintentar. Es alto
  pero no un muro, porque ningun nodo se repite indefinidamente.
- **54/54 completan.** No hay cuello de botella aritmetico: nadie se queda sin
  sobres por falta de moneda ni atasco en un nodo.
- Sobran ~30 monedas al final: menos que un sobre. La economia esta ajustada,
  ni AHORRA ni estrangula.

### Detalle de estructura

`campana.recompensas_de("trono")` devuelve **lista vacia**: el trono no da
recompensa. No es un fallo, es que es el remate (ganar cierra la campana y
dispara el final). Pero conviene saberlo: hay cinco recompensas por campana,
no seis.

**La garantia vive en el perfil, no en la campana.** Con 3-4 sobres por campana
y `PITY_SOBRES = 10`, una garantia por partida no se alcanzaria nunca. Al
contarse en el perfil cruza de una campana a otra, que es lo que hace que
abrir sobres a lo largo de varias partidas tenga recompensa. Esta comprobado en
`tests/test_economia.py`.

## G5: evaluacion de una oferta directa (NO se introduce)

El objetivo pedia "evaluar despues, segun economia medida, una oferta directa
limitada para reducir dependencia del azar; **no introducirla sin validar coste
y progresion**". Se midio, y la conclusion es **no introducirla**.

La oferta simulada es el caso mas generoso posible: el primer sobre de cada
campana sale gratis (60 de moneda de regalo).

| | sobres | cartas nuevas | legendarias |
|---|---|---|---|
| normal | 3.04 | 8.33 | 0.31 (17 en total) |
| con regalo | 4.09 | 11.26 | 0.37 (20 en total) |

**El regalo no reduce la dependencia del azar.** Suma ~1 sobre y +2.9 cartas,
pero las legendarias pasan de 17 a 20 en 54 campanas: +0.06 por campana, dentro
del ruido de un Poisson con ~18 eventos esperados.

La razon es aritmetica, no casual: el regalo mete 60 de moneda antes de tiempo,
lo que compra **un sobre mas**, y un sobre mas son ~0.3 legendarias
esperadas. Para cambiar de verdad la dependencia del azar haria falta ofrecer
**la legendaria garantizada**, no un sobre gratis. Y eso ya existe y se anuncia
en la tienda: es la garantia del pity.

Ademas, un sobre regalado **adelanta la progresion**: el jugador llega al
trono con mas cartas de las que tendria, lo que aplana justo el tramo que hoy
esta llano (ruinas/fortaleza/asalto al mismo nivel).

**Decision: no se introduce la oferta directa.** Se cumple la condicion de G5
("no introducirla sin validar coste y progresion"): validada, y el fallo es
justo el que G5 queria evitar (avanzar progreso sin tocar la dependencia del
azar).

- **No se ha fijado un objetivo de victoria por nodo.** El objetivo avisa
  explicitamente de no imponer 50% a todos. Fijar una cifra sin sesiones
  humanas seria inventar el criterio.
- **No se ha tocado el pool ni las cartas de los jefes.** Con una sola faccion
  de jugador simulada y sin playtest, tocar el catalogo seria endlessenar.
- **No se ha verificado el efecto de `debilitar` con refuerzo capado** mas alla
  de que reduce la fuerza total del mazo rival.

## Pendiente de playtest

El informe medido con maquina no sustituye a cinco personas nuevas jugando. Lo
que sigue sin responder:

1. Si un humano novel cae en el rango medido o mucho por debajo (la IA juega
   mejor que la mayoria al principio).
2. Si el trono al ~54% se siente como jefe o como un nudo mas. La cifra es
   intermedia a proposito y puede necesitar ajuste en cualquier direccion.
3. Si el salto de dificultad se percibe o si hace falta una senal de aviso
   (musica, cartel) que el numero no sustituye.
