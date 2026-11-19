"""Modal "Configurar e-mail": assunto e corpo salvos para os próximos envios."""
import pytest
from PySide6.QtWidgets import QApplication, QDialog

from core import configuracao, modelo
from core.configuracao import Configuracao


@pytest.fixture(scope="module", autouse=True)
def app():
    app = QApplication.instance() or QApplication([])
    from ui.themes import theme_manager
    theme_manager.apply()
    return app


@pytest.fixture
def caminho(tmp_path):
    caminho = tmp_path / "c.json"
    configuracao.salvar(Configuracao(["a@b.com"], ["x@y.com"]), caminho)
    return caminho


def modal(caminho):
    from ui.email import EmailModal
    return EmailModal(configuracao.carregar(caminho), caminho_config=caminho)


def test_abre_com_texto_salvo(caminho):
    configuracao.salvar(Configuracao(["a@b.com"], [], "NF {nome}", "Oi **{vcto}**"), caminho)
    m = modal(caminho)
    assert m.campo_assunto.text() == "NF {nome}"
    assert m.campo_corpo.toPlainText() == "Oi **{vcto}**"


def test_salvar_grava_e_mantem_destinatarios(caminho):
    m = modal(caminho)
    m.campo_assunto.setText("TCM - CTE {nome}")
    m.campo_corpo.setPlainText("Segue\n\n**Vcto: {vcto}**")
    m.botao_salvar.click()
    assert m.result() == QDialog.DialogCode.Accepted
    salvo = configuracao.carregar(caminho)
    assert salvo == Configuracao(["a@b.com"], ["x@y.com"], "TCM - CTE {nome}", "Segue\n\n**Vcto: {vcto}**")
    assert m.resultado == salvo


def test_campo_desconhecido_nao_salva(caminho):
    m = modal(caminho)
    m.campo_assunto.setText("CTE {nmoe}")
    m.botao_salvar.click()
    assert m.result() != QDialog.DialogCode.Accepted
    assert m.campo_assunto.property("error") is True
    assert configuracao.carregar(caminho).assunto == modelo.ASSUNTO


def test_assunto_de_exemplo_nao_salva(caminho):
    m = modal(caminho)
    m.botao_salvar.click()  # ainda é o "TEXTO FIXO" padrão
    assert m.result() != QDialog.DialogCode.Accepted
    assert m.campo_assunto.property("error") is True


def test_restaurar_padrao(caminho):
    configuracao.salvar(Configuracao(["a@b.com"], [], "NF {nome}", "Oi"), caminho)
    m = modal(caminho)
    m.botao_restaurar.click()
    assert m.campo_assunto.text() == modelo.ASSUNTO
    assert m.campo_corpo.toPlainText() == modelo.CORPO
    assert configuracao.carregar(caminho).assunto == "NF {nome}"  # só grava no Salvar


def test_previa_mostra_exemplo_com_negrito(caminho):
    m = modal(caminho)
    m.campo_assunto.setText("NF {nome}")
    m.campo_corpo.setPlainText("**Vcto: {vcto}**")
    assert "NF 123456" in m.previa_assunto.text()
    assert "<b>Vcto: " in m.previa_corpo.text()


def test_configuracoes_de_conta_nao_apagam_o_texto(caminho):
    from tests.test_ui_conta import FakeConta
    from ui.conta import ContaModal
    configuracao.salvar(Configuracao(["a@b.com"], [], "NF {nome}", "Oi"), caminho)
    m = ContaModal(FakeConta("eu@tcm.com"), configuracao.carregar(caminho), caminho_config=caminho)
    m.campo_para.setText("c@d.com")
    m.botao_salvar.click()
    salvo = configuracao.carregar(caminho)
    assert salvo.para == ["c@d.com"] and salvo.assunto == "NF {nome}" and salvo.corpo == "Oi"
