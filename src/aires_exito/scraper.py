"""Recorrido del listado con Selenium.

La lógica de paginación (``recorrer_paginas``) está separada del navegador:
recibe una función ``obtener_html(pagina) -> str | None``. Así el pipeline de CI
puede probar la paginación y el control de duplicados sin abrir Chrome.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager

import pandas as pd

from . import BASE_URL
from .parser import parsear_pagina

MAX_PAGINAS = 40
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def recorrer_paginas(
    obtener_html: Callable[[int], str | None],
    max_paginas: int = MAX_PAGINAS,
    pausa: Callable[[], None] | None = None,
    log: Callable[[str], None] = print,
) -> pd.DataFrame:
    """Visita ?page=1, 2, ... y se detiene en la primera página vacía o sin productos nuevos."""
    productos: list[dict] = []
    urls_vistas: set[str] = set()
    for pagina in range(1, max_paginas + 1):
        html = obtener_html(pagina)
        if not html:
            log(f"Página {pagina}: sin productos. Fin del recorrido.")
            break
        tarjetas = parsear_pagina(html)
        nuevos = 0
        for p in tarjetas:
            if p["url"] and p["url"] not in urls_vistas:
                urls_vistas.add(p["url"])
                p["pagina"] = pagina
                productos.append(p)
                nuevos += 1
        log(f"Página {pagina}: {len(tarjetas)} tarjetas, {nuevos} productos nuevos.")
        if nuevos == 0:
            break
        if pausa:
            pausa()
    return pd.DataFrame(productos)


# --------------------------------------------------------------------------- Selenium


def crear_driver():  # pragma: no cover - requiere Chrome instalado
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    for arg in (
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-extensions",
        "--window-size=1920,1080",
        f"--user-agent={USER_AGENT}",
    ):
        opts.add_argument(arg)
    return webdriver.Chrome(options=opts)


def scroll_hasta_el_final(driver, pausa=1.2, max_intentos=10):  # pragma: no cover
    """Baja por la página hasta que el número de tarjetas deja de crecer (lazy loading)."""
    from selenium.webdriver.common.by import By

    previo = -1
    for _ in range(max_intentos):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(pausa)
        actual = len(driver.find_elements(By.TAG_NAME, "article"))
        if actual == previo:
            break
        previo = actual


@contextmanager
def navegador() -> Iterator[Callable[[int], str | None]]:  # pragma: no cover
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    driver = crear_driver()
    wait = WebDriverWait(driver, 15)

    def obtener_html(pagina: int) -> str | None:
        driver.get(f"{BASE_URL}?page={pagina}")
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
        except TimeoutException:
            return None
        scroll_hasta_el_final(driver)
        return driver.page_source

    try:
        yield obtener_html
    finally:
        driver.quit()


def scrapear_todo(max_paginas: int = MAX_PAGINAS) -> pd.DataFrame:  # pragma: no cover
    with navegador() as obtener_html:
        return recorrer_paginas(
            obtener_html,
            max_paginas=max_paginas,
            pausa=lambda: time.sleep(random.uniform(1.5, 3.0)),
        )
