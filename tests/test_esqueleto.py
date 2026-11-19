def test_atualizacao_aponta_para_este_repo():
    from core import atualizacao
    assert atualizacao.REPOSITORIO == "ErikDeFreitas/pdf-xml-mailer"
    assert atualizacao.NOME_EXE == "EnviadorEmails.exe"
    assert atualizacao.NOME_SHA == "EnviadorEmails.exe.sha256"


def test_modelo_tem_variaveis():
    from core import modelo
    assert "{nome}" in modelo.ASSUNTO
    assert "{vcto}" in modelo.CORPO


def test_tema_carrega():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from ui.themes import theme_manager, APLICACAO
    assert APLICACAO == "EnviadorEmails"
    assert theme_manager.stylesheet()
