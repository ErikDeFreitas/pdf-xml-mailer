"""Instância do Enviador aberta na casca ou no avulso."""

import logging
import queue
import threading
from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QWidget
from tcm_ui.modulo import Contexto

from enviador_pdf_xml import conta
from enviador_pdf_xml.conta import Conta, ContaNaoConfigurada
from enviador_pdf_xml.tela import AVISO_NAO_CONFIGURADA, TelaEnviar

INTERVALO_FILA_MS = 30  # de quanto em quanto tempo a tela confere se a conta ficou pronta
FABRICA_CONTA: Callable = conta.Conta  # os testes trocam por uma conta falsa


def criar_conta(log: logging.Logger) -> tuple[Conta | None, str]:
    """Cria a Conta Microsoft; sem ela a tela abre mesmo assim, com o motivo no aviso."""
    try:
        return FABRICA_CONTA(), ""
    except ContaNaoConfigurada:
        return None, AVISO_NAO_CONFIGURADA
    except Exception:  # noqa: BLE001 — sem rede ou cache ilegível não pode derrubar a janela
        log.exception("Não foi possível iniciar o login Microsoft")
        return None, "Não foi possível conectar ao login Microsoft (verifique a internet). Detalhes no log."


class _EntregaDeConta(QObject):
    """Esvazia, na thread da interface, a fila onde a thread de criação deixa a Conta.

    Filha da tela: some com ela. A thread nunca toca no Qt, então fechar a tela antes de a Conta
    chegar só descarta o resultado.
    """

    def __init__(self, tela: TelaEnviar, fila: queue.Queue):
        super().__init__(tela)
        self._tela = tela
        self._fila = fila
        self._timer = QTimer(self)
        self._timer.setInterval(INTERVALO_FILA_MS)
        self._timer.timeout.connect(self._conferir)
        self._timer.start()

    def _conferir(self) -> None:
        try:
            conta_msal, aviso = self._fila.get_nowait()
        except queue.Empty:
            return
        self._timer.stop()
        self.deleteLater()
        self._tela.definir_conta(conta_msal, aviso)


class Enviador:
    def __init__(self, contexto: Contexto):
        self.contexto = contexto
        self.tela: TelaEnviar | None = None

    def widget(self, chave_pagina: str) -> QWidget:
        if chave_pagina != "enviar":
            raise KeyError(chave_pagina)
        if self.tela is None:
            self.tela = TelaEnviar(self.contexto, None)
            self.tela.recriar_conta = self._criar_conta_em_segundo_plano
            self._criar_conta_em_segundo_plano()
        return self.tela

    def _criar_conta_em_segundo_plano(self) -> None:
        """O MSAL consulta a rede ao ser criado: isso roda fora da thread da interface, que não pode travar.

        A thread é daemon (não segura o fim do programa) e não toca no Qt: devolve o resultado por uma
        fila, que um timer da própria tela esvazia na thread da interface. Se a tela fechar antes, o
        resultado é simplesmente descartado.
        """
        tela = self.tela
        tela.aguardando_conta()
        log = self.contexto.log
        resultado: queue.Queue = queue.Queue(maxsize=1)
        threading.Thread(target=lambda: resultado.put(criar_conta(log)), daemon=True, name="criar-conta").start()
        _EntregaDeConta(tela, resultado)

    def acoes_cabecalho(self, chave_pagina: str) -> list[QWidget]:
        return []  # "Configurações" fica no cartão "Conta e destino"

    def pode_fechar(self) -> bool:
        return self.tela is None or not self.tela.rodando  # nunca fecha no meio de um envio
