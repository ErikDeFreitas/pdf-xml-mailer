"""Regras de envio: pares PDF + XML, mensagem, SMTP e movimentação (sem interface)."""
from __future__ import annotations

import html as html_lib
import os
import re
import smtplib
import string
import time
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Callable, Iterable

from enviador_pdf_xml import modelo

PASTA_ENVIADOS = "enviados"
PASTA_ERROS = "erros"
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class Par:
    nome: str
    pdf: Path
    xml: Path


def arquivos_da_pasta(pasta: Path) -> list[Path]:
    """Arquivos diretamente dentro da pasta (sem subpastas, logo sem enviados/ e erros/)."""
    return sorted(p for p in Path(pasta).iterdir() if p.is_file())


def achar_pares(arquivos: Iterable[Path]) -> tuple[list[Par], list[str]]:
    """Junta PDF e XML de mesmo nome (sem diferenciar maiúsculas). Devolve (pares, avisos)."""
    pdfs: dict[str, list[Path]] = {}
    xmls: dict[str, list[Path]] = {}
    for arq in arquivos:
        arq = Path(arq)
        ext = arq.suffix.lower()
        destino = pdfs if ext == ".pdf" else xmls if ext == ".xml" else None
        if destino is not None:
            destino.setdefault(arq.stem.casefold(), []).append(arq)

    pares: list[Par] = []
    avisos: list[str] = []
    for chave in sorted(set(pdfs) | set(xmls)):
        lista_pdf, lista_xml = pdfs.get(chave, []), xmls.get(chave, [])
        if len(lista_pdf) > 1:
            avisos.append(f"{lista_pdf[0].stem}: mais de um PDF com o mesmo nome")
        elif len(lista_xml) > 1:
            avisos.append(f"{lista_xml[0].stem}: mais de um XML com o mesmo nome")
        elif not lista_xml:
            avisos.append(f"{lista_pdf[0].name}: sem XML")
        elif not lista_pdf:
            avisos.append(f"{lista_xml[0].name}: sem PDF")
        else:
            pares.append(Par(lista_pdf[0].stem, lista_pdf[0], lista_xml[0]))
    pares.sort(key=lambda p: p.nome.casefold())
    return pares, avisos


def pdf_valido(dados: bytes) -> bool:
    return b"%PDF-" in dados[:1024]


def xml_valido(dados: bytes) -> bool:
    return dados.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"<")


def validar_vcto(texto: str) -> str:
    """Aceita só dd/mm/aaaa com data real (ex.: 20/11/2026)."""
    texto = (texto or "").strip()
    try:
        datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        raise ValueError("Vencimento inválido. Use o formato dd/mm/aaaa.") from None
    return texto


def validar_emails(texto: str, obrigatorio: bool) -> list[str]:
    """Separa por ';' ou ',' e confere o formato de cada endereço."""
    emails = [e.strip() for e in re.split(r"[;,]", texto or "") if e.strip()]
    for e in emails:
        if not _EMAIL.match(e):
            raise ValueError(f"E-mail inválido: {e}")
    if obrigatorio and not emails:
        raise ValueError("Informe pelo menos um e-mail.")
    return emails


CAMPOS = ("nome", "vcto")
_NEGRITO = re.compile(r"\*\*(.+?)\*\*")


def validar_modelo(texto: str, rotulo: str) -> str:
    """Assunto/corpo digitado em "Configurar e-mail": só aceita {nome} e {vcto}."""
    texto = (texto or "").strip()
    if not texto:
        raise ValueError(f"Informe o {rotulo}.")
    try:
        campos = [campo for _, campo, _, _ in string.Formatter().parse(texto) if campo is not None]
    except ValueError:
        raise ValueError("Tem uma chave { ou } sem par. Use só {nome} e {vcto}.") from None
    for campo in campos:
        if campo not in CAMPOS:
            raise ValueError(f"Campo desconhecido: {{{campo}}}. Use {{nome}} ou {{vcto}}.")
    return texto


def assunto_de_exemplo(assunto: str) -> bool:
    """O assunto padrão é só um exemplo: precisa ser configurado antes de enviar."""
    return "TEXTO FIXO" in assunto.upper()


def _preencher(texto: str, nome: str, vcto: str) -> str:
    return texto.replace("{nome}", nome).replace("{vcto}", vcto)


def montar_assunto(nome: str, vcto: str = "", assunto: str | None = None) -> str:
    nome = nome.replace("\r", " ").replace("\n", " ").strip()
    return _preencher(assunto or modelo.ASSUNTO, nome, vcto)


def montar_corpo(vcto: str, nome: str = "", corpo: str | None = None) -> tuple[str, str]:
    """(texto, html). **x** vira negrito no HTML; linha em branco separa parágrafos."""
    corpo = (corpo or modelo.CORPO).replace("\r\n", "\n").strip()
    texto = _preencher(_NEGRITO.sub(r"\1", corpo), nome, vcto)
    paragrafos = []
    for bloco in re.split(r"\n\s*\n", corpo):
        bloco = _NEGRITO.sub(r"<b>\1</b>", html_lib.escape(bloco.strip(), quote=False))
        paragrafos.append("<p>" + bloco.replace("\n", "<br>") + "</p>")
    html = _preencher("\n".join(paragrafos), html_lib.escape(nome), html_lib.escape(vcto))
    return texto, html


def montar_mensagem(par: Par, remetente: str, para: list[str], cco: list[str], vcto: str,
                    pdf: bytes, xml: bytes, assunto: str | None = None,
                    corpo: str | None = None) -> EmailMessage:
    texto, html = montar_corpo(vcto, par.nome, corpo)
    msg = EmailMessage()
    msg["From"] = remetente
    msg["To"] = ", ".join(para)
    if cco:
        msg["Bcc"] = ", ".join(cco)
    msg["Subject"] = montar_assunto(par.nome, vcto, assunto)
    msg.set_content(texto)
    msg.add_alternative(html, subtype="html")
    msg.add_attachment(pdf, maintype="application", subtype="pdf", filename=par.pdf.name)
    msg.add_attachment(xml, maintype="application", subtype="xml", filename=par.xml.name)
    return msg


def destino_livre(pasta: Path, nome_arquivo: str) -> Path:
    """Caminho em `pasta` que não sobrescreve nada: nome.pdf, nome_2.pdf, nome_3.pdf…"""
    alvo = Path(pasta) / nome_arquivo
    n = 2
    while alvo.exists():
        alvo = Path(pasta) / f"{Path(nome_arquivo).stem}_{n}{Path(nome_arquivo).suffix}"
        n += 1
    return alvo


def mover_par(par: Par, sucesso: bool) -> None:
    """Move o PDF e o XML para enviados/ (ou erros/) dentro da pasta de cada um."""
    # os.rename (mesmo disco: é uma subpasta) e não shutil.move: com o arquivo aberto em outro
    # programa, o shutil copiaria e falharia ao apagar, deixando uma cópia em enviados/ E o original.
    sub = PASTA_ENVIADOS if sucesso else PASTA_ERROS
    for arq in (par.pdf, par.xml):
        pasta = arq.parent / sub
        pasta.mkdir(exist_ok=True)
        os.rename(arq, destino_livre(pasta, arq.name))


# ---------------------------------------------------------------------------
# Conexão (XOAUTH2) e envio do lote
# ---------------------------------------------------------------------------

class FalhaConexao(Exception):
    """Não deu para conectar/autenticar no servidor. Nenhum arquivo foi movido."""


@dataclass
class ResultadoPar:
    nome: str
    status: str  # "enviado" | "aviso" | "erro"
    detalhe: str = ""


_QUEDA = (smtplib.SMTPServerDisconnected, ConnectionError)


def _fechar(server) -> None:
    try:
        server.quit()
    except Exception:  # noqa: BLE001 - conexão já caída
        pass


def enviar_lote(pares: list[Par], remetente: str, para: list[str], cco: list[str], vcto: str,
                conectar: Callable[[], smtplib.SMTP],
                intervalo: float = modelo.INTERVALO_SEGUNDOS,
                ao_iniciar: Callable[[int, int, str], None] | None = None,
                ao_concluir: Callable[[ResultadoPar], None] | None = None,
                cancelado: Callable[[], bool] = lambda: False,
                dormir: Callable[[float], None] = time.sleep,
                assunto: str | None = None, corpo: str | None = None) -> list[ResultadoPar]:
    """Envia um e-mail por par numa única conexão. Um erro num par nunca derruba o lote."""
    vcto = validar_vcto(vcto)
    try:
        server = conectar()
    except Exception as e:  # noqa: BLE001
        raise FalhaConexao(f"Não foi possível conectar ao servidor de e-mail: {e}") from e

    resultados: list[ResultadoPar] = []

    def registrar(r: ResultadoPar) -> None:
        resultados.append(r)
        if ao_concluir:
            ao_concluir(r)

    try:
        for i, par in enumerate(pares):
            if cancelado():
                break
            if i:
                dormir(intervalo)
            if ao_iniciar:
                ao_iniciar(i + 1, len(pares), par.nome)
            try:
                dados_pdf, dados_xml = par.pdf.read_bytes(), par.xml.read_bytes()
            except OSError as e:
                registrar(ResultadoPar(par.nome, "erro", f"Não foi possível ler os arquivos: {e}"))
                continue
            invalido = (f"{par.pdf.name} não parece ser um PDF válido" if not pdf_valido(dados_pdf) else
                        f"{par.xml.name} não parece ser um XML válido" if not xml_valido(dados_xml) else "")
            if invalido:
                _mover_sem_falhar(par, False)
                registrar(ResultadoPar(par.nome, "erro", invalido))
                continue

            mensagem = montar_mensagem(par, remetente, para, cco, vcto, dados_pdf, dados_xml,
                                       assunto, corpo)
            perdida = incerto = None
            recusados = {}
            try:
                recusados = server.send_message(mensagem) or {}
            except _QUEDA:
                # Caiu: reconecta uma vez e repete este par. Falhou de novo -> para o lote
                # sem mover nada (os arquivos ficam para um novo envio).
                _fechar(server)
                try:
                    server = conectar()
                    recusados = server.send_message(mensagem) or {}
                except Exception as e:  # noqa: BLE001
                    perdida = e
            except smtplib.SMTPException as e:  # recusa do servidor: este par não saiu
                _mover_sem_falhar(par, False)
                registrar(ResultadoPar(par.nome, "erro", str(e)))
                continue
            except OSError as e:
                # Timeout/TLS: não dá para saber se o e-mail saiu. Não move nada e para o lote.
                incerto = e
            except Exception as e:  # noqa: BLE001
                _mover_sem_falhar(par, False)
                registrar(ResultadoPar(par.nome, "erro", str(e)))
                continue
            if incerto is not None:
                registrar(ResultadoPar(par.nome, "erro",
                                       f"Sem resposta do servidor ({incerto}). O e-mail pode ter saído: "
                                       "confira na pasta Itens Enviados antes de reenviar."))
                for resto in pares[i + 1:]:
                    registrar(ResultadoPar(resto.nome, "erro", "Não enviado: o lote parou por falta de resposta do servidor"))
                break
            if perdida is not None:
                for resto in pares[i:]:
                    registrar(ResultadoPar(resto.nome, "erro", f"Conexão perdida com o servidor ({perdida})"))
                break

            avisos = []
            if recusados:
                avisos.append("Destinatário(s) recusado(s): " + ", ".join(sorted(recusados)))
            try:
                mover_par(par, True)
            except OSError as e:
                avisos.append(f"Enviado, mas não foi movido para enviados/ ({e}). "
                              "O arquivo continua na pasta: não envie de novo.")
            registrar(ResultadoPar(par.nome, "aviso", " ".join(avisos)) if avisos
                      else ResultadoPar(par.nome, "enviado"))
    finally:
        _fechar(server)
    return resultados


def _mover_sem_falhar(par: Par, sucesso: bool) -> None:
    try:
        mover_par(par, sucesso)
    except OSError:
        pass
