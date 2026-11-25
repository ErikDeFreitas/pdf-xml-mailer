"""Login e envio fora da thread da interface, para a janela nunca travar (só QtCore)."""
from PySide6.QtCore import QObject, Signal, Slot

from enviador_pdf_xml import envio
from enviador_pdf_xml.conta import ContaNaoConfigurada, FalhaLogin


class LoginWorker(QObject):
    concluido = Signal(str)  # e-mail logado
    falhou = Signal(str)

    def __init__(self, conta):
        super().__init__()
        self._conta = conta

    @Slot()
    def run(self) -> None:
        try:
            email = self._conta.entrar()
        except (FalhaLogin, ContaNaoConfigurada) as e:
            self.falhou.emit(str(e))
        except Exception as e:  # noqa: BLE001
            self.falhou.emit(f"Erro inesperado no login: {type(e).__name__}: {e}")
        else:
            self.concluido.emit(email)


class EnviarWorker(QObject):
    iniciou_par = Signal(int, int, str)  # índice (1..N), total, nome
    par_concluido = Signal(object)       # envio.ResultadoPar
    concluido = Signal(object)           # list[envio.ResultadoPar]
    falhou = Signal(str)
    sessao_expirada = Signal(str)        # precisa entrar com a Microsoft de novo

    def __init__(self, pares, para, cco, vcto, conta, assunto=None, corpo=None):
        super().__init__()
        self._pares, self._para, self._cco, self._vcto = pares, para, cco, vcto
        self._assunto, self._corpo = assunto, corpo  # texto de "Configurar e-mail"
        self._conta = conta
        self._cancelar = False

    def cancelar(self) -> None:
        self._cancelar = True

    @Slot()
    def run(self) -> None:
        conta = self._conta
        try:
            email = conta.email()
            if not email:
                raise FalhaLogin("Nenhuma conta logada. Entre com a Microsoft.")
            conta.token()  # confere a sessão antes de conectar
            resultados = envio.enviar_lote(
                self._pares, email, self._para, self._cco, self._vcto,
                conectar=lambda: envio.abrir_smtp(email, conta.token()),
                ao_iniciar=self.iniciou_par.emit,
                ao_concluir=self.par_concluido.emit,
                cancelado=lambda: self._cancelar,
                assunto=self._assunto, corpo=self._corpo,
            )
        except FalhaLogin as e:
            self.sessao_expirada.emit(str(e))
        except (envio.FalhaConexao, ContaNaoConfigurada, ValueError) as e:
            self.falhou.emit(str(e))
        except Exception as e:  # noqa: BLE001
            self.falhou.emit(f"Erro inesperado: {type(e).__name__}: {e}")
        else:
            self.concluido.emit(resultados)

