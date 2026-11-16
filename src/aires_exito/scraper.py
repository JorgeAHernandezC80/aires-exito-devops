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
from pathlib import Path

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


CARPETA_DEBUG = Path("debug")


def guardar_evidencia(driver, pagina: int) -> None:  # pragma: no cover
    """Guarda HTML y captura de lo que recibió el navegador, para diagnosticar bloqueos."""
    CARPETA_DEBUG.mkdir(exist_ok=True)
    (CARPETA_DEBUG / f"page_{pagina:02d}.html").write_text(driver.page_source, encoding="utf-8")
    driver.save_screenshot(str(CARPETA_DEBUG / f"page_{pagina:02d}.png"))
    print(f"  título recibido: {driver.title!r} | url final: {driver.current_url}")
    print(f"  evidencia guardada en {CARPETA_DEBUG}/page_{pagina:02d}.(html|png)")


@contextmanager
def navegador(intentos: int = 3) -> Iterator[Callable[[int], str | None]]:  # pragma: no cover
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    driver = crear_driver()
    wait = WebDriverWait(driver, 30)

    def obtener_html(pagina: int) -> str | None:
        # La primera página se reintenta: si falla, el sitio está lento o bloqueó al runner.
        # En las siguientes, no encontrar <article> es el fin normal del listado.
        for intento in range(1, (intentos if pagina == 1 else 1) + 1):
            driver.get(f"{BASE_URL}?page={pagina}")
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
            except TimeoutException:
                if pagina == 1:
                    print(f"Página 1, intento {intento}/{intentos}: no aparecieron productos.")
                    guardar_evidencia(driver, pagina)
                    time.sleep(5 * intento)
                continue
            scroll_hasta_el_final(driver)
            return driver.page_source
        return None

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
