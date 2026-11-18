from core import envio
from core.worker import EnviarWorker, LoginWorker
from tests.test_lote import FakeSMTP, pares


class ContaFalsa:
    def __init__(self, falha=None):
        self.falha = falha

    def email(self):
        return "eu@tcm.com"

    def token(self):
        if self.falha:
            raise self.falha
        return "T"

    def entrar(self):
        if self.falha:
            raise self.falha
        return "eu@tcm.com"


def test_enviar_worker_emite_resultados(tmp_path, monkeypatch):
    monkeypatch.setattr(envio, "abrir_smtp", lambda e, t: FakeSMTP())
    monkeypatch.setattr(envio.time, "sleep", lambda s: None)
    w = EnviarWorker(pares(tmp_path, "1", "2"), ["a@b.com"], [], "20/11/2026", ContaFalsa())
    por_par, fim = [], []
    w.par_concluido.connect(por_par.append)
    w.concluido.connect(fim.append)
    w.run()
    assert [r.status for r in por_par] == ["enviado", "enviado"]
    assert len(fim) == 1 and len(fim[0]) == 2


def test_enviar_worker_sessao_expirada(tmp_path):
    from core.conta import FalhaLogin
    w = EnviarWorker(pares(tmp_path, "1"), ["a@b.com"], [], "20/11/2026",
                     ContaFalsa(FalhaLogin("Sua sessão expirou.")))
    falhas = []
    w.sessao_expirada.connect(falhas.append)
    w.run()
    assert falhas and "sessão expirou" in falhas[0]
    assert (tmp_path / "1.pdf").exists()


def test_login_worker():
    w = LoginWorker(ContaFalsa())
    ok = []
    w.concluido.connect(ok.append)
    w.run()
    assert ok == ["eu@tcm.com"]
