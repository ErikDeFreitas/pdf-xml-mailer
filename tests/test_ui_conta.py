import pytest
from PySide6.QtWidgets import QApplication, QDialog

from core import configuracao
from core.configuracao import Configuracao


@pytest.fixture(scope="module", autouse=True)
def app():
    app = QApplication.instance() or QApplication([])
    from ui.themes import theme_manager
    theme_manager.apply()
    return app


class FakeConta:
    def __init__(self, email=None):
        self._email = email
        self.saiu = False

    def email(self):
        return self._email

    def entrar(self):
        self._email = "eu@tcm.com"
        return self._email

    def sair(self):
        self._email = None
        self.saiu = True


def modal(conta, cfg=None, caminho=None):
    from ui.conta import ContaModal
    return ContaModal(conta, cfg, caminho_config=caminho)


def test_salvar_desabilitado_sem_login(tmp_path):
    m = modal(FakeConta(), caminho=tmp_path / "c.json")
    assert not m.botao_salvar.isEnabled()
    assert m.botao_entrar.isVisible() or not m.botao_entrar.isHidden()


def test_salvar_grava_config(tmp_path):
    caminho = tmp_path / "c.json"
    m = modal(FakeConta("eu@tcm.com"), caminho=caminho)
    m.campo_para.setText("a@b.com")
    m.campo_cco.setText("x@y.com")
    m.botao_salvar.click()
    assert m.result() == QDialog.DialogCode.Accepted
    assert m.resultado == Configuracao(para=["a@b.com"], cco=["x@y.com"])
    assert configuracao.carregar(caminho) == m.resultado


def test_preenche_com_config_existente(tmp_path):
    m = modal(FakeConta("eu@tcm.com"), Configuracao(["a@b.com", "c@d.com"], ["x@y.com"]), tmp_path / "c.json")
    assert m.campo_para.text() == "a@b.com; c@d.com"
    assert m.campo_cco.text() == "x@y.com"


def test_para_invalido_mostra_erro(tmp_path):
    caminho = tmp_path / "c.json"
    m = modal(FakeConta("eu@tcm.com"), caminho=caminho)
    m.campo_para.setText("a@b.com; nada")
    m.botao_salvar.click()
    assert m.result() != QDialog.DialogCode.Accepted
    assert m.campo_para.property("error") is True
    assert not caminho.exists()


def test_sair_volta_para_nao_logado(tmp_path):
    conta = FakeConta("eu@tcm.com")
    m = modal(conta, caminho=tmp_path / "c.json")
    m.botao_sair.click()
    assert conta.saiu
    assert not m.botao_salvar.isEnabled()


def test_sem_conta_configurada_desabilita_login(tmp_path):
    m = modal(None, caminho=tmp_path / "c.json")
    assert not m.botao_entrar.isEnabled()
    assert not m.botao_salvar.isEnabled()
