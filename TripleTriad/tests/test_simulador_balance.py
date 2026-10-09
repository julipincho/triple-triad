"""El simulador de balance no puede perder trabajo ni mentir por encima de su ruido.

Dos garantias, las dos aprendidas a la mala:

1. Regenerar el informe NO puede borrar las conclusiones. Viven en el codigo
   (`_CONCLUSIONES_POR_DEFECTO`) y se vuelven a escribir al final.
2. Con pocas muestras el informe NO puede pisar el bueno. Con 60 trials el
   margen es de ~8 puntos y salen cinco cruces "injustos" que con 400 no
   existen: es ruido, y escribirlo como si fuera un hallazgo es peor que no
   escribir nada.
"""

import os
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tests"))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import duelos_simulador as ds  # noqa: E402


def setUpModule():
    pygame.init()
    pygame.display.set_mode((1280, 800))


class TestUmbralDePublicabilidad(unittest.TestCase):
    def test_el_minimo_esta_por_encima_del_punto_de_ruido(self):
        """Con 60 trials el margen es ~10 puntos y salen cruces falsos.

        Por debajo de 200 casi cualquier diferencia se marca, que es justo lo
        contrario de lo que sirve para decidir un reequilibrio.
        """
        self.assertGreaterEqual(ds.MIN_TRIALS_PUBLIQUABLE, 200)

    def test_el_error_baja_con_las_muestras(self):
        """La razon de ser del umbral: el margen tiene que encogerse.

        Cada trial juega DOS partidas, asi que 400 trials son 800 muestras.
        """
        pocos = ds.error_binomial(60, 60)     # 120 muestras
        muchos = ds.error_binomial(400, 400)  # 800 muestras
        self.assertGreater(pocos, 8.0)
        self.assertLess(muchos, 5.0)
        self.assertGreater(pocos, muchos)


class TestElInformeSeConserva(unittest.TestCase):
    """Se prueba `escribir_informe` directamente, no `main`.

    `main` simula 36.000 duelos y tarda minutos; aqui lo que importa es la
    MECANICA del fichero, que se puede comprobar en milisegundos.
    """

    def _escribir(self, nombre, trials):
        ruta = os.path.join(tempfile.gettempdir(), nombre)
        self.addCleanup(self._borrar, ruta, trials)
        real = ds.escribir_informe(ruta, ["DATOS DE PRUEBA"], trials)
        return ruta, real

    @staticmethod
    def _borrar(ruta, trials):
        for nombre in (ruta, f"{ruta}.muestrecha-{trials}.md"):
            try:
                os.remove(nombre)
            except OSError:
                pass

    @staticmethod
    def _leer(ruta):
        with open(ruta, encoding="utf-8") as fh:
            return fh.read()

    def test_nada_se_escribe_en_el_repo(self):
        ruta, real = self._escribir("ds_test_raiz.md", 400)
        self.assertEqual(real, ruta)
        self.assertTrue(os.path.exists(ruta))
        self.assertFalse(
            os.path.exists(os.path.join(RAIZ, "ds_test_raiz.md")),
            "el simulador ha escrito en la raiz del repo en vez del temporal")

    def test_con_few_muestras_no_toca_el_informe_bueno(self):
        _, real_bueno = self._escribir("ds_bueno.md", 400)
        antes = self._leer(real_bueno)

        _, real_pobre = self._escribir("ds_poca.md", 30)
        self.assertNotEqual(real_bueno, real_pobre,
                            "la muestra pobre debe escribir aparte")
        self.assertIn("muestrecha", real_pobre.lower(),
                      "el nombre del fichero debe avisar de la muestra pobre")
        self.assertIn("MUESTRECHA", self._leer(real_pobre))
        # Y el bueno sigue intacto, byte a byte.
        self.assertEqual(antes, self._leer(real_bueno))

    def test_el_fichero_muestrecha_lo_avisa_en_cabecera(self):
        _, real = self._escribir("ds_aviso.md", 30)
        cabecera = self._leer(real)[:600]
        self.assertIn("MUESTRECHA", cabecera)
        self.assertIn(str(ds.MIN_TRIALS_PUBLIQUABLE), cabecera)

    def test_las_conclusiones_se_conservan_al_regenerar(self):
        ruta, real = self._escribir("ds_conclu.md", 400)
        c1 = self._leer(real)
        self.assertIn("## Conclusiones", c1)
        self.assertIn("DATOS DE PRUEBA", c1)

        # Relanzar con OTROS datos debe conservar las conclusiones y cambiar
        # solo el bloque de numeros. Si vivieran solo en el fichero, la segunda
        # pasada las borraria.
        ds.escribir_informe(ruta, ["DATOS NUEVOS"], 400)
        c2 = self._leer(ruta)
        self.assertIn("DATOS NUEVOS", c2)
        self.assertNotIn("DATOS DE PRUEBA", c2)
        self.assertIn("## Conclusiones", c2)
        self.assertEqual(c1.count("## Conclusiones"), 1)
        self.assertEqual(c2.count("## Conclusiones"), 1)

    def test_una_conclusion_editada_a_mano_manda_sobre_la_del_codigo(self):
        """Lo escrito a mano se respeta: el codigo no pisa el analisis."""
        ruta, real = self._escribir("ds_manual.md", 400)
        with open(real, encoding="utf-8") as fh:
            contenido = fh.read()
        manual = contenido.split(ds.MARCA_DATOS_FIN, 1)[1]
        with open(real, "w", encoding="utf-8") as fh:
            fh.write(contenido.split(ds.MARCA_DATOS_FIN, 1)[0]
                     + ds.MARCA_DATOS_FIN + "\n\nCONCLUSION ESCRITA A MANO\n")
        ds.escribir_informe(ruta, ["X"], 400)
        self.assertIn("CONCLUSION ESCRITA A MANO", self._leer(ruta))
        self.assertNotIn("Conclusiones", self._leer(real))

    def test_el_mismo_fichero_es_idempotente(self):
        ruta, real = self._escribir("ds_idem.md", 400)
        uno = self._leer(real)
        ds.escribir_informe(ruta, ["DATOS DE PRUEBA"], 400)
        self.assertEqual(uno, self._leer(real))


class TestLasConclusionsNoSePierdenEnElFicheroReal(unittest.TestCase):
    """El fichero del repo, no uno temporal: es el que se lee."""

    def test_balance_md_tiene_datos_y_conclusiones(self):
        ruta = os.path.join(RAIZ, "BALANCE.md")
        if not os.path.exists(ruta):
            self.skipTest("BALANCE.md no generado todavia")
        with open(ruta, encoding="utf-8") as fh:
            contenido = fh.read()
        self.assertIn("Conclusiones", contenido)
        self.assertIn("Metodologia", contenido)
        self.assertIn("MEDIA POR FACCION", contenido)


if __name__ == "__main__":
    unittest.main()