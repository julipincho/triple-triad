"""Script de grabación de gameplay en foreground para TripleTriad.

Lanza el juego en ventana real y captura la pantalla mientras se juega.
"""
import os
import sys
import time
import subprocess

import pyautogui
import mss
from PIL import Image

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gravedad_fg")
VIDEO_NAME = "gameplay_foreground.mp4"
CLIPS_NAME = "clips.json"
LANDING_NAME = "index_foreground.html"
MAX_SECONDS = 40
FPS = 15

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def find_game_window():
    """Busca la ventana de TripleTriad entre las ventanas de Windows."""
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

    # Paso 1: Lanzar el juego
    print("Lanzando TripleTriad.exe...")
    game_exe = os.path.join(PROJECT_ROOT, "TripleTriad.exe")
    if not os.path.exists(game_exe):
        print("No encontrado:", game_exe)
        return

    print("Proceso iniciado, PID:", proc.pid if 'proc' in dir() else "N/A")
    proc = subprocess.Popen([game_exe], shell=True)
    print("Proceso iniciado, PID:", proc.pid)
    print("Esperando 5s a que aparezca la ventana...")
    time.sleep(5)

    # Paso 2: Buscar y poner en primer plano
    print("\nBuscando ventana del juego...")
    game_win = find_game_window()
    if not game_win:
        print("No se encontró ventana de TripleTriad")
        print("Ventanas activas:")
        for w in pyautogui.getAllWindows()[:10]:
            print("  -", w.title[:60])
        proc.terminate()
        return

    print("Ventana encontrada:", game_win.title)
    print("Tamaño:", game_win.size)
    print("Posición:", game_win.topleft)

    print("Poniendo en primer plano...")
    try:
        game_win.activate()
        time.sleep(1)
        game_win.maximize()
        time.sleep(1)
    except Exception as e:
        print("No se pudo activar completamente:", e)

    print("\nPausa 3s para que veas la ventana...")
    time.sleep(3)

    # Paso 3: Grabar gameplay
    print("\nIniciando grabación de gameplay...")
    print("El juego debería estar visible en primer plano")
    print("Duración máxima:", MAX_SECONDS, "segundos")
    print("FPS:", FPS)

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        print("Monitor de captura: " + str(monitor["width"]) + "x" + str(monitor["height"]))

        frames_data = []
        start_time = time.time()
        frame_count = 0

        print("Grabando frames...")
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
            print("\nGrabación interrumpida por el usuario")

        print("Frames capturados:", len(frames_data))

    # Paso 4: Generar video
    print("\nEnsamblando video...")
    if len(frames_data) < 3:
        print("Pocos frames capturados (mínimo 3).")
        return

    frame_files = [f[1] for f in frames_data]
    print("Frames a incluir:", len(frame_files))

    from moviepy import ImageSequenceClip
    try:
        clip = ImageSequenceClip(frame_files, fps=FPS)
        video_path = os.path.join(OUTPUT_DIR, VIDEO_NAME)
        clip.write_videofile(video_path, fps=FPS, codec="libx264", verbose=False, logger=None)
        print("Video guardado:", video_path)
        if os.path.exists(video_path):
            size = os.path.getsize(video_path)
            print("Tamaño:", size, "bytes")
            print("Duración estimada:", len(frame_files) / FPS, "segundos")
    except Exception as e:
        print("Error generando video:", e)

    # Clips destacados
    print("\nGenerando clips destacados...")
    clips = {}
    try:
        if len(frame_files) >= 8:
            opening_paths = frame_files[:8]
            from moviepy import ImageSequenceClip
            clip = ImageSequenceClip(opening_paths, fps=FPS)
            opening_path = os.path.join(OUTPUT_DIR, "opening_foreground.webm")
            clip.write_videofile(opening_path, fps=FPS, codec="libvpx", verbose=False, logger=None)
            clips["opening"] = {"path": opening_path, "description": "Opening - primeros frames"}
            print("Clip opening generado")

        if len(frame_files) >= 8:
            final_paths = frame_files[-8:]
            clip = ImageSequenceClip(final_paths, fps=FPS)
            final_path = os.path.join(OUTPUT_DIR, "final_foreground.webm")
            clip.write_videofile(final_path, fps=FPS, codec="libvpx", verbose=False, logger=None)
            clips["final"] = {"path": final_path, "description": "Final - últimos frames"}
            print("Clip final generado")
    except Exception as e:
        print("Error generando clips:", e)

    # Landing page - escribir en archivo separado
    html_path = os.path.join(OUTPUT_DIR, LANDING_NAME)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("<html><head><title>TripleTriad Foreground</title>")
        f.write("<style>body{background:#0a0a0a;color:#e0e0e0;font-family:Arial;padding:2rem;}"
                ".video-wrapper{background:#111;padding:1rem;margin:1rem 0;}"
                ".video-wrapper video{width:100%;background:#000;}"
                ".clip-info{color:#a0a0a0;font-size:0.9rem;margin-top:0.5rem;}"
                ".footer{text-align:center;padding:2rem;color:#505050;font-size:0.8rem;}</style>")
        f.write("<head><meta charset='UTF-8'></head>")
        f.write("<body>")
        f.write("<h1>TripleTriad Gameplay (Foreground)</h1>")
        f.write("<p>Video grabado con la ventana en primer plano</p>")
        f.write("<div class='video-wrapper'>")
        f.write("<video width='640' controls>")
        f.write("<source src='" + VIDEO_NAME + "' type='video/mp4'>")
        f.write("Tu navegador no soporta video.")
        f.write("</source></video>")
        f.write("<div class='clip-info'>Video principal - " + str(MAX_SECONDS) + " segundos</div>")
        f.write("</div></div>")
        f.write("<div class='footer'>")
        f.write("Generado el " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        f.write("<br>OpenCode + TripleTriad</div>")
        f.write("</body></html>")
    print("Landing page guardada:", html_path)

    # Resumen final
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print("Video principal:", VIDEO_NAME)
    print("Frames capturados:", len(frames_data))
    print("Clips:", list(clips.keys()))
    print("Landing page:", LANDING_NAME)
    print("\nArchivos en:", OUTPUT_DIR)
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if f.endswith((".mp4", ".webm", ".png")):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            print("  -" + f + " (" + str(size) + " bytes)")
    print("\n¡Listo! Revisa el video generado.")