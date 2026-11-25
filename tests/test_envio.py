from pathlib import Path

import pytest

from enviador_pdf_xml import envio, modelo

PDF = b"%PDF-1.4\n%fake\n"
XML = b"<?xml version='1.0'?><a/>"


def criar(pasta: Path, nome: str, dados: bytes = b"") -> Path:
    caminho = pasta / nome
    caminho.parent.mkdir(parents=True, exist_ok=True)
    if not dados:
        dados = PDF if nome.lower().endswith(".pdf") else XML
    caminho.write_bytes(dados)
    return caminho


def test_arquivos_da_pasta_ignora_subpastas(tmp_path):
    criar(tmp_path, "1.pdf")
    criar(tmp_path, "enviados/2.pdf")
    assert [p.name for p in envio.arquivos_da_pasta(tmp_path)] == ["1.pdf"]


def test_achar_pares_basico(tmp_path):
    arquivos = [criar(tmp_path, n) for n in ("1.pdf", "1.xml", "2.pdf", "3.xml")]
    arquivos.append(criar(tmp_path, "notas.txt", b"x"))
    pares, avisos = envio.achar_pares(arquivos)
    assert [p.nome for p in pares] == ["1"]
    assert avisos == ["2.pdf: sem XML", "3.xml: sem PDF"]


def test_achar_pares_ignora_maiusculas(tmp_path):
    pares, avisos = envio.achar_pares([criar(tmp_path, "123.PDF"), criar(tmp_path, "123.Xml")])
    assert [p.nome for p in pares] == ["123"]
    assert avisos == []


def test_achar_pares_duplicado(tmp_path):
    arquivos = [criar(tmp_path, "a/5.pdf"), criar(tmp_path, "b/5.pdf"), criar(tmp_path, "a/5.xml")]
    pares, avisos = envio.achar_pares(arquivos)
    assert pares == []
    assert avisos == ["5: mais de um PDF com o mesmo nome"]


def test_pdf_xml_validos():
    assert envio.pdf_valido(PDF)
    assert not envio.pdf_valido(b"lixo")
    assert envio.xml_valido(b"\xef\xbb\xbf  <x/>")
    assert not envio.xml_valido(b"oi")


def test_validar_vcto():
    assert envio.validar_vcto(" 20/11/2026 ") == "20/11/2026"
    for ruim in ("31/02/2026", "2026-11-20", ""):
        with pytest.raises(ValueError):
            envio.validar_vcto(ruim)


def test_validar_emails_separadores():
    assert envio.validar_emails(" a@b.com, c@d.com.br; ", True) == ["a@b.com", "c@d.com.br"]


def test_validar_emails_invalido():
    with pytest.raises(ValueError, match="nada"):
        envio.validar_emails("a@b.com; nada", True)
    with pytest.raises(ValueError):
        envio.validar_emails("", True)
    assert envio.validar_emails("  ", False) == []


def test_assunto_e_corpo():
    assert envio.montar_assunto("12\n3") == modelo.ASSUNTO.replace("{nome}", "12 3")
    texto, html = envio.montar_corpo("20/11/2026")
    assert "20/11/2026" in texto and "20/11/2026" in html
    assert "{vcto}" not in texto + html


def test_montar_mensagem(tmp_path):
    par = envio.Par("1", criar(tmp_path, "1.pdf"), criar(tmp_path, "1.xml"))
    msg = envio.montar_mensagem(par, "eu@tcm.com", ["a@b.com"], ["x@y.com"], "20/11/2026", PDF, XML)
    assert msg["From"] == "eu@tcm.com"
    assert msg["To"] == "a@b.com"
    assert msg["Bcc"] == "x@y.com"
    assert msg["Subject"] == envio.montar_assunto("1")
    anexos = [(a.get_filename(), a.get_content_type()) for a in msg.iter_attachments()]
    assert anexos == [("1.pdf", "application/pdf"), ("1.xml", "application/xml")]
    sem_cco = envio.montar_mensagem(par, "eu@tcm.com", ["a@b.com"], [], "20/11/2026", PDF, XML)
    assert sem_cco["Bcc"] is None


def test_destino_livre_nao_sobrescreve(tmp_path):
    criar(tmp_path, "enviados/1.pdf")
    assert envio.destino_livre(tmp_path / "enviados", "1.pdf") == tmp_path / "enviados" / "1_2.pdf"
    criar(tmp_path, "enviados/1_2.pdf")
    assert envio.destino_livre(tmp_path / "enviados", "1.pdf") == tmp_path / "enviados" / "1_3.pdf"
    assert envio.destino_livre(tmp_path / "enviados", "9.pdf") == tmp_path / "enviados" / "9.pdf"


def test_mover_par(tmp_path):
    ok = envio.Par("1", criar(tmp_path, "1.pdf"), criar(tmp_path, "1.xml"))
    ruim = envio.Par("2", criar(tmp_path, "2.pdf"), criar(tmp_path, "2.xml"))
    envio.mover_par(ok, True)
    envio.mover_par(ruim, False)
    assert sorted(p.name for p in (tmp_path / "enviados").iterdir()) == ["1.pdf", "1.xml"]
    assert sorted(p.name for p in (tmp_path / "erros").iterdir()) == ["2.pdf", "2.xml"]
    assert not ok.pdf.exists() and not ruim.xml.exists()
