"""Musica en el reproductor nativo del navegador, fuera del mezclador WASM."""
import base64
import json
from pathlib import Path


def controlar(accion, ruta=None, volumen=0.35, bucle=True):
    import platform
    if accion == 'play':
        uri = 'data:audio/ogg;base64,' + base64.b64encode(Path(ruta).read_bytes()).decode('ascii')
        script = (
            "if(window.__ttMusic){window.__ttMusic.pause();window.__ttMusic.src='';}"
            "window.__ttMusic=new Audio(" + json.dumps(uri) + ");"
            f"window.__ttMusic.volume={float(volumen)};window.__ttMusic.loop={str(bool(bucle)).lower()};"
            "window.__ttMusicError=null;((m)=>m.play().catch(e=>{if(window.__ttMusic===m && e.name!=='AbortError')window.__ttMusicError=String(e)}))(window.__ttMusic);"
        )
    elif accion == 'volume':
        script = f"if(window.__ttMusic)window.__ttMusic.volume={float(volumen)};"
    elif accion == 'pause':
        script = "if(window.__ttMusic)window.__ttMusic.pause();"
    elif accion == 'resume':
        script = "if(window.__ttMusic)((m)=>m.play().catch(e=>{if(window.__ttMusic===m && e.name!=='AbortError')window.__ttMusicError=String(e)}))(window.__ttMusic);"
    elif accion == 'stop':
        script = "if(window.__ttMusic){window.__ttMusic.pause();window.__ttMusic.src='';window.__ttMusic=null;}"
    else:
        raise ValueError(accion)
    platform.window.eval(script)
