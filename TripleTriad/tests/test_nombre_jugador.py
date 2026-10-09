"""El nombre del jugador: que se guarde, que se sanee y que se vea.

Cubre las tres cosas que se pueden romper: la pantalla de entrada, el
saneado (un `<` rompe el renderizador y un salto de linea descuadra las cajas
de dialogo) y que el nombre se use de verdad en el juego.
"""

import os
import sys
import tempfile
import unittest

os.environ.setdefault(
    "TRIPLETRIAD_DATA", os.path.join(tempfile.gettempdir(), "tt_test_nombre")
)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

import campana  # noqa: E402
import cinematicas  # noqa: E402
import duelistas  # noqa: E402
import facciones  # noqa: E402
import finales  # noqa: E402

NODOS = ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono")
MOMENTOS = ("pre", "win", "lose")


def setUpModule():
    pygame.init()
    pygame.display.set_mode((1280, 800))


class TestSaneaNombre(unittest.TestCase):
    """Lo que el jugador teclea tiene que ser presentable o no se guarda."""

    def test_recorta_los_extremos(self):
        self.assertEqual(campana.sanea_nombre("  Juan  "), "Juan")

    def test_neutraliza_lo_que_rompe_el_render(self):
        """`<` y `>` abren etiquetas en el motor de texto."""
        for sucio in ("<b>", "a>b", "<script>alert(1)</script>"):
            limpio = campana.sanea_nombre(sucio)
            self.assertNotIn("<", limpio)
            self.assertNotIn(">", limpio)

    def test_los_saltos_de_linea_no_pasan(self):
        """Un \\n dentro del texto descuadra la caja de dialogo."""
        for sucio in ("a\nb", "a\rb", "a\tb", "a\n\nb"):
            limpio = campana.sanea_nombre(sucio)
            self.assertNotIn("\n", limpio)
            self.assertNotIn("\r", limpio)
            self.assertNotIn("\t", limpio)

    def test_colapsa_los_espacios(self):
        self.assertEqual(campana.sanea_nombre("  a    b  "), "a b")

    def test_recorta_al_tope(self):
        largo = "x" * 100
        self.assertEqual(len(campana.sanea_nombre(largo)), campana.NOMBRE_MAX)

    def test_sin_nombre_utilizable_devuelve_el_defecto(self):
        for vacio in ("", "   ", None, 123, [], "\t\n"):
            self.assertEqual(
                campana.sanea_nombre(vacio), campana.NOMBRE_POR_DEFECTO,
                f"{vacio!r} deberia dar el defecto")

    def test_el_tope_es_el_que_cabe_en_las_cajas(self):
        """15 caracteres: es el ancho de la caja de dialogo de cuatro lineas."""
        self.assertLessEqual(campana.NOMBRE_MAX, 15)


class TestPersistencia(unittest.TestCase):
    def test_el_nombre_sobrevive_al_perfil(self):
        campana.establecer_nombre("Bartolo")
        self.assertEqual(campana.nombre_jugador(), "Bartolo")

    def test_el_perfil_por_defecto_no_tiene_nombre(self):
        self.assertEqual(campana.perfil_por_defecto()["nombre_jugador"], "")

    def test_leer_sin_perfil_devuelve_el_defecto(self):
        """Un perfil sin la clave (viejo) no puede romper nada."""
        self.assertTrue(campana.nombre_jugador())
        campana.establecer_nombre("")
        self.assertEqual(campana.nombre_jugador(), campana.NOMBRE_POR_DEFECTO)

    def test_tiene_nombre_distingue_lo_propio_del_defecto(self):
        self.assertFalse(campana.tiene_nombre())
        campana.establecer_nombre("Bartolo")
        self.assertTrue(campana.tiene_nombre())

    def test_el_valor_inicial_no_precarga_el_defecto(self):
        """`nombre_guardado` es lo que va al campo, no `nombre_jugador`.

        Si el campo se precargara con "el duelista", con solo pulsar ENTER se
        guardaria como nombre propio y `tiene_nombre()` pasaria a True sin que
        nadie escribiera nada.
        """
        campana.establecer_nombre("")
        self.assertEqual(campana.nombre_guardado(), "",
                         "sin nombre propio el campo debe salir vacio")
        self.assertEqual(campana.nombre_jugador(), campana.NOMBRE_POR_DEFECTO,
                         "pero el nombre que se muestra y se usa si es el defecto")
        campana.establecer_nombre("Bartolo")
        self.assertEqual(campana.nombre_guardado(), "Bartolo")

    def test_sin_nombre_no_se_confunde_con_el_defecto_al_guardar(self):
        """El ciclo completo: vacio -> no tiene nombre -> sigue vacio."""
        campana.establecer_nombre("")
        campana.invalidar_nombre()
        self.assertFalse(campana.tiene_nombre())
        self.assertEqual(campana.nombre_guardado(), "")


class TestElNombreSeUsa(unittest.TestCase):
    def test_los_rivales_se_dirigen_al_jugador_por_su_nombre(self):
        for nodo in NODOS:
            lineas = duelistas.dialogo_de(nodo, "pre", "Kor", "Bartolo")
            self.assertTrue(
                any("Bartolo" in (e.get("texto") or "") for e in lineas),
                f"{nodo}: el rival nunca habla al jugador por su nombre")

    def test_sin_nombre_se_sigue_diciendo_el_duelista(self):
        for nodo in NODOS:
            lineas = duelistas.dialogo_de(nodo, "pre", "Kor", "")
            self.assertTrue(
                any("duelista" in (e.get("texto") or "").lower() for e in lineas),
                f"{nodo}: sin nombre deberia salir 'el duelista'")

    def test_no_queda_ningun_marcador_en_el_juego(self):
        for nodo in NODOS:
            for momento in MOMENTOS:
                for e in duelistas.dialogo_de(nodo, momento, "Kor", "Bartolo"):
                    for campo in ("texto", "hablante"):
                        v = e.get(campo)
                        if isinstance(v, str):
                            self.assertNotIn("__", v,
                                             f"{nodo}/{momento}/{campo}: {v}")

    def test_el_nombre_mas_largo_cabe_en_la_caja_de_dialogo(self):
        """El caso peor: 15 chars dentro de una linea de 4.

        Se mide de verdad con la fuente del juego, no con una cuenta.
        """
        import ui

        largo = "A" * campana.NOMBRE_MAX
        self.assertEqual(len(campana.sanea_nombre(largo)), campana.NOMBRE_MAX)
        ancho_max = 900  # ancho util de la caja de dialogo
        for nodo in NODOS:
            for momento in MOMENTOS:
                for e in duelistas.dialogo_de(nodo, momento, "Kor", largo):
                    texto = e.get("texto") or ""
                    if largo not in texto:
                        continue
                    # Se mide la linea mas larga despues de partir por palabras.
                    for linea in ui.envolver(texto, 12, ancho_max):
                        self.assertLessEqual(
                            ui.ancho_texto(linea, 12), ancho_max + 40,
                            f"{nodo}/{momento}: la linea no cabe: {linea!r}")

    def test_el_hud_toma_el_nombre_del_info(self):
        """`info_duelo` lleva el nombre para que el HUD lo pinte."""
        campana.establecer_nombre("Bartolo")
        estado = {"faccion": "humano", "nodo": "senda", "ruta": []}
        info = campana.info_duelo(estado)
        self.assertEqual(info["nombre_jugador"], "Bartolo")
        self.assertIn("Bartolo", str(info["dialogo_pre"]))

    def test_el_nombre_no_se_relee_de_disco_por_frame(self):
        """`info_duelo` se llama POR FRAME (elegir_rama dibuja las dos ramas).

        Leer `perfil.json` ahi costaba 0,65 ms por llamada, o sea 1,3 ms por
        frame: el 8% del presupuesto de 16,67 ms para una cadena que cambia una
        vez por partida. Se cachea; este test falla si alguien quita la cache.
        """
        campana.establecer_nombre("Bartolo")
        estado = {"faccion": "humano", "nodo": "senda", "ruta": []}
        campana.info_duelo(estado)  # calentia la cache

        # Se cuenta el numero de lecturas reales del perfil.
        import campana as _c
        original = _c.ruta_perfil
        lecturas = []
        _c.ruta_perfil = lambda: (lecturas.append(1), original())[1]
        try:
            for _ in range(20):
                campana.info_duelo(estado)
        finally:
            _c.ruta_perfil = original

        self.assertEqual(
            len(lecturas), 0,
            f"info_duelo leyio el perfil {len(lecturas)} veces en 20 llamadas")

    def test_la_cache_se_refresca_al_cambiar_el_nombre(self):
        campana.establecer_nombre("Bartolo")
        self.assertEqual(campana.nombre_jugador(), "Bartolo")
        campana.establecer_nombre("Gralixa")
        self.assertEqual(campana.nombre_jugador(), "Gralixa")
        campana.establecer_nombre("")
        self.assertEqual(campana.nombre_jugador(), campana.NOMBRE_POR_DEFECTO)

    def test_invalidate_deja_releer(self):
        campana.establecer_nombre("Bartolo")
        campana.invalidar_nombre()
        campana.guardar_perfil(dict(campana.cargar_perfil(),
                                    nombre_jugador="Otro"))
        self.assertEqual(campana.nombre_jugador(), "Otro")


class TestElMarcadorSeResuelveEnTodoElGuion(unittest.TestCase):
    """El bug de `__NOMBRE__` se repitio con `__JUGADOR__`.

    Aquella vez el marcador vivia en `hablante` y el test solo miraba `texto`,
    asi que salia literal en pantalla y la suite daba verde. Aqui se recorre
    TODO el guion del juego, no solo los duelistas.
    """

    def _todo_el_guion(self):
        """Generador de (etiqueta, escenas) de todo el guion."""
        import finales
        import fragmentos
        import narrativa
        import prologo

        for nombre in ("escenas_pre_duelo", "escenas_post_duelo",
                       "escenas_carta_umbral", "escenas_transporte",
                       "escenas_despertar", "escenas_encuentro_hostil",
                       "escenas_nara", "escenas_explicacion", "escenas_cierre"):
            yield ("prologo." + nombre, getattr(prologo, nombre)())

        yield ("finales.UMBRAL", finales.UMBRAL)
        yield ("finales.EPILOGO", finales.EPILOGO)

        for nodo in ("senda", "aldea", "ruinas", "fortaleza", "asalto", "trono"):
            yield ("narrativa.posterior_nodo:" + nodo,
                   narrativa.posterior_nodo(nodo))
            yield ("narrativa.previa_nodo:" + nodo,
                   narrativa.previa_nodo(nodo))

        yield ("narrativa.escena_amistad", narrativa.escena_amistad())

        for faccion in facciones.orden_facciones():
            for momento in ("victoria", "derrota"):
                for linea in narrativa.nara_linea(momento, 2):
                    yield (f"narrativa.nara_linea:{faccion}:{momento}", [linea])
            for linea in narrativa.reaccion_mazo(faccion) or []:
                yield ("narrativa.reaccion_mazo:" + faccion, [linea])
            for linea in narrativa.segunda_reaccion_mazo(faccion) or []:
                yield ("narrativa.2a_reaccion_mazo:" + faccion, [linea])

        for i in fragmentos.ids_fragmentos():
            yield (f"fragmentos.{i}", fragmentos.escena_desbloqueo(i))

    def _resolver(self, dato, nombre):
        """Construye la cinematica pasando por el aplanador, que acepta
        cualquier forma de guion (listas, dicts anidados, cadenas sueltas)."""
        if not isinstance(dato, (list, tuple)):
            raise AssertionError(f"el guion no es una secuencia: {type(dato)}")
        escenas = []
        for linea in dato:
            if isinstance(linea, str):
                lineas = linea.split("\n")
            else:
                lineas = [linea]
            for l in lineas:
                if isinstance(l, str):
                    escenas.append(cinematicas.esc(l))
                else:
                    escenas.append(dict(l))
        return cinematicas.Cinematica(escenas, nombre_jugador=nombre).escenas

    def _resolver_guion(self, guion, nombre):
        """Como `_resolver` pero baja por `_lineas` primero."""
        return self._resolver(self._lineas(guion), nombre)

    def _lineas(self, dato):
        """Aplana cualquier forma de guion a lista de dicts con texto/hablante.

        Los guiones vienen en tres formas distintas y ninguna es la misma:
        listas de escenas (dict con clave "texto"), listas de cadenas sueltas
        (`finales.UMBRAL["lineas"]`) y dicts anidados de varias claves. Un
        dict con "texto" ES una escena, no un contenedor: hay que mirar eso
        ANTES de tratar sus valores como subguion, o se comia el texto.
        """
        salida = []
        if isinstance(dato, str):
            for parte in dato.split("\n"):
                if parte:
                    salida.append({"texto": parte, "hablante": None})
        elif isinstance(dato, dict):
            if "texto" in dato:
                salida.append({"texto": dato.get("texto"),
                               "hablante": dato.get("hablante")})
            else:
                for valor in dato.values():
                    salida.extend(self._lineas(valor))
        elif isinstance(dato, (list, tuple)):
            for valor in dato:
                salida.extend(self._lineas(valor))
        else:
            texto = getattr(dato, "texto", None)
            if texto is not None:
                salida.append({"texto": texto,
                               "hablante": getattr(dato, "hablante", None)})
        return salida

    def test_no_queda_ningun_marcador_en_todo_el_guion(self):
        """Se mide lo que SE PINTA, o sea despues de pasar por `Cinematica`.

        El guion de modulo guarda el marcador a proposito; lo que no puede
        pasar es que llegue crudo a la caja de dialogo. Por eso el recorrido es
        guion -> `Cinematica` -> escenas finales, no guion a pelo.
        """
        campana.establecer_nombre("Bartolo")
        revisadas = 0
        for etiqueta, guion in self._todo_el_guion():
            for e in self._resolver_guion(guion, "Bartolo"):
                for campo in ("texto", "hablante"):
                    valor = getattr(e, campo, None)
                    if isinstance(valor, str) and "__" in valor:
                        self.fail(f"{etiqueta}/{campo}: {valor!r} sin resolver")
                revisadas += 1
        self.assertGreater(revisadas, 200,
                           f"solo se revisaron {revisadas} lineas: falta guion")

    def test_el_guion_de_modulo_conserva_el_marcador(self):
        """La otra mitad: el marcador debe estar en el guion, no cocido.

        Si alguien sustituye el nombre a mano en `prologo.py` o `finales.py`,
        este test falla: asi el nombre sigue siendo configurable.
        """
        import prologo as _p
        marcado = any("__JUGADOR__" in e.get("texto", "")
                      for e in _p.escenas_post_duelo())
        self.assertTrue(marcado,
                        "el prologo deberia conservar __JUGADOR__ sin resolver")

    def test_todo_el_guion_se_resuelve_tambien_sin_nombre(self):
        campana.establecer_nombre("")
        for etiqueta, guion in self._todo_el_guion():
            escenas = self._resolver_guion(guion, "")
            for e in escenas:
                for campo in ("texto", "hablante"):
                    valor = getattr(e, campo, None)
                    if isinstance(valor, str):
                        self.assertNotIn("__", valor,
                                         f"{etiqueta}/{campo}: {valor!r}")

    def test_el_nombre_aparece_en_el_guion_final(self):
        """No basta con que se sustituya: el nombre tiene que usarse."""
        campana.establecer_nombre("Bartolo")
        escenas = self._resolver(finales.EPILOGO["dominio"]["lineas"], "Bartolo")
        self.assertTrue(escenas)
        textos = " ".join(e.texto for e in escenas)
        self.assertIn("Bartolo", textos,
                      "el epilogo deberia dirigirse al jugador por su nombre")

    def test_la_cinematica_no_toca_el_guion_original(self):
        """Resolver no puede mutar las listas de modulo: se play dos veces."""
        import finales as _f
        original = list(_f.EPILOGO["caos"]["lineas"])
        self._resolver(_f.EPILOGO["caos"]["lineas"], "Bartolo")
        self.assertEqual(_f.EPILOGO["caos"]["lineas"], original,
                         "resolver el marcador ha mutado el guion de modulo")


if __name__ == "__main__":
    unittest.main()