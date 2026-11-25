from tcm_ui import microsoft
import pytest

from enviador_pdf_xml import cli, configuracao, envio
from enviador_pdf_xml.configuracao import Configuracao
from tests.test_lote import FakeSMTP, pares


@pytest.fixture
def appdata(tmp_path, monkeypatch):
    pasta = tmp_path / "appdata"
    monkeypatch.setenv("APPDATA", str(pasta))
    return pasta


@pytest.fixture
def com_config(appdata):
    configuracao.salvar(Configuracao(para=["a@b.com"], cco=["x@y.com"], assunto="NF {nome} - {vcto}"))


def sem_conta():
    raise AssertionError("não devia criar a conta")


class ContaFalsa:
    def email(self):
        return "eu@tcm.com"

    def token(self):
        return "T"


def test_cli_sem_configuracao_retorna_2(tmp_path, appdata, capsys):
    assert cli.main([str(tmp_path), "--vcto", "20/11/2026"], conta_factory=sem_conta) == 2
    assert "Configure" in capsys.readouterr().out


def test_cli_vcto_invalido_retorna_2(tmp_path, com_config):
    assert cli.main([str(tmp_path), "--vcto", "31/02/2026"], conta_factory=sem_conta) == 2


def test_cli_dry_run_lista_assuntos(tmp_path, com_config, capsys):
    pasta = tmp_path / "docs"
    pasta.mkdir()
    pares(pasta, "123")
    assert cli.main([str(pasta), "--vcto", "20/11/2026", "--dry-run"], conta_factory=sem_conta) == 0
    saida = capsys.readouterr().out
    assert "NF 123 - 20/11/2026" in saida
    assert "a@b.com" in saida


def test_cli_envia_com_conta_falsa(tmp_path, com_config, monkeypatch, capsys):
    pasta = tmp_path / "docs"
    pasta.mkdir()
    pares(pasta, "1")
    smtp = FakeSMTP()
    monkeypatch.setattr(microsoft, "abrir_smtp", lambda email, token: smtp)
    monkeypatch.setattr(envio.time, "sleep", lambda s: None)
    assert cli.main([str(pasta), "--vcto", "20/11/2026"], conta_factory=ContaFalsa) == 0
    assert (pasta / "enviados" / "1.pdf").exists()
    assert smtp.enviadas[0]["Bcc"] == "x@y.com"
    assert smtp.enviadas[0]["Subject"] == "NF 1 - 20/11/2026"
    assert "Concluído: 1 enviado(s)" in capsys.readouterr().out


def test_cli_assunto_de_exemplo_nao_envia(tmp_path, appdata, capsys):
    configuracao.salvar(Configuracao(para=["a@b.com"]))  # assunto padrão (TEXTO FIXO)
    pasta = tmp_path / "docs"
    pasta.mkdir()
    pares(pasta, "1")
    assert cli.main([str(pasta), "--vcto", "20/11/2026"], conta_factory=sem_conta) == 2
    assert "Configurar e-mail" in capsys.readouterr().out
