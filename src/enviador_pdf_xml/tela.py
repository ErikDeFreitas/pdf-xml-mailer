"""Tela do Enviador de PDF + XML: escolhe os arquivos, confere os pares e envia um e-mail por par."""

from pathlib import Path

from PySide6.QtCore import Qt, QThread, QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLabel
from tcm_ui import icons
from tcm_ui.components import BarraProgresso, Botao, Campo, CampoTexto, Cartao, Etiqueta, Modal, Pagina, Tabela, Texto
from tcm_ui.microsoft import AVISO_NAO_CONFIGURADA
from tcm_ui.modulo import Contexto
from tcm_ui.themes import ESPACO, TAMANHOS, tema

from enviador_pdf_xml import configuracao, envio
from enviador_pdf_xml.configuracao import Configuracao
from enviador_pdf_xml.dialogos import DialogoConta, DialogoEmail
from enviador_pdf_xml.worker import EnviarWorker

STATUS = {  # status -> (texto, tom da Etiqueta)
    "pronto": ("Pronto", "neutro"),
    "enviando": ("Enviando…", "primaria"),
    "enviado": ("Enviado", "sucesso"),
    "aviso": ("Enviado com aviso", "aviso"),
    "erro": ("Erro", "perigo"),
    "sem_par": ("Sem par", "aviso"),
}

AVISO_CONECTANDO = "Conectando à conta Microsoft…"

COL_NOME = 0
COL_STATUS = 3
ROLE_NOME = Qt.UserRole + 1  # Qt.UserRole é do filtro de texto da Tabela


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _linha(*itens, espaco: int = ESPACO["sm"]) -> QHBoxLayout:
    """Layout horizontal; None vira espaço elástico."""
    caixa = QHBoxLayout()
    caixa.setSpacing(espaco)
    for item in itens:
        if item is None:
            caixa.addStretch(1)
        else:
            caixa.addWidget(item)
    return caixa


class TelaEnviar(Pagina):
    """Página única do Enviador (o antigo EnviarPage, sem janela, barra lateral e cabeçalho)."""

    def __init__(self, contexto: Contexto, conta, caminho_config: Path | None = None):
        super().__init__()
        self.contexto = contexto
        self.conta = conta
        self.caminho_config = caminho_config
        self.cfg: Configuracao | None = configuracao.carregar(caminho_config)
        self._aviso_conta = ""  # motivo de não haver conta (ex.: login Microsoft não configurado)
        self._arquivos: dict[str, Path] = {}  # chave normalizada -> caminho (sem duplicar)
        self._pares: list[envio.Par] = []
        self._avisos: list[str] = []
        self._linha: dict[str, int] = {}
        self._detalhe: dict[str, str] = {}
        self._status: dict[str, str] = {}
        self._thread: QThread | None = None
        self._worker: EnviarWorker | None = None
        self._resultados: list[envio.ResultadoPar] = []
        self._encerrando = False
        self._primeiro_acesso_feito = False
        self._primeiro_acesso_pendente = False  # o timer disparou enquanto a conta ainda era criada
        self._conectando = False  # criando a Conta Microsoft em segundo plano
        self.recriar_conta = None  # quem cria a Conta (Enviador) liga aqui o "Tentar de novo"
        self.setAcceptDrops(True)

        # --- Conta e destino ------------------------------------------------
        self._icone_conta = QLabel()
        self.lbl_conta = Texto("")
        self.btn_config = Botao("Configurações", "secundario", "sm", icone="config")
        self.btn_config.clicked.connect(self.abrir_configuracoes)
        self.lbl_para = Texto("", "suave")
        self.lbl_para.setWordWrap(True)
        self.aviso_login = Texto("", "dica")
        self.aviso_login.setWordWrap(True)
        destino = Cartao("Conta e destino")
        self.btn_tentar = Botao("Tentar de novo", "secundario", "sm")
        self.btn_tentar.clicked.connect(self.tentar_de_novo)
        self.btn_tentar.hide()
        destino.adicionar_acao(self.btn_tentar)
        destino.adicionar_acao(self.btn_config)
        destino.corpo.addLayout(_linha(self._icone_conta, self.lbl_conta, None))
        destino.corpo.addWidget(self.lbl_para)
        destino.corpo.addWidget(self.aviso_login)
        tema.mudou.connect(self._pintar_icone)
        self._pintar_icone()

        # --- Arquivos -------------------------------------------------------
        self.btn_arquivos = Botao("Escolher arquivos", "secundario", icone="arquivo")
        self.btn_arquivos.clicked.connect(self._escolher_arquivos)
        self.btn_limpar = Botao("Limpar", "fantasma", icone="borracha")
        self.btn_limpar.clicked.connect(self.limpar)
        self.tabela = Tabela(["Nome", "PDF", "XML", "Status"])
        self.tabela.setMinimumHeight(280)
        self.tabela.cellClicked.connect(self._clique_linha)
        arquivos = Cartao("Arquivos", "Arraste PDFs, XMLs ou pastas para esta página. "
                                      "Cada PDF precisa de um XML com o mesmo nome.")
        arquivos.corpo.addLayout(_linha(self.btn_arquivos, None, self.btn_limpar))
        arquivos.corpo.addWidget(self.tabela)

        # --- Envio ----------------------------------------------------------
        self.campo_vcto = CampoTexto("dd/mm/aaaa")
        self.campo_vcto.setInputMask("99/99/9999;_")
        self.campo_vcto.textChanged.connect(self._atualizar_botao)
        self.campo_vcto.textChanged.connect(self._atualizar_assunto)
        self.campo_vcto_field = Campo("Vencimento", self.campo_vcto, "Aparece no corpo do e-mail.")
        self.lbl_assunto = Texto("", "suave")
        self.lbl_assunto.setWordWrap(True)
        self.btn_email = Botao("Configurar e-mail", "secundario", "sm", icone="email")
        self.btn_email.clicked.connect(self.abrir_email)
        self.lbl_resumo = Texto("", "suave")
        self.progresso = BarraProgresso()
        self.progresso.hide()
        self.botao_cancelar = Botao("Cancelar", "perigo", icone="fechar")
        self.botao_cancelar.clicked.connect(self._cancelar)
        self.botao_cancelar.hide()
        # Design TCM: azul (primário) para escolher a pasta, vermelho (perigo) para o envio, que
        # não tem volta.
        self.btn_pasta = Botao("Escolher pasta", "primario", icone="pasta")
        self.btn_pasta.clicked.connect(self._escolher_pasta)
        self.botao_enviar = Botao("Enviar", "perigo", icone="enviar")
        self.botao_enviar.clicked.connect(self._enviar)
        envio_card = Cartao("Envio")
        envio_card.corpo.addWidget(self.campo_vcto_field)
        linha_assunto = QHBoxLayout()
        linha_assunto.setSpacing(ESPACO["sm"])
        linha_assunto.addWidget(self.lbl_assunto, 1)
        linha_assunto.addWidget(self.btn_email)
        envio_card.corpo.addLayout(linha_assunto)
        envio_card.corpo.addWidget(self.progresso)
        envio_card.corpo.addLayout(
            _linha(self.lbl_resumo, None, self.botao_cancelar, self.btn_pasta, self.botao_enviar))

        self.conteudo.addWidget(destino)
        self.conteudo.addWidget(envio_card)
        self.conteudo.addWidget(arquivos, 1)
        self.recarregar_conta()

        # Ao fechar o programa o envio para e a thread termina antes de o processo acabar (a
        # confirmação já vem do pode_fechar na JanelaPrincipal). A conexão com um método de
        # QObject some sozinha quando a tela é destruída.
        QApplication.instance().aboutToQuit.connect(self._encerrar)

    def _pintar_icone(self, *_) -> None:
        self._icone_conta.setPixmap(icons.pixmap("email", tema.tokens()["primaria"], TAMANHOS["icone"]))

    # --- Estado ---------------------------------------------------------
    @property
    def rodando(self) -> bool:
        return self._thread is not None

    def aguardando_conta(self) -> None:
        """A Conta está sendo criada em segundo plano: Enviar e Configurações ficam desativados."""
        self._conectando = True
        self._aviso_conta = ""
        self.recarregar_conta()

    def definir_conta(self, conta, aviso: str = "") -> None:
        """Recebe a Conta criada em segundo plano (ou o motivo de não haver)."""
        if self._encerrando:
            return
        self._conectando = False
        self.conta = conta
        self._aviso_conta = aviso
        self.recarregar_conta()
        if self._primeiro_acesso_pendente:
            self._primeiro_acesso_pendente = False
            QTimer.singleShot(0, self._primeiro_acesso)

    def pode_tentar_de_novo(self) -> bool:
        """Falha passageira (sem internet, cache ilegível): vale criar a Conta de novo."""
        return (self.conta is None and not self._conectando and bool(self._aviso_conta)
                and self._aviso_conta != AVISO_NAO_CONFIGURADA and self.recriar_conta is not None)

    def tentar_de_novo(self) -> None:
        if self.pode_tentar_de_novo():
            self.recriar_conta()

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
        if self._conectando:
            aviso = AVISO_CONECTANDO
        else:
            aviso = (self._aviso_conta or AVISO_NAO_CONFIGURADA) if self.conta is None else ""
        self.aviso_login.setText(aviso)
        self.aviso_login.setVisible(bool(aviso))
        self.btn_tentar.setVisible(self.pode_tentar_de_novo())
        self._atualizar_assunto()
        self._atualizar_botao()

    def _assunto_pendente(self) -> bool:
        return self.cfg is not None and envio.assunto_de_exemplo(self.cfg.assunto)

    def _atualizar_assunto(self) -> None:
        if self._assunto_pendente():
            self.lbl_assunto.setText('O assunto ainda é o texto de exemplo. Clique em "Configurar e-mail" '
                                     "antes de enviar.")
        elif self._pares and self.cfg is not None:
            vcto = self.campo_vcto.text() if self._vcto_valido() else ""
            self.lbl_assunto.setText(
                f"Assunto (prévia): {envio.montar_assunto(self._pares[0].nome, vcto, self.cfg.assunto)}")
        else:
            self.lbl_assunto.setText("")

    def pronto_para_configurar(self) -> bool:
        """True se falta conta logada ou Para (primeiro acesso)."""
        return not self._conectando and self.conta is not None and (self.cfg is None or not self.email())

    def _vcto_valido(self) -> bool:
        try:
            envio.validar_vcto(self.campo_vcto.text())
            return True
        except ValueError:
            return False

    def _atualizar_botao(self, *_) -> None:
        n = len(self._pares)
        self.botao_enviar.setText(
            f" Enviar {_plural(n, 'e-mail', 'e-mails')}" if n else " Enviar")
        self.botao_enviar.setEnabled(
            bool(n) and self._vcto_valido() and self.cfg is not None and bool(self.email()) and not self.rodando
            and not self._assunto_pendente() and not self._conectando
        )
        self.btn_config.setEnabled(not self.rodando and not self._conectando)
        self.btn_email.setEnabled(self.cfg is not None and not self.rodando)

    # --- Primeiro acesso ------------------------------------------------
    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        if not self._primeiro_acesso_feito:
            self._primeiro_acesso_feito = True  # só uma vez por instância
            QTimer.singleShot(300, self._primeiro_acesso)

    def _primeiro_acesso(self) -> None:
        if self._encerrando:
            return
        if self._conectando:
            self._primeiro_acesso_pendente = True  # definir_conta() retoma quando a conta chegar
        elif self.pronto_para_configurar():
            self.abrir_configuracoes(primeiro_acesso=True)

    # --- Arrastar e soltar ----------------------------------------------
    def dragEnterEvent(self, evento) -> None:  # noqa: N802
        if evento.mimeData().hasUrls() and not self.rodando:
            evento.acceptProposedAction()

    def dropEvent(self, evento) -> None:  # noqa: N802
        if self.rodando:
            return
        caminhos = [Path(u.toLocalFile()) for u in evento.mimeData().urls() if u.isLocalFile()]
        self.adicionar(caminhos)
        evento.acceptProposedAction()

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
        self.tabela.setRowCount(0)
        self._linha.clear()
        self._status.clear()
        self._detalhe.clear()
        for par in self._pares:
            linha = self.tabela.adicionar_linha(
                [par.nome, par.pdf.name, par.xml.name, Etiqueta(*STATUS["pronto"])])
            self.tabela.item(linha, COL_NOME).setData(ROLE_NOME, par.nome)
            self._linha[par.nome] = linha
            self._status[par.nome] = STATUS["pronto"][0]
        for aviso in self._avisos:
            nome, _, motivo = aviso.partition(": ")
            self.tabela.adicionar_linha([nome, "—", "—", Etiqueta(motivo.capitalize(), STATUS["sem_par"][1])])
        self._atualizar_assunto()
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
        nomes, _ = QFileDialog.getOpenFileNames(self.contexto.janela, "Escolha os PDFs e XMLs", str(Path.home()),
                                                "PDF e XML (*.pdf *.xml)")
        if nomes:
            self.adicionar([Path(n) for n in nomes])

    def _escolher_pasta(self) -> None:
        pasta = QFileDialog.getExistingDirectory(self.contexto.janela, "Escolha a pasta com os PDFs e XMLs",
                                                 str(Path.home()))
        if pasta:
            self.adicionar([Path(pasta)])

    # --- Status por linha -------------------------------------------------
    def _set_status(self, nome: str, status: str, detalhe: str = "") -> None:
        linha = self._linha.get(nome)
        if linha is None:
            return
        texto, tom = STATUS[status]
        etiqueta = Etiqueta(texto, tom, clicavel=bool(detalhe),
                            dica="Clique para ver os detalhes" if detalhe else "")
        if detalhe:
            etiqueta.clicada.connect(lambda n=nome: self._mostrar_detalhe(n))
        self.tabela.definir_celula(linha, COL_STATUS, etiqueta)
        self._status[nome] = texto
        self._detalhe[nome] = detalhe

    def status_de(self, nome: str) -> str | None:
        return self._status.get(nome)

    def _clique_linha(self, linha: int, _coluna: int) -> None:
        item = self.tabela.item(linha, COL_NOME)
        nome = item.data(ROLE_NOME) if item else None
        if nome and self._detalhe.get(nome):
            self._mostrar_detalhe(nome)

    def _mostrar_detalhe(self, nome: str) -> None:
        Modal.informar(self.contexto.janela, f"{nome} · {self._status.get(nome, '')}", self._detalhe.get(nome, ""),
                       tom="perigo" if self._status.get(nome) == "Erro" else "aviso")

    # --- Diálogos -------------------------------------------------------
    def abrir_configuracoes(self, primeiro_acesso: bool = False, sessao_expirada: bool = False) -> bool:
        if self._conectando:
            return False
        if self.pode_tentar_de_novo():  # sem conta por falha: criar de novo em vez de abrir um diálogo morto
            self.tentar_de_novo()
            return False
        dialogo = DialogoConta(self.conta, self.cfg, self.contexto.janela, self.caminho_config, primeiro_acesso,
                               sessao_expirada, aviso_conta=self._aviso_conta)
        aceito = dialogo.exec() == DialogoConta.DialogCode.Accepted
        self.recarregar_conta()
        return aceito

    def abrir_email(self) -> None:
        if self.cfg is None or self.rodando:
            return
        DialogoEmail(self.cfg, self.contexto.janela, self.caminho_config).exec()
        self.recarregar_conta()

    # --- Envio ----------------------------------------------------------
    def _enviar(self) -> None:
        if self.rodando or not self._pares or self.cfg is None or self._assunto_pendente():
            return
        try:
            vcto = envio.validar_vcto(self.campo_vcto.text())
            self.campo_vcto_field.definir_erro(None)
        except ValueError as e:
            self.campo_vcto_field.definir_erro(str(e))
            return
        cco = list(self.cfg.cco)  # definido só em Configurações

        n = len(self._pares)
        mensagem = f"Para: {'; '.join(self.cfg.para)}" + (f"\nCco: {'; '.join(cco)}" if cco else "")
        if not Modal.confirmar(self.contexto.janela, f"Enviar {_plural(n, 'e-mail', 'e-mails')}?", mensagem,
                               texto_ok="Enviar"):
            return

        self._resultados = []
        self.progresso.setRange(0, n)
        self.progresso.setValue(0)
        self.progresso.show()
        self._set_rodando(True)

        self._thread = QThread(self)
        self._worker = EnviarWorker(list(self._pares), list(self.cfg.para), cco, vcto, self.conta,
                                    assunto=self.cfg.assunto, corpo=self.cfg.corpo)
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
        self._thread.finished.connect(self._ao_terminar_thread)
        self._thread.start()

    def _set_rodando(self, rodando: bool) -> None:
        for w in (self.btn_arquivos, self.btn_pasta, self.btn_limpar):
            w.setEnabled(not rodando)
        self.campo_vcto.setReadOnly(rodando)
        self.botao_cancelar.setVisible(rodando)
        self.botao_cancelar.setEnabled(True)
        self.botao_enviar.setVisible(not rodando)
        self._atualizar_botao()

    def _cancelar(self) -> None:
        if self.rodando and Modal.confirmar(
                self.contexto.janela, "Cancelar envio?",
                "O envio para depois do e-mail atual. Os já enviados continuam enviados.",
                texto_ok="Cancelar envio", destrutivo=True, texto_cancelar="Continuar"):
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

    def _encerrar(self) -> None:
        self._encerrando = True  # uma conta que chegue depois é ignorada (a thread de criação é daemon)
        self.parar()
        self.aguardar()

    # --- Sinais do worker -----------------------------------------------
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
        Modal.informar(self.contexto.janela, "Não foi possível enviar", mensagem, tom="perigo")

    def _ao_expirar(self, mensagem: str) -> None:
        self.progresso.hide()
        self.lbl_resumo.setText(mensagem)
        if not self._encerrando:
            QTimer.singleShot(0, self._reabrir_conta)

    def _reabrir_conta(self) -> None:
        if not self._encerrando:  # o programa pode ter começado a fechar neste meio-tempo
            self.abrir_configuracoes(sessao_expirada=True)

    def _ao_terminar_thread(self) -> None:
        if self._thread is not None:
            self._thread.wait()  # `finished` sai de dentro da thread: espera ela acabar de vez antes de soltar
            self._thread.deleteLater()
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
