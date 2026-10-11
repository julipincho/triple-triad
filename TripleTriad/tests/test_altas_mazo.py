"""G4: las altas automaticas (draft, sobre, encuentro) respetan las mismas
reglas del mazo que el editor.

Antes estas rutas escribian en `estado["cartas"]` sin mirar nada, y se
llegaba a mazos que el editor rechazaba: la misma carta dos veces, mas de una
legendaria o mas de 10 cartas. La carta NUNCA se pierde (siempre va a la
coleccion); lo que se controla es si entra al mazo.
"""

import os
import random
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import campana  # noqa: E402
from reglas import Carta, rareza, total_carta  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(prefix="tt_altas_")
        self.addCleanup(self.d.cleanup)
        os.environ["TRIPLETRIAD_DATA"] = self.d.name
        self.estado = campana.nueva_campana("humano")
        campana.asegurar_coleccion("humano")
        campana.guardar(self.estado)

    def validar(self):
        return campana.validar_mazo(self.estado["cartas"], campana.coleccion_de())

    def nombres(self):
        return [d["nombre"] for d in self.estado["cartas"]]

    def mailedo(self, cartas):
        """Instala un mazo concreto, regalando antes las cartas."""
        for c in cartas:
            campana.otorgar_base(c.nombre, c.a_dict())
        self.estado["cartas"] = [c.a_dict() for c in cartas]
        campana.guardar(self.estado)

    def comunes(self, n=10):
        import mazos

        return [c for c in mazos.TODOS["humano"] if rareza(c)[0] == "COMUN"][:n]

    def legendaria(self):
        import mazos

        return next(c for c in mazos.TODOS["humano"]
                    if rareza(c)[0] == "LEGENDARIA")


class TestMazoAdmite(Base):
    def test_rechaza_una_carta_que_ya_esta(self):
        repetida = Carta.desde_dict(self.estado["cartas"][0])
        cabe, motivo = campana.mazo_admite(self.estado, repetida)
        self.assertFalse(cabe)
        self.assertIn("ya esta", motivo)

    def test_admite_una_carta_nueva(self):
        nueva = self.comunes(12)[-1]
        otras = [c for c in self.comunes(12) if c.nombre != nueva.nombre]
        self.mailedo(otras[:9])
        campana.otorgar_base(nueva.nombre, nueva.a_dict())
        cabe, motivo = campana.mazo_admite(self.estado, nueva)
        self.assertTrue(cabe, motivo)

    def test_rechaza_una_segunda_legendaria(self):
        import mazos

        leg = self.legendaria()
        otras = [c for c in mazos.TODOS["humano"] if rareza(c)[0] == "COMUN"][:9]
        self.mailedo([leg] + otras)
        otra_leg = next(c for cs in mazos.TODOS.values() for c in cs
                        if rareza(c)[0] == "LEGENDARIA" and c.nombre != leg.nombre)
        campana.otorgar_base(otra_leg.nombre, otra_leg.a_dict())
        # Sustituyendo una COMUN: quedarian 2 legendarias.
        cabe, motivo = campana.mazo_admite(self.estado, otra_leg, reemplazo=1)
        self.assertFalse(cabe)
        self.assertIn("legendaria", motivo)

    def test_rechaza_mas_de_tres_raras(self):
        import mazos

        raras = [c for c in mazos.TODOS["humano"] if rareza(c)[0] == "RARA"][:4]
        if len(raras) < 4:
            self.skipTest("no hay 4 raras humanas")
        comunes = self.comunes(6)
        self.mailedo(raras[:3] + comunes)
        extra = next(c for cs in mazos.TODOS.values() for c in cs
                     if rareza(c)[0] == "RARA" and c.nombre not in {r.nombre for r in raras})
        campana.otorgar_base(extra.nombre, extra.a_dict())
        # Sustituye una COMUN: quedarían 4 raras.
        cabe, motivo = campana.mazo_admite(self.estado, extra,
                                          reemplazo=len(raras))
        self.assertFalse(cabe)
        self.assertIn("raras", motivo)

    def test_sustituir_una_carta_por_si_misma_no_es_duplicado(self):
        """`reemplazo` deja de contar, asi que no puede dar un falso positivo."""
        repetida = Carta.desde_dict(self.estado["cartas"][0])
        cabe, motivo = campana.mazo_admite(self.estado, repetida, reemplazo=0)
        self.assertTrue(cabe, motivo)


class TestAltasReales(Base):
    def test_el_draft_no_ofrece_cartas_del_mazo(self):
        en_mazo = set(self.nombres())
        for _ in range(120):
            ofertas = campana.draft_aleatorio(self.estado, 3)
            for o in ofertas:
                self.assertNotIn(o.nombre, en_mazo,
                                 "el draft ofrecio una carta ya equipada")

    def test_el_draft_no_ofrece_una_legendaria_que_no_cabe(self):
        """Con la legendaria ya puesta, otra no puede entrar: no se ofrece."""
        leg = self.legendaria()
        self.mailedo([leg] + self.comunes(9))
        for _ in range(120):
            for o in campana.draft_aleatorio(self.estado, 3):
                self.assertNotEqual(rareza(o)[0], "LEGENDARIA",
                                    "ofrecio una legendaria con el tope cubierto")

    def test_toda_oferta_del_draft_puede_entrar_en_el_mazo(self):
        """La garantia de fondo: elegir una oferta nunca es una eleccion wasted."""
        import mazos

        pool = [c for cs in mazos.TODOS.values() for c in cs]
        leg = self.legendaria()
        for _ in range(60):
            cartas = self.comunes(10)
            cartas.sort(key=total_carta)
            self.mailedo(([leg] if _ % 2 else []) + cartas[:5])
            for o in campana.draft_aleatorio(self.estado, 3):
                campana.otorgar_base(o.nombre, o.a_dict())
                idx = random.randrange(0, len(self.estado["cartas"]))
                cabe, motivo = campana.mazo_admite(self.estado, o, reemplazo=idx)
                self.assertTrue(cabe, f"draft ofrecio {o.nombre} y no cabe: {motivo}")

    def test_recluta_no_deja_duplicados(self):
        repetida = Carta.desde_dict(self.estado["cartas"][0])
        campana.draft_reemplazo(self.estado, repetida.copia(), 5)
        nombres = self.nombres()
        self.assertEqual(len(nombres), len(set(nombres)),
                         "la recluta duplico una carta")
        ok, motivo = self.validar()
        self.assertTrue(ok, motivo)

    def test_robo_no_deja_duplicados(self):
        repetida = Carta.desde_dict(self.estado["cartas"][0])
        campana.anadir_carta(self.estado, repetida.copia())
        nombres = self.nombres()
        self.assertEqual(len(nombres), len(set(nombres)))
        ok, motivo = self.validar()
        self.assertTrue(ok, motivo)

    def test_la_carta_siempre_llega_a_la_coleccion(self):
        """Aunque no entre al mazo, la carta es del jugador: no se pierde."""
        repetida = Carta.desde_dict(self.estado["cartas"][0])
        campana.anadir_carta(self.estado, repetida.copia())
        self.assertIn(repetida.nombre, campana.coleccion_de())

    def test_sobre_con_mazo_reducido_no_rompe_las_reglas(self):
        import mazos

        comunes = self.comunes(6)
        self.mailedo(comunes)
        for _ in range(8):
            campana.abrir_sobre(self.estado, cantidad=3)
        ok, motivo = self.validar()
        self.assertTrue(ok, motivo)
        self.assertLessEqual(len(self.estado["cartas"]), campana.MAZO_RUN_N)

    def test_muchos_sobres_mantienen_el_mazo_valido(self):
        """Estres: 15 sobres seguidos sobre un mazo reducido."""
        comunes = self.comunes(5)
        self.mailedo(comunes)
        for _ in range(15):
            campana.abrir_sobre(self.estado, cantidad=3)
        ok, motivo = self.validar()
        self.assertTrue(ok, motivo)

    def test_sobre_no_mete_la_leyenda_una_vez_detenida(self):
        """Con una legendaria dentro, otra no puede entrar por la puerta de atrás."""
        leg = self.legendaria()
        comunes = self.comunes(9)
        self.mailedo([leg] + comunes)
        for _ in range(12):
            campana.abrir_sobre(self.estado, cantidad=3)
        r = [rareza(Carta.desde_dict(d))[0] for d in self.estado["cartas"]]
        self.assertLessEqual(r.count("LEGENDARIA"), campana.LIMITE_LEGENDARIAS)
        ok, motivo = self.validar()
        self.assertTrue(ok, motivo)

    def test_la_carta_del_sobre_todavia_se_guarda_en_la_coleccion(self):
        comunes = self.comunes(5)
        self.mailedo(comunes)
        antes = set(campana.coleccion_de())
        nuevas, _ = campana.abrir_sobre(self.estado, cantidad=3)
        despues = set(campana.coleccion_de())
        for nombre in nuevas:
            self.assertIn(nombre, despues)
        self.assertTrue(despues >= antes)


class TestElReciboDiceLaVerdad(Base):
    """G6: ninguna promesa mecanica sin efecto.

    El recibo de "recluta" decia "X entra en el mazo" sin comprobarlo. Con las
    altas condicionadas a las reglas del mazo, ese texto puede ser falso, y un
    texto falso es peor que un texto clumsy.
    """

    def _recluta(self, carta, idx):
        return campana.entregar_recompensa(self.estado, "recluta", "senda",
                                          idx=idx, carta=carta)

    def test_si_entra_anuncia_que_entra(self):
        en_mazo = set(self.nombres())
        nueva = next(c for c in self.comunes(20) if c.nombre not in en_mazo)
        campana.otorgar_base(nueva.nombre, nueva.a_dict())
        recibo = self._recluta(nueva, 5)
        self.assertIn("entra en el mazo", recibo["mensaje"])
        self.assertIn(nueva.nombre, recibo["mensaje"])

    def test_si_no_entra_lo_dice_y_explica_por_que(self):
        repetida = Carta.desde_dict(self.estado["cartas"][0])
        recibo = self._recluta(repetida, 5)
        mensaje = recibo["mensaje"]
        self.assertNotIn("entra en el mazo", mensaje,
                         "el recibo promete que entra cuando no entra")
        self.assertIn("coleccion", mensaje)
        # Y el motivo es concreto, no un "no se pudo".
        self.assertTrue(len(mensaje.split(":")) > 1, mensaje)

    def test_el_recibo_es_idempotente(self):
        repetida = Carta.desde_dict(self.estado["cartas"][0])
        self._recluta(repetida, 5)
        otra = self._recluta(repetida, 5)
        # La segunda entrega devuelve el recibo guardado, sin volver a aplicar.
        self.assertEqual(otra["mensaje"], self._recluta(repetida, 5)["mensaje"])


class TestCoherenciaEditorAlta(Base):
    def test_todo_lo_que_acepta_el_alta_lo_acepta_el_editor(self):
        """Lo invertido: si `mazo_admite` dice que si, validar_mazo tambien."""
        import mazos

        pool = [c for cs in mazos.TODOS.values() for c in cs]
        for _ in range(400):
            cartas = self.comunes(10)
            cartas.sort(key=total_carta)
            self.mailedo(cartas[:5])
            cand = random.choice(pool)
            # El flujo real (`anadir_carta` / `draft_reemplazo`) concede la carta
            # a la coleccion ANTES de decidir si entra al mazo. Sin esto la
            # comparacion mediria el orden de las llamadas, no la politica.
            campana.otorgar_base(cand.nombre, cand.a_dict())
            idx = random.randrange(0, 5)
            cabe, _ = campana.mazo_admite(self.estado, cand, reemplazo=idx)
            if cabe:
                nuevo = list(self.estado["cartas"])
                nuevo[idx] = cand.a_dict()
                ok, motivo = campana.validar_mazo(nuevo, campana.coleccion_de())
                self.assertTrue(
                    ok,
                    f"mazo_admite dijo que si pero validar_mazo no: {motivo}")


if __name__ == "__main__":
    unittest.main()