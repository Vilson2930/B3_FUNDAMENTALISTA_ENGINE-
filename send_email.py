# ============================================================
# send_email.py
# B3 FUNDAMENTALISTA ENGINE
# Institutional Report Mailer
# ============================================================

import os
import smtplib
from pathlib import Path
from email.message import EmailMessage
from email.utils import formatdate


OUTPUT_DIR = Path("output")
PDF_FILE = OUTPUT_DIR / "relatorio_institucional_b3.pdf"


def anexar_pdf(msg, caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        raise FileNotFoundError(f"PDF não encontrado: {caminho}")

    with open(caminho, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=caminho.name,
        )


def main():

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("EMAIL_TO")

    if not all([smtp_server, smtp_user, smtp_password, email_to]):
        raise Exception("Configuração SMTP incompleta.")

    if not PDF_FILE.exists():
        raise FileNotFoundError(
            "Relatório institucional não encontrado."
        )

    msg = EmailMessage()

    msg["Subject"] = "B3 Fundamentalista Engine | Institutional Portfolio Report"
    msg["From"] = smtp_user
    msg["To"] = email_to
    msg["Date"] = formatdate(localtime=True)

    corpo = """
Olá,

O ciclo de processamento do B3 Fundamentalista Engine foi concluído com sucesso.

O relatório institucional em PDF segue anexado.

Conteúdo do relatório:

• Resumo Executivo

• Dashboard da Carteira

• Carteira Institucional

• Exposição Setorial

• Distribuição dos Pesos

• Auditoria Institucional com Inteligência Artificial

• Metodologia

• Conclusão Executiva

------------------------------------------------------------

Relatório gerado automaticamente pelo GitHub Actions.

B3 FUNDAMENTALISTA ENGINE
Institutional Portfolio Report

------------------------------------------------------------
"""

    msg.set_content(corpo)

    anexar_pdf(msg, PDF_FILE)

    print("=" * 70)
    print("ENVIANDO RELATÓRIO")
    print("=" * 70)
    print(f"Destino : {email_to}")
    print(f"Arquivo : {PDF_FILE.name}")

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    print("=" * 70)
    print("RELATÓRIO ENVIADO COM SUCESSO")
    print("=" * 70)


if __name__ == "__main__":
    main()
