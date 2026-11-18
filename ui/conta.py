"""Modal "Conta e destino": primeiro acesso e Configurações.

Login Microsoft (no navegador, numa QThread) + Para (obrigatório) e Cco (opcional).
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread

from core import configuracao, envio
from core.configuracao import Configuracao
from core.worker import LoginWorker
from ui import components as c


class ContaModal(c.Modal):
    def __init__(self, conta, cfg: Configuracao | None, parent=None, caminho_config: Path | None = None,
                 primeiro_acesso: bool = False, sessao_expirada: bool = False):
        super().__init__("Bem-vindo! Configure o envio" if primeiro_acesso else "Conta e destino",
                         "Entre com a sua conta Microsoft e informe para quem os e-mails vão.",
                         "settings", "primary", parent)
        self._conta = conta
        # Sessão expirada: a conta ainda aparece no cache, mas o token não renova.
        # Força "Entrar com a Microsoft" até um login novo dar certo.
        self._precisa_login = sessao_expirada
        self._caminho = caminho_config
        self._thread: QThread | None = None
        self.resultado: Configuracao | None = None

        # Conta
        self.rotulo_conta = c.Label("", "body")
        self.aviso = c.Label("", "hint", wrap=True)
        self.botao_entrar = c.Button("Entrar com a Microsoft", "primary")
        self.botao_entrar.clicked.connect(self._entrar)
        self.botao_sair = c.Button("Sair da conta", "ghost", "sm", icon="log-out")
        self.botao_sair.clicked.connect(self._sair)
        self.body.addWidget(c.Label("Conta de envio", "label"))
        self.body.addLayout(c.hbox(self.rotulo_conta, None, self.botao_sair, spacing=c.SPACE["sm"]))
        self.body.addWidget(self.botao_entrar)
        self.body.addWidget(self.aviso)

        # Destino
        self.campo_para = c.Input("destino@cliente.com.br")
        self.campo_cco = c.Input("opcional")
        self.campo_para_field = c.FormField("Para", self.campo_para, "Um ou mais e-mails separados por ;")
        self.campo_cco_field = c.FormField("Cco (opcional)", self.campo_cco,
                                           "Cópia oculta. Também pode ser trocado na tela de envio.")
        self.body.addWidget(self.campo_para_field)
        self.body.addWidget(self.campo_cco_field)
        if cfg:
            self.campo_para.setText("; ".join(cfg.para))
            self.campo_cco.setText("; ".join(cfg.cco))

        self.add_button("Cancelar", "secondary")
        self.botao_salvar = c.Button("Salvar", "primary")
        self.botao_salvar.setDefault(True)
        self.botao_salvar.clicked.connect(self._salvar)
        self.footer.addWidget(self.botao_salvar)

        self._atualizar()

    # ------------------------------------------------------------------
    def _email(self) -> str | None:
        if self._conta is None or self._precisa_login:
            return None
        return self._conta.email()

    def _atualizar(self) -> None:
        email = self._email()
        logado = bool(email)
        texto = "Sua sessão expirou. Entre novamente." if self._precisa_login else "Nenhuma conta conectada"
        self.rotulo_conta.setText(email or texto)
        self.botao_sair.setVisible(logado)
        self.botao_entrar.setVisible(not logado)
        self.botao_entrar.setEnabled(self._conta is not None and self._thread is None)
        self.botao_salvar.setEnabled(logado)
        if self._conta is None:
            self.aviso.setText("O login Microsoft ainda não foi configurado nesta versão. Fale com a TI.")
        self.aviso.setVisible(bool(self.aviso.text()))

    def _entrar(self) -> None:
        self.aviso.setText("")
        self.botao_entrar.setText("Aguardando login no navegador…")
        self._thread = QThread(self)
        self._worker = LoginWorker(self._conta)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.concluido.connect(self._fim_login)
        self._worker.falhou.connect(self._falha_login)
        self._worker.concluido.connect(self._thread.quit)
        self._worker.falhou.connect(self._thread.quit)
        self._thread.finished.connect(self._thread_terminou)
        self._atualizar()
        self._thread.start()

    def _fim_login(self, _email: str) -> None:
        self._precisa_login = False
        self.botao_entrar.setText("Entrar com a Microsoft")

    def _falha_login(self, mensagem: str) -> None:
        self.botao_entrar.setText("Entrar com a Microsoft")
        self.aviso.setText(mensagem)

    def _thread_terminou(self) -> None:
        self._thread = None
        self._atualizar()

    def _sair(self) -> None:
        if self._conta is not None:
            self._conta.sair()
        self._atualizar()

    def _salvar(self) -> None:
        if not self._email():
            return
        ok = True
        try:
            para = envio.validar_emails(self.campo_para.text(), True)
            self.campo_para_field.set_error(None)
        except ValueError as e:
            self.campo_para_field.set_error(str(e))
            ok = False
        try:
            cco = envio.validar_emails(self.campo_cco.text(), False)
            self.campo_cco_field.set_error(None)
        except ValueError as e:
            self.campo_cco_field.set_error(str(e))
            ok = False
        if not ok:
            return
        self.resultado = Configuracao(para=para, cco=cco)
        configuracao.salvar(self.resultado, self._caminho)
        self.accept()

    def reject(self) -> None:  # não fecha no meio do login
        if self._thread is None:
            super().reject()

    def done(self, r: int) -> None:  # noqa: D401
        if self._thread is not None and self._thread.isRunning():
            return
        super().done(r)
