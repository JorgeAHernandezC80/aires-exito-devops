"""Pruebas de la paginación sin abrir el navegador (se simula obtener_html)."""

from aires_exito.scraper import recorrer_paginas


def _tarjeta(slug: str, precio: str = "1.000.000") -> str:
    return f'<article><a href="/{slug}/p">Aire {slug} 12000 Btu</a> $ {precio}</article>'


def test_se_detiene_en_pagina_vacia():
    paginas = {1: _tarjeta("a") + _tarjeta("b"), 2: _tarjeta("c")}
    visitadas = []

    def obtener(n):
        visitadas.append(n)
        return paginas.get(n)

    df = recorrer_paginas(obtener, log=lambda _: None)
    assert len(df) == 3
    assert visitadas == [1, 2, 3]
    assert df["pagina"].tolist() == [1, 1, 2]


def test_descarta_duplicados_y_para_si_no_hay_nuevos():
    # La página 2 repite la 1 (pasa cuando el sitio ignora ?page=N): debe detenerse.
    repetida = _tarjeta("a") + _tarjeta("b")
    df = recorrer_paginas(lambda n: repetida, max_paginas=10, log=lambda _: None)
    assert len(df) == 2
    assert df["url"].is_unique


def test_respeta_max_paginas():
    df = recorrer_paginas(lambda n: _tarjeta(f"p{n}"), max_paginas=4, log=lambda _: None)
    assert len(df) == 4


def test_pausa_entre_paginas():
    llamadas = []
    recorrer_paginas(
        lambda n: _tarjeta(f"p{n}") if n < 3 else None,
        pausa=lambda: llamadas.append(1),
        log=lambda _: None,
    )
    assert len(llamadas) == 2
