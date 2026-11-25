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

TIMEOUT = 30
INTERVALO_SEGUNDOS = 2.0
