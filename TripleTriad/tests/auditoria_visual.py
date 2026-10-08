"""Auditoria visual: detecta textos desbordados y elementos fuera de lugar.

    python tests/auditoria_visual.py

Revisa con las metricas reales de `ui` (ancho_texto/envolver) que ningun
texto se salga de su panel y ningun rectangulo se salga de la pantalla.
Devuelve codigo 1 si hay problemas, asi que sirve como puerta visual.

Cubre: selector de faccion, coleccion, cartas, cinematicas, manual y
practicas del tutorial, HUD del duelo y menu. Las pantallas con contenido
fijo preexistente (recompensa, encuentro, draft...) no tienen cadenas
nuevas en las Fases 1-2 y quedan fuera del alcance.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import campana  # noqa: E402
import cartas as crt  # noqa: E402
import cinematicas  # noqa: E402
import facciones  # noqa: E402
import mazos  # noqa: E402
import tutorial  # noqa: E402
from reglas import LADOS  # noqa: E402
from ui import ALTO, ANCHO, CARD_W, ancho_texto, envolver  # noqa: E402


def exceso_lineas(texto, tam, ancho, max_lineas, donde):
    n = len(envolver(texto, tam, ancho))
    if n > max_lineas:
        return f"{donde}: {n} lineas (max {max_lineas}): {texto[:50]}..."
    return None


def desborda(texto, tam, ancho_max, donde):
    w = ancho_texto(texto, tam)
    if w > ancho_max:
        return f"{donde}: {w}px > {ancho_max}px: {texto[:50]}..."
    return None


def fuera_pantalla(rect, donde):
    x, y, w, h = rect
    if x < 0 or y < 0 or x + w > ANCHO or y + h > ALTO:
        return f"{donde}: rect {rect} fuera de {ANCHO}x{ALTO}"
    return None


# ------------------------------------------------------------------ selector
def revisar_selector():
    fallos = []
    for n in (7, len(facciones.orden_facciones())):
        orden = facciones.orden_facciones()[:n]
        compacta = len(orden) > 7
        cols = 5 if compacta else 3
        paso_x, paso_y = (178, 225) if compacta else (290, 205)
        x0, y0, rw, rh = (50, 160, 168, 210) if compacta else (50, 165, 220, 190)
        for i, f in enumerate(orden):
            rect = (x0 + (i % cols) * paso_x, y0 + (i // cols) * paso_y, rw, rh)
            p = fuera_pantalla(rect, f"selector({n}): {f}")
            if p:
                fallos.append(p)
            if compacta:
                lineas = envolver(facciones.nombre(f), 8, rw - 88)[:2]
                if len(envolver(facciones.nombre(f), 8, rw - 88)) > 2:
                    fallos.append(f"selector({n}): nombre en 3+ lineas: {f}")
                for linea in lineas:
                    p = desborda(linea, 8, rw - 88, f"selector({n}): {f}")
                    if p:
                        fallos.append(p)
            else:
                lineas = envolver(facciones.nombre(f), 11, rw - 116)
                if len(lineas) > 2:
                    fallos.append(f"selector({n}): nombre en 3+ lineas: {f}")
                for linea in lineas[:2]:
                    p = desborda(linea, 11, rw - 116, f"selector({n}): {f}")
                    if p:
                        fallos.append(p)
                if len(envolver(mazos.DESCRIPCION_BANDO.get(f, ""), 7, rw - 116)) > 8:
                    fallos.append(f"selector({n}): descripcion larguisima: {f}")
    # ficha lateral: cursor replicado de pantallas.elegir_faccion (arco dinamico,
    # mazo en filas de 5, rivales reales)
    for f in facciones.orden_facciones():
        lema = facciones.FACCIONES[f]["lema"]
        arco = facciones.FACCIONES[f]["arco"]
        y = max(165 + 84, 165 + 46 + 13 * len(envolver(lema, 8, 264)) + 4)
        y += 15 * len(envolver(arco, 8, 264)) + 8 + 12
        filas_mazo = (min(len(mazos.TODOS[f]), 10) + 5) // 6
        y += 80 if filas_mazo == 1 else filas_mazo * 56 + 8
        if len(mazos.TODOS[f]) > 10:
            y += 16  # linea "+N mas en el mazo"
        y += 16
        for hab in sorted({c.habilidad for c in mazos.TODOS[f] if c.habilidad}):
            y += 12 * len(envolver(f"{hab}: {hab}", 7, 264)) + 4
        y += 18
        rivales = [facciones.nombre(r) for r in campana.escalera_de(f)]
        rivales.append(facciones.nombre(facciones.rival_final(f)))
        vistos = set()
        rivales = [r for r in rivales if not (r in vistos or vistos.add(r))]
        y += 12 * len(envolver(" › ".join(rivales), 7, 264))
        if y > 165 + 470 - 10:
            fallos.append(f"ficha: contenido hasta y={y} (fondo 635): {f}")
    return fallos


# ----------------------------------------------------------------- coleccion
def revisar_coleccion():
    fallos = []
    orden = facciones.orden_facciones()
    compacta = len(orden) > 7
    for i, f in enumerate(orden):
        rect = (40 + i * 120, 100, 112, 84) if compacta else (60 + i * 170, 100, 150, 70)
        p = fuera_pantalla(rect, f"coleccion: {f}")
        if p:
            fallos.append(p)
        if compacta:
            lineas = envolver(facciones.nombre(f), 7, rect[2] - 12)
            if len(lineas) > 2:
                fallos.append(f"coleccion: nombre en 3+ lineas: {f}")
            for linea in lineas:
                p = desborda(linea, 7, rect[2] - 12, f"coleccion: {f}")
                if p:
                    fallos.append(p)
    # panel de finales: el codigo dibuja solo las que caben + "+N finales mas"
    alturas = []
    for f in orden:
        conseguidos = campana.cargar_perfil().get("finales", {}).get(f, [])
        titulos = [campana.FINALES[f][v]["titulo"]
                   for v in ("dominio", "equilibrio", "caos")]
        h = 22 + 8 + 14 * max(1, len(envolver(" / ".join(titulos), 7, 300)))
        alturas.append(h)
    tope = ALTO - 200 - 96
    usado, n_vis = 0, 0
    for h in alturas:
        if usado + h + 60 > tope - 22:
            break
        usado += h
        n_vis += 1
    if len(alturas) - n_vis:
        usado += 22
    if max(120, usado + 60) > tope:
        fallos.append("coleccion: panel de finales no cabe ni recortado")
    # racha por faccion: dos filas con corto (el codigo las dibuja asi)
    for i, f in enumerate(orden):
        fila, col = divmod(i, 5)
        x = 80 + col * 95
        p = desborda(f"{facciones.corto(f)}: 12", 8, 90, f"coleccion racha: {f}")
        if p:
            fallos.append(p)
        if 80 + 4 * 95 + 90 > 60 + 500:
            fallos.append("coleccion racha: la fila se sale del panel")
            break
    return fallos


# -------------------------------------------------------------------- cartas
def _cabe_ajustado(texto, tam0, ancho_max):
    """Replica cartas._texto_ajustado: encoge hasta tam 5."""
    tam = tam0
    while tam > 5 and ancho_texto(texto, tam) > ancho_max:
        tam -= 1
    return ancho_texto(texto, tam) <= ancho_max


def revisar_cartas():
    fallos = []
    for bando, cartas in mazos.TODOS.items():
        for c in cartas:
            lineas = crt._lineas_nombre(c.nombre, CARD_W - 14)
            if len(lineas) > 2:
                fallos.append(f"carta: nombre en 3+ lineas: {c.nombre}")
            tam = 8 if len(lineas) == 1 else 6
            for linea in lineas:
                if not _cabe_ajustado(linea, tam, CARD_W - 14):
                    fallos.append(f"carta: nombre no cabe ni en tam 5: {c.nombre}")
            for lado in LADOS:
                if not 1 <= c.valores[lado] <= 10:
                    fallos.append(f"carta: valor fuera de 1-10: {c.nombre}.{lado}")
    return fallos


# --------------------------------------------------------------- cinematicas
def _textos_cinematicas():
    textos = []
    escenas, _ = cinematicas.intro()
    textos += [(e["texto"], e["fondo"]) for e in escenas if e["efecto"] != "titulo"]
    textos += [(e["texto"], "titulo") for e in escenas if e["efecto"] == "titulo"]
    for f in facciones.orden_facciones():
        escenas, _ = cinematicas.apertura(f)
        textos += [(e["texto"], f"apertura {f}") for e in escenas if e["efecto"] != "titulo"]
        for variante in ("dominio", "equilibrio", "caos"):
            datos = campana.FINALES[f][variante]
            textos += [(datos["titulo"], f"final {f}/{variante} (titulo)")]
            textos += [(l, f"final {f}/{variante}") for l in datos["lineas"]]
    for nodo_id, datos in campana.NODOS.items():
        textos += [(l, f"nodo {nodo_id}") for l in datos.get("previa", [])]
    for rival, d in campana.DUELISTAS.items():
        for clave in ("entrada", "captura_player", "captura_cpu", "win", "lose"):
            if d.get(clave):
                textos += [(d[clave], f"duelista {rival}/{clave}")]
    return textos


def revisar_cinematicas():
    fallos = []
    for texto, donde in _textos_cinematicas():
        if donde.endswith("(titulo)"):
            p = desborda(texto, 26, ANCHO - 100, f"cinematica: {donde}")
            if p:
                fallos.append(p)
            continue
        # caja de dialogo: Rect(120, ALTO-212, ANCHO-240, 152), 26px por linea
        p = exceso_lineas(texto, 12, ANCHO - 240 - 60, 4, f"cinematica: {donde}")
        if p:
            fallos.append(p)
    return fallos


# ------------------------------------------------------------------ tutorial
def revisar_tutorial():
    fallos = []
    for pagina in tutorial.paginas_manual():
        que = " ".join(pagina["que"])
        y_fin = 120 + 52 + 22 * len(envolver(que, 10, 760 - 48))
        if pagina.get("demo"):
            y_cartas = min(max(y_fin + 24, 120 + 250), 120 + 470 - 144 - 56)
            if y_cartas < y_fin + 10:
                fallos.append(f"manual: demo pisa el texto: {pagina['id']}")
            if y_cartas + 144 + 40 > 120 + 470:
                fallos.append(f"manual: demo fuera del panel: {pagina['id']}")
        p = exceso_lineas(pagina["sirve"], 9, 280, 20, f"manual sirve: {pagina['id']}")
        if p:
            fallos.append(p)
    for practica in tutorial.PRACTICAS:
        for s, paso in enumerate(practica["pasos"]):
            for clave in ("intro", "objetivo", "pista", "exito", "fallo"):
                # mensajes del HUD: panel de 600px centrado, tam 9
                p = desborda(paso[clave], 9, 580, f"practica {practica['id']} p{s}/{clave}")
                if p:
                    fallos.append(p)
            # panel lateral: Rect(ANCHO-400, 250, 340, 280), boton en y=430
            fin_obj = 250 + 104 + 21 * len(envolver(paso["objetivo"], 9, 300))
            if fin_obj > 250 + 180:
                fallos.append(f"practica {practica['id']} p{s}: objetivo hasta y={fin_obj} (boton 430)")
    return fallos


# --------------------------------------------------------------------- duelo
def revisar_duelo():
    fallos = []
    for f in facciones.orden_facciones():
        p = desborda(f"{facciones.nombre(f)} vs {facciones.nombre('orco')}", 8, 500,
                     f"duelo HUD: {f}")
        if p:
            fallos.append(p)
    for bando, cartas in mazos.TODOS.items():
        for c in cartas:
            for plantilla in (f"Juegas {c.nombre} y capturas 9",
                              f"Rival juega {c.nombre} y captura 9 - tu turno"):
                p = desborda(plantilla, 9, 580, f"duelo mensaje: {c.nombre}")
                if p:
                    fallos.append(p)
    fijos = ["Tu turno: arrastra una carta al tablero",
             "Consejo: Same y Plus voltean al vuelo",
             "Has ganado el duelo", "Empate: cuenta como victoria"]
    for m in fijos:
        p = desborda(m, 9, 580, "duelo mensaje fijo")
        if p:
            fallos.append(p)
    return fallos


# ---------------------------------------------------------------------- menu
def revisar_menu():
    fallos = []
    botones = [
        (ANCHO // 2 - 340, 230, 300, 54), (ANCHO // 2 - 340, 296, 300, 54),
        (ANCHO // 2 - 340, 362, 300, 54), (ANCHO // 2 - 340, 428, 300, 54),
        (ANCHO // 2 + 40, 230, 300, 54), (ANCHO // 2 + 40, 296, 300, 54),
        (ANCHO // 2 + 40, 362, 300, 54),
    ]
    for i, r in enumerate(botones):
        p = fuera_pantalla(r, f"menu: boton {i}")
        if p:
            fallos.append(p)
    p = fuera_pantalla((ANCHO // 2 - 300, 494, 600, 190), "menu: panel campana")
    if p:
        fallos.append(p)
    # sub de CONTINUAR: nombre o corto segun quepa en 280px a tam 8
    for f in facciones.orden_facciones():
        for nid in list(campana.NODOS) + list(campana.NODOS_MINI):
            sub = f"{facciones.nombre(f)} - {campana.nodo(nid)['titulo']}"
            if ancho_texto(sub, 8) > 280:
                sub = f"{facciones.corto(f)} - {campana.nodo(nid)['titulo']}"
            p = desborda(sub, 8, 280, f"menu sub: {f}/{nid}")
            if p:
                fallos.append(p)
    return fallos


def revisar_mapa_mini():
    fallos = []
    for i in range(3):
        rect = (ANCHO // 2 - 460 + i * 320, 240, 280, 220)
        p = fuera_pantalla(rect, f"mapa_mini: nodo {i}")
        if p:
            fallos.append(p)
    for nid in ("mini_senda", "mini_nudo", "mini_trono"):
        datos = campana.nodo(nid)
        p = desborda(datos["titulo"], 10, 260, f"mapa_mini: {nid}")
        if p:
            fallos.append(p)
        for f in facciones.orden_facciones():
            rival = campana.rival_de_nodo(
                {"faccion": f, "mini": True, "nodo": nid, "ruta": []}, nid)
            p = desborda(f"Rival: {facciones.nombre(rival)}", 8, 260,
                         f"mapa_mini rival: {f}/{nid}")
            if p:
                fallos.append(p)
    for r in [(ANCHO // 2 - 320, 520, 300, 54), (ANCHO // 2 + 20, 520, 300, 54)]:
        p = fuera_pantalla(r, "mapa_mini: boton")
        if p:
            fallos.append(p)
    return fallos


def revisar_mapa():
    from pantallas import CONEXIONES, POSICIONES
    fallos = []
    # titulo bajo cada circulo: no debe pisar al vecino
    cajas = {}
    for nid, (x, y) in POSICIONES.items():
        datos = campana.nodo(nid)
        radio = 46 if datos["tipo"] != "eleccion" else 38
        w = ancho_texto(datos["titulo"], 7)
        cajas[nid] = (x - w // 2, y + radio + 14 - 10, w, 20)
    nombres = list(cajas)
    for i in range(len(nombres)):
        for j in range(i + 1, len(nombres)):
            ax, ay, aw, ah = cajas[nombres[i]]
            bx, by, bw, bh = cajas[nombres[j]]
            if ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah:
                fallos.append(f"mapa: titulos solapados: {nombres[i]} / {nombres[j]}")
    # nombre del rival dentro del circulo (radio 46 -> 92px)
    for f in facciones.orden_facciones():
        p = desborda(facciones.nombre(f), 6, 92, f"mapa circulo: {f}")
        if p:
            fallos.append(p)
        p = desborda(facciones.corto(f), 9, 92, f"mapa circulo corto: {f}")
        if p:
            fallos.append(p)
    # panel SIGUIENTE: textos con nombres reales
    for f in facciones.orden_facciones():
        estado = {"faccion": f, "nodo": "senda", "ruta": [], "cartas": [],
                  "victorias": 0, "derrotas": 0, "aliados": []}
        info = campana.info_duelo(estado)
        for texto, tam in (
                (f"SIGUIENTE: {info['titulo'].upper()}", 10),
                (f"Rival: {info['nombre']} ({info['nombre_faccion']})   Dificultad {info['dificultad']}", 8)):
            p = desborda(texto, tam, 460, f"mapa panel: {f}")
            if p:
                fallos.append(p)
    # tira del mazo: 5 + "+N mas" (el codigo la dibuja asi)
    p = desborda("+5 mas", 8, 50, "mapa mazo +N")
    if p:
        fallos.append(p)
    return fallos


def revisar_encuentros():
    fallos = []
    for enc in campana.ENCUENTROS:
        p = desborda(enc["titulo"], 18, 1000, f"encuentro titulo: {enc['id']}")
        if p:
            fallos.append(p)
        p = exceso_lineas(enc["texto"], 10, 840, 6, f"encuentro texto: {enc['id']}")
        if p:
            fallos.append(p)
        for op in enc["opciones"]:
            p = exceso_lineas(op["texto"], 8, 280, 5, f"encuentro op: {enc['id']}/{op['id']}")
            if p:
                fallos.append(p)
    return fallos


def revisar_ficha_nodo():
    fallos = []
    for nid, datos in list(campana.NODOS.items()) + list(campana.NODOS_MINI.items()):
        p = desborda(datos["titulo"], 14, 500, f"ficha_nodo titulo: {nid}")
        if p:
            fallos.append(p)
        y = 180 + 140
        for previa in datos.get("previa", []):
            y += 18 * len(envolver(previa, 8, 460))
        if y > 180 + 380 - 40:
            fallos.append(f"ficha_nodo: previas hasta y={y}: {nid}")
    for rival, d in campana.DUELISTAS.items():
        for clave in ("nombre", "entrada", "captura_player", "captura_cpu", "win", "lose"):
            v = d.get(clave, "")
            if not v:
                continue
            tam, ancho = (10, 500) if clave == "nombre" else (8, 500)
            p = desborda(f"- {v}" if clave == "entrada" else v, tam, ancho,
                         f"ficha_nodo/duelo: {rival}/{clave}")
            if p:
                fallos.append(p)
    return fallos


def revisar_elegir_rama():
    fallos = []
    for rama, datos in campana.NODOS["bifurcacion"]["opciones"].items():
        for previa in datos.get("previa", []):
            p = exceso_lineas(previa, 9, 412, 4, f"rama previa: {rama}")
            if p:
                fallos.append(p)
        p = exceso_lineas(datos["resumen"], 9, 400, 4, f"rama resumen: {rama}")
        if p:
            fallos.append(p)
    for recompensas in campana.RECOMPENSAS.values():
        linea = "RECOMPENSAS: " + ", ".join(
            {"entrenamiento": "entrenamiento", "recluta": "recluta",
             "sigilo": "sigilo", "aliado": "pacto",
             "sobre": "sobre"}[r] for r in recompensas)
        p = desborda(linea, 7, 440, "rama recompensas")
        if p:
            fallos.append(p)
    return fallos


def revisar_epilogo():
    fallos = []
    # pactos envueltos en 800px centrados (el codigo usa parrafo)
    todas = ", ".join(facciones.nombre(f) for f in facciones.orden_facciones())
    p = exceso_lineas(f"Pactos: {todas}", 10, 800, 4, "epilogo pactos (peor caso)")
    if p:
        fallos.append(p)
    return fallos


def revisar_sobre():
    fallos = []
    # 3 cartas: x = centro - 180 + i*120, 104 de ancho
    for i in range(3):
        p = fuera_pantalla((ANCHO // 2 - 180 + i * 120, 250, 104, 144),
                           f"sobre: carta {i}")
        if p:
            fallos.append(p)
    # linea de duplicadas con los nombres mas largos del juego
    nombres = sorted((c.nombre for cartas in mazos.TODOS.values() for c in cartas),
                     key=len, reverse=True)[:3]
    linea = "Duplicadas (+1): " + ", ".join(nombres)
    p = exceso_lineas(linea, 9, 600, 3, "sobre duplicadas (peor caso)")
    if p:
        fallos.append(p)
    return fallos


def revisar_tienda():
    fallos = []
    for r in [(ANCHO // 2 - 200, 200, 400, 220),
              (ANCHO // 2 - 160, 450, 320, 54),
              (ANCHO // 2 - 130, 520, 260, 44)]:
        p = fuera_pantalla(r, "tienda")
        if p:
            fallos.append(p)
    for texto, tam in (("SOBRE DE CARTAS", 12),
                       ("3 cartas al azar del pool", 9),
                       ("Legendaria ~10% - pity al 10", 8),
                       (f"Precio: {campana.PRECIO_SOBRE} moneda", 10),
                       ("Sobres sin legendaria: 9/9", 8),
                       ("Sin moneda: gana duelos de campana", 9)):
        p = desborda(texto, tam, 380, "tienda")
        if p:
            fallos.append(p)
    p = fuera_pantalla((ANCHO - 300, 596, 260, 50), "mapa: boton tienda")
    if p:
        fallos.append(p)
    return fallos


def revisar_armar_mazo():
    fallos = []
    # fila de 10 a escala 0.7 (73 de ancho, paso 120)
    for i in range(10):
        p = fuera_pantalla((ANCHO // 2 - 600 + i * 120, 200, 73, 101),
                           f"armar_mazo: carta {i}")
        if p:
            fallos.append(p)
    for r in [(90, 360, 220, 40),
              (ANCHO // 2 - 160, 360, 64, 40), (ANCHO // 2 + 96, 360, 64, 40),
              (ANCHO // 2 - 350, 690, 330, 54), (ANCHO // 2 + 20, 690, 330, 54)]:
        p = fuera_pantalla(r, "armar_mazo: control")
        if p:
            fallos.append(p)
    # contadores y motivo con textos largos
    for texto, tam, ancho in (
            ("MAZO 10/10  -  LEG 1/1  -  RARA 3/3", 10, 1200),
            ("Mazo lleno (10): quita una primero", 9, 1200),
            ("BANDO: ELFOS NOCTURNOS", 8, 200)):
        p = desborda(texto, tam, ancho, "armar_mazo")
        if p:
            fallos.append(p)
    return fallos


def revisar_coleccion_nav():
    fallos = []
    for r in [(310, 574, 190, 32), (510, 574, 190, 32), (710, 574, 56, 32),
              (862, 574, 56, 32)]:
        p = fuera_pantalla(r, "coleccion: control")
        if p:
            fallos.append(p)
    for r in [(ANCHO // 2 - 160, 640, 64, 40), (ANCHO // 2 + 96, 640, 64, 40),
              (ANCHO // 2 - 160, 560, 64, 40), (ANCHO // 2 + 96, 560, 64, 40)]:
        p = fuera_pantalla(r, "mejora/reemplazo: paginador")
        if p:
            fallos.append(p)
    # ficha ampliada: carta 1.6 (166x230) + panel 400x230
    p = fuera_pantalla((ANCHO // 2 - 330, 240, 166, 230), "ficha carta")
    if p:
        fallos.append(p)
    p = fuera_pantalla((ANCHO // 2 - 140, 240, 400, 230), "ficha panel")
    if p:
        fallos.append(p)
    mas_larga = max((c.nombre for cartas in mazos.TODOS.values() for c in cartas),
                    key=len)
    p = desborda(mas_larga, 13, 360, "ficha nombre (peor caso)")
    if p:
        fallos.append(p)
    return fallos


def revisar_ayuda_derrota():
    fallos = []
    lineas = [
        "Raton: arrastra una carta de la mano al tablero.",
        "Raton sobre una carta: la levanta y muestra la mejor casilla.",
        "Clic: continuar en las cinematicallyas y los menus.",
        "ESC: pausa dentro del duelo, cerrar una pantalla.",
        "Flechas y ENTER: moverse por los menus.",
        "H: recordatorio de Same y Plus.",
        "T: abrir el tutorial completo.",
        "Basica: ganas la carta vecina si tu lado es mayor.",
        "Same: dos vecinos con el mismo valor Capture.",
        "Plus: dos comparaciones con la misma suma capturan.",
        "Cadena: una carta capturada sigue capturando.",
        "Muro: su mejor lado no puede caer.",
        "Furia: +1 a cada lado si toca una carta amiga.",
        "Embestida: +2 en la casilla central.",
        "Sinergia: 3+ cartas de tu bando dan +1 a todo.",
        "Empatar cuenta como ganar el duelo.",
        "Tu racha se rompe. Duelos ganados: 99  -  Reintentos: 99",
    ]
    for linea in lineas:
        p = desborda(linea, 10, 1200, "ayuda/derrota")
        if p:
            fallos.append(p)
    return fallos


def auditar():
    pygame.init()
    problemas = []
    for nombre, fn in (("selector", revisar_selector),
                       ("coleccion", revisar_coleccion),
                       ("cartas", revisar_cartas),
                       ("cinematicas", revisar_cinematicas),
                       ("tutorial", revisar_tutorial),
                       ("duelo", revisar_duelo),
                       ("menu", revisar_menu),
                       ("mapa_mini", revisar_mapa_mini),
                       ("mapa", revisar_mapa),
                       ("encuentros", revisar_encuentros),
                       ("ficha_nodo", revisar_ficha_nodo),
                       ("elegir_rama", revisar_elegir_rama),
                       ("epilogo", revisar_epilogo),
                       ("sobre", revisar_sobre),
                       ("armar_mazo", revisar_armar_mazo),
                       ("tienda", revisar_tienda),
                       ("coleccion_nav", revisar_coleccion_nav),
                       ("ayuda_derrota", revisar_ayuda_derrota)):
        try:
            problemas += [f"[{nombre}] {p}" for p in fn()]
        except Exception as exc:  # noqa: BLE001 - la auditoria no debe morir
            problemas.append(f"[{nombre}] ERROR al auditar: {exc!r}")
    return problemas


def main():
    problemas = auditar()
    if problemas:
        print(f"\nAUDITORIA VISUAL: {len(problemas)} problemas:")
        for p in problemas:
            print(f"  - {p}")
        return 1
    print("\nAuditoria visual: sin desbordes ni elementos fuera de lugar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
