# Graph Report - pdf-xml-mailer  (2026-11-18)

## Corpus Check
- 32 files · ~17,117 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 3, .spec 1, .ini 1)

## Summary
- 551 nodes · 1202 edges · 26 communities (14 shown, 12 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 40 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `422504ca`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- Workers de login e update
- Tema claro/escuro
- components.py
- Layouts e rótulos
- Testes da janela
- Label
- Badges e progresso
- FormField e erros
- Sidebar
- Page
- Tabela de dados
- Cards
- Ícone temático

## God Nodes (most connected - your core abstractions)
1. `EnviarPage` - 35 edges
2. `Conta` - 26 edges
3. `pares()` - 25 edges
4. `Configuracao` - 23 edges
5. `ContaModal` - 22 edges
6. `enviar_lote()` - 21 edges
7. `FalhaLogin` - 20 edges
8. `main()` - 20 edges
9. `FakeSMTP` - 19 edges
10. `EnviarWorker` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Local config (Para/Cco) in %APPDATA% config.json` --rationale_for--> `Configuracao`  [INFERRED]
  docs/superpowers/specs/2026-11-18-app-desktop-design.md → core/configuracao.py
- `Pairing PDF + XML by same name (one email per pair)` --rationale_for--> `achar_pares()`  [INFERRED]
  README.md → core/envio.py
- `Implementation Plan: app desktop (8 tasks)` --references--> `ContaModal`  [EXTRACTED]
  docs/superpowers/plans/2026-11-18-app-desktop.md → ui/conta.py
- `Microsoft OAuth 2.0 login with SMTP XOAUTH2` --rationale_for--> `Conta`  [EXTRACTED]
  docs/superpowers/specs/2026-11-18-app-desktop-design.md → core/conta.py
- `Implementation Plan: app desktop (8 tasks)` --references--> `Conta`  [EXTRACTED]
  docs/superpowers/plans/2026-11-18-app-desktop.md → core/conta.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **First-access setup (login + Para/Cco)** — ui_conta_contamodal, core_worker_loginworker, core_conta_conta, core_configuracao_configuracao [EXTRACTED 1.00]
- **Microsoft login to SMTP send flow** — core_conta_conta, core_envio_abrir_smtp, core_envio_enviar_lote, core_worker_enviarworker [EXTRACTED 1.00]

## Communities (26 total, 12 thin omitted)

### Community 0 - "Conta Microsoft e CLI"
Cohesion: 0.08
Nodes (20): caminho_cache(), Conta, ContaNaoConfigurada, _criar_app(), _criar_cache(), FalhaLogin, pendencias_release(), FakeApp (+12 more)

### Community 1 - "Envio do lote e pares"
Cohesion: 0.06
Nodes (30): abrir_smtp(), achar_pares(), arquivos_da_pasta(), destino_livre(), enviar_lote(), FalhaConexao, _fechar(), montar_corpo() (+22 more)

### Community 2 - "Worker de envio e testes"
Cohesion: 0.09
Nodes (27): EnviarWorker, FakeSMTP, lote(), pares(), SMTPComErro, test_abrir_smtp_usa_xoauth2(), test_lote_avisa_inicio(), test_lote_aviso_diz_para_nao_reenviar() (+19 more)

### Community 3 - "Configuração Para/Cco"
Cohesion: 0.08
Nodes (33): Auto-update via GitHub Releases with SHA-256 check, Local config (Para/Cco) in %APPDATA% config.json, Design System rules: PySide6 + QSS only, tokens, no inline style, Microsoft 365 / Entra ID prerequisites (app registration, SMTP.Send, SMTP AUTH), mesclador project (reference skeleton and Design System), Pairing PDF + XML by same name (one email per pair), Release workflow (tag, GitHub Actions, PyInstaller exe + sha256), main() (+25 more)

### Community 4 - "Atualização automática"
Cohesion: 0.14
Nodes (16): _abrir(), _antigo(), baixar_e_conferir(), buscar_ultima(), executavel_atual(), FalhaAtualizacao, instalar(), limpar_antigo() (+8 more)

### Community 5 - "Tela de envio"
Cohesion: 0.10
Nodes (4): EnviarPage, main(), MainWindow, _plural()

### Community 6 - "Botões e diálogos"
Cohesion: 0.08
Nodes (8): Button, IconButton, Input, Modal, NavButton, SearchInput, themed_icon(), ThemeToggle

### Community 7 - "Workflow de release"
Cohesion: 0.08
Nodes (25): runs-on, steps, QT_QPA_PLATFORM, jobs, build, name, on, push (+17 more)

### Community 8 - "Testes do modal de conta"
Cohesion: 0.12
Nodes (16): ContaTravada, _esperar(), FakeConta, modal(), test_cancelar_fecha_durante_login_travado(), test_falha_no_login_mostra_motivo_e_permite_tentar_de_novo(), entrar(), test_login_em_segundo_plano_habilita_salvar() (+8 more)

### Community 10 - "Workers de login e update"
Cohesion: 0.12
Nodes (5): BaixarAtualizacaoWorker, LoginWorker, test_login_worker(), AtualizacaoModal, _mb()

### Community 12 - "components.py"
Cohesion: 0.06
Nodes (11): _Aviso, VerificadorAtualizacao, Checkbox, Select, TextArea, _dpr(), icon(), pixmap() (+3 more)

### Community 13 - "Layouts e rótulos"
Cohesion: 0.26
Nodes (4): _fill(), hbox(), Header, vbox()

### Community 14 - "Testes da janela"
Cohesion: 0.22
Nodes (10): ResultadoPar, app(), app(), arquivos(), test_adicionar_duas_vezes_nao_duplica(), test_adicionar_monta_pares(), test_adicionar_pasta(), test_enviado_com_aviso_nao_fica_pendente() (+2 more)

### Community 17 - "FormField e erros"
Cohesion: 0.24
Nodes (3): FormField, repolish(), set_prop()

## Knowledge Gaps
- **2 isolated node(s):** `Design System rules: PySide6 + QSS only, tokens, no inline style`, `Release workflow (tag, GitHub Actions, PyInstaller exe + sha256)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 171 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EnviarPage` connect `Tela de envio` to `Envio do lote e pares`, `Worker de envio e testes`, `Configuração Para/Cco`, `Testes do modal de conta`, `components.py`, `Layouts e rótulos`, `Cards`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `EnviarPage` (e.g. with `ContaModal` and `MainWindow`) actually correct?**
  _`EnviarPage` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Design System rules: PySide6 + QSS only, tokens, no inline style`, `Release workflow (tag, GitHub Actions, PyInstaller exe + sha256)` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Conta Microsoft e CLI` be split into smaller, more focused modules?**
  _Cohesion score 0.0782312925170068 - nodes in this community are weakly interconnected._
- **Why does `Conta` connect `Conta Microsoft e CLI` to `Envio do lote e pares`, `Worker de envio e testes`, `Configuração Para/Cco`, `Workers de login e update`, `components.py`, `Layouts e rótulos`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Configuracao` (e.g. with `Local config (Para/Cco) in %APPDATA% config.json` and `com_config()`) actually correct?**
  _`Configuracao` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `Envio do lote e pares` be split into smaller, more focused modules?**
  _Cohesion score 0.06170598911070781 - nodes in this community are weakly interconnected._