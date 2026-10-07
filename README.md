# Enviador de PDF + XML por e-mail

Envia um e-mail para um destinatário fixo para cada par **PDF + XML de mesmo nome**.
O assunto muda apenas no nome do arquivo (`{nome}`); o corpo é sempre o mesmo
(`corpo.html`, com `corpo.txt` como versão em texto simples).

## Instalação

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    |  Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Configuração

1. Copie `config.exemplo.ini` para `config.ini` e preencha SMTP, usuário, remetente, destinatário e assunto.
   - Use `{nome}` no assunto, por exemplo: `assunto = EMPRESA - CTE {nome} - TEXTO FIXO`.
2. Edite o corpo do e-mail. **Mantenha os dois arquivos iguais**:
   - `corpo.html`: versão que os clientes de e-mail exibem (aceita negrito com `<b>`).
   - `corpo.txt`: versão em texto simples, usada como alternativa.
   - O vencimento usa o campo `{vcto}` nos dois arquivos. Na interface há um campo **Vencimento**
     (obrigatório); na linha de comando use `--vcto dd/mm/aaaa`. Se remover `{vcto}` dos arquivos,
     o campo some e o corpo passa a ser 100% fixo.

3. Guarde a **senha** no cofre do sistema (no Windows, o Gerenciador de Credenciais), sem escrevê-la em arquivo:
   ```bash
   python configurar_senha.py
   ```
   Para apagar depois: `python configurar_senha.py --remover`.

> Gmail/Office 365 geralmente exigem **senha de aplicativo** ou SMTP autenticado liberado.

## Segurança

- **A senha nunca fica em arquivo do projeto.** Ordem de busca: variável de ambiente
  `ENVIADOR_SMTP_SENHA` → cofre do sistema (`configurar_senha.py`) → pergunta no terminal
  (fica só na memória). Um `senha =` antigo no `config.ini` ainda funciona, mas gera aviso: apague-o.
- `config.ini` (e-mails, assunto) e os documentos reais (`*.pdf`, `*.xml`, `entrada/`, `enviados/`,
  `erros/`) estão no `.gitignore`. Antes de cada commit, rode `git status` e confira o que vai subir.
- Prefira um repositório **privado**: o código é de uso interno e o assunto/corpo podem citar a empresa.
- Se uma senha chegou a ser commitada, **troque a senha** e trate-a como vazada (apagar o commit
  depois não basta, o histórico e os forks continuam com ela).
- Use uma **senha de aplicativo** (ou conta de serviço) dedicada a este envio, nunca a senha pessoal.
- A interface escuta só em `127.0.0.1`, exige um token por execução e aceita só requisições locais,
  para que outro site aberto no navegador não consiga disparar e-mails. Não exponha a porta na rede.
- A tela recusa arquivos que não sejam PDF/XML de verdade.

## Uso com interface (recomendado)

```bash
python app.py
```

Abra <http://127.0.0.1:5055>, arraste os PDFs e XMLs, confira os pares, escolha o **Vencimento**
e clique em **Enviar e-mails**.
A tela só aceita conexões do próprio computador (127.0.0.1).

## Uso por linha de comando

Coloque os arquivos na pasta `entrada/`:

```bash
python enviar_emails.py --vcto 20/11/2026 --dry-run   # só lista os assuntos
python enviar_emails.py --vcto 20/11/2026             # envia
```

Enviados vão para `enviados/`, falhas para `erros/`, arquivos sem par ficam em `entrada/`.

## Estrutura

| Arquivo | Função |
|---|---|
| `enviador.py` | Lógica de envio (SMTP, montagem da mensagem) |
| `app.py` + `templates/index.html` | Interface web local |
| `enviar_emails.py` | Modo linha de comando por pasta |
| `configurar_senha.py` | Guarda/remove a senha SMTP no cofre do sistema |
| `config.exemplo.ini` | Modelo de configuração (sem senha) |
| `corpo.html` / `corpo.txt` | Corpo fixo do e-mail (HTML e texto simples) |
