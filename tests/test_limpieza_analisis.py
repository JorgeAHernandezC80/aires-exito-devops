import pandas as pd
import pytest

from aires_exito.analisis import indicadores, por_grupo, resumen_precios
from aires_exito.limpieza import clasificar_tipo, detectar_marca, extraer_btu, preparar_dataset


@pytest.fixture
def df_limpio(productos):
    df = pd.DataFrame(productos)
    df["pagina"] = 1
    return preparar_dataset(df)


@pytest.mark.parametrize(
    "nombre, esperado",
    [
        ("Aire Acondicionado Dual Inverter LG 12000 Btu", "Inverter"),
        ("Aire Acondicionado Convencional MABE 9000 Btu", "Convencional"),
        ("Aire 9000 Btu On/Off", "Convencional"),
        ("Ventilador de pedestal", "Otro"),
    ],
)
def test_clasificar_tipo(nombre, esperado):
    assert clasificar_tipo(nombre) == esperado


def test_preparar_dataset_elimina_duplicados_y_nulos():
    df = pd.DataFrame(
        {
            "nombre": ["Aire A 12000 Btu", "Aire A 12000 Btu", "Aire B 9000 Btu"],
            "url": ["u1", "u1", "u2"],
            "precio_actual": [100.0, 100.0, None],
            "precio_anterior": [200.0, 200.0, None],
            "detalles": ["", "", ""],
        }
    )
    out = preparar_dataset(df)
    assert len(out) == 1
    assert out.loc[0, "btu"] == 12000
    assert out.loc[0, "descuento_calc"] == 50.0


def test_variables_derivadas(df_limpio):
    for col in ("btu", "marca", "tipo", "portatil", "descuento_calc"):
        assert col in df_limpio
    assert df_limpio["portatil"].sum() >= 2


def test_resumen_precios(df_limpio):
    r = resumen_precios(df_limpio)
    assert r["n"] == 10
    assert r["min"] == 22_900
    assert r["min"] <= r["p25"] <= r["mediana"] <= r["p75"] <= r["max"]


def test_por_grupo_ordenado(df_limpio):
    t = por_grupo(df_limpio, "tipo")
    assert list(t.columns) == ["count", "mean", "median", "min", "max"]
    assert t["count"].is_monotonic_decreasing


def test_indicadores(df_limpio):
    ind = indicadores(df_limpio)
    assert ind["pct_patrocinados"] == pytest.approx(10.0)
    assert ind["pct_con_descuento"] == pytest.approx(80.0)
    assert ind["paginas"] == 1


# --- fix/normalizar-marcas-btu ---


@pytest.mark.parametrize(
    "marca_tarjeta, esperado",
    [("LG", "LG"), ("TCL", "TCL"), ("MABE", "Mabe"), ("HOME ELEMENTS", "Home Elements"),
     ("GENERICO", "Genérico"), ("ARTIC AIR X 2", "Artic Air"), ("GENERAL ELECTIC", "GE")],
)  # fmt: skip
def test_marca_desde_la_tarjeta_normalizada(marca_tarjeta, esperado):
    assert detectar_marca("cualquier nombre", "", marca_tarjeta) == esperado


def test_marca_sin_sufijos_de_referencia(df_limpio):
    assert set(df_limpio["marca"]) >= {"LG", "Finlandek", "Mabe", "Artic Air"}
    assert not df_limpio["marca"].str.contains(r"^\.|\d", regex=True).any()


@pytest.mark.parametrize(
    "nombre, btu",
    [("Aire LG 12000 Btu 110 V", 12000), ("Minisplit 12,000Btu Midea", 12000),
     ("Aire Kalley 12.000Btu Tipo Split", 12000), ("Gree Cosmo 24.000 Btu", 24000),
     ("Induham 12.000 Btus Blanco", 12000),
     ("Aire Acondi. 1200BTU Inverter ELECTROLUX 12000 Btu", 12000),
     ("Ventilador de pedestal", None)],
)  # fmt: skip
def test_extraer_btu(nombre, btu):
    assert extraer_btu(nombre) == btu
