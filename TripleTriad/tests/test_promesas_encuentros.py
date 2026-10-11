"""Los encuentros prometen un efecto mecanico y tienen que cumplirlo.

`ENCUENTROS` ofrece ocho opciones al jugador y cada una anuncia en su texto lo
que va a pasar. G6 pide que "cada promesa mecanica del texto tiene efecto
verificable o se reescribe como narrativa".

Este test mide el mazo ANTES y DESPUES de aplicar cada efecto y comprueba que
el texto y el efecto coinciden. Se escribio porque al revisar las promesas
encontrado que una de ellas no hacia nada: el jugador leia "recibiste un punto
mas de fuerza" y su mazo no habia cambiado.
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


def _fuerza(estado):
    """Suma de todos los lados de todas las cartas del mazo, ya.mejoradas."""
    return sum(sum(c.valores.values()) for c in campana.cartas_jugador(estado))


def _efectos():
    for encuentro in campana.ENCUENTROS:
        for opcion in encuentro["opciones"]:
            yield encuentro["id"], opcion


class TestPromesasDeEncuentro(unittest.TestCase):

    def setUp(self):
        directorio = tempfile.TemporaryDirectory(prefix="tt_encuentros_")
        self.addCleanup(directorio.cleanup)
        env = patch.dict(os.environ, {"TRIPLETRIAD_DATA": directorio.name})
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(random.setstate, random.getstate())

    def _aplicar(self, efecto):
        random.seed(4242)
        campana.guardar_perfil({})
        estado = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        antes_fuerza = _fuerza(estado)
        antes_cartas = [c.nombre for c in campana.cartas_jugador(estado)]
        antes_coleccion = campana.coleccion_de()
        titulo, texto = campana.aplicar_encuentro(estado, efecto)
        return {
            "estado": estado,
            "titulo": titulo,
            "texto": texto,
            "delta": _fuerza(estado) - antes_fuerza,
            "antes_cartas": antes_cartas,
            "despues_cartas": [c.nombre for c in campana.cartas_jugador(estado)],
            "antes_coleccion": antes_coleccion,
            "despues_coleccion": campana.coleccion_de(),
        }

    def test_todas_las_opciones_anuncian_una_efecto_conocido(self):
        for enc_id, opcion in _efectos():
            efecto = opcion["efecto"]
            with self.subTest(encuentro=enc_id, opcion=opcion["id"]):
                r = self._aplicar(efecto)
                self.assertNotIn(
                    "No ocurre nada", r["texto"],
                    f"el efecto {efecto!r} cae en el 'return' por defecto: "
                    f"no hace nada")

    def test_ningun_efecto_anuncia_fuerza_sin_darla(self):
        """"un punto mas de fuerza" con el mazo igual es una promesa rota."""
        for enc_id, opcion in _efectos():
            efecto = opcion["efecto"]
            with self.subTest(encuentro=enc_id, opcion=opcion["id"]):
                r = self._aplicar(efecto)
                if "+1" in opcion["texto"] or "mas fuerte" in r["texto"]:
                    self.assertGreater(
                        r["delta"], 0,
                        f"el texto anuncia +1 y el mazo no cambio: "
                        f"{opcion['texto']!r} devolvio {r['texto']!r} "
                        f"(delta {r['delta']})")

    def test_robo_entrega_una_carta(self):
        r = self._aplicar("robo")
        nuevas = set(r["despues_coleccion"]) - set(r["antes_coleccion"])
        self.assertEqual(1, len(nuevas))
        self.assertIn(next(iter(nuevas)), r["texto"])

    def test_sobre_abre_tres_cartas(self):
        r = self._aplicar("sobre")
        self.assertIn("Caravana", r["titulo"])
        self.assertIn("Abres el sobre", r["texto"])
        nuevas = set(r["despues_coleccion"]) - set(r["antes_coleccion"])
        cambiadas = {n for n in r["antes_coleccion"]
                     if r["antes_coleccion"][n] != r["despues_coleccion"][n]}
        self.assertEqual(3, len(nuevas | cambiadas))

    def test_mejorar_respeta_la_carta_elegida(self):
        """La opcion promete "la que elijas": con `idx` se mejora esa y no otra."""
        random.seed(7)
        campana.guardar_perfil({})
        estado = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        elegido = 3
        # Se elige una carta que NO sea la mas debil, para que la prueba
        # distinga "mejoro la que eligio" de "mejoro la mas debil siempre".
        fuerzas = [sum(c.valores.values()) for c in campana.cartas_jugador(estado)]
        elegido = fuerzas.index(max(fuerzas))
        antes = dict(campana.cartas_jugador(estado)[elegido].valores)
        otros_antes = [sum(c.valores.values()) for i, c in
                       enumerate(campana.cartas_jugador(estado)) if i != elegido]

        titulo, texto = campana.aplicar_encuentro(estado, "mejorar", elegido)

        despues = campana.cartas_jugador(estado)
        nombre = despues[elegido].nombre
        self.assertIn(nombre, texto,
                      f"el jugador eligio {nombre} y el cartel habla de otra")
        self.assertEqual(sum(antes.values()) + 1, sum(despues[elegido].valores.values()),
                         "la carta elegida no subio exactamente un punto")
        otros_despues = [sum(c.valores.values()) for i, c in enumerate(despues)
                         if i != elegido]
        self.assertEqual(otros_antes, otros_despues,
                         "se mejoro una carta que el jugador no eligio")

    def test_ningun_texto_de_encuentro_usa_jargon(self):
        """G5 pidio quitar 'pool' y 'pity' de la jerga visible al jugador."""
        for encuentro in campana.ENCUENTROS:
            for opcion in encuentro["opciones"]:
                texto = opcion["texto"].lower()
                for palabra in ("pool", "pity", "prob", "rng"):
                    self.assertNotIn(
                        palabra, texto,
                        f"{encuentro['id']}/{opcion['id']}: jargon {palabra!r} "
                        f"en {opcion['texto']!r}")

    def test_debilitar_suma_y_se_guarda(self):
        r = self._aplicar("debilitar")
        self.assertEqual(1, r["estado"].get("debilitar"))
        self.assertEqual(1, campana.cargar().get("debilitar"))

    def test_sigilo_sube_el_lado_mas_bajo_y_es_de_campana(self):
        """El sigilo se anuncia "durante esta campana": no debe persistir."""
        random.seed(99)
        estado = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        antes = _fuerza(estado)
        perfil_antes = campana.coleccion_de()
        campana.aplicar_encuentro(estado, "sigilo")
        con_sigilo = _fuerza(estado)
        self.assertGreater(con_sigilo, antes, "el sigilo no subio nada")
        # Una campana nueva no hereda el sigilo anterior.
        self.assertEqual(perfil_antes, campana.coleccion_de())
        random.seed(99)
        estado2 = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        self.assertEqual(antes, _fuerza(estado2))


if __name__ == "__main__":
    unittest.main()
