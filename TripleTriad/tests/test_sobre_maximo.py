"""El sobre no puede anunciar un +1 que no ocurre (G5).

G5 pide, literalmente, "contemplar carta al maximo sin anunciar +1 falso".
Reproducido antes de corregir:

    coleccion con las tres cartas del sobre a 10/10/10/10
    -> el encuentro de la caravana decia
       "duplicadas (+1): Oraculo de Sangre, Musgo Viejo, Ansia Nocturna"
    -> y el detalle real, que el propio codigo guardaba, era
       "Al maximo: sin cambio" en las tres

O sea: el juego decia "+1" a un jugador que se iba a quedar igual, y la
verdad estaba a un `cargar_perfil()` de distancia. No hacia falta adivinar
nada: el detalle exacto ya lo calculaba `abrir_sobre`.

Aqui se mide: se compara lo que el texto anuncia con lo que las cartas valen
antes y despues. No se mira el texto: se miran los numeros.
"""

import os
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import campana  # noqa: E402
import mazos  # noqa: E402

CATALOGO = {c.nombre: c for lista in mazos.TODOS.values() for c in lista}


def _coleccion_al_maximo(nombres):
    return {n: {"nombre": n, "n": 10, "s": 10, "e": 10, "o": 10,
                "bando": CATALOGO[n].bando,
                "habilidad": CATALOGO[n].habilidad}
            for n in nombres}


def _fuerza_perfil():
    """Suma de los cuatro lados de toda la coleccion poseida.

    Solo los cuatro lados: el dict de cada carta tambien trae `nombre`,
    `bando` y `habilidad`, que son cadenas y no se suman.
    """
    perfil = campana.cargar_perfil()
    total = 0
    for d in perfil.get("coleccion", {}).values():
        if isinstance(d, dict):
            total += sum(int(d.get(l, 0) or 0) for l in "nseo")
    return total


class TestSobreNoAnunciaMasDeLoQueDa(unittest.TestCase):

    def setUp(self):
        directorio = tempfile.TemporaryDirectory(prefix="tt_sobre_max_")
        self.addCleanup(directorio.cleanup)
        env = patch.dict(os.environ, {"TRIPLETRIAD_DATA": directorio.name})
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(random.setstate, random.getstate())

    def _abrir(self, coleccion):
        random.seed(3)
        estado = campana.nueva_campana("humano")
        campana.guardar_perfil({"moneda": 5000, "coleccion": coleccion})
        antes = _fuerza_perfil()
        titulo, texto = campana.aplicar_encuentro(estado, "sobre")
        return titulo, texto, _fuerza_perfil() - antes

    def test_duplicadas_al_maximo_no_anuncian_un_mas(self):
        """Con toda la coleccion al 10, ningun texto puede prometer un +1."""
        todo = list(CATALOGO)
        titulo, texto, delta = self._abrir(_coleccion_al_maximo(todo))
        self.assertEqual(0, delta,
                         "con las cartas al maximo no deberia subir nada")
        self.assertIn("duplicadas", texto)
        self.assertNotIn("(+1)", texto,
                         f"anuncia un +1 que no ocurrio: {texto!r}")

    def test_el_texto_dice_que_estan_al_maximo(self):
        todo = list(CATALOGO)
        titulo, texto, delta = self._abrir(_coleccion_al_maximo(todo))
        self.assertIn("maximo", texto.lower(),
                      f"el jugador no puede saber que no ha subido: {texto!r}")

    def test_cuando_sube_de_verdad_lo_dice(self):
        """Sustituto: si una duplicada sube, el texto dice cuanto.

        Se posee TODO el catalogo, asi que el sobre solo puede sacar
        duplicadas y cualquier subida viene de una mejora. Sin este control, el
        test anterior pasaria con un texto vacio o con una etiqueta fija que no
        cuadre con nada.
        """
        coleccion = _coleccion_al_maximo(sorted(CATALOGO))
        # Cualquier carta sorteada tiene exactamente un lado mejorable.
        for datos in coleccion.values():
            datos["s"] = 4
        _, texto, delta = self._abrir(coleccion)
        self.assertEqual(3, delta, "tres duplicadas deben sumar tres puntos")
        detalles = campana.cargar_perfil()["ultimo_sobre_detalles"]
        self.assertEqual(3, len(detalles))
        for nombre, detalle in detalles.items():
            self.assertEqual("S: 4 -> 5", detalle)
            self.assertIn(f"{nombre} ({detalle})", texto)
        self.assertNotIn("(+1)", texto,
                         "el texto deberia dar el valor, no una etiqueta")

    def test_el_detalle_guardado_y_el_texto_coinciden(self):
        """Lo que se enseña tiene que ser lo que el codigo calculo."""
        todo = list(CATALOGO)
        _, texto, _ = self._abrir(_coleccion_al_maximo(todo))
        detalles = campana.cargar_perfil().get("ultimo_sobre_detalles", {})
        self.assertTrue(detalles, "no se guardo ningun detalle del sobre")
        for nombre, detalle in detalles.items():
            self.assertEqual("Al maximo: sin cambio", detalle)
            self.assertIn(f"{nombre} ({detalle})", texto)


if __name__ == "__main__":
    unittest.main()
