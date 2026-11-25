"""Instância do Enviador aberta na casca ou no avulso."""

import logging
from collections.abc import Callable

from PySide6.QtWidgets import QWidget
from tcm_ui import microsoft
from tcm_ui.microsoft import Conta
from tcm_ui.modulo import Contexto

from enviador_pdf_xml import dados
from enviador_pdf_xml.tela import TelaEnviar

FABRICA_CONTA: Callable = microsoft.Conta  # os testes trocam por uma conta falsa


def criar_conta(log: logging.Logger) -> tuple[Conta | None, str]:
    """Cria a Conta Microsoft; sem ela a tela abre mesmo assim, com o motivo no aviso."""
    return microsoft.criar_conta(log, lambda: FABRICA_CONTA())


class Enviador:
    def __init__(self, contexto: Contexto):
        self.contexto = contexto
        self.tela: TelaEnviar | None = None

    def widget(self, chave_pagina: str) -> QWidget:
        if chave_pagina != "enviar":
            raise KeyError(chave_pagina)
        if self.tela is None:
            # o login da 2.0 ficava na pasta do Enviador; agora é compartilhado com os outros sistemas
            microsoft.migrar_cache(dados.pasta_local() / "token_cache.bin")
            self.tela = TelaEnviar(self.contexto, None)
            self.tela.recriar_conta = self._criar_conta_em_segundo_plano
            self._criar_conta_em_segundo_plano()
        return self.tela

    def _criar_conta_em_segundo_plano(self) -> None:
        """O MSAL consulta a rede ao ser criado: roda fora da thread da interface (ver tcm_ui.microsoft)."""
        tela = self.tela
        tela.aguardando_conta()
        microsoft.criar_conta_em_segundo_plano(tela, self.contexto.log, tela.definir_conta,
                                               fabrica=lambda: FABRICA_CONTA())

    def acoes_cabecalho(self, chave_pagina: str) -> list[QWidget]:
        return []  # "Configurações" fica no cartão "Conta e destino"

    def pode_fechar(self) -> bool:
        return self.tela is None or not self.tela.rodando  # nunca fecha no meio de um envio
