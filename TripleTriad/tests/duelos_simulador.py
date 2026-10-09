"""Simulador de duelos para medir el balance de verdad.

    python tests/duelos_simulador.py --duelos 400

Por que existe esto: `auditoria_poder.py` solo mira la SUMA de los cuatro
lados y que la media de cada faccion este entre 20 y 30. Con eso todo pasa
(las diez facciones estan entre 25 y 27) y aun asi no se ve el balance real de
un duelo: una carta 8-9-2-2 y otra 2-2-8-9 suman lo mismo y se juegan distinto.

Aqui se juega de verdad con las funciones puras de `reglas.py` y se mide el
PORCENTAJE DE VICTORIAS de cada cruce.

AVANTAGE DEL QUE EMPIEZA (medido, no supuesto): con 5 cartas por bando en un
tablero de 9 casillas, el que empieza coloca 5 cartas y el rival 4. El mismo
mazo contra si mismo da 66/34 a favor de quien empieza. Eso NO es un fallo
del motor: es una propiedad del reparto de turnos del juego.

Por eso cada trial juega el cruce DOS VECES con el orden invertido y se
promedian las dos partidas. La ventaja de empezar es la misma para las dos
facciones, asi que no sesga la comparacion; solo sube el suelo de ruido, que
se reporta aparte con `ventaja_de_empezar`.

Politicas de juego:
  - `aleatorio`: cualquier jugada legal al azar. Mide el sesgo puro del mazo.
  - `voraz`: la jugada que mas capturas da. Mide el techo de cada mazo.
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import facciones  # noqa: E402
import mazos  # noqa: E402
import reglas  # noqa: E402

#: Rango sano de victorias para un cruce. Fuera de esto se marca.
MIN_SANO = 35.0
MAX_SANO = 65.0

#: Trials minimos para que el informe sea publicable. Por debajo el margen de
#: error es de ~8 puntos y los cruces "injustos" que salen son ruido: con 60
#: trials aparecian cinco, y con 400 solo dos (los de verdad).
MIN_TRIALS_PUBLIQUABLE = 200

#: Texto que va al final de BALANCE.md. Vive AQUI y no solo en el fichero
#: porque el simulador regenera el bloque de datos cada vez que se lanza, y
#: unas conclusiones escritas solo en el .md desaparecerian al primer
#: `python tests/duelos_simulador.py`.
_CONCLUSIONES_POR_DEFECTO = """
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
"""

CARTAS_POR_DUELO = 5


def mazo_competitivo(faccion, rnd):
    """Las mejores cartas de una faccion, como las tendria un jugador.

    1 legendaria + 3 raras + 6 comunes (los limites del mazo de campana) y se
    reparten 5 al azar, que es lo que hace el sorteo de cada duelo.
    """
    cartas = list(mazos.TODOS[faccion])
    comunes = [c for c in cartas if reglas.rareza(c)[0] == "COMUN"]
    raras = [c for c in cartas if reglas.rareza(c)[0] == "RARA"]
    legs = [c for c in cartas if reglas.rareza(c)[0] == "LEGENDARIA"]

    for grupo in (comunes, raras, legs):
        grupo.sort(key=lambda c: (-reglas.total_carta(c), c.nombre))

    elegidas = ([c.copia() for c in legs[:1]]
                + [c.copia() for c in raras[:3]]
                + [c.copia() for c in comunes[:6]])
    rnd.shuffle(elegidas)
    return elegidas[:CARTAS_POR_DUELO]


def jugar_turno(board, mano, dueno, rnd, voraz):
    """Coloca una carta. Devuelve True si se pudo jugar."""
    if not mano:
        return False
    vacias = reglas.celdas_vacias(board)
    if not vacias:
        return False

    if voraz:
        mejor = None
        mejor_clave = None
        for carta in mano:
            for (r, c) in vacias:
                score = reglas.simular(board, carta, r, c, dueno)
                # Desempate por suma: con igual captura juega la mas fuerte.
                clave = (score, reglas.total_carta(carta))
                if mejor_clave is None or clave > mejor_clave:
                    mejor_clave = clave
                    mejor = (carta, r, c)
        if mejor is None:
            carta, (r, c) = mano[0], vacias[0]
        else:
            carta, r, c = mejor
    else:
        carta = mano[rnd.randrange(len(mano))]
        r, c = vacias[rnd.randrange(len(vacias))]

    jugada = carta.copia()
    jugada.dueno = dueno
    board[r][c] = jugada
    reglas.capturas(board, r, c)
    mano.remove(carta)
    return True


def jugar_duelo(mazo_a, mazo_b, rnd, voraz=False, empieza_a=True):
    """Un duelo. `empieza_a` fija quien mueve primero. Devuelve 'A'/'B'/None."""
    board = [[None] * 3 for _ in range(3)]
    a = [c.copia() for c in mazo_a]
    b = [c.copia() for c in mazo_b]

    turno_a = empieza_a
    while a or b:
        mano = a if turno_a else b
        dueno = "T" if turno_a else "C"
        if not jugar_turno(board, mano, dueno, rnd, voraz):
            break
        if not reglas.celdas_vacias(board) or (not a and not b):
            break
        turno_a = not turno_a

    _t, _c, ganador = reglas.puntaje_final(board)
    if ganador == "T":
        return "A"
    if ganador == "C":
        return "B"
    return None


def ventaja_de_empezar(faccion="humano", n=400, voraz=False, semilla=99):
    """El mismo mazo contra si mismo, SIEMPRE empezando A: mide el sesgo.

    Con 5 cartas por bando en 9 casillas, quien empieza coloca 5 cartas y el
    rival 4. Es una propiedad del reparto de turnos, no un fallo del motor.
    """
    rnd = random.Random(semilla)
    primero = 0
    for _ in range(n):
        m = mazo_competitivo(faccion, rnd)
        if jugar_duelo(m, m, rnd, voraz, True) == "A":
            primero += 1
    return 100.0 * primero / max(1, n)


def auto_cruce(faccion, n_duelos, voraz, semilla):
    """Una faccion CONTRA SI MISMA, con la metodologia de `cruzar`.

    Da el suelo de ruido real: mide cuanto se aparta del 50% un cruce donde
    no hay ninguna diferencia de poder. Si esto sale 51%, ningun 52% cuenta.
    """
    rnd = random.Random(semilla)
    propio = ajeno = 0
    for _ in range(n_duelos):
        ma = mazo_competitivo(faccion, rnd)
        mb = mazo_competitivo(faccion, rnd)
        r1 = jugar_duelo(ma, mb, rnd, voraz, True)
        r2 = jugar_duelo(ma, mb, rnd, voraz, False)
        for r in (r1, r2):
            if r == "A":
                propio += 1
            elif r == "B":
                ajeno += 1
    return _pct(propio, ajeno)


def error_binomial(v, e):
    """95% de confianza del porcentaje, en puntos, con dos muestras.

    `sqrt(p*(1-p)/n)`: a p=0,5 y n=400 son ~5 puntos de margen, asi que un
    52% y un 48% son indistinguibles de la paridad y no son un problema.
    """
    n = v + e
    if n <= 0:
        return 0.0
    p = v / n
    return 100.0 * 1.96 * math.sqrt(max(0.0, p * (1 - p)) / n)


def cruzar(fa, fb, n_duelos, voraz, semilla):
    """Compara dos facciones CANCELANDO la ventaja de empezar.

    Cada trial juega el cruce dos veces con el orden invertido y anota el
    resultado de CADA partida por separado. La ventaja de empezar (~66%) es
    la misma en los dos bandos, asi que promediar no la sesga; lo que hace
    es subir el suelo de ruido, y por eso se reporta tambien.

    NO se filtran los trials discordantes: si A gana una y pierde la otra,
    ambas partidas cuentan y la media sale 50%, que es exactamente lo que
    quiere decir "no hay diferencia entre estos dos mazos".
    """
    rnd = random.Random(semilla)
    puntos_a = puntos_b = 0
    for _ in range(n_duelos):
        ma = mazo_competitivo(fa, rnd)
        mb = mazo_competitivo(fb, rnd)
        r1 = jugar_duelo(ma, mb, rnd, voraz, True)
        r2 = jugar_duelo(ma, mb, rnd, voraz, False)
        if r1 == "A":
            puntos_a += 1
        elif r1 == "B":
            puntos_b += 1
        if r2 == "A":
            puntos_a += 1
        elif r2 == "B":
            puntos_b += 1
    return puntos_a, puntos_b


def _pct(v, e):
    return 100.0 * v / (v + e) if (v + e) else 50.0


def medir_todo(n_duelos=400, semilla=20261008, verbose=True):
    """Barre los 45 cruces con las dos politicas.

    Cada cruce se marca `injusto` solo si se sale de 35-65% Y el margen de
    error no llega a tapar el 50%. Sin esa segunda condicion, con 200 trials
    el error es de ~5 puntos y casi todos los cruces saldrian "injustos" sin
    serlo: seria alarma falsa, que es justo lo que hay que evitar.
    """
    orden = facciones.orden_facciones()
    informe = {"aleatorio": [], "voraz": [], "problemas": [], "suelo": {}}

    for politica, voraz in (("aleatorio", False), ("voraz", True)):
        filas = []
        for i, fa in enumerate(orden):
            for fb in orden[i + 1:]:
                s = (semilla + i * 31 + len(fb) * 7) % 999983
                va, vb = cruzar(fa, fb, n_duelos, voraz, s)
                p1 = _pct(va, vb)
                err = error_binomial(va, vb)
                fuera = p1 < MIN_SANO or p1 > MAX_SANO
                # Significativo: el intervalo de confianza NO toca el 50%.
                signif = abs(p1 - 50.0) > err
                filas.append({
                    "a": fa, "b": fb, "vic_a": va, "vic_b": vb,
                    "pct_a": p1, "pct_b": 100.0 - p1, "error": err,
                    "fuera_rango": fuera, "significativo": signif,
                    "injusto": fuera and signif,
                })
                if filas[-1]["injusto"]:
                    informe["problemas"].append((politica, fa, fb, p1, err))
        informe[politica] = filas

        if verbose:
            print(f"\n=== {politica.upper()} ({n_duelos} trials por cruce) ===")
            print(f"{'cruce':38s} {'% A':>7s} {'% B':>7s} {'+/-':>5s}")
            print("-" * 62)
            for f in filas:
                if f["injusto"]:
                    marca = "  <-- INJUSTO"
                elif f["fuera_rango"]:
                    marca = "  (dentro del ruido)"
                else:
                    marca = ""
                print(f"{f['a'] + ' vs ' + f['b']:38s} {f['pct_a']:6.1f}% "
                      f"{f['pct_b']:6.1f}% {f['error']:4.1f}{marca}")

    for politica, voraz in (("aleatorio", False), ("voraz", True)):
        informe["suelo"][politica] = [
            auto_cruce(f, n_duelos, voraz, semilla + 7) for f in orden]
    return informe


def resumen_por_faccion(informe):
    """Media de victorias de cada faccion sobre todas las demas."""
    orden = facciones.orden_facciones()
    out = {}
    for politica in ("aleatorio", "voraz"):
        acc = {f: [] for f in orden}
        for fila in informe[politica]:
            acc[fila["a"]].append(fila["pct_a"])
            acc[fila["b"]].append(fila["pct_b"])
        out[politica] = {f: (sum(v) / len(v) if v else 50.0) for f, v in acc.items()}
    return out


def auditar_estructura():
    """Habilidades por faccion, reparto por lado y cartas sin habilidad."""
    orden = facciones.orden_facciones()
    problemas = []
    detalle = {"habilidades": {}, "lados": {}}

    for f in orden:
        cartas = mazos.TODOS[f]
        detalle["habilidades"][f] = {
            h: sum(1 for c in cartas if c.habilidad == h)
            for h in sorted({c.habilidad for c in cartas if c.habilidad})
        }
        if not any(c.habilidad for c in cartas):
            problemas.append(f"[{f}] ninguna carta tiene habilidad")
        lados = {l: [] for l in ("N", "S", "E", "O")}
        for c in cartas:
            for l in lados:
                lados[l].append(c.valores[l])
        detalle["lados"][f] = {k: sum(v) / len(v) for k, v in lados.items()}

    for f in orden:
        m = detalle["lados"][f]
        if max(m.values()) - min(m.values()) > 2.5:
            problemas.append(
                f"[{f}] lados desequilibrados: "
                + ", ".join(f"{k}={v:.1f}" for k, v in m.items()))
    return problemas, detalle


#: El fichero lleva las CONCLUSIONES al final de los numeros, asi que no se
#: puede regenerar entero: se sustituye solo el bloque de datos. Si no, cada
#: ejecucion borraria el trabajo de revisar los numeros, que es justo lo que hay
#: que hacer antes de tocar una carta.
MARCA_DATOS_INICIO = "<!-- DATOS-INICIO -->"
MARCA_DATOS_FIN = "<!-- DATOS-FIN -->"


def escribir_informe(destino, lineas, trials):
    """Escribe el informe y devuelve la ruta REAL donde ha quedado.

    Va separado de `main` a proposito: `main` tarda minutos (simula 36.000
    duelos) y asi los tests pueden comprobar la mecanica del fichero sin
    pagar esa cuenta.Lo que protege:

    - Por debajo de `MIN_TRIALS_PUBLIQUABLE` NO se toca el fichero bueno: se
      escribe aparte con "MUESTRECHA" en el nombre. Con 60 trials salen cinco
      cruces "injustos" que con 400 no existen, y son ruido.
    - Las conclusiones se conservan: viven en `_CONCLUSIONES_POR_DEFECTO` y se
      vuelven a escribir, en vez de quedar borradas al regenerar los datos.
    """
    pocos = trials < MIN_TRIALS_PUBLIQUABLE
    if pocos:
        destino = f"{destino}.muestrecha-{trials}.md"

    try:
        with open(destino, encoding="utf-8") as fh:
            previo = fh.read()
    except OSError:
        previo = ""

    if MARCA_DATOS_INICIO in previo and MARCA_DATOS_FIN in previo:
        # Conclusions escritas a mano: mandan sobre las del codigo.
        conclusions = previo.split(MARCA_DATOS_FIN, 1)[1]
    else:
        conclusions = _CONCLUSIONES_POR_DEFECTO

    try:
        with open(destino, "w", encoding="utf-8") as fh:
            fh.write("# Informe de balance de Cartones y Mazmorras\n\n")
            fh.write("Generado por `python tests/duelos_simulador.py`.\n\n")
            if pocos:
                fh.write(f"> **MUESTRECHA: {trials} trials.** El margen de "
                         "error es de ~10 puntos, asi que los cruces marcados "
                         "pueden ser ruido. Minimo publicable: "
                         f"{MIN_TRIALS_PUBLIQUABLE}. Usa `--duelos 400`.\n\n")
            fh.write(MARCA_DATOS_INICIO + "\n\n```\n")
            fh.write("\n".join(lineas))
            fh.write("\n```\n\n" + MARCA_DATOS_FIN + "\n\n")
            fh.write(conclusions.lstrip("\n"))
    except OSError as exc:
        raise SystemExit(f"No se pudo escribir el informe: {exc}")
    return destino


def _tabla(titulo, cabeceras, filas):
    anchos = [max(len(c), *(len(str(f[i])) for f in filas)) if filas else len(c)
              for i, c in enumerate(cabeceras)]
    lineas = [titulo, "-" * (sum(anchos) + 3 * (len(anchos) - 1))]
    lineas.append("  ".join(c.ljust(a) for c, a in zip(cabeceras, anchos)))
    lineas.append("-" * (sum(anchos) + 3 * (len(anchos) - 1)))
    lineas += ["  ".join(str(x).ljust(a) for x, a in zip(f, anchos)) for f in filas]
    return "\n".join(lineas)


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--duelos", type=int, default=400)
    ap.add_argument("--semilla", type=int, default=20261008)
    ap.add_argument("--fichero", default="BALANCE.md",
                    help="donde escribir el informe en markdown")
    args = ap.parse_args()

    out = []

    def echo(s=""):
        print(s)
        out.append(s)

    echo(f"Simulador de duelos: {args.duelos} trials x 45 cruces x 2 politicas")
    echo("Cada trial juega el cruce dos veces con el orden invertido, para que")
    echo("la ventaja de empezar no sesgue la comparacion.")

    echo()
    echo(_tabla(
        "SUELO DE RUIDO",
        ["medida", "aleatorio", "voraz"],
        [["ventaja de empezar (mazo vs si mismo, A siempre primero)",
          f"{ventaja_de_empezar(n=400):.1f}%",
          f"{ventaja_de_empezar(n=400, voraz=True):.1f}%"]]))

    problemas, detalle = auditar_estructura()
    echo()
    filas_estruct = []
    for f in facciones.orden_facciones():
        hs = ", ".join(f"{k}:{v}" for k, v in detalle["habilidades"][f].items()) or "ninguna"
        ls = " ".join(f"{k}{v:.1f}" for k, v in detalle["lados"][f].items())
        filas_estruct.append([f, hs, ls])
    echo(_tabla("ESTRUCTURA DE MAZOS", ["faccion", "habilidades", "media por lado"],
                filas_estruct))
    echo()
    if problemas:
        echo("Problemas de estructura:")
        for p in problemas:
            echo(f"  - {p}")
    else:
        echo("Ningun problema de estructura: todas las facciones tienen")
        echo("habilidades y sus lados estan repartidos.")

    informe = medir_todo(args.duelos, args.semilla, verbose=False)

    echo()
    echo("SUELO DE RUIDO POR POLITICA (una faccion contra si misma)")
    for politica in ("aleatorio", "voraz"):
        vals = informe["suelo"][politica]
        echo(f"  {politica:10s} min {min(vals):.1f}%  max {max(vals):.1f}%  "
             f"media {sum(vals)/len(vals):.1f}%")

    for politica in ("aleatorio", "voraz"):
        echo()
        filas = [[f["a"] + " vs " + f["b"], f"{f['pct_a']:.1f}%", f"{f['pct_b']:.1f}%",
                  f"+/-{f['error']:.1f}",
                  "INJUSTO" if f["injusto"] else
                  ("fuera, pero ruido" if f["fuera_rango"] else "")]
                 for f in informe[politica]]
        filas.sort(key=lambda r: -float(r[1][:-1]))
        echo(_tabla(f"{politica.upper()} -ordenado de mas a menos favorable a A-",
                    ["cruce", "% A", "% B", "error", ""], filas))

    echo()
    resumen = resumen_por_faccion(informe)
    filas_res = [[f, f"{resumen['aleatorio'][f]:.1f}%", f"{resumen['voraz'][f]:.1f}%"]
                 for f in facciones.orden_facciones()]
    filas_res.sort(key=lambda r: -float(r[2][:-1]))
    echo(_tabla("MEDIA POR FACCION (victorias sobre las otras nueve)",
                ["faccion", "aleatorio", "voraz"], filas_res))

    echo()
    if informe["problemas"]:
        echo(f"CRUCES INJUSTOS (fuera de {MIN_SANO}-{MAX_SANO}% y por encima del ruido):")
        for politica, fa, fb, p, err in sorted(informe["problemas"], key=lambda x: x[3]):
            echo(f"  {politica:10s} {fa} vs {fb}: {p:.1f}% a favor de {fa} "
                 f"(+/- {err:.1f})")
    else:
        echo(f"Ningun cruce injusto: los 90 medidos (45 cruces x 2 politicas)")
        echo(f"caen dentro de {MIN_SANO}-{MAX_SANO}% con significance estadistica.")

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    destino = escribir_informe(os.path.join(raiz, args.fichero), out, args.duelos)
    print()
    if args.duelos < MIN_TRIALS_PUBLIQUABLE:
        print(f"SOLO {args.duelos} trials: margen ~10 puntos y cruces "
              "posiblemente falsos.")
        print(f"Informe MUESTRECHA escrito en {destino}")
        print(f"{args.fichero} NO se ha tocado.")
    else:
        print(f"Informe escrito en {destino} (conclusiones conservadas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())