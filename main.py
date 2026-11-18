"""
Enviador de PDF + XML — aplicação desktop (PySide6).

Uso:   python main.py                       -> abre a janela
       python -m core "C:\\Pasta" --vcto dd/mm/aaaa [--dry-run]   -> modo terminal
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMainWindow, QStackedWidget, QWidget

from core import atualizacao, configuracao, envio
from core.configuracao import Configuracao
from core.conta import Conta, ContaNaoConfigurada
from core.worker import EnviarWorker
from ui import components as c
from ui import icons
from ui.atualizacao import VerificadorAtualizacao
from ui.conta import ContaModal
from ui.themes import APLICACAO, ORGANIZACAO, SPACE, theme_manager
from version import __version__

STATUS = {  # status -> (texto, tom do Badge)
    "pronto": ("Pronto", "neutral"),
    "enviando": ("Enviando…", "primary"),
    "enviado": ("Enviado", "success"),
    "aviso": ("Enviado com aviso", "warning"),
    "erro": ("Erro", "danger"),
    "sem_par": ("Sem par", "warning"),
}
_PADRAO = object()


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


class EnviarPage(c.Page):
    def __init__(self, conta, caminho_config: Path | None = None):
        super().__init__()
        self.conta = conta
        self.caminho_config = caminho_config
        self.cfg: Configuracao | None = configuracao.carregar(caminho_config)
        self._arquivos: dict[str, Path] = {}  # chave normalizada -> caminho (sem duplicar)
        self._pares: list[envio.Par] = []
        self._avisos: list[str] = []
        self._linha: dict[str, int] = {}
        self._detalhe: dict[str, str] = {}
        self._status: dict[str, str] = {}
        self._thread: QThread | None = None
        self._worker: EnviarWorker | None = None
        self._resultados: list[envio.ResultadoPar] = []

        # --- Conta e destino ------------------------------------------------
        self.lbl_conta = c.Label("", "body")
        self.btn_config = c.Button("Configurações", "secondary", "sm", icon="settings")
        self.btn_config.clicked.connect(self.abrir_configuracoes)
        self.lbl_para = c.Label("", "muted", wrap=True)
        self.aviso_login = c.Label("", "hint", wrap=True)
        destino = c.Card("Conta e destino")
        destino.add_header_action(self.btn_config)
        destino.add(c.hbox(c.Icon("mail", "primary"), self.lbl_conta, None, spacing=SPACE["sm"]),
                    self.lbl_para, self.aviso_login)

        # --- Arquivos -------------------------------------------------------
        self.btn_arquivos = c.Button("Escolher arquivos", "secondary", icon="file-text")
        self.btn_arquivos.clicked.connect(self._escolher_arquivos)
        self.btn_limpar = c.Button("Limpar", "ghost", icon="eraser")
        self.btn_limpar.clicked.connect(self.limpar)
        self.tabela = c.DataTable(["Nome", "PDF", "XML", "Status"])
        self.tabela.set_column_widths({0: 200, 1: 200, 2: 200})
        self.tabela.setMinimumHeight(280)
        self.tabela.cellClicked.connect(self._clique_linha)
        arquivos = c.Card("Arquivos", "Arraste PDFs, XMLs ou pastas para esta janela. "
                                      "Cada PDF precisa de um XML com o mesmo nome.")
        arquivos.add(c.hbox(self.btn_arquivos, None, self.btn_limpar, spacing=SPACE["sm"]),
                     self.tabela)

        # --- Envio ----------------------------------------------------------
        self.campo_vcto = c.Input("dd/mm/aaaa")
        self.campo_vcto.setInputMask("99/99/9999;_")
        self.campo_vcto.textChanged.connect(self._atualizar_botao)
        self.campo_vcto_field = c.FormField("Vencimento", self.campo_vcto, "Aparece no corpo do e-mail.")
        self.lbl_assunto = c.Label("", "muted", wrap=True)
        self.lbl_resumo = c.Label("", "muted")
        self.progresso = c.ProgressBar()
        self.progresso.hide()
        self.botao_cancelar = c.Button("Cancelar", "danger", icon="x")
        self.botao_cancelar.clicked.connect(self._cancelar)
        self.botao_cancelar.hide()
        # Design TCM: azul (primary) para escolher a pasta, vermelho (danger) para o envio, que
        # não tem volta.
        self.btn_pasta = c.Button("Escolher pasta", "primary", icon="folder-open")
        self.btn_pasta.clicked.connect(self._escolher_pasta)
        self.botao_enviar = c.Button("Enviar", "danger", icon="send")
        self.botao_enviar.clicked.connect(self._enviar)
        envio_card = c.Card("Envio")
        envio_card.add(
            self.campo_vcto_field,
            self.lbl_assunto,
            self.progresso,
            c.hbox(self.lbl_resumo, None, self.botao_cancelar, self.btn_pasta, self.botao_enviar,
                   spacing=SPACE["sm"]),
        )

        self.add(destino, envio_card, arquivos, stretch_last=True)
        self.recarregar_conta()

    # --- Estado ---------------------------------------------------------
    @property
    def rodando(self) -> bool:
        return self._thread is not None

    def email(self) -> str | None:
        return self.conta.email() if self.conta is not None else None

    def recarregar_conta(self) -> None:
        self.cfg = configuracao.carregar(self.caminho_config)
        email = self.email()
        self.lbl_conta.setText(email or "Nenhuma conta conectada")
        texto = "Para: " + ("; ".join(self.cfg.para) if self.cfg else "não configurado")
        if self.cfg and self.cfg.cco:
            texto += "   ·   Cco: " + "; ".join(self.cfg.cco)
        self.lbl_para.setText(texto)
        self.aviso_login.setText(
            "O login Microsoft ainda não foi configurado nesta versão. Fale com a TI."
            if self.conta is None else "")
        self.aviso_login.setVisible(bool(self.aviso_login.text()))
        self._atualizar_botao()

    def pronto_para_configurar(self) -> bool:
        """True se falta conta logada ou Para (primeiro acesso)."""
        return self.conta is not None and (self.cfg is None or not self.email())

    def _vcto_valido(self) -> bool:
        try:
            envio.validar_vcto(self.campo_vcto.text())
            return True
        except ValueError:
            return False

    def _atualizar_botao(self, *_) -> None:
        n = len(self._pares)
        self.botao_enviar.setText(f"Enviar {_plural(n, 'e-mail', 'e-mails')}" if n else "Enviar")
        self.botao_enviar.setEnabled(
            bool(n) and self._vcto_valido() and self.cfg is not None and bool(self.email()) and not self.rodando
        )

    # --- Arquivos -------------------------------------------------------
    def adicionar(self, caminhos: list[Path]) -> None:
        if self.rodando:
            return
        for caminho in map(Path, caminhos):
            lista = envio.arquivos_da_pasta(caminho) if caminho.is_dir() else [caminho]
            for arq in lista:
                if arq.suffix.lower() in (".pdf", ".xml"):
                    self._arquivos.setdefault(str(arq.resolve()).casefold(), arq)
        self._remontar()

    def _remontar(self) -> None:
        self._pares, self._avisos = envio.achar_pares(self._arquivos.values())
        self.tabela.clear_rows()
        self._linha.clear()
        self._status.clear()
        self._detalhe.clear()
        for par in self._pares:
            self._linha[par.nome] = self.tabela.add_row(
                [par.nome, par.pdf.name, par.xml.name, c.Badge(*STATUS["pronto"])], data=par.nome)
            self._status[par.nome] = STATUS["pronto"][0]
        for aviso in self._avisos:
            nome, _, motivo = aviso.partition(": ")
            self.tabela.add_row([nome, "—", "—", c.Badge(motivo.capitalize(), STATUS["sem_par"][1])])
        if self._pares:
            self.lbl_assunto.setText(f"Assunto (prévia): {envio.montar_assunto(self._pares[0].nome)}")
        else:
            self.lbl_assunto.setText("")
        sem_par = len(self._avisos)
        self.lbl_resumo.setText(
            f"{_plural(len(self._pares), 'par pronto', 'pares prontos')}"
            + (f" · {sem_par} sem par" if sem_par else "") if (self._pares or sem_par) else "")
        self._atualizar_botao()

    def limpar(self) -> None:
        if self.rodando:
            return
        self._arquivos.clear()
        self._resultados = []
        self.progresso.hide()
        self._remontar()

    def _escolher_arquivos(self) -> None:
        nomes, _ = QFileDialog.getOpenFileNames(self, "Escolha os PDFs e XMLs", str(Path.home()),
                                                "PDF e XML (*.pdf *.xml)")
        if nomes:
            self.adicionar([Path(n) for n in nomes])

    def _escolher_pasta(self) -> None:
        pasta = QFileDialog.getExistingDirectory(self, "Escolha a pasta com os PDFs e XMLs", str(Path.home()))
        if pasta:
            self.adicionar([Path(pasta)])

    # --- Status por linha -------------------------------------------------
    def _set_status(self, nome: str, status: str, detalhe: str = "") -> None:
        linha = self._linha.get(nome)
        if linha is None:
            return
        texto, tom = STATUS[status]
        badge = c.Badge(texto, tom, clickable=bool(detalhe),
                        tooltip="Clique para ver os detalhes" if detalhe else "")
        if detalhe:
            badge.clicked.connect(lambda n=nome: self._mostrar_detalhe(n))
        celula = QWidget()
        celula.setLayout(c.hbox(badge, None))
        celula.layout().setContentsMargins(SPACE["md"], 0, SPACE["md"], 0)
        self.tabela.setCellWidget(linha, 3, celula)
        self._status[nome] = texto
        self._detalhe[nome] = detalhe

    def status_de(self, nome: str) -> str | None:
        return self._status.get(nome)

    def _clique_linha(self, linha: int, _coluna: int) -> None:
        nome = self.tabela.row_data(linha)
        if nome and self._detalhe.get(nome):
            self._mostrar_detalhe(nome)

    def _mostrar_detalhe(self, nome: str) -> None:
        c.Modal.alert(self, f"{nome} · {self._status.get(nome, '')}", self._detalhe.get(nome, ""),
                      tone="danger" if self._status.get(nome) == "Erro" else "warning")

    # --- Envio ----------------------------------------------------------
    def abrir_configuracoes(self, primeiro_acesso: bool = False, sessao_expirada: bool = False) -> bool:
        modal = ContaModal(self.conta, self.cfg, self.window(), self.caminho_config, primeiro_acesso,
                           sessao_expirada)
        aceito = modal.exec() == ContaModal.DialogCode.Accepted
        self.recarregar_conta()
        return aceito

    def _enviar(self) -> None:
        if self.rodando or not self._pares or self.cfg is None:
            return
        try:
            vcto = envio.validar_vcto(self.campo_vcto.text())
            self.campo_vcto_field.set_error(None)
        except ValueError as e:
            self.campo_vcto_field.set_error(str(e))
            return
        cco = list(self.cfg.cco)  # definido só em Configurações

        n = len(self._pares)
        mensagem = f"Para: {'; '.join(self.cfg.para)}" + (f"\nCco: {'; '.join(cco)}" if cco else "")
        if not c.Modal.confirm(self, f"Enviar {_plural(n, 'e-mail', 'e-mails')}?", mensagem,
                               confirm_text="Enviar"):
            return

        self._resultados = []
        self.progresso.setRange(0, n)
        self.progresso.setValue(0)
        self.progresso.show()
        self._set_rodando(True)

        self._thread = QThread(self)
        self._worker = EnviarWorker(list(self._pares), list(self.cfg.para), cco, vcto, self.conta)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.iniciou_par.connect(self._ao_iniciar_par)
        self._worker.par_concluido.connect(self._ao_concluir_par)
        self._worker.concluido.connect(self._ao_concluir)
        self._worker.falhou.connect(self._ao_falhar)
        self._worker.sessao_expirada.connect(self._ao_expirar)
        for sinal in (self._worker.concluido, self._worker.falhou, self._worker.sessao_expirada):
            sinal.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._ao_terminar_thread)
        self._thread.start()

    def _set_rodando(self, rodando: bool) -> None:
        for w in (self.btn_arquivos, self.btn_pasta, self.btn_limpar, self.btn_config):
            w.setEnabled(not rodando)
        self.campo_vcto.setReadOnly(rodando)
        self.botao_cancelar.setVisible(rodando)
        self.botao_cancelar.setEnabled(True)
        self.botao_enviar.setVisible(not rodando)
        self._atualizar_botao()

    def _cancelar(self) -> None:
        if self.rodando and c.Modal.confirm(
                self, "Cancelar envio?", "O envio para depois do e-mail atual. Os já enviados continuam enviados.",
                confirm_text="Cancelar envio", cancel_text="Continuar", destructive=True):
            self.parar()

    def parar(self) -> None:
        if self._worker:
            self._worker.cancelar()
            self.botao_cancelar.setEnabled(False)
            self.lbl_resumo.setText("Cancelando após o e-mail atual…")

    def aguardar(self) -> None:
        if self._thread:
            self._thread.quit()
            self._thread.wait()

    def _ao_iniciar_par(self, indice: int, total: int, nome: str) -> None:
        self._set_status(nome, "enviando")
        if self.botao_cancelar.isEnabled():
            self.lbl_resumo.setText(f"Enviando {indice} de {total}: {nome}")

    def _ao_concluir_par(self, r: envio.ResultadoPar) -> None:
        self._resultados.append(r)
        self._set_status(r.nome, r.status, r.detalhe)
        self.progresso.setValue(len(self._resultados))

    def _ao_concluir(self, resultados: list) -> None:
        n = {s: sum(r.status == s for r in resultados) for s in ("enviado", "aviso", "erro")}
        texto = f"{_plural(n['enviado'] + n['aviso'], 'enviado', 'enviados')}"
        if n["aviso"]:
            texto += f" ({n['aviso']} com aviso)"
        if n["erro"]:
            texto += f" · {n['erro']} com erro, clique na linha para ver o motivo"
        if len(resultados) < len(self._pares):
            texto = f"Cancelado: {texto}"
        self.lbl_resumo.setText(texto)

    def _ao_falhar(self, mensagem: str) -> None:
        self.progresso.hide()
        self.lbl_resumo.setText("")
        c.Modal.alert(self, "Não foi possível enviar", mensagem, tone="danger")

    def _ao_expirar(self, mensagem: str) -> None:
        self.progresso.hide()
        self.lbl_resumo.setText(mensagem)
        QTimer.singleShot(0, lambda: self.abrir_configuracoes(sessao_expirada=True))

    def _ao_terminar_thread(self) -> None:
        self._thread = None
        self._worker = None
        # Só segue pendente o par que NÃO saiu e continua no lugar (ex.: conexão caiu). Enviado ou
        # enviado com aviso (arquivo preso, não movido) nunca volta para a fila: evita e-mail duplicado.
        # A tabela fica como está até "Limpar".
        saiu = {r.nome for r in self._resultados if r.status in ("enviado", "aviso")}
        self._pares = [p for p in self._pares
                       if p.nome not in saiu and p.pdf.exists() and p.xml.exists()]
        self._arquivos = {k: v for k, v in self._arquivos.items() if v.exists()}
        self._set_rodando(False)


# ---------------------------------------------------------------------------
# Janela principal
# ---------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, conta=_PADRAO, caminho_config: Path | None = None):
        super().__init__()
        self.setWindowTitle("Enviador de PDF + XML")
        self.resize(1180, 820)
        self.setMinimumSize(960, 640)
        self.setAcceptDrops(True)
        self._atualizar_icone_janela()
        theme_manager.changed.connect(self._atualizar_icone_janela)

        if conta is _PADRAO:
            try:
                conta = Conta()
            except ContaNaoConfigurada:
                conta = None
        self.pagina = EnviarPage(conta, caminho_config)

        self.sidebar = c.Sidebar("Enviador", "mail")
        self.sidebar.add_item("Enviar", "send")
        self.sidebar.footer.addWidget(c.Label(f"Versão {__version__}", "hint"))
        self.header = c.Header()
        self.header.add_action(c.ThemeToggle())
        self.header.set_title("Enviar PDF + XML", "Um e-mail por par de arquivos com o mesmo nome.")

        self.stack = QStackedWidget()
        self.stack.addWidget(self.pagina)
        raiz = QWidget()
        raiz.setObjectName("AppRoot")
        raiz.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        raiz.setLayout(c.hbox(self.sidebar, c.vbox(self.header, self.stack, spacing=0), spacing=0))
        self.setCentralWidget(raiz)
        self.sidebar.set_current(0)

        self.atualizacao = VerificadorAtualizacao(self, __version__, lambda: self.pagina.rodando)
        QTimer.singleShot(1500, self.atualizacao.iniciar)

    def primeiro_acesso(self) -> None:
        if self.pagina.pronto_para_configurar():
            self.pagina.abrir_configuracoes(primeiro_acesso=True)

    def _atualizar_icone_janela(self, *_) -> None:
        self.setWindowIcon(icons.icon("mail", theme_manager.color("primary"), 64))

    # Arrastar e soltar arquivos/pastas em qualquer lugar da janela.
    def dragEnterEvent(self, event) -> None:  # noqa: N802
        if event.mimeData().hasUrls() and not self.pagina.rodando:
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        caminhos = [Path(u.toLocalFile()) for u in event.mimeData().urls() if u.isLocalFile()]
        self.pagina.adicionar(caminhos)
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:  # noqa: N802
        pagina = self.pagina
        if pagina.rodando:
            if not c.Modal.confirm(
                self, "Sair durante o envio?", "O envio será interrompido depois do e-mail atual.",
                confirm_text="Sair", cancel_text="Continuar", destructive=True,
            ):
                event.ignore()
                return
            pagina.parar()
            pagina.aguardar()
        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZACAO)
    app.setApplicationName(APLICACAO)
    app.setApplicationVersion(__version__)
    theme_manager.apply()
    atualizacao.limpar_antigo()  # remove o .exe.old deixado pela última atualização

    janela = MainWindow()
    janela.show()
    QTimer.singleShot(300, janela.primeiro_acesso)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
