from pathlib import Path

import pytest

from aires_exito.parser import parsear_pagina

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def html_muestra() -> str:
    return (FIXTURES / "tarjetas_muestra.html").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def productos(html_muestra) -> list[dict]:
    """Las 10 tarjetas reales del fixture, ya extraídas."""
    return parsear_pagina(html_muestra)
