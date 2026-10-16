# Cartones y Mazmorras — versión 2.0

**Actualización: revisión web 1.** Volvé a subir el ZIP Web de esta carpeta si ya habías publicado la primera entrega 2.0. Incluye carga por bloques con progreso, música mediante el reproductor del navegador, efectos OGG, límite web de 30 FPS y reparación del mazo inicial. Windows conserva 60 FPS y también incluye la reparación del mazo.

## Archivos para subir

- `Cartones-y-Mazmorras-2.0-Windows.zip`: descarga para Windows de 64 bits.
- `Cartones-y-Mazmorras-2.0-Web.zip`: juego HTML5 para navegador.
- `Portada-2.0-630x500.png`: portada de la página.
- `Portada-2.0-1260x1000.png`: portada en resolución mayor.

## Configuración de itch.io

1. Creá o editá la página del juego y elegí **HTML Game** para permitir jugar en el navegador.
2. Subí el ZIP **Web** y marcá **This file will be played in the browser**. Su `index.html` está en la raíz.
3. Subí también el ZIP **Windows**, seleccioná la plataforma Windows y dejalo como descarga; no lo marques como jugable en el navegador.
4. Cargá `Portada-2.0-630x500.png` como imagen de portada.
5. Activá **Click to play** y el botón de pantalla completa. Usá un área de 1280 × 800 o lanzamiento en pantalla completa. Esta entrega se preparó para computadora; no anuncia compatibilidad móvil.
6. Identificá ambos archivos como **versión 2.0**. Revisá la vista previa de la página antes de publicarla.

Instrucciones oficiales: https://itch.io/docs/creators/html5

## Para quien descarga Windows

Extraer todo el ZIP en una carpeta y abrir `CartonesYMazmorras.exe`. No hace falta instalar Python. El paquete no incluye perfiles ni partidas personales. Los guardados nuevos se crean al jugar; si actualizás una instalación existente, conservá sus archivos de perfil y campaña.

## Novedades 2.0

Arte integrado para avatares y escenas revisadas, nuevo arte de derrota y escena ya vista, mapa de campaña mejorado, ajustes de lectura y distribución de pantallas, español con ñ y signos de apertura, selección de mejoras en dos filas y vaciado del editor de mazos manteniendo la validación de diez cartas. En las cartas se conserva el arte: solo se ajusta Embestida y se reubica el indicador de propietario.

## Alcance

La versión web descarga el entorno de Python/pygame desde el CDN HTTPS de pygame-web y requiere conexión durante la carga. El ZIP es un exportado para itch.io: no se abre haciendo doble clic en `index.html` desde el explorador.

La portada fue generada con `image_gen` usando el logo y el retrato del duelista como referencias. Los prompts y las pruebas técnicas se conservan en el proyecto, fuera de los ZIP de subida.
