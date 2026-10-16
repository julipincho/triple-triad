"""Ortografía de texto narrativo heredado; conserva claves, guion y nombres de usuario."""
from functools import lru_cache
import re
import unicodedata

# Sustituciones inequívocas del vocabulario del juego. No se acentúan
# automáticamente demostrativos ni palabras ambiguas como esta, el, si o tu.
_PALABRAS = dict(par.split('=') for par in '''
campana=campaña campanas=campañas ano=año anos=años manana=mañana
pequeno=pequeño pequena=pequeña pequenos=pequeños pequenas=pequeñas
acompanante=acompañante acompana=acompaña acompano=acompaño
acompanarte=acompañarte senala=señala senalar=señalar senal=señal
senales=señales dueno=dueño sueno=sueño engano=engaño
faccion=facción coleccion=colección decision=decisión decisiones=decisiones
tambien=también aqui=aquí alli=allí atras=atrás todavia=todavía
mas=más ningun=ningún algun=algún segun=según asi=así despues=después
capitan=capitán simbolos=símbolos desconfia=desconfía cortesia=cortesía
explicacion=explicación pregunta=pregunta juicio=juicio
tomara=tomará mirara=mirará cruzaria=cruzaría tendras=tendrás
habia=había podria=podría deberia=debería seria=sería estaba=estaba
energia=energía ultimo=último ultima=última ultimos=últimos
unico=único unica=única numero=número epilogo=epílogo prologo=prólogo
dialogo=diálogo vacio=vacío fria=fría grito=gritó
devolvertela=devolvértela devolvera=devolverá entendio=entendió
aprendio=aprendió perdio=perdió gano=ganó volvio=volvió
'''.split())
_INTERROGATIVOS = {'como': 'cómo', 'que': 'qué', 'quien': 'quién',
                   'quienes': 'quiénes', 'donde': 'dónde', 'cuando': 'cuándo',
                   'cuanto': 'cuánto', 'cuantos': 'cuántos', 'cual': 'cuál'}


def _caso(original, nuevo):
    return nuevo.upper() if original.isupper() else nuevo.capitalize() if original.istitle() else nuevo


@lru_cache(maxsize=4096)
def espanol(texto):
    """Se aplica a prosa fija ANTES de insertar el nombre del jugador."""
    texto = unicodedata.normalize('NFC', texto)
    texto = re.sub(r'\b[A-Za-z]+\b', lambda m: _caso(m[0], _PALABRAS.get(m[0].lower(), m[0])), texto)
    texto = texto.replace('No se que', 'No sé qué').replace('No se qué', 'No sé qué')
    texto = texto.replace('Ya se por que', 'Ya sé por qué')
    def pregunta(m):
        contenido = m[3]
        contenido = re.sub(r'^((?:(?:De|A|Por|Para|Con|En|Desde|Hasta)\s+)?)(Como|Que|Quien|Quienes|Donde|Cuando|Cuanto|Cuantos|Cual)\b',
                           lambda w: w[1] + _caso(w[2], _INTERROGATIVOS[w[2].lower()]), contenido, flags=re.I)
        contenido = re.sub(r'\bpor que\b', 'por qué', contenido)
        return m[1] + (m[2] or '') + '¿' + contenido
    return re.sub(r'(^|(?<=[.!])\s+|\n)([-—]\s*)?([^¿?\n.!]*\?)', pregunta, texto)
