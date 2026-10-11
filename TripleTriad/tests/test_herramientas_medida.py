"""Las herramientas de medicion no pueden devolver cifras que no midieron.

Todo el balance de G8 sale de estos dos scripts. Un parametro imposible que
cae al valor por defecto, o un nombre de nodo que no existe, producen un
informe con aspecto de evidencia y sin relacion con lo que se queria medir.
Medido antes de arreglarlo:

  --nodos papel    -> columna de nodo rotulada "papel" con 62.5%-81.2% reales
                      (era `senda` medida y etiquetada con un nombre falso)
  --rival 0        -> 0 es falsy, asi que midio 5 cartas y lo mismo dio
  --refuerzo -5    -> se ignoraba en silencio
  --duelos 0       -> "victorias del jugador: 0.0%", promediado sobre nada
  --cartas 3       -> por debajo del minimo de mazo del propio juego
  TT_SEMILLAS=0    -> division por cero dentro del informe

Cada uno de esos numeros es peor que no dar numero: parece una medida.
"""

import io
import os
import subprocess
import sys
import tempfile
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def _correr(script, *args, env_extra=None):
    env = dict(os.environ)
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    if env_extra:
        env.update(env_extra)
    with tempfile.TemporaryDirectory(prefix="tt_herramienta_") as tmp:
        env["TRIPLETRIAD_DATA"] = tmp
        p = subprocess.run([PY, "-B", os.path.join("tools", script), *args],
                           cwd=RAIZ, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=1200)
    return p.returncode, p.stdout + p.stderr


class TestSimuladorRechazaLoImposible(unittest.TestCase):

    def test_nodo_desconocido_no_se_mide_con_una_etiqueta_falsa(self):
        codigo, salida = _correr("simular_g8.py", "--nodos", "papel", "--duelos", "20")
        self.assertEqual(2, codigo, salida[-400:])
        self.assertIn("nodo desconocido", salida)
        # Y lo importante: no puede haber ninguna cifra de victorias.
        self.assertNotIn("resumen:", salida)

    def test_rival_cero_no_cae_al_valor_por_defecto(self):
        codigo, salida = _correr("simular_g8.py", "--nodos", "senda",
                                 "--duelos", "20", "--rival", "0")
        self.assertEqual(2, codigo, salida[-400:])
        self.assertIn("--rival", salida)
        self.assertNotIn("resumen:", salida)

    def test_cartas_fuera_del_mazo_del_juego_se_rechazan(self):
        for valor in ("3", "99"):
            codigo, salida = _correr("simular_g8.py", "--nodos", "senda",
                                     "--duelos", "20", "--cartas", valor)
            self.assertEqual(2, codigo, f"--cartas {valor}: {salida[-300:]}")
            self.assertIn("--cartas", salida)

    def test_cero_duelos_no_se_reporta_como_derrota_del_jugador(self):
        codigo, salida = _correr("simular_g8.py", "--nodos", "senda", "--duelos", "0")
        self.assertEqual(2, codigo, salida[-400:])
        self.assertNotIn("0.0%", salida)

    def test_refuerzo_negativo_se_rechaza(self):
        codigo, salida = _correr("simular_g8.py", "--nodos", "senda",
                                 "--duelos", "20", "--refuerzo", "-5")
        self.assertEqual(2, codigo, salida[-400:])
        self.assertIn("--refuerzo", salida)

    def test_un_nodo_valido_sigue_midiendose(self):
        """La validacion no puede cerrar la puerta a la medicion legitima."""
        codigo, salida = _correr("simular_g8.py", "--nodos", "trono",
                                 "--duelos", "20", "--rival", "10")
        self.assertEqual(0, codigo, salida[-400:])
        self.assertIn("resumen:", salida)


class TestEconomiaRechazaMuestrasVacias(unittest.TestCase):

    def test_semillas_cero_no_promedian_sobre_nada(self):
        codigo, salida = _correr("economia_g8.py", env_extra={"TT_SEMILLAS": "0"})
        self.assertEqual(2, codigo, salida[-400:])
        self.assertNotIn("Traceback", salida)

    def test_semillas_no_numericas_no_reventan(self):
        codigo, salida = _correr("economia_g8.py", env_extra={"TT_SEMILLAS": "abc"})
        self.assertEqual(2, codigo, salida[-400:])
        self.assertNotIn("Traceback", salida)


if __name__ == "__main__":
    unittest.main()
