"""Integridad de la version web: toda pantalla que dibuja frames debe ser async.

`asyncificar.py` es el codemod que convertsen `async` las pantallas con bucle
de render, porque pygbag exige `await asyncio.sleep(0)` dentro del bucle: sin
ello la pagina se congela. Su lista `PANTALLAS_ASYNC` es una lista NOMBRADA y
se queda vieja en cuanto se anade una pantalla nueva: no avisa de las que se
cuelan.

Este test no se fia de esa lista. Comprueba la propiedad directamente sobre el
codigo: toda funcion que dibuja frames (`display.flip` o `clock.tick`) tiene
que ser `async def`. Asi anadir una pantalla sin convertirla rompe el build, que
es justo cuando hay que enterarse.
"""

import ast
import io
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)


def _arbol(modulo):
    with io.open(os.path.join(RAIZ, modulo), encoding="utf-8") as f:
        return ast.parse(f.read())


class TestPantallasAsync(unittest.TestCase):
    MODULOS = ("pantallas.py", "partida.py", "cinematicas.py")

    def _dibujadoras_sincronas(self, modulo):
        """Funciones sync que tienen un BUCLE y dibujan: esas congelan la web.

        No basta con que pinten un frame: `Cinematica.ejecutar_un_frame` pinta
        uno solo, a proposito y sin eventos, para demos y tests, y es correcto
        que sea sync. Lo que rompe pygbag es un bucle de render sin `await`.
        """
        with io.open(os.path.join(RAIZ, modulo), encoding="utf-8") as f:
            src = f.read()
        arbol = ast.parse(src)
        malas = []
        for node in ast.walk(arbol):
            if not isinstance(node, ast.FunctionDef):
                continue          # solo las sync; las async ya estan bien
            seg = ast.get_source_segment(src, node) or ""
            dibuja = "display.flip" in seg or "clock.tick" in seg
            if not dibuja:
                continue
            # Un bucle real dentro del cuerpo: `while` o `for`.
            tiene_bucle = any(isinstance(n, (ast.While, ast.For))
                              for n in ast.walk(node))
            if not tiene_bucle:
                continue          # pinta un frame y sale: es correcto
            if "await " in seg:
                continue          # envuelto a mano dentro de un async
            malas.append(node.name)
        return malas

    def test_ninguna_pantalla_dibuja_frames_de_forma_sincrona(self):
        for modulo in self.MODULOS:
            malas = self._dibujadoras_sincronas(modulo)
            self.assertEqual(
                [], malas,
                f"{modulo}: estas funciones dibujan frames pero no son async: "
                f"{malas}. Sin `await asyncio.sleep(0)` el bucle congela la "
                f"version web.")

    def test_la_lista_de_asyncificar_no_esta_obsoleta(self):
        """Si el codemod nombra pantallas que ya no existen, avisa.

        Una lista con nombres caducados no rompe nada por si sola, pero
        significa que nadie la esta manteniendo y hay que saberlo.
        """
        import asyncificar

        with io.open(os.path.join(RAIZ, "pantallas.py"), encoding="utf-8") as f:
            arbol = ast.parse(f.read())
        existentes = {n.name for n in arbol.body
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        caducados = [n for n in asyncificar.PANTALLAS_ASYNC if n not in existentes]
        self.assertEqual([], caducados,
                         f"asyncificar.PANTALLAS_ASYNC nombra funciones que ya "
                         f"no existen: {caducados}")


if __name__ == "__main__":
    unittest.main()