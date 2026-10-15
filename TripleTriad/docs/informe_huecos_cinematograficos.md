# Informe de imágenes faltantes — cinemáticas

**Alcance:** intro, prólogo, aperturas de facción y secuencias de final/epílogo. No incluye carteles de nodos, duelos, victorias/derrotas, encuentros, avatares ni eventos de campaña.

## Estado verificado

Fondos cinematográficos HD ya asignados: `salon_torneo.png`, `salon_torneo_lleno.png`, `revelacion_carta_torneo.png`, `portal_umbral_torneo.png`, `camino_lluvioso.png` y `sala_trono.png`. Cubren el torneo concurrido, la revelación, el portal visto desde el torneo, el camino lluvioso del despertar y el salón del trono.

Hay además fondos pixel-anime genéricos para varias claves (`amanecer`, `escenario`, `apagon`, `campamento`, `ruinas`, `trono`, `umbral`, entre otras). Los prompts de abajo piden **planos cinematográficos dedicados**, no implican que el juego esté sin imagen. Las claves se comparten entre cinemáticas distintas; cualquier integración futura debe asignarse por escena exacta, nunca reemplazar globalmente una clave.

El epílogo del mundo real usa deliberadamente `salon_torneo.png` en sus tres variantes. No se debe cambiar ese fondo globalmente. El único hueco específico detectado allí es un candidato exclusivo para el epílogo de caos, por los pinos que invaden el salón.

## Especificación común para ChatGPT

Generar cada imagen como **un PNG RGB de 1280×720**, fondo panorámico para videojuego 2D, estilo pixel-art anime JRPG consistente con los lotes HD aprobados: píxel limpio y legible, colores vibrantes donde corresponda, buena profundidad, sin texto, letras, interfaz, marcos, logotipos, cartas dibujadas, personajes en primer plano ni collage. Mantener espacio despejado en la zona inferior para la caja de diálogo. Entregar cada archivo con el nombre exacto indicado y conservar aparte el master original sin recortarlo ni sobrescribirlo.

## Prompts y nombres de integración sugeridos

Los prompts describen solo lo que el guion confirma; no añadir acontecimientos, personajes ni geografía no mencionados.

### Prioridad alta — intro y prólogo

1. **`intro_amanecer_mundo_antiguo.png`** — Intro: “Hubo un tiempo en que el mundo amanecía sin ceniza”. Paisaje fantástico amplio, luminoso y fértil antes de la guerra; amanecer cálido, sin grieta ni trono en primer plano. Debe diferenciarse del reino ya devastado de la apertura humana.
2. **`intro_grieta_umbral_cielo.png`** — Intro: “Entonces el cielo se rajó. Por la grieta asomó el Umbral”. Cielo fantástico abierto por una fisura dimensional, luz sobrenatural al otro lado; imagen de origen del conflicto, no el portal del salón real ni una puerta de piedra convencional.
3. **`intro_estandartes_siete_bandos.png`** — Intro: siete bandos preparan sus barajas. Gran plano de estandartes distintos frente a un horizonte de guerra; sin símbolos con texto, sin inventar emblemas reconocibles ni mostrar una facción como protagonista.
4. **`prologo_escenario_presentacion.png`** — Prólogo del torneo: escenario de la última ronda clasificatoria, con atril/luces y público al fondo. Mismo mundo real, iluminación fría y arquitectura de evento moderno que `salon_torneo_lleno.png`; no cambiar el plano aprobado del salón para las escenas que ya lo usan.
5. **`prologo_apagon_salon.png`** — Prólogo: “La luz se apaga”. El salón moderno del torneo inmediatamente después del corte: casi a oscuras, siluetas de mesas y escenario apenas legibles, sin portal visible ni destellos mágicos; conservar continuidad con el salón real.
6. **`prologo_campamento_nara.png`** — Prólogo: conversación y explicación de Nara. Refugio/campamento sencillo en el bosque, lugar íntimo para hablar y escribir; ambiente fantástico sobrio. No incluir castillo lejano, ruinas arcanas, Nara, el protagonista ni sucesos no narrados. Este archivo solo debe proponerse para las escenas concretas de Nara, no para toda escena con clave `campamento`.

### Prioridad media — aperturas cinematográficas de facción

El código comparte claves de fondo entre aperturas distintas. Para evitar que una imagen arruine otra, producir y asignar estos planos **por llamada de apertura**, no por reemplazo de `ceniza`, `campamento`, `ruinas`, `trono` o `umbral` en todas las pantallas.

7. **`apertura_humano_reino_en_cenizas.png`** — Reino humano: noche, cuatro murallas, reino reducido a cenizas; desolado, aún defendible.
8. **`apertura_orco_frontera_muralla.png`** — Orco: campamento al otro lado de una gran muralla fronteriza; tensión de invasión, sin mostrar una batalla que el texto no cuenta.
9. **`apertura_goblin_puerta_bajo_foso.png`** — Goblin: ruinas bajo un foso y una puerta antigua que acaba de abrirse; tono pícaro, sin representar a Grix ni a una horda en primer plano.
10. **`apertura_elfo_bosque_silencioso.png`** — Elfo: bosque antiguo que lleva siglos en silencio, una hoja distinta cae al amanecer; naturaleza contenida, no bosque genérico de aventura.
11. **`apertura_hombre_lobo_ciudad_lunar.png`** — Hombre lobo: ciudad bajo una luna que aparece antes del sol; contraste entre ciudad con agua y bosque hambriento, sin ilustrar un ataque explícito.
12. **`apertura_vampiro_cripta_pacto_roto.png`** — Vampiro: cripta y salón funerario nocturno que sugieran un pacto roto entre noche y tierra; paleta gótica, sin sangre explícita.
13. **`apertura_dragon_cielo_brasa.png`** — Dragón: cielo durante semanas del color de la brasa, silencio sin pájaros; paisaje quemado por luz y ceniza, sin mostrar al dragón.
14. **`apertura_elfo_nocturno_bosque_umbral.png`** — Elfo nocturno: bosque oscuro que expulsó a quienes miraban el Umbral; noche protectora, presencia dimensional sugerida, sin copiar el portal del torneo.
15. **`apertura_pantera_tejados_ciudad.png`** — Hombre pantera: tejados y calle urbana vistos desde arriba; sensación de que alguien ya estaba allí, sin mostrar ni siluetas humanoides ni estandartes de otra facción.
16. **`apertura_lagarto_pantano_ruinas.png`** — Hombre lagarto: pantano antiguo que emerge restos de un ejército y ruinas; fango, agua quieta y paciencia, sin confundirlo con las ruinas goblin.

### Prioridad media — desenlaces del Umbral

Son tres variantes narrativas que hoy comparten el fondo genérico `umbral`. Mantener las variantes aisladas; no tocar las asignaciones de epílogo real.

17. **`final_umbral_dominio_forzado.png`** — Dominio: grieta dimensional forzada, el salón del torneo se distingue al otro lado y una sombra ambigua cruza; no revelar qué es.
18. **`final_umbral_equilibrio_apertura.png`** — Equilibrio: abertura estrecha y estable entre ambos mundos, apenas suficiente para cruzar; sensación de control y despedida, no de destrucción.
19. **`final_umbral_caos_mundos_mezclados.png`** — Caos: bosque y salón del torneo superpuestos a través de una ruptura; composición legible que combine ambos espacios, sin convertirlo en un nuevo lugar canónico.
20. **`epilogo_caos_salon_invadio.png`** — Solo epílogo de caos: salón del torneo real con pinos del otro mundo creciendo entre las mesas; conservar la luz y distribución reconocibles del salón aprobado. No usar en los epílogos de dominio/equilibrio ni reemplazar `salon_torneo.png`.

## Nota de integración

Los nombres anteriores son IDs sugeridos e independientes. Para fondos HD, guardar candidatos en el área de candidatos del lote y registrar hashes; una futura aprobación debe enlazar el ID al índice/variante exacta de la cinemática. No copiar sobre los seis fondos aprobados ni alterar el guion para acomodar una imagen. Las propuestas de las cuatro primeras prioridades no invalidan los fondos de Lote 05, que siguen pendientes.
