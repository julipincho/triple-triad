"""Un perfil nuevo puede iniciar un duelo con diez cartas legales."""
import unittest
from unittest.mock import patch
import campana
import mazos


class TestMazoInicialGlobal(unittest.TestCase):
    def test_perfil_nuevo_sale_del_ritual_con_diez_cartas_jugables(self):
        profile = campana.perfil_por_defecto()
        with patch('campana.cargar_perfil', return_value=profile), patch('campana.guardar_perfil'), patch('campana.random.sample', return_value=mazos.HUMANOS[:5]):
            names = campana.asegurar_mazo_global()
        self.assertEqual(len(names), 10)
        self.assertEqual(len(set(names)), 10)
        cards = [profile['coleccion'][n] for n in names]
        self.assertTrue(campana.validar_mazo(cards, set(profile['coleccion']))[0])
        self.assertTrue(all(c.nombre in profile['coleccion'] for c in mazos.HUMANOS[:5]))

    def test_un_mazo_valido_y_el_progreso_se_conservan(self):
        profile = campana.perfil_por_defecto()
        profile.update(coleccion=campana.coleccion_inicial('humano'), moneda=123, duelos=50)
        profile['mazo'] = list(profile['coleccion'])
        original = list(profile['mazo'])
        with patch('campana.cargar_perfil', return_value=profile), patch('campana.guardar_perfil') as save:
            self.assertEqual(campana.asegurar_mazo_global(), original)
        save.assert_not_called()
        self.assertEqual(profile['moneda'], 123)
        self.assertEqual(profile['duelos'], 50)
