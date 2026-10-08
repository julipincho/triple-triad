"""Convierte las pantallas con bucle de render en async (requisito de pygbag).

pygbag exige `await asyncio.sleep(0)` dentro del bucle del juego; sin eso la
pagina se congela. Solo se tocan las funciones que dibujan frames.
"""
import ast
import sys

PANTALLAS_ASYNC = [
    "portada", "menu", "elegir_faccion", "mapa_campana", "_ficha_nodo",
    "elegir_rama", "recompensa", "elegir_carta_para_mejorar", "draft",
    "draft_reemplazo", "aplicar_recompensa", "cartel", "encuentro",
    "coleccion", "ajustes", "_pantalla_ayuda", "pantalla_error", "derrota",
    "epilogo",
]


def rango_funcion(tree, nombre, es_metodo=False):
    """Lineas [inicio, fin] de la funcion/contenido de la funcion."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == nombre:
            return node.lineno, node.end_lineno
    return None


def transformar(ruta, nombres, tras_tick=True, importar=True):
    src = open(ruta, encoding="utf8").read()
    tree = ast.parse(src)
    lineas = src.splitlines(keepends=True)

    rangos = []
    for n in nombres:
        r = rango_funcion(tree, n)
        if r is None:
            print(f"  ! no existe {n} en {ruta}")
            continue
        rangos.append(r)
        ini, fin = r
        # convertir el def en async def en su linea de inicio
        i = ini - 1
        if lineas[i].lstrip().startswith("def "):
            lineas[i] = lineas[i].replace("def ", "async def ", 1)
        elif not lineas[i].lstrip().startswith("async def "):
            print(f"  ! {n}: linea {ini} inesperada: {lineas[i]!r}")

    # insertar el yield de navegador tras cada clock.tick() de esas funciones
    inserciones = []
    if tras_tick:
        for ini, fin in rangos:
            for i in range(ini - 1, fin):
                stripped = lineas[i].lstrip()
                if "clock.tick(" in lineas[i] and stripped.startswith(("dt =", "clock.tick(")):
                    indent = lineas[i][: len(lineas[i]) - len(lineas[i].lstrip())]
                    if "await asyncio.sleep(0)" not in lineas[i + 1]:
                        inserciones.append((i + 1, f"{indent}await asyncio.sleep(0)\n"))

    for pos, texto in sorted(inserciones, reverse=True):
        lineas.insert(pos, texto)

    nuevo = "".join(lineas)

    if importar and "import asyncio" not in nuevo:
        # despues del docstring/primer import
        tree2 = ast.parse(nuevo)
        lineas2 = nuevo.splitlines(keepends=True)
        ultimo_import = 0
        for node in tree2.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                ultimo_import = max(ultimo_import, node.end_lineno)
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                ultimo_import = max(ultimo_import, node.end_lineno)
        lineas2.insert(ultimo_import, "\nimport asyncio\n")
        nuevo = "".join(lineas2)

    open(ruta, "w", encoding="utf8", newline="\n").write(nuevo)
    print(f"{ruta}: {len(rangos)} funciones async, {len(inserciones)} yields")


if __name__ == "__main__":
    transformar("pantallas.py", PANTALLAS_ASYNC)
    transformar("partida.py", ["partida"])
    transformar("cinematicas.py", ["ejecutar", "reproducir"])
    # tutorial.py ya nace async con sus yields; si se vuelve a correr,
    # solo verifica que existen (no rompe nada ya convertido).
    transformar("tutorial.py", ["manual", "tutorial", "puerta_primer_arranque"])
    sys.exit(0)
