# Enviador de PDF + XML (app desktop) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trocar a interface Flask por um `.exe` PySide6 no padrão do mesclador, com login Microsoft (OAuth 2.0 / XOAUTH2), Para/Cco configurados no primeiro acesso e atualização automática pelo GitHub Releases.

**Architecture:** `core/` guarda as regras sem nenhum import de interface (pares, mensagem, SMTP, conta MSAL, configuração local, CLI). `ui/` é copiado do mesclador (tokens, QSS, componentes, ícones, modal de atualização). `main.py` monta a janela, e o trabalho pesado (login, envio) roda em `QThread` via `core/worker.py`.

**Tech Stack:** Python 3.13, PySide6-Essentials 6.12.0, msal, msal-extensions, PyInstaller 6.22.3, pytest.

**Spec:** `docs/superpowers/specs/2026-11-18-app-desktop-design.md`

**Referência:** projeto mesclador em `C:\Users\erik.freitas\OneDrive - TCM - LOGISTICA, TRANSPORTES & ARMAZENS GERAIS LTDA\Área de Trabalho\mesclador` (leia o `CLAUDE.md` dele; copie arquivos de lá quando a tarefa mandar).

## Global Constraints

- Responder e escrever textos de interface em **português**.
- **Somente PySide6 + QSS.** Nada de estilo inline nem cor literal no código; aparência via propriedades dinâmicas e tokens de `ui/themes.py` (regras do Design System no `CLAUDE.md` do mesclador valem aqui).
- `core/` **nunca** importa `PySide6.QtWidgets`/`ui` (exceto `core/worker.py`, que usa só `QtCore`).
- Nome do app: `APLICACAO = "EnviadorEmails"`, `ORGANIZACAO = "TCM"`, executável `EnviadorEmails.exe` + `EnviadorEmails.exe.sha256`, repositório `ErikDeFreitas/pdf-xml-mailer`.
- SMTP `smtp.office365.com:587`, STARTTLS com `ssl.create_default_context()`, timeout 30 s, `AUTH XOAUTH2`, intervalo de 2 s entre e-mails, uma conexão por lote.
- MSAL como aplicativo público; escopo `["https://outlook.office.com/SMTP.Send"]` (não passar `offline_access`: o MSAL já inclui e recusa escopos reservados). Cache de tokens com `msal-extensions` (DPAPI) em `%LOCALAPPDATA%\EnviadorEmails\token_cache.bin`.
- Configuração do usuário em `%APPDATA%\EnviadorEmails\config.json` com `{"para": [...], "cco": [...]}`. Nada de senha ou token em texto puro, log ou tela.
- Vencimento `dd/mm/aaaa`, data real, obrigatório. `{nome}` no assunto, `{vcto}` no corpo (escapado no HTML).
- Testes e arquivos temporários de teste em `tmp_path`/`%TEMP%`, nunca na pasta do projeto. Nunca usar PDFs/XMLs reais em testes.
- Trabalhar no branch `feat/app-desktop`. Nunca force push.

## Review Focus

1. Extensões em maiúsculas (`123.PDF`, `123.Xml`) e nomes que diferem só por maiúsculas/minúsculas formam par (Windows não diferencia) → Task 2 `test_achar_pares_ignora_maiusculas`.
2. Já existe arquivo com o mesmo nome em `enviados/` → o novo vira `nome_2.pdf`, nunca sobrescreve → Task 2 `test_destino_livre_nao_sobrescreve`.
3. O e-mail saiu, mas o arquivo não pôde ser movido (aberto no leitor de PDF, OneDrive bloqueando) → o par aparece como **enviado com aviso** ("não foi movido para enviados/"), nunca como erro → Task 4 `test_lote_envio_ok_mas_arquivo_preso`.
4. Conexão SMTP cai no meio do lote → reconecta uma vez e repete aquele par; se falhar de novo, os pares restantes ficam como erro **sem** serem movidos → Task 4 `test_lote_reconecta_uma_vez`.
5. Para/Cco digitados com `,`, `;` no fim ou espaços → aceitos; e-mail inválido → mensagem que diz qual → Task 2 `test_validar_emails_*`.

---

### Task 1: Esqueleto no padrão do mesclador

**Files:**
- Create: `ui/__init__.py`, `ui/themes.py`, `ui/styles.qss`, `ui/components.py`, `ui/icons.py`, `ui/atualizacao.py` (copiados do mesclador)
- Create: `core/__init__.py`, `core/atualizacao.py` (copiado), `core/modelo.py`, `version.py`, `requirements.txt` (substitui o atual), `pytest.ini`
- Test: `tests/test_esqueleto.py`

**Interfaces:**
- Produces: `core.modelo` com `APLICACAO`, `ORGANIZACAO`, `ASSUNTO`, `CORPO_TEXTO`, `CORPO_HTML`, `SMTP_HOST`, `SMTP_PORTA`, `TIMEOUT`, `INTERVALO_SEGUNDOS`, `CLIENT_ID`, `TENANT_ID`, `ESCOPOS`; `version.__version__`; `ui.*` igual ao mesclador.

- [ ] **Step 1: Criar o branch** `git switch -c feat/app-desktop`.
- [ ] **Step 2: Copiar `ui/` e `core/atualizacao.py` do mesclador.** Ajustes: `ui/themes.py` → `APLICACAO = "EnviadorEmails"`; `core/atualizacao.py` → `REPOSITORIO = "ErikDeFreitas/pdf-xml-mailer"`, `NOME_EXE = "EnviadorEmails.exe"`, User-Agent `EnviadorEmails/{versao}`. Em `ui/atualizacao.py` e `ui/components.py`, trocar textos que citem "mesclagem"/"Mesclador" por equivalentes neutros ("envio"). `ui/themes.py` deve importar `APLICACAO`/`ORGANIZACAO` de `core.modelo` (fonte única).
- [ ] **Step 3: Criar `core/modelo.py`.** Valores:
  - `ASSUNTO = "EMPRESA - CTE {nome} - TEXTO FIXO DO ASSUNTO"` (texto real será fornecido pelo Erik antes da 1ª release; deixe comentário `# TODO(Erik): texto real do assunto`).
  - `CORPO_TEXTO` = conteúdo atual de `corpo.txt`; `CORPO_HTML` = conteúdo atual de `corpo.html` (literalmente).
  - `SMTP_HOST = "smtp.office365.com"`, `SMTP_PORTA = 587`, `TIMEOUT = 30`, `INTERVALO_SEGUNDOS = 2.0`.
  - `CLIENT_ID = ""`, `TENANT_ID = ""` (com comentário: preencher com o registro do Entra ID), `ESCOPOS = ["https://outlook.office.com/SMTP.Send"]`.
- [ ] **Step 4: `version.py`** = `__version__ = "1.0.0"` com o mesmo comentário do mesclador.
- [ ] **Step 5: `requirements.txt`**: `PySide6-Essentials==6.12.0`, `msal==<última>`, `msal-extensions==<última>`, `pyinstaller==6.22.3`, `pytest==<última>`; descubra as versões com `python -m pip index versions <pacote>` e fixe com `==`. Instale num `.venv` fora do OneDrive não é necessário; `python -m pip install -r requirements.txt`.
- [ ] **Step 6: `pytest.ini`** com `testpaths = tests` e `env`-free; `tests/conftest.py` define `os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")`.
- [ ] **Step 7: Escrever `tests/test_esqueleto.py`:**

```python
def test_atualizacao_aponta_para_este_repo():
    from core import atualizacao
    assert atualizacao.REPOSITORIO == "ErikDeFreitas/pdf-xml-mailer"
    assert atualizacao.NOME_EXE == "EnviadorEmails.exe"
    assert atualizacao.NOME_SHA == "EnviadorEmails.exe.sha256"

def test_modelo_tem_variaveis():
    from core import modelo
    assert "{nome}" in modelo.ASSUNTO
    assert "{vcto}" in modelo.CORPO_TEXTO and "{vcto}" in modelo.CORPO_HTML

def test_tema_carrega():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from ui.themes import theme_manager, APLICACAO
    assert APLICACAO == "EnviadorEmails"
    assert theme_manager.stylesheet()
```

- [ ] **Step 8: Rodar** `python -m pytest tests/test_esqueleto.py -v` → 3 passed.
- [ ] **Step 9: Commit** `feat: esqueleto PySide6 no padrão do mesclador`.

---

### Task 2: Regras puras de envio

**Files:**
- Create: `core/envio.py`
- Test: `tests/test_envio.py`

**Interfaces:**
- Consumes: `core.modelo`.
- Produces (em `core/envio.py`):
  - `@dataclass(frozen=True) class Par: nome: str; pdf: Path; xml: Path`
  - `arquivos_da_pasta(pasta: Path) -> list[Path]` — só arquivos, não recursivo, ignora `enviados/`/`erros/`.
  - `achar_pares(arquivos: Iterable[Path]) -> tuple[list[Par], list[str]]` — chave = `stem.casefold()`; extensões `.pdf`/`.xml` sem diferenciar maiúsculas; `Par.nome` = stem do PDF; pares ordenados por nome; segunda lista = mensagens de aviso legíveis: `"123815.pdf: sem XML"`, `"123816.xml: sem PDF"`, `"123817: mais de um PDF com o mesmo nome"`. Outros tipos de arquivo são ignorados em silêncio.
  - `pdf_valido(dados: bytes) -> bool` (`b"%PDF-"` no 1º KB); `xml_valido(dados: bytes) -> bool` (começa com `<` após remover BOM UTF-8 e espaços).
  - `validar_vcto(texto: str) -> str` — `ValueError("Vencimento inválido. Use o formato dd/mm/aaaa.")`.
  - `validar_emails(texto: str, obrigatorio: bool) -> list[str]` — separa por `;` ou `,`, remove vazios/espaços; formato mínimo `algo@dominio.tld` sem espaço; `ValueError` cita o endereço inválido; vazio + obrigatório → `ValueError("Informe pelo menos um e-mail.")`.
  - `montar_assunto(nome: str) -> str`; `montar_corpo(vcto: str) -> tuple[str, str]` (texto, html; vcto escapado no HTML).
  - `montar_mensagem(par: Par, remetente: str, para: list[str], cco: list[str], vcto: str, pdf: bytes, xml: bytes) -> EmailMessage` — `From`, `To` (`", "`), `Bcc` só se houver cco, `Subject`, texto + alternativa HTML, anexos `application/pdf` e `application/xml` com os nomes originais.
  - `destino_livre(pasta: Path, nome_arquivo: str) -> Path` — se existe, `stem_2.ext`, `stem_3.ext`…
  - `mover_par(par: Par, sucesso: bool) -> None` — move PDF e XML para `par.pdf.parent / ("enviados" if sucesso else "erros")` (cria a pasta) usando `destino_livre`; o XML vai para a pasta do próprio XML.

- [ ] **Step 1: Escrever os testes** (crie arquivos falsos em `tmp_path`, ex.: `b"%PDF-1.4\n..."` e `b"<?xml version='1.0'?><a/>"`):
  - `test_achar_pares_basico`: `1.pdf,1.xml,2.pdf,3.xml,notas.txt` → pares `["1"]`, avisos `["2.pdf: sem XML", "3.xml: sem PDF"]`.
  - `test_achar_pares_ignora_maiusculas`: `123.PDF` + `123.Xml` → 1 par com nome `"123"`.
  - `test_achar_pares_duplicado`: `a/5.pdf`, `b/5.pdf`, `a/5.xml` → 0 pares, aviso `"5: mais de um PDF com o mesmo nome"`.
  - `test_pdf_xml_validos`: `pdf_valido(b"lixo")` False; `xml_valido(b"\xef\xbb\xbf  <x/>")` True; `xml_valido(b"oi")` False.
  - `test_validar_vcto`: `"20/11/2026"` ok; `"31/02/2026"` e `"2026-11-20"` → `ValueError`.
  - `test_validar_emails_separadores`: `" a@b.com, c@d.com.br; "` → `["a@b.com", "c@d.com.br"]`.
  - `test_validar_emails_invalido`: `"a@b.com; nada"` → `ValueError` com `"nada"` na mensagem; `""` com `obrigatorio=True` → `ValueError`; com `False` → `[]`.
  - `test_assunto_e_corpo`: `montar_assunto("12\n3")` == `modelo.ASSUNTO.replace("{nome}", "12 3")`; `montar_corpo("20/11/2026")` contém a data nas duas partes e nenhum `{vcto}`.
  - `test_montar_mensagem`: `To` == `"a@b.com"`, `Bcc` == `"x@y.com"`, 2 anexos com os nomes certos; sem cco → `msg["Bcc"] is None`.
  - `test_destino_livre_nao_sobrescreve`: com `enviados/1.pdf` existente → retorna `enviados/1_2.pdf`; com `1_2.pdf` também → `1_3.pdf`.
  - `test_mover_par`: sucesso → arquivos em `enviados/`; falha → em `erros/`; originais não existem mais.
- [ ] **Step 2: Rodar** `python -m pytest tests/test_envio.py -v` → falha (módulo inexistente).
- [ ] **Step 3: Implementar `core/envio.py`** com as assinaturas acima.
- [ ] **Step 4: Rodar** de novo → todos passam.
- [ ] **Step 5: Commit** `feat: regras de pares, mensagem e movimentação`.

---

### Task 3: Configuração local (Para/Cco)

**Files:**
- Create: `core/configuracao.py`
- Test: `tests/test_configuracao.py`

**Interfaces:**
- Produces:
  - `@dataclass class Configuracao: para: list[str]; cco: list[str] = field(default_factory=list)`
  - `caminho_padrao() -> Path` — `Path(os.environ["APPDATA"]) / "EnviadorEmails" / "config.json"` (fallback `Path.home() / "AppData/Roaming"` se a variável faltar).
  - `carregar(caminho: Path | None = None) -> Configuracao | None` — `None` se o arquivo não existe, é JSON inválido, ou `para` vazio/inválido (usa `envio.validar_emails`).
  - `salvar(cfg: Configuracao, caminho: Path | None = None) -> None` — cria a pasta, grava UTF-8 em `*.tmp` e faz `os.replace` (gravação atômica).

- [ ] **Step 1: Testes:** `test_ida_e_volta` (salvar → carregar devolve igual); `test_sem_arquivo_retorna_none`; `test_json_quebrado_retorna_none` (arquivo com `"{"`); `test_para_vazio_retorna_none`; `test_caminho_padrao_usa_appdata` (monkeypatch `APPDATA` = `tmp_path`).
- [ ] **Step 2: Rodar** → falha.
- [ ] **Step 3: Implementar.**
- [ ] **Step 4: Rodar** → passa.
- [ ] **Step 5: Commit** `feat: configuração local de Para e Cco`.

---

### Task 4: Conta Microsoft (MSAL), conexão XOAUTH2 e envio do lote

**Files:**
- Create: `core/conta.py`
- Modify: `core/envio.py` (acrescenta conexão e lote)
- Test: `tests/test_conta.py`, `tests/test_lote.py`

**Interfaces:**
- Consumes: Task 2 (`Par`, `montar_mensagem`, `mover_par`, `pdf_valido`, `xml_valido`, `validar_vcto`), `core.modelo`.
- Produces:
  - `core/conta.py`:
    - `class ContaNaoConfigurada(Exception)` — `CLIENT_ID`/`TENANT_ID` vazios; mensagem: `"O login Microsoft ainda não foi configurado nesta versão (CLIENT_ID/TENANT_ID)."`
    - `class FalhaLogin(Exception)` — mensagem pronta para o usuário.
    - `class Conta:`
      - `__init__(self, app=None)` — sem `app`, cria `msal.PublicClientApplication(CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT_ID}", token_cache=PersistedTokenCache(build_encrypted_persistence(str(caminho_cache()))))` (levanta `ContaNaoConfigurada` se vazio). `app` injetável para teste.
      - `email() -> str | None` — `username` da primeira conta em `app.get_accounts()`.
      - `entrar() -> str` — `acquire_token_interactive(ESCOPOS, prompt="select_account")`; sem `access_token` → `FalhaLogin(result.get("error_description") ou "Login cancelado.")`; retorna o e-mail.
      - `token() -> str` — `acquire_token_silent(ESCOPOS, account=conta)`; sem conta ou sem token → `FalhaLogin("Sua sessão expirou. Entre novamente com a Microsoft.")`.
      - `sair() -> None` — `remove_account` para todas.
    - `caminho_cache() -> Path` — `%LOCALAPPDATA%\EnviadorEmails\token_cache.bin`.
  - `core/envio.py` (acréscimos):
    - `xoauth2(email: str, token: str) -> str` — `f"user={email}\x01auth=Bearer {token}\x01\x01"`.
    - `abrir_smtp(email: str, token: str, fabrica=smtplib.SMTP) -> smtplib.SMTP` — `fabrica(SMTP_HOST, SMTP_PORTA, timeout=TIMEOUT)`, `ehlo`, `starttls(context=ssl.create_default_context())`, `ehlo`, `auth("XOAUTH2", lambda _=None: xoauth2(email, token), initial_response_ok=True)`.
    - `@dataclass class ResultadoPar: nome: str; status: str; detalhe: str = ""` — `status` ∈ `{"enviado", "aviso", "erro"}`.
    - `class FalhaConexao(Exception)`.
    - `enviar_lote(pares: list[Par], remetente: str, para: list[str], cco: list[str], vcto: str, conectar: Callable[[], smtplib.SMTP], intervalo: float = INTERVALO_SEGUNDOS, ao_iniciar: Callable[[int, int, str], None] | None = None, ao_concluir: Callable[[ResultadoPar], None] | None = None, cancelado: Callable[[], bool] = lambda: False, dormir: Callable[[float], None] = time.sleep) -> list[ResultadoPar]`.

**Regras de `enviar_lote`:**
- `validar_vcto` antes de conectar. Falha no `conectar()` inicial → `FalhaConexao(str(e))`, nenhum arquivo movido.
- Por par: lê bytes; conteúdo inválido → `ResultadoPar(nome, "erro", "<arquivo> não parece ser um PDF/XML válido")` e `mover_par(par, False)`.
- `send_message` ok → `mover_par(par, True)`; se o mover der `OSError` → `status="aviso"`, `detalhe="Enviado, mas não foi movido para enviados/: <erro>"`.
- `SMTPServerDisconnected`/`ConnectionError` no envio → `conectar()` de novo e repete o par **uma** vez; se falhar de novo, este par e todos os restantes viram `"erro"` com detalhe `"Conexão perdida com o servidor"` e **não** são movidos; para o lote.
- Outra exceção no envio → `"erro"` com a mensagem, `mover_par(par, False)`, segue.
- `cancelado()` checado antes de cada par: para sem tocar nos restantes (eles não entram no resultado).
- `dormir(intervalo)` entre pares (não depois do último). Fecha a conexão com `quit()` no `finally` (ignorando erro).

- [ ] **Step 1: Testes de conta** (`tests/test_conta.py`) com um `FakeApp` (métodos `get_accounts`, `acquire_token_interactive`, `acquire_token_silent`, `remove_account`):
  - `test_entrar_retorna_email`; `test_entrar_cancelado_levanta_falha_login`; `test_token_sem_conta_levanta`; `test_token_ok`; `test_sair_remove_contas`; `test_sem_client_id_levanta_conta_nao_configurada` (monkeypatch `modelo.CLIENT_ID = ""`, `Conta()` sem app).
- [ ] **Step 2: Testes de lote** (`tests/test_lote.py`) com `FakeSMTP` (registra mensagens; pode ser programado para levantar `SMTPServerDisconnected` N vezes ou para um nome):
  - `test_xoauth2_formato` == `"user=a@b.com\x01auth=Bearer T\x01\x01"`.
  - `test_abrir_smtp_usa_xoauth2`: fábrica falsa registra `starttls` chamado e `auth("XOAUTH2", ...)`.
  - `test_lote_tudo_ok`: 2 pares → 2 `"enviado"`, arquivos em `enviados/`, `dormir` chamado 1 vez com `2.0`.
  - `test_lote_pdf_invalido_vai_para_erros`.
  - `test_lote_envio_ok_mas_arquivo_preso`: monkeypatch `envio.mover_par` para levantar `PermissionError` no sucesso → `status == "aviso"` e `"não foi movido"` no detalhe.
  - `test_lote_reconecta_uma_vez`: 1ª tentativa do 1º par levanta disconnect → reconecta, os 2 saem `"enviado"`, `conectar` chamado 2 vezes.
  - `test_lote_conexao_perdida_de_vez`: disconnect sempre → todos `"erro"`, nenhum movido.
  - `test_lote_cancelado`: `cancelado` vira True após o 1º → só 1 resultado; 2º par continua na pasta.
  - `test_lote_falha_ao_conectar`: `conectar` levanta → `FalhaConexao`, arquivos intactos.
  - `test_lote_vcto_invalido_nao_conecta`.
- [ ] **Step 3: Rodar** `python -m pytest tests/test_conta.py tests/test_lote.py -v` → falham.
- [ ] **Step 4: Implementar** `core/conta.py` e os acréscimos em `core/envio.py`.
- [ ] **Step 5: Rodar** toda a suíte → passa.
- [ ] **Step 6: Commit** `feat: login Microsoft (MSAL) e envio do lote via XOAUTH2`.

---

### Task 5: Workers e modo terminal

**Files:**
- Create: `core/worker.py`, `core/cli.py`, `core/__main__.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: Tasks 2–4, `core.atualizacao`.
- Produces:
  - `core/worker.py` (só `QtCore`):
    - `LoginWorker(QObject)`: `__init__(conta: Conta)`; sinais `concluido = Signal(str)` (e-mail), `falhou = Signal(str)`; `run()` chama `conta.entrar()`.
    - `EnviarWorker(QObject)`: `__init__(pares, para, cco, vcto, conta: Conta)`; sinais `iniciou_par = Signal(int, int, str)`, `par_concluido = Signal(object)`, `concluido = Signal(object)` (lista de `ResultadoPar`), `falhou = Signal(str)`; `cancelar()`; `run()` obtém `conta.email()` e `conta.token()` e chama `envio.enviar_lote(..., conectar=lambda: envio.abrir_smtp(email, conta.token()))`. `FalhaLogin`/`FalhaConexao` → `falhou` com a mensagem; outro erro → `"Erro inesperado: <tipo>: <msg>"`.
    - `BaixarAtualizacaoWorker`: copiado do mesclador sem mudança.
  - `core/cli.py`: `main(argv: list[str], conta_factory=Conta) -> int`. Argumentos: `pasta`, `--vcto` (obrigatório), `--cco` (opcional; sem ele usa o Cco salvo), `--dry-run`. Lê `configuracao.carregar()`; sem configuração → imprime `"Configure Para/Cco abrindo o programa uma vez."` e retorna 2. Lista avisos de `achar_pares`. `--dry-run` imprime `"[dry-run] Para: ... | Assunto: ..."` por par e retorna 0 **sem** criar `Conta`. Envio real: imprime `OK`/`AVISO`/`ERRO` por par e o resumo `"Concluído: N enviado(s), M com aviso, K com erro."`; retorna 1 se houver erro.
  - `core/__main__.py`: `sys.exit(cli.main(sys.argv[1:]))`.

- [ ] **Step 1: Testes** (`tests/test_cli.py`; monkeypatch `APPDATA` para `tmp_path`):
  - `test_cli_sem_configuracao_retorna_2`.
  - `test_cli_dry_run_lista_assuntos` (capsys contém o assunto do par e não cria conta: `conta_factory` que levanta se chamada).
  - `test_cli_vcto_invalido_retorna_2`.
  - `test_cli_envia_com_conta_falsa`: `conta_factory` devolve um objeto com `email()`/`token()`, e monkeypatch `envio.abrir_smtp` para um `FakeSMTP` → retorna 0 e os arquivos vão para `enviados/`.
- [ ] **Step 2: Rodar** → falha. **Step 3: Implementar.** **Step 4: Rodar** → passa.
- [ ] **Step 5: Commit** `feat: workers e modo terminal`.

---

### Task 6: Modal "Conta e destino" (primeiro acesso e Configurações)

**Files:**
- Create: `ui/conta.py`
- Test: `tests/test_ui_conta.py`

**Interfaces:**
- Consumes: `c.Modal`, `c.Input`, `c.FormField`, `c.Button`, `c.Label` (assinaturas do mesclador), `LoginWorker`, `Configuracao`, `configuracao.salvar`, `envio.validar_emails`.
- Produces: `class ContaModal(c.Modal)`: `__init__(self, conta: Conta, cfg: Configuracao | None, parent=None)`; após `exec()` aceito, `self.resultado: Configuracao` e a conta está logada. Botão "Sair da conta" chama `conta.sair()` e volta ao estado "não logado".

**Comportamento:**
- Título: `"Conta e destino"` (primeiro acesso: `"Bem-vindo! Configure o envio"`).
- Seção 1: se `conta.email()` é `None` → botão primário **"Entrar com a Microsoft"** (roda `LoginWorker` numa `QThread`, botão em estado "Aguardando login no navegador…"); logado → `Label` com o e-mail + link-botão "Sair da conta".
- Seção 2: `FormField("Para", Input)` (hint "Um ou mais e-mails separados por ;"), `FormField("Cco (opcional)", Input)`, preenchidos com `cfg`.
- "Salvar" só habilitado logado; valida com `validar_emails` (erro aparece no campo via `set_prop(campo, "error", True)` + hint com a mensagem); grava com `configuracao.salvar` e aceita.
- `ContaNaoConfigurada` → mensagem no modal "O login Microsoft ainda não foi configurado nesta versão. Fale com a TI." e botão de login desabilitado.

- [ ] **Step 1: Testes** (QApplication offscreen; `FakeConta` com `email()`, `entrar()`, `sair()`):
  - `test_salvar_desabilitado_sem_login`.
  - `test_salvar_grava_config` (conta logada, Para `"a@b.com"`, Cco `"x@y.com"`, clicar salvar → `configuracao.carregar(tmp)` igual; `result() == Accepted`). Para permitir o teste, `ContaModal` aceita `caminho_config: Path | None = None`.
  - `test_para_invalido_mostra_erro` (não aceita; propriedade `error` True no campo Para).
- [ ] **Step 2: Rodar** → falha. **Step 3: Implementar.** **Step 4: Rodar** → passa.
- [ ] **Step 5: Commit** `feat: modal de conta e destino`.

---

### Task 7: Janela principal "Enviar"

**Files:**
- Create: `main.py`
- Test: `tests/test_ui_janela.py`

**Interfaces:**
- Consumes: tudo acima; `VerificadorAtualizacao` (`ui/atualizacao.py`), `theme_manager`, componentes.
- Produces: `class EnviarPage(c.Page)` com `adicionar(arquivos: list[Path])`, `limpar()`, propriedade `rodando: bool`; `class MainWindow(QMainWindow)`: `__init__(conta=None, caminho_config=None)`; `main() -> int`.

**Comportamento (layout do spec):**
- Janela "Enviador de PDF + XML", mesmo esqueleto do mesclador (Sidebar "Enviador" com um item "Enviar" ícone `mail` — acrescente o ícone `mail` estilo Lucide em `ui/icons.py` se não existir — Header com `ThemeToggle`, rodapé "Versão X").
- Topo: área de soltar (aceita arrastar arquivos e pastas; pasta = `arquivos_da_pasta`) + botão "Escolher pasta"; à direita o e-mail logado + botão "Configurações" (abre `ContaModal`).
- Linha "Para: …" (somente leitura, da configuração); `Input` Cco preenchido com `cfg.cco`; `Input` Vencimento com máscara `99/99/9999`; prévia do assunto do 1º par.
- `DataTable(["Nome", "PDF", "XML", "Status"])`; avisos de `achar_pares` aparecem como linhas com `Badge` tom `warning`. Adicionar mais arquivos acumula (sem duplicar o mesmo caminho).
- Rodapé: "N pares prontos · M sem par", "Limpar", primário "Enviar N e-mails" (desabilitado sem pares, sem vencimento válido ou durante envio).
- Ao clicar Enviar: valida vencimento e Cco (`validar_emails(..., False)`); `c.Modal.confirm(self, "Enviar N e-mails?", "Para: …\nCco: …")`; salva o Cco na configuração; roda `EnviarWorker` em `QThread`; status por linha ("Enviando…", Badge success "Enviado", warning "Enviado com aviso", danger "Erro"); clique numa linha com aviso/erro abre modal com o detalhe. Fim: resumo no rodapé e lista mantida até "Limpar".
- `falhou` com sessão expirada → abre `ContaModal` e mantém a lista.
- Na abertura: sem configuração ou sem conta logada → abre `ContaModal` (primeiro acesso) antes de liberar a tela. `ContaNaoConfigurada` → a tela abre, com aviso no topo e Enviar desabilitado.
- `closeEvent` durante envio: confirmação igual ao mesclador; cancelar o worker e aguardar.
- `main()`: igual ao mesclador (`limpar_antigo`, org/app name, `theme_manager.apply()`), e `VerificadorAtualizacao(self, __version__, lambda: pagina.rodando)` 1,5 s após abrir.

- [ ] **Step 1: Testes** (offscreen; `FakeConta` logada; config gravada em `tmp_path`):
  - `test_janela_abre` (constrói `MainWindow(conta=FakeConta(), caminho_config=...)` sem abrir modal).
  - `test_adicionar_monta_pares` (2 pares + 1 sem par → tabela com 3 linhas, botão "Enviar 2 e-mails").
  - `test_enviar_desabilitado_sem_vencimento`.
  - `test_adicionar_duas_vezes_nao_duplica`.
- [ ] **Step 2: Rodar** → falha. **Step 3: Implementar.** **Step 4: Rodar** → passa.
- [ ] **Step 5: Conferir à mão** `python main.py` (plataforma normal): primeiro acesso abre; arrastar arquivos falsos de `%TEMP%` monta a tabela; tema claro/escuro ok. Login real só com `CLIENT_ID` preenchido.
- [ ] **Step 6: Commit** `feat: janela principal de envio`.

---

### Task 8: Empacotamento, release e limpeza

**Files:**
- Create: `EnviadorEmails.spec`, `assets/EnviadorEmails.ico`, `.github/workflows/release.yml`, `CLAUDE.md`, `.graphifyignore`
- Modify: `README.md`, `.gitignore`
- Delete: `app.py`, `templates/`, `enviador.py`, `enviar_emails.py`, `configurar_senha.py`, `config.exemplo.ini`, `corpo.html`, `corpo.txt`

- [ ] **Step 1: `EnviadorEmails.spec`** copiado do `MesclarPDFs.spec`, trocando `name`/`icon`; manter os `excludes` e `DESNECESSARIOS`, **mas remover `PySide6.QtNetwork`/`qt6network` da exclusão só se o build quebrar** (MSAL usa `requests`, não Qt). Acrescentar `hiddenimports=['msal_extensions']` se o build não o detectar.
- [ ] **Step 2: Ícone** `assets/EnviadorEmails.ico` = ícone `mail` na cor primária `#2563EB` (gerar com `ui/icons.py` + `QImage.save`, tamanhos 16–256), como foi feito no mesclador.
- [ ] **Step 3: `release.yml`** copiado do mesclador com `MesclarPDFs` → `EnviadorEmails`; o passo "Verificar se a janela abre" passa a rodar `python -m pytest -q` (os testes de UI já constroem a janela com `FakeConta`, sem login real).
- [ ] **Step 4: Apagar os arquivos antigos** listados acima; `requirements.txt` já não tem Flask/keyring.
- [ ] **Step 5: `.gitignore`**: manter as regras atuais + `build/`, `dist/`, `*.spec.bak`, `token_cache.bin`. **`.graphifyignore`**: `*.pdf`, `*.xml`, `entrada/`, `enviados/`, `erros/`, `config.ini`, `.env`, `dist/`, `build/`.
- [ ] **Step 6: `README.md`** no formato do mesclador: Usar (baixar da Release), primeiro acesso, tela, o que acontece com os arquivos, atualização automática, pré-requisitos do Entra ID (registro de app público, redirect `http://localhost`, permissão delegada `SMTP.Send`, consentimento, SMTP AUTH na caixa), Desenvolver, Lançar uma versão, Estrutura.
- [ ] **Step 7: `CLAUDE.md`** no formato do mesclador: fluxo "Salvar versão" (sugerir `https://github.com/ErikDeFreitas/pdf-xml-mailer.git`; depois gerar `dist\EnviadorEmails.exe` + `.sha256` local), Releases, Arquitetura (tabela), Regras de negócio (pares, assunto/corpo fixos, Para/Cco no primeiro acesso, Cco lembrado, movimentação, reconexão única), Design System (copiado), Testes e armadilhas.
- [ ] **Step 8: Build local** fora do OneDrive: `python -m PyInstaller --noconfirm --clean --workpath "%TEMP%\enviador-build" --distpath "%TEMP%\enviador-dist" EnviadorEmails.spec` → gera o `.exe`; abrir e confirmar que a janela aparece.
- [ ] **Step 9: Rodar** `python -m pytest -q` → tudo passa.
- [ ] **Step 10: Commit** `chore: build, release e documentação; remove a versão Flask`.
- [ ] **Step 11: Graphify** (regra global do Erik): conferir o `.graphifyignore`, rodar `/graphify .`, revisar `skipped_sensitive`, depois `graphify claude install` e `graphify hook install`. Perguntar antes de pôr `graphify-out/` no `.gitignore`.
