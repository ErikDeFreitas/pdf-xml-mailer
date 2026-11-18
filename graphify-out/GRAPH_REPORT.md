# Graph Report - pdf-xml-mailer  (2026-11-18)

## Corpus Check
- Corpus is ~16,831 words - fits in a single context window. You may not need a graph.

## Summary
- 538 nodes · 1181 edges · 25 communities (17 shown, 8 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 46 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Conta Microsoft e CLI
- Envio do lote e pares
- Worker de envio e testes
- Configuração Para/Cco
- Atualização automática
- Tela de envio
- Botões e diálogos
- Workflow de release
- Testes do modal de conta
- Decisões de design
- Workers de login e update
- Tema claro/escuro
- Ícones SVG
- Layouts e rótulos
- Testes da janela
- Campos de formulário
- Badges e progresso
- FormField e erros
- Sidebar e cabeçalho
- Inputs de texto
- Tabela de dados
- Cards
- Ícone temático
- Página rolável

## God Nodes (most connected - your core abstractions)
1. `EnviarPage` - 36 edges
2. `Conta` - 27 edges
3. `pares()` - 25 edges
4. `Configuracao` - 24 edges
5. `ContaModal` - 22 edges
6. `enviar_lote()` - 21 edges
7. `main()` - 20 edges
8. `FakeSMTP` - 19 edges
9. `FalhaLogin` - 17 edges
10. `EnviarWorker` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Local config (Para/Cco) in %APPDATA% config.json` --rationale_for--> `Configuracao`  [INFERRED]
  docs/superpowers/specs/2026-11-18-app-desktop-design.md → core/configuracao.py
- `Pairing PDF + XML by same name (one email per pair)` --rationale_for--> `achar_pares()`  [INFERRED]
  README.md → core/envio.py
- `Implementation Plan: app desktop (8 tasks)` --references--> `main()`  [EXTRACTED]
  docs/superpowers/plans/2026-11-18-app-desktop.md → core/cli.py
- `README Enviador de PDF + XML` --references--> `main()`  [EXTRACTED]
  README.md → core/cli.py
- `Implementation Plan: app desktop (8 tasks)` --references--> `Configuracao`  [EXTRACTED]
  docs/superpowers/plans/2026-11-18-app-desktop.md → core/configuracao.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Microsoft login to SMTP send flow** — core_conta_conta, core_envio_abrir_smtp, core_envio_enviar_lote, core_worker_enviarworker [EXTRACTED 1.00]
- **First-access setup (login + Para/Cco)** — ui_conta_contamodal, core_worker_loginworker, core_conta_conta, core_configuracao_configuracao [EXTRACTED 1.00]

## Communities (25 total, 8 thin omitted)

### Community 0 - "Conta Microsoft e CLI"
Cohesion: 0.06
Nodes (20): caminho_cache(), Conta, ContaNaoConfigurada, _criar_app(), _criar_cache(), FalhaLogin, pendencias_release(), FakeApp (+12 more)

### Community 1 - "Envio do lote e pares"
Cohesion: 0.07
Nodes (27): achar_pares(), arquivos_da_pasta(), destino_livre(), enviar_lote(), FalhaConexao, _fechar(), montar_corpo(), montar_mensagem() (+19 more)

### Community 2 - "Worker de envio e testes"
Cohesion: 0.10
Nodes (26): EnviarWorker, FakeSMTP, lote(), pares(), SMTPComErro, test_lote_avisa_inicio(), test_lote_aviso_diz_para_nao_reenviar(), test_lote_cancelado() (+18 more)

### Community 3 - "Configuração Para/Cco"
Cohesion: 0.11
Nodes (22): main(), caminho_padrao(), carregar(), Configuracao, salvar(), montar_assunto(), validar_emails(), appdata() (+14 more)

### Community 4 - "Atualização automática"
Cohesion: 0.11
Nodes (18): _abrir(), _antigo(), baixar_e_conferir(), buscar_ultima(), executavel_atual(), FalhaAtualizacao, instalar(), limpar_antigo() (+10 more)

### Community 5 - "Tela de envio"
Cohesion: 0.11
Nodes (4): EnviarPage, main(), MainWindow, _plural()

### Community 6 - "Botões e diálogos"
Cohesion: 0.10
Nodes (6): Button, IconButton, Modal, NavButton, themed_icon(), ThemeToggle

### Community 7 - "Workflow de release"
Cohesion: 0.08
Nodes (25): runs-on, steps, QT_QPA_PLATFORM, jobs, build, name, on, push (+17 more)

### Community 8 - "Testes do modal de conta"
Cohesion: 0.13
Nodes (11): app(), FakeConta, modal(), test_para_invalido_mostra_erro(), test_preenche_com_config_existente(), test_sair_volta_para_nao_logado(), test_salvar_desabilitado_sem_login(), test_salvar_grava_config() (+3 more)

### Community 9 - "Decisões de design"
Cohesion: 0.10
Nodes (15): Auto-update via GitHub Releases with SHA-256 check, Local config (Para/Cco) in %APPDATA% config.json, Design System rules: PySide6 + QSS only, tokens, no inline style, Microsoft 365 / Entra ID prerequisites (app registration, SMTP.Send, SMTP AUTH), mesclador project (reference skeleton and Design System), Pairing PDF + XML by same name (one email per pair), Release workflow (tag, GitHub Actions, PyInstaller exe + sha256), abrir_smtp() (+7 more)

### Community 10 - "Workers de login e update"
Cohesion: 0.13
Nodes (5): BaixarAtualizacaoWorker, LoginWorker, test_login_worker(), AtualizacaoModal, _mb()

### Community 12 - "Ícones SVG"
Cohesion: 0.20
Nodes (6): _dpr(), icon(), pixmap(), _pixmap(), svg(), svg_file()

### Community 13 - "Layouts e rótulos"
Cohesion: 0.25
Nodes (4): _fill(), hbox(), Label, vbox()

### Community 14 - "Testes da janela"
Cohesion: 0.27
Nodes (9): ResultadoPar, app(), arquivos(), test_adicionar_duas_vezes_nao_duplica(), test_adicionar_monta_pares(), test_adicionar_pasta(), test_enviado_com_aviso_nao_fica_pendente(), test_enviar_desabilitado_sem_vencimento() (+1 more)

### Community 15 - "Campos de formulário"
Cohesion: 0.18
Nodes (3): Checkbox, Select, TextArea

### Community 17 - "FormField e erros"
Cohesion: 0.24
Nodes (3): FormField, repolish(), set_prop()

### Community 18 - "Sidebar e cabeçalho"
Cohesion: 0.25
Nodes (3): Divider, Header, Sidebar

## Knowledge Gaps
- **2 isolated node(s):** `Design System rules: PySide6 + QSS only, tokens, no inline style`, `Release workflow (tag, GitHub Actions, PyInstaller exe + sha256)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 173 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EnviarPage` connect `Tela de envio` to `Conta Microsoft e CLI`, `Envio do lote e pares`, `Worker de envio e testes`, `Configuração Para/Cco`, `Testes do modal de conta`, `Decisões de design`, `Sidebar e cabeçalho`, `Cards`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `EnviarPage` (e.g. with `Configuracao` and `ContaModal`) actually correct?**
  _`EnviarPage` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Design System rules: PySide6 + QSS only, tokens, no inline style`, `Release workflow (tag, GitHub Actions, PyInstaller exe + sha256)` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Conta Microsoft e CLI` be split into smaller, more focused modules?**
  _Cohesion score 0.057902973395931145 - nodes in this community are weakly interconnected._
- **Why does `Conta` connect `Conta Microsoft e CLI` to `Worker de envio e testes`, `Configuração Para/Cco`, `Tela de envio`, `Decisões de design`, `Workers de login e update`, `Sidebar e cabeçalho`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Conta` (e.g. with `main()` and `MainWindow`) actually correct?**
  _`Conta` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Envio do lote e pares` be split into smaller, more focused modules?**
  _Cohesion score 0.0693815987933635 - nodes in this community are weakly interconnected._