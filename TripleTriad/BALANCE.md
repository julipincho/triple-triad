# Informe de balance de Cartones y Mazmorras

Generado por `python tests/duelos_simulador.py`.

<!-- DATOS-INICIO -->

```
Simulador de duelos: 400 trials x 45 cruces x 2 politicas
Cada trial juega el cruce dos veces con el orden invertido, para que
la ventaja de empezar no sesgue la comparacion.

SUELO DE RUIDO
----------------------------------------------------------------------------
medida                                                    aleatorio  voraz
----------------------------------------------------------------------------
ventaja de empezar (mazo vs si mismo, A siempre primero)  68.5%      60.2%

ESTRUCTURA DE MAZOS
----------------------------------------------------------------------------
faccion         habilidades                            media por lado     
----------------------------------------------------------------------------
humano          embestida:3, furia:3, muro:3, quema:1  N6.7 S6.3 E6.4 O6.4
orco            embestida:2, furia:6, muro:1, quema:3  N6.9 S6.8 E6.5 O6.2
elfo            embestida:2, furia:2, muro:1, quema:1  N6.5 S6.7 E6.4 O6.5
goblin          embestida:2, furia:2, muro:1, quema:2  N6.7 S6.2 E6.1 O6.3
hombre_lobo     embestida:1, furia:2, muro:1, quema:1  N6.6 S6.5 E6.5 O6.1
vampiro         embestida:1, furia:1, muro:1, quema:1  N6.4 S6.8 E6.6 O6.4
dragon          embestida:3, furia:2, muro:1, quema:2  N6.9 S6.6 E6.7 O6.2
elfo_nocturno   embestida:1, furia:3, muro:2, quema:2  N6.6 S6.4 E6.5 O6.4
hombre_pantera  embestida:3, furia:3, muro:1, quema:2  N7.0 S6.2 E6.5 O6.4
hombre_lagarto  embestida:1, furia:1, muro:2, quema:2  N6.7 S6.6 E6.3 O6.5

Ningun problema de estructura: todas las facciones tienen
habilidades y sus lados estan repartidos.

SUELO DE RUIDO POR POLITICA (una faccion contra si misma)
  aleatorio  min 46.2%  max 50.4%  media 48.3%
  voraz      min 47.1%  max 51.5%  media 49.6%

ALEATORIO -ordenado de mas a menos favorable a A-
------------------------------------------------------------
cruce                             % A    % B    error   
------------------------------------------------------------
orco vs vampiro                   57.9%  42.1%  +/-3.4  
hombre_lobo vs hombre_lagarto     57.1%  42.9%  +/-3.4  
hombre_lobo vs vampiro            57.0%  43.0%  +/-3.4  
orco vs elfo_nocturno             56.1%  43.9%  +/-3.4  
orco vs hombre_lagarto            56.0%  44.0%  +/-3.4  
hombre_lobo vs dragon             55.4%  44.6%  +/-3.4  
orco vs dragon                    55.0%  45.0%  +/-3.4  
goblin vs vampiro                 54.8%  45.2%  +/-3.4  
humano vs elfo                    54.1%  45.9%  +/-3.5  
orco vs hombre_pantera            54.1%  45.9%  +/-3.5  
hombre_lobo vs hombre_pantera     54.0%  46.0%  +/-3.5  
goblin vs hombre_lagarto          53.8%  46.2%  +/-3.5  
orco vs elfo                      53.6%  46.4%  +/-3.5  
humano vs vampiro                 53.5%  46.5%  +/-3.5  
hombre_pantera vs hombre_lagarto  53.5%  46.5%  +/-3.5  
hombre_lobo vs elfo_nocturno      53.2%  46.8%  +/-3.5  
elfo vs vampiro                   53.1%  46.9%  +/-3.5  
orco vs goblin                    52.6%  47.4%  +/-3.5  
dragon vs hombre_lagarto          51.8%  48.2%  +/-3.5  
goblin vs elfo_nocturno           51.5%  48.5%  +/-3.5  
goblin vs hombre_pantera          51.5%  48.5%  +/-3.5  
humano vs dragon                  50.9%  49.1%  +/-3.5  
dragon vs elfo_nocturno           50.8%  49.2%  +/-3.5  
humano vs goblin                  50.6%  49.4%  +/-3.5  
vampiro vs hombre_lagarto         50.1%  49.9%  +/-3.5  
elfo_nocturno vs hombre_pantera   49.8%  50.2%  +/-3.5  
humano vs hombre_lagarto          49.6%  50.4%  +/-3.5  
elfo vs dragon                    49.5%  50.5%  +/-3.5  
elfo_nocturno vs hombre_lagarto   49.5%  50.5%  +/-3.5  
orco vs hombre_lobo               49.4%  50.6%  +/-3.5  
humano vs hombre_pantera          49.2%  50.8%  +/-3.5  
goblin vs dragon                  49.2%  50.8%  +/-3.5  
elfo vs goblin                    49.1%  50.9%  +/-3.5  
elfo vs hombre_lagarto            48.8%  51.2%  +/-3.5  
dragon vs hombre_pantera          48.6%  51.4%  +/-3.5  
humano vs elfo_nocturno           48.5%  51.5%  +/-3.5  
elfo vs elfo_nocturno             48.4%  51.6%  +/-3.5  
elfo vs hombre_pantera            48.0%  52.0%  +/-3.5  
vampiro vs hombre_pantera         47.2%  52.8%  +/-3.5  
humano vs hombre_lobo             46.4%  53.6%  +/-3.5  
vampiro vs dragon                 46.0%  54.0%  +/-3.5  
elfo vs hombre_lobo               44.5%  55.5%  +/-3.4  
humano vs orco                    44.4%  55.6%  +/-3.4  
goblin vs hombre_lobo             44.1%  55.9%  +/-3.4  
vampiro vs elfo_nocturno          43.1%  56.9%  +/-3.4  

VORAZ -ordenado de mas a menos favorable a A-
-------------------------------------------------------------------
cruce                             % A    % B    error          
-------------------------------------------------------------------
hombre_lobo vs vampiro            67.1%  32.9%  +/-3.3  INJUSTO
humano vs vampiro                 65.4%  34.6%  +/-3.3  INJUSTO
orco vs elfo                      63.6%  36.4%  +/-3.3         
orco vs dragon                    61.6%  38.4%  +/-3.4         
orco vs hombre_lagarto            61.6%  38.4%  +/-3.4         
orco vs vampiro                   61.4%  38.6%  +/-3.4         
goblin vs vampiro                 60.8%  39.2%  +/-3.4         
humano vs dragon                  60.4%  39.6%  +/-3.4         
orco vs hombre_pantera            57.6%  42.4%  +/-3.4         
hombre_pantera vs hombre_lagarto  57.5%  42.5%  +/-3.4         
humano vs elfo                    56.8%  43.2%  +/-3.4         
orco vs goblin                    56.5%  43.5%  +/-3.4         
elfo vs vampiro                   56.5%  43.5%  +/-3.4         
orco vs elfo_nocturno             55.1%  44.9%  +/-3.4         
humano vs goblin                  54.9%  45.1%  +/-3.4         
goblin vs hombre_lagarto          53.8%  46.2%  +/-3.5         
humano vs hombre_lagarto          53.6%  46.4%  +/-3.5         
hombre_lobo vs dragon             53.1%  46.9%  +/-3.5         
hombre_lobo vs elfo_nocturno      53.1%  46.9%  +/-3.5         
hombre_lobo vs hombre_lagarto     53.0%  47.0%  +/-3.5         
humano vs elfo_nocturno           52.4%  47.6%  +/-3.5         
humano vs orco                    50.9%  49.1%  +/-3.5         
orco vs hombre_lobo               50.9%  49.1%  +/-3.5         
goblin vs dragon                  50.0%  50.0%  +/-3.5         
humano vs hombre_pantera          49.8%  50.2%  +/-3.5         
elfo vs dragon                    49.8%  50.2%  +/-3.5         
elfo_nocturno vs hombre_lagarto   49.4%  50.6%  +/-3.5         
elfo vs goblin                    49.2%  50.8%  +/-3.5         
elfo vs hombre_lagarto            49.0%  51.0%  +/-3.5         
dragon vs hombre_lagarto          48.8%  51.2%  +/-3.5         
goblin vs elfo_nocturno           47.6%  52.4%  +/-3.5         
elfo_nocturno vs hombre_pantera   47.4%  52.6%  +/-3.5         
vampiro vs hombre_lagarto         46.8%  53.2%  +/-3.5         
hombre_lobo vs hombre_pantera     46.5%  53.5%  +/-3.5         
dragon vs elfo_nocturno           46.2%  53.8%  +/-3.5         
elfo vs hombre_pantera            45.8%  54.2%  +/-3.5         
goblin vs hombre_lobo             45.6%  54.4%  +/-3.5         
goblin vs hombre_pantera          44.5%  55.5%  +/-3.4         
humano vs hombre_lobo             42.4%  57.6%  +/-3.4         
vampiro vs dragon                 42.2%  57.8%  +/-3.4         
elfo vs elfo_nocturno             41.6%  58.4%  +/-3.4         
vampiro vs elfo_nocturno          41.5%  58.5%  +/-3.4         
dragon vs hombre_pantera          40.8%  59.2%  +/-3.4         
elfo vs hombre_lobo               40.0%  60.0%  +/-3.4         
vampiro vs hombre_pantera         38.6%  61.4%  +/-3.4         

MEDIA POR FACCION (victorias sobre las otras nueve)
----------------------------------
faccion         aleatorio  voraz
----------------------------------
orco            54.5%      57.5%
hombre_lobo     54.7%      54.9%
hombre_pantera  50.1%      54.1%
humano          49.7%      54.0%
elfo_nocturno   49.7%      51.0%
goblin          50.3%      49.1%
hombre_lagarto  47.8%      47.4%
dragon          49.5%      46.5%
elfo            48.2%      45.7%
vampiro         45.6%      39.8%

CRUCES INJUSTOS (fuera de 35.0-65.0% y por encima del ruido):
  voraz      humano vs vampiro: 65.4% a favor de humano (+/- 3.3)
  voraz      hombre_lobo vs vampiro: 67.1% a favor de hombre_lobo (+/- 3.3)
```

<!-- DATOS-FIN -->

## Conclusiones

1. **Con juego aleatorio los diez bandos estan equilibrados.** Los 45 cruces
   caen entre 43% y 58%, todos dentro del rango sano. Ningun duelo es
   "imposiblemente injusto" contra un rival que no juega bien.

2. **Con juego voraz hay un bando claramente mas debil: el vampiro.** Es el
   unico por debajo del 45% de media, y pierde con claridad contra humano y
   hombre_lobo. Los otros nueve estan entre 45% y 58%, que es un reparto sano.

   No es un problema de "duelos imposibles": es que un bando concreta tiene
   peor techo de mazo. Se arregla subiendo las cartas del vampiro, no bajando
   las de los demas.

3. **La ventaja de empezar es estructural (~68% con juego aleatorio).** Con 5
   cartas por bando en 9 casillas, quien empieza coloca 5 cartas y el rival 4.
   Es una propiedad del reparto de turnos, no un fallo del motor. Si se
   quisiera corregir, la via natural seria que quien empieza juegue con 4
   cartas y el rival con 5, o penalizar el primer turno.

4. **La estructura de mazos esta sana.** Las diez facciones tienen
   habilidades y sus lados estan repartidos.

5. **No se ha tocado ninguna carta.** Este es un informe para revisar. El
   reequilibrio es una ronda aparte y es decision del jugador.

## Metodologia (para poder discutir los numeros)

- Cada trial juega el cruce DOS VECES con el orden de turno invertido y
  promedia las dos partidas, para que la ventaja de empezar no sesgue.
- Los empates no cuentan como victoria de nadie.
- El margen de error es binomial al 95%: ~3,5 puntos con 400 trials.
- Un cruce se marca "injusto" solo si se sale de 35-65% Y su intervalo de
  confianza no toca el 50%. Sin esa segunda condicion casi todos los cruces
  saldrian "injustos" sin serlo: seria alarma falsa.
- El suelo de ruido se mide con una faccion contra si misma con la misma
  metodologia: sale 46-51%.
- **Por que 400 trials y no 60**: con 60 el margen es ~8 puntos y salen cinco
  cruces "injustos" que aqui son ruido. El simulador no pisa este fichero por
  debajo de `MIN_TRIALS_PUBLIQUABLE` trials: escribe aparte con
  "MUESTRECHA" en el nombre y avisa.

## Nota sobre el rendimiento de los fondos

El fondo se escala con factor ENTERO (vecino mas cercano). Medido: escalar a
1536x768 y recortar cuesta ~3,0 ms frente a ~2,0 ms de un `smoothscale` a
1280x800. Es decir, el metodo entero es algo MAS LENTO por llamada. No
importa porque ocurre UNA vez por fondo y se cachea (`fondo_pantalla`), no por
frame. Lo que se gana es nitidez: cada pixel original es un bloque 3x3 con
borde duro, sin difuminado ni pixeles inventados.

Un error real que se corrigio por el camino: `_mejor_factor` sumaba las barras
de fondo por producto, asi que con un fondo cuadrado (256x256) ganaba el
factor 4 dejando 256px de negro a los lados, en vez del factor 5 que cubre la
pantalla entera. Ahora la barra pesa triple frente al recorte (la barra se ve,
el recorte no).
