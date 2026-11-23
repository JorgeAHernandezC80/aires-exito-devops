"""Genera el sitio estático del reporte (lo publica el pipeline de CD en GitHub Pages).

    python -m aires_exito reporte --entrada data/aires_acondicionados_exito.csv --salida _site

Solo usa la librería estándar y pandas: los gráficos son SVG escritos a mano.
"""

from __future__ import annotations

import html
import json
import shutil
from datetime import date
from pathlib import Path

import pandas as pd

from . import BASE_URL, __version__
from .analisis import indicadores, resumen_precios

# --------------------------------------------------------------------------- formato


def cop(valor: float) -> str:
    """1234567.8 -> '$1.234.568' (separador de miles colombiano)."""
    return "$" + f"{round(valor):,}".replace(",", ".")


def pct(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",") + " %"


def _e(texto) -> str:
    return html.escape(str(texto), quote=True)


# --------------------------------------------------------------------------- gráficos


def barras_horizontales(filas: list[tuple[str, float, str]], titulo: str, ancho: int = 640) -> str:
    """SVG de barras horizontales de una sola serie.

    filas: (etiqueta, valor, texto mostrado en la punta y en el tooltip).
    """
    if not filas:
        return ""
    alto_fila, grosor, margen_izq = 34, 20, 170
    # espacio para el texto de la punta: ~7.5 px por carácter a 13 px (antes era fijo y se cortaba)
    margen_der = 16 + int(7.5 * max(len(t) for _, _, t in filas))
    alto = alto_fila * len(filas) + 8
    maximo = max(v for _, v, _ in filas) or 1
    util = ancho - margen_izq - margen_der
    partes = [
        f'<svg class="grafico" viewBox="0 0 {ancho} {alto}" role="img" '
        f'aria-label="{_e(titulo)}" width="100%">',
        f'<line class="base" x1="{margen_izq}" y1="0" x2="{margen_izq}" y2="{alto}"/>',
    ]
    for i, (etiqueta, valor, texto) in enumerate(filas):
        y = i * alto_fila + (alto_fila - grosor) / 2 + 4
        w = max(util * valor / maximo, 2)
        r = min(4, w)
        # barra con punta redondeada (4px) y base recta en el eje
        d = (
            f"M{margen_izq},{y} h{w - r} a{r},{r} 0 0 1 {r},{r} v{grosor - 2 * r} "
            f"a{r},{r} 0 0 1 {-r},{r} h{-(w - r)} z"
        )
        cy = y + grosor / 2
        partes.append(
            f'<g class="barra" tabindex="0" data-tip="{_e(etiqueta)}: {_e(texto)}">'
            f'<rect class="hit" x="0" y="{y - 6}" width="{ancho}" height="{grosor + 12}"/>'
            f'<path class="marca" d="{d}"/>'
            f'<text class="etq" x="{margen_izq - 10}" y="{cy}" text-anchor="end">'
            f"{_e(etiqueta)}</text>"
            f'<text class="val" x="{margen_izq + w + 8}" y="{cy}">{_e(texto)}</text>'
            f"<title>{_e(etiqueta)}: {_e(texto)}</title></g>"
        )
    partes.append("</svg>")
    return "".join(partes)


# --------------------------------------------------------------------------- datos


def calcular(df: pd.DataFrame) -> dict:
    aires = df[df["es_aire"]] if "es_aire" in df else df
    tipo = (
        aires[aires["tipo"].isin(["Inverter", "Convencional"])]
        .groupby("tipo")["precio_actual"]
        .agg(["count", "median"])
    )
    por_btu = (
        aires.dropna(subset=["btu"])
        .groupby("btu")["precio_actual"]
        .agg(["count", "median"])
        .query("count >= 2")
    )
    marcas = aires["marca"].value_counts().head(8)
    return {
        "total": len(df),
        "aires": len(aires),
        "precios_aires": resumen_precios(aires) if len(aires) else None,
        "indicadores": indicadores(df),
        "categorias": df["categoria"].value_counts().to_dict() if "categoria" in df else {},
        "tipo": {
            k: {"n": int(v["count"]), "mediana": float(v["median"])} for k, v in tipo.iterrows()
        },
        "btu": {
            int(k): {"n": int(v["count"]), "mediana": float(v["median"])}
            for k, v in por_btu.iterrows()
        },
        "marcas": {k: int(v) for k, v in marcas.items()},
    }


# --------------------------------------------------------------------------- página

CSS = """
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--surface-2:#f2f1ee;--text-primary:#0b0b0b;
--text-secondary:#52514e;--text-muted:#77766f;--border:#dddcd6;--series-1:#2a78d6;
font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--surface-1);
color:var(--text-primary);margin:0}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{
color-scheme:dark;--surface-1:#1a1a19;--surface-2:#242422;--text-primary:#f0efec;
--text-secondary:#c3c2b7;--text-muted:#9a998f;--border:#3a3a37;--series-1:#3987e5}}
main{max-width:980px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.1rem;margin:40px 0 4px}
.sub{color:var(--text-secondary);margin:0 0 24px}.nota{color:var(--text-muted);font-size:.85rem}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.tile{background:var(--surface-2);border-radius:10px;padding:16px}
.tile .n{font-size:1.7rem;font-weight:650;font-variant-numeric:tabular-nums}
.tile .l{color:var(--text-secondary);font-size:.9rem}
.grafico text{font-size:13px;dominant-baseline:middle;fill:var(--text-secondary)}
.grafico .val{fill:var(--text-primary);font-variant-numeric:tabular-nums}
.grafico .marca{fill:var(--series-1)}.grafico .base{stroke:var(--border);stroke-width:1}
.grafico .hit{fill:transparent}.barra:hover .marca,.barra:focus .marca{opacity:.8}
.barra:focus{outline:none}.barra:focus .etq{text-decoration:underline}
#tip{position:fixed;pointer-events:none;background:var(--text-primary);color:var(--surface-1);
padding:6px 10px;border-radius:6px;font-size:13px;display:none;z-index:9}
input{padding:8px 10px;border:1px solid var(--border);border-radius:8px;width:min(360px,100%);
background:var(--surface-1);color:var(--text-primary);margin:8px 0}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--border)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
th{color:var(--text-secondary);font-weight:600;cursor:pointer}
a{color:var(--series-1)}footer{margin-top:48px;color:var(--text-muted);font-size:.85rem}
"""

JS = """
const tip=document.getElementById('tip');
document.querySelectorAll('.barra').forEach(b=>{
 const show=e=>{tip.textContent=b.dataset.tip;tip.style.display='block';
  const r=b.getBoundingClientRect();const x=e.clientX??r.left+r.width/2,y=e.clientY??r.top;
  tip.style.left=Math.min(x+12,innerWidth-tip.offsetWidth-8)+'px';tip.style.top=(y-36)+'px'};
 b.addEventListener('mousemove',show);b.addEventListener('focus',show);
 ['mouseleave','blur'].forEach(ev=>b.addEventListener(ev,()=>tip.style.display='none'));});
const q=document.getElementById('buscar'),filas=[...document.querySelectorAll('#tabla tbody tr')];
q.addEventListener('input',()=>{const t=q.value.toLowerCase();let n=0;
 filas.forEach(f=>{const ok=f.textContent.toLowerCase().includes(t);f.hidden=!ok;n+=ok});
 document.getElementById('conteo').textContent=n+' productos';});
document.querySelectorAll('#tabla th').forEach((th,i)=>th.addEventListener('click',()=>{
 const asc=th.dataset.asc!=='1';th.dataset.asc=asc?'1':'0';const tb=th.closest('table').tBodies[0];
 const k=f=>{const c=f.cells[i];return c.dataset.v!==undefined?+c.dataset.v:c.textContent};
 [...tb.rows].sort((a,b)=>(k(a)>k(b)?1:-1)*(asc?1:-1)).forEach(r=>tb.appendChild(r));}));
"""


def construir_html(df: pd.DataFrame, r: dict, fecha: str) -> str:
    p = r["precios_aires"]
    ind = r["indicadores"]
    tiles = [
        (str(r["total"]), "productos en el listado de la categoría"),
        (str(r["aires"]), "son equipos de aire acondicionado"),
        (cop(p["mediana"]) if p else "–", "precio mediano de un equipo"),
        (pct(ind["pct_con_descuento"]), "publican precio anterior (oferta)"),
    ]
    g_cat = barras_horizontales(
        [(k, v, f"{v} productos") for k, v in r["categorias"].items()],
        "Productos por categoría real",
    )
    g_btu = barras_horizontales(
        [(f"{k:,} BTU".replace(",", "."), v["mediana"], f"{cop(v['mediana'])} (n={v['n']})")
         for k, v in sorted(r["btu"].items())],
        "Precio mediano por capacidad",
    )  # fmt: skip
    g_tipo = barras_horizontales(
        [(k, v["mediana"], f"{cop(v['mediana'])} (n={v['n']})") for k, v in r["tipo"].items()],
        "Precio mediano por tecnología",
    )
    g_marca = barras_horizontales(
        [(k, v, f"{v} equipos") for k, v in r["marcas"].items()], "Marcas con más equipos"
    )

    aires = df[df["es_aire"]] if "es_aire" in df else df
    filas = []
    for _, f in aires.sort_values("precio_actual").iterrows():
        btu = "" if pd.isna(f["btu"]) else f"{int(f['btu']):,}".replace(",", ".")
        desc = "" if pd.isna(f["descuento_calc"]) else pct(f["descuento_calc"])
        filas.append(
            f'<tr><td><a href="{_e(f["url"])}" rel="noopener">{_e(f["nombre"])}</a></td>'
            f"<td>{_e(f['marca'])}</td><td>{_e(f['tipo'])}</td>"
            f'<td class="num" data-v="{0 if not btu else int(f["btu"])}">{btu}</td>'
            f'<td class="num" data-v="{f["precio_actual"]}">{cop(f["precio_actual"])}</td>'
            f'<td class="num" data-v="{f["descuento_calc"] if desc else 0}">{desc}</td>'
            f"<td>{_e(f['vendedor'])}</td></tr>"
        )

    tiles_html = "".join(
        f'<div class="tile"><div class="n">{_e(n)}</div><div class="l">{_e(lab)}</div></div>'
        for n, lab in tiles
    )
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aires acondicionados en Éxito.com – reporte</title>
<style>{CSS}</style></head>
<body class="viz-root"><main>
<h1>Aires acondicionados en Éxito.com</h1>
<p class="sub">Extracción del {_e(fecha)} · {ind["paginas"]} páginas del listado ·
<a href="{BASE_URL}">categoría en el sitio</a></p>
<section class="tiles">{tiles_html}</section>

<h2>¿Qué hay realmente en la categoría?</h2>
<p class="nota">El listado mezcla equipos con ventiladores, enfriadores pequeños, calentadores
y repuestos. El resto del reporte usa solo los equipos de aire acondicionado.</p>
{g_cat}

<h2>Precio mediano según capacidad</h2>
<p class="nota">Solo capacidades con al menos 2 equipos. Se usa la mediana porque hay precios
extremos.</p>
{g_btu}

<h2>Inverter frente a convencional</h2>
{g_tipo}

<h2>Marcas con más equipos publicados</h2>
{g_marca}

<h2>Tabla de equipos</h2>
<input id="buscar" type="search" placeholder="Filtrar por nombre, marca, vendedor…"
 aria-label="Filtrar tabla"> <span id="conteo" class="nota">{len(filas)} productos</span>
<table id="tabla"><thead><tr><th>Producto</th><th>Marca</th><th>Tipo</th>
<th class="num">BTU</th><th class="num">Precio</th><th class="num">Desc.</th><th>Vendedor</th>
</tr></thead><tbody>{"".join(filas)}</tbody></table>
<p class="nota"><a href="datos.csv">Descargar CSV completo</a> ·
<a href="resumen.json">resumen.json</a></p>

<footer>Generado automáticamente por GitHub Actions con aires-exito v{__version__}.
Proyecto académico – IU Digital de Antioquia, Programación para Análisis de Datos.
Datos públicos del sitio, sin información personal.</footer>
</main><div id="tip" role="tooltip"></div><script>{JS}</script></body></html>
"""


def generar_sitio(entrada: Path, salida: Path, fecha: str | None = None) -> dict:
    df = pd.read_csv(entrada, encoding="utf-8-sig")
    r = calcular(df)
    fecha = fecha or date.today().isoformat()
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "index.html").write_text(construir_html(df, r, fecha), encoding="utf-8")
    shutil.copyfile(entrada, salida / "datos.csv")
    (salida / "resumen.json").write_text(
        json.dumps({"fecha": fecha, **r}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (salida / ".nojekyll").write_text("", encoding="utf-8")
    return r
