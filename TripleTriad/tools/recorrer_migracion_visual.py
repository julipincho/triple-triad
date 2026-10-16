"""Evidencia visual y campañas automáticas con reglas reales y guardados temporales."""
import json
import math
import random
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / 'tools'))
sys.path.insert(0, str(BASE / 'tests'))
import auditar_cinematicas_y_prototipos as a
import pygame
from duelos_simulador import jugar_turno
from partida import Resultado
import reglas
import encuentros

OUT = BASE / 'auditoria/migracion_avatares_20261015'


def secuencias():
    yield from a.secuencias()
    for faction in ('elfo_nocturno', 'hombre_pantera', 'hombre_lagarto'):
        state = a.campana.nueva_mini_campana(faction)
        for node in a.campana.NODOS_MINI:
            info = a.campana.info_duelo(state, node)
            yield f'mini.{faction}.{node}.previa', a.cine.escenas_nodo(info)[0]
            yield f'mini.{faction}.{node}.victoria', a.cine.escenas_posterior(info, True)
            yield f'mini.{faction}.{node}.derrota', a.cine.escenas_posterior(info, False)
    for faction in a.cine.APERTURAS:
        for encounter in encuentros.LORE:
            yield f'encuentro.{faction}.{encounter}', encuentros.escena_antes(encounter, faction)


def renderizar():
    screen = pygame.display.set_mode((1280, 800))
    rows, seen = [], {}
    for block, scenes in secuencias():
        for index, data in enumerate(scenes):
            cine = a.cine.Cinematica([data], nombre_jugador='El duelista')
            scene = cine.escena()
            scene.mostrado = len(scene.texto)
            path = ('assets/cinematicas_hd/' + scene.fondo_hd if scene.fondo_hd else
                    scene.fondo_lote or a.arte_visual.alternativa(a.ui.ruta_fondo(scene.fondo), 'fondo')
                    or a.ui.ruta_fondo(scene.fondo))
            assert (BASE / path).is_file(), path
            rows.append(dict(id=f'{block}.{index}', fondo=path, retrato=data.get('retrato'), texto=data['texto']))
            if path not in seen:
                cine._dibujar(screen, scene, 2)
                name = f'despues_{len(seen):02d}.png'
                pygame.image.save(screen, str(OUT / name))
                seen[path] = name
    sheet = pygame.Surface((1280, math.ceil(len(seen) / 4) * 220))
    sheet.fill((20, 27, 40))
    font = pygame.font.Font(None, 18)
    for index, (path, name) in enumerate(seen.items()):
        x, y = index % 4 * 320, index // 4 * 220
        sheet.blit(pygame.transform.scale(pygame.image.load(str(OUT / name)), (320, 200)), (x, y))
        sheet.blit(font.render(Path(path).stem, True, 'white'), (x, y + 201))
    pygame.image.save(sheet, str(OUT / 'cinematicas_despues.png'))
    before = json.loads((OUT / 'recorrido.json').read_text(encoding='utf-8'))
    before += json.loads((OUT / 'secundarias_antes.json').read_text(encoding='utf-8'))
    assert len(before) == len(rows)
    changed = []
    for old, new in zip(before, rows):
        assert old['id'] == new['id'] and old['texto'] == new['texto'] and old['retrato'] == new['retrato']
        if old['fondo'] != new['fondo']:
            assert old['id'].startswith(('campana.', 'mini.', 'encuentro.'))
            assert Path(old['fondo']).stem in ('aldea', 'ruinas', 'fortaleza', 'asalto', 'umbral', 'estandartes', 'campamento', 'camino')
            changed.append(new['id'])
    (OUT / 'recorrido_despues.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    return dict(escenas=len(rows), fondos=len(seen), escenas_corregidas=len(changed))


def jugar_campanas():
    results = []
    rng = random.Random(20261015)
    for faction in a.cine.APERTURAS:
        for branch in ('aldea', 'ruinas'):
            state = a.campana.nueva_campana(faction)
            played = []
            for attempt in range(500):
                if state.get('completada'):
                    break
                node = a.campana.nodo_actual(state)
                if node == 'bifurcacion':
                    a.campana.elegir_bifurcacion(state, branch)
                    continue
                board = [[None] * 3 for _ in range(3)]
                hands = [a.campana.cartas_duelo(state), a.campana.mazo_rival(state)]
                turn, moves = attempt % 2, 0
                while reglas.celdas_vacias(board):
                    if not jugar_turno(board, hands[turn], 'T' if turn == 0 else 'C', rng, True):
                        break
                    moves += 1
                    turn = 1 - turn
                assert moves == 9
                player, cpu, winner = reglas.puntaje_final(board)
                won = winner == 'T'
                a.campana.registrar_resultado(state, Resultado(won, 0, 5, (player, cpu)))
                played.append(dict(nodo=node, victoria=won, marcador=[player, cpu]))
                pending = state.get('recompensa_pendiente')
                if pending:
                    choices = a.campana.recompensas_de(pending)
                    reward = 'entrenamiento' if 'entrenamiento' in choices else 'sigilo'
                    a.campana.entregar_recompensa(state, reward, pending, idx=0)
            assert state.get('completada'), (faction, branch, len(played))
            results.append(dict(faccion=faction, rama=branch, duelos=played, final=a.campana.final_de(state)))
    (OUT / 'campanas_jugadas.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    return dict(campanas=len(results), duelos=sum(len(x['duelos']) for x in results))


def main():
    OUT.mkdir(exist_ok=True)
    pygame.init()
    summary = renderizar()
    summary.update(jugar_campanas())
    (OUT / 'resumen.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(summary)
    pygame.quit()


if __name__ == '__main__':
    main()
