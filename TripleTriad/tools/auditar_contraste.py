"""G2: auditor de contraste sobre los FONDOStiles REALES.

Por que este fichero y no un calculo de tabla: el requisito es "contraste
medido en fondos reales". Un texto no se lee contra `PANEL`, se lee contra lo
que queda debajo despues de componerse: el fondo, la capa de oscurecido, la
vineta, el panel y la propia sombra del texto. Medir el color nominal del
panel da un numero y no dice nada de lo que el jugador ve de verdad.

Como funciona, sin mockear el juego:
1. Reproduce pantallas de verdad con el driver de video falso, con `MEDIR` a
   True. Cada `texto`, `panel` y `Boton.dibujar` deja su rect real en
   `ui._REGISTRO_TODOS` porque `_volcar_frame` se engancha a `display.flip`.
2. Para cada rect de texto, vuelve a pintar SOLO ese rect sin el texto y lee los
   pixeles resultantes: eso es el fondo compuesto real bajo esas letras.
3. Calcula el ratio WCAG entre el color del texto y ese fondo.

Uso:
    python tools/auditar_contraste.py            # informe
    python tools/auditar_contraste.py --json     # salida para maquinas
"""

import argparse
import contextlib
import json
import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

_tmp = tempfile.TemporaryDirectory(prefix="tt_contraste_")
os.environ["TRIPLETRIAD_DATA"] = _tmp.name

import pygame  # noqa: E402

import campana  # noqa: E402
import opciones  # noqa: E402
import pantallas  # noqa: E402
import ui  # noqa: E402
from ui import ALTO, ANCHO  # noqa: E402


# ------------------------------------------------------------- matematica WCAG
def _canal(c):
    """Canal sRGB a lineal, segun la formula de WCAG 2.x."""
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminancia(rgb):
    """Luminancia relativa WCAG de un color opaco."""
    r, g, b = (_canal(x) for x in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(sobre, fondo):
    """Ratio WCAG entre dos colores, 1.0..21.0."""
    a, b = luminancia(sobre), luminancia(fondo)
    claro, oscuro = max(a, b), min(a, b)
    return (claro + 0.05) / (oscuro + 0.05)


def luminancia_media(sup, rect=None, paso=4):
    """Luminancia media de los pixeles de `rect` (o de toda la surface)."""
    if rect is not None:
        rect = rect.clip(sup.get_rect())
        if rect.w <= 0 or rect.h <= 0:
            return 0.0
        sup = sup.subsurface(rect)
    tot, n = 0.0, 0
    for y in range(0, sup.get_height(), paso):
        for x in range(0, sup.get_width(), paso):
            tot += luminancia(sup.get_at((x, y))[:3])
            n += 1
    return tot / n if n else 0.0


def fondos_del_rect(copia, rect):
    """(color medio, color extremo) del fondo bajo `rect`.

    El MEDIO es la cifra principal: es lo que integra el ojo detras de las
    letras, y es lo que supone WCAG cuando el fondo es razonablemente uniforme.

    El EXTREMO (el pixel mas claro y mas oscuro) se reporta aparte como aviso.
    Usar el extremo como veredicto seria injusto: en un fondo pixel-art un solo
    destello hundiria el contraste de un texto perfectamente legible, y el
    resultado seria un informe inservible.
    """
    rect = rect.clip(copia.get_rect())
    if rect.w <= 0 or rect.h <= 0:
        return None, None
    suma = [0, 0, 0]
    claro, oscuro = -1.0, 2.0
    claro_c = oscuro_c = None
    n = 0
    for y in range(rect.y, rect.bottom):
        for x in range(rect.x, rect.right):
            c = copia.get_at((x, y))[:3]
            suma[0] += c[0]
            suma[1] += c[1]
            suma[2] += c[2]
            n += 1
            l = luminancia(c)
            if l > claro:
                claro, claro_c = l, c
            if l < oscuro:
                oscuro, oscuro_c = l, c
    medio = (suma[0] // n, suma[1] // n, suma[2] // n)
    return medio, (claro_c, oscuro_c)


#: Colores del frame EN CURSO, y pares (rects, colores) ya cerrados.
#: `_instrumentando` apila el color de cada texto en `_COLORES_FRAME` y el
#: observador de flip de `ui` cierra el par. Rect y color tienen que ser del
#: MISMO frame para poder emparejarlos por posicion: antes los rects venian de
#: `_REGISTRO_TODOS` (que acumula todos los frames) y los colores de la lista
#: que se vaciaba por pantalla, y salian 234 colores para 78 rects.
_COLORES_FRAME = []
_FRAMES_CERRADOS = []


def _cerrar_frame(frame):
    """Observador de `ui`: cierra el par (rects, colores) de este frame."""
    if not frame:
        return
    _FRAMES_CERRADOS.append((list(frame), list(_COLORES_FRAME)))
    del _COLORES_FRAME[:]


class Reloj:
    """Reloj congelado: el frame se dibuja y se corta."""

    def __init__(self):
        self.n = 0

    def tick(self, fps=60):
        self.n += 1
        return 16


#: Modulos que hacen `from ui import texto`. Todos ellos deben quedar mudos a
#: la vez: si se neutraliza solo uno, el resto sigue escribiendo el texto y la
#: medicion vuelve a contaminarse.
_MODULOS_CON_TEXTO = ("ui", "pantallas", "partida", "cartas", "cinematicas",
                      "tutorial", "duelistas", "finales", "prologo")


@contextlib.contextmanager
def _instrumentando(registro):
    """Anota el color REAL con el que se dibuja cada texto.

    Es imprescindible: medir los ocho colores de la paleta contra cada rect da
    numeros que no significan nada, porque cada rect se dibujo con uno solo. La
    lista de `registro` se llena en el MISMO orden en que `ui.registrar`
    apunta los rects, asi que se emparejan por posicion.
    """
    import importlib

    guardados = []

    def _envoltura(*a, **k):
        # `texto(screen, cadena, tam, color=TEXTO, ...)`: el color es el 4o.
        color = a[3] if len(a) > 3 else k.get("color", ui.TEXTO)
        cadena = a[1] if len(a) > 1 else k.get("cadena", "")
        registro.append((color, str(cadena)[:40]))
        return original_texto(*a, **k)

    original_texto = ui.texto
    try:
        for nombre in _MODULOS_CON_TEXTO:
            mod = sys.modules.get(nombre)
            if mod is None:
                mod = importlib.import_module(nombre)
            if hasattr(mod, "texto"):
                guardados.append((mod, mod.texto))
                mod.texto = _envoltura
        yield
    finally:
        for mod, original in guardados:
            mod.texto = original


@contextlib.contextmanager
def _sin_textos():
    """Pinta la pantalla sin escribir ni una letra (fondos y paneles si)."""
    import importlib

    guardados = []
    try:
        for nombre in _MODULOS_CON_TEXTO:
            mod = sys.modules.get(nombre)
            if mod is None:
                mod = importlib.import_module(nombre)
            if hasattr(mod, "texto"):
                guardados.append((mod, mod.texto))
                mod.texto = lambda *a, **k: None
        yield
    finally:
        for mod, original in guardados:
            mod.texto = original


def _es_legible(cadena):
    """True si el texto es algo que el jugador tiene que LEER.

    Filtra el adorno: un "-", un "+" o un "?" que dibuja una union entre nodos
    no es informacion, y exigirle contraste de cuerpo de texto lo convierte en
    un falso positivo que enseuria a ignorar el informe entero.
    """
    limpio = "".join(ch for ch in str(cadena) if not ch.isspace())
    if not limpio:
        return False
    return any(ch.isalnum() for ch in limpio)


def _nombre_color(c):
    """Nombre legible de un color, para el informe."""
    for etiqueta, ref in COLORES_A_MEDIR:
        if tuple(ref[:3]) == tuple(c):
            return etiqueta
    return "#%02X%02X%02X" % tuple(c)


# ----------------------------------------------------------------- pantallas
def _pintar_un_frame(dibujar, screen, max_frames=40):
    """Corre `dibujar` hasta que ha pintado al menos un frame completo.

    El bucle se queda un par de vueltas mas despues de que la pantalla haya
    ticked. Cortar en el primer `reloj.n >= 2` parecia suficiente porque casi
    todas las pantallas pintan antes de mirar eventos, pero `encuentro` primero
    lanza una cinematica y solo despues escribe: se quedaba sin un solo texto
    y la pantalla pasaba por medida con 0, o sea, sin medir.
    """
    import asyncio
    reloj = Reloj()

    async def correr():
        tarea = asyncio.ensure_future(dibujar(screen, reloj))
        settling = 0
        for _ in range(max_frames):
            await asyncio.sleep(0)
            if reloj.n >= 2:
                settling += 1
                if settling >= 3:
                    break
        tarea.cancel()
        try:
            await tarea
        except (asyncio.CancelledError, Exception):
            pass

    asyncio.run(correr())
    pygame.display.flip()


def pantallas_a_auditar():
    """(nombre, funcion de pintado) de cada pantalla que se mide."""
    estado = campana.nueva_campana("humano")
    campana.asegurar_coleccion("humano")
    campana.guardar(estado)
    import mazos

    return [
        ("menu", lambda s, r: pantallas.menu(s, r, estado)),
        ("mapa_campana", lambda s, r: pantallas.mapa_campana(s, r, estado)),
        ("tienda", lambda s, r: pantallas.tienda(s, r, estado)),
        ("coleccion", lambda s, r: pantallas.coleccion(s, r, estado)),
        ("recompensa", lambda s, r: pantallas.recompensa(s, r, estado, "senda")),
        ("revelar_sobre", lambda s, r: pantallas.revelar_sobre(
            s, r, mazos.HUMANOS[:1], [], {})),
        ("diario_dialogos", lambda s, r: pantallas.diario_dialogos(s, r, estado)),
        ("ajustes", lambda s, r: pantallas.ajustes(s, r)),
        ("elegir_rama", lambda s, r: pantallas.elegir_rama(s, r, estado)),
        ("draft", lambda s, r: pantallas.draft(s, r, estado, ofertas=mazos.HUMANOS[:3])),
        ("encuentro", lambda s, r: pantallas.encuentro(s, r, estado, "senda")),
    ]


#: Colores de texto que hay que ver legibles. El nombre es la etiqueta.
COLORES_A_MEDIR = [
    ("TEXTO", ui.TEXTO),
    ("TEXTO_ON", ui.TEXTO_ON),
    ("TEXTO_TENUE", ui.TEXTO_TENUE),
    ("DORADO", ui.DORADO),
    ("FOCO", ui.FOCO),
    ("EXITO", ui.EXITO),
    ("AVISO", ui.AVISO),
    ("ERROR", ui.ERROR),
]


def auditar(screen, corte_normal=4.5, corte_texto_grande=3.0):
    """Mide el contraste real de cada color de texto en cada pantalla."""
    import facciones

    pygame.display.set_mode((ANCHO, ALTO))
    # El enganche de `display.flip` es de un solo dueno (`ui.activar_medicion`).
    # Esta herramienta antes lo reescribia por su cuenta y se comia el de
    # `tests/auditoria_visual.py`, o al reves, segun el orden de importacion.
    ui.activar_medicion()
    ui.observar_flip(_cerrar_frame)
    resultados = []
    del SIN_MEDIR[:]
    try:
        for nombre, dibujar in pantallas_a_auditar():
            ui.limpiar_medicion()
            del _FRAMES_CERRADOS[:]
            del _COLORES_FRAME[:]
            with _instrumentando(_COLORES_FRAME):
                _pintar_un_frame(dibujar, screen)
            if not _FRAMES_CERRADOS:
                SIN_MEDIR.append(nombre)
                continue
            ultimos_rects, colores = _FRAMES_CERRADOS[-1]
            rects = [r for r, rol, _c in ultimos_rects if rol == "texto"]
            if not rects:
                # Sin esto, una pantalla que se deja de dibujar (o un enganche
                # de flip que se ha comido otro) mide cero textos y el
                # resumen sale "0 de 0, todo correcto": el falso verde mas
                # silencioso que hay. Medir cero es un fallo, no un aprobado.
                SIN_MEDIR.append(nombre)
                continue
            # El numero de colores y el de rects deben casar; si no, el
            # emparejamiento por posicion no vale y es mejor no medir que medir
            # mal.
            if len(colores) != len(rects):
                print(f"AVISO {nombre}: {len(colores)} colores para "
                      f"{len(rects)} rects; se omite")
                continue
            # FONDO COMPUESTO REAL: hay que repintar la pantalla SIN los textos.
            # Poner `MEDIR` a False NO sirve: esa bandera solo controla el
            # registro de rects, `texto()` sigue pintando igual. La unica forma
            # honesta de obtener el fondo es neutralizar el dibujo del texto
            # en todos los modulos que lo importan de `ui` (los botones y los
            # paragrafos llaman a ese mismo `texto`).
            _captura_con_textos = screen.copy()
            with _sin_textos():
                _pintar_un_frame(dibujar, screen)
            fondo_real = screen.copy()
            screen.blit(_captura_con_textos, (0, 0))
            peor_global = 21.0
            extremo_global = 21.0
            extremo_legible = 21.0
            locales_bajos = 0
            pixeles_bajos = []
            detalle = []
            decoracion = []
            for rect, (color, cadena) in zip(rects, colores):
                medio, extremos = fondos_del_rect(fondo_real, rect)
                if medio is None:
                    continue
                c = tuple(color[:3]) if isinstance(color, (tuple, list)) else tuple(color)[:3]
                valor = contraste(c, medio)
                extremo = min(contraste(c, extremos[0]), contraste(c, extremos[1]))
                etiqueta = _nombre_color(c)
                # Un guion o una interrogacion es decoracion, no texto que el
                # jugador lea: exigirle 4.5:1 a un "-" que une dos nodos del
                # mapa no dice nada sobre accesibilidad. Se mide igual, pero no
                # cuenta para el veredicto, y sale en el informe aparte.
                if _es_legible(cadena):
                    detalle.append((valor, etiqueta, tuple(rect), cadena))
                    peor_global = min(peor_global, valor)
                    extremo_legible = min(extremo_legible, extremo)
                    if extremo < corte_normal:
                        locales_bajos += 1
                        pixeles_bajos.append(
                            {"contraste_pixel": round(extremo, 2),
                             "contraste_medio": round(valor, 2),
                             "color": etiqueta, "rect": list(rect),
                             "texto": cadena})
                decoracion.append((valor, etiqueta, cadena))
                extremo_global = min(extremo_global, extremo)
            detalle.sort()
            resultados.append({
                "pantalla": nombre,
                "textos": len(rects),
                "contraste_minimo": round(peor_global, 2),
                "contraste_extremo": round(extremo_global, 2),
                "extremo_sobre_texto_legible": round(extremo_legible, 2),
                "textos_con_pixel_desfavorable": locales_bajos,
                "pixeles_bajos": pixeles_bajos,
                "cumple_normal": peor_global >= corte_normal,
                "cumple_texto_grande": peor_global >= corte_texto_grande,
                # Peores casos, para saber que color y donde arreglar: un
                # minimo sin localizar no dice nada.
                "peores": [
                    {"contraste": round(v, 2), "color": c, "rect": list(r),
                     "texto": t}
                    for v, c, r, t in detalle[:5]
                ],
            })
    finally:
        ui.MEDIR = False
        ui.limpiar_medicion()
        _ = facciones
    return resultados


#: Pantallas que no produjeron ningun texto medible. Se rellena dentro de
#: `auditar` y lo consulta `main`. Medir cero textos no es un aprobado: es un
#: dato que falta, y confundirlos daba un "todo correcto" con diez pantallas
#: sin medir.
SIN_MEDIR = []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="salida para maquinas")
    args = ap.parse_args()

    pygame.init()
    screen = pygame.display.set_mode((ANCHO, ALTO))
    opciones.invalidar()
    res = auditar(screen)

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    print("contraste medido sobre el FONDO COMPUESTO REAL (fondo + capas + panel),")
    print("contra la luminancia media de la zona donde se escribe.")
    print()
    print(f"{'pantalla':22} {'textos':>6} {'medio':>8} {'extremo':>9} "
          f"{'ext.legible':>11} {'pix.bajos':>10}  veredicto")
    print("-" * 96)
    fallos = 0
    for r in res:
        n = "OK " if r["cumple_normal"] else "NO "
        if not r["cumple_normal"]:
            fallos += 1
        print(f"{r['pantalla']:22} {r['textos']:>6} {r['contraste_minimo']:>8} "
              f"{r['contraste_extremo']:>9} "
              f"{r['extremo_sobre_texto_legible']:>11} "
              f"{r['textos_con_pixel_desfavorable']:>10}  {n}")
    print("-" * 96)
    print(f"pantallas por debajo de 4.5 (media): {fallos} de {len(res)}")
    total_pix = sum(r["textos_con_pixel_desfavorable"] for r in res)
    total_txt = sum(r["textos"] for r in res)
    print(f"pixeles desfavorables sobre texto legible: {total_pix} de {total_txt} textos")
    if SIN_MEDIR:
        print()
        print(f"PANTALLAS SIN MEDIR: {len(SIN_MEDIR)}: {', '.join(SIN_MEDIR)}")
        print("Una pantalla que no dibuja texto no es una pantalla correcta: el")
        print("contraste de 'esa' pantalla es desconocido, no bueno.")
    print()
    print("Nota: esta medicion NO es reproducible pixel a pixel. Los fondos tienen")
    print("estrellas y velos animados, de modo que el pixel mas desfavorable de un")
    print("mismo texto cambia entre ejecuciones (medido: 6 y 10 textos con algun")
    print("pixel bajo en dos ejecuciones seguidas). El veredicto se apoya en la")
    print("media de la zona, que si es estable; la columna 'pix' es el peor pixel")
    print("e individual y la mueven las particulas del fondo.")
    print()
    print("peores casos (color real del texto sobre el fondo medio de su zona):")
    for r in res:
        if r["cumple_normal"]:
            continue
        for p in r["peores"][:3]:
            x, y, w, h = p["rect"]
            print(f"  {r['pantalla']:16} {p['color']:12} {p['contraste']:>6}  "
                  f"({x},{y}) {w}x{h}  {p['texto']!r}")
    print()
    print("texto legible con algun pixel desfavorable (el color se pierde ahi):")
    for r in res:
        for p in r.get("pixeles_bajos", []):
            x, y, w, h = p["rect"]
            print(f"  {r['pantalla']:16} {p['color']:12} pix={p['contraste_pixel']:>5} "
                  f"medio={p['contraste_medio']:>5}  ({x},{y}) {w}x{h}  {p['texto']!r}")
    return 1 if SIN_MEDIR else 0


if __name__ == "__main__":
    sys.exit(main())