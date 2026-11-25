import os
import subprocess
import sys
from importlib.metadata import entry_points

import enviador_pdf_xml
from enviador_pdf_xml.modulo import MODULO


def test_valores_do_modulo():
    assert (MODULO.id, MODULO.nome, MODULO.icone) == ("enviador_pdf_xml", "Enviador de PDF + XML", "email")
    assert (MODULO.grupo_ad, MODULO.repositorio, MODULO.nome_exe) == (
        "SF-EnviadorPDFXML", "ErikDeFreitas/pdf-xml-mailer", "EnviadorEmails.exe")
    assert MODULO.versao == enviador_pdf_xml.__version__ == "2.1.0"
    assert MODULO.aplicacao_settings == "EnviadorEmails"
    assert [(p.chave, p.titulo, p.subtitulo, p.icone) for p in MODULO.paginas] == [
        ("enviar", "Enviar PDF + XML", "Um e-mail por par de arquivos com o mesmo nome.", "enviar")]


def test_entry_point_carrega_o_modulo():
    eps = {ep.name: ep for ep in entry_points(group="sistema_financeiro.modulos")}
    assert eps["enviador_pdf_xml"].load() is MODULO


def test_modulo_e_leve_e_usa_a_pasta_local(tmp_path):
    # PySide6.QtWidgets já vem do contrato (tcm_ui.modulo); o que não pode vir é o resto pesado.
    codigo = ("import sys, enviador_pdf_xml.modulo as m; "
              "print(*[x in sys.modules for x in ('msal', 'msal_extensions', 'smtplib', "
              "'enviador_pdf_xml.tela', 'enviador_pdf_xml.instancia')]); print(m.MODULO.pasta_dados)")
    env = {k: v for k, v in os.environ.items() if k != "ENVIADOR_DADOS"}
    env["LOCALAPPDATA"] = str(tmp_path / "local")
    saida = subprocess.run([sys.executable, "-c", codigo], capture_output=True, text=True, env=env, check=True)
    importados, pasta = saida.stdout.strip().splitlines()
    assert importados.split() == ["False"] * 5
    assert pasta == str(tmp_path / "local" / "EnviadorEmails")
    assert not (tmp_path / "local").exists()
