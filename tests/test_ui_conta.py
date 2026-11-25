from PySide6.QtWidgets import QApplication, QDialog

from enviador_pdf_xml import configuracao
from enviador_pdf_xml.configuracao import Configuracao
from enviador_pdf_xml.dialogos import DialogoConta


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
    return DialogoConta(conta, cfg, caminho_config=caminho)


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
    assert m.campo_para.property("erro") is True
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


def test_sessao_expirada_mostra_entrar(tmp_path):
    m = DialogoConta(FakeConta("eu@tcm.com"), None, caminho_config=tmp_path / "c.json", sessao_expirada=True)
    assert not m.botao_entrar.isHidden()
    assert not m.botao_salvar.isEnabled()


class ContaTravada(FakeConta):
    """Login que nunca volta sozinho: como o navegador parado numa página de erro da Microsoft."""

    def __init__(self):
        super().__init__()
        import threading
        self.liberar = threading.Event()

    def entrar(self):
        self.liberar.wait(5)
        return super().entrar()


def test_cancelar_fecha_durante_login_travado(tmp_path):
    import time
    conta = ContaTravada()
    m = modal(conta, caminho=tmp_path / "c.json")
    fechou = []
    m.finished.connect(fechou.append)
    m.open()
    m.botao_entrar.click()
    m.reject()  # X ou Cancelar
    try:
        assert fechou == [QDialog.DialogCode.Rejected]
        assert not m.isVisible()
        assert m.resultado is None
    finally:
        conta.liberar.set()
    # o login abandonado termina depois sem quebrar nada
    fim = time.monotonic() + 2
    while time.monotonic() < fim:
        QApplication.processEvents()
        time.sleep(0.01)
    assert fechou == [QDialog.DialogCode.Rejected]


def _esperar(condicao, segundos=3):
    import time
    fim = time.monotonic() + segundos
    while not condicao() and time.monotonic() < fim:
        QApplication.processEvents()
        time.sleep(0.01)
    return condicao()


def test_login_em_segundo_plano_habilita_salvar(tmp_path):
    m = modal(FakeConta(), caminho=tmp_path / "c.json")
    m.botao_entrar.click()
    assert _esperar(m.botao_salvar.isEnabled)
    assert "eu@tcm.com" in m.rotulo_conta.text()
    assert m.botao_entrar.isEnabled() or m.botao_entrar.isHidden()


def test_falha_no_login_mostra_motivo_e_permite_tentar_de_novo(tmp_path):
    from enviador_pdf_xml.conta import FalhaLogin

    class ContaComErro(FakeConta):
        def entrar(self):
            raise FalhaLogin("AADSTS500113: No reply address")

    m = modal(ContaComErro(), caminho=tmp_path / "c.json")
    m.botao_entrar.click()
    assert _esperar(lambda: "AADSTS500113" in m.aviso.text())
    assert m.botao_entrar.isEnabled()


def test_aviso_de_conta_substitui_o_texto_de_nao_configurado():
    m = DialogoConta(None, None, aviso_conta="Sem internet.")
    assert m.aviso.text() == "Sem internet."
    assert "fale com a ti" in DialogoConta(None, None).aviso.text().lower()
