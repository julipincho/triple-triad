"""Script de grabación de gameplay en foreground para TripleTriad."""

import os
import sys
import time
import json
import datetime
import subprocess

import pyautogui
import mss
from PIL import Image

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gravedad_fg")
VIDEO_NAME = "gameplay_foreground.mp4"
MAX_SECONDS = 40
FPS = 15

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def find_game_window():
    import pygetwindow as gw
    windows = [w for w in gw.getAllWindows() if "TripleTriad" in w.title]
    if not windows:
        return None
    for w in windows:
        if w.isVisible:
            return w
    return windows[0] if windows else None

def main():
    print("=" * 60)
    print("Fase 4: Grabación de Gameplay en Foreground")
    print("=" * 60)
    print()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Directorio de salida:", OUTPUT_DIR)
    print()

    # Lanzar el juego
    print("\\\\\\\\\\\\\\\\\\")
    print("▶️ Lanzando TripleTriad.exe...")
    game_exe = os.path.join(PROJECT_ROOT, "TripleTriad.exe")
    proc = subprocess.Popen([game_exe], shell=True)
    print("   Proceso iniciado, PID:", proc.pid)
    print("   Esperando 5s...")
    time.sleep(5)

    # Buscar ventana
    print("

🔍 Buscando ventana del juego...")
    game_win = find_game_window()
    if not game_win:
        print("❌ No se encontró ventana de TripleTriad")
        proc.terminate()
        return
    print("   ✅ Ventana encontrada:", game_win.title)
    print("   Tamaño:", game_win.size)
    print("   Posición:", game_win.topleft)

    # Poner en primer plano
    print("\\\\\\\\\\\\\\\\\\")
    print("   🔘 Poner en primer plano...")
    try:
        game_win.activate()
        time.sleep(1)
        game_win.maximize()
        time.sleep(1)
    except Exception as e:
        print("   ⚠️ No se pudo activar completamente:", e)

    print("

⏳ Pausa 3s para que veas la ventana...")
    time.sleep(3)

    # Grabar gameplay
    print("\\\\\\\\\\\\\\\\\\")
    print("▶️ Iniciando grabación de gameplay...")
    print("   Duración máxima:", MAX_SECONDS, "segundos")
    print("   FPS:", FPS)
    print()

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        print("   Monitor de captura:", "" + str(monitor["width"]) + "x" + str(monitor["height"]) + " @ (" + str(monitor["left"]) + ", " + str(monitor["top"]) + ")")

        frames_data = []
        start_time = time.time()
        frame_count = 0

        print("   Grabando frames...")
        try:
            while time.time() - start_time < MAX_SECONDS:
                img = sct.grab(monitor)
                from PIL import Image
                pil_img = Image.frombytes("RGB", (img.width, img.height), img.rgb)
                pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)
                frame_name = "frame_{:04d}".format(frame_count)
                frame_path = os.path.join(OUTPUT_DIR, frame_name + ".png")
                pil_img.save(frame_path)
                frames_data.append((time.time(), frame_path, frame_count))
                frame_count += 1
                time.sleep(1.0 / FPS)
                if frame_count % 20 == 0:
                    try:
                        pyautogui.move(5, 0)
                        pyautogui.move(-5, 0)
                    except Exception:
                        pass
        except KeyboardInterrupt:
            print()
            print("   ⏹️ Grabación interrumpida por el usuario")

        print()
        print("   Frames capturados:", len(frames_data))

    # Generar video
    print()
    print("\\\\\\\\\\\\\\\\\\")
    print("🎬 Ensamblando video...")
    if len(frames_data) < 3:
        print("❌ Pocos frames capturados (mínimo 3).")
        return
    frame_files = [f[1] for f in frames_data]
    print("   Frames a incluir:", len(frame_files))
    from moviepy import ImageSequenceClip
    try:
        clip = ImageSequenceClip(frame_files, fps=FPS)
        video_path = os.path.join(OUTPUT_DIR, VIDEO_NAME)
        clip.write_videofile(video_path, fps=FPS, codec="libx264", verbose=False, logger=None)
        print("✅ Video guardado:", video_path)
        if os.path.exists(video_path):
            size = os.path.getsize(video_path)
            print("   Tamaño:", size, "bytes")
            print("   Duración estimada:", len(frame_files) / FPS, "segundos")
    except Exception as e:
        print("❌ Error generando video:", e)

    # Clips destacados
    print()
    print("✂️ Generando clips destacados...")
    clips = {}
    try:
        if len(frame_files) >= 8:
            opening_paths = frame_files[:8]
            from moviepy import ImageSequenceClip
            clip = ImageSequenceClip(opening_paths, fps=FPS)
            opening_path = os.path.join(OUTPUT_DIR, "opening_foreground.webm")
            clip.write_videofile(opening_path, fps=FPS, codec="libvpx", verbose=False, logger=None)
            clips["opening"] = {"path": opening_path, "description": "Opening - primeros frames"}
            print("   Clip opening generado")
        if len(frame_files) >= 8:
            final_paths = frame_files[-8:]
            clip = ImageSequenceClip(final_paths, fps=FPS)
            final_path = os.path.join(OUTPUT_DIR, "final_foreground.webm")
            clip.write_videofile(final_path, fps=FPS, codec="libvpx", verbose=False, logger=None)
            clips["final"] = {"path": final_path, "description": "Final - últimos frames"}
            print("   Clip final generado")
    except Exception as e:
        print("   ⚠️ Error generando clips:", e)

    # Landing page - escribir en archivo separado
    html_path = os.path.join(OUTPUT_DIR, "index_foreground.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<html><head><title>TripleTriad Foreground</title></head>")
        f.write("<body><h1>Gameplay Grabado en Foreground</h1>")
        f.write("<p>Video: " + VIDEO_NAME + "</p>")
        f.write("<p>Frames capturados: " + str(len(frames_data)) + "</p>")
        f.write("</body></html>")
    print("
🌐 Landing page guardada:", html_path)

    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print("\\\\\\\\\\\\\\\\\\")
    print("Video principal:", VIDEO_NAME)
    print("Frames capturados:", len(frames_data))
    print("Clips:", list(clips.keys()))
    print("Landing page:", os.path.basename(html_path))
    print("
¡Listo! Revisa la carpeta", OUTPUT_DIR)
