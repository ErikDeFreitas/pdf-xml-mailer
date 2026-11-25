from enviador_pdf_xml import configuracao
from enviador_pdf_xml.configuracao import Configuracao


def test_ida_e_volta(tmp_path):
    caminho = tmp_path / "sub" / "config.json"
    cfg = Configuracao(para=["a@b.com", "c@d.com"], cco=["x@y.com"])
    configuracao.salvar(cfg, caminho)
    assert configuracao.carregar(caminho) == cfg
    assert not list(caminho.parent.glob("*.tmp"))


def test_sem_arquivo_retorna_none(tmp_path):
    assert configuracao.carregar(tmp_path / "config.json") is None


def test_json_quebrado_retorna_none(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text("{", encoding="utf-8")
    assert configuracao.carregar(caminho) is None


def test_para_vazio_retorna_none(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text('{"para": [], "cco": []}', encoding="utf-8")
    assert configuracao.carregar(caminho) is None


def test_cco_invalido_vira_vazio(tmp_path):
    caminho = tmp_path / "config.json"
    caminho.write_text('{"para": ["a@b.com"], "cco": ["nada"]}', encoding="utf-8")
    assert configuracao.carregar(caminho) == Configuracao(para=["a@b.com"], cco=[])


def test_caminho_padrao_usa_appdata(tmp_path, monkeypatch):
    monkeypatch.delenv("ENVIADOR_DADOS")
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert configuracao.caminho_padrao() == tmp_path / "EnviadorEmails" / "config.json"
