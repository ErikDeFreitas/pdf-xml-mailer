"""Conta Microsoft (OAuth 2.0) via MSAL. Nenhuma senha passa por aqui.

O login abre a página da Microsoft no navegador. O token fica num cache criptografado
pelo Windows (DPAPI) em %LOCALAPPDATA%\\EnviadorEmails\\token_cache.bin e é renovado sozinho.
"""
from __future__ import annotations

import os
from pathlib import Path

from core import modelo

TEMPO_LOGIN = 180  # segundos esperando o login no navegador

class ContaNaoConfigurada(Exception):
    """CLIENT_ID/TENANT_ID ainda não preenchidos em core/modelo.py."""


class FalhaLogin(Exception):
    """Mensagem já pronta para mostrar ao usuário."""


def caminho_cache() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    raiz = Path(base) if base else Path.home() / "AppData" / "Local"
    return raiz / modelo.APLICACAO / "token_cache.bin"


def _criar_app():
    if not modelo.CLIENT_ID or not modelo.TENANT_ID:
        raise ContaNaoConfigurada(
            "O login Microsoft ainda não foi configurado nesta versão (CLIENT_ID/TENANT_ID)."
        )
    import msal

    return msal.PublicClientApplication(
        modelo.CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{modelo.TENANT_ID}",
        token_cache=_criar_cache(),
    )


def _criar_cache():
    """Cache de tokens do MSAL gravado em disco criptografado com DPAPI (por usuário do Windows)."""
    from msal_extensions import PersistedTokenCache, build_encrypted_persistence

    cache = caminho_cache()
    cache.parent.mkdir(parents=True, exist_ok=True)
    return PersistedTokenCache(build_encrypted_persistence(str(cache)))


class Conta:
    def __init__(self, app=None):
        self._app = app if app is not None else _criar_app()

    def _conta(self):
        contas = self._app.get_accounts()
        return contas[0] if contas else None

    def email(self) -> str | None:
        conta = self._conta()
        return conta.get("username") if conta else None

    def entrar(self) -> str:
        # timeout: se a pessoa fechar o navegador sem logar, o app não fica preso esperando.
        resultado = self._app.acquire_token_interactive(modelo.ESCOPOS, prompt="select_account",
                                                        timeout=TEMPO_LOGIN)
        if not resultado or "access_token" not in resultado:
            descricao = (resultado or {}).get("error_description") or "Login cancelado."
            raise FalhaLogin(descricao)
        email = self.email()
        if not email:
            raise FalhaLogin("Não foi possível identificar a conta logada.")
        return email

    def token(self) -> str:
        conta = self._conta()
        resultado = self._app.acquire_token_silent(modelo.ESCOPOS, account=conta) if conta else None
        if not resultado or "access_token" not in resultado:
            raise FalhaLogin("Sua sessão expirou. Entre novamente com a Microsoft.")
        return resultado["access_token"]

    def sair(self) -> None:
        for conta in self._app.get_accounts():
            self._app.remove_account(conta)
