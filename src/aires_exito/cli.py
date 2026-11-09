"""Línea de comandos: ``python -m aires_exito <comando>``.

Comandos:
  scrape        Recorre Éxito.com con Selenium y guarda el CSV crudo.
  desde-html    Procesa páginas HTML guardadas (data/raw/page_XX.html) sin navegador.
  limpiar       Genera el CSV limpio con las variables derivadas.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .limpieza import preparar_dataset
from .scraper import recorrer_paginas

CSV_CRUDO = Path("data/aires_acondicionados_exito_crudo.csv")
CSV_LIMPIO = Path("data/aires_acondicionados_exito.csv")


def _guardar(df: pd.DataFrame, ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"{len(df)} registros -> {ruta}")


def cmd_scrape(args) -> None:  # pragma: no cover - requiere Chrome
    from .scraper import scrapear_todo

    _guardar(scrapear_todo(args.max_paginas), Path(args.salida))


def cmd_desde_html(args) -> None:
    carpeta = Path(args.carpeta)

    def obtener_html(pagina: int) -> str | None:
        f = carpeta / f"page_{pagina:02d}.html"
        if not f.exists():
            return None
        html = f.read_text(encoding="utf-8")
        return html if "<article" in html else None

    _guardar(recorrer_paginas(obtener_html), Path(args.salida))


def cmd_limpiar(args) -> None:
    df = pd.read_csv(args.entrada, encoding="utf-8-sig")
    _guardar(preparar_dataset(df), Path(args.salida))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="aires-exito", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("scrape", help="scraping en vivo con Selenium")
    s.add_argument("--max-paginas", type=int, default=40)
    s.add_argument("--salida", default=str(CSV_CRUDO))
    s.set_defaults(func=cmd_scrape)

    h = sub.add_parser("desde-html", help="procesar HTML guardado")
    h.add_argument("carpeta")
    h.add_argument("--salida", default=str(CSV_CRUDO))
    h.set_defaults(func=cmd_desde_html)

    lp = sub.add_parser("limpiar", help="crear variables derivadas")
    lp.add_argument("--entrada", default=str(CSV_CRUDO))
    lp.add_argument("--salida", default=str(CSV_LIMPIO))
    lp.set_defaults(func=cmd_limpiar)

    args = ap.parse_args(argv)
    args.func(args)
