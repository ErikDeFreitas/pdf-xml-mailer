import gc
import logging
import threading
import time

import pytest
from PySide6.QtWidgets import QApplication
from tcm_ui.components import Modal

from enviador_pdf_xml import configuracao, instancia
from enviador_pdf_xml.configuracao import Configuracao
from tcm_ui.microsoft import ContaNaoConfigurada
from enviador_pdf_xml.instancia import Enviador
from tests.test_lote import FakeSMTP, pares
from tests.test_ui_conta import FakeConta


@pytest.fixture(autouse=True)
def _lixo_antes_do_teste():
    """Libera o lixo cíclico dos testes anteriores agora: um GC com a thread do envio rodando aborta o Qt."""
    gc.collect()


@pytest.fixture
def inst(qtbot, contexto, monkeypatch):
    monkeypatch.setattr(instancia, "FABRICA_CONTA", lambda: FakeConta("eu@tcm.com"))
    objeto = Enviador(contexto)
    yield objeto
    if objeto.tela is not None:
        qtbot.addWidget(objeto.tela)


def test_widget_e_criado_uma_vez(inst):
    assert inst.widget("enviar") is inst.widget("enviar")


def test_pagina_desconhecida(inst):
    with pytest.raises(KeyError):
        inst.widget("outra")


def test_sem_acoes_no_cabecalho(inst):
    assert inst.acoes_cabecalho("enviar") == []


def test_conta_e_criada_com_a_tela(qtbot, inst):
    assert inst.tela is None
    tela = inst.widget("enviar")
    qtbot.waitUntil(lambda: tela.email() == "eu@tcm.com", timeout=3000)
    assert not tela._conectando


def test_pode_fechar_so_sem_envio(inst):
    assert inst.pode_fechar()  # antes de abrir a tela
    tela = inst.widget("enviar")
    assert inst.pode_fechar()
    tela._thread = object()  # simula envio em andamento
    assert not inst.pode_fechar()
    tela._thread = None


def test_fabrica_que_falha_abre_a_tela_com_aviso(qtbot, inst, monkeypatch, caplog):
    def falha():
        raise OSError("sem rede")

    monkeypatch.setattr(instancia, "FABRICA_CONTA", falha)
    inst.contexto.log.propagate = True
    with caplog.at_level(logging.ERROR, logger="teste"):
        tela = inst.widget("enviar")
        qtbot.waitUntil(lambda: not tela._conectando, timeout=3000)
    assert tela.conta is None
    assert "Não foi possível conectar ao login Microsoft (verifique a internet). Detalhes no log."         in tela.aviso_login.text()
    assert not tela.aviso_login.isHidden()
    assert "sem rede" in caplog.text


def test_criar_conta_sem_login_configurado(monkeypatch):
    def nao_configurada():
        raise ContaNaoConfigurada("x")

    monkeypatch.setattr(instancia, "FABRICA_CONTA", nao_configurada)
    assert instancia.criar_conta(logging.getLogger("t")) == (
        None, "O login Microsoft ainda não foi configurado nesta versão. Fale com a TI.")


def test_criar_conta_devolve_a_conta(monkeypatch):
    conta = FakeConta("eu@tcm.com")
    monkeypatch.setattr(instancia, "FABRICA_CONTA", lambda: conta)
    assert instancia.criar_conta(logging.getLogger("t")) == (conta, "")


class ContaLenta(FakeConta):
    def token(self):
        return "T"


def test_ao_sair_do_programa_cancela_e_espera_a_thread(qtbot, inst, tmp_path, monkeypatch):
    """aboutToQuit: o e-mail em curso termina, o seguinte não sai e a thread acaba antes de o processo fechar."""
    caminho = tmp_path / "dados" / "config.json"
    configuracao.salvar(Configuracao(["a@b.com"], [], assunto="TCM - CTE {nome}"), caminho)
    monkeypatch.setattr(instancia, "FABRICA_CONTA", lambda: ContaLenta("eu@tcm.com"))
    tela = inst.widget("enviar")
    qtbot.waitUntil(lambda: tela.conta is not None, timeout=3000)
    tela.caminho_config = caminho
    tela.recarregar_conta()
    docs = tmp_path / "docs"
    docs.mkdir()
    lista = pares(docs, "1", "2")
    tela.adicionar([p for par in lista for p in (par.pdf, par.xml)])
    tela.campo_vcto.setText("20/11/2026")

    preso, solto = threading.Event(), threading.Event()
    smtp = FakeSMTP()
    original = smtp.send_message

    def devagar(msg):
        preso.set()
        solto.wait(5)  # segura o primeiro e-mail até o teste mandar sair
        original(msg)

    smtp.send_message = devagar
    monkeypatch.setattr("tcm_ui.microsoft.abrir_smtp", lambda email, token: smtp)
    monkeypatch.setattr(Modal, "confirmar", classmethod(lambda cls, *a, **k: True))

    tela._enviar()
    assert tela.rodando and not inst.pode_fechar()
    qtbot.waitUntil(preso.is_set, timeout=5000)

    threading.Timer(0.3, solto.set).start()  # a thread principal vai ficar presa em aguardar()
    QApplication.instance().aboutToQuit.emit()

    assert len(smtp.enviadas) == 1  # o segundo não saiu
    assert tela._thread is not None and tela._thread.isFinished()
    qtbot.waitUntil(lambda: not tela.rodando, timeout=5000)
    assert inst.pode_fechar()
    assert tela.status_de("1") == "Enviado" and tela.status_de("2") == "Pronto"
    assert (docs / "enviados" / "1.pdf").exists() and (docs / "2.pdf").exists()


# --- E1: a Conta (MSAL) é criada fora da thread da interface ------------------------------------

def test_widget_volta_na_hora_com_a_conta_ainda_sendo_criada(qtbot, inst, monkeypatch):
    solta = threading.Event()

    def lenta():
        solta.wait(10)
        return FakeConta("eu@tcm.com")

    monkeypatch.setattr(instancia, "FABRICA_CONTA", lenta)
    t0 = time.monotonic()
    tela = inst.widget("enviar")
    try:
        assert time.monotonic() - t0 < 1
        assert tela.aviso_login.text() == "Conectando à conta Microsoft…"
        assert not tela.aviso_login.isHidden()
        assert not tela.botao_enviar.isEnabled() and not tela.btn_config.isEnabled()
        assert tela.email() is None
    finally:
        solta.set()
    qtbot.waitUntil(lambda: tela.email() == "eu@tcm.com", timeout=3000)
    assert tela.aviso_login.isHidden() and tela.btn_config.isEnabled()


def test_enviar_continua_desativado_enquanto_conecta(qtbot, inst, monkeypatch, tmp_path):
    solta = threading.Event()
    monkeypatch.setattr(instancia, "FABRICA_CONTA", lambda: (solta.wait(10), FakeConta("eu@tcm.com"))[1])
    tela = inst.widget("enviar")
    try:
        tela.cfg = Configuracao(["a@b.com"], [], assunto="TCM - CTE {nome}")
        docs = tmp_path / "docs"
        docs.mkdir()
        tela.adicionar([p for par in pares(docs, "1") for p in (par.pdf, par.xml)])
        tela.campo_vcto.setText("20/11/2026")
        tela._atualizar_botao()
        assert not tela.botao_enviar.isEnabled()
        assert tela.abrir_configuracoes() is False  # não abre diálogo enquanto conecta
    finally:
        solta.set()
    qtbot.waitUntil(lambda: tela.conta is not None, timeout=3000)


def test_falha_mostra_tentar_de_novo_e_recria_a_conta(qtbot, inst, monkeypatch):
    chamadas = []

    def fabrica():
        chamadas.append(1)
        if len(chamadas) == 1:
            raise OSError("sem rede")
        return FakeConta("eu@tcm.com")

    monkeypatch.setattr(instancia, "FABRICA_CONTA", fabrica)
    tela = inst.widget("enviar")
    qtbot.waitUntil(lambda: not tela._conectando, timeout=3000)
    assert tela.conta is None and not tela.btn_tentar.isHidden()
    tela.btn_tentar.click()
    assert tela._conectando and tela.btn_tentar.isHidden()
    qtbot.waitUntil(lambda: tela.email() == "eu@tcm.com", timeout=3000)
    assert len(chamadas) == 2 and tela.btn_tentar.isHidden()


def test_configuracoes_sem_conta_por_falha_tenta_de_novo(qtbot, inst, monkeypatch):
    chamadas = []

    def fabrica():
        chamadas.append(1)
        raise OSError("sem rede")

    monkeypatch.setattr(instancia, "FABRICA_CONTA", fabrica)
    tela = inst.widget("enviar")
    qtbot.waitUntil(lambda: not tela._conectando, timeout=3000)
    assert tela.abrir_configuracoes() is False  # recriou em vez de abrir o diálogo
    qtbot.waitUntil(lambda: len(chamadas) == 2 and not tela._conectando, timeout=3000)


def test_nao_configurada_nao_oferece_tentar_de_novo(qtbot, inst, monkeypatch):
    def nao_configurada():
        raise ContaNaoConfigurada("x")

    monkeypatch.setattr(instancia, "FABRICA_CONTA", nao_configurada)
    tela = inst.widget("enviar")
    qtbot.waitUntil(lambda: not tela._conectando, timeout=3000)
    assert tela.btn_tentar.isHidden()
    assert "Fale com a TI" in tela.aviso_login.text()


def test_primeiro_acesso_espera_a_conta(qtbot, inst, monkeypatch):
    solta = threading.Event()
    monkeypatch.setattr(instancia, "FABRICA_CONTA", lambda: (solta.wait(10), FakeConta())[1])
    abertos = []
    tela = inst.widget("enviar")
    monkeypatch.setattr(tela, "abrir_configuracoes", lambda **kw: abertos.append(kw))
    tela._primeiro_acesso()  # o timer de 300 ms disparou com a conta ainda sendo criada
    assert abertos == [] and tela._primeiro_acesso_pendente
    solta.set()
    qtbot.waitUntil(lambda: abertos == [{"primeiro_acesso": True}], timeout=3000)


def test_fechar_com_a_conta_pendente_nao_trava_nem_quebra(qtbot, inst, monkeypatch):
    solta = threading.Event()
    monkeypatch.setattr(instancia, "FABRICA_CONTA", lambda: (solta.wait(10), FakeConta("eu@tcm.com"))[1])
    tela = inst.widget("enviar")
    t0 = time.monotonic()
    QApplication.instance().aboutToQuit.emit()  # a thread de criação é daemon: não se espera
    assert time.monotonic() - t0 < 1
    solta.set()
    qtbot.wait(200)  # a conta que chega depois do encerramento é ignorada
    assert tela.conta is None


def test_tela_destruida_antes_da_conta_nao_levanta(qtbot, inst, monkeypatch):
    solta = threading.Event()
    feito = threading.Event()

    def fabrica():
        solta.wait(10)
        return FakeConta()

    monkeypatch.setattr(instancia, "FABRICA_CONTA", fabrica)
    tela = inst.widget("enviar")
    erros = []
    original = threading.excepthook
    monkeypatch.setattr(threading, "excepthook", lambda args: erros.append(args))
    import shiboken6
    shiboken6.delete(tela)
    solta.set()
    qtbot.wait(300)
    assert erros == []
    inst.tela = None


def test_migra_o_login_antigo_ao_abrir(qtbot, inst, monkeypatch, tmp_path):
    """O login da 2.0 (cache em ENVIADOR_DADOS) vai para o cache compartilhado: ninguém precisa entrar de novo."""
    from enviador_pdf_xml import dados

    monkeypatch.setenv("TCM_CONTA_MICROSOFT", str(tmp_path / "novo"))
    antigo = dados.pasta_local() / "token_cache.bin"
    antigo.parent.mkdir(parents=True, exist_ok=True)
    antigo.write_bytes(b"C")
    try:
        tela = inst.widget("enviar")
        qtbot.waitUntil(lambda: tela.conta is not None, timeout=3000)
        assert (tmp_path / "novo" / "token_cache.bin").read_bytes() == b"C"
    finally:
        antigo.unlink()
