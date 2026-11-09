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
