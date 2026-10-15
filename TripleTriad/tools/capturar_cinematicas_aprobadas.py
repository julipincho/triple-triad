"""Renderiza en el reproductor los 20 fondos aprobados sin tocar guardados."""
import os
from pathlib import Path
import sys
import tempfile

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["TRIPLETRIAD_DATA"] = tempfile.mkdtemp(prefix="tt_cinematicas_20261015_")

import pygame
import cinematicas
import finales
import prologo


def escenas_muestra():
    intro, _ = cinematicas.intro()
    resultado = {
        "intro_amanecer_mundo_antiguo": intro[0],
        "intro_grieta_umbral_cielo": intro[2],
        "intro_estandartes_siete_bandos": intro[3],
        "prologo_escenario_presentacion": prologo.escenas_pre_duelo()[1],
        "prologo_apagon_salon": prologo.escenas_transporte()[0],
        "prologo_campamento_nara": prologo.escenas_nara()[0],
    }
    facciones = {
        "humano": "apertura_humano_reino_en_cenizas",
        "orco": "apertura_orco_frontera_muralla",
        "goblin": "apertura_goblin_puerta_bajo_foso",
        "elfo": "apertura_elfo_bosque_silencioso",
        "hombre_lobo": "apertura_hombre_lobo_ciudad_lunar",
        "vampiro": "apertura_vampiro_cripta_pacto_roto",
        "dragon": "apertura_dragon_cielo_brasa",
        "elfo_nocturno": "apertura_elfo_nocturno_bosque_umbral",
        "hombre_pantera": "apertura_pantera_tejados_ciudad",
        "hombre_lagarto": "apertura_lagarto_pantano_ruinas",
    }
    for faccion, ident in facciones.items():
        resultado[ident] = cinematicas.apertura(faccion)[0][0]
    for variante in ("dominio", "equilibrio", "caos"):
        resultado[f"final_umbral_{variante}"] = finales.escenas_umbral(variante)[0]
    resultado["epilogo_caos_salon_invadio"] = finales.escenas_epilogo("caos")[0]
    return resultado


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    assert screen.get_size() == (1280, 800)
    output = BASE / "capturas/cinematicas_aprobadas_20261015"
    output.mkdir(parents=True, exist_ok=True)
    muestras = escenas_muestra()
    assert len(muestras) == 20, len(muestras)
    for ident, datos in muestras.items():
        ruta = datos.get("fondo_hd")
        assert ruta and ruta.endswith(".png"), (ident, ruta)
        cine = cinematicas.Cinematica([datos], nombre_jugador="El duelista")
        escena = cine.escena()
        escena.mostrado = len(escena.texto)
        cine._dibujar(screen, escena, 2.0)
        pygame.image.save(screen, str(output / ruta))
    pygame.quit()
    print(f"Capturas: {len(muestras)} cinemáticas; lienzo lógico 1280x800; viewport HD 1280x720")


if __name__ == "__main__":
    main()
