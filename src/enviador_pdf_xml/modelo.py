"""Valores fixos do programa e o texto PADRÃO do e-mail.

Assunto e corpo podem ser trocados em "Configurar e-mail" (salvos no config.json de cada pessoa);
os daqui valem enquanto ninguém configurar. Variáveis: {nome} (nome do par) e {vcto} (vencimento).
No corpo, **texto** sai em negrito.
Para e Cco NÃO ficam aqui: cada pessoa configura no primeiro acesso (enviador_pdf_xml/configuracao.py).
"""

ORGANIZACAO = "TCM"
APLICACAO = "EnviadorEmails"

# Enquanto o assunto tiver "TEXTO FIXO", o programa pede para configurar antes de enviar.
ASSUNTO = "EMPRESA - CTE {nome} - TEXTO FIXO DO ASSUNTO"

CORPO = """Prezados, bom dia, tudo bem?

Segue fechamento

**Fatura + XML**

**Vcto: {vcto}**"""

SMTP_HOST = "smtp.office365.com"
SMTP_PORTA = 587
TIMEOUT = 30
INTERVALO_SEGUNDOS = 2.0

# Registro do aplicativo no Entra ID (cliente público). Não são segredos.
# Preencher com o "ID do aplicativo (cliente)" e o "ID do diretório (locatário)".
CLIENT_ID = "55e442e7-4f32-4d4a-ba25-18bd037d0a97"
TENANT_ID = "ffabf46e-1c33-44f1-89a5-4ac34fc7a8ef"
ESCOPOS = ["https://outlook.office.com/SMTP.Send"]


def pendencias_release() -> list[str]:
    """O que ainda impede uma release (o workflow falha se a lista não estiver vazia)."""
    faltando = []
    if not CLIENT_ID:
        faltando.append("CLIENT_ID vazio em enviador_pdf_xml/modelo.py")
    if not TENANT_ID:
        faltando.append("TENANT_ID vazio em enviador_pdf_xml/modelo.py")
    return faltando
