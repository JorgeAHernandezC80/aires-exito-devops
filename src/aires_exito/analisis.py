"""Estadística descriptiva del dataset limpio."""

from __future__ import annotations

import pandas as pd

AGREGADOS = ["count", "mean", "median", "min", "max"]


def resumen_precios(df: pd.DataFrame) -> dict:
    p = df["precio_actual"]
    return {
        "n": int(p.count()),
        "media": float(p.mean()),
        "mediana": float(p.median()),
        "desv": float(p.std()),
        "min": float(p.min()),
        "p25": float(p.quantile(0.25)),
        "p75": float(p.quantile(0.75)),
        "max": float(p.max()),
    }


def por_grupo(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    return (
        df.groupby(columna)["precio_actual"]
        .agg(AGREGADOS)
        .sort_values("count", ascending=False)
    )


def indicadores(df: pd.DataFrame) -> dict:
    return {
        "pct_con_descuento": float(df["precio_anterior"].notna().mean() * 100),
        "pct_patrocinados": float(df["patrocinado"].mean() * 100),
        "paginas": int(df["pagina"].nunique()) if "pagina" in df else None,
    }
