# Aires acondicionados en Éxito.com – scraping con flujo DevOps

[![CI](https://github.com/JorgeAHernandezC80/aires-exito-devops/actions/workflows/ci.yml/badge.svg)](https://github.com/JorgeAHernandezC80/aires-exito-devops/actions/workflows/ci.yml)
[![Deploy](https://github.com/JorgeAHernandezC80/aires-exito-devops/actions/workflows/deploy.yml/badge.svg)](https://github.com/JorgeAHernandezC80/aires-exito-devops/actions/workflows/deploy.yml)

**Reporte publicado:** https://jorgeahernandezc80.github.io/aires-exito-devops/

Este es nuestro proyecto para el curso *Programación para Análisis de Datos* (Ingeniería de
Software y Datos, IU Digital de Antioquia). Lo hicimos en grupo:

- Lady Laura Olmos
- Selenis Lorena Ramos Guardo
- María Isabel Atencia Ramos
- Jorge Andrés Hernández

| Evidencia | Qué hicimos |
|---|---|
| EA1 | En grupo hicimos un notebook de Colab que saca los aires acondicionados de Éxito.com con Selenium y Beautiful Soup. Está en `legacy/` sin cambios. |
| EA2 | Pasamos ese notebook a un paquete de Python con Git y GitHub, le hicimos pruebas automáticas, configuramos CI con GitHub Actions y el despliegue automático del reporte en GitHub Pages. |

## Lo que salió con los datos del 8 de noviembre de 2026

- 201 productos distintos en 16 páginas del listado.
- De esos, solo **101 son equipos de aire acondicionado**. Los demás son enfriadores pequeños
  (37), otros artículos (27), ventiladores (25) y accesorios o repuestos (11).
- El precio mediano de un equipo es **$1.749.900 COP**, y van desde $827.955 hasta $5.519.900.
- Los inverter tienen una mediana de $1.929.900 (53 equipos) y los convencionales de
  $1.416.937 (30 equipos).
- El 88,6 % de los productos muestra un precio anterior, o sea que casi todo aparece en oferta.

## Cómo está organizado

```
src/aires_exito/
  parser.py     saca los datos de cada tarjeta <article> con Beautiful Soup
  scraper.py    recorre las páginas con Selenium (la paginación no depende del navegador)
  limpieza.py   marca, BTU, tipo, categoría real y descuento
  analisis.py   estadística descriptiva
  reporte.py    arma el sitio (HTML + SVG) que se publica en GitHub Pages
  cli.py        python -m aires_exito {scrape|desde-html|limpiar|validar|reporte}
tests/          las pruebas con pytest, usando tarjetas reales (tests/fixtures/)
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

## Cómo correrlo en tu computador

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

Si no tienes Chrome, puedes trabajar con páginas que ya estén descargadas:
`python -m aires_exito desde-html data/raw`.

## Flujo de trabajo

Usamos **GitHub Flow**: en `main` siempre debe estar algo que funcione. Cada cambio lo hacemos en
una rama aparte (`feature/`, `fix/`, `test/`, `ci/`, `cd/`, `docs/`), abrimos un pull request, el
CI lo revisa y cuando se fusiona se publica solo. Lo explicamos con más detalle en
[docs/flujo-devops.md](docs/flujo-devops.md).

## Ética

Solo sacamos datos públicos de productos (nada de datos personales), con pausas entre página y
página, y los usamos únicamente para el curso.
