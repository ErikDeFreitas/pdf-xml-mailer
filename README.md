# Enviador de PDF + XML

Envia **um e-mail para cada par PDF + XML de mesmo nome** (ex.: `123814.pdf` + `123814.xml`),
com os dois arquivos anexados. O assunto e o corpo são configuráveis e podem usar o nome do par e a data de vencimento.

## Usar

Baixe o `EnviadorEmails.exe` da última [Release](../../releases/latest) e abra.

**Primeiro acesso:** clique em **Entrar com a Microsoft** (o login acontece no navegador, com MFA se
houver) e informe **Para** (obrigatório) e **Cco** (opcional). Para trocar depois: **Configurações**.

**Texto do e-mail:** clique em **Configurar e-mail** (card Envio) e edite o assunto e o corpo. Use `{nome}`
para o nome do arquivo e `{vcto}` para o vencimento; `**texto**` sai em negrito. O que você salvar vale para
todos os próximos envios. Enquanto o assunto for o de exemplo ("TEXTO FIXO"), o envio fica bloqueado.

**Enviar:**
1. Arraste PDFs, XMLs ou pastas para a janela (ou use **Escolher pasta**, ao lado do Enviar, ou **Escolher arquivos**).
2. Confira os pares na tabela. Arquivo sem par aparece como aviso e não é enviado.
3. Informe o **Vencimento** (dd/mm/aaaa).
4. Clique em **Enviar N e-mails** (vermelho) e confirme. O Cco é o definido em **Configurações**.

Cada linha mostra o andamento: Enviando, Enviado, Enviado com aviso ou Erro (clique para ver o motivo).

## O que acontece com os arquivos

| Situação | Para onde vai |
|---|---|
| E-mail enviado | `enviados/` dentro da pasta de onde o arquivo veio |
| Erro no envio ou arquivo inválido | `erros/` dentro da pasta de onde o arquivo veio |
| Enviado, mas o arquivo estava aberto e não pôde ser movido | Fica no lugar; a linha mostra **Enviado com aviso** |
| Conexão caiu de vez no meio do lote | Os restantes ficam no lugar para um novo envio |
| Sem par | Fica no lugar |

Se já existir um arquivo com o mesmo nome em `enviados/`, o novo vira `nome_2.pdf`, `nome_3.pdf`…
Como os enviados saem da pasta, enviar a mesma pasta de novo não repete e-mails.

## Segurança

- **Nenhuma senha passa pelo programa.** O login é feito pela Microsoft (OAuth 2.0); o programa guarda só
  um token, criptografado pelo Windows para o seu usuário, em `%LOCALAPPDATA%\TCM\ContaMicrosoft\token_cache.bin`.
  Esse login é compartilhado com os outros sistemas da TCM que enviam e-mail (ex.: RoboAgregado): quem entrou
  num deles já está logado nos outros. Na 2.1.0, o login da versão anterior é copiado para lá automaticamente.
- **Para e Cco** ficam em `%APPDATA%\EnviadorEmails\config.json`, fora do programa e do repositório.
- Assunto e corpo ficam no mesmo `config.json`; o texto padrão está em `src/enviador_pdf_xml/modelo.py`.
- Conexão sempre com TLS. Nenhuma porta é aberta no computador.
- A atualização automática só instala o `.exe` novo se o SHA-256 bater com o publicado na Release.

## Pré-requisitos no Microsoft 365 (uma vez, pela TI)

1. **Entra ID → Registros de aplicativo → Novo registro**: tipo de conta "somente este diretório".
2. **Autenticação**: adicionar plataforma "Aplicativos móveis e da área de trabalho" com o URI
   `http://localhost` e ativar "Permitir fluxos de cliente público".
3. **Permissões de API**: Office 365 Exchange Online → permissão delegada `SMTP.Send` → conceder consentimento.
4. Copiar o **ID do aplicativo (cliente)** e o **ID do diretório (locatário)** para `CLIENT_ID` e `TENANT_ID`
   em `src/tcm_ui/microsoft.py` do repositório `Tcm-ui` e lançar uma versão (vale para todos os sistemas).
5. Nas caixas que vão enviar: **SMTP autenticado** habilitado (Exchange → Caixa de correio → E-mail → Aplicativos de e-mail).

Sem os IDs, o programa abre, mas o login avisa "Fale com a TI".

## Atualização automática

Ao abrir, o programa consulta a última Release no GitHub. Se houver versão nova (e nenhum envio
em andamento), mostra "Atualizando para a versão X", com a barra do download, confere o SHA-256 e
reinicia já atualizado. Se o download falhar, avisa e continua na versão atual. Sem internet, nada
aparece.

## Desenvolver

A interface vem da biblioteca [`tcm-ui`](https://github.com/ErikDeFreitas/Tcm-ui).

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\python main.py
```

Para desenvolver junto com o `tcm-ui`, instale-o editável a partir do clone vizinho
(`.venv\Scripts\pip install -e ..\Tcm-ui`) antes do `pip install -e ".[dev]"`.

Testes (não escrevem no registro, nas pastas reais de dados nem enviam e-mail):

```
.venv\Scripts\python -m pytest -q
```

Os dados ficam onde sempre ficaram (`%APPDATA%\EnviadorEmails` e `%LOCALAPPDATA%\EnviadorEmails`);
defina `ENVIADOR_DADOS` para usar uma única pasta, por exemplo em testes.

Modo terminal (usa a conta e o Para/Cco salvos pelo programa):

```
python -m enviador_pdf_xml "C:\Pasta" --vcto 20/11/2026 --dry-run
python -m enviador_pdf_xml "C:\Pasta" --vcto 20/11/2026 [--cco copia@empresa.com.br]
```

## Gerar o executável

```
powershell -File build.ps1
```

Gera `dist\EnviadorEmails.exe` e `dist\EnviadorEmails.exe.sha256` (precisa do PyInstaller no ambiente).

## Lançar uma versão

1. Suba `__version__` em `src/enviador_pdf_xml/__init__.py` (ex.: `2.0.1`).
2. Crie a tag igual, com `v` na frente, e envie: `git tag v2.0.1` e `git push origin v2.0.1`.

O GitHub Actions (`.github/workflows/release.yml`) confere que a tag bate com `__version__`, roda os
testes, gera o `.exe` e o `.sha256` e publica a Release com os dois arquivos.
O `requirements.txt` fixa o `tcm-ui[microsoft]` numa tag (`v1.6.0`), que precisa existir no GitHub.

## Módulo do Sistema Financeiro

O Enviador também é um módulo da casca Sistema Financeiro (`MODULO` em `src/enviador_pdf_xml/modulo.py`,
registrado no entry point `sistema_financeiro.modulos`). Na casca ele aparece para quem está no grupo
`SF-EnviadorPDFXML`.

## Estrutura

| Pasta/arquivo | Conteúdo |
|---|---|
| `src/enviador_pdf_xml/modelo.py` | Assunto e corpo padrão |
| `src/enviador_pdf_xml/envio.py` | Pares, validação, mensagem, SMTP (XOAUTH2), envio do lote, movimentação |
| `src/enviador_pdf_xml/configuracao.py` | Para, Cco, assunto e corpo do usuário (`config.json`) |
| `src/enviador_pdf_xml/worker.py` | Envio em segundo plano para a janela (o login vem de `tcm_ui.microsoft`) |
| `src/enviador_pdf_xml/tela.py`, `dialogos.py` | Tela do módulo e diálogos de conta e de e-mail |
| `src/enviador_pdf_xml/instancia.py` | Instância do módulo (casca e avulso) |
| `src/enviador_pdf_xml/modulo.py` | Registro do módulo (`MODULO`) |
| `src/enviador_pdf_xml/dados.py` | Pastas de dados |
| `src/enviador_pdf_xml/cli.py` | Modo terminal |
| `main.py` | Ponto de entrada do `.exe` avulso |
| `build.ps1` | Gera o `.exe` e o `.sha256` |
| `assets/` | Ícone do executável (`EnviadorEmails.ico`) |
| `tests/` | Testes (pytest) |
