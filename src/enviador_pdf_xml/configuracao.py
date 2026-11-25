r"""Configuração de cada pessoa em %APPDATA%\EnviadorEmails\config.json (fora do programa).

Para e Cco (obrigatório / opcional) e o texto do e-mail (assunto e corpo). Assunto e corpo
começam com o padrão de enviador_pdf_xml/modelo.py e mudam em "Configurar e-mail".
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from enviador_pdf_xml import envio, modelo
from enviador_pdf_xml.dados import pasta_config


@dataclass
class Configuracao:
    para: list[str]
    cco: list[str] = field(default_factory=list)
    assunto: str = modelo.ASSUNTO
    corpo: str = modelo.CORPO


def caminho_padrao() -> Path:
    return pasta_config() / "config.json"


def _modelo_ou_padrao(valor, padrao: str, rotulo: str) -> str:
    """Texto salvo, se ainda for válido; senão o padrão (nunca quebra um envio)."""
    try:
        return envio.validar_modelo(valor, rotulo) if isinstance(valor, str) else padrao
    except ValueError:
        return padrao


def carregar(caminho: Path | None = None) -> Configuracao | None:
    """None se não houver configuração válida (vira 'primeiro acesso')."""
    caminho = Path(caminho or caminho_padrao())
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        para = envio.validar_emails("; ".join(dados.get("para") or []), True)
    except (OSError, ValueError, TypeError, AttributeError):
        return None
    try:
        cco = envio.validar_emails("; ".join(dados.get("cco") or []), False)
    except (ValueError, TypeError):
        cco = []
    return Configuracao(para=para, cco=cco,
                        assunto=_modelo_ou_padrao(dados.get("assunto"), modelo.ASSUNTO, "assunto"),
                        corpo=_modelo_ou_padrao(dados.get("corpo"), modelo.CORPO, "corpo"))


def salvar(cfg: Configuracao, caminho: Path | None = None) -> None:
    """Gravação atômica: escreve num .tmp e troca, para nunca deixar o arquivo pela metade."""
    caminho = Path(caminho or caminho_padrao())
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, caminho)
