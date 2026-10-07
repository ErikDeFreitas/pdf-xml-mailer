#!/usr/bin/env python3
"""
Guarda a senha SMTP no cofre do sistema (no Windows: Gerenciador de Credenciais),
em vez de deixá-la escrita em arquivo.

    python configurar_senha.py             # pergunta a senha e guarda
    python configurar_senha.py --remover   # apaga a senha guardada

O usuário vem do config.ini ([smtp] usuario). Precisa de:  python -m pip install keyring
"""
import argparse
import getpass
import sys

import enviador


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remover", action="store_true", help="apaga a senha guardada")
    args = ap.parse_args()

    try:
        import keyring
        import keyring.errors
    except ImportError:
        sys.exit("Instale primeiro: python -m pip install keyring")

    try:
        cfg = enviador.carregar_config()
    except FileNotFoundError as e:
        sys.exit(str(e))
    usuario = cfg["smtp"]["usuario"]

    if args.remover:
        try:
            keyring.delete_password(enviador.SERVICO_KEYRING, usuario)
            print(f"Senha de {usuario} removida do cofre.")
        except keyring.errors.PasswordDeleteError:
            print(f"Não havia senha guardada para {usuario}.")
        return

    senha = getpass.getpass(f"Senha de {usuario} (a digitação não aparece): ")
    if not senha:
        sys.exit("Senha vazia; nada foi salvo.")
    try:
        keyring.set_password(enviador.SERVICO_KEYRING, usuario, senha)
    except Exception as e:  # noqa: BLE001
        sys.exit(
            f"Não foi possível usar o cofre do sistema ({e}).\n"
            "Alternativa: defina a variável de ambiente ENVIADOR_SMTP_SENHA, "
            "ou deixe o programa perguntar a senha a cada execução."
        )
    print("Senha guardada no cofre do sistema.")
    print("Se o config.ini ainda tiver a linha 'senha', apague-a agora.")


if __name__ == "__main__":
    main()
