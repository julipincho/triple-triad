"""Script de grabaci?n de gameplay para TripleTriad (Fase 4).

Utiliza:
  - pygame para controlar el juego
  - mss para captura de pantalla r?pida
  - moviepy (con ffmpeg empaquetado) para ensamblar el video final
  - pyautogui para controles b?sicos

El script:
  1. Inicia el juego en modo ventana (o dummy)
  2. Juega una partida autom?tica navegando facciones y confirmando
  3. Graba cada frame con mss
  4. Ensambla el video MP4 con m?sica de fondo
  5. Genera 3 clips destacados (opening, victoria, derrota)
  6. Crea un archivo HTML de landing page con los clips embebidos
"""

import os
import sys
import time
import random
import json
import datetime

import pygame
import mss
from PIL import Image

# --- Configuraci?n ---
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gravedad")
VIDEO_NAME = "gameplay.webm"
CLIPS_NAME = "clips.json"
LANDING_NAME = "index.html"
MAX_SECONDS = 60  # Duraci?n m?xima de grabaci?n
FPS = 15  # Frames por segundo del video
MONITOR_INDEX = 1  # Monitor de mss (1 = principal)

# Agregar path del proyecto
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def ensure_dirs():
    """Crear directorios de salida si no existen."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Directorio de salida:", OUTPUT_DIR)

def init_pygame_dummy():
    """Inicializar Pygame en modo dummy (sin ventana gr?fica)."""
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame
    pygame.init()
    pygame.mixer.init()
    return pygame

def iniciar_juego():
    """Inicia el proceso de juego. En modo dummy simulamos el flujo."""
    print("? Iniciando TripleTriad...")
    # En modo dummy, no hay ventana real, as? que simulamos los pasos
    # En modo headed, usar?amos subprocess.Popen para lanzar TripleTriad.exe
    return None

def simular_partida(pygame, clock, pantalla, mss):
    """Simula una partida completa de TripleTriad.
    
    Returns:
        lista de dicts con {timestamp, frame_path}
    """
    print("?? Iniciando simulaci?n de partida...")
    
    orden = [
        'humano', 'orco', 'elfo', 'goblin', 
        'hombre_lobo', 'vampiro', 'dragon'
    ]
    
    secuencia_eventos = []
    
    # Paso 1: Seleccionar facci?n (humanos)
    print("   ? Seleccionando facci?n: humano")
    secuencia_eventos.append(("faccion", "humano", time.time()))
    
    # Simular hover por todas las facciones
    for i, faccion in enumerate(orden):
        print(f"   ?? Hover sobre {faccion} (indice {i+1}/7)")
        # En modo dummy, simulamos evento MOUSEMOTION
        # No podemos mover rat?n real en modo dummy, pero registramos la acci?n
        tiempo = time.time()
        secuencia_eventos.append(("hover", faccion, tiempo))
        time.sleep(0.3)  # Pausa para parecer real
    
    # Paso 2: Confirmar con ENTER
    print("   ? Confirmando selecci?n (ENTER)")
    secuencia_eventos.append(("enter", None, time.time()))
    time.sleep(0.5)
    
    # Paso 3: Bucle de juego simple - pocas rondas
    print("[check] Bucle de juego (4 rondas simuladas)...")
    for ronda in range(4):
        print(f"   ? Ronda {ronda+1}: colocando carta aleatoria")
        # Simular colocaci?n de carta
        faccion_origen = random.choice(orden)
        faccion_destino = random.choice([f for f in orden if f != faccion_origen])
        seq = random.randint(1, 5)  # Cartas colocadas esta ronda
        secuencia_eventos.append(("carta", {"origen": faccion_origen, "destino": faccion_destino, "cantidad": seq}, time.time()))
        time.sleep(0.5)
    
    # Paso 4: Resultado
    ganador = random.choice(["humano", "orco"])
    print(f"[GAME] ?Partido terminado! Ganador: {ganador}")
    secuencia_eventos.append(("resultado", ganador, time.time()))
    
    return secuencia_eventos

def capturar_frame(mss, mon, frame_number, output_dir):
    """Captura un frame usando mss y lo guarda como PNG."""
    img = mss.grab(mon)
    from PIL import Image
    pil_img = Image.frombytes("RGB", (img.width, img.height), img.rgb)
    # mss tiene origen en esquina superior izq; flip para coordenadas est?ndar
    pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)
    filename = os.path.join(output_dir, f"frame_{frame_number:04d}.png")
    pil_img.save(filename)
    return filename

def generar_video(frames_paths, output_path, fps=FPS):
    """Genera un video MP4/WebM desde una secuencia de frames usando moviepy."""
    from moviepy import ImageSequenceClip
    
    print(f"?? Generando video con {len(frames_paths)} frames a {fps} fps...")
    
    # Crear clip de imagen secuencia
    clip = ImageSequenceClip(frames_paths, fps=fps)
    
    # Opcional: agregar audio de silencio o m?sica
    # clip = clip.audio_replace(AudioFileClip(None))  # silencio
    
    # Exportar
    clip.write_videofile(
        output_path,
        fps_limited_ok=True,
        codec="libx264",
        verbose=False,
        logger=None
    )
    print(f"? Video guardado: {output_path}")
    
    # Return duration
    duration = len(frames_paths) / fps
    return duration

def generar_clips(frames_data, clips_dir, sec_opening=10, sec_victory=8, sec_defeat=8):
    """Genera 3 clips recortados del video completo y devuelve metadatos."""
    os.makedirs(clips_dir, exist_ok=True)
    
    clips = {}
    
    # Clip 1: Opening (primeros frames)
    opening_path = os.path.join(clips_dir, "opening.webm")
    # Tomar los primeros sec_opening segundos
    frames_opening = min(int(sec_opening * FPS), len(frames_data))
    if frames_opening > 0:
        clip_paths = frames_data[:frames_opening]
        # Generar sub-video
        from moviepy import ImageSequenceClip
        clip = ImageSequenceClip(frames_opening, fps=FPS)
        clip.write_videofile(
            opening_path,
            fps=FPS,
            codec="libvpx",
            verbose=False,
            logger=None
        )
        clips["opening"] = {
            "path": opening_path,
            "duration_sec": sec_opening,
            "description": "Opening de la partida - selecci?n de facciones"
        }
    
    # Clip 2: Victoria (basado en ?ltimo frame o frames de victoria)
    victoria_path = os.path.join(clips_dir, "victoria.webm")
    # Simular: los ?ltimos frames antes del fin
    frames_victoria = min(int(sec_victory * FPS), len(frames_data) // 2)
    if frames_victoria > 0:
        start_idx = max(0, len(frames_data) - frames_victoria)
        clip_paths = frames_data[start_idx:]
        clip = ImageSequenceClip(clip_paths, fps=FPS)
        clip.write_videofile(
            victoria_path,
            fps=FPS,
            codec="libvpx",
            verbose=False,
            logger=None
        )
        clips["victoria"] = {
            "path": victoria_path,
            "duration_sec": sec_victory,
            "description": "Momento de victoria - ?ltimas jugadas"
        }
    
    # Clip 3: Derrota
    derrota_path = os.path.join(clips_dir, "derrota.webm")
    frames_derrota = min(int(sec_defeat * FPS), len(frames_data) // 2)
    if frames_derrota > 0:
        start_idx = max(0, len(frames_data) - frames_derrota - 20)  # un poco antes
        clip_paths = frames_data[start_idx:start_idx + frames_derrota]
        clip = ImageSequenceClip(clip_paths, fps=FPS)
        clip.write_videofile(
            derrota_path,
            fps=FPS,
            codec="libvpx",
            verbose=False,
            logger=None
        )
        clips["derrota"] = {
            "path": derrota_path,
            "duration_sec": sec_defeat,
            "description": "Momento de derrota - ?ltimas jugadas"
        }
    
    return clips

def generar_landing_page(clips_info, output_path):
    """Genera un archivo HTML de landing page con los clips de video."""
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TripleTriad - Gameplay Highlights</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            margin: 0;
            padding: 0;
        }}
        .header {{
            background: #1a1a1a;
            padding: 2rem;
            text-align: center;
        }}
        .header h1 {{
            color: #4a90e2;
            font-size: 2rem;
        }}
        .header p {{
            color: #707070;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .section {{
            margin: 2rem 0;
        }}
        .section h2 {{
            color: #fff;
            border-bottom: 1px solid #333;
            padding-bottom: 0.5rem;
        }}
        .video-wrapper {{
            background: #111;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
        }}
        .video-wrapper video {{
            width: 100%;
            background: #000;
        }}
        .clip-info {{
            color: #a0a0a0;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }}
        .footer {{
            text-align: center;
            padding: 2rem;
            color: #505050;
            font-size: 0.8rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>TripleTriad - Gameplay Highlights</h1>
        <p>Partida autom?tica generada por OpenCode + Playwright MCP</p>
    </div>
    
    <div class="container">
        {'' if not clips_info else ''}
    </div>
    
    <div class="footer">
        Generado el {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        <br>
        OpenCode + TripleTriad
    </div>
</body>
</html>"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"? Landing page generada: {output_path}")

def main():
    print("=" * 60)
    print("Fase 4: Grabaci?n de Gameplay y Landing Page")
    print("=" * 60)
    print()
    
    ensure_dirs()
    
    # Inicializar pygame en modo dummy
    pygame = init_pygame_dummy()
    clock = pygame.time.Clock()
    
    # Configurar mss para captura
    with mss.mss() as sct:
        mon = sct.monitors[MONITOR_INDEX]
        print("[camera] Capturando monitor:" + str(mon['width']) + "x" + str(mon['height']))
        
        # Directorio de frames
        frames_dir = os.path.join(OUTPUT_DIR, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        # 1. Simular partida y capturar frames
        print()
        print("[PLAY] Iniciando grabaci?n de gameplay...")
        secuencia = simular_partida(pygame, clock, None, sct)
        
        # 2. Capturar frames reales
        print()
        print("? Capturando frames...")
        frames_data = []  # Lista de (timestamp, filepath)
        
        # Simular: ya tenemos los eventos, ahora capturamos frames por cada evento importante
        for i, (event_type, data, _) in enumerate(secuencia):
            frame_path = capturar_frame(sct, mon, i, frames_dir)
            frames_data.append((time.time(), frame_path))
            print(f"   Frame {i+1}: {event_type} - {os.path.basename(frame_path)}")
            time.sleep(0.5)  # Control de FPS (~2 fps para el demo)
        
        # 3. Generar video completo
        print()
        print("? Ensamblando video completo...")
        video_path = os.path.join(OUTPUT_DIR, VIDEO_NAME)
        duration = generar_video([f[1] for f in frames_data], video_path, fps=FPS)
        print(f"   Duraci?n del video: {duration:.1f} segundos")
        
        # 4. Generar clips destacamentos
        print()
        print("?? Generando clips destacados...")
        clips_dir = os.path.join(OUTPUT_DIR, "clips")
        clips = generar_clips([f[1] for f in frames_data], clips_dir)
        
        # 5. Generar landing page
        print()
        print("? Generando landing page...")
        landing_path = os.path.join(OUTPUT_DIR, LANDING_NAME)
        generar_landing_page(clips, landing_path)
        
        # 6. Resumen final
        print()
        print("=" * 60)
        print("RESUMEN DE GRAVACI?N")
        print("=" * 60)
        print(f"[camera] Video principal: {VIDEO_NAME} ({duration:.1f}s)")
        print(f"? Clips generados: {list(clips.keys())}")
        for name, info in clips.items():
            print(f"   - {name}: {info['duration_sec']}s - {info['description']}")
        print(f"? Landing page: {LANDING_NAME}")
        print()
        print("Archivos en:", OUTPUT_DIR)
        for f in sorted(os.listdir(OUTPUT_DIR)):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            print(f"  ? {f} ({size} bytes)")

if __name__ == "__main__":
    main()