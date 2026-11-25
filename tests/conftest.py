import os
import tempfile

# Antes de qualquer import do pacote: nenhum teste pode tocar %APPDATA%\EnviadorEmails nem %LOCALAPPDATA%\EnviadorEmails.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["ENVIADOR_DADOS"] = tempfile.mkdtemp(prefix="enviador_dados_")

import pytest  # noqa: E402
from PySide6 import QtCore  # noqa: E402


class _QSettingsIni(QtCore.QSettings):
    """QSettings(org, app) em arquivo .ini (pasta temporária), nunca no registro do Windows.

    No Qt 6, QSettings(org, app) ignora setDefaultFormat() e usa sempre o registro; por isso a classe é
    trocada em PySide6.QtCore antes de qualquer `from PySide6.QtCore import QSettings`.
    """

    def __init__(self, *args, **kwargs):
        if 1 <= len(args) <= 2 and not kwargs and all(isinstance(a, str) for a in args):
            super().__init__(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, *args)
        else:
            super().__init__(*args, **kwargs)


QtCore.QSettings = _QSettingsIni
from PySide6.QtCore import QSettings  # noqa: E402


@pytest.fixture(autouse=True, scope="session")
def _qsettings_fora_do_registro(tmp_path_factory):
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path_factory.mktemp("qsettings")))


@pytest.fixture(autouse=True)
def _dados_isolados(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVIADOR_DADOS", str(tmp_path / "dados"))


@pytest.fixture(scope="session", autouse=True)
def _tema_aplicado(qapp):
    """Aplica o tema do tcm-ui uma vez (sem ele os componentes saem sem QSS e sem paleta)."""
    from tcm_ui.themes import tema
    tema.aplicar(qapp)


@pytest.fixture
def contexto(qtbot, tmp_path):
    import logging
    from PySide6.QtWidgets import QWidget
    from tcm_ui.modulo import Contexto
    janela = QWidget()
    qtbot.addWidget(janela)
    return Contexto("TCMSP\teste", tmp_path / "dados", "avulso", logging.getLogger("teste"), janela)




@pytest.fixture(autouse=True)
def tentativas_de_rede(monkeypatch):
    """Nenhum teste do Enviador alcanca a rede: connect/connect_ex para fora do loopback levantam erro.

    Devolve a lista de enderecos externos tentados (para os testes conferirem que ficou vazia).
    """
    import ipaddress
    import socket

    tentativas = []
    connect, connect_ex = socket.socket.connect, socket.socket.connect_ex

    def externo(endereco):
        if not isinstance(endereco, tuple):  # AF_UNIX / pipes: nao e rede
            return False
        try:
            return not ipaddress.ip_address(endereco[0]).is_loopback
        except ValueError:  # nome de host: so "localhost" e permitido
            return endereco[0] != "localhost"

    def barrado(self, endereco):
        if externo(endereco):
            tentativas.append(endereco)
            raise OSError(f"rede bloqueada nos testes: {endereco}")
        return connect(self, endereco)

    def barrado_ex(self, endereco):
        if externo(endereco):
            tentativas.append(endereco)
            return 111  # ECONNREFUSED
        return connect_ex(self, endereco)

    monkeypatch.setattr(socket.socket, "connect", barrado)
    monkeypatch.setattr(socket.socket, "connect_ex", barrado_ex)
    return tentativas
