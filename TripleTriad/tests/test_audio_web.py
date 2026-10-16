"""El audio web mantiene pista, pausa y volumen sin usar SDL para musica."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import audio
import audio_web


class TestAudioWeb(unittest.TestCase):
    def test_reproductor_recibe_audio_y_parametros(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'pista.ogg'
            path.write_bytes(b'OggS-test')
            window = SimpleNamespace(eval=Mock())
            with patch('platform.window', window, create=True):
                audio_web.controlar('play', ruta=path, volumen=0.2, bucle=False)
            script = window.eval.call_args.args[0]
            self.assertIn('data:audio/ogg;base64,T2dnUy10ZXN0', script)
            self.assertIn('volume=0.2', script)
            self.assertIn('loop=false', script)

    def test_ciclo_de_vida_no_reinicia_la_misma_pista(self):
        before = audio._musica_actual, audio._musica_pausada
        try:
            audio._musica_actual, audio._musica_pausada = None, False
            with patch.object(audio, '_WEB', True), patch('audio.disponible', return_value=True), patch('audio.os.path.exists', return_value=True), patch('audio_web.controlar') as control, patch('audio.pygame.mixer.music') as mixer:
                audio.musica('prueba_web_unica')
                audio.musica('prueba_web_unica')
                self.assertEqual([c.args[0] for c in control.call_args_list], ['play'])
                audio.pausar_musica()
                audio.musica('prueba_web_unica')
                audio._ajustar_volumen_musica()
                audio.detener_musica()
                self.assertEqual([c.args[0] for c in control.call_args_list], ['play', 'pause', 'resume', 'volume', 'stop'])
                mixer.load.assert_not_called()
                mixer.play.assert_not_called()
        finally:
            audio._musica_actual, audio._musica_pausada = before


if __name__ == '__main__':
    unittest.main()
