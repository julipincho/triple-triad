"""Medicion opcional del juego real. Solo se activa con ?auditar=1."""
import json
import time
import pygame


def activar(contexto):
    import platform
    if 'auditar=1' not in str(platform.window.location.search):
        return
    flip = pygame.display.flip
    eventos = pygame.event.get
    periodos = []
    anterior = time.perf_counter()
    cuadros = 0
    ultimo_evento = None

    def get(*args, **kwargs):
        nonlocal ultimo_evento
        result = eventos(*args, **kwargs)
        for event in result:
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                ultimo_evento = {'tipo': event.type, 'pos': list(event.pos)}
        return result

    def presentar():
        nonlocal anterior, cuadros
        ahora = time.perf_counter()
        periodos.append((ahora - anterior) * 1000)
        del periodos[:-180]
        anterior = ahora
        cuadros += 1
        if cuadros % 15 == 0:
            ordenados = sorted(periodos)
            media = sum(periodos) / len(periodos)
            datos = {'cuadros': cuadros, 'fps': 1000 / media if media else 0,
                     'p95_ms': ordenados[int(len(ordenados) * .95)],
                     'max_ms': max(periodos), 'periodos': periodos,
                     'puntero': list(pygame.mouse.get_pos()), 'evento': ultimo_evento,
                     'ventana': list(pygame.display.get_window_size()),
                     'superficie': list(pygame.display.get_surface().get_size()),
                     'contexto': contexto()}
            platform.window.eval('window.__ttDiag=' + json.dumps(datos))
        flip()

    pygame.event.get = get
    pygame.display.flip = presentar
