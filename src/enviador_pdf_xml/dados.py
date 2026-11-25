"""Pastas de dados do Enviador. Só stdlib; nada é criado ao importar.

ENVIADOR_DADOS (testes) substitui as duas pastas; sem ela, a configuração fica em %APPDATA% e o
cache de token em %LOCALAPPDATA%.
"""

import os
from pathlib import Path

NOME_PASTA = "EnviadorEmails"


def pasta_config() -> Path:
    var = os.environ.get("ENVIADOR_DADOS")
    if var:
        return Path(var)
    base = os.environ.get("APPDATA")
    raiz = Path(base) if base else Path.home() / "AppData" / "Roaming"
    return raiz / NOME_PASTA


def pasta_local() -> Path:
    var = os.environ.get("ENVIADOR_DADOS")
    if var:
        return Path(var)
    base = os.environ.get("LOCALAPPDATA")
    raiz = Path(base) if base else Path.home() / "AppData" / "Local"
    return raiz / NOME_PASTA


PASTA: Path = pasta_local()
