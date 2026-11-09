"""Pruebas de extracción con tarjetas reales de Éxito.com (fixture del 2026-11-08)."""

from aires_exito.parser import parsear_pagina


def test_extrae_todas_las_tarjetas(productos):
    assert len(productos) == 10


def test_campos_obligatorios_sin_nulos(productos):
    for p in productos:
        assert p["nombre"]
        assert p["url"].startswith("https://www.exito.com/")
        assert isinstance(p["precio_actual"], int) and p["precio_actual"] > 0


def test_precio_actual_y_anterior(productos):
    lg = productos[3]
    assert lg["precio_actual"] == 2_806_000
    assert lg["precio_anterior"] == 4_384_700
    assert lg["descuento_pct"] == 36


def test_producto_sin_precio_anterior(productos):
    finlandek = productos[1]
    assert finlandek["precio_actual"] == 1_195_900
    assert finlandek["precio_anterior"] is None
    assert finlandek["descuento_pct"] is None


def test_calificacion_y_opiniones(productos):
    artic = productos[4]
    assert artic["calificacion"] == 5.0
    assert artic["n_opiniones"] == 1


def test_patrocinado(productos):
    assert productos[0]["patrocinado"] is True
    assert sum(p["patrocinado"] for p in productos) == 1


def test_vendedor_tercero(productos):
    assert productos[8]["vendedor"] == "Oportunidades"


def test_pagina_sin_tarjetas():
    assert parsear_pagina("<html><body><p>Sin resultados</p></body></html>") == []


def test_url_relativa_se_completa():
    html = '<article><a href="/aire-x/p">Aire X 12000 Btu</a> $ 1.000.000</article>'
    (p,) = parsear_pagina(html)
    assert p["url"] == "https://www.exito.com/aire-x/p"
    assert p["vendedor"] == "Éxito"  # valor por defecto cuando no aparece "Vendido por:"


# --- Bugs heredados de la EA1 (docs/bitacora.md) ---


def test_vendedor_sin_texto_de_ofertas_adicionales(productos):
    # La tarjeta muestra "Vendido por: Exito  Ver 1 oferta adicional"
    assert productos[0]["vendedor"] == "Exito"


def test_nombre_completo_no_truncado(productos):
    # El enlace trae el nombre recortado; el <h3> de la tarjeta lo trae completo.
    assert productos[3]["nombre"].endswith("2IN1S18C3.SSO")
    assert productos[5]["nombre"].endswith("A FDAC12222")
    assert "ELECTROLUX 12000 Btu" in productos[2]["nombre"]


def test_marca_publicada_en_la_tarjeta(productos):
    assert [p["marca_tarjeta"] for p in productos[:6]] == [
        "MABE", "FINLANDEK", "ELECTROLUX", "LG", "ARTIC AIR X 2", "FINLANDEK",
    ]  # fmt: skip
