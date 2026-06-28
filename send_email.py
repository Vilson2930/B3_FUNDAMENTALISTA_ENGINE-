# ============================================================
# send_email.py
# B3 FUNDAMENTALISTA ENGINE
# Envio automático do relatório institucional em PDF
# ============================================================

import os
import smtplib
from pathlib import Path
from email.message import EmailMessage


OUTPUT_DIR = Path("output")
PDF_FILE = OUTPUT_DIR / "relatorio_institucional_b3.pdf"


def anexar_arquivo(msg, caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado para anexo: {caminho}")

    with open(caminho, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=caminho.name
        )


def main():
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("EMAIL_TO")

    if not all([smtp_server, smtp_user, smtp_password, email_to]):
        raise Exception("Secrets de e-mail não configurados corretamente.")

    if not PDF_FILE.exists():
        raise FileNotFoundError(
            "PDF institucional não encontrado. Verifique se engine/pdf_report.py rodou antes do envio."
        )

    msg = EmailMessage()
    msg["Subject"] = "Relatório Institucional B3 Fundamentalista Engine"
    msg["From"] = smtp_user
    msg["To"] = email_to

    corpo = """
B3 FUNDAMENTALISTA ENGINE

Execução automática concluída com sucesso.

Segue em anexo o relatório institucional em PDF, contendo:

- Capa
- Resumo executivo
- Carteira sugerida
- Gráficos
- Auditoria da IA
- Conclusão

Gerado automaticamente pelo GitHub Actions.
"""

    msg.set_content(corpo)

    anexar_arquivo(msg, PDF_FILE)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    print("E-mail enviado com sucesso com PDF institucional.")


if __name__ == "__main__":
    main()
