# Aires acondicionados en Éxito.com – scraping con flujo DevOps

[![CI](https://github.com/JorgeAHernandezC80/aires-exito-devops/actions/workflows/ci.yml/badge.svg)](https://github.com/JorgeAHernandezC80/aires-exito-devops/actions/workflows/ci.yml)
[![Deploy](https://github.com/JorgeAHernandezC80/aires-exito-devops/actions/workflows/deploy.yml/badge.svg)](https://github.com/JorgeAHernandezC80/aires-exito-devops/actions/workflows/deploy.yml)

**Reporte publicado:** https://jorgeahernandezc80.github.io/aires-exito-devops/

Este es un proyecto grupal para el curso *Programación para Análisis de Datos*
(PREICA2602B020048), del programa de Ingeniería de Software y Datos de la IU Digital de Antioquia.

## Índice

1. [Integrantes](#integrantes)
2. [Evidencias](#evidencias)
3. [Resultados de la extracción del 8 de noviembre de 2026](#resultados-de-la-extracción-del-8-de-noviembre-de-2026)
4. [Estructura del repositorio](#estructura-del-repositorio)
5. [Cómo ejecutarlo](#cómo-ejecutarlo)
6. [Actualizar datos en local](#actualizar-datos-en-local)
7. [Flujo de trabajo](#flujo-de-trabajo)
8. [Consideraciones éticas](#consideraciones-éticas)

## Integrantes

Los integrantes del grupo somos:

- Lady Laura Olmos
- Selenis Lorena Ramos Guardo
- María Isabel Atencia Ramos
- Jorge Andrés Hernández

## Evidencias

| Evidencia | Qué se hizo |
|---|---|
| **EA1** – S30. Análisis y herramientas de extracción de datos | En grupo hicimos un notebook de Google Colab que saca los aires acondicionados de Éxito.com con Selenium y Beautiful Soup. Está en `legacy/` sin cambios. |
| **EA2** – S35. Optimizando la productividad en el mundo del software | Pasamos ese notebook a un paquete de Python con Git y GitHub, le hicimos pruebas automáticas y configuramos la integración continua con GitHub Actions y el despliegue automático del reporte en GitHub Pages. |

## Resultados de la extracción del 8 de noviembre de 2026

- Se obtuvieron 201 productos distintos en 16 páginas del listado.
- De ellos, solo **101 son equipos de aire acondicionado**. Los demás son enfriadores pequeños
  (37), otros artículos (27), ventiladores (25) y accesorios o repuestos (11).
- El precio mediano de un equipo es **$1.749.900 COP**, y los precios van desde $827.955 hasta
  $5.519.900.
- Los equipos *inverter* tienen una mediana de $1.929.900 (53 equipos), y los convencionales,
  de $1.416.937 (30 equipos).
- El 88,6 % de los productos muestra un precio anterior; es decir, casi todo aparece en oferta.

## Estructura del repositorio

```
src/aires_exito/
  parser.py     saca los datos de cada tarjeta <article> con Beautiful Soup
  scraper.py    recorre las páginas con Selenium (la paginación no depende del navegador)
  limpieza.py   marca, BTU, tipo, categoría real y descuento
  analisis.py   estadística descriptiva
  reporte.py    arma el sitio (HTML + SVG) que se publica en GitHub Pages
  cli.py        python -m aires_exito {scrape|desde-html|limpiar|validar|reporte}
tests/          pruebas con pytest sobre tarjetas reales (tests/fixtures/)
data/           CSV crudo y limpio, y la fecha de la extracción
.github/
  workflows/ci.yml                lint + pruebas en Python 3.11, 3.12 y 3.13
  workflows/deploy.yml            pruebas -> build -> GitHub Pages -> prueba de humo
  workflows/actualizar-datos.yml  scraping cada semana y PR automático (todavía experimental)
docs/
  flujo-devops.md   cómo funciona el flujo de trabajo
  bitacora.md       lo que fuimos haciendo, lo que falló y cómo lo arreglamos
legacy/         el notebook original de la EA1
```

## Cómo ejecutarlo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,scraping]"

pytest                                   # pruebas
ruff check . && ruff format --check .    # estilo del código

python -m aires_exito scrape             # scraping en vivo (necesita Google Chrome)
python -m aires_exito validar
python -m aires_exito limpiar
python -m aires_exito reporte            # genera _site/index.html
```

Si no se tiene Chrome, se puede trabajar con páginas ya descargadas:
`python -m aires_exito desde-html data/raw`.

## Actualizar datos en local

Desde noviembre de 2026, Éxito.com responde a los servidores de GitHub Actions con la
verificación anti-bots de Cloudflare (*"Just a moment..."*). Cuando pasa, el workflow
*Actualizar datos* termina con una advertencia, no modifica los datos y sube la captura como
artefacto `debug-scraping`. En ese caso, la extracción se hace desde un computador propio con
un solo comando (Windows, desde la carpeta del repositorio):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\actualizar_datos_local.ps1
```

El script actualiza `main`, hace el scraping, valida, limpia, escribe la fecha, genera y abre el
reporte (`_site/index.html`), sube los datos a la rama `data/actualizacion-AAAAMMDD` y abre el
pull request (o muestra el enlace si no está instalado GitHub CLI). Si algo falla, deja los datos
como estaban. Al fusionar el PR, el workflow *Deploy* publica el reporte en GitHub Pages.

Si el sitio también muestra la verificación en el equipo local, se pueden guardar las páginas
desde el navegador (*Guardar como → Página web completa*) en `data/raw/page_01.html`,
`page_02.html`, ... y procesarlas con `python -m aires_exito desde-html data/raw`.

## Flujo de trabajo

Usamos **GitHub Flow**: en `main` siempre debe haber una versión que funcione. Cada cambio lo
hacemos en una rama aparte (`feature/`, `fix/`, `test/`, `ci/`, `cd/`, `docs/`) y abrimos un
*pull request*; el CI lo revisa y, cuando se fusiona, el reporte se publica automáticamente. Lo
explicamos con más detalle en [docs/flujo-devops.md](docs/flujo-devops.md).

## Consideraciones éticas

Solo extraemos datos públicos de productos (ningún dato personal), con pausas entre una página
y otra, y los usamos únicamente con fines académicos.
