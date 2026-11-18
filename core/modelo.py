"""Valores fixos do e-mail e do login. Mudam só com uma nova versão do programa.

Variáveis: {nome} (nome do par, no assunto) e {vcto} (vencimento, no corpo).
Para e Cco NÃO ficam aqui: cada pessoa configura no primeiro acesso (core/configuracao.py).
"""

ORGANIZACAO = "TCM"
APLICACAO = "EnviadorEmails"

# TODO(Erik): texto real do assunto antes da 1ª release.
ASSUNTO = "EMPRESA - CTE {nome} - TEXTO FIXO DO ASSUNTO"

CORPO_TEXTO = """Prezados, bom dia, tudo bem?

Segue fechamento

Fatura + XML

Vcto: {vcto}
"""

CORPO_HTML = """<p>Prezados, bom dia, tudo bem?</p>
<p>Segue fechamento</p>
<p><b>Fatura + XML</b></p>
<p><b>Vcto: {vcto}</b></p>
"""

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
        faltando.append("CLIENT_ID vazio em core/modelo.py")
    if not TENANT_ID:
        faltando.append("TENANT_ID vazio em core/modelo.py")
    if "TEXTO FIXO" in ASSUNTO:
        faltando.append("ASSUNTO ainda é o texto de exemplo em core/modelo.py")
    return faltando
