"""Tests del bonificador de cartas: si sube, se ve subido.

El bug: `cartas_jugador` devolvia los valores de fabrica mientras `cartas_duelo`
aplicaba encima las mejoras de la campana. El resultado era que una carta
mejorada valia 5 en el duelo y seguia enseñando 4 en todas las pantallas, y que
el mensaje de recompensa decia "sube su O a 4" justo despues de gastar la
recompensa. El jugador no tenia forma de ver que habia pasado nada.
"""

import os
import sys
import tempfile
import unittest

# No escribir en los datos reales del jugador
os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tripletriad_tests")
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import campana  # noqa: E402


def _estado():
    return campana.nueva_campana("humano")


class TestMejorasSeVen(unittest.TestCase):
    def setUp(self):
        self.estado = _estado()
        self.idx = 0
        self.datos = self.estado["cartas"][self.idx]
        self.nombre = self.datos["nombre"]

    def test_sin_mejoras_nada_cambia(self):
        for carta in campana.cartas_jugador(self.estado):
            base = next(d for d in self.estado["cartas"] if d["nombre"] == carta.nombre)
            self.assertEqual(carta.valores,
                             {"N": base["n"], "S": base["s"],
                              "E": base["e"], "O": base["o"]})

    def test_la_mejora_cambia_el_numero_que_se_ensena(self):
        campana.mejorar_carta(self.estado, self.idx, lado="n")
        carta = next(c for c in campana.cartas_jugador(self.estado)
                     if c.nombre == self.nombre)
        self.assertEqual(self.datos["n"] + 1, carta.valores["N"])

    def test_varias_mejoras_se_acumulan(self):
        for _ in range(3):
            campana.mejorar_carta(self.estado, self.idx, lado="n")
        carta = next(c for c in campana.cartas_jugador(self.estado)
                     if c.nombre == self.nombre)
        self.assertEqual(min(10, self.datos["n"] + 3), carta.valores["N"])

    def test_la_carta_del_menu_es_la_misma_que_la_del_duelo(self):
        """El fallo de raiz: dos funciones, dos cartas distintas con el mismo
        nombre. Es lo que hacia que la mejora pareciese no existir."""
        campana.mejorar_carta(self.estado, self.idx, lado="s")
        campana.mejorar_carta(self.estado, self.idx, lado="o")
        menu = next(c for c in campana.cartas_jugador(self.estado)
                    if c.nombre == self.nombre)
        # El duelo sortea 5 de las 10, asi que se juega con lo que salio y se
        # exige que, si salio la carta, coincida con la del menu.
        for carta in campana.cartas_duelo(self.estado, "aldea"):
            if carta.nombre == self.nombre:
                self.assertEqual(menu.valores, carta.valores)
        # Y el tope es 10, no 12
        self.assertLessEqual(max(menu.valores.values()), 10)

    def test_cartas_duelo_no_aplica_las_mejoras_dos_veces(self):
        """`cartas_duelo` se apoya en `cartas_jugador`, que ya las aplica. Si
        esta funcion las sumara otra vez, +1 valdria +2 en el duelo."""
        campana.mejorar_carta(self.estado, self.idx, lado="n")
        esperado = next(c for c in campana.cartas_jugador(self.estado)
                        if c.nombre == self.nombre).valores["N"]
        en_duelo = campana.cartas_duelo(self.estado, "aldea")
        carta = next((c for c in en_duelo if c.nombre == self.nombre), None)
        if carta is not None:
            self.assertEqual(esperado, carta.valores["N"])

    def test_cartas_base_sigue_dando_el_valor_de_fabrica(self):
        campana.mejorar_carta(self.estado, self.idx, lado="n")
        base = next(c for c in campana.cartas_base(self.estado)
                    if c.nombre == self.nombre)
        self.assertEqual(self.datos["n"], base.valores["N"])


class TestMensajeDeRecompensa(unittest.TestCase):
    def test_valor_actual_dice_la_cifra_final(self):
        estado = _estado()
        datos = estado["cartas"][0]
        campana.mejorar_carta(estado, 0, lado="n")
        self.assertEqual(datos["n"] + 1,
                         campana.valor_actual(estado, datos, "n"))
        # La ficha sigue dando el base, y por eso hay dos funciones
        self.assertEqual(datos["n"], campana.valor_con_mejoras(
            datos, {})["n"])

    def test_valor_actual_respeta_el_tope(self):
        estado = _estado()
        datos = {"nombre": "X", "n": 10, "s": 5, "e": 5, "o": 5}
        campana.registrar_mejora(estado, "X", "n", puntos=5)
        self.assertEqual(10, campana.valor_actual(estado, datos, "n"))

    def test_una_mejora_no_se_suma_dos_veces_en_el_valor(self):
        estado = _estado()
        datos = estado["cartas"][0]
        campana.mejorar_carta(estado, 0, lado="n")
        campana.mejorar_carta(estado, 0, lado="n")
        # dos mejoras = +2 exactos, ni +1 ni +3
        self.assertEqual(datos["n"] + 2,
                         campana.valor_actual(estado, datos, "n"))


class TestSigiloSeAplicaATodas(unittest.TestCase):
    def test_el_sigilo_sube_el_lado_mas_bajo_de_cada_carta(self):
        estado = _estado()
        campana.aplicar_sigilo(estado)
        deltas = campana.mejoras_de(estado)
        for d in estado["cartas"]:
            self.assertIn(d["nombre"], deltas,
                          "%s se quedo sin sigilo" % d["nombre"])

    def test_despues_del_sigilo_el_mazo_muestra_los_valores_nuevos(self):
        """El sigilo dice 'suben su lado mas bajo'. Si el mazo sigue mostrando
        los de antes, el jugador no ve que ha pasado nada."""
        estado = _estado()
        antes = {c.nombre: c.valores["N"] for c in campana.cartas_jugador(estado)}
        campana.aplicar_sigilo(estado)
        despues = campana.cartas_jugador(estado)
        subidas = 0
        for c in despues:
            if c.nombre in antes and c.valores["N"] > antes[c.nombre]:
                subidas += 1
        self.assertGreater(subidas, 0,
                           "el sigilo no cambio ningun numero visible")

    def test_las_mejoras_no_tocan_la_coleccion_permanente(self):
        """Las mejoras son de la campana en curso. Si se colaran en el perfil,
        al empezar otra campana habria cartas infladas para siempre."""
        estado = _estado()
        antes = {d["nombre"]: {k: d[k] for k in "nseo"}
                 for d in estado["cartas"]}
        campana.aplicar_sigilo(estado)
        campana.mejorar_carta(estado, 0)
        # `estado["cartas"]` guarda la ficha de fabrica: si el bonus se escribiera
        # ahi, las mejoras se sumarian una y otra vez en cada combate.
        despues = {d["nombre"]: {k: d[k] for k in "nseo"}
                   for d in estado["cartas"]}
        self.assertEqual(antes, despues)
        # Y el perfil no se ha tocado.
        perfil = campana.cargar_perfil()
        for nombre, valores in antes.items():
            if nombre in perfil.get("coleccion", {}):
                self.assertEqual(
                    {k: perfil["coleccion"][nombre][k] for k in "nseo"}, valores)


if __name__ == "__main__":
    unittest.main()
