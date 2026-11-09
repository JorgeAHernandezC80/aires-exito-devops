"""Extracción de datos de las tarjetas de producto (Beautiful Soup).

Estas funciones no abren el navegador: reciben HTML ya renderizado.
Por eso se pueden probar sin conexión, con archivos de ejemplo.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup
from bs4.element import Tag

URL_SITIO = "https://www.exito.com"

_RE_PRECIO = re.compile(r"\$\s*([\d\.]{4,})")
_RE_DESCUENTO = re.compile(r"(\d{1,2})\s*%")
_RE_VENDEDOR = re.compile(
    r"Vendido por:\s*(.+?)(?=\s+\d\.\d\s+\(|\s+\(\d+\s*opini|\s+Agregar|$)"
)
_RE_CALIFICACION = re.compile(r"(\d\.\d)\s*\((\d+)\s*opini")
_RE_NOMBRE_TEXTO = re.compile(
    r"(Aire\s.+?\d{4,5}\s*Btu\S*(?:\s+\d+\s*V)?(?:\s+[A-Z0-9\-]{5,})?)", re.I
)


def _nombre_y_url(art: Tag, texto: str) -> tuple[str, str]:
    nombre, url = "", ""
    enlace = art.find("a", href=lambda h: h and "/p" in h)
    if enlace:
        url = enlace["href"]
        nombre = (
            enlace.get_text(strip=True) or enlace.get("title") or enlace.get("aria-label") or ""
        )
    if not nombre:
        img = art.find("img", alt=True)
        if img:
            nombre = img["alt"].strip()
    if not nombre:
        m = _RE_NOMBRE_TEXTO.search(texto)
        nombre = m.group(1) if m else "Producto sin nombre"
    if url.startswith("/"):
        url = URL_SITIO + url
    return nombre, url


def extraer_producto(art: Tag) -> dict:
    """Extrae los campos de una tarjeta ``<article>`` del listado."""
    texto = art.get_text(" ", strip=True)
    nombre, url = _nombre_y_url(art, texto)

    precios = [int(p.replace(".", "")) for p in _RE_PRECIO.findall(texto)]
    m_desc = _RE_DESCUENTO.search(texto)
    m_vend = _RE_VENDEDOR.search(texto)
    m_rat = _RE_CALIFICACION.search(texto)

    return {
        "nombre": nombre,
        "url": url,
        "patrocinado": "Patrocinado" in texto,
        "precio_actual": min(precios) if precios else None,
        "precio_anterior": max(precios) if len(precios) > 1 else None,
        "descuento_pct": int(m_desc.group(1)) if m_desc else None,
        "vendedor": m_vend.group(1).strip() if m_vend else "Éxito",
        "calificacion": float(m_rat.group(1)) if m_rat else None,
        "n_opiniones": int(m_rat.group(2)) if m_rat else None,
        "detalles": texto,
    }


def parsear_pagina(html: str) -> list[dict]:
    """Devuelve la lista de productos (diccionarios) de una página del listado."""
    soup = BeautifulSoup(html, "lxml")
    return [extraer_producto(art) for art in soup.find_all("article")]
