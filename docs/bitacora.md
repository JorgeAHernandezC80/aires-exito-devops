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
