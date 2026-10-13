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
| `salon_torneo_lleno.png` | Torneo activo, postduelo inmediato y público reunido para la presentación | `assets/fondos/salon.png` |
| `revelacion_carta_torneo.png` | La carta cambia por primera vez, después de anunciar El Umbral | `assets/fondos/umbral.png` |
| `portal_umbral_torneo.png` | Visión sobrenatural final antes del apagón | `assets/fondos/umbral.png` |

Los demás callsites con clave `camino` (campaña y variantes) no seleccionan el
fondo lluvioso. `campamento` permanece sin cambios. Masters y manifest original
del paquete están preservados fuera del repositorio en el staging aprobado.

Capturas del reproductor a 1280×800, generadas con pygame:
`capturas/cinematicas_hd/01_salon_prologo.png`,
`capturas/cinematicas_hd/02_camino_dialogo_retrato.png`,
`capturas/cinematicas_hd/03_sala_trono.png` y
`capturas/cinematicas_hd/04_salon_epilogo.png`.

## Planos pendientes del primer arco

- Primer plano de la carta física dentro de su caja, antes de activarse; los
  nuevos planos ya tienen magia visible y no sirven para esa fase.
- Detalle de los símbolos/bordes de la carta y plano de reacción del público.
- Apagón como transición progresiva y cruce visual del salón real al otro
  mundo; hoy el corte sigue usando la escena `apagon` original.
- Un plano de llegada/despertar distinto del camino general, si el próximo
  lote quiere separar el punto de vista del protagonista del paisaje.

No se modificó texto ni se adelantó la carta con efectos mágicos: la revelación
HD entra en “La carta central cambia”; el portal entra en la última frase de la
visión, inmediatamente antes de las escenas de apagón/transporte.
