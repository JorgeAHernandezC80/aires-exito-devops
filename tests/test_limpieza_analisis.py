import pandas as pd
import pytest

from aires_exito.analisis import indicadores, por_grupo, resumen_precios
from aires_exito.limpieza import (
    clasificar_categoria,
    clasificar_tipo,
    detectar_marca,
    extraer_btu,
    preparar_dataset,
)


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


# --- feature/categoria-producto ---


@pytest.mark.parametrize(
    "nombre, precio, esperado",
    [
        ("Aire Acondicionado Dual Inverter LG 12000 Btu 110 V", 2_072_000, "Aire acondicionado"),
        ("Minisplit 12,000Btu Midea Ecomaster 220V Inverter", 1_339_900, "Aire acondicionado"),
        ("Aire Acondicionado De Ventana Clima Fresh 500", 869_000, "Aire acondicionado"),
        (
            "Aire Acondicionado Portátil 250 Pies Cuadrados Insignia",
            2_807_550,
            "Aire acondicionado",
        ),
        ("Aire Acondicionado Portatil Artic Air Ultra 2X Original", 29_330, "Enfriador portátil"),
        (
            "Mini Enfriador De Aire Acondicionado Ventilador Portátil Usb",
            30_372,
            "Enfriador portátil",
        ),
        ('Ventilador Pared Home Elements 16" Pulgadas Maxiflow', 201_900, "Ventilador"),
        ("Ventilador Difusor Aire Acondicionado Portátil Doble Luz Led", 122_170, "Ventilador"),
        ("Soporte Para Unidad De Aire Acondicionado De 12.000Btu", 40_000, "Accesorio o repuesto"),
        ("Valvula Actuador Danfoss Icad 1200B 24V", 14_999_990, "Accesorio o repuesto"),
        ("Calentador de Paso Haceb 12 Litros Tiro Forzado", 1_704_900, "Otro"),
        ("Combo Mertec Mini Waflera Mas Picatodo 350 Ml", 125_900, "Otro"),
        # casos encontrados al revisar los 201 productos reales:
        ("Aire Ac Port 12000BTU 110V Convencional ELECTROLUX", 1_710_941, "Aire acondicionado"),
        ("Mini Ventilador De Mesa Usb Con 3 Aspas", 84_000, "Ventilador"),
    ],
)
def test_clasificar_categoria(nombre, precio, esperado):
    assert clasificar_categoria(nombre, precio) == esperado


def test_tipo_reconoce_onoff():
    assert clasificar_tipo("Aire Acondicionado 12000 Btu 220V Onoff Estar") == "Convencional"
    assert clasificar_tipo("Mini Split York 12.000 Btu Seer 16 On Off") == "Convencional"
