# ============================================================
# pdf_report.py
# B3 FUNDAMENTALISTA ENGINE
# Relatório Institucional em PDF
# ============================================================

from pathlib import Path
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)


OUTPUT_DIR = Path("output")
PDF_FILE = OUTPUT_DIR / "relatorio_institucional_b3.pdf"

CARTEIRA_FILE = OUTPUT_DIR / "carteira_institucional.csv"
DIVERSIFICADA_FILE = OUTPUT_DIR / "carteira_diversificada.csv"
AUDITORIA_FILE = OUTPUT_DIR / "auditoria_ia.txt"
REPORT_FILE = OUTPUT_DIR / "report.txt"

GRAFICO_SETOR = OUTPUT_DIR / "grafico_setor.png"
GRAFICO_PESOS = OUTPUT_DIR / "grafico_pesos.png"


def carregar_csv(caminho):
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()

    return pd.read_csv(caminho, encoding="utf-8-sig")


def ler_texto(caminho):
    if not caminho.exists():
        return "Arquivo não encontrado."

    return caminho.read_text(encoding="utf-8", errors="ignore")


def criar_grafico_setor(df):
    if df.empty or "setor" not in df.columns or "peso_sugerido_pct" not in df.columns:
        return None

    dados = (
        df.groupby("setor")["peso_sugerido_pct"]
        .sum()
        .sort_values(ascending=True)
    )

    plt.figure(figsize=(8, 5))
    dados.plot(kind="barh")
    plt.title("Exposição por Setor")
    plt.xlabel("Peso (%)")
    plt.tight_layout()
    plt.savefig(GRAFICO_SETOR, dpi=150)
    plt.close()

    return GRAFICO_SETOR


def criar_grafico_pesos(df):
    if df.empty or "ticker" not in df.columns or "peso_sugerido_pct" not in df.columns:
        return None

    dados = df.sort_values("peso_sugerido_pct", ascending=True).tail(15)

    plt.figure(figsize=(8, 5))
    plt.barh(dados["ticker"], dados["peso_sugerido_pct"])
    plt.title("Peso Sugerido por Ativo")
    plt.xlabel("Peso (%)")
    plt.tight_layout()
    plt.savefig(GRAFICO_PESOS, dpi=150)
    plt.close()

    return GRAFICO_PESOS


def montar_tabela_carteira(df):
    if df.empty:
        return [["Sem dados disponíveis"]]

    colunas = [
        "ranking_carteira",
        "ticker",
        "setor",
        "score_final_carteira",
        "peso_sugerido_pct",
        "decisao",
    ]

    colunas = [c for c in colunas if c in df.columns]

    tabela = [colunas]

    for _, row in df[colunas].head(20).iterrows():
        linha = []

        for col in colunas:
            valor = row.get(col, "")

            if col in ["score_final_carteira", "peso_sugerido_pct"]:
                try:
                    valor = f"{float(valor):.2f}"
                except Exception:
                    valor = str(valor)

            linha.append(str(valor))

        tabela.append(linha)

    return tabela


def gerar_pdf_institucional():
    OUTPUT_DIR.mkdir(exist_ok=True)

    carteira = carregar_csv(CARTEIRA_FILE)
    diversificada = carregar_csv(DIVERSIFICADA_FILE)

    base_relatorio = diversificada if not diversificada.empty else carteira

    auditoria = ler_texto(AUDITORIA_FILE)

    grafico_setor = criar_grafico_setor(base_relatorio)
    grafico_pesos = criar_grafico_pesos(base_relatorio)

    doc = SimpleDocTemplate(
        str(PDF_FILE),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()

    titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=28,
        spaceAfter=20,
    )

    subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=styles["Heading2"],
        alignment=TA_LEFT,
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
    )

    texto = ParagraphStyle(
        "Texto",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        alignment=TA_LEFT,
    )

    pequeno = ParagraphStyle(
        "Pequeno",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
    )

    elementos = []

    # CAPA
    elementos.append(Spacer(1, 4 * cm))
    elementos.append(Paragraph("B3 FUNDAMENTALISTA ENGINE", titulo))
    elementos.append(Paragraph("Relatório Institucional de Carteira", styles["Heading2"]))
    elementos.append(Spacer(1, 1 * cm))
    elementos.append(Paragraph(f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}", texto))
    elementos.append(Spacer(1, 1 * cm))
    elementos.append(Paragraph("Relatório gerado automaticamente pelo GitHub Actions.", pequeno))
    elementos.append(PageBreak())

    # RESUMO EXECUTIVO
    elementos.append(Paragraph("1. Resumo Executivo", subtitulo))

    qtd_ativos = len(base_relatorio)

    peso_total = 0
    if "peso_sugerido_pct" in base_relatorio.columns:
        peso_total = base_relatorio["peso_sugerido_pct"].sum()

    melhor_ativo = "N/A"
    if not base_relatorio.empty and "ticker" in base_relatorio.columns:
        melhor_ativo = base_relatorio.iloc[0]["ticker"]

    resumo = f"""
    Este relatório consolida a execução automática do B3 Fundamentalista Engine.
    O motor seleciona empresas com base em fundamentos, avalia o momento técnico,
    monta a carteira institucional, aplica diversificação e gera uma auditoria com IA.
    <br/><br/>
    Quantidade de ativos na carteira final: <b>{qtd_ativos}</b><br/>
    Peso total alocado: <b>{peso_total:.2f}%</b><br/>
    Principal ativo ranqueado: <b>{melhor_ativo}</b><br/>
    """

    elementos.append(Paragraph(resumo, texto))
    elementos.append(Spacer(1, 0.5 * cm))

    # CARTEIRA
    elementos.append(Paragraph("2. Carteira Sugerida", subtitulo))

    tabela_dados = montar_tabela_carteira(base_relatorio)

    tabela = Table(tabela_dados, repeatRows=1)

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elementos.append(tabela)
    elementos.append(PageBreak())

    # GRÁFICOS
    elementos.append(Paragraph("3. Gráficos da Carteira", subtitulo))

    if grafico_setor:
        elementos.append(Paragraph("Exposição por setor", texto))
        elementos.append(Image(str(grafico_setor), width=16 * cm, height=10 * cm))
        elementos.append(Spacer(1, 0.5 * cm))

    if grafico_pesos:
        elementos.append(Paragraph("Peso sugerido por ativo", texto))
        elementos.append(Image(str(grafico_pesos), width=16 * cm, height=10 * cm))

    elementos.append(PageBreak())

    # AUDITORIA IA
    elementos.append(Paragraph("4. Auditoria Institucional com IA", subtitulo))

    for bloco in auditoria.split("\n"):
        bloco = bloco.strip()
        if bloco:
            elementos.append(Paragraph(bloco, texto))
            elementos.append(Spacer(1, 0.15 * cm))

    elementos.append(PageBreak())

    # CONCLUSÃO
    elementos.append(Paragraph("5. Conclusão", subtitulo))

    conclusao = """
    O relatório apresenta uma carteira construída por processo quantitativo,
    com combinação entre análise fundamentalista, análise técnica, controle
    de diversificação e auditoria por inteligência artificial.
    <br/><br/>
    Este documento não representa recomendação absoluta de compra ou venda.
    Ele serve como apoio institucional à análise, priorização e acompanhamento
    de oportunidades na B3.
    """

    elementos.append(Paragraph(conclusao, texto))

    doc.build(elementos)

    print("=" * 70)
    print("PDF INSTITUCIONAL GERADO")
    print("=" * 70)
    print(PDF_FILE)

    return PDF_FILE


if __name__ == "__main__":
    gerar_pdf_institucional()
