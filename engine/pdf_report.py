# ============================================================
# pdf_report.py
# B3 FUNDAMENTALISTA ENGINE
# Relatório Institucional em PDF — Versão Profissional
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

GRAFICO_SETOR = OUTPUT_DIR / "grafico_setor.png"
GRAFICO_PESOS = OUTPUT_DIR / "grafico_pesos.png"
GRAFICO_SCORE = OUTPUT_DIR / "grafico_score.png"


COR_PRIMARIA = colors.HexColor("#111827")
COR_SECUNDARIA = colors.HexColor("#1f2937")
COR_AZUL = colors.HexColor("#2563eb")
COR_CINZA = colors.HexColor("#f3f4f6")
COR_VERDE = colors.HexColor("#16a34a")
COR_TEXTO = colors.HexColor("#111827")


def carregar_csv(caminho):
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()

    return pd.read_csv(caminho, encoding="utf-8-sig")


def ler_texto(caminho):
    if not caminho.exists():
        return "Arquivo não encontrado."

    return caminho.read_text(encoding="utf-8", errors="ignore")


def numero_seguro(valor, default=0):
    try:
        return float(valor)
    except Exception:
        return default


def calcular_metricas(df):
    if df.empty:
        return {
            "qtd_ativos": 0,
            "peso_total": 0,
            "melhor_ativo": "N/A",
            "score_medio": 0,
            "peso_top5": 0,
            "qtd_setores": 0,
        }

    qtd_ativos = len(df)

    peso_total = (
        df["peso_sugerido_pct"].sum()
        if "peso_sugerido_pct" in df.columns
        else 0
    )

    melhor_ativo = (
        df.iloc[0]["ticker"]
        if "ticker" in df.columns and not df.empty
        else "N/A"
    )

    score_medio = (
        df["score_final_carteira"].mean()
        if "score_final_carteira" in df.columns
        else 0
    )

    peso_top5 = (
        df.head(5)["peso_sugerido_pct"].sum()
        if "peso_sugerido_pct" in df.columns
        else 0
    )

    qtd_setores = (
        df["setor"].nunique()
        if "setor" in df.columns
        else 0
    )

    return {
        "qtd_ativos": qtd_ativos,
        "peso_total": peso_total,
        "melhor_ativo": melhor_ativo,
        "score_medio": score_medio,
        "peso_top5": peso_top5,
        "qtd_setores": qtd_setores,
    }


def criar_grafico_setor(df):
    if df.empty or "setor" not in df.columns or "peso_sugerido_pct" not in df.columns:
        return None

    dados = (
        df.groupby("setor")["peso_sugerido_pct"]
        .sum()
        .sort_values(ascending=True)
    )

    plt.figure(figsize=(8, 5))
    plt.barh(dados.index, dados.values)
    plt.title("Exposição por Setor")
    plt.xlabel("Peso (%)")
    plt.tight_layout()
    plt.savefig(GRAFICO_SETOR, dpi=180)
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
    plt.savefig(GRAFICO_PESOS, dpi=180)
    plt.close()

    return GRAFICO_PESOS


def criar_grafico_score(df):
    if df.empty or "ticker" not in df.columns or "score_final_carteira" not in df.columns:
        return None

    dados = df.sort_values("score_final_carteira", ascending=True).tail(15)

    plt.figure(figsize=(8, 5))
    plt.barh(dados["ticker"], dados["score_final_carteira"])
    plt.title("Score Final da Carteira")
    plt.xlabel("Score")
    plt.tight_layout()
    plt.savefig(GRAFICO_SCORE, dpi=180)
    plt.close()

    return GRAFICO_SCORE


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

    nomes = {
        "ranking_carteira": "Rank",
        "ticker": "Ticker",
        "setor": "Setor",
        "score_final_carteira": "Score",
        "peso_sugerido_pct": "Peso %",
        "decisao": "Decisão",
    }

    tabela = [[nomes.get(c, c) for c in colunas]]

    for _, row in df[colunas].head(20).iterrows():
        linha = []

        for col in colunas:
            valor = row.get(col, "")

            if col in ["score_final_carteira", "peso_sugerido_pct"]:
                valor = f"{numero_seguro(valor):.2f}"

            linha.append(str(valor))

        tabela.append(linha)

    return tabela


def criar_card(titulo, valor, descricao=""):
    return [
        Paragraph(f"<b>{titulo}</b>", ParagraphStyle(
            "CardTitulo",
            fontSize=8,
            textColor=colors.white,
            alignment=TA_CENTER,
            leading=10,
        )),
        Paragraph(str(valor), ParagraphStyle(
            "CardValor",
            fontSize=16,
            textColor=colors.white,
            alignment=TA_CENTER,
            leading=20,
        )),
        Paragraph(descricao, ParagraphStyle(
            "CardDesc",
            fontSize=7,
            textColor=colors.white,
            alignment=TA_CENTER,
            leading=9,
        )),
    ]


def montar_dashboard(metricas):
    dados = [
        [
            criar_card("ATIVOS", metricas["qtd_ativos"], "Carteira final"),
            criar_card("PESO TOTAL", f"{metricas['peso_total']:.1f}%", "Alocação"),
            criar_card("TOP 1", metricas["melhor_ativo"], "Principal ativo"),
        ],
        [
            criar_card("SCORE MÉDIO", f"{metricas['score_medio']:.1f}", "Qualidade geral"),
            criar_card("TOP 5", f"{metricas['peso_top5']:.1f}%", "Concentração"),
            criar_card("SETORES", metricas["qtd_setores"], "Diversificação"),
        ],
    ]

    tabela = Table(dados, colWidths=[5.7 * cm, 5.7 * cm, 5.7 * cm])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COR_SECUNDARIA),
        ("BOX", (0, 0), (-1, -1), 0.5, COR_PRIMARIA),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    return tabela


def limpar_texto_para_pdf(texto):
    texto = texto.replace("&", "&amp;")
    texto = texto.replace("<", "&lt;")
    texto = texto.replace(">", "&gt;")
    return texto
