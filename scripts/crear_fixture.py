"""Crea tests/fixtures/tarjetas_muestra.html a partir de páginas reales descargadas.

Toma tarjetas <article> concretas (página, posición), elimina imágenes, SVG y scripts para
que el archivo sea liviano, y las guarda en un HTML mínimo. Se ejecuta a mano:

    python scripts/crear_fixture.py data/raw tests/fixtures/tarjetas_muestra.html
"""

import sys
from pathlib import Path

from bs4 import BeautifulSoup

# (página, índice de la tarjeta, caso que cubre)
SELECCION = [
    (1, 0, "patrocinado, 'Ver 1 oferta adicional' pegado al vendedor"),
    (1, 2, "sin precio anterior ni descuento"),
    (1, 4, "nombre truncado: '1200BTU' en el enlace, 12000 Btu en el nombre completo"),
    (1, 9, "nombre truncado: falta '.SSO' antes de la marca LG"),
    (1, 10, "calificación y número de opiniones"),
    (6, 2, "nombre truncado: falta 'A FDAC12222' antes de FINLANDEK"),
    (3, 12, "producto genérico"),
    (7, 9, "accesorio (deflector), no es un aire acondicionado"),
    (7, 11, "ventilador, no es un aire acondicionado"),
    (15, 13, "combo de cocina mal categorizado por el sitio"),
]


def main(carpeta: str, salida: str) -> None:
    partes = []
    for pagina, idx, caso in SELECCION:
        html = Path(carpeta, f"page_{pagina:02d}.html").read_text(encoding="utf-8")
        art = BeautifulSoup(html, "lxml").find_all("article")[idx]
        for basura in art.find_all(["script", "style", "svg", "noscript", "picture", "source"]):
            basura.decompose()
        for img in art.find_all("img"):
            img.attrs = {"alt": img.get("alt", "")}
        partes.append(f"<!-- página {pagina}, tarjeta {idx}: {caso} -->\n{art}")
    doc = "<!DOCTYPE html>\n<html lang='es'><body>\n" + "\n".join(partes) + "\n</body></html>\n"
    Path(salida).write_text(doc, encoding="utf-8")
    print(f"{len(partes)} tarjetas -> {salida} ({len(doc) // 1024} KB)")


if __name__ == "__main__":
    main(*sys.argv[1:3])
