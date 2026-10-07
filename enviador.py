"""Lógica compartilhada de envio (usada pelo CLI e pela interface web)."""
import configparser
import getpass
import html as html_lib
import mimetypes
import os
import smtplib
import ssl
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

BASE = Path(__file__).parent


def carregar_config() -> configparser.ConfigParser:
    caminho = BASE / "config.ini"
    if not caminho.exists():
        raise FileNotFoundError(
            "config.ini não encontrado. Copie config.exemplo.ini para config.ini e preencha."
        )
    cfg = configparser.ConfigParser(interpolation=None)  # '%' em valores não quebra a leitura
    cfg.read(caminho, encoding="utf-8")
    return cfg


SERVICO_KEYRING = "enviador-emails"
_senhas = {}  # cache só em memória: a senha nunca é escrita em disco por este programa


def obter_senha(cfg) -> str:
    """Descobre a senha SMTP sem exigir que ela fique escrita em arquivo.

    Ordem: variável de ambiente ENVIADOR_SMTP_SENHA -> cofre do sistema (keyring; no
    Windows, o Gerenciador de Credenciais) -> [legado] campo 'senha' do config.ini ->
    pergunta no terminal (fica só na memória). Guarde no cofre com configurar_senha.py.
    """
    s = cfg["smtp"]
    usuario = s["usuario"]
    if usuario in _senhas:
        return _senhas[usuario]

    senha = os.environ.get("ENVIADOR_SMTP_SENHA") or None
    if not senha:
        try:
            import keyring

            senha = keyring.get_password(SERVICO_KEYRING, usuario)
        except Exception:  # noqa: BLE001 - keyring ausente ou sem cofre disponível
            senha = None
    if not senha and s.get("senha"):
        print(
            "AVISO: há uma senha em texto puro no config.ini. Rode 'python configurar_senha.py' "
            "e apague a linha 'senha' desse arquivo.",
            file=sys.stderr,
        )
        senha = s["senha"]
    if not senha:
        if not sys.stdin or not sys.stdin.isatty():
            raise RuntimeError("Senha SMTP não configurada. Rode: python configurar_senha.py")
        senha = getpass.getpass(f"Senha de {usuario} (não será salva): ")
    _senhas[usuario] = senha
    return senha


def carregar_corpo() -> tuple:
    """Retorna (texto_simples, html). O HTML (corpo.html) é opcional e permite negrito etc."""
    texto = (BASE / "corpo.txt").read_text(encoding="utf-8")
    caminho_html = BASE / "corpo.html"
    html = caminho_html.read_text(encoding="utf-8") if caminho_html.exists() else None
    return texto, html


def montar_assunto(cfg, nome: str) -> str:
    nome = nome.replace("\r", " ").replace("\n", " ").strip()
    return cfg["email"]["assunto"].replace("{nome}", nome)


def corpo_exige_vcto(corpo: tuple) -> bool:
    """True se o corpo (texto ou HTML) usa o campo {vcto}."""
    return any("{vcto}" in (parte or "") for parte in corpo)


def validar_vcto(vcto) -> str:
    """Aceita só dd/mm/aaaa com data real (ex.: 20/11/2026)."""
    vcto = (vcto or "").strip()
    try:
        datetime.strptime(vcto, "%d/%m/%Y")
    except ValueError:
        raise ValueError("Vencimento inválido. Use o formato dd/mm/aaaa.") from None
    return vcto


def aplicar_vcto(corpo: tuple, vcto) -> tuple:
    """Troca {vcto} pela data, no texto e no HTML. Sem {vcto} no corpo, nada muda."""
    if not corpo_exige_vcto(corpo):
        return corpo
    vcto = validar_vcto(vcto)
    texto, html = corpo
    return (
        texto.replace("{vcto}", vcto),
        html.replace("{vcto}", html_lib.escape(vcto)) if html else None,
    )


def montar_mensagem(cfg, corpo: tuple, nome: str, anexos, vcto=None) -> EmailMessage:
    """corpo: (texto, html) de carregar_corpo(). anexos: lista de (nome_do_arquivo, bytes).
    vcto: data dd/mm/aaaa, obrigatória se o corpo tiver {vcto}."""
    texto, html = aplicar_vcto(corpo, vcto)
    msg = EmailMessage()
    msg["From"] = cfg["email"]["remetente"]
    msg["To"] = cfg["email"]["destinatario"]
    if cfg["email"].get("copia"):
        msg["Cc"] = cfg["email"]["copia"]
    msg["Subject"] = montar_assunto(cfg, nome)
    msg.set_content(texto)
    if html:
        msg.add_alternative(html, subtype="html")

    for filename, dados in anexos:
        tipo, _ = mimetypes.guess_type(filename)
        maintype, subtype = (tipo or "application/octet-stream").split("/", 1)
        msg.add_attachment(dados, maintype=maintype, subtype=subtype, filename=filename)
    return msg


def abrir_smtp(cfg) -> smtplib.SMTP:
    s = cfg["smtp"]
    host, porta = s["host"], int(s["porta"])
    contexto = ssl.create_default_context()
    if s.get("seguranca", "starttls").lower() == "ssl":
        server = smtplib.SMTP_SSL(host, porta, context=contexto, timeout=30)
    else:
        server = smtplib.SMTP(host, porta, timeout=30)
        server.starttls(context=contexto)
    server.login(s["usuario"], obter_senha(cfg))
    return server


def enviar_par(cfg, corpo: tuple, nome: str, anexos, vcto=None) -> None:
    """Abre uma conexão, envia um e-mail e fecha."""
    mensagem = montar_mensagem(cfg, corpo, nome, anexos, vcto)  # valida antes de conectar
    server = abrir_smtp(cfg)
    try:
        server.send_message(mensagem)
    finally:
        server.quit()
