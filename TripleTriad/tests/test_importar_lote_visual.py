"""Paquetes sintéticos: integridad, aislamiento, selección y reversión reales."""
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
from PIL import Image
from tools.importar_lote_visual import Importador, digest
import lotes_visuales


def png(size, color=(61, 82, 105)):
    buf = io.BytesIO()
    Image.new('RGB', size, color).save(buf, 'PNG')
    return buf.getvalue()


class TestImportador(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='tt_lotes_', dir='C:/Users/julip/AppData/Local/Temp/opencode')
        self.root = Path(self.temp.name)
        (self.root / 'assets/cinematicas_hd').mkdir(parents=True)
        (self.root / 'assets/cinematicas_hd/protegido.png').write_bytes(png((1280, 720)))
        (self.root / 'assets/avatar_pik.png').write_bytes(png((256, 256)))
        self.escena = {'texto': 'Prueba técnica', 'fondo': 'escenario', 'mundo': 'real', 'retrato': 'pik'}
        self.catalogo = {'prologo.pre_duelo.3': self.escena,
                         'prologo.despertar.0': {**self.escena, 'fondo_hd': 'protegido.png'}}
        self.imp = Importador(self.root, self.root / 'incoming', self.catalogo)
        self.imp.iniciar()
        self.manifest = {'version': 1, 'lote': 'simulado_01', 'recursos': [
            {'id': 'escenario', 'nombre': 'Fondo simulado', 'tipo': 'fondo', 'archivo': 'fondo.png',
             'dimensiones': [1280, 720], 'escenas': ['prologo.pre_duelo.3']},
            {'id': 'pik', 'nombre': 'Retrato simulado', 'tipo': 'retrato', 'archivo': 'pik.png',
             'dimensiones': [256, 256], 'personaje': 'pik'}]}
        self.contents = {'fondo.png': png((1280, 720), (24, 62, 95)), 'pik.png': png((256, 256), (90, 130, 60))}

    def tearDown(self):
        lotes_visuales.registro.cache_clear()
        lotes_visuales._buscar.cache_clear()
        self.temp.cleanup()

    def paquete(self, manifest=None, contents=None, name='lote.zip'):
        p = self.imp.incoming / name
        with zipfile.ZipFile(p, 'w') as z:
            z.writestr('manifest.json', json.dumps(manifest or self.manifest))
            for nombre, data in (contents or self.contents).items():
                z.writestr(nombre, data)
        return p

    def test_importar_activar_revertir_sin_tocar_originales(self):
        before = (self.root / 'assets/avatar_pik.png').read_bytes()
        nombre = self.imp.preparar(self.paquete())
        self.assertFalse(self.imp.verificar()['lotes'][nombre]['activo'])
        self.imp.activar(nombre)
        with patch.object(lotes_visuales, 'registro', side_effect=self.imp.verificar), \
                patch.object(lotes_visuales, 'recurso', side_effect=lambda p: str(self.root / p)):
            self.assertIn('/fondos/', lotes_visuales.fondo(self.escena))
            self.assertIn('/retratos/', lotes_visuales.retrato('assets/avatar_pik.png'))
            self.assertIsNone(lotes_visuales.fondo(self.catalogo['prologo.despertar.0']))
            self.assertIsNone(lotes_visuales.retrato('cartas/pik.png'))
            self.imp.activar(nombre, False)
            lotes_visuales._buscar.cache_clear()
            self.assertIsNone(lotes_visuales.fondo(self.escena))
            self.assertIsNone(lotes_visuales.retrato('assets/avatar_pik.png'))
        self.assertEqual(before, (self.root / 'assets/avatar_pik.png').read_bytes())
        self.imp.verificar()

    def test_hash_declarado_incorrecto_rechaza_todo(self):
        self.manifest['recursos'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            self.imp.preparar(self.paquete())
        self.assertEqual(self.imp.verificar()['lotes'], {})

    def test_hash_correcto_y_fallback_runtime_ante_archivo_ausente(self):
        self.manifest['recursos'][0]['sha256'] = digest(self.contents['fondo.png'])
        nombre = self.imp.preparar(self.paquete())
        self.imp.activar(nombre)
        data = self.imp.verificar()
        self.assertTrue(data['lotes'][nombre]['recursos'][0]['hash_proporcionado'])
        (self.imp.base / nombre / 'fondos/escenario.png').unlink()
        with patch.object(lotes_visuales, 'registro', return_value=data), \
                patch.object(lotes_visuales, 'recurso', side_effect=lambda p: str(self.root / p)):
            self.assertIsNone(lotes_visuales.fondo(self.escena))

    def test_lote_totalmente_pendiente_no_se_activa(self):
        self.manifest['recursos'] = self.manifest['recursos'][:1]
        self.manifest['recursos'][0]['escenas'] = []
        nombre = self.imp.preparar(self.paquete())
        with self.assertRaisesRegex(ValueError, 'Todo el lote'):
            self.imp.activar(nombre)
        self.assertFalse(self.imp.verificar()['lotes'][nombre]['activo'])

    def test_resolucion_y_formato(self):
        self.contents['fondo.png'] = png((512, 256))
        with self.assertRaisesRegex(ValueError, 'resolución'):
            self.imp.preparar(self.paquete())
        self.contents['fondo.png'] = b'no es png'
        with self.assertRaises(OSError):
            self.imp.preparar(self.paquete(name='invalido.zip'))

    def test_zip_traversal_y_duplicados(self):
        self.contents['../escape.png'] = b'escape'
        with self.assertRaisesRegex(ValueError, 'insegura'):
            self.imp.preparar(self.paquete())
        self.assertFalse((self.root / 'escape.png').exists())
        del self.contents['../escape.png']
        self.contents['FONDO.PNG'] = self.contents['fondo.png']
        with self.assertRaisesRegex(ValueError, 'duplicada'):
            self.imp.preparar(self.paquete(name='duplicado.zip'))

    def test_asignaciones_ausentes_desconocidas_y_protegidas_pendientes(self):
        for escenas in ([], ['prologo.inventado.0'], ['prologo.despertar.0']):
            manifest = copy.deepcopy(self.manifest)
            manifest['lote'] = 'pendiente_' + str(len(self.imp.verificar()['lotes']))
            manifest['recursos'][0]['escenas'] = escenas
            nombre = self.imp.preparar(self.paquete(manifest=manifest))
            lote = self.imp.verificar()['lotes'][nombre]
            self.assertEqual(lote['recursos'][0]['estado'], 'pendiente')
            self.assertEqual(lote['recursos'][1]['estado'], 'listo')

    def test_idempotencia_y_no_sobrescritura(self):
        p = self.paquete()
        nombre = self.imp.preparar(p)
        self.assertEqual(nombre, self.imp.preparar(p))
        self.contents['pik.png'] = png((256, 256), (1, 2, 3))
        with self.assertRaisesRegex(ValueError, 'reservado'):
            self.imp.preparar(self.paquete(name='otro.zip'))

    def test_destino_integrado_protegido_incluso_revertido(self):
        nombre = self.imp.preparar(self.paquete())
        self.imp.activar(nombre)
        self.imp.activar(nombre, False)
        self.manifest['lote'] = 'simulado_02'
        otro = self.imp.preparar(self.paquete(name='otro.zip'))
        with self.assertRaisesRegex(ValueError, 'reservado'):
            self.imp.activar(otro)

    def test_tampering_detectado(self):
        nombre = self.imp.preparar(self.paquete())
        (self.imp.base / nombre / 'retratos/pik.png').write_bytes(b'alterado')
        with self.assertRaisesRegex(ValueError, 'inmutable'):
            self.imp.activar(nombre)

    def test_original_protegido_detectado(self):
        (self.root / 'assets/cinematicas_hd/protegido.png').write_bytes(b'alterado')
        with self.assertRaisesRegex(ValueError, 'protegido'):
            self.imp.verificar()

    def test_cambio_guion_no_reasigna(self):
        nombre = self.imp.preparar(self.paquete())
        self.escena['texto'] = 'Otro texto'
        with self.assertRaisesRegex(ValueError, 'guion cambió'):
            self.imp.activar(nombre)

    def test_siguiente_no_reactiva_revertido(self):
        self.paquete()
        nombre = self.imp.siguiente()
        self.imp.activar(nombre, False)
        with self.assertRaisesRegex(ValueError, 'No hay ZIP nuevos'):
            self.imp.siguiente()

    def test_preview_renderer_real_y_seleccion_sin_activar(self):
        nombre = self.imp.preparar(self.paquete())
        salida = self.imp.previsualizar(nombre)
        a = salida / 'prologo.pre_duelo.3_antes.png'
        b = salida / 'prologo.pre_duelo.3_candidato.png'
        self.assertNotEqual(digest(a.read_bytes()), digest(b.read_bytes()))
        with Image.open(b) as imagen:
            self.assertEqual(imagen.size, (1280, 800))
        self.assertFalse(self.imp.verificar()['lotes'][nombre]['activo'])
        evidencia = os.environ.get('TT_EVIDENCIA_IMPORTADOR')
        if evidencia:
            import shutil
            destino = Path(evidencia)
            destino.mkdir(parents=True, exist_ok=True)
            shutil.copy2(a, destino / 'simulado_antes.png')
            shutil.copy2(b, destino / 'simulado_candidato.png')
            shutil.copy2(self.imp.base / nombre / 'paquete_original.zip', destino / 'simulado_NO_PRODUCCION.zip')


if __name__ == '__main__':
    unittest.main()
