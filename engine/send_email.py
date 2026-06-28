import os
import smtplib
from pathlib import Path
from email.message import EmailMessage


OUTPUT_DIR = Path("output")


def anexar_arquivo(msg, caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        print(f"Arquivo não encontrado para anexo: {caminho}")
        return

    with open(caminho, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="octet-stream",
            filename=caminho.name
        )


def ler_texto(caminho, limite=5000):
    caminho = Path(caminho)

    if not caminho.exists():
        return "Auditoria IA não encontrada."

    texto = caminho.read_text(encoding="utf-8", errors="ignore")

    if len(texto) > limite:
        texto = texto[:limite] + "\n\n...[texto reduzido]"

    return texto


def main():
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("EMAIL_TO")

    if not all([smtp_server, smtp_user, smtp_password, email_to]):
        raise Exception("Secrets de e-mail não configurados corretamente.")

    auditoria = ler_texto(OUTPUT_DIR / "auditoria_ia.txt")

    msg = EmailMessage()
    msg["Subject"] = "Relatório B3 Full Portfolio Pipeline"
    msg["From"] = smtp_user
    msg["To"] = email_to

    corpo = f"""
B3 FUNDAMENTALISTA ENGINE

Execução automática concluída com sucesso.

============================================================
AUDITORIA IA
============================================================

{auditoria}

============================================================

Arquivos anexos:
- report.txt
- auditoria_ia.txt
- top20_premium.csv
- top20_tecnico.csv
- carteira_institucional.csv
- carteira_diversificada.csv

Gerado automaticamente pelo GitHub Actions.
"""

    msg.set_content(corpo)

    arquivos = [
        OUTPUT_DIR / "report.txt",
        OUTPUT_DIR / "auditoria_ia.txt",
        OUTPUT_DIR / "top20_premium.csv",
        OUTPUT_DIR / "top20_tecnico.csv",
        OUTPUT_DIR / "carteira_institucional.csv",
        OUTPUT_DIR / "carteira_diversificada.csv",
    ]

    for arquivo in arquivos:
        anexar_arquivo(msg, arquivo)

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)

    print("E-mail enviado com sucesso.")


if __name__ == "__main__":
    main()
