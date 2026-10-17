"""Recorre los bucles reales con eventos SDL y datos temporales.

No sustituye resultados ni IA. La política de prueba conoce ambas manos;
sirve para comprobar recorridos, no para medir dificultad humana.
"""
import asyncio
import copy
import json
import os
from pathlib import Path
import random
import shutil
import sys
import tempfile
import time

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
TEMP = tempfile.TemporaryDirectory(prefix='tt_v21_b07_')
RESUME = '--resume-editor' in sys.argv
SELECT = sys.argv[sys.argv.index('--case') + 1] if '--case' in sys.argv else None
if RESUME:
    for path in (BASE / 'build/v2_1_b07_resume').glob('*.json'):
        shutil.copy2(path, Path(TEMP.name) / path.name)
os.environ.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy', TRIPLETRIAD_DATA=TEMP.name)
import audio
import campana
import cinematicas
import main
import pantallas
import partida
import pygame
import reglas
import ui

OUT = BASE / 'auditoria/v2_1_bloque_07'
if SELECT:
    assert SELECT in ('principal_aldea', 'principal_ruinas', 'mini_nocturno', 'mini_pantera', 'mini_lagarto')
    OUT = OUT / SELECT
OUT.mkdir(parents=True, exist_ok=True)
LOG = dict(base='9eddb94', metodo='Eventos SDL en bucles reales, reloj normal, IA sin modificar',
           limite='Política automatizada con ambas manos visibles; no evaluación humana de dificultad o ritmo.',
           recorridos=[])
if RESUME:
    LOG = json.loads((OUT / 'recorridos.json').read_text(encoding='utf-8'))
    LOG['recorridos'] = LOG['recorridos'][:1]
    LOG['reanudacion_editor'] = 'Prólogo y duelo completos conservados; editor reiniciado tras corregir clics antiguos.'


def save():
    (OUT / 'recorridos.json').write_text(json.dumps(LOG, ensure_ascii=False, indent=2), encoding='utf-8')


def frames(task):
    co, result = task.get_coro(), []
    while co is not None:
        frame = getattr(co, 'cr_frame', None)
        if frame:
            result.append(frame)
        co = getattr(co, 'cr_await', None)
    return result


def key(code):
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=code, unicode=''))
    pygame.event.post(pygame.event.Event(pygame.KEYUP, key=code))


def click(pos):
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))
    pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=pos))


def moved(board, card, owner, r, c):
    board = [[x.copia() if x else None for x in row] for row in board]
    board[r][c] = card.copia()
    board[r][c].dueno = owner
    reglas.cascada(board, r, c)
    return board


def score(board, hands, owner, depth, alpha=-1000, beta=1000):
    empty = reglas.celdas_vacias(board)
    if not depth or not empty or not hands[owner]:
        t, c = reglas.contar(board)
        return t - c
    best = -1000 if owner == reglas.USUARIO else 1000
    enemy = reglas.CPU if owner == reglas.USUARIO else reglas.USUARIO
    for i, card in enumerate(hands[owner]):
        new_hands = dict(hands)
        new_hands[owner] = hands[owner][:i] + hands[owner][i+1:]
        for r, c in empty:
            value = score(moved(board, card, owner, r, c), new_hands, enemy, depth-1, alpha, beta)
            if owner == reglas.USUARIO:
                best, alpha = max(best, value), max(alpha, value)
            else:
                best, beta = min(best, value), min(beta, value)
            if beta <= alpha:
                return best
    return best


def choose(game, lose=False):
    choices = []
    empty = reglas.celdas_vacias(game.board)
    depth = len(empty) - 1 if len(empty) <= 4 else 1
    for i, card in enumerate(game.mano_u):
        hands = {reglas.USUARIO:game.mano_u[:i]+game.mano_u[i+1:], reglas.CPU:game.mano_c}
        for r, c in empty:
            board = moved(game.board, card, reglas.USUARIO, r, c)
            value = score(board, hands, reglas.CPU, depth)
            value += game._bono_posicion(card, r, c) * 0.12
            choices.append((value, i, r, c))
    return (min if lose else max)(choices)[1:]


async def drive(task, record, screen, faction, branch, request_loss):
    seen_scenes, seen_screens, seen_games, completed = set(), set(), [], set()
    started, last_action, last_save, lost = time.time(), 0, 0, False
    duel_offset = len(record['duelos'])
    while not task.done():
        await asyncio.sleep(0.06)
        now = time.time()
        if now - started > 1200:
            raise TimeoutError('Recorrido excede veinte minutos')
        chain = frames(task)
        relevant = [f for f in chain if f.f_code.co_filename.endswith(('main.py', 'pantallas.py', 'cinematicas.py', 'partida.py'))]
        if not relevant:
            continue
        frame = relevant[-1]
        name, loc = frame.f_code.co_name, frame.f_locals
        if now-last_save > 5:
            record['activo'] = dict(pantalla=name, segundos=round(now-started, 2))
            save()
            last_save = now
        state = next((f.f_locals['estado'] for f in chain if isinstance(f.f_locals.get('estado'), dict)), None)
        if state:
            record['estado'] = copy.deepcopy(state)
        signature = (name, state.get('nodo') if state else None)
        if signature not in seen_screens:
            seen_screens.add(signature)
            record['pantallas'].append(dict(nombre=name, nodo=signature[1], segundos=round(now-started, 2)))
            print(record['id'], name, signature[1], flush=True)
            if name != 'ejecutar':
                pygame.image.save(screen, str(OUT / f"{record['id']}_{name}_{signature[1]}.png"))
            save()
        game = loc.get('juego')
        if name == 'partida' and isinstance(game, partida.Juego):
            if game not in seen_games:
                seen_games.append(game)
                record['duelos'].append(dict(nodo=game.info.get('nodo'), rival=game.info.get('nombre'),
                                            mano_u=[c.nombre for c in game.mano_u], mano_c=[c.nombre for c in game.mano_c]))
            item = record['duelos'][duel_offset + seen_games.index(game)]
            if game.fin:
                if id(game) not in completed:
                    completed.add(id(game))
                    item.update(ganador=game.ganador, marcador=list(reglas.contar(game.board)),
                                jugadas=game.jugadas, capturas=game.capturas)
                    if game.ganador == reglas.CPU and game.info.get('nodo') != 'prologo':
                        lost = True
                    print('RESULTADO', record['id'], item, flush=True)
                    pygame.image.save(screen, str(OUT / f"{record['id']}_duelo_{len(record['duelos'])}.png"))
                    save()
                    if len(record['duelos']) > 30:
                        raise RuntimeError('Demasiados reintentos para esta política de prueba')
                if partida.now_clickable(now, game.tiempo_fin):
                    key(pygame.K_RETURN)
                continue
            if not game.turno_cpu and not game.efecto and now-last_action > 0.18:
                intentional = request_loss and not lost and game.info.get('nodo') == 'senda'
                i, r, c = choose(game, intentional)
                click(ui.mano_rect(i, len(game.mano_u)).center)
                click(ui.celda_rect(r, c).center)
                last_action = now
            continue
        if name == 'ejecutar' and isinstance(loc.get('self'), cinematicas.Cinematica):
            cine = loc['self']
            scene = cine.escena()
            if scene is None:
                continue
            identity = (id(cine), cine.i, scene.texto)
            if scene.completa:
                if identity not in seen_scenes:
                    seen_scenes.add(identity)
                    record['escenas'].append(dict(texto=scene.texto, hablante=scene.hablante,
                                                contexto=main.contexto(), segundos=round(now-started, 2)))
                    save()
                    if len(record['escenas']) in (1, 8, 20, 40, 60):
                        pygame.image.save(screen, str(OUT / f"{record['id']}_escena_{len(record['escenas'])}.png"))
                if now-cine._t_escena >= max(1.2, len(scene.texto.split()) / 5):
                    key(pygame.K_RETURN)
            continue
        if now-last_action < 0.3:
            continue
        if name == 'pedir_nombre':
            key(pygame.K_RETURN)
        elif name == 'elegir_faccion':
            order = loc['orden']
            key(pygame.K_RETURN if order[loc['seleccion']] == faction else pygame.K_RIGHT)
        elif name == 'armar_mazo':
            if len(loc['seleccion']) == 10:
                click((640, 770))
            else:
                items = loc.get('rects_coleccion', [])
                candidate = next(((n, r) for n, r in items if n not in loc['seleccion']), None)
                if candidate:
                    click(candidate[1].center)
        elif name == 'elegir_rama':
            key(pygame.K_LEFT if branch == 'aldea' else pygame.K_RIGHT)
        elif name == 'mapa_campana':
            click(loc['seguir'].rect.center)
        elif name == 'mapa_mini':
            click(loc['luchar'].rect.center)
        elif name == 'derrota':
            click(loc['reintentar'].rect.center)
        elif name == 'elegir_carta_para_mejorar':
            key(pygame.K_1)
        elif name in ('draft_reemplazo', 'draft'):
            if loc.get('rects'):
                click(loc['rects'][0].center)
        elif name in ('recompensa', 'decision_narrativa', 'encuentro', 'confirmar'):
            key(pygame.K_RETURN)
        elif name in ('cartel', 'epilogo', 'revelar_sobre', '_preguntar_rever'):
            click((640, 680))
        else:
            record['esperando'] = name
        last_action = now
    await task
    record.update(terminado=True, segundos=round(time.time()-started, 2), derrota_real=lost)
    save()


async def resume_editor(screen, clock, record):
    state = copy.deepcopy(record['estado'])
    deck = await pantallas.armar_mazo(screen, clock, state['faccion'], nuevo=True)
    assert deck is not None
    state['cartas'] = deck
    campana.guardar(state)
    await main._campana(screen, clock, state, nuevo=True)


async def run():
    pygame.init()
    audio.iniciar()
    screen = pygame.display.set_mode((1280, 800))
    clock = pygame.time.Clock()
    random.seed(2107)
    campana.establecer_nombre('Auditoría')
    cases = [('principal_aldea','humano','aldea',True), ('principal_ruinas','orco','ruinas',False),
             ('mini_nocturno','elfo_nocturno',None,False), ('mini_pantera','hombre_pantera',None,False),
             ('mini_lagarto','hombre_lagarto',None,False)]
    for index, (label,faction,branch,loss) in enumerate(cases):
        if SELECT and label != SELECT:
            continue
        if RESUME and index == 0:
            record = LOG['recorridos'][0]
        else:
            record = dict(id=label, pantallas=[], duelos=[], escenas=[], terminado=False)
            LOG['recorridos'].append(record)
        if index == 0:
            coroutine = resume_editor(screen, clock, record) if RESUME else main._nueva_campana(screen, clock)
        elif branch:
            state = campana.nueva_campana(faction)
            # Variante inicial explícita para cubrir la identidad de asalto.
            # Perder un duelo incrementa derrotas, no cambia este selector.
            state['revancha'] = 1
            campana.asegurar_coleccion(faction)
            campana.guardar(state)
            coroutine = main._campana(screen, clock, state, nuevo=True)
        else:
            coroutine = main._mini_campana(screen, clock)
        task = asyncio.create_task(coroutine)
        try:
            await drive(task, record, screen, faction, branch, loss)
        except BaseException as exc:
            record['error'] = repr(exc)
            pygame.image.save(screen, str(OUT / f'{label}_error.png'))
            save()
            task.cancel()
            raise
        if branch:
            assert record['estado']['completada'], record
            assert record['estado']['ruta'] == ['senda',branch,'fortaleza','asalto','trono']
        else:
            assert len([d for d in record['duelos'] if d.get('ganador') != reglas.CPU]) == 3
    pygame.quit()


if __name__ == '__main__':
    asyncio.run(run())
