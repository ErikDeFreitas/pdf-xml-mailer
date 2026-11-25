"""Assunto e corpo editáveis em "Configurar e-mail" (salvos no config.json)."""
import pytest

from enviador_pdf_xml import configuracao, envio, modelo
from enviador_pdf_xml.configuracao import Configuracao
from tests.test_lote import FakeSMTP, lote, pares


def test_corpo_padrao_mantem_negrito():
    texto, html = envio.montar_corpo("20/11/2026")
    assert "**" not in texto
    assert "Vcto: 20/11/2026" in texto
    assert "<b>Vcto: 20/11/2026</b>" in html
    assert "<p>Prezados, bom dia, tudo bem?</p>" in html


def test_corpo_personalizado_vira_html():
    texto, html = envio.montar_corpo("01/02/2026", "123", "Olá\n**NF {nome}**\nlinha2\n\nFim <x> & {vcto}")
    assert texto == "Olá\nNF 123\nlinha2\n\nFim <x> & 01/02/2026"
    assert "<p>Olá<br><b>NF 123</b><br>linha2</p>" in html
    assert "<p>Fim &lt;x&gt; &amp; 01/02/2026</p>" in html


def test_assunto_personalizado_aceita_nome_e_vcto():
    assert envio.montar_assunto("1\n2", "20/11/2026", "CTE {nome} venc {vcto}") == "CTE 1 2 venc 20/11/2026"


@pytest.mark.parametrize("texto, trecho", [
    ("   ", "Informe o assunto"),
    ("CTE {nmoe}", "{nmoe}"),
    ("CTE {", "chave"),
    ("CTE {}", "{}"),
])
def test_validar_modelo_recusa(texto, trecho):
    with pytest.raises(ValueError, match=trecho.replace("{", r"\{").replace("}", r"\}")):
        envio.validar_modelo(texto, "assunto")


def test_validar_modelo_aceita_e_limpa():
    assert envio.validar_modelo("  CTE {nome} - {vcto}  ", "assunto") == "CTE {nome} - {vcto}"


def test_assunto_de_exemplo():
    assert envio.assunto_de_exemplo(modelo.ASSUNTO)
    assert not envio.assunto_de_exemplo("TCM - CTE {nome}")


def test_mensagem_usa_modelo_salvo(tmp_path):
    (par,) = pares(tmp_path, "7")
    msg = envio.montar_mensagem(par, "eu@tcm.com", ["a@b.com"], [], "20/11/2026", b"%PDF", b"<x/>",
                                assunto="NF {nome}", corpo="**Oi** {vcto}")
    assert msg["Subject"] == "NF 7"
    assert "Oi 20/11/2026" in msg.get_body(("plain",)).get_content()
    assert "<b>Oi</b> 20/11/2026" in msg.get_body(("html",)).get_content()


def test_lote_usa_modelo_salvo(tmp_path):
    smtp = FakeSMTP()
    lote(pares(tmp_path, "9"), lambda: smtp, assunto="Fatura {nome}", corpo="x")
    assert smtp.enviadas[0]["Subject"] == "Fatura 9"


def test_config_antiga_usa_padrao(tmp_path):
    caminho = tmp_path / "c.json"
    caminho.write_text('{"para": ["a@b.com"], "cco": []}', encoding="utf-8")
    cfg = configuracao.carregar(caminho)
    assert cfg.assunto == modelo.ASSUNTO and cfg.corpo == modelo.CORPO


def test_config_salva_assunto_e_corpo(tmp_path):
    caminho = tmp_path / "c.json"
    cfg = Configuracao(["a@b.com"], [], assunto="NF {nome}", corpo="Linha\n**{vcto}**")
    configuracao.salvar(cfg, caminho)
    assert configuracao.carregar(caminho) == cfg


def test_config_modelo_invalido_volta_ao_padrao(tmp_path):
    caminho = tmp_path / "c.json"
    caminho.write_text('{"para": ["a@b.com"], "assunto": "NF {x}", "corpo": 5}', encoding="utf-8")
    cfg = configuracao.carregar(caminho)
    assert cfg.para == ["a@b.com"]
    assert cfg.assunto == modelo.ASSUNTO and cfg.corpo == modelo.CORPO
