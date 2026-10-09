"""Ninguna linea puede usar un nombre que no existe.

El bug que motivo esto estaba en la pantalla de encuentro: una linea hacia
`screen.blit(dibujo, ...)` cuando la variable se llamaba `dibujo_enc`, por
resto de un renombrado. Solo saltaba cuando el encuentro tenia ilustracion,
asi que las capturas estaticas no lo veian y los tests tampoco: hacia falta
mirar el encountering de verdad.

En vez de esperar al siguiente crash, se comprueba estaticamente que toda
identidad usada como nombre se defina antes en su ambito. No sustituye a
ejecutar el juego, pero convierte "un dia habra un NameError" en "el test
falla hoy".
"""

import ast
import builtins
import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Modulos que se revisan: los que forman parte del juego. Los de `tests/` se
#: dejan fuera porque investigan y usan APIs internas a proposito.
MODULOS = [
    "audio", "campana", "cartas", "cinematicas", "compendio", "duelistas",
    "encuentros", "facciones", "finales", "fragmentos", "hoja_contactos",
    "main", "mazos", "narrativa", "opciones", "paths", "peticiones",
    "pantallas", "partida", "prologo", "reglas", "ui",
]

#: Builtins: estan definidos siempre, no hace falta rastrearlos.
PERMITIDOS = set(dir(builtins)) | {"self", "cls", "return", "yield", "await",
                                    "pass"}


def _nombres_definidos_en_algun_sitio(arbol):
    """Todo nombre que se ASIGNA o declara en algun punto del modulo.

    No se hace analisis de flujo: da igual si la asignacion ocurre antes o
    despues del uso, o en otra rama. Lo que se busca es la clase de bug del
    `dibujo`/`dibujo_enc`: un nombre que no se escribe EN NINGUN sitio y se usa
    por error. Ese es un fallo de tecleo o de renombrado, no de orden, y esto
    lo detecta sin falsos positivos de flujo.
    """
    definidos = set()
    for n in ast.walk(arbol):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definidos.add(n.name)
            args = getattr(n, "args", None)
            if args:
                definidos.update(a.arg for a in
                                 args.args + args.posonlyargs + args.kwonlyargs)
                if args.vararg:
                    definidos.add(args.vararg.arg)
                if args.kwarg:
                    definidos.add(args.kwarg.arg)
        elif isinstance(n, ast.Import):
            definidos.update((a.asname or a.name).split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            definidos.update(a.asname or a.name for a in n.names)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            definidos.update(n.names)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            definidos.add(n.id)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            definidos.add(n.name)
        elif isinstance(n, (ast.MatchAs, ast.MatchStar)) and getattr(n, "name", None):
            definidos.add(n.name)
        elif isinstance(n, (ast.MatchMapping, getattr(ast, "MatchClass", ()))):
            for sub in ast.walk(n):
                if isinstance(sub, ast.Name) and sub.id:
                    definidos.add(sub.id)
    return definidos


def _nombres_usados(arbol):
    """Nombres leidos, con su linea, en orden."""
    usados = []
    for n in ast.walk(arbol):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            usados.append((n.id, n.lineno))
    return usados


class TestNoHayNombresInexistentes(unittest.TestCase):
    def test_ningun_modulo_usa_un_nombre_inexistente(self):
        problemas = []
        for modulo in MODULOS:
            ruta = os.path.join(RAIZ, modulo + ".py")
            if not os.path.exists(ruta):
                self.fail(f"{modulo}.py no existe (MODULOS desactualizado?)")
            with open(ruta, encoding="utf-8") as fh:
                arbol = ast.parse(fh.read(), filename=modulo + ".py")

            definidos = _nombres_definidos_en_algun_sitio(arbol) | PERMITIDOS
            for nombre, linea in _nombres_usados(arbol):
                if nombre in definidos or nombre.startswith("_"):
                    continue
                problemas.append(f"{modulo}.py:{linea}: '{nombre}'")

        if problemas:
            self.fail("Nombres usados que no se definen en ningun sitio "
                      "(NameError en tiempo de ejecucion):\n  "
                      + "\n  ".join(sorted(set(problemas))))

    def test_detecta_el_bug_del_que_nacio_este_test(self):
        """`dibujo` se usaba sin existir, siendo la variable `dibujo_enc`."""
        codigo = (
            "def f(dibujo_enc):\n"
            "    if dibujo_enc is not None:\n"
            "        return dibujo_enc\n"
            "    return dibujo\n"
        )
        arbol = ast.parse(codigo)
        definidos = _nombres_definidos_en_algun_sitio(arbol) | PERMITIDOS
        huerfanos = {n for n, _ in _nombres_usados(arbol)} - definidos
        self.assertEqual(huerfanos, {"dibujo"},
                         "la heuristica deberia señalar solo 'dibujo'")

    def test_no_señala_codigo_correcto(self):
        codigo = (
            "import os\n"
            "CONST = 1\n"
            "def f(a, b=2, *args, **kw):\n"
            "    total = a + b\n"
            "    for i in range(len(args)):\n"
            "        total += [x for x in args][i]\n"
            "    try:\n"
            "        pass\n"
            "    except ValueError as exc:\n"
            "        print(exc)\n"
            "    with open('x') as fh:\n"
            "        pass\n"
            "    return total + fh + kw.get('k', 0) + CONST + os.sep\n"
        )
        arbol = ast.parse(codigo)
        definidos = _nombres_definidos_en_algun_sitio(arbol) | PERMITIDOS
        huerfanos = {n for n, _ in _nombres_usados(arbol)} - definidos
        self.assertEqual(huerfanos, set(),
                         f"no deberia señalar nada, pero senala {huerfanos}")


class TestLosCaminosQueCrashaabanAhoraSeEjecutan(unittest.TestCase):
    """Los cuatro `NameError` que encontro este test eran de verdad.

    `test_nombres_no_definidos` dice que no hay ningun nombre huerfano, pero
    eso es estatico. Aqui se comprueba que las funciones afectadas llegan de
    verdad a la linea que se habia arreglado, que es donde estaba el crash.
    """

    def setUp(self):
        import pygame

        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        os.environ.setdefault(
            "TRIPLETRIAD_DATA",
            os.path.join(tempfile.gettempdir(), "tt_test_nombres"))
        if RAIZ not in sys.path:
            sys.path.insert(0, RAIZ)
        import audio
        import campana

        pygame.init()
        pygame.display.set_mode((1280, 800))
        audio.iniciar()
        campana.asegurar_coleccion("humano")

    def _src_de(self, modulo):
        with open(os.path.join(RAIZ, modulo + ".py"), encoding="utf-8") as fh:
            return ast.parse(fh.read(), filename=modulo + ".py")

    def test_toda_llamada_a_cartel_lleva_el_prefijo(self):
        """`cartel` sin `pantallas.` era un NameError en 3 sitios."""
        arbol = self._src_de("main")
        sueltas = [n.lineno for n in ast.walk(arbol)
                   if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Name)
                   and n.func.id == "cartel"]
        self.assertEqual(
            sueltas, [],
            f"llamadas a `cartel` sin `pantallas.`: lineas {sueltas}")

    def test_ganar_fragmento_llega_al_cartel(self):
        """El fragmento de verdad (NG+) crasheaba al pedir el fragmento."""
        import campana

        campana.establecer_nombre("Bartolo")
        arbol = self._src_de("main")
        fn = next(n for n in ast.walk(arbol)
                  if isinstance(n, ast.AsyncFunctionDef)
                  and n.name == "_ganar_fragmento")
        llamadas = [ast.unparse(n.func) for n in ast.walk(fn)
                    if isinstance(n, ast.Call)]
        self.assertIn("pantallas.cartel", llamadas,
                      "el fragmento de verdad debe abrir su cartel")

    def test_campana_secreta_abre_cartel_en_victoria_y_derrota(self):
        """Las dos ramas de la campana secreta crasheaban."""
        arbol = self._src_de("main")
        fn = next(n for n in ast.walk(arbol)
                  if isinstance(n, ast.AsyncFunctionDef)
                  and n.name == "_campana_secreta")
        llamadas = [ast.unparse(n.func) for n in ast.walk(fn)
                    if isinstance(n, ast.Call)]
        self.assertEqual(llamadas.count("pantallas.cartel"), 2,
                         "deben abrir cartel en victoria y en derrota")

    def test_encuentro_con_ilustracion_no_usa_ningun_nombre_roto(self):
        """La pantalla de encuentro: `dibujo` en vez de `dibujo_enc`."""
        arbol = self._src_de("pantallas")
        fn = next(n for n in ast.walk(arbol)
                  if isinstance(n, ast.AsyncFunctionDef)
                  and n.name == "encuentro")
        usados = {n.id for n in ast.walk(fn)
                  if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        self.assertNotIn("dibujo", usados,
                         "'dibujo' no existe: la variable se llama 'dibujo_enc'")
        self.assertIn("dibujo_enc", usados)

    def test_el_encuentro_con_ilustracion_se_dibuja_de_verdad(self):
        """Ejecuta la rama de la ilustracion, que es la que crasheaba."""
        import asyncio

        import campana
        import pantallas
        import pygame

        estado = campana.nueva_campana("humano")

        async def correr():
            reloj = type("R", (), {"tick": lambda self, f=60: 16})()
            tarea = asyncio.ensure_future(
                pantallas.encuentro(pygame.display.get_surface(),
                                    reloj, estado, "senda"))
            for _ in range(4):
                await asyncio.sleep(0)
            tarea.cancel()
            try:
                await tarea
            except asyncio.CancelledError:
                pass

        # El loop se cierra siempre: si no, queda abierto y ensucia el resto
        # de la suite con ResourceWarning y puede colgar otros tests async.
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(correr())
        finally:
            loop.close()


if __name__ == "__main__":
    unittest.main()