import pandas as pd

from aires_exito.cli import main


def test_flujo_desde_html_y_limpiar(tmp_path, html_muestra):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "page_01.html").write_text(html_muestra, encoding="utf-8")
    crudo, limpio = tmp_path / "crudo.csv", tmp_path / "limpio.csv"

    main(["desde-html", str(raw), "--salida", str(crudo)])
    main(["limpiar", "--entrada", str(crudo), "--salida", str(limpio)])

    df = pd.read_csv(limpio, encoding="utf-8-sig")
    assert len(df) == 10
    assert {"marca", "tipo", "btu"} <= set(df.columns)


def test_validar_dataset():
    from aires_exito.cli import validar_dataset

    ok = pd.DataFrame({"nombre": ["a", "b"], "url": ["u1", "u2"], "precio_actual": [1, 2]})
    assert validar_dataset(ok, minimo=2) == []
    malo = pd.DataFrame({"nombre": ["a", None], "url": ["u1", "u1"], "precio_actual": [1, 2]})
    problemas = validar_dataset(malo, minimo=5)
    assert len(problemas) == 3


def test_cmd_validar_sale_con_error(tmp_path):
    import pytest

    f = tmp_path / "x.csv"
    pd.DataFrame({"nombre": ["a"], "url": ["u"], "precio_actual": [1]}).to_csv(f, index=False)
    with pytest.raises(SystemExit):
        main(["validar", "--entrada", str(f)])
    main(["validar", "--entrada", str(f), "--minimo", "1"])
