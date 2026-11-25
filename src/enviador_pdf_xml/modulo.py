"""MODULO do Enviador de PDF + XML para a casca e o avulso. Leve: só dados e a fábrica (sem msal nem a tela)."""

from tcm_ui.modulo import Contexto, Modulo, Pagina

from enviador_pdf_xml import __version__, dados


def criar(contexto: Contexto):
    from enviador_pdf_xml.instancia import Enviador  # import pesado só quando o módulo é aberto
    return Enviador(contexto)


MODULO = Modulo(
    id="enviador_pdf_xml",
    nome="Enviador de PDF + XML",
    icone="email",
    versao=__version__,
    grupo_ad="SF-EnviadorPDFXML",
    repositorio="ErikDeFreitas/pdf-xml-mailer",
    nome_exe="EnviadorEmails.exe",
    pasta_dados=dados.PASTA,
    paginas=(Pagina("enviar", "Enviar PDF + XML", "Um e-mail por par de arquivos com o mesmo nome.", "enviar"),),
    criar=criar,
)
