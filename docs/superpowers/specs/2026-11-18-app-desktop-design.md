# Enviador de PDF + XML — app desktop (design)

Data: 2026-11-18 · Status: aprovado

## Intenção

Hoje o envio roda como uma página local servida por Flask (`app.py` + `templates/index.html`) ou por linha
de comando (`enviar_emails.py`), e depende de `config.ini`, `corpo.html` e `corpo.txt` editados à mão, com
login SMTP por usuário e senha.
O Erik quer **um `.exe` único, sem Flask**, para controlar as versões e distribuir **atualizações automáticas
pelo GitHub Releases**, no mesmo padrão do projeto `mesclador` (`ErikDeFreitas/pdf-merge`), e já preparado
para o **login moderno da Microsoft (OAuth 2.0)**, que substitui usuário + senha no SMTP do Office 365.

## O que o app faz (essência mantida)

Para cada par **PDF + XML de mesmo nome** (nome sem extensão, ex.: `123814.pdf` + `123814.xml`), envia
**um e-mail** com os dois anexos:

- **Assunto**: modelo fixo no código com `{nome}` trocado pelo nome do par (quebras de linha removidas).
- **Corpo**: fixo no código, em HTML + versão texto (alternativa), com `{vcto}` trocado pela data de
  vencimento (`dd/mm/aaaa`, data real; obrigatória). No HTML a data é escapada.
- **Para** e **Cco**: definidos pela pessoa no primeiro acesso e lidos de um arquivo local (ver Configuração).
  O Cco também aparece na tela principal, editável, e o último valor usado fica salvo. Não há Cc.
- **Remetente**: o e-mail da conta Microsoft logada.
- Intervalo de 2 s entre e-mails (evita bloqueio do servidor). Uma única conexão SMTP por lote.
- Validação de conteúdo: o PDF tem `%PDF-` no 1º KB; o XML começa com `<` (ignorando BOM/espaços).
- Arquivo sem par é listado como aviso, não é enviado e não é movido.
- Um e-mail com erro **nunca** interrompe o lote.
- **Depois do envio**: o par enviado é movido para `enviados/` e o par com erro para `erros/`, ambos
  **dentro da pasta de onde os arquivos vieram** (criadas se não existirem). Isso impede reenvio
  duplicado ao enviar a mesma pasta de novo. Se o nome já existir no destino, acrescenta `_2`, `_3`…

## Decisões do usuário

1. **Sem Flask.** App desktop, um `.exe`, atualização automática pelo GitHub Releases.
2. **Repositório público.** Assunto e corpo fixos no código não têm dado sensível (os dados variáveis vêm dos
   arquivos e da tela).
3. **Login pela Microsoft (OAuth 2.0 / XOAUTH2 no SMTP)** em vez de senha.
4. **Para e Cco** preenchidos no primeiro acesso, salvos num arquivo local e lidos dele a cada abertura
   (fora do código, então não ficam no repositório público).
5. **Cco** opcional, também editável na tela principal, lembrando a última escolha.
6. **Mover para `enviados/` e `erros/`** após o envio.

## Abordagens consideradas

**Estrutura do app**

| Abordagem | Prós | Contras |
|---|---|---|
| **Portar para o esqueleto do mesclador (PySide6 + core/ui + PyInstaller + Releases)** — escolhida | Mesmo padrão, Design System e atualização já validados | Reescreve a interface |
| Empacotar o Flask atual num `.exe` | Pouca mudança | Continua com servidor local; foi o que o usuário pediu para tirar |
| Tkinter | `.exe` menor | Proibido pelo Design System dos apps |

**Envio com OAuth 2.0**

| Abordagem | Prós | Contras |
|---|---|---|
| **SMTP com XOAUTH2 (`smtplib` + token do MSAL)** — escolhida | Mantém a lógica de envio atual; anexos até ~25 MB; é o que o usuário pediu | A caixa precisa ter "SMTP autenticado" habilitado no Exchange |
| Microsoft Graph `sendMail` | Caminho preferido pela Microsoft; não depende de SMTP AUTH | Reescreve o envio; anexos > 3 MB exigem sessão de upload |

## Login Microsoft (OAuth 2.0)

- Biblioteca `msal` como **aplicativo público** (sem segredo de cliente no `.exe`).
- Escopo delegado `https://outlook.office.com/SMTP.Send` + `offline_access`.
- Login interativo: abre a página de login da Microsoft no navegador padrão (`acquire_token_interactive`),
  inclusive com MFA. Depois disso o app usa `acquire_token_silent` (token renovado sozinho, sem pedir login
  de novo enquanto a renovação for válida).
- **Cache de tokens criptografado** com `msal-extensions` (DPAPI do Windows, por usuário), em
  `%LOCALAPPDATA%\EnviadorEmails\token_cache.bin`. **O app não vê nem guarda senha nenhuma.**
- SMTP: `smtp.office365.com:587` com STARTTLS, autenticação `AUTH XOAUTH2` com o e-mail da conta e o token.
- **Pré-requisitos no Microsoft 365 (feitos uma vez pela TI):**
  - Registro de aplicativo no Entra ID: tipo "cliente público", redirect `http://localhost`, permissão
    delegada `SMTP.Send` (Office 365 Exchange Online), com consentimento.
  - `CLIENT_ID` e `TENANT_ID` desse registro ficam fixos em `core/modelo.py` (não são segredos).
  - SMTP AUTH habilitado nas caixas que vão enviar.
- "Sair da conta" remove a conta do cache MSAL.

## Configuração local (primeiro acesso)

Arquivo `%APPDATA%\EnviadorEmails\config.json` (por usuário do Windows, fora da pasta do programa):

```json
{ "para": "destino@cliente.com.br", "cco": "" }
```

- **Primeiro acesso** (sem arquivo ou sem conta logada): assistente em um modal
  1. "Entrar com a Microsoft" → login no navegador → mostra o e-mail logado.
  2. "Para" (obrigatório, um ou mais e-mails separados por `;`) e "Cco" (opcional, idem). Validação de formato.
  3. "Salvar". Só então a tela principal libera o envio.
- **Configurações** (botão na tela principal) reabre o mesmo modal para trocar Para/Cco ou sair da conta.
- O `cco` é atualizado a cada envio com o valor do campo Cco da tela principal.
- Arquivo ilegível ou inválido → trata como primeiro acesso, sem travar o app.

## Arquitetura (espelho do mesclador)

| Caminho | Papel |
|---|---|
| `core/envio.py` | Regras: achar pares, validar arquivos, montar assunto/corpo/mensagem, abrir SMTP (XOAUTH2), enviar lote, mover para `enviados/`/`erros/`. **Sem import de interface.** |
| `core/modelo.py` | Constantes fixas: modelo de assunto, corpo HTML e texto, servidor SMTP, `CLIENT_ID`, `TENANT_ID` |
| `core/conta.py` | MSAL: login interativo, token silencioso, sair; cache criptografado |
| `core/configuracao.py` | Ler/gravar `config.json` (Para, Cco) com validação |
| `core/worker.py` | `QObject`s numa `QThread`: login e envio do lote (sinal por par: enviando/OK/erro). A janela nunca trava |
| `core/atualizacao.py` | Copiado do mesclador, trocando `REPOSITORIO` e `NOME_EXE` |
| `core/__main__.py` | Modo terminal: `python -m core "C:\Pasta" --vcto dd/mm/aaaa [--cco x] [--dry-run]` (usa conta e config salvas) |
| `ui/` | `themes.py`, `styles.qss`, `components.py`, `icons.py`, `atualizacao.py` copiados do mesclador |
| `main.py` | Janela |
| `version.py`, `EnviadorEmails.spec`, `assets/EnviadorEmails.ico`, `.github/workflows/release.yml`, `CLAUDE.md`, `README.md` | Iguais ao padrão do mesclador, com os nomes deste app |

Saem: `app.py`, `templates/`, `enviador.py`, `enviar_emails.py`, `configurar_senha.py`, `config.exemplo.ini`,
`corpo.html`, `corpo.txt` (o conteúdo vai para `core/modelo.py`), dependências `Flask` e `keyring`.
Dependências novas (versões fixadas como no mesclador): `PySide6-Essentials`, `msal`, `msal-extensions`, `pyinstaller`.

## Tela principal "Enviar"

```
[ Arraste PDFs e XMLs aqui  ou  Escolher pasta ]        fulano@tcm.com.br  [Configurações]
Para: destino@cliente.com.br
Cco: [________________]        Vencimento: [dd/mm/aaaa]
Assunto (prévia): EMPRESA - CTE 123814 - ...
┌ Nome    │ PDF │ XML │ Status ────────────┐
│ 123814  │  ✓  │  ✓  │ Pronto             │
│ 123815  │  ✓  │  —  │ Aviso: sem XML     │
└────────────────────────────────────────────┘
2 pares prontos · 1 sem par        [Limpar]  [Enviar 2 e-mails]
```

- Confirmação antes de enviar ("Enviar 2 e-mails para X?").
- Durante o envio: status por linha (Enviando, Enviado, Erro + motivo), botões travados.
- Fim: resumo "N enviados, M com erro"; clique na linha com erro mostra o detalhe.
- Token expirado e sem renovação possível → pede login de novo antes de enviar, sem perder a lista.
- Tema claro/escuro e aviso de nova versão iguais ao mesclador.

## Segurança

- Nenhuma senha passa pelo app. Tokens só no cache MSAL criptografado com DPAPI.
- Sem segredo de cliente no `.exe` (aplicativo público).
- Sem servidor/porta aberta (some a superfície de CSRF/DNS rebinding do Flask).
- TLS sempre (`ssl.create_default_context()`), timeout 30 s.
- Para/Cco ficam no `%APPDATA%` do usuário, nunca no repositório.
- Atualização só instala se o SHA-256 bater com o publicado na Release.
- `.gitignore` mantém `*.pdf`, `*.xml`, `entrada/`, `enviados/`, `erros/`, `config.ini`, `.env`.
- `.graphifyignore` antes de gerar o grafo.

## Não-objetivos

- Editar assunto ou corpo pela tela.
- Histórico de envios em arquivo (a proteção contra duplicado é a movimentação para `enviados/`).
- Leitura de dados de dentro do XML.
- Instalador (MSI): o `.exe` é único e portátil.
- Login por senha (SMTP básico) como alternativa.

## Anti-objetivos

- Senha ou token gravados em texto puro, ou visíveis em log/tela.
- Enviar e-mail sem a pessoa confirmar o lote.
- Um erro num par derrubar o lote ou travar a janela.

## Decisões do construtor (podem ser corrigidas)

- Remetente = e-mail da conta logada (sem "enviar como" / caixa compartilhada).
- Arquivos arrastados de pastas diferentes: cada par é movido para `enviados/`/`erros/` da sua própria pasta.
- Para e Cco aceitam vários e-mails separados por `;`.

## Pendências

- Registro do aplicativo no Entra ID (`CLIENT_ID`, `TENANT_ID`) e SMTP AUTH habilitado nas caixas.
