"""Interface web local: arraste PDFs e XMLs, confira os pares e envie.

    python app.py
    # abra http://127.0.0.1:5055

Segurança: escuta só em 127.0.0.1; exige um token por execução (contra CSRF, isto é,
outro site aberto no navegador disparando e-mails); aceita só Host/Origin locais
(contra DNS rebinding); valida o tipo dos arquivos recebidos.
"""
import os
import secrets
import sys

from flask import Flask, abort, jsonify, render_template, request

import enviador

PORTA = 5055
HOSTS_PERMITIDOS = {f"127.0.0.1:{PORTA}", f"localhost:{PORTA}"}
TOKEN = secrets.token_urlsafe(32)  # novo a cada execução; só a página servida por este app o vê

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB por requisição (1 par)


@app.before_request
def proteger():
    if request.host not in HOSTS_PERMITIDOS:
        abort(403)
    if request.method == "POST":
        origem = request.headers.get("Origin")
        if origem and origem.split("://", 1)[-1] not in HOSTS_PERMITIDOS:
            abort(403)
        enviado = request.headers.get("X-Token", "")
        if not secrets.compare_digest(enviado.encode(), TOKEN.encode()):
            abort(403)


@app.after_request
def cabecalhos(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; "
        "base-uri 'none'; form-action 'self'"
    )
    return resp


@app.errorhandler(403)
def negado(_e):
    return jsonify(ok=False, erro="Acesso negado."), 403


@app.errorhandler(413)
def grande_demais(_e):
    return jsonify(ok=False, erro="Arquivos grandes demais (máximo de 25 MB por e-mail)."), 413


@app.get("/")
def index():
    return render_template("index.html", token=TOKEN)


@app.get("/config")
def config():
    """Dados não sensíveis para a tela mostrar a prévia do assunto."""
    try:
        cfg = enviador.carregar_config()
        exige_vcto = enviador.corpo_exige_vcto(enviador.carregar_corpo())
    except FileNotFoundError as e:
        return jsonify(erro=str(e)), 500
    return jsonify(
        assunto=cfg["email"]["assunto"],
        destinatario=cfg["email"]["destinatario"],
        intervalo=float(cfg["smtp"].get("intervalo_segundos", "2")),
        exige_vcto=exige_vcto,
    )


def _erro(msg, codigo=400):
    return jsonify(ok=False, erro=msg), codigo


@app.post("/enviar")
def enviar():
    """Recebe um par (nome + pdf + xml + vcto) e envia um e-mail."""
    nome = request.form.get("nome", "").strip()
    vcto = request.form.get("vcto", "").strip()
    pdf = request.files.get("pdf")
    xml = request.files.get("xml")
    if not nome or not pdf or not xml:
        return _erro("Envie o nome, o PDF e o XML.")

    nome_pdf = os.path.basename(pdf.filename or "")
    nome_xml = os.path.basename(xml.filename or "")
    if not nome_pdf.lower().endswith(".pdf") or not nome_xml.lower().endswith(".xml"):
        return _erro("Os arquivos precisam ser um .pdf e um .xml.")

    dados_pdf, dados_xml = pdf.read(), xml.read()
    if b"%PDF-" not in dados_pdf[:1024]:
        return _erro(f"{nome_pdf} não parece ser um PDF válido.")
    if not dados_xml.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"<"):
        return _erro(f"{nome_xml} não parece ser um XML válido.")

    try:
        cfg = enviador.carregar_config()
        corpo = enviador.carregar_corpo()
        enviador.enviar_par(cfg, corpo, nome, [(nome_pdf, dados_pdf), (nome_xml, dados_xml)], vcto)
    except ValueError as e:  # vencimento ausente/inválido
        return _erro(str(e))
    except Exception as e:  # noqa: BLE001
        return _erro(str(e), 500)
    return jsonify(ok=True)


if __name__ == "__main__":
    try:
        # Pergunta a senha agora, no terminal, e não no meio de um envio.
        enviador.obter_senha(enviador.carregar_config())
    except FileNotFoundError:
        pass  # a tela mostra o aviso de config.ini ausente
    except RuntimeError as e:
        sys.exit(str(e))
    # 127.0.0.1: acessível só deste computador (a tela dispara e-mails com a sua conta).
    app.run(host="127.0.0.1", port=PORTA, debug=False)
