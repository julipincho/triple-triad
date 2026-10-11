"""Repara `docs/informe_g9.md`, que tiene la frase 'es lo que vale' pegada 64 veces.

No es un problema de estilo: las frases quedan partidas y hay palabras
cortadas ('bloqueos' partido en dos, 'queda' partido, 'por validada' ->
'porvalidada'). El documento es la evidencia de cierre de G9.

Se hace por sustituciones explicitas, no por regexp ciega, porque la frase se
ha pegado dentro de palabras y hay que reconstruir cada caso.

CUIDADO con los espacios. En Markdown:
  - dos espacios al final de la linea son un salto de linea;
  - la sangria de una linea de lista (2-4 espacios) es parte del formato.
Por eso aqui NO se colapsan espacios a pelo: solo se quita el que estaba
pegado a la frase, y luego se limpian los casos concretos que quedan.
"""

import io
import sys

RUTA = "docs/informe_g9.md"

#: Casos donde la frase esta pegada DENTRO de una palabra o de una expresion.
#: Se arreglan antes de quitar la frase suelta.
PEGADAS = [
    # "que es lo que vale|que es lo que vale" (habia dos seguidas)
    ("que es lo que vale|que es lo que vale un script casero",
     "que es lo de un script casero"),
    # "que es lo que valeda pendiente" -> "queda pendiente"
    ("que es lo que valeda pendiente", "queda pendiente"),
    # "El detector que es lo que valeda como filtro" -> "queda como filtro"
    ("que es lo que valeda como filtro", "queda como filtro"),
    # "bloque es lo que valeos" -> "bloqueos"
    ("bloque es lo que valeos", "bloqueos"),
    # "bloque es lo que valeado" -> "bloqueado"
    ("bloque es lo que valeado", "bloqueado"),
    # "sin repetir nodo ni bloque es lo que valearse"
    ("sin repetir nodo ni bloque es lo que valearse",
     "sin repetir nodo ni bloque"),
    # "asi que es lo que vale **no se da porvalidada**"
    ("porvalidada", "por validada"),
]

FRASE = "es lo que vale"

#: Casos en los que al quitar la frase la frase queda mal conectada y hay que
#: reescribirla a mano. "cuando hay que no lo haria" no es espanol.
REDACCION = [
    ("cuando hay que no lo haria: hay que ", "cuando no deberia: hay que "),
]

#: Lineas donde al partirse la frase queda un espacio al final. En Markdown eso
#: es un salto de linea DENTRO de una frase, que aqui no debe existir: eran
#: prosa envuelta.
SIN_SALTO = [
    ("Un detector que dice \"no hay nada\" cuando no deberia: hay que \n",
     "Un detector que dice \"no hay nada\" cuando no deberia: hay que\n"),
    ("las pantallas con bucle de render porque \n",
     "las pantallas con bucle de render porque\n"),
    ("pero no existe artefacto web que \n", "pero no existe artefacto web que\n"),
    ("\"pisa la partida sin preguntar\" sin mencionar que \n",
     "\"pisa la partida sin preguntar\" sin mencionar que\n"),
    ("Se deja constancia porque \n", "Se deja constancia porque\n"),
]

#: Limpiezas de los huecos que deja la frase al quitarla.
LIMPIEZA = [
    ("por que , y no se da", "porque y no se da"),
    ("comprueba que \n", "comprueba que\n"),
    (" , ", ", "),
    # NO se toca " .": hay comillas del enunciado con puntos suspensivos
    # ("sin recorte** ... con texto ampliado") y quitarselo las altera.
]


def main():
    texto = io.open(RUTA, encoding="utf-8").read()
    for viejo, nuevo in PEGADAS:
        if viejo not in texto:
            print(f"AVISO: no aparece {viejo!r}", file=sys.stderr)
        texto = texto.replace(viejo, nuevo)

    n_frases = texto.count(FRASE)
    # Primero la frase con el espacio que la sigue (asi se lleva el hueco que
    # la propia frase creo), luego la que quede suelta.
    texto = texto.replace(FRASE + " ", "")
    texto = texto.replace(FRASE, "")
    # Estas reglas se aplican DESPUES de quitar la frase, porque describen como
    # queda el texto cuando ya no esta.
    for viejo, nuevo in LIMPIEZA + REDACCION + SIN_SALTO:
        if viejo not in texto:
            print(f"AVISO: no aparece {viejo!r}", file=sys.stderr)
        texto = texto.replace(viejo, nuevo)

    if FRASE in texto:
        print(f"ERROR: quedan {texto.count(FRASE)} ocurrencias", file=sys.stderr)
        return 1
    io.open(RUTA, "w", encoding="utf-8", newline="").write(texto)
    print(f"reparado: {n_frases} frases quitadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
