# Graph Report - pdf-xml-mailer  (2026-11-19)

## Corpus Check
- 35 files · ~18,669 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 3, .spec 1, .ini 1)

## Summary
- 605 nodes · 1355 edges · 22 communities (16 shown, 6 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c1ecdd28`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Conta Microsoft e CLI
- Envio do lote e pares
- Worker de envio e testes
- Configuracao
- Atualização automática
- Tela de envio
- Botões e diálogos
- Workflow de release
- Testes do modal de conta
- Implementation Plan: app desktop (8 tasks)
- Workers de login e update
- Tema claro/escuro
- components.py
- hbox
- Testes da janela
- EmailModal
- icons.py

## God Nodes (most connected - your core abstractions)
1. `EnviarPage` - 40 edges
2. `Configuracao` - 37 edges
3. `pares()` - 29 edges
4. `carregar()` - 25 edges
5. `Conta` - 25 edges
6. `ContaModal` - 24 edges
7. `enviar_lote()` - 21 edges
8. `FakeSMTP` - 21 edges
9. `main()` - 20 edges
10. `salvar()` - 19 edges

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
- **First-access setup (login + Para/Cco)** — ui_conta_contamodal, core_worker_loginworker, core_conta_conta, core_configuracao_configuracao [EXTRACTED 1.00]
- **Microsoft login to SMTP send flow** — core_conta_conta, core_envio_abrir_smtp, core_envio_enviar_lote, core_worker_enviarworker [EXTRACTED 1.00]

## Communities (22 total, 6 thin omitted)

### Community 0 - "Conta Microsoft e CLI"
Cohesion: 0.11
Nodes (17): caminho_cache(), Conta, _criar_cache(), pendencias_release(), FakeApp, test_cache_de_token_criptografado_funciona(), test_caminho_cache_usa_localappdata(), test_email_sem_conta_e_none() (+9 more)

### Community 1 - "Envio do lote e pares"
Cohesion: 0.06
Nodes (33): achar_pares(), arquivos_da_pasta(), destino_livre(), enviar_lote(), FalhaConexao, _fechar(), montar_assunto(), montar_corpo() (+25 more)

### Community 2 - "Worker de envio e testes"
Cohesion: 0.07
Nodes (38): main(), _modelo_ou_padrao(), assunto_de_exemplo(), validar_modelo(), ContaFalsa, sem_conta(), test_cli_assunto_de_exemplo_nao_envia(), test_cli_dry_run_lista_assuntos() (+30 more)

### Community 3 - "Configuracao"
Cohesion: 0.09
Nodes (27): caminho_padrao(), carregar(), Configuracao, salvar(), appdata(), com_config(), test_caminho_padrao_usa_appdata(), test_cco_invalido_vira_vazio() (+19 more)

### Community 4 - "Atualização automática"
Cohesion: 0.09
Nodes (18): _abrir(), _antigo(), baixar_e_conferir(), buscar_ultima(), executavel_atual(), FalhaAtualizacao, instalar(), limpar_antigo() (+10 more)

### Community 5 - "Tela de envio"
Cohesion: 0.10
Nodes (4): EnviarPage, main(), MainWindow, _plural()

### Community 6 - "Botões e diálogos"
Cohesion: 0.10
Nodes (6): Button, IconButton, Modal, NavButton, themed_icon(), ThemeToggle

### Community 7 - "Workflow de release"
Cohesion: 0.08
Nodes (25): runs-on, steps, QT_QPA_PLATFORM, jobs, build, name, on, push (+17 more)

### Community 8 - "Testes do modal de conta"
Cohesion: 0.16
Nodes (15): app(), ContaTravada, _esperar(), FakeConta, modal(), test_cancelar_fecha_durante_login_travado(), test_falha_no_login_mostra_motivo_e_permite_tentar_de_novo(), test_login_em_segundo_plano_habilita_salvar() (+7 more)

### Community 9 - "Implementation Plan: app desktop (8 tasks)"
Cohesion: 0.10
Nodes (15): Auto-update via GitHub Releases with SHA-256 check, Local config (Para/Cco) in %APPDATA% config.json, Design System rules: PySide6 + QSS only, tokens, no inline style, Microsoft 365 / Entra ID prerequisites (app registration, SMTP.Send, SMTP AUTH), mesclador project (reference skeleton and Design System), Pairing PDF + XML by same name (one email per pair), Release workflow (tag, GitHub Actions, PyInstaller exe + sha256), abrir_smtp() (+7 more)

### Community 10 - "Workers de login e update"
Cohesion: 0.08
Nodes (11): FalhaLogin, BaixarAtualizacaoWorker, EnviarWorker, LoginWorker, entrar(), ContaFalsa, test_enviar_worker_emite_resultados(), test_enviar_worker_sessao_expirada() (+3 more)

### Community 12 - "components.py"
Cohesion: 0.09
Nodes (4): ContaNaoConfigurada, _criar_app(), Checkbox, Select

### Community 13 - "hbox"
Cohesion: 0.05
Nodes (17): Badge, Card, DataTable, Divider, _fill(), FormField, hbox(), Header (+9 more)

### Community 14 - "Testes da janela"
Cohesion: 0.21
Nodes (10): ResultadoPar, app(), arquivos(), test_adicionar_duas_vezes_nao_duplica(), test_adicionar_monta_pares(), test_adicionar_pasta(), test_assunto_de_exemplo_bloqueia_envio(), test_enviado_com_aviso_nao_fica_pendente() (+2 more)

### Community 16 - "EmailModal"
Cohesion: 0.16
Nodes (4): Input, SearchInput, TextArea, EmailModal

### Community 17 - "icons.py"
Cohesion: 0.20
Nodes (6): _dpr(), icon(), pixmap(), _pixmap(), svg(), svg_file()

## Knowledge Gaps
- **2 isolated node(s):** `Design System rules: PySide6 + QSS only, tokens, no inline style`, `Release workflow (tag, GitHub Actions, PyInstaller exe + sha256)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 184 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Configuracao` connect `Configuracao` to `Envio do lote e pares`, `Worker de envio e testes`, `Tela de envio`, `Testes do modal de conta`, `Implementation Plan: app desktop (8 tasks)`, `components.py`, `Testes da janela`, `EmailModal`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `EnviarPage` (e.g. with `Configuracao` and `ContaModal`) actually correct?**
  _`EnviarPage` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Design System rules: PySide6 + QSS only, tokens, no inline style`, `Release workflow (tag, GitHub Actions, PyInstaller exe + sha256)` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Conta Microsoft e CLI` be split into smaller, more focused modules?**
  _Cohesion score 0.11088709677419355 - nodes in this community are weakly interconnected._
- **Why does `EnviarPage` connect `Tela de envio` to `Envio do lote e pares`, `Configuracao`, `Implementation Plan: app desktop (8 tasks)`, `Workers de login e update`, `components.py`, `hbox`, `EmailModal`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Configuracao` (e.g. with `Local config (Para/Cco) in %APPDATA% config.json` and `EnviarPage`) actually correct?**
  _`Configuracao` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `Envio do lote e pares` be split into smaller, more focused modules?**
  _Cohesion score 0.06390977443609022 - nodes in this community are weakly interconnected._