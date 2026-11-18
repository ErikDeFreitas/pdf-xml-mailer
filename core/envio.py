"""Regras de envio: pares PDF + XML, mensagem, SMTP e movimentação (sem interface)."""
from __future__ import annotations

import html as html_lib
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from core import modelo

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


def montar_assunto(nome: str) -> str:
    nome = nome.replace("\r", " ").replace("\n", " ").strip()
    return modelo.ASSUNTO.replace("{nome}", nome)


def montar_corpo(vcto: str) -> tuple[str, str]:
    return (modelo.CORPO_TEXTO.replace("{vcto}", vcto),
            modelo.CORPO_HTML.replace("{vcto}", html_lib.escape(vcto)))


def montar_mensagem(par: Par, remetente: str, para: list[str], cco: list[str], vcto: str,
                    pdf: bytes, xml: bytes) -> EmailMessage:
    texto, html = montar_corpo(vcto)
    msg = EmailMessage()
    msg["From"] = remetente
    msg["To"] = ", ".join(para)
    if cco:
        msg["Bcc"] = ", ".join(cco)
    msg["Subject"] = montar_assunto(par.nome)
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
    sub = PASTA_ENVIADOS if sucesso else PASTA_ERROS
    for arq in (par.pdf, par.xml):
        pasta = arq.parent / sub
        pasta.mkdir(exist_ok=True)
        shutil.move(str(arq), str(destino_livre(pasta, arq.name)))
