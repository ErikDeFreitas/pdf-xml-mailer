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
  um token, criptografado pelo Windows para o seu usuário, em `%LOCALAPPDATA%\EnviadorEmails\token_cache.bin`.
- **Para e Cco** ficam em `%APPDATA%\EnviadorEmails\config.json`, fora do programa e do repositório.
- Assunto e corpo ficam no mesmo `config.json`; o texto padrão está em `core/modelo.py`.
- Conexão sempre com TLS. Nenhuma porta é aberta no computador.
- A atualização automática só instala o `.exe` novo se o SHA-256 bater com o publicado na Release.

## Pré-requisitos no Microsoft 365 (uma vez, pela TI)

1. **Entra ID → Registros de aplicativo → Novo registro**: tipo de conta "somente este diretório".
2. **Autenticação**: adicionar plataforma "Aplicativos móveis e da área de trabalho" com o URI
   `http://localhost` e ativar "Permitir fluxos de cliente público".
3. **Permissões de API**: Office 365 Exchange Online → permissão delegada `SMTP.Send` → conceder consentimento.
4. Copiar o **ID do aplicativo (cliente)** e o **ID do diretório (locatário)** para `CLIENT_ID` e `TENANT_ID`
   em `core/modelo.py` e lançar uma versão.
5. Nas caixas que vão enviar: **SMTP autenticado** habilitado (Exchange → Caixa de correio → E-mail → Aplicativos de e-mail).

Sem os IDs, o programa abre, mas o login avisa "Fale com a TI".

## Atualização automática

Ao abrir, o programa consulta a última Release no GitHub. Se houver versão nova, aparece o aviso
**Nova versão disponível**: em **Atualizar** ele baixa o novo `.exe`, confere o SHA-256 e reabre já atualizado.
Sem internet, nada aparece. Se um envio estiver em andamento, o aviso espera ele terminar.

## Desenvolver

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
python -m pytest
```

Modo terminal (usa a conta e o Para/Cco salvos pelo programa):

```
python -m core "C:\Pasta" --vcto 20/11/2026 --dry-run
python -m core "C:\Pasta" --vcto 20/11/2026 [--cco copia@empresa.com.br]
```

## Lançar uma versão

```
git tag v1.1.0
git push origin v1.1.0
```

O GitHub Actions roda os testes, gera o `.exe` e publica na Release (`.github/workflows/release.yml`).
Antes, ele confere `core/modelo.py`: a release **falha** se `CLIENT_ID`/`TENANT_ID` estiverem vazios.
A versão exibida no app vem da tag.

## Estrutura

| Pasta/arquivo | Conteúdo |
|---|---|
| `core/modelo.py` | Assunto e corpo padrão, SMTP e IDs do registro Microsoft |
| `core/envio.py` | Pares, validação, mensagem, SMTP (XOAUTH2), envio do lote, movimentação |
| `core/conta.py` | Login Microsoft (MSAL) e cache criptografado do token |
| `core/configuracao.py` | Para, Cco, assunto e corpo do usuário (`config.json`) |
| `core/worker.py` | Login e envio em segundo plano para a janela |
| `core/cli.py` | Modo terminal (`python -m core`) |
| `core/atualizacao.py` | Busca, download e instalação de nova versão |
| `ui/` | Design System (tokens, QSS, componentes, ícones), modal de conta e de atualização |
| `main.py` | Aplicação |
| `EnviadorEmails.spec` | Configuração do PyInstaller |
| `tests/` | Testes (`python -m pytest`) |
