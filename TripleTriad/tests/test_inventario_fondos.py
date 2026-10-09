"""Tests del inventario de fondos.

Existia un fondo para cada cosa que se ve y al reves: fondos generados que
nadie usaba (`salon` y `apagon` quedaron huerfanos una vez) y fondos en disco
que el codigo no encuentra nunca.

El inventario tiene que cubrir TODOS los caminos que piden un fondo. Cuando se
agrega uno nuevo y no se agrega aqui, el test se ciega y vuelve a pasar un
fondo por huerfano. Por eso se prueba en las dos direcciones.
"""

import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import campana  # noqa: E402
import cinematicas  # noqa: E402
import encuentros  # noqa: E402
import finales  # noqa: E402
import narrativa  # noqa: E402
import prologo  # noqa: E402
import ui  # noqa: E402

CARPETA = os.path.join(RAIZ, "assets", "fondos")


def _todos_los_fondos_del_juego():
    """Cada fondo que el codigo puede pedir, con el camino que lo pide.

    Si se agrega una pantalla nueva con un fondo propio, hay que sumar su
    funcion ACA. `test_todo_camino_esta_cubierto` lo reclama.
    """
    usados = {}

    def anota(fondo, donde):
        if not fondo:
            return
        usados.setdefault(fondo, set()).add(donde)

    # Nodos y encuentros de la campana
    for nid, nodo in campana.NODOS.items():
        anota(nodo.get("escena"), "nodo " + nid)
    for e in campana.ENCUENTROS:
        anota(e.get("escena", "campamento"), "encuentro " + e["id"])
    for vid in ("hostil", "nara"):
        extra = encuentros._datos_extra(vid)
        if extra:
            anota(extra.get("escena"), "encuentro " + vid)
    # Mini campanas (son `NODOS_MINI`; `MINI_FINALES` solo tiene titulo y lineas)
    for clave, nodo in campana.NODOS_MINI.items():
        anota(nodo.get("escena"), "mini " + clave)

    # Finales: capa comun por variante
    for variante in ("dominio", "equilibrio", "caos"):
        for e in finales.escenas_umbral(variante):
            anota(e["fondo"], "umbral " + variante)
        for e in finales.escenas_epilogo(variante):
            anota(e["fondo"], "epilogo " + variante)

    # Cinematica de intro
    escenas, _ = cinematicas.intro()
    for e in escenas:
        anota(e["fondo"], "intro")

    # Aperturas por faccion
    from facciones import orden_facciones
    for fac in orden_facciones():
        escenas, _ = cinematicas.apertura(fac)
        for e in escenas:
            anota(e["fondo"], "apertura " + fac)

    # Prologo
    for nombre in ("escenas_pre_duelo", "escenas_post_duelo",
                   "escenas_carta_umbral", "escenas_transporte",
                   "escenas_despertar", "escenas_encuentro_hostil",
                   "escenas_nara", "escenas_explicacion", "escenas_cierre"):
        for e in getattr(prologo, nombre)():
            anota(e["fondo"], "prologo")

    # Narrativa de nodo
    for nid in ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono"):
        for e in narrativa.previa_nodo(nid) + narrativa.posterior_nodo(nid):
            anota(e["fondo"], "narrativa " + nid)

    # El fondo por defecto de `esc()`: si nadie pasa fondo, sale este.
    anota(cinematicas.esc("x")["fondo"], "default de esc()")
    return usados


class TestInventarioDeFondos(unittest.TestCase):
    def setUp(self):
        self.usados = _todos_los_fondos_del_juego()
        self.en_disco = {n[:-4] for n in os.listdir(CARPETA) if n.endswith(".png")}
        self._suma_variantes()

    def _suma_variantes(self):
        """Las variantes de fondo TAMBIEN se usan, y por un camino propio.

        El codigo no las pide por su nombre: pide la escena y `ui.ruta_fondo`
        elige una variante con la semilla de la partida. Sin sumarlas aqui las
        24 variables salen huerfanas, y el test que de verdad importa
        (`test_ningun_fondo_queda_huerfano`) pasa a ser el que da falsos
        positivos por cada fondo nuevo que se genere.
        """
        for escena in list(self.usados):
            for variante in ui.variantes_de(escena):
                self.usados.setdefault(variante, set()).add("variante de " + escena)

    def test_todo_fondo_que_pide_el_codigo_existe(self):
        faltan = sorted(f for f in self.usados
                        if not os.path.exists(os.path.join(CARPETA, f + ".png")))
        self.assertEqual([], faltan,
                         "el codigo pide estos fondos y no estan: %s" % faltan)

    def test_ningun_fondo_queda_huerfano(self):
        """Un fondo generado que nadie pide es trabajo perdido y ademas
        esconde bugs de cableado, como paso con `salon` y `apagon`."""
        huerfanos = sorted(self.en_disco - set(self.usados))
        self.assertEqual([], huerfanos,
                         "Estos fondos estan en disco y ningun camino del "
                         "juego los pide: %s" % huerfanos)

    def test_los_dos_fondos_de_nuestro_mundo_se_usan(self):
        """`salon` (el torneo) y `apagon` (el corte) son de nuestro mundo.
        Es el bug que ya paso una vez."""
        for nombre in ("salon", "apagon"):
            self.assertIn(nombre, self.usados,
                          "%s dejo de usarse: el prologo debe Draw sobre el "
                          "fondo de SU mundo" % nombre)

    def test_los_fondos_tienen_el_tamano_que_espera_el_juego(self):
        from PIL import Image
        for nombre in sorted(self.usados):
            with Image.open(os.path.join(CARPETA, nombre + ".png")) as im:
                self.assertEqual((512, 256), im.size,
                                 "%s no es 512x256 y el motor lo escala mal"
                                 % nombre)

    def test_el_inventario_recorre_de_verdad_cada_camino(self):
        """Un inventario que no llega a un camino no ve sus problemas, que es
        como el rojo falso que dio el primer pase de la auditoria: `amanecer`,
        `ceniza` y `estandartes` parecian huerfanos porque el inventario no
        miraba ni la intro, ni las aperturas, ni el fondo por defecto."""
        for prefijo in ("intro", "apertura ", "prologo", "narrativa ",
                        "umbral dominio", "epilogo caos", "mini ",
                        "nodo ", "encuentro ", "default de esc()",
                        "variante de "):
            caminos = {d for ds in self.usados.values() for d in ds
                       if d.startswith(prefijo)}
            self.assertTrue(caminos,
                            "el inventario no recorrio el camino %r" % prefijo)
        # Y el total tiene que ser el de los fondos reales, ni uno mas ni menos
        self.assertEqual(len(self.en_disco), len(self.usados),
                         "el inventario ve %d fondos y hay %d en disco"
                         % (len(self.usados), len(self.en_disco)))


if __name__ == "__main__":
    unittest.main()