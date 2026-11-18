"""Login e envio fora da thread da interface, para a janela nunca travar (só QtCore)."""
from PySide6.QtCore import QObject, Signal, Slot

from core import atualizacao, envio
from core.conta import ContaNaoConfigurada, FalhaLogin


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

    def __init__(self, pares, para, cco, vcto, conta):
        super().__init__()
        self._pares, self._para, self._cco, self._vcto = pares, para, cco, vcto
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
            )
        except FalhaLogin as e:
            self.sessao_expirada.emit(str(e))
        except (envio.FalhaConexao, ContaNaoConfigurada, ValueError) as e:
            self.falhou.emit(str(e))
        except Exception as e:  # noqa: BLE001
            self.falhou.emit(f"Erro inesperado: {type(e).__name__}: {e}")
        else:
            self.concluido.emit(resultados)


class BaixarAtualizacaoWorker(QObject):
    progresso = Signal(int, int)  # bytes lidos, total
    concluido = Signal(str)       # caminho do .exe novo (já conferido)
    falhou = Signal(str)

    def __init__(self, release, exe):
        super().__init__()
        self._release, self._exe = release, exe
        self._cancelar = False

    def cancelar(self) -> None:
        self._cancelar = True

    @Slot()
    def run(self) -> None:
        try:
            novo = atualizacao.baixar_e_conferir(self._release, self._exe, self.progresso.emit,
                                                 lambda: self._cancelar)
        except atualizacao.FalhaAtualizacao as e:
            self.falhou.emit(str(e))
        except Exception as e:
            self.falhou.emit(f"Erro inesperado: {type(e).__name__}: {e}")
        else:
            self.concluido.emit(str(novo))
