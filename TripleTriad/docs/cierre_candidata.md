# Revision final de la candidata — 2026-10-10

**Entrega tecnica disponible para validacion: `dist/TripleTriad.exe`.**
El objetivo completo de produccion sigue pendiente de aceptacion humana y
del dispositivo de destino. No se certifica como completado por tener tests verdes.

## Ultimos cambios revisados

- El mercader aplica la mejora a la carta elegida mediante el selector existente.
- El sobre de la caravana muestra los cambios reales por carta y avisa
  `Al maximo: sin cambio`, sin prometer un incremento inexistente.
- Reparada la prueba que quedo fallando: ahora cualquier carta sorteada puede
  mejorar exactamente un punto; no depende de que salga un nombre concreto.
  Comprueba tres puntos entregados y cada texto `S: 4 -> 5` contra el recibo.
- Los tres modulos de pruebas nuevos aislan sus datos por caso y restauran el
  generador aleatorio. La prueba del encuentro ya no oculta excepciones ni
  acepta un bucle que no termina. Las pruebas de robo y sobre ahora comprueban
  entregas, no solo que el mazo existe o que aparece un titulo.
- El robo usa cartas de la faccion del jugador y aliados; corregido el texto
  anterior que prometia cualquier faccion. Los sobres si usan todo el catalogo.
- Corregidas afirmaciones desfasadas de README, G9 y limites de soporte:
  artefacto web existente pero antiguo, sigilo temporal, probabilidades de
  sobres y alcance real de las pruebas del ejecutable.
- No se editaron assets artisticos en esta revision. Los dos avatares ya
  modificados en el arbol se conservaron. No se hizo commit ni push.

## Evidencia ejecutada en esta revision

Comandos desde `E:\openCode\TripleTriad`, con Python 3.12.10:

| Comprobacion | Resultado observado | Alcance |
|---|---|---|
| `python -B -m unittest discover -s tests -p "test_*.py"` | 976 pruebas, OK, 67.055 s | Codigo fuente; SDL dummy |
| `python -B tools/recorridos_g9.py` | 7/7 sin problemas | Flujos automatizados con datos temporales |
| `python -m PyInstaller --noconfirm TripleTriad.spec` | Build completado | Ejecutable Windows actualizado |
| `dist/TripleTriad.exe --check` | Codigo 0; ningun recurso ausente | Recursos empaquetados |
| `dist/TripleTriad.exe --test` | Codigo 0; sin `crash.log` | Arranque de duelo; SDL dummy |

Los comandos del ejecutable utilizaron `TRIPLETRIAD_DATA` temporal,
`SDL_VIDEODRIVER=dummy` y `SDL_AUDIODRIVER=dummy`. El aviso de falta de renderer
rapido es esperable en ese entorno. La suite emite avisos de limpieza de
temporales; las excepciones de la pantalla ficticia `rota` son casos negativos
del auditor, no errores silenciados de una pantalla del juego.

Binario: 49 254 501 bytes. SHA-256:

```
b0d99fc246b8183303a908cc57af2c552cb2d8e052824ea880d503aebafa674a
```

## Matriz del objetivo y limites de la evidencia

Las rutas de pruebas de esta tabla son relativas a `tests/`. Todas estan
incluidas en la ejecucion de 976 pruebas. Una fila automatizada no acredita
por si sola usabilidad humana ni rendimiento del dispositivo.

| Hito y requisitos | Artefactos / pruebas | Estado de aceptacion |
|---|---|---|
| G1: base y deltas; editor sin doble mejora; victoria, premio, recompensa y final reanudables; compra con un cobro y una entrega; escritura atomica y errores visibles; abandono sin moneda | `campana.py`, `persistencia.py`, `main.py`; `test_integridad_progreso.py`, `test_partida_danada.py` | Cobertura automatizada de fallos, reanudacion y persistencia aislada |
| G2: foco/seleccion, exito, aviso y error; faccion separada; propio/rival y captura por forma/texto; deshabilitados; contraste | `ui.py`, `cartas.py`, `partida.py`, `pantallas.py`; `test_propiedad_forma.py`, `test_capturas_propiedad.py`, `test_contraste.py` | Comprobaciones de pantallas y marcas; contraste limitado a pantallas auditadas |
| G3: clic-clic, arrastre, cancelar, teclado; turno; preview basico/Same/Plus/cadena/Muro; historial; movimiento reducido; pausa con clic | `partida.py`, `reglas.py`; `test_controles_duelo.py`, `test_reglas.py`, `test_habilidades.py` | Duelo completo automatizado por teclado y por clic; falta uso humano |
| G4: catalogo/poseidas; EN MAZO/NUEVA/NO POSEIDA; mejoras; filtros, busqueda, comparacion; limites y rareza; altas de draft/sobre conservadas | `campana.py`, `pantallas.py`; `test_coleccion.py`, `test_integridad_progreso.py`, `test_altas_mazo.py` | Validacion automatizada de coleccion/editor y altas |
| G5: saldo/coste/falta, compra deshabilitada; catalogo/garantia; probabilidad por sobre; duplicadas antes/despues/maximo; resumen/editor; desglose moneda; evaluar oferta directa | `test_sobres.py`, `test_integridad_progreso.py`, `test_sobre_maximo.py`, `test_economia.py`; `docs/informe_g8.md` | Logica y mensajes comprobados; no se introdujo oferta directa sin justificacion economica |
| G6: resumen al continuar; diario/relectura/saltar vistas; amistad sin repeticion; titulos narrativos; sigilo temporal y decisiones sin promesas falsas; consecuencias | `narrativa.py`, `campana.py`, `pantallas.py`; `test_ritmo_narrativo.py`, `test_continuidad_historia.py`, `test_promesas_encuentros.py`, `test_encuentro_efecto.py` | Pruebas de continuidad y efectos; ultimo encuentro revisado |
| G7: teclado en mapa/tienda/editor/recompensas/decisiones; volumen/pantalla persistentes; lectura y movimiento reducido; escalado y raton | `opciones.py`, `ui.py`; `test_accesibilidad.py`, `test_accesibilidad_extra.py`, `test_texto_ampliado.py`, `test_instrumentacion.py` | Layout y persistencia automatizados; escalado, coordenadas fisicas y resoluciones de destino pendientes |
| G8: motor/IA reales, semillas, faccion/nodo/inicio, mazos 5/10, mejoras/reintentos/compras, debilitar, intervalos emparejados y cuellos de botella | `tools/simular_g8.py`, `tools/economia_g8.py`, `docs/informe_g8.md`; `test_curva_dificultad.py`, `test_herramientas_medida.py`, `test_economia.py` | Informe reproducible existente; contraste con jugadores y calibracion humana pendientes |
| G9: suite, nuevo jugador/reanudar/derrota/reintento/compra/equipar/mejorar/final; capturas normal/error/foco/lectura; ejecutable/web; rendimiento; 5 personas; limites | `tools/recorridos_g9.py`, `capturas/`, `docs/informe_g9.md`, `docs/limites_soporte.md`, binario identificado arriba | Fuente y arranque empaquetado comprobados; no acredita campaña completa en ejecutable ni aceptacion humana |

Las capturas existentes son evidencia historica de los estados que muestran.
No se han regenerado para fingir una nueva revision visual de todas las pantallas.
Los cambios finales del sobre estan comprobados por contenido y valores;
su presentacion forma parte de la comprobacion manual siguiente.

## Puertas pendientes para cerrar el objetivo completo

1. **Cinco personas nuevas.** En el ejecutable identificado arriba, cada una
   debe completar primer duelo, explicar una captura, comprar/equipar una carta
   y reanudar sin asistencia. Registrar por tarea exito, ayuda e incidencias.
   Aceptacion: al menos cuatro completan todas las tareas sin ayuda. No hay
   resultados humanos disponibles; las simulaciones no los sustituyen.
2. **Equipo de destino y ventana real.** Registrar sistema, resolucion y escala
   del escritorio. Probar ventana/redimensionado/pantalla completa, clic sobre
   cartas y botones, texto grande y movimiento reducido. Completar los siete
   recorridos en el binario y comprobar que no hay perdida de progreso. Medir
   rendimiento durante esos recorridos, no solo el arranque. Incluir mercader
   y sobre de caravana con duplicadas al maximo.
3. **Alcance web.** Existe `build/web/index.html` y paquetes antiguos. No son
   una entrega actual validada. Si la web es objetivo de entrega, hace falta
   reconstruccion y prueba de recorridos/persistencia en navegador.

Por estas puertas externas, el objetivo global no se marca completado.
