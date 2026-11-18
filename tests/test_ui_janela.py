import pytest
from PySide6.QtWidgets import QApplication

from core import configuracao, envio
from core.configuracao import Configuracao
from tests.test_lote import pares
from tests.test_ui_conta import FakeConta


@pytest.fixture(scope="module", autouse=True)
def app():
    app = QApplication.instance() or QApplication([])
    from ui.themes import theme_manager
    theme_manager.apply()
    return app


@pytest.fixture
def janela(tmp_path):
    import main
    caminho = tmp_path / "config.json"
    configuracao.salvar(Configuracao(["a@b.com"], ["x@y.com"]), caminho)
    j = main.MainWindow(conta=FakeConta("eu@tcm.com"), caminho_config=caminho)
    yield j
    j.close()


def arquivos(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    lista = pares(docs, "1", "2")
    (docs / "3.pdf").write_bytes(b"%PDF-1.4")
    return docs, [p for par in lista for p in (par.pdf, par.xml)] + [docs / "3.pdf"]


def test_janela_abre(janela):
    pagina = janela.pagina
    assert "a@b.com" in pagina.lbl_para.text()
    assert "x@y.com" in pagina.lbl_para.text()  # Cco só é exibido; edição só em Configurações
    assert "eu@tcm.com" in pagina.lbl_conta.text()
    assert not hasattr(pagina, "campo_cco")


def test_botoes_de_envio(janela):
    pagina = janela.pagina
    assert pagina.btn_pasta.parent() is pagina.botao_enviar.parent()  # lado a lado no card Envio
    assert pagina.btn_pasta.property("variant") == "primary"         # azul
    assert pagina.botao_enviar.property("variant") == "danger"       # vermelho


def test_adicionar_monta_pares(janela, tmp_path):
    _, lista = arquivos(tmp_path)
    pagina = janela.pagina
    pagina.adicionar(lista)
    assert pagina.tabela.rowCount() == 3
    assert pagina.botao_enviar.text() == "Enviar 2 e-mails"
    assert envio.montar_assunto("1") in pagina.lbl_assunto.text()


def test_adicionar_pasta(janela, tmp_path):
    docs, _ = arquivos(tmp_path)
    janela.pagina.adicionar([docs])
    assert janela.pagina.tabela.rowCount() == 3


def test_enviar_desabilitado_sem_vencimento(janela, tmp_path):
    _, lista = arquivos(tmp_path)
    pagina = janela.pagina
    pagina.adicionar(lista)
    assert not pagina.botao_enviar.isEnabled()
    pagina.campo_vcto.setText("20/11/2026")
    assert pagina.botao_enviar.isEnabled()
    pagina.campo_vcto.setText("31/02/2026")
    assert not pagina.botao_enviar.isEnabled()


def test_adicionar_duas_vezes_nao_duplica(janela, tmp_path):
    _, lista = arquivos(tmp_path)
    janela.pagina.adicionar(lista)
    janela.pagina.adicionar(lista)
    assert janela.pagina.tabela.rowCount() == 3


def test_resultado_atualiza_status_e_limpar(janela, tmp_path):
    _, lista = arquivos(tmp_path)
    pagina = janela.pagina
    pagina.adicionar(lista)
    pagina._ao_concluir_par(envio.ResultadoPar("1", "erro", "falhou"))
    assert pagina.status_de("1") == "Erro"
    pagina.limpar()
    assert pagina.tabela.rowCount() == 0
    assert pagina.botao_enviar.text() == "Enviar"


def test_enviado_com_aviso_nao_fica_pendente(janela, tmp_path):
    _, lista = arquivos(tmp_path)
    pagina = janela.pagina
    pagina.adicionar(lista)
    pagina._ao_concluir_par(envio.ResultadoPar("1", "aviso", "não foi movido"))
    pagina._ao_terminar_thread()
    assert [p.nome for p in pagina._pares] == ["2"]
