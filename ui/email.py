"""Modal "Configurar e-mail": assunto e corpo, salvos no config.json para os próximos envios."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt

from core import configuracao, envio, modelo
from core.configuracao import Configuracao
from ui import components as c

EXEMPLO_NOME = "123456"
EXEMPLO_VCTO = "31/12/2026"
# Modal (480) menos as margens do modal (2 x 32) e o padding do card (2 x 20).
LARGURA_PREVIA = c.SIZE["modal"] - 2 * c.SPACE["xl"] - 2 * 20


class EmailModal(c.Modal):
    def __init__(self, cfg: Configuracao, parent=None, caminho_config: Path | None = None):
        super().__init__("Configurar e-mail",
                         "Vale para todos os próximos envios. Use {nome} para o nome do arquivo e "
                         "{vcto} para o vencimento. No corpo, **texto** sai em negrito.",
                         "mail", "primary", parent)
        self._cfg = cfg
        self._caminho = caminho_config
        self.resultado: Configuracao | None = None

        self.campo_assunto = c.Input("Ex.: TCM - CTE {nome}")
        self.campo_corpo = c.TextArea("Texto do e-mail")
        self.campo_corpo.setMinimumHeight(160)
        self.campo_assunto_field = c.FormField("Assunto", self.campo_assunto, "{nome} = nome do par (PDF + XML).")
        self.campo_corpo_field = c.FormField("Corpo", self.campo_corpo,
                                             "{vcto} = vencimento. Linha em branco separa parágrafos.")
        self.body.addWidget(self.campo_assunto_field)
        self.body.addWidget(self.campo_corpo_field)

        # Prévia com um par de exemplo, já com o negrito aplicado.
        self.previa_assunto = c.Label("", "body", wrap=True)
        self.previa_corpo = c.Label("", "muted", wrap=True)
        self.previa_corpo.setTextFormat(Qt.TextFormat.RichText)
        previa = c.Card()
        previa.add(c.Label(f"Prévia (exemplo: {EXEMPLO_NOME}, vencimento {EXEMPLO_VCTO})", "label"),
                   self.previa_assunto, self.previa_corpo)
        self.body.addWidget(previa)

        self.botao_restaurar = c.Button("Restaurar padrão", "ghost", "sm")
        self.botao_restaurar.clicked.connect(self.restaurar_padrao)
        self.footer.insertWidget(0, self.botao_restaurar)
        self.add_button("Cancelar", "secondary")
        self.botao_salvar = c.Button("Salvar", "primary")
        self.botao_salvar.setDefault(True)
        self.botao_salvar.clicked.connect(self._salvar)
        self.footer.addWidget(self.botao_salvar)

        self.campo_assunto.textChanged.connect(self._atualizar_previa)
        self.campo_corpo.textChanged.connect(self._atualizar_previa)
        self.campo_assunto.setText(cfg.assunto)
        self.campo_corpo.setPlainText(cfg.corpo)
        self._atualizar_previa()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._atualizar_previa()  # a fonte do QSS só vale depois de exibido: recalcula a altura

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
        # Com quebra automática o QLabel subestima a altura; reserva a altura real para a largura do modal.
        largura = max(self.previa_corpo.width(), LARGURA_PREVIA)
        self.previa_corpo.setMinimumHeight(self.previa_corpo.heightForWidth(largura))
        # O QDialog de largura fixa não cresce sozinho com textos que quebram linha: pede a altura certa.
        self.setMinimumHeight(self.layout().totalHeightForWidth(c.SIZE["modal"]))
        self.adjustSize()

    def _salvar(self) -> None:
        ok = True
        try:
            assunto = envio.validar_modelo(self.campo_assunto.text(), "assunto")
            if envio.assunto_de_exemplo(assunto):
                raise ValueError('Troque o "TEXTO FIXO" pelo assunto real.')
            self.campo_assunto_field.set_error(None)
        except ValueError as e:
            self.campo_assunto_field.set_error(str(e))
            ok = False
        try:
            corpo = envio.validar_modelo(self.campo_corpo.toPlainText(), "corpo")
            self.campo_corpo_field.set_error(None)
        except ValueError as e:
            self.campo_corpo_field.set_error(str(e))
            ok = False
        if not ok:
            return
        self.resultado = replace(self._cfg, assunto=assunto, corpo=corpo)
        configuracao.salvar(self.resultado, self._caminho)
        self.accept()
