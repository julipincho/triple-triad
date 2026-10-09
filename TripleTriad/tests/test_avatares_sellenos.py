"""Los avatares que ya estan bien, fijados por hash.

Por que hace falta: el repo tenia `AVATARES_BIEN`, una lista en el generador de
los avatares que no hay que rehacer. Pero esa lista solo protege del `--fuerza`.
No impide que alguien regenere uno editando el fichero, y no deja rastro cuando
pasa: `assets/avatar_humano.png` puede cambiar y nada se queja hasta que alguien
mira la pantalla de faccion y ve que un bando ha cambiado de estilo.

Eso ya paso dos veces en este proyecto. La primera al cambiar los dos avatares de
modelo; la segunda al pasarlos a `animagine-xl` con un prompt que pedia sombreado
plano. En las dos se toco el fichero y no habia forma de notar cual habia sido.

Este test convierte el acuerdo en algo verificable. Los diecisiete que estan
bien se guardan por SHA-256: si alguno cambia, salta el test con el nombre del
culpable.

Para cambiar uno A PROPOSITO, que tiene que ser una decision y no un descuido:

    python tests/actualizar_hashes_avatares.py

que imprime los hashes nuevos para pegarlos en `HASHES_AVATARES_OK` de este
fichero. Si estas leyendo esto porque el test ha fallado sin querer cambiar nada,
no lo ignores: `git checkout assets/` lo vuelve a dejar como estaba.
"""

import hashlib
import os
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

CARPETA = os.path.join(RAIZ, "assets")

#: Los que NO se tocan. Los dos que si van a cambiar de vez en cuando son
#: `avatar_hombre_lobo` y `avatar_hombre_pantera`: son los que se han tenido que
#: rehacer para que casaran con los demas, y es normal querer volver a
##: intentarlo. Los otros diecisiete estan bien y hay que dejarlos como estan.
HASHES_AVATARES_OK = {
    "avatar_dara.png":           "0079c06b9b272a7f",
    "avatar_dragon.png":         "c6c23bdfdc5dbb45",
    "avatar_duelista.png":       "f310cedfecf0400a",
    "avatar_elfo.png":           "aeabd64af80dac29",
    "avatar_elfo_nocturno.png":  "f27772ef95e5e9c3",
    "avatar_gobernante.png":     "b0e8ffdc6468f281",
    "avatar_goblin.png":         "0495bcddbbf18131",
    "avatar_hombre_lagarto.png": "35c7974510985d58",
    "avatar_humano.png":         "4cba0a838bc7cc5c",
    "avatar_jefe_arco.png":      "d88fb40a24f22e12",
    "avatar_nara.png":           "f087459276271300",
    "avatar_orco.png":           "26579b0f84f54140",
    "avatar_pik.png":            "42312984fb53ab3d",
    "avatar_presentador.png":    "7e7a6fb188e7e3e5",
    "avatar_rajoy.png":          "9c99a30e4c9f1b7f",
    "avatar_revancha.png":       "3caa49941b98c1d2",
    "avatar_vampiro.png":        "382439998dce1cba",
}

#: Los que SI se pueden cambiar. No se avisa de ellos, pero tienen que existir.
HASHES_AVATARES_LIBRES = ("avatar_hombre_lobo.png", "avatar_hombre_pantera.png")


def _hash(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


class TestAvataresSellenos(unittest.TestCase):
    def test_los_que_ya_estan_bien_no_han_cambiado(self):
        """El acuerdo, convertido en red de seguridad."""
        cambios = []
        for nombre, esperado in sorted(HASHES_AVATARES_OK.items()):
            ruta = os.path.join(CARPETA, nombre)
            if not os.path.exists(ruta):
                cambios.append("%s ha desaparecido" % nombre)
                continue
            actual = _hash(ruta)
            if actual != esperado:
                cambios.append("%s: era %s y ahora es %s"
                               % (nombre, esperado, actual))
        self.assertEqual([], cambios,
                         "avatares que estaban bien y han cambiado sin "
                         "querer:\n  %s\n\nSi el cambio es a proposito, "
                         "actualiza los hashes con "
                         "tests/actualizar_hashes_avatares.py. Si no, "
                         "`git checkout assets/`" % "\n  ".join(cambios))

    def test_los_dos_libres_siguen_existiendo(self):
        """Que sean 'libres' no significa que puedan desaparecer."""
        for nombre in HASHES_AVATARES_LIBRES:
            self.assertTrue(os.path.join(CARPETA, nombre),
                            "falta %s" % nombre)

    def test_todos_los_fijados_estan_en_disco(self):
        """Si un avatar se renombra, el hash viejo dejaria demirar solo. Aqui se
        ve enseguida que la lista se ha quedado desfasada."""
        faltan = [n for n in HASHES_AVATARES_OK
                  if not os.path.exists(os.path.join(CARPETA, n))]
        self.assertEqual([], faltan,
                         "estos avatares estan en la lista de fijos pero no "
                         "en disco: %s" % faltan)

    def test_los_avatar_del_juego_son_rgba_y_256(self):
        """La forma que espera el motor. Si un avatar se regenera a otro tamano
        o sin canal alfa, se dibuja raro aunque tenga buena pinta."""
        from PIL import Image
        for nombre in list(HASHES_AVATARES_OK) + list(HASHES_AVATARES_LIBRES):
            with Image.open(os.path.join(CARPETA, nombre)) as im:
                self.assertEqual((256, 256), im.size,
                                 "%s no es 256x256" % nombre)
                self.assertEqual("RGBA", im.mode,
                                 "%s no es RGBA" % nombre)


if __name__ == "__main__":
    unittest.main()
