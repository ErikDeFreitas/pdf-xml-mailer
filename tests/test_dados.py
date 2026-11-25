import importlib
from pathlib import Path

from enviador_pdf_xml import dados, modelo


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


