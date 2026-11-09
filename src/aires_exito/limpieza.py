"""Limpieza del dataset y creación de variables derivadas (pandas)."""

from __future__ import annotations

import re

import pandas as pd

MARCAS = [
    "LG", "Samsung", "Mabe", "Electrolux", "Midea", "Haceb", "Whirlpool", "Challenger",
    "Kalley", "Hyundai", "Finlandek", "Hisense", "TCL", "Carrier", "York", "Gree",
]  # fmt: skip

# "12000 Btu", "12.000 BTU", "12,000Btu", "24.000 Btus"
_RE_BTU = re.compile(r"(\d{1,2}[.,]?\d{3})\s*Btu", re.I)

# Correcciones a la marca publicada por el vendedor en la tarjeta
ALIAS_MARCA = {
    "GENERICO": "Genérico",
    "ARTIC AIR X 2": "Artic Air",
    "GENERAL ELECTIC": "GE",  # error de digitación del vendedor
}


def extraer_btu(nombre: str) -> float | None:
    """Capacidad en BTU. Si el nombre trae varias cifras se toma la mayor.

    Ej.: "Aire Acondi. 1200BTU Inverter ... 12000 Btu" -> 12000.
    """
    valores = [int(re.sub(r"[.,]", "", v)) for v in _RE_BTU.findall(str(nombre))]
    return float(max(valores)) if valores else None


def normalizar_marca(marca: str) -> str:
    marca = " ".join(str(marca).split()).upper()
    if marca in ALIAS_MARCA:
        return ALIAS_MARCA[marca]
    return marca if len(marca) <= 3 else marca.title()


def _marca_desde_texto(nombre: str, texto: str) -> str | None:
    """Método de la EA1: texto que sigue al nombre en la tarjeta. Solo como respaldo."""
    if nombre not in texto:
        return None
    despues = texto.split(nombre, 1)[1].strip()
    m = re.match(r"([A-Za-zÁÉÍÓÚÑ0-9\+\.& ]{2,25}?)(?=\s+-\s|\s+\d{1,2}\s*%|\s+\$|$)", despues)
    if m and m.group(1).strip().lower() not in ("producto genérico", "producto generico"):
        return m.group(1).strip()
    return None


def detectar_marca(nombre: str, texto: str, marca_tarjeta: str | None = None) -> str:
    """Marca publicada en la tarjeta; si falta, texto tras el nombre; si no, lista conocida."""
    if isinstance(marca_tarjeta, str) and marca_tarjeta.strip():
        return normalizar_marca(marca_tarjeta)
    nombre, texto = str(nombre), str(texto)
    desde_texto = _marca_desde_texto(nombre, texto)
    if desde_texto:
        return normalizar_marca(desde_texto)
    for marca in MARCAS:
        if re.search(rf"\b{re.escape(marca)}\b", nombre, re.I):
            return normalizar_marca(marca)
    return "Otra"


_RE_CONVENCIONAL = re.compile(r"convencional|\bon\s*[/-]?\s*off\b", re.I)


def clasificar_tipo(nombre: str) -> str:
    n = str(nombre)
    if re.search(r"inverte?r?\b", n, re.I):  # incluye el error frecuente "Inverte"
        return "Inverter"
    if _RE_CONVENCIONAL.search(n):
        return "Convencional"
    return "Otro"


CATEGORIAS = [
    "Aire acondicionado",
    "Enfriador portátil",
    "Ventilador",
    "Accesorio o repuesto",
    "Otro",
]
_RE_ACCESORIO = re.compile(
    r"^(soporte|deflector|valvula|válvula|actuador|condensador|refrigerante|acumulador|control)",
    re.I,
)
_RE_OTRO = re.compile(
    r"^(calentador|calefactor|combo|deshumi|enchufe|raqueta|quitamotas|extractor|difusor humid)",
    re.I,
)
_RE_VENTILADOR = re.compile(r"^((aire|mini)\s+)?ventilador|abanico", re.I)
_RE_AIRE = re.compile(
    r"aire\s+ac\b|aire\s*acon?d?i?c?i?onado|aire\s+acondi\.|mini\s*split|enfriador|climatizador",
    re.I,
)
_RE_EQUIPO = re.compile(r"\d[\d.,]*\s*btu|mini\s*split|\bsplit\b|ventana", re.I)
_RE_PEQUENO = re.compile(r"mini|personal|usb|recargable|artic|arctic|ultra|cooler|led|5v", re.I)
PRECIO_MINIMO_EQUIPO = 700_000  # COP; por debajo, sin BTU ni "split", es un enfriador


def clasificar_categoria(nombre: str, precio: float | None = None) -> str:
    """Clasifica el producto, porque la categoría del sitio mezcla otros artículos.

    Reglas en orden: accesorios y otros artículos por la primera palabra; ventiladores;
    equipo de aire acondicionado si trae BTU, split o ventana (o si cuesta más de
    PRECIO_MINIMO_EQUIPO y no parece un mini enfriador); el resto con "aire" es enfriador.
    """
    n = " ".join(str(nombre).split())
    if _RE_ACCESORIO.search(n):
        return "Accesorio o repuesto"
    if _RE_OTRO.search(n):
        return "Otro"
    if _RE_VENTILADOR.search(n):
        return "Ventilador"
    if _RE_AIRE.search(n) or n.lower().startswith("aireacondicionado"):
        if _RE_EQUIPO.search(n):
            return "Aire acondicionado"
        if precio is not None and precio >= PRECIO_MINIMO_EQUIPO and not _RE_PEQUENO.search(n):
            return "Aire acondicionado"
        return "Enfriador portátil"
    return "Otro"


def preparar_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina duplicados/nulos y agrega btu, marca, tipo, categoria, portatil y descuento."""
    df = df.drop_duplicates(subset="url").dropna(subset=["precio_actual"]).copy()
    df["btu"] = df["nombre"].map(extraer_btu).astype(float)
    tarjeta = df["marca_tarjeta"] if "marca_tarjeta" in df else pd.Series(None, index=df.index)
    df["marca"] = [
        detectar_marca(n, t, m)
        for n, t, m in zip(df["nombre"], df["detalles"], tarjeta, strict=True)
    ]
    df["tipo"] = df["nombre"].map(clasificar_tipo)
    df["categoria"] = [
        clasificar_categoria(n, p) for n, p in zip(df["nombre"], df["precio_actual"], strict=True)
    ]
    df["es_aire"] = df["categoria"] == "Aire acondicionado"
    df["portatil"] = df["nombre"].str.contains("port[aá]til", case=False, regex=True)
    df["descuento_calc"] = (
        (df["precio_anterior"] - df["precio_actual"]) / df["precio_anterior"] * 100
    ).round(1)
    return df.reset_index(drop=True)
