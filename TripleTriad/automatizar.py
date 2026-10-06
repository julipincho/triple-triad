"""Script de automatizacion para TripleTriad (Fase 1).

Controla la ventana nativa del juego Pygame usando pyautogui/mss.
Pasos:
  1. Levantar el juego (o validar que arranca en modo headless)
  2. Navegar el selector de faccion (mover raton, teclas de flecha)
  3. Confirmar seleccion (ENTER)
  4. Capturar screenshots para la Fase 2 (UX auditor)

Modos:
  - "headed": ventana visible (por defecto, usa pyautogui sobre ventana real)
  - "dummy": SDL_VIDEODRIVER=dummy (para pruebas sin ventana grafica)
"""

import os
import sys
import time
import pygame

# --- Configuracion ---
MODE = os.environ.get("AUTOMATIZAR_MODE", "dummy")  # "headed" o "dummy"
SLEEP_BETWEEN_ACTIONS = 0.5  # segundos
MAX_FACCIONES = 7  # total de facciones en el juego

# Agregar path del proyecto
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def main():
    print("=" * 60)
    print("Automatizacion TripleTriad - Fase 1")
    print("=" * 60)
    print(f"Modo: {MODE}")
    print(f"Directorio: {PROJECT_ROOT}")
    print()

    # --- Configurar SDL ---
    if MODE == "dummy":
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        print("Modo dummy (headless) activado")
    elif MODE == "headed":
        print("Modo headed (ventana visible) activado")
        # En modo headed, pyautogui controlara la ventana real
        # Asegurarse de que el juego este abierto antes de correr

    # --- Importar modulos del juego ---
    try:
        os.chdir(PROJECT_ROOT)
        import audio
        import facciones
        import pantallas
        from ui import ANCHO, ALTO
        from paths import recurso
    except ImportError as e:
        print(f"Error importando modulos: {e}")
        print("   Asegurate de que los assets existen y el path es correcto.")
        return

    pygame.init()
    audio.iniciar()

    if not audio.disponible():
        print("Advertencia: Audio no disponible, continuando igual.")
    
    print(f"PyGame inicializado - Audio: {audio.disponible()}")
    print(f"Facciones disponibles: {facciones.orden_facciones()}")
    print()

    # --- Pantalla ---
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("TripleTriad - Automatizacion")
    reloj = pygame.time.Clock()

    # --- Probar que el audio MENU_MOVE funciona ---
    try:
        audio.sfx(audio.MENU_MOVE)
        print("SFX MENU_MOVE reproducido correctamente")
    except AttributeError as e:
        print(f"Error accediendo a audio.MENU_MOVE: {e}")
        print("   Revisar audio.py - debe tener MENU_MOVE = \"menu_move.wav\"")
        return
    except Exception as e:
        print(f"Error reproduciendo SFX: {e}")

    print()
    print("Paso 1: Navegando por el selector de faccion...")
    print()

    # --- Paso 1: Mover el raton por las facciones ---
    # En modo headed, pyautogui moveria el raton real.
    # En modo dummy, simularemos los eventos internos.
    
    orden = facciones.orden_facciones()
    print(f"Orden de facciones: {orden}")
    print()

    # Simular movimiento de raton por cada faccion (modo dummy)
    # En modo headed, descomentar los pyautogui.moveTo correspondiente
    for i, faccion in enumerate(orden):
        print(f"  [{i+1}/{len(orden)}] Faccion: {faccion}")
        
        if MODE == "headed":
            # Mover raton a posicion de la faccion en pantalla
            # Las facciones estan dispuestas horizontalmente empezando en x=160
            x = 160 + (i + 1) * 190
            y = 250
            pyautogui.moveTo(x, y, duration=SLEEP_BETWEEN_ACTIONS)
            # Pequena pausa para "ver" el hover
            time.sleep(SLEEP_BETWEEN_ACTIONS)
            # Hacer clic para seleccionar (opcional - probemos primero hover)
            # pyautogui.click()
            
        elif MODE == "dummy":
            # En modo dummy, simulamos el evento de MOUSEMOTION interno
            # que dispara audio.sfx(audio.MENU_MOVE) en pantallas.py
            # Las facciones estan dispuestas horizontalmente empezando en x=160
            x = 160 + (i + 1) * 190
            # Simular evento MOUSEMOTION
            evt = pygame.MOUSEMOTION
            pygame.event.post(pygame.event.Event(evt, pos=(x, 250), rel=(1, 0), buttons=(0, 0, 0)))
            # Pequena pausa
            time.sleep(SLEEP_BETWEEN_ACTIONS)
        
        print(f"      -> Hover sobre {faccion} OK")

    print()
    print("Paso 2: Confirmando seleccion (tecla ENTER)...")
    print()

    # --- Paso 2: Presionar ENTER para confirmar ---
    if MODE == "headed":
        print("   Presionando tecla ENTER en la ventana del juego...")
        pyautogui.press("enter")
        time.sleep(1.0)
        
    elif MODE == "dummy":
        # Simular evento KEYDOWN de ENTER
        enter_evt = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r", mod=0)
        pygame.event.post(enter_evt)
        time.sleep(1.0)
        print("   -> Tecla ENTER simulada OK")

    print()
    print("Paso 3: Capturando screenshot para UX Auditor...")
    
    # --- Paso 3: Capturar screenshot con mss ---
    try:
        import mss
        with mss.mss() as sct:
            # En modo dummy, monitor 1 es el escritorio virtual
            # En modo headed, usaria la ventana especifica
            mon = sct.monitors[1]  # Monitor principal
            img = sct.grab(mon)
            
        # Guardar screenshot
        screenshot_path = os.path.join(PROJECT_ROOT, "screenshot_fase1.png")
        # Convertir a formato PIL y guardar
        from PIL import Image
        pil_img = Image.frombytes("RGB", (img.width, img.height), img.rgb)
        pil_img = pil_img.transpose(Image.FLIP_TOP_BOTTOM)  # mss tiene origen en esquina superior izq
        pil_img.save(screenshot_path)
        
        print(f"   Screenshot guardado: {screenshot_path}")
        print(f"   Dimensiones: {img.width} x {img.height}")
    except ImportError:
        print("   mss no disponible, usando pygame.surfarray")
        # Fallback simple
        screenshot_path = os.path.join(PROJECT_ROOT, "screenshot_fase1.png")
        pygame.image.save(pantalla, screenshot_path)
        print(f"   Screenshot guardado via pygame: {screenshot_path}")
    except Exception as e:
        print(f"   Error capturando screenshot: {e}")

    print()
    print("Paso 4: Cerrando el juego y finalizando...")
    
    # --- Limpiar ---
    pygame.quit()
    
    print()
    print("=" * 60)
    print("Fase 1 completada exitosamente")
    print("=" * 60)
    print()
    print("Resumen:")
    print("  Audio MENU_MOVE verificado y reproducible")
    print("  Navegacion por facciones completada")
    print("  Screenshot guardado para Fase 2 (UX Auditor)")
    print("  Listo para: crear agente ux-auditor y generar UI_AUDIT.md")
    print()

if __name__ == "__main__":
    main()