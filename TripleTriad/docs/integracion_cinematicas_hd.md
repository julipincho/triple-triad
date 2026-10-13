# Fondos HD para cinemáticas

Los PNG aprobados de 1280×720 se guardan en `assets/cinematicas_hd/`; no
reemplazan `assets/fondos/`. El reproductor los presenta 1:1, centrados en el
lienzo lógico 1280×800 (origen 0,40). `TRIPLETRIAD_CINEMATICAS_HD=0` desactiva
el selector y recupera los fondos clásicos sin retirar los archivos nuevos.

Para un lote futuro, agregar los PNG aprobados al directorio y asignar
`fondo_hd="nombre.png"` solamente en los datos de las escenas autorizadas.
Si el archivo no está o la bandera está desactivada, el reproductor conserva
el fondo indicado por `fondo`, por lo que los lotes no requieren cambiar su
código. El cache de la presentación se separa por ruta, tamaño y viewport.

## Lote 01

| Archivo | Callsite integrado | Fallback clásico |
| --- | --- | --- |
| `salon_torneo.png` | Prólogo del torneo y tres epílogos de regreso al mundo real | `assets/fondos/salon.png` |
| `camino_lluvioso.png` | Despertar y encuentro inicial con Pik | `assets/fondos/camino.png` |
| `sala_trono.png` | Escenas de clave `trono` del prólogo y la campaña | `assets/fondos/trono.png` |

Los demás callsites con clave `camino` (campaña y variantes) no seleccionan el
fondo lluvioso. `campamento` permanece sin cambios. Masters y manifest original
del paquete están preservados fuera del repositorio en el staging aprobado.

Las capturas in-game requieren el runtime pygame disponible; no se deben
presentar previsualizaciones del PNG como capturas del juego.
