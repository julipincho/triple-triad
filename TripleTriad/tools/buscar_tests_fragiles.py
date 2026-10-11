"""Detector de tests fragil: asertan sobre datos que el juego sortea.

Un test que comprueba una cifra sobre un mazo, un sobre o un rival ALEATORIO
pasa casi siempre y falla de vez en cuando. Es la forma mas comun de tener una
suite que "a veces esta verde", y entrena a reintentar en vez de a mirar.

Este script revisa los tests y marca los que:
  - crean una campana / abren un sobre / sortean un draft / arman un rival
    (es decir, consumen azar), y
  - ademas comprueban una MAGNITUD numerica (comparaciones con numeros, no
    igualdad de estructuras).

No es un test: es una herramienta de auditoria. Los falsos positivos se
descartan mirando el caso.

    python tools/buscar_tests_fragiles.py
"""

import ast
import io
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(RAIZ, "tests")

#: Funciones del juego whose result depends on the RNG.
AZAR = {"nueva_campana", "abrir_sobre", "comprar_sobre", "draft_aleatorio",
        "mazo_rival", "nueva_mini_campana", "_abrir_sobre", "elegir_ancla"}

#: Comparaciones numericas: un numero contra otro.
COMPARACIONES = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)


def _nombre_llamada(func):
    """Nombre de la llamada, sea `nombre()` o `modulo.nombre()`.

    La mayoria del juego se llama con prefijo (`campana.mazo_rival`), asi que
    mirar solo `ast.Name` no encuentra casi nada: el detectoreria cero tests y
    pareceria que todo esta bien.
    """
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def usa_azar(nodo):
    for sub in ast.walk(nodo):
        if isinstance(sub, ast.Call) and _nombre_llamada(sub.func) in AZAR:
            return True
    return False


#: Aserciones que comparan dos valores (la forma mas comun de escribir un
#: test numerico en unittest; buscar solo operadores `>` en el codigo se
#: escapaba de todas ellas).
ASERCIONES = {"assertGreater", "assertLess", "assertGreaterEqual",
              "assertLessEqual", "assertAlmostEqual"}


def compara_numeros(nodo):
    for sub in ast.walk(nodo):
        # caso 1: `assertGreater(a, b)` y compañía
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                and sub.func.attr in ASERCIONES:
            return True
        # caso 2: comparacion suelta en una expresion, tipo `assertTrue(x > 3)`
        if isinstance(sub, ast.Compare):
            for op, comp in zip(sub.ops, sub.comparators):
                if isinstance(op, COMPARACIONES):
                    if isinstance(comp, ast.Constant) and isinstance(comp.value, (int, float)):
                        return True
                    if isinstance(comp, (ast.Call, ast.Attribute, ast.Subscript,
                                          ast.BinOp, ast.Name)):
                        return True
    return False


def fija_semilla(nodo):
    """El test fija la semilla: entonces el azar deja de ser azar."""
    for sub in ast.walk(nodo):
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                and sub.func.attr == "seed":
            return True
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) \
                and sub.func.id in ("randomseed", "sembrar"):
            return True
    return False


def main():
    hallazgos = []
    for nombre in sorted(os.listdir(TESTS)):
        if not nombre.startswith("test_") or not nombre.endswith(".py"):
            continue
        ruta = os.path.join(TESTS, nombre)
        with io.open(ruta, encoding="utf-8") as f:
            arbol = ast.parse(f.read())
        for node in ast.walk(arbol):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test"):
                continue
            if usa_azar(node) and compara_numeros(node):
                hallazgos.append((nombre, node.name, node.lineno,
                                  "fijado" if fija_semilla(node) else "SIN FIJAR"))

    if not hallazgos:
        print("No se han encontrado tests fragiles (azar + comparacion numerica).")
        return 0
    print("Tests que comprueban cifras sobre datos que el juego sortea:")
    print()
    for nombre, func, linea, estado in hallazgos:
        marca = "ok " if estado == "fijado" else ">> "
        print(f"  {marca}{nombre}:{linea}  {func}  [{estado}]")
    print()
    sin = sum(1 for _n, _f, _l, e in hallazgos if e != "fijado")
    print(f"total: {len(hallazgos)}  (sin fijar la semilla: {sin})")
    return 0


if __name__ == "__main__":
    sys.exit(main())