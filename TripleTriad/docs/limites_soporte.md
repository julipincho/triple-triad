# Limites de soporte

Que se puede prometer de **Cartones y Mazmorras** y que no. Escrito a partir de
pruebas hechas, no de supuestos: cada punto de "si" esta comprobado con el
codigo actual y los tests de la suite.

## Donde se guarda

El progreso vive en una carpeta de datos. Se puede forzar con la variable de
entorno `TRIPLETRIAD_DATA` (la usan los tests para no tocar la partida real).

Si no se fuerza, `dir_datos()` busca **el primer directorio escribible** de
esta lista, en orden:

1. la carpeta del ejecutable (cuando va empaquetado, `congelado()` es cierto)
2. la carpeta del propio codigo
3. el directorio de trabajo desde el que se lanzo
4. `~/TripleTriad` en el perfil del usuario

Es decir: **normalmente cae junto al `.exe`**, no en una carpeta de aplicacion
del sistema. Solo si esa carpeta no admite escritura baja a la carpeta personal
del jugador.

Archivos:

| archivo | que guarda |
|---|---|
| `campana.json` | la partida en curso: nodo, mazo, decisiones, ruta |
| `perfil.json` | coleccion, moneda, finales, fragmentos, revelaciones |
| `opciones.json` | preferencias: volumen, pantalla, texto grande, ritmo |

Borrar `campana.json` **no** borra la coleccion ni la moneda: son cosas
distintas a proposito. Empezar una campana nueva pisa la partida, pero el
progreso del perfil se conserva.

## Garantias comprobadas

**El guardado es atomico.** Se escribe a un temporal y se renombra con
`os.replace`: nunca queda un `campana.json` a medio escribir. Ademas agrupa
perfil y campana en un commit con un diario, de modo que un corte de luz a mitad
no deja una cosa guardada y la otra no; al reabrir se completa el commit.

**Un guardado ilegible no rompe el juego, y avisa.** Antes de G9 un
`campana.json` corrupto hacia que el menu pareciese el de una primera partida y
el jugador perdia su campana en silencio. Ahora `campana.partida_danada()`
distingue "no has jugado nunca" de "tenias algo y se ha roto", y el juego lo
dice al entrar al menu, indicando donde esta el archivo y que se puede
renombrar o borrar.

**Los fallos son visibles.** El juego ya no se cierra en silencio: cualquier
excepcion va a una pantalla que explica que paso y donde esta la traza
(`crash.log`), distinguiendo "no se pudo guardar" de "algo ha fallado".

**Reanudar es seguro.** Victoria, recompensa y final son reanudables: si se
cierra a mitad, se vuelve exactamente al mismo punto sin cobrar dos veces ni
entregar dos veces.

**Abandonar no es ganar.** Salir de un duel no avanza el nodo, no cuenta
derrota y no da la moneda de duelo completado.

## Limites que hay que conocer

- **Perder un `campana.json` ilegible es perder esa campana.** El aviso lo dice
  y da la ruta, pero no hay copia de seguridad automatica: el juego no repara ni
  reconstruye una partida corrupta. Copiar la carpeta de datos de vez en cuando
  es la unica red. El archivado automatico solo ocurre al empezar de cero, no
  ante un archivo ya danado.
- **La partida y el perfil son independientes.** Si se borra solo el perfil, se
  pierde la coleccion pero la partida sigue. Si se borra solo la campana, se
  empieza de cero con la coleccion intacta.
- **Empezar de cero no pierde el archivo anterior.** Antes de sobrescribir,
  `_archivar_partida()` copia `campana.json` y `perfil.json` a una carpeta
  `_partida_archivada_<fecha>` junto a los datos del juego. No hay confirmacion
  (es una decision consciente para no poner un dialogo delante de cada
  reinicio), pero el archivo anterior **no desaparece**: esta ahi para
  recuperarlo a mano si hizo falta.
- **No hay multijugador.** Todo es en local, un jugador contra la maquina.
- **No hay version web validada.** Existe un artefacto antiguo en `build/web/`,
  anterior a los cambios actuales. Falta decidir si la web es entrega y, en
  ese caso, reconstruir y validar en navegador.
- **El balance medido es maquina contra maquina.** Las cifras de
  `docs/informe_g8.md` salen de una IA de dificultad fija. Un humano novel juega
  peor que esa IA, asi que **esas cifras no predicen la experiencia**. Calibrar
  de verdad requiere el playtest con personas, que sigue pendiente.
- **El contraste medido cubre las pantallas auditadas.** El auditor
  `tools/auditar_contraste.py` mide 11 pantallas; no todas las del juego.

## Pantalla y resolutions

El juego esta disenado a 1280x800 y se dibuja siempre a ese tamano logico. La
ventana se puede redimensionar libremente y el contenido se escala; el raton se
traduce al tamano logico, asi que los clics caen donde se ven.

- **La ventana se puede redimensionar arrastrando el borde.** El juego se
  adapta solo.
- **Pantalla completa** se cambia desde Ajustes o con el atajo de teclado, y se
  recuerda al reabrir el juego.
- **Si el sistema no puede escalar** (drivers antiguos, entornos sin ventana),
  el juego NO se queda sin arrancar: cae a una ventana normal de 1280x800 y
  avisa con el aviso de pygame. Es una molestia, no una rotura.

**Sin verificar en un equipo real:** el comportamiento visual del escalado y la
correspondencia real del raton solo se han comprobado en un entorno sin
ventana. Lo que si esta comprobado con tests es que el lienzo logico nunca
cambia de tamano (ni al abrir, ni al cambiar a pantalla completa, ni al
redimensionar), que es la condicion de que nada se salga de sitio.

## Diagnostico

El ejecutable lleva un modo de autocomprobacion:

```
TripleTriad.exe --check
```

Verifica que estan todas las cartas, fondos y sonidos empaquetados y dice que
falta si falta. Es el primer paso cuando algo no suena o no se ve.

Para errores, `crash.log` esta junto a los datos del juego y registra cada
excepcion con su traza y el contexto (pantalla en la que estaba).

## Estado del playtest

**Pendiente: no se ha hecho.** El objetivo pide cinco personas nuevas y que al
menos cuatro completen el primer duelo, entiendan la captura, compren y
equipen una carta y reanudan sin asistencia. No hay participantes disponibles,
y **no se sustituye esa prueba por simulacion**: una partida simulada no es una
persona, y decir lo contrario seria dar por validado algo que no se ha validado.
