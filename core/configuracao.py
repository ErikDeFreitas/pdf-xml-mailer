"""Para e Cco de cada pessoa, em %APPDATA%\\EnviadorEmails\\config.json (fora do programa)."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from core import envio
from core.modelo import APLICACAO


@dataclass
class Configuracao:
    para: list[str]
    cco: list[str] = field(default_factory=list)


def caminho_padrao() -> Path:
    base = os.environ.get("APPDATA")
    raiz = Path(base) if base else Path.home() / "AppData" / "Roaming"
    return raiz / APLICACAO / "config.json"


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
    return Configuracao(para=para, cco=cco)


def salvar(cfg: Configuracao, caminho: Path | None = None) -> None:
    """Gravação atômica: escreve num .tmp e troca, para nunca deixar o arquivo pela metade."""
    caminho = Path(caminho or caminho_padrao())
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, caminho)
