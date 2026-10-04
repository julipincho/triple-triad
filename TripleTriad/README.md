# Triple Triad — Goblins vs Elfos

Juego de cartas estilo Triple Triad (Final Fantasy 8) en Python + pygame.

## Correr

- Ejecutable: `TripleTriad.exe` (doble click).
- Desde código: `python TripleTriad/main.py`

## Tests y auditoría visual

Cada cambio debe aprobarse así:

1. **Tests de reglas:**
   ```
   cd TripleTriad
   python -m unittest discover tests -v
   ```
2. **Demos visuales (screenshots):**
   ```
   python tests/demo_capturas.py
   ```
   Genera PNGs en `TripleTriad/auditoria/` para revisar tablero, capturas, cadena y solapamientos.

3. Recompilar el exe tras cambios en código o assets:
   ```
   cd TripleTriad
   python -m PyInstaller --onefile --windowed --name TripleTriad --add-data "cartas;cartas" --add-data "assets;assets" main.py
   ```

## Estructura

- `main.py` — GUI y loop de juego
- `reglas.py` — lógica de Triple Triad (capturas, cadena, simulación)
- `mazos.py` — mazos Goblins / Elfos
- `generar_cartas.py` — regenera arte de cartas con Pollinations
- `tests/` — tests de reglas y demos visuales
- `auditoria/` — screenshots generados
- `.env` — API key de Pollinations (no compartir)
