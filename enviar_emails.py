#!/usr/bin/env python3
"""
Modo linha de comando: envia um e-mail por par PDF + XML da pasta 'entrada'.

    python enviar_emails.py --vcto 20/11/2026              # envia de verdade
    python enviar_emails.py --vcto 20/11/2026 --dry-run    # só mostra o que seria enviado

--vcto (dd/mm/aaaa) é obrigatório quando o corpo tem o campo {vcto}.
"""
import argparse
import shutil
import sys
import time
from pathlib import Path

import enviador


def achar_pares(pasta: Path):
    """Retorna (pares, sem_par). pares = {nome: (pdf, xml)}."""
    pdfs, xmls = {}, {}
    for arq in pasta.iterdir():
        if not arq.is_file():
            continue
        ext = arq.suffix.lower()
        if ext == ".pdf":
            pdfs[arq.stem] = arq
        elif ext == ".xml":
            xmls[arq.stem] = arq
    pares = {n: (pdfs[n], xmls[n]) for n in sorted(set(pdfs) & set(xmls))}
    sem_par = sorted(set(pdfs) ^ set(xmls))
    return pares, sem_par


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="não envia, só lista")
    ap.add_argument("--vcto", help="data de vencimento (dd/mm/aaaa) para o corpo do e-mail")
    args = ap.parse_args()

    try:
        cfg = enviador.carregar_config()
    except FileNotFoundError as e:
        sys.exit(str(e))

    base = enviador.BASE
    entrada = base / cfg["pastas"].get("entrada", "entrada")
    enviados = base / cfg["pastas"].get("enviados", "enviados")
    erros = base / cfg["pastas"].get("erros", "erros")
    for p in (entrada, enviados, erros):
        p.mkdir(exist_ok=True)

    corpo = enviador.carregar_corpo()
    vcto = args.vcto
    if enviador.corpo_exige_vcto(corpo):
        if not vcto:
            sys.exit("O corpo do e-mail usa {vcto}. Informe o vencimento: --vcto dd/mm/aaaa")
        try:
            vcto = enviador.validar_vcto(vcto)
        except ValueError as e:
            sys.exit(str(e))
    pares, sem_par = achar_pares(entrada)

    if sem_par:
        print("ATENÇÃO - arquivos sem par (ficam na pasta de entrada):")
        for n in sem_par:
            print(f"  - {n}")
    if not pares:
        print("Nenhum par PDF+XML encontrado.")
        return

    print(f"{len(pares)} par(es) encontrado(s).")
    if args.dry_run:
        for nome in pares:
            print(f"  [dry-run] Assunto: {enviador.montar_assunto(cfg, nome)}")
        return

    intervalo = float(cfg["smtp"].get("intervalo_segundos", "2"))
    ok = falha = 0
    server = enviador.abrir_smtp(cfg)
    try:
        for nome, (pdf, xml) in pares.items():
            try:
                anexos = [(pdf.name, pdf.read_bytes()), (xml.name, xml.read_bytes())]
                server.send_message(enviador.montar_mensagem(cfg, corpo, nome, anexos, vcto))
                shutil.move(str(pdf), enviados / pdf.name)
                shutil.move(str(xml), enviados / xml.name)
                print(f"  OK    {nome}")
                ok += 1
            except Exception as e:  # noqa: BLE001
                print(f"  ERRO  {nome}: {e}")
                shutil.move(str(pdf), erros / pdf.name)
                shutil.move(str(xml), erros / xml.name)
                falha += 1
            time.sleep(intervalo)
    finally:
        server.quit()

    print(f"\nConcluído: {ok} enviado(s), {falha} com erro.")


if __name__ == "__main__":
    main()
