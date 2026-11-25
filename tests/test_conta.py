import pytest

from enviador_pdf_xml import conta as conta_mod
from enviador_pdf_xml import modelo
from enviador_pdf_xml.conta import Conta, ContaNaoConfigurada, FalhaLogin


class FakeApp:
    def __init__(self, contas=None, interativo=None, silencioso=None):
        self.contas = list(contas or [])
        self.interativo = interativo or {}
        self.silencioso = silencioso
        self.removidas = []

    def get_accounts(self):
        return self.contas

    def acquire_token_interactive(self, scopes, **kw):
        assert scopes == modelo.ESCOPOS
        if "access_token" in self.interativo:
            self.contas = [{"username": self.interativo["email"]}]
        return self.interativo

    def acquire_token_silent(self, scopes, account):
        return self.silencioso

    def remove_account(self, conta):
        self.removidas.append(conta)


def test_entrar_retorna_email():
    app = FakeApp(interativo={"access_token": "T", "email": "eu@tcm.com"})
    assert Conta(app).entrar() == "eu@tcm.com"


def test_entrar_cancelado_levanta_falha_login():
    app = FakeApp(interativo={"error": "x", "error_description": "Usuário cancelou"})
    with pytest.raises(FalhaLogin, match="cancelou"):
        Conta(app).entrar()


def test_email_sem_conta_e_none():
    assert Conta(FakeApp()).email() is None


def test_token_sem_conta_levanta():
    with pytest.raises(FalhaLogin, match="Entre novamente"):
        Conta(FakeApp()).token()


def test_token_expirado_levanta():
    app = FakeApp(contas=[{"username": "eu@tcm.com"}], silencioso=None)
    with pytest.raises(FalhaLogin):
        Conta(app).token()


def test_token_ok():
    app = FakeApp(contas=[{"username": "eu@tcm.com"}], silencioso={"access_token": "T"})
    c = Conta(app)
    assert c.email() == "eu@tcm.com"
    assert c.token() == "T"


def test_sair_remove_contas():
    app = FakeApp(contas=[{"username": "a"}, {"username": "b"}])
    Conta(app).sair()
    assert len(app.removidas) == 2


def test_sem_client_id_levanta_conta_nao_configurada(monkeypatch):
    monkeypatch.setattr(modelo, "CLIENT_ID", "")
    with pytest.raises(ContaNaoConfigurada):
        Conta()


def test_caminho_cache_usa_localappdata(tmp_path, monkeypatch):
    monkeypatch.delenv("ENVIADOR_DADOS")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert conta_mod.caminho_cache() == tmp_path / "EnviadorEmails" / "token_cache.bin"


def test_cache_de_token_criptografado_funciona(tmp_path, monkeypatch):
    monkeypatch.delenv("ENVIADOR_DADOS")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    cache = conta_mod._criar_cache()
    cache.add({"client_id": "c", "scope": ["s"], "token_endpoint": "https://login.microsoftonline.com/t/oauth2/v2.0/token",
               "response": {"access_token": "SEGREDO", "token_type": "Bearer", "expires_in": 3600}})
    arquivo = conta_mod.caminho_cache()
    assert arquivo.exists()
    assert b"SEGREDO" not in arquivo.read_bytes()  # DPAPI: nada em texto puro


def test_entrar_tem_timeout():
    app = FakeApp(interativo={"access_token": "T", "email": "eu@tcm.com"})
    chamadas = []
    original = app.acquire_token_interactive
    app.acquire_token_interactive = lambda scopes, **kw: chamadas.append(kw) or original(scopes, **kw)
    Conta(app).entrar()
    assert chamadas[0].get("timeout") == 180


def test_pendencias_release(monkeypatch):
    monkeypatch.setattr(modelo, "CLIENT_ID", "")
    monkeypatch.setattr(modelo, "TENANT_ID", "")
    assert len(modelo.pendencias_release()) == 2
    monkeypatch.setattr(modelo, "CLIENT_ID", "id")
    monkeypatch.setattr(modelo, "TENANT_ID", "tenant")
    # o assunto de exemplo não barra a release: cada pessoa configura em "Configurar e-mail"
    assert modelo.pendencias_release() == []
