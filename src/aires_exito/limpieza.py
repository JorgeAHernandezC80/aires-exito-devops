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


def clasificar_tipo(nombre: str) -> str:
    n = str(nombre).lower()
    if "inverter" in n:
        return "Inverter"
    if any(k in n for k in ("convencional", "on/off", "on-off")):
        return "Convencional"
    return "Otro"


def preparar_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina duplicados/nulos y agrega btu, marca, tipo, portatil y descuento_calc."""
    df = df.drop_duplicates(subset="url").dropna(subset=["precio_actual"]).copy()
    df["btu"] = df["nombre"].map(extraer_btu).astype(float)
    tarjeta = df["marca_tarjeta"] if "marca_tarjeta" in df else pd.Series(None, index=df.index)
    df["marca"] = [
        detectar_marca(n, t, m)
        for n, t, m in zip(df["nombre"], df["detalles"], tarjeta, strict=True)
    ]
    df["tipo"] = df["nombre"].map(clasificar_tipo)
    df["portatil"] = df["nombre"].str.contains("port[aá]til", case=False, regex=True)
    df["descuento_calc"] = (
        (df["precio_anterior"] - df["precio_actual"]) / df["precio_anterior"] * 100
    ).round(1)
    return df.reset_index(drop=True)
