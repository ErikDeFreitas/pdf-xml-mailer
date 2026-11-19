"""Modo terminal: envia um e-mail por par PDF + XML de uma pasta.

    python -m core "C:\\Pasta" --vcto 20/11/2026 --dry-run   # só lista
    python -m core "C:\\Pasta" --vcto 20/11/2026             # envia

Usa a conta Microsoft, o Para/Cco e o texto do e-mail salvos pelo programa (abra a janela uma vez antes).
"""
from __future__ import annotations

import argparse
from pathlib import Path

from core import configuracao, envio
from core.conta import Conta, ContaNaoConfigurada, FalhaLogin

ROTULO = {"enviado": "OK   ", "aviso": "AVISO", "erro": "ERRO "}


def main(argv: list[str], conta_factory=Conta) -> int:
    ap = argparse.ArgumentParser(prog="python -m core", description="Envia PDF + XML por e-mail.")
    ap.add_argument("pasta", help="pasta com os PDFs e XMLs")
    ap.add_argument("--vcto", required=True, help="vencimento (dd/mm/aaaa)")
    ap.add_argument("--cco", help="cópia oculta (sem isso, usa a salva)")
    ap.add_argument("--dry-run", action="store_true", help="não envia, só lista")
    args = ap.parse_args(argv)

    cfg = configuracao.carregar()
    if cfg is None:
        print("Configure Para/Cco abrindo o programa uma vez.")
        return 2
    try:
        vcto = envio.validar_vcto(args.vcto)
        cco = envio.validar_emails(args.cco, False) if args.cco is not None else cfg.cco
    except ValueError as e:
        print(e)
        return 2

    pasta = Path(args.pasta)
    if not pasta.is_dir():
        print(f"Pasta não encontrada: {pasta}")
        return 2
    pares, avisos = envio.achar_pares(envio.arquivos_da_pasta(pasta))
    for aviso in avisos:
        print(f"  AVISO {aviso}")
    if not pares:
        print("Nenhum par PDF + XML encontrado.")
        return 0

    print(f"{len(pares)} par(es) encontrado(s).")
    if args.dry_run:
        for par in pares:
            assunto = envio.montar_assunto(par.nome, vcto, cfg.assunto)
            print(f"  [dry-run] Para: {', '.join(cfg.para)} | Assunto: {assunto}")
        return 0
    if envio.assunto_de_exemplo(cfg.assunto):
        print('O assunto ainda é o texto de exemplo. Abra o programa e use "Configurar e-mail".')
        return 2

    try:
        conta = conta_factory()
        email = conta.email()
        if not email:
            raise FalhaLogin("Nenhuma conta logada. Abra o programa e entre com a Microsoft.")
        resultados = envio.enviar_lote(
            pares, email, cfg.para, cco, vcto,
            conectar=lambda: envio.abrir_smtp(email, conta.token()),
            assunto=cfg.assunto, corpo=cfg.corpo,
            ao_concluir=lambda r: print(f"  {ROTULO[r.status]} {r.nome}" + (f": {r.detalhe}" if r.detalhe else "")),
        )
    except (ContaNaoConfigurada, FalhaLogin, envio.FalhaConexao) as e:
        print(e)
        return 2

    conta_status = {s: sum(r.status == s for r in resultados) for s in ROTULO}
    print(f"\nConcluído: {conta_status['enviado']} enviado(s), {conta_status['aviso']} com aviso, "
          f"{conta_status['erro']} com erro.")
    return 1 if conta_status["erro"] else 0
