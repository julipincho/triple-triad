"""Mapeo exacto del lote aprobado de fondos cinematográficos."""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cinematicas
import finales
import prologo
import narrativa
from paths import recurso


class TestCinematicasAprobadas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lote = ROOT / "assets/lotes_visuales/cinematicas_aprobadas_2026_10_15"
        cls.manifest = json.loads((cls.lote / "manifest.json").read_text(encoding="utf-8"))

    def test_los_20_png_cumplen_manifest_y_se_cargan(self):
        for item in self.manifest["fondos"]:
            path = ROOT / "assets/cinematicas_hd" / (item["id"] + ".png")
            self.assertTrue(path.is_file(), item["id"])
            data = path.read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"], item["id"])
            with Image.open(path) as im:
                self.assertEqual((im.format, im.mode, im.size),
                                 ("PNG", "RGB", (1280, 720)), item["id"])
                im.load()

    def test_intro_asigna_solo_los_tres_planos_nuevos(self):
        escenas, _ = cinematicas.intro()
        self.assertEqual([e.get("fondo_hd") for e in escenas], [
            "intro_amanecer_mundo_antiguo.png",
            "intro_amanecer_mundo_antiguo.png",
            "intro_grieta_umbral_cielo.png",
            "intro_estandartes_siete_bandos.png",
            "sala_trono.png",
        ])

    def test_cada_apertura_usa_su_fondo_sin_fuga_a_otras_cinemas(self):
        ids = {
            "humano": "apertura_humano_reino_en_cenizas.png",
            "orco": "apertura_orco_frontera_muralla.png",
            "goblin": "apertura_goblin_puerta_bajo_foso.png",
            "elfo": "apertura_elfo_bosque_silencioso.png",
            "hombre_lobo": "apertura_hombre_lobo_ciudad_lunar.png",
            "vampiro": "apertura_vampiro_cripta_pacto_roto.png",
            "dragon": "apertura_dragon_cielo_brasa.png",
            "elfo_nocturno": "apertura_elfo_nocturno_bosque_umbral.png",
            "hombre_pantera": "apertura_pantera_tejados_ciudad.png",
            "hombre_lagarto": "apertura_lagarto_pantano_ruinas.png",
        }
        for faccion, fondo in ids.items():
            escenas, _ = cinematicas.apertura(faccion)
            self.assertTrue(escenas)
            self.assertTrue(all(e["fondo_hd"] == fondo for e in escenas), faccion)
        self.assertTrue(any(e.get("fondo_hd") == "sala_trono.png"
                            for e in narrativa.previa_nodo("trono")))

    def test_prologo_campamento_y_mundos_no_remapean_claves_globales(self):
        for bloque in (prologo.escenas_nara, prologo.escenas_explicacion,
                       prologo.escenas_cierre):
            self.assertTrue(all(e.get("fondo_hd") == "prologo_campamento_nara.png"
                                for e in bloque() if e.get("fondo") == "campamento"))
        self.assertTrue(all(e.get("fondo_hd") == "prologo_apagon_salon.png"
                            for e in prologo.escenas_transporte()))
        self.assertTrue(all(e.get("fondo_hd") == "camino_lluvioso.png"
                            for e in prologo.escenas_despertar()))
        self.assertTrue(all(e.get("fondo_hd") == "salon_torneo.png"
                            for e in finales.escenas_epilogo("equilibrio")))

    def test_variantes_del_umbral_y_epilogo_caos_quedan_separados(self):
        por_variante = {
            "dominio": "final_umbral_dominio_forzado.png",
            "equilibrio": "final_umbral_equilibrio_apertura.png",
            "caos": "final_umbral_caos_mundos_mezclados.png",
        }
        for variante, fondo in por_variante.items():
            self.assertTrue(all(e["fondo_hd"] == fondo
                                for e in finales.escenas_umbral(variante)))
        self.assertTrue(all(e["fondo_hd"] == "epilogo_caos_salon_invadio.png"
                            for e in finales.escenas_epilogo("caos")))
        for variante in ("dominio", "equilibrio"):
            self.assertTrue(all(e["fondo_hd"] == "salon_torneo.png"
                                for e in finales.escenas_epilogo(variante)))


if __name__ == "__main__":
    unittest.main()
