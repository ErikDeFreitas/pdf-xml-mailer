"""Diálogos do Enviador: "Conta e destino" (primeiro acesso e Configurações) e "Configurar e-mail"."""

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout
from tcm_ui.components import AreaTexto, Botao, Campo, CampoTexto, Cartao, Modal, Texto
from tcm_ui.microsoft_ui import CartaoContaMicrosoft
from tcm_ui.themes import ESPACO

from enviador_pdf_xml import configuracao, envio, modelo
from enviador_pdf_xml.configuracao import Configuracao

EXEMPLO_NOME = "123456"
EXEMPLO_VCTO = "31/12/2026"


def _linha(*itens) -> QHBoxLayout:
    """Layout horizontal; None vira espaço elástico."""
    caixa = QHBoxLayout()
    caixa.setSpacing(ESPACO["sm"])
    for item in itens:
        if item is None:
            caixa.addStretch(1)
        else:
            caixa.addWidget(item)
    return caixa


class DialogoConta(Modal):
    """Login Microsoft (bloco do tcm_ui) + Para (obrigatório) e Cco (opcional)."""

    def __init__(self, conta, cfg: Configuracao | None, parent=None, caminho_config: Path | None = None,
                 primeiro_acesso: bool = False, sessao_expirada: bool = False, aviso_conta: str = ""):
        super().__init__("Bem-vindo! Configure o envio" if primeiro_acesso else "Conta e destino",
                         "Entre com a sua conta Microsoft e informe para quem os e-mails vão.",
                         parent, "info")
        self._cfg = cfg
        self._caminho = caminho_config
        self.resultado: Configuracao | None = None

        self.cartao = CartaoContaMicrosoft(conta, aviso_sem_conta=aviso_conta, sessao_expirada=sessao_expirada)
        self.rotulo_conta, self.aviso = self.cartao.rotulo_conta, self.cartao.aviso
        self.botao_entrar, self.botao_sair = self.cartao.botao_entrar, self.cartao.botao_sair
        self.corpo.addWidget(self.cartao)

        # Destino
        self.campo_para = CampoTexto("destino@cliente.com.br")
        self.campo_cco = CampoTexto("opcional")
        self.campo_para_field = Campo("Para", self.campo_para, "Um ou mais e-mails separados por ;")
        self.campo_cco_field = Campo("Cco (opcional)", self.campo_cco, "Cópia oculta, usada em todos os envios.")
        self.corpo.addWidget(self.campo_para_field)
        self.corpo.addWidget(self.campo_cco_field)
        if cfg:
            self.campo_para.setText("; ".join(cfg.para))
            self.campo_cco.setText("; ".join(cfg.cco))

        self.adicionar_botao(Botao("Cancelar", "secundario")).clicked.connect(self.reject)
        self.botao_salvar = self.adicionar_botao(Botao("Salvar", "primario"))
        self.botao_salvar.setDefault(True)
        self.botao_salvar.clicked.connect(self._salvar)

        self.cartao.mudou.connect(self._atualizar)
        self._atualizar()

    # ------------------------------------------------------------------
    def _atualizar(self) -> None:
        self.botao_salvar.setEnabled(bool(self.cartao.email()))
        self._reajustar()

    def _reajustar(self) -> None:
        if self.isVisible():  # antes de exibir, o showEvent já calcula a altura
            self.reajustar_altura()

    def _salvar(self) -> None:
        if not self.cartao.email():
            return
        ok = True
        try:
            para = envio.validar_emails(self.campo_para.text(), True)
            self.campo_para_field.definir_erro(None)
        except ValueError as e:
            self.campo_para_field.definir_erro(str(e))
            ok = False
        try:
            cco = envio.validar_emails(self.campo_cco.text(), False)
            self.campo_cco_field.definir_erro(None)
        except ValueError as e:
            self.campo_cco_field.definir_erro(str(e))
            ok = False
        if not ok:
            self._reajustar()
            return
        # Mantém o assunto e o corpo de "Configurar e-mail".
        self.resultado = (replace(self._cfg, para=para, cco=cco) if self._cfg
                          else Configuracao(para=para, cco=cco))
        configuracao.salvar(self.resultado, self._caminho)
        self.accept()

    def done(self, r: int) -> None:
        self.cartao.abandonar_login()  # X, Cancelar ou Esc fecham mesmo com o login aberto no navegador
        super().done(r)


class DialogoEmail(Modal):
    """Assunto e corpo do e-mail, salvos no config.json para os próximos envios."""

    def __init__(self, cfg: Configuracao, parent=None, caminho_config: Path | None = None):
        super().__init__("Configurar e-mail",
                         "Vale para todos os próximos envios. Use {nome} para o nome do arquivo e "
                         "{vcto} para o vencimento. No corpo, **texto** sai em negrito.",
                         parent, "info")
        self._cfg = cfg
        self._caminho = caminho_config
        self.resultado: Configuracao | None = None

        self.campo_assunto = CampoTexto("Ex.: TCM - CTE {nome}")
        self.campo_corpo = AreaTexto("Texto do e-mail")
        self.campo_corpo.setMinimumHeight(160)
        self.campo_assunto_field = Campo("Assunto", self.campo_assunto, "{nome} = nome do par (PDF + XML).")
        self.campo_corpo_field = Campo("Corpo", self.campo_corpo,
                                       "{vcto} = vencimento. Linha em branco separa parágrafos.")
        self.corpo.addWidget(self.campo_assunto_field)
        self.corpo.addWidget(self.campo_corpo_field)

        # Prévia com um par de exemplo, já com o negrito aplicado.
        self.previa_assunto = Texto("")
        self.previa_assunto.setWordWrap(True)
        self.previa_corpo = Texto("", "suave")
        self.previa_corpo.setWordWrap(True)
        self.previa_corpo.setTextFormat(Qt.TextFormat.RichText)
        previa = Cartao()
        previa.corpo.addWidget(Texto(f"Prévia (exemplo: {EXEMPLO_NOME}, vencimento {EXEMPLO_VCTO})", "rotulo"))
        previa.corpo.addWidget(self.previa_assunto)
        previa.corpo.addWidget(self.previa_corpo)
        self.corpo.addWidget(previa)

        self.botao_restaurar = Botao("Restaurar padrão", "fantasma", "sm")
        self.botao_restaurar.clicked.connect(self.restaurar_padrao)
        self._botoes.insertWidget(0, self.botao_restaurar)  # à esquerda do rodapé, antes do espaço elástico
        self.adicionar_botao(Botao("Cancelar", "secundario")).clicked.connect(self.reject)
        self.botao_salvar = self.adicionar_botao(Botao("Salvar", "primario"))
        self.botao_salvar.setDefault(True)
        self.botao_salvar.clicked.connect(self._salvar)

        self.campo_assunto.textChanged.connect(self._atualizar_previa)
        self.campo_corpo.textChanged.connect(self._atualizar_previa)
        self.campo_assunto.setText(cfg.assunto)
        self.campo_corpo.setPlainText(cfg.corpo)
        self._atualizar_previa()

    def restaurar_padrao(self) -> None:
        """Volta os campos ao texto padrão do programa (só grava no Salvar)."""
        self.campo_assunto.setText(modelo.ASSUNTO)
        self.campo_corpo.setPlainText(modelo.CORPO)

    def _atualizar_previa(self, *_) -> None:
        assunto = self.campo_assunto.text().strip()
        corpo = self.campo_corpo.toPlainText().strip()
        self.previa_assunto.setText(
            envio.montar_assunto(EXEMPLO_NOME, EXEMPLO_VCTO, assunto) if assunto else "(sem assunto)")
        html = envio.montar_corpo(EXEMPLO_VCTO, EXEMPLO_NOME, corpo)[1] if corpo else ""
        # QLabel calcula mal a altura de vários <p> com quebra de linha: na prévia, parágrafo vira <br><br>.
        html = html.replace("</p>\n<p>", "<br><br>").removeprefix("<p>").removesuffix("</p>")
        self.previa_corpo.setText(html)
        if self.isVisible():  # a prévia muda de altura enquanto a pessoa digita
            self.reajustar_altura()

    def _salvar(self) -> None:
        ok = True
        try:
            assunto = envio.validar_modelo(self.campo_assunto.text(), "assunto")
            if envio.assunto_de_exemplo(assunto):
                raise ValueError('Troque o "TEXTO FIXO" pelo assunto real.')
            self.campo_assunto_field.definir_erro(None)
        except ValueError as e:
            self.campo_assunto_field.definir_erro(str(e))
            ok = False
        try:
            corpo = envio.validar_modelo(self.campo_corpo.toPlainText(), "corpo")
            self.campo_corpo_field.definir_erro(None)
        except ValueError as e:
            self.campo_corpo_field.definir_erro(str(e))
            ok = False
        if not ok:
            if self.isVisible():
                self.reajustar_altura()
            return
        self.resultado = replace(self._cfg, assunto=assunto, corpo=corpo)
        configuracao.salvar(self.resultado, self._caminho)
        self.accept()
