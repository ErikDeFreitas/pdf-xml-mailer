import hashlib
import re
from pathlib import Path

from PySide6.QtCore import QSettings

from enviador_pdf_xml.modulo import MODULO

RAIZ = Path(__file__).resolve().parent.parent


def test_build_usa_nome_do_exe():
    script = (RAIZ / "build.ps1").read_text(encoding="utf-8")
    workflow = (RAIZ / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert MODULO.nome_exe == "EnviadorEmails.exe"
    assert '$nome = "EnviadorEmails"' in script
    assert "--collect-data tcm_ui --collect-data enviador_pdf_xml" in script
    assert "--hidden-import msal --hidden-import msal_extensions" in script
    assert workflow.count("EnviadorEmails.exe") >= 2
    assert "EnviadorEmails.exe.sha256" in workflow
    assert (RAIZ / "assets" / "EnviadorEmails.ico").is_file()


def test_requirements_fixa_tcm_ui():
    texto = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
    assert re.search(r"tcm-ui\[microsoft\] @ git\+https://github.com/ErikDeFreitas/Tcm-ui@v\d+\.\d+\.\d+", texto)


def test_sha256_legivel_pelos_dois_atualizadores():
    script = (RAIZ / "build.ps1").read_text(encoding="utf-8")
    assert '"$hash  $nome.exe`n"' in script  # o formato que o build grava
    hash_ = hashlib.sha256(b"exe").hexdigest()
    conteudo = f"{hash_}  EnviadorEmails.exe\n"
    assert conteudo.split()[0] == hash_  # atualizador do 1.0.0
    assert re.match(r"\s*([0-9a-fA-F]{64})", conteudo).group(1) == hash_  # tcm_ui.atualizador


def test_tema_antigo_e_lido(tmp_path):
    from tcm_ui.themes import GerenciadorTema
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path))
    QSettings("TCM", MODULO.aplicacao_settings).setValue("aparencia/tema", "dark")
    gerente = GerenciadorTema()
    gerente.configurar("TCM", MODULO.aplicacao_settings)
    assert gerente.nome == "escuro"


def test_workflow_confere_a_versao():
    texto = (RAIZ / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "__version__" in texto
