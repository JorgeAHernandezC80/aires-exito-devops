# Bitácora de la EA2

Aquí voy anotando lo que hago, lo que me sale mal y cómo lo arreglo. La idea es que quede como
evidencia del proceso y también para no olvidarme yo de las cosas.

## 8 de noviembre de 2026 – Pasar el notebook a módulos

- Tenía todo el código de la EA1 en celdas de Colab, así que lo separé en un paquete
  `src/aires_exito/` con cinco archivos: `parser` (Beautiful Soup), `scraper` (Selenium),
  `limpieza`, `analisis` y `cli`.
- Algo que me sirvió mucho fue separar la paginación del navegador. Ahora la función
  `recorrer_paginas(obtener_html)` recibe otra función que le entrega el HTML de cada página.
  Así puedo usar Selenium cuando quiero datos en vivo, o archivos HTML guardados cuando quiero
  probar sin abrir Chrome (que es lo que va a pasar en el CI).
- Volví a sacar los datos el 8 de noviembre: **201 productos en 16 páginas** (la 17 ya sale
  vacía). En octubre, para la EA1, eran 190 productos en 15 páginas, o sea que el catálogo creció.

### Problemas que encontré revisando los datos (vienen desde la EA1)

1. **El vendedor sale con texto de más**: a veces queda pegado "Ver 1 oferta adicional". Por eso
   "Zona smart" me aparece como si fueran 4 vendedores distintos.
2. **Marcas raras**: salen cosas como ".Sso Lg", ".Ss1 Lg" o "A Fdac12222 Finlandek".
   Mirando el HTML entendí por qué: el texto del enlace trae el nombre **cortado**, y el pedazo
   que falta (".SSO", "A FDAC12222") queda entre el nombre y la marca, entonces la regex lo toma
   como si fuera parte de la marca. Lo bueno es que la tarjeta sí tiene un
   `<h3 class="styles_name__…">` con el nombre completo y otro `<h3 class="styles_brand__…">` con
   la marca.
3. **Mayúsculas**: el `.title()` que usábamos convierte "LG" en "Lg" y "TCL" en "Tcl".
4. Hay productos que no son aires acondicionados (ventiladores, deflectores, hasta combos de
   cocina) y se están metiendo en el análisis.

## 8 de noviembre de 2026 – Saber qué es realmente cada producto

- Agregué una variable `categoria` (Aire acondicionado, Enfriador portátil, Ventilador,
  Accesorio o repuesto, Otro) y otra `es_aire`. Me sorprendió el resultado: solo 101 de los 201
  productos son equipos de aire acondicionado. Lo demás son enfriadores pequeños, ventiladores,
  calentadores, válvulas y cosas así.
- También mejoré `tipo` para que reconozca "On/Off", "Onoff", "On Off" e "Inverte" (que es
  "Inverter" mal escrito por el vendedor).
- **Me equivoqué**: en la primera versión el "Aire Ac Port 12000BTU … ELECTROLUX" me quedaba como
  "Otro", y el "Mini Ventilador De Mesa" no entraba en ventiladores. Me di cuenta porque revisé los
  201 productos uno por uno y no solo los casos de prueba que yo había escogido. Los agregué como
  pruebas nuevas y corregí las reglas.
- **Otro error mío**: hice un reemplazo de texto con un script y no se aplicó, porque antes
  `ruff format` había partido la línea en varias. No salió ningún error, simplemente la prueba
  seguía en rojo. Tuve que revisar regex por regex hasta encontrarlo. Aprendí a usar una forma de
  editar que avise cuando no encuentra el texto.

## 8 de noviembre de 2026 – Pipeline, reporte y publicación

- **Hice el merge en la rama equivocada**: la primera vez que quise fusionar
  `test/pruebas-unitarias` estaba parado en esa misma rama. Git dijo "Already up to date" y no
  fusionó nada. Me cambié a `main` y lo repetí.
- **El linter revisaba el código viejo**: `ruff` me sacó 55 errores porque estaba revisando
  `legacy/`, y el `.py` que exporta Colab tiene líneas `!pip install` que no son Python válido.
  Excluí esa carpeta en `pyproject.toml`, porque ese código lo quiero guardar tal cual.
- **Versiones de las acciones**: leí que Node 20 dejó de tener soporte en abril de 2026, así que
  revisé con `git ls-remote` qué versiones existen de verdad y usé `checkout@v6`,
  `setup-python@v6`, `upload-pages-artifact@v5` y `deploy-pages@v5`.
- **actionlint me salvó**: encontró que el job `deploy` no tenía declarado `outputs.page_url`, y
  la prueba de humo lo necesita. Si no lo reviso antes, el error me habría salido ya en GitHub.
- **Revisé el reporte en el navegador** (en modo claro y oscuro): el valor de la barra más larga
  se cortaba ("$4.959.950 (n=2" sin cerrar) porque el margen derecho era fijo. Ahora se calcula
  según el largo del texto. El porcentaje de descuento también se partía en dos líneas y lo
  arreglé con `nowrap`.
- **Una prueba estaba mal pensada**: esperaba 6 equipos en el fixture y eran 5 (el Artic Air es
  un enfriador, no un equipo). El código estaba bien, la que estaba mal era mi expectativa.
- **Script para publicar**: lo probé primero con un `gh` falso y un repositorio remoto local. La
  primera prueba falló porque el script todavía no estaba en ningún commit, así que lo metí a
  `main` con la rama `chore/script-publicacion`. También cambié `${VAR,,}` (que solo funciona en
  bash 4) por `tr` para que sirva en macOS. Revisé además que los dos PRs pendientes se fusionan
  sin conflicto y con las 62 pruebas en verde.
- **Lo que no pude probar**: el scraping en vivo con Selenium, porque en el entorno donde trabajé
  no había Chrome ni acceso directo al sitio. El HTML del 8 de noviembre lo saqué con un servicio
  de renderizado en la nube y lo procesé con `python -m aires_exito desde-html`.
