# Bitácora de la EA2

Aquí fuimos anotando lo que hicimos, lo que nos salió mal y cómo lo arreglamos. La idea es que
quede como evidencia del proceso y también para que nadie del grupo se olvide de las cosas.

## 8 de noviembre de 2026 – Pasar el notebook a módulos

- Teníamos todo el código de la EA1 en celdas de Colab, así que lo separamos en un paquete
  `src/aires_exito/` con cinco archivos: `parser` (Beautiful Soup), `scraper` (Selenium),
  `limpieza`, `analisis` y `cli`.
- Algo que nos sirvió mucho fue separar la paginación del navegador. Ahora la función
  `recorrer_paginas(obtener_html)` recibe otra función que le entrega el HTML de cada página.
  Así podemos usar Selenium cuando queremos datos en vivo, o archivos HTML guardados cuando
  queremos probar sin abrir Chrome (que es lo que pasa en el CI).
- Volvimos a sacar los datos el 8 de noviembre: **201 productos en 16 páginas** (la 17 ya sale
  vacía). En octubre, para la EA1, eran 190 productos en 15 páginas, o sea que el catálogo creció.

### Problemas que encontramos revisando los datos (vienen desde la EA1)

1. **El vendedor sale con texto de más**: a veces queda pegado "Ver 1 oferta adicional". Por eso
   "Zona smart" aparecía como si fueran 4 vendedores distintos.
2. **Marcas raras**: salían cosas como ".Sso Lg", ".Ss1 Lg" o "A Fdac12222 Finlandek".
   Mirando el HTML entendimos por qué: el texto del enlace trae el nombre **cortado**, y el pedazo
   que falta (".SSO", "A FDAC12222") queda entre el nombre y la marca, entonces la regex lo toma
   como si fuera parte de la marca. Lo bueno es que la tarjeta sí tiene un
   `<h3 class="styles_name__…">` con el nombre completo y otro `<h3 class="styles_brand__…">` con
   la marca.
3. **Mayúsculas**: el `.title()` que usábamos convierte "LG" en "Lg" y "TCL" en "Tcl".
4. Hay productos que no son aires acondicionados (ventiladores, deflectores, hasta combos de
   cocina) y se estaban metiendo en el análisis.

## 8 de noviembre de 2026 – Saber qué es realmente cada producto

- Agregamos una variable `categoria` (Aire acondicionado, Enfriador portátil, Ventilador,
  Accesorio o repuesto, Otro) y otra `es_aire`. Nos sorprendió el resultado: solo 101 de los 201
  productos son equipos de aire acondicionado. Lo demás son enfriadores pequeños, ventiladores,
  calentadores, válvulas y cosas así.
- También mejoramos `tipo` para que reconozca "On/Off", "Onoff", "On Off" e "Inverte" (que es
  "Inverter" mal escrito por el vendedor).
- **Nos equivocamos**: en la primera versión el "Aire Ac Port 12000BTU … ELECTROLUX" quedaba como
  "Otro", y el "Mini Ventilador De Mesa" no entraba en ventiladores. Nos dimos cuenta porque
  revisamos los 201 productos y no solo los casos de prueba que habíamos escogido. Los agregamos
  como pruebas nuevas y corregimos las reglas.
- **Otro error**: hicimos un reemplazo de texto con un script y no se aplicó, porque antes
  `ruff format` había partido la línea en varias. No salió ningún error, simplemente la prueba
  seguía en rojo. Tocó revisar regex por regex hasta encontrarlo. Aprendimos a usar una forma de
  editar que avise cuando no encuentra el texto.

## 8 de noviembre de 2026 – Pipeline, reporte y publicación

- **Merge en la rama equivocada**: la primera vez que quisimos fusionar `test/pruebas-unitarias`
  estábamos parados en esa misma rama. Git dijo "Already up to date" y no fusionó nada. Nos
  cambiamos a `main` y lo repetimos.
- **El linter revisaba el código viejo**: `ruff` sacó 55 errores porque estaba revisando
  `legacy/`, y el `.py` que exporta Colab tiene líneas `!pip install` que no son Python válido.
  Excluimos esa carpeta en `pyproject.toml`, porque ese código lo queremos guardar tal cual.
- **Versiones de las acciones**: leímos que Node 20 dejó de tener soporte en abril de 2026, así
  que revisamos con `git ls-remote` qué versiones existen de verdad y usamos `checkout@v6`,
  `setup-python@v6`, `upload-pages-artifact@v5` y `deploy-pages@v5`.
- **actionlint nos salvó**: encontró que el job `deploy` no tenía declarado `outputs.page_url`, y
  la prueba de humo lo necesita. Si no lo revisamos antes, el error habría salido ya en GitHub.
- **Revisamos el reporte en el navegador** (en modo claro y oscuro): el valor de la barra más
  larga se cortaba ("$4.959.950 (n=2" sin cerrar) porque el margen derecho era fijo. Ahora se
  calcula según el largo del texto. El porcentaje de descuento también se partía en dos líneas y
  lo arreglamos con `nowrap`.
- **Una prueba estaba mal pensada**: esperaba 6 equipos en el fixture y eran 5 (el Artic Air es
  un enfriador, no un equipo). El código estaba bien, la que estaba mal era la expectativa.
- **Script para publicar**: lo probamos primero con un `gh` falso y un repositorio remoto local.
  La primera prueba falló porque el script todavía no estaba en ningún commit, así que lo metimos
  a `main` con la rama `chore/script-publicacion`. También cambiamos `${VAR,,}` (que solo funciona
  en bash 4) por `tr` para que sirva en macOS.
- **Lo que no pudimos probar**: el scraping en vivo con Selenium, porque en el entorno donde
  trabajamos no había Chrome ni acceso directo al sitio. El HTML del 8 de noviembre lo sacamos con
  un servicio de renderizado en la nube y lo procesamos con `python -m aires_exito desde-html`.

## 9 de noviembre de 2026 – Publicación en GitHub

- Al subir el repositorio, el primer Deploy falló en `configure-pages` porque GitHub Pages todavía
  no estaba activado en el repositorio. Las pruebas y el build sí habían pasado. Lo activamos
  (*Settings → Pages → Source: GitHub Actions*), volvimos a correr el workflow y pasó completo,
  con la prueba de humo en verde.
- Fusionamos los dos pull requests pendientes (#1 documentación y #2 actualización semanal) con el
  check de CI aprobado. Cada merge disparó el Deploy otra vez y todos terminaron en verde.
- **Dependabot sí funcionó**: apenas subimos el repositorio abrió 4 PRs para actualizar acciones
  (`checkout` y `setup-python` a v7, `upload-artifact` a v7 y `configure-pages` a v6). Los
  fusionamos de a uno, esperando a que Dependabot actualizara los demás y su CI volviera a pasar.
  El que más nos preocupaba era `configure-pages`, porque toca la publicación, así que revisamos
  que el Deploy siguiera en verde después de fusionarlo.

## 10 de noviembre de 2026 – Primer error real del workflow semanal

- Corrimos a mano el workflow *Actualizar datos (semanal)* y el scraping con Selenium **sí
  funcionó** dentro de GitHub Actions, que era lo que no habíamos podido probar.
- Pero falló el último paso: `git push` rechazó la rama `data/actualizacion-20261110` porque ya
  existía. Una ejecución anterior del mismo día la había subido y después no pudo abrir el PR, y
  como el nombre de la rama solo depende de la fecha, el segundo intento chocó con el primero.
- Lo arreglamos así: ahora hay una sola rama por día y se sobrescribe con `--force` usando la
  extracción más reciente; el PR solo se abre si no hay uno abierto para esa rama, y si GitHub no
  deja crearlo por permisos, el job muestra un error que dice qué opción activar. Antes de subirlo
  lo probamos en local con un remoto donde la rama ya existía.
