# ============================================================
# send_email.py
# B3 FUNDAMENTALISTA ENGINE
# Envio Automático do Relatório Institucional
# ============================================================

import os
import smtplib
from pathlib import Path
from email.message import EmailMessage
from email.utils import formatdate


OUTPUT_DIR = Path("output")
PDF_FILE = OUTPUT_DIR / "relatorio_institucional_b3.pdf"


def anexar_pdf(msg, caminho_pdf):
    caminho_pdf = Path(caminho_pdf)

    if not caminho_pdf.exists():
        raise FileNotFoundError(
            f"PDF não encontrado: {caminho_pdf}"
        )

    with open(caminho_pdf, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=caminho_pdf.name,
        )


def main():

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("EMAIL_TO")

    if not all([
        smtp_server,
        smtp_port,
        smtp_user,
        smtp_password,
        email_to
    ]):
        raise Exception(
            "Secrets SMTP não configurados corretamente."
        )

    if not PDF_FILE.exists():
        raise FileNotFoundError(
            "Relatório PDF não encontrado."
        )

    msg = EmailMessage()

    msg["Subject"] = "B3 Fundamentalista Engine | Relatório Institucional"
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg["Date"] = formatdate(localtime=True)

    corpo = """
Olá,

A execução automática do B3 Fundamentalista Engine foi concluída com sucesso.

O relatório institucional em PDF está anexado.

O documento contém:

• Resumo Executivo

• Dashboard da Carteira

• Carteira Institucional

• Exposição Setorial

• Distribuição dos Pesos

• Auditoria Institucional com Inteligência Artificial

• Metodologia do Motor

• Conclusão Executiva

Este relatório é gerado automaticamente pelo GitHub Actions.

--------------------------------------------------------

B3 FUNDAMENTALISTA ENGINE
Institutional Portfolio Report

--------------------------------------------------------
"""

    msg.set_content(corpo)

    anexar_pdf(msg, PDF_FILE)

    print("=" * 70)
    print("ENVIANDO E-MAIL")
    print("=" * 70)
    print(f"Destino : {email_to}")
    print(f"Arquivo : {PDF_FILE.name}")

    with smtplib.SMTP(smtp_server, smtp_port) as server:

        server.starttls()

        server.login(
            smtp_user,
            smtp_password
        )

        server.send_message(msg)

    print("=" * 70)
    print("E-MAIL ENVIADO COM SUCESSO")
    print("=" * 70)


if __name__ == "__main__":
    main()
