"""Los documentos de entrega tienen que estar sanos, no solo existir.

`docs/informe_g9.md` es la evidencia de cierre de G9 y aparecio con la frase
"es lo que vale" pegada 70 veces, partiendo frases y hasta palabras:

    "| cero bloque **es lo que vale**os o perdidas ..."  -> "bloqueos"
    "**es lo que valeda** pendiente"                    -> "queda pendiente"
    "**porvalidada**"                                   -> "por validada"
    "cuando **es lo que vale** hay que no lo haria"     -> "cuando no deberia"

Setenta frases partidas. Nadie lo habia leido porque el fichero existia y
tenia el tamano esperado: "esta" no es lo mismo que "esta bien".

Estos tests miran las formas ROTAS, no las reparadas. Comprobado: ejecutados
sobre el fichero tal como estaba, fallan.

Tambien vigilan la convencion del proyecto (ASCII en la documentacion) y que
la sangria de las listas de Markdown no se destruya, porque un espacio de mas
o de menos convierte una lista en un parrafo.
"""

import io
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(RAIZ, "docs")
PERMITIDOS = set("áéíóúñÁÉÍÓÚÑ¿¡°—·«»→±")
PERMITIDOS.update("×–“”≥─│└├")

#: Formas rotas que delatan la sustitucion espuria. Cada una es una frase o
#: una palabra que NO se escriben asi.
FRASES_ROTAS = (
    "es lo que vale",      # la frase entera pegada
    "que es lo que |",     # dos seguidas, con la barra del separador
    "bloque es lo que valeos",   # "bloqueos" partido
    "bloque es lo que valeado",  # "bloqueado" partido
    "valeda",              # "queda" partido
    "porvalidada",         # "por validada" partido
    "valearse",            # "sin repetir nodo ni bloquearse"
)


def _sin_bloques(texto):
    """Quita los bloques cercados ```...```.

    Documentar un defecto obliga a citar sus formas rotas. Un ejemplo dentro de
    un bloque de codigo es documentacion, no una prosa partida, asi que ahi no
    se busca nada. Fuera de los bloques, cualquier forma rota es un fallo.
    """
    lineas = texto.split("\n")
    fuera, dentro = [], False
    for l in lineas:
        if l.lstrip().startswith("```"):
            dentro = not dentro
            fuera.append("")
            continue
        fuera.append("" if dentro else l)
    return "\n".join(fuera)


def _documentos():
    for nombre in sorted(os.listdir(DOCS)):
        if nombre.endswith(".md"):
            yield os.path.join(DOCS, nombre)


def _leer(ruta):
    with io.open(ruta, encoding="utf-8") as fh:
        return fh.read()


def _lineas(ruta):
    return _leer(ruta).split("\n")


class TestDocumentacionSana(unittest.TestCase):

    def test_no_hay_frases_pegadas_ni_palabras_partidas(self):
        for ruta in _documentos():
            texto = _sin_bloques(_leer(ruta))
            for rota in FRASES_ROTAS:
                self.assertNotIn(
                    rota, texto,
                    f"{os.path.basename(ruta)}: {rota!r} (frase pegada o "
                    f"palabra partida por una sustitucion)")

    def test_unicode_legible_en_la_documentacion(self):
        """Español y símbolos usados en tablas, medidas y diagramas."""
        for ruta in _documentos():
            texto = _leer(ruta)
            malos = sorted({c for c in texto if ord(c) > 127 and c not in PERMITIDOS})
            self.assertEqual(
                [], malos,
                f"{os.path.basename(ruta)} tiene no-ASCII: "
                f"{[hex(ord(c)) for c in malos]}")

    def test_la_sangria_de_las_listas_esta_intacta(self):
        """Una linea de lista en Markdown lleva 2-4 espacios o empieza por '-'.

        Una sustitucion que colapsa espacios convierte la lista en prosa y el
        documento deja de leerse como informe. Los bloques de codigo se saltan:
        ahi la sangria es parte del ejemplo.
        """
        for ruta in _documentos():
            for i, linea in enumerate(_sin_bloques(_leer(ruta)).split("\n"), 1):
                sangria = len(linea) - len(linea.lstrip(" "))
                if sangria == 1:
                    self.fail(
                        f"{os.path.basename(ruta)}:{i} sangria de 1 espacio: "
                        f"la lista se ha deshecho |{linea[:60]}|")
                if sangria > 8:
                    self.fail(
                        f"{os.path.basename(ruta)}:{i} sangria de {sangria} "
                        f"espacios: probablemente un bloque de codigo")

    def test_no_hay_saltos_de_linea_en_mitad_de_una_frase(self):
        """Dos espacios al final son un `<br>`. En medio de una frase envuelta
        son un fallo: la frase queda partida en dos lineas visibles."""
        for ruta in _documentos():
            lineas = _sin_bloques(_leer(ruta)).split("\n")
            for i, linea in enumerate(lineas[:-1], 1):
                if not linea.endswith("  "):
                    continue
                siguiente = lineas[i].strip()
                # Un salto legitimo es el de una celda de tabla o el de un
                # elemento de lista; no el de una frase a mitad.
                if (siguiente and not siguiente.startswith(("-", "|", ">", "#"))
                        and linea.strip() and not linea.lstrip().startswith("**")):
                    self.fail(
                        f"{os.path.basename(ruta)}:{i} salto de linea a "
                        f"mitad de una frase: |{linea.strip()}| / "
                        f"|{siguiente}|")

    def test_el_informe_de_g9_cubre_lo_que_dice_cubrir(self):
        """El documento tiene que seguir siendo el indice de la evidencia."""
        texto = _leer(os.path.join(DOCS, "informe_g9.md"))
        for seccion in ("Recorridos integrados", "Texto ampliado",
                        "Propiedad de las cartas", "Integridad de la version web",
                        "Lo que NO se ha hecho"):
            self.assertIn(seccion, texto, f"falta la seccion {seccion!r}")
        # Y los dos pendientes externos tienen que seguir declarados.
        self.assertIn("playtest", texto.lower())
        self.assertIn("pendiente", texto.lower())


if __name__ == "__main__":
    unittest.main()
