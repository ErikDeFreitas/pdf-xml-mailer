import pytest
from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl
from PySide6.QtGui import QDropEvent
from tcm_ui.components import Etiqueta, Modal

from enviador_pdf_xml import configuracao, dialogos, envio
from enviador_pdf_xml.configuracao import Configuracao
from enviador_pdf_xml.tela import ROLE_NOME, TelaEnviar
from tests.test_lote import pares
from tests.test_ui_conta import FakeConta


@pytest.fixture
def caminho(tmp_path):
    caminho = tmp_path / "config.json"
    configuracao.salvar(Configuracao(["a@b.com"], [], assunto="TCM - CTE {nome}"), caminho)
    return caminho


@pytest.fixture
def tela(qtbot, contexto, caminho):
    t = TelaEnviar(contexto, FakeConta("eu@tcm.com"), caminho)
    qtbot.addWidget(t)
    return t


def soltar(tela, *caminhos):
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(c)) for c in caminhos])
    evento = QDropEvent(QPointF(5, 5), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    tela.dropEvent(evento)
    return evento


def test_soltar_arquivos_adiciona(tela, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    lista = pares(docs, "1", "2")
    evento = soltar(tela, lista[0].pdf, lista[0].xml, docs / "x.txt")
    assert evento.isAccepted()
    assert tela.tabela.rowCount() == 1
    assert tela.acceptDrops()


def test_soltar_pasta_adiciona(tela, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    pares(docs, "1", "2")
    soltar(tela, docs)
    assert tela.tabela.rowCount() == 2


def test_soltar_durante_envio_e_recusado(tela, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    pares(docs, "1")
    tela._thread = object()  # simula envio em andamento
    try:
        soltar(tela, docs)
        assert tela.tabela.rowCount() == 0
    finally:
        tela._thread = None


def test_primeiro_acesso_abre_uma_vez(qtbot, contexto, tmp_path, monkeypatch):
    aberturas = []
    monkeypatch.setattr(dialogos.DialogoConta, "exec", lambda self: aberturas.append(self) or 0)
    t = TelaEnviar(contexto, FakeConta("eu@tcm.com"), tmp_path / "sem_config.json")  # sem Para: primeiro acesso
    qtbot.addWidget(t)
    t.show()
    qtbot.waitUntil(lambda: len(aberturas) == 1, timeout=3000)
    assert aberturas[0].windowTitle() == "Bem-vindo! Configure o envio"
    t.hide()
    t.show()
    qtbot.wait(500)
    assert len(aberturas) == 1


def test_primeiro_acesso_nao_abre_com_tudo_configurado(qtbot, tela, monkeypatch):
    aberturas = []
    monkeypatch.setattr(dialogos.DialogoConta, "exec", lambda self: aberturas.append(self) or 0)
    tela.show()
    qtbot.wait(500)
    assert aberturas == []


def preparar_erro(tela, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    pares(docs, "1", "2")
    tela.adicionar([docs])
    tela._ao_concluir_par(envio.ResultadoPar("1", "erro", "falhou ao conectar"))
    tela._ao_concluir_par(envio.ResultadoPar("2", "aviso", "não foi movido"))


def test_etiqueta_de_erro_abre_detalhe(tela, tmp_path, monkeypatch):
    chamadas = []
    monkeypatch.setattr(Modal, "informar",
                        classmethod(lambda cls, parent, titulo, texto, tom="info": chamadas.append(
                            (parent, titulo, texto, tom))))
    preparar_erro(tela, tmp_path)
    etiqueta = tela.tabela.cellWidget(0, 3).findChild(Etiqueta)
    assert etiqueta.text() == "Erro"
    etiqueta.clicada.emit()
    assert chamadas == [(tela.contexto.janela, "1 · Erro", "falhou ao conectar", "perigo")]
    tela.tabela.cellWidget(1, 3).findChild(Etiqueta).clicada.emit()
    assert chamadas[-1][1:] == ("2 · Enviado com aviso", "não foi movido", "aviso")


def test_clique_na_linha_abre_detalhe(tela, tmp_path, monkeypatch):
    chamadas = []
    monkeypatch.setattr(Modal, "informar",
                        classmethod(lambda cls, parent, titulo, texto, tom="info": chamadas.append(titulo)))
    preparar_erro(tela, tmp_path)
    assert tela.tabela.item(0, 0).data(ROLE_NOME) == "1"
    tela.tabela.cellClicked.emit(0, 1)
    assert chamadas == ["1 · Erro"]


def test_etiqueta_sem_detalhe_nao_e_clicavel(tela, tmp_path, monkeypatch):
    chamadas = []
    monkeypatch.setattr(Modal, "informar", classmethod(lambda cls, *a, **k: chamadas.append(a)))
    docs = tmp_path / "docs"
    docs.mkdir()
    pares(docs, "1")
    tela.adicionar([docs])
    tela.tabela.cellClicked.emit(0, 1)  # "Pronto" não tem detalhe
    assert chamadas == []


def test_sessao_expirada_abre_conta(qtbot, tela, monkeypatch):
    aberturas = []
    monkeypatch.setattr(dialogos.DialogoConta, "exec", lambda self: aberturas.append(self) or 0)
    tela._ao_expirar("Sua sessão expirou.")
    qtbot.waitUntil(lambda: len(aberturas) == 1, timeout=2000)
    assert aberturas[0].parent() is tela.contexto.janela
    assert not aberturas[0].botao_entrar.isHidden()  # força "Entrar com a Microsoft"
    assert tela.lbl_resumo.text() == "Sua sessão expirou."


def test_sessao_expirada_com_o_programa_fechando_nao_abre_conta(qtbot, tela, monkeypatch):
    aberturas = []
    monkeypatch.setattr(dialogos.DialogoConta, "exec", lambda self: aberturas.append(self) or 0)
    tela._encerrando = True
    tela._ao_expirar("Sua sessão expirou.")
    qtbot.wait(100)
    assert aberturas == []


def test_dialogos_de_arquivo_usam_a_janela_como_pai(tela, monkeypatch):
    pais = []
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(QFileDialog, "getOpenFileNames", staticmethod(lambda parent, *a: pais.append(parent) or ([], "")))
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", staticmethod(lambda parent, *a: pais.append(parent) or ""))
    tela._escolher_arquivos()
    tela._escolher_pasta()
    assert pais == [tela.contexto.janela] * 2


def test_cancelar_envio_pede_confirmacao(tela, monkeypatch):
    chamadas = []

    def confirmar(cls, parent, titulo, descricao, texto_ok="Confirmar", destrutivo=False, tom=None, *,
                  texto_cancelar="Cancelar"):
        chamadas.append((parent, titulo, texto_ok, destrutivo, texto_cancelar))
        return False

    monkeypatch.setattr(Modal, "confirmar", classmethod(confirmar))
    tela._thread = object()
    try:
        tela._cancelar()
    finally:
        tela._thread = None
    assert chamadas == [(tela.contexto.janela, "Cancelar envio?", "Cancelar envio", True, "Continuar")]
