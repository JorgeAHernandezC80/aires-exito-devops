import json

import pandas as pd

from aires_exito.cli import main
from aires_exito.limpieza import preparar_dataset
from aires_exito.reporte import barras_horizontales, cop, generar_sitio, pct


def test_formato_colombiano():
    assert cop(1_749_900) == "$1.749.900"
    assert cop(22_900.4) == "$22.900"
    assert pct(88.56) == "88,6 %"


def test_barras_un_svg_por_fila_y_escapa_html():
    svg = barras_horizontales([("A<b>", 10, "10"), ("B", 5, "5")], "titulo")
    assert svg.startswith("<svg") and svg.count('class="barra"') == 2
    assert "A&lt;b&gt;" in svg and "<b>" not in svg
    assert barras_horizontales([], "vacío") == ""


def test_generar_sitio(tmp_path, productos):
    df = pd.DataFrame(productos)
    df["pagina"] = 1
    entrada = tmp_path / "limpio.csv"
    preparar_dataset(df).to_csv(entrada, index=False)

    r = generar_sitio(entrada, tmp_path / "_site", fecha="2026-11-08")

    index = (tmp_path / "_site" / "index.html").read_text(encoding="utf-8")
    assert "2026-11-08" in index and "<svg" in index
    assert (tmp_path / "_site" / "datos.csv").exists()
    assert (tmp_path / "_site" / ".nojekyll").exists()
    resumen = json.loads((tmp_path / "_site" / "resumen.json").read_text(encoding="utf-8"))
    assert resumen["total"] == 10
    assert r["aires"] == resumen["aires"] == 5  # MABE, FINLANDEK x2, ELECTROLUX, LG


def test_cli_reporte(tmp_path, productos):
    df = pd.DataFrame(productos)
    df["pagina"] = 1
    entrada = tmp_path / "limpio.csv"
    preparar_dataset(df).to_csv(entrada, index=False)
    main(["reporte", "--entrada", str(entrada), "--salida", str(tmp_path / "s"), "--fecha", "x"])
    assert (tmp_path / "s" / "index.html").exists()
