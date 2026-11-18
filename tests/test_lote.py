import smtplib

import pytest

from core import envio

PDF = b"%PDF-1.4\n"
XML = b"<a/>"


class FakeSMTP:
    """Servidor falso: guarda as mensagens; pode cair N vezes."""

    def __init__(self, quedas=0, sempre_cai=False):
        self.enviadas = []
        self.quedas = quedas
        self.sempre_cai = sempre_cai
        self.fechado = False

    def send_message(self, msg):
        if self.sempre_cai or self.quedas > 0:
            self.quedas -= 1
            raise smtplib.SMTPServerDisconnected("caiu")
        self.enviadas.append(msg)

    def quit(self):
        self.fechado = True


def pares(tmp_path, *nomes, pdf=PDF):
    resultado = []
    for n in nomes:
        (tmp_path / f"{n}.pdf").write_bytes(pdf)
        (tmp_path / f"{n}.xml").write_bytes(XML)
        resultado.append(envio.Par(n, tmp_path / f"{n}.pdf", tmp_path / f"{n}.xml"))
    return resultado


def lote(lista, conectar, **kw):
    kw.setdefault("dormir", lambda s: None)
    return envio.enviar_lote(lista, "eu@tcm.com", ["a@b.com"], [], "20/11/2026", conectar, **kw)


def test_xoauth2_formato():
    assert envio.xoauth2("a@b.com", "T") == "user=a@b.com\x01auth=Bearer T\x01\x01"


def test_abrir_smtp_usa_xoauth2():
    chamadas = []

    class Fabrica:
        def __init__(self, host, porta, timeout):
            chamadas.append(("conectar", host, porta, timeout))

        def ehlo(self):
            chamadas.append(("ehlo",))

        def starttls(self, context):
            chamadas.append(("starttls",))

        def auth(self, mecanismo, objeto, initial_response_ok=True):
            chamadas.append(("auth", mecanismo, objeto()))

    envio.abrir_smtp("a@b.com", "T", fabrica=Fabrica)
    assert chamadas[0] == ("conectar", "smtp.office365.com", 587, 30)
    assert ("starttls",) in chamadas
    assert chamadas[-1] == ("auth", "XOAUTH2", "user=a@b.com\x01auth=Bearer T\x01\x01")


def test_lote_tudo_ok(tmp_path):
    smtp, pausas = FakeSMTP(), []
    r = lote(pares(tmp_path, "1", "2"), lambda: smtp, dormir=pausas.append)
    assert [x.status for x in r] == ["enviado", "enviado"]
    assert len(smtp.enviadas) == 2 and smtp.fechado
    assert sorted(p.name for p in (tmp_path / "enviados").iterdir()) == ["1.pdf", "1.xml", "2.pdf", "2.xml"]
    assert pausas == [2.0]


def test_lote_pdf_invalido_vai_para_erros(tmp_path):
    r = lote(pares(tmp_path, "1", pdf=b"lixo"), lambda: FakeSMTP())
    assert r[0].status == "erro" and "PDF" in r[0].detalhe
    assert (tmp_path / "erros" / "1.pdf").exists()


def test_lote_envio_ok_mas_arquivo_preso(tmp_path, monkeypatch):
    def preso(par, sucesso):
        raise PermissionError("arquivo em uso")

    monkeypatch.setattr(envio, "mover_par", preso)
    r = lote(pares(tmp_path, "1"), lambda: FakeSMTP())
    assert r[0].status == "aviso"
    assert "não foi movido" in r[0].detalhe


def test_lote_reconecta_uma_vez(tmp_path):
    conexoes = []

    def conectar():
        conexoes.append(FakeSMTP(quedas=1 if not conexoes else 0))
        return conexoes[-1]

    r = lote(pares(tmp_path, "1", "2"), conectar)
    assert [x.status for x in r] == ["enviado", "enviado"]
    assert len(conexoes) == 2


def test_lote_conexao_perdida_de_vez(tmp_path):
    lista = pares(tmp_path, "1", "2")
    r = lote(lista, lambda: FakeSMTP(sempre_cai=True))
    assert [x.status for x in r] == ["erro", "erro"]
    assert all("Conexão perdida" in x.detalhe for x in r)
    assert all(p.pdf.exists() and p.xml.exists() for p in lista)


def test_lote_cancelado(tmp_path):
    lista = pares(tmp_path, "1", "2")
    feitos = []
    r = lote(lista, lambda: FakeSMTP(), ao_concluir=feitos.append, cancelado=lambda: len(feitos) >= 1)
    assert [x.nome for x in r] == ["1"]
    assert lista[1].pdf.exists()


def test_lote_falha_ao_conectar(tmp_path):
    lista = pares(tmp_path, "1")

    def conectar():
        raise smtplib.SMTPAuthenticationError(535, b"negado")

    with pytest.raises(envio.FalhaConexao):
        lote(lista, conectar)
    assert lista[0].pdf.exists()


def test_lote_vcto_invalido_nao_conecta(tmp_path):
    def conectar():
        raise AssertionError("não devia conectar")

    with pytest.raises(ValueError):
        envio.enviar_lote(pares(tmp_path, "1"), "eu@tcm.com", ["a@b.com"], [], "99/99/2026", conectar)


def test_lote_avisa_inicio(tmp_path):
    inicios = []
    lote(pares(tmp_path, "1", "2"), lambda: FakeSMTP(), ao_iniciar=lambda i, t, n: inicios.append((i, t, n)))
    assert inicios == [(1, 2, "1"), (2, 2, "2")]


def test_lote_reconexao_falha_marca_restantes(tmp_path):
    lista = pares(tmp_path, "1", "2")
    conexoes = []

    def conectar():
        if conexoes:
            raise RuntimeError("Sua sessão expirou")
        conexoes.append(FakeSMTP(sempre_cai=True))
        return conexoes[-1]

    r = lote(lista, conectar)
    assert [x.status for x in r] == ["erro", "erro"]
    assert all(p.pdf.exists() for p in lista)
