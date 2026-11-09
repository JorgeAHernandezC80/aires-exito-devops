"""Limpieza del dataset y creación de variables derivadas (pandas)."""

from __future__ import annotations

import re

import pandas as pd

MARCAS = [
    "LG", "Samsung", "Mabe", "Electrolux", "Midea", "Haceb", "Whirlpool", "Challenger",
    "Kalley", "Hyundai", "Finlandek", "Hisense", "TCL", "Carrier", "York", "Gree",
]  # fmt: skip

_RE_BTU = r"(\d{4,5})\s*Btu"


def detectar_marca(nombre: str, texto: str) -> str:
    """Marca mostrada en la tarjeta (texto después del nombre) o, si no, la lista conocida."""
    nombre, texto = str(nombre), str(texto)
    if nombre in texto:
        despues = texto.split(nombre, 1)[1].strip()
        m = re.match(r"([A-Za-zÁÉÍÓÚÑ0-9\+\.& ]{2,25}?)(?=\s+-\s|\s+\d{1,2}\s*%|\s+\$|$)", despues)
        if (
            m
            and m.group(1).strip()
            and m.group(1).strip().lower()
            not in (
                "producto genérico",
                "producto generico",
            )
        ):
            return m.group(1).strip().title()
    for marca in MARCAS:
        if re.search(rf"\b{re.escape(marca)}\b", nombre, re.I):
            return marca.upper() if len(marca) <= 3 else marca
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
    df["btu"] = df["nombre"].str.extract(_RE_BTU, flags=re.I)[0].astype(float)
    df["marca"] = [detectar_marca(n, t) for n, t in zip(df["nombre"], df["detalles"], strict=True)]
    df["tipo"] = df["nombre"].map(clasificar_tipo)
    df["portatil"] = df["nombre"].str.contains("port[aá]til", case=False, regex=True)
    df["descuento_calc"] = (
        (df["precio_anterior"] - df["precio_actual"]) / df["precio_anterior"] * 100
    ).round(1)
    return df.reset_index(drop=True)
