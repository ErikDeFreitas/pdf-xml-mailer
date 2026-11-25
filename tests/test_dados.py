import importlib
from pathlib import Path

from enviador_pdf_xml import conta, dados, modelo


def test_enviador_dados_substitui_as_duas_pastas(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIADOR_DADOS", str(tmp_path / "x"))
    assert dados.pasta_config() == tmp_path / "x"
    assert dados.pasta_local() == tmp_path / "x"


def test_sem_variavel_usa_appdata_e_localappdata(tmp_path, monkeypatch):
    monkeypatch.delenv("ENVIADOR_DADOS")
    monkeypatch.setenv("APPDATA", str(tmp_path / "roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    assert dados.pasta_config() == tmp_path / "roaming" / "EnviadorEmails"
    assert dados.pasta_local() == tmp_path / "local" / "EnviadorEmails"
    assert dados.NOME_PASTA == modelo.APLICACAO


def test_importar_nao_cria_pasta(tmp_path, monkeypatch):
    alvo = tmp_path / "nao_criar"
    monkeypatch.setenv("ENVIADOR_DADOS", str(alvo))
    importlib.reload(dados)
    assert not alvo.exists()
    assert isinstance(dados.PASTA, Path)


def test_criar_app_mesmos_parametros(monkeypatch):
    import msal
    from msal_extensions import PersistedTokenCache

    guardado = {}

    class AppFalso:
        def __init__(self, client_id, **kw):
            guardado["client_id"] = client_id
            guardado.update(kw)

    monkeypatch.setattr(msal, "PublicClientApplication", AppFalso)
    conta._criar_app()
    assert guardado["client_id"] == modelo.CLIENT_ID
    assert guardado["authority"] == f"https://login.microsoftonline.com/{modelo.TENANT_ID}"
    assert isinstance(guardado["token_cache"], PersistedTokenCache)
    assert guardado["timeout"] == 15
    assert conta.caminho_cache().parent.exists()
