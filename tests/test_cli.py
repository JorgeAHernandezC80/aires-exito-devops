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
