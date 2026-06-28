# ============================================================
# pdf_report.py
# B3 FUNDAMENTALISTA ENGINE
# Relatório Institucional em PDF — Versão 2.0
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


# ============================================================
# PATHS
# ============================================================

OUTPUT_DIR = Path("output")
PDF_FILE = OUTPUT_DIR / "relatorio_institucional_b3.pdf"

CARTEIRA_FILE = OUTPUT_DIR / "carteira_institucional.csv"
DIVERSIFICADA_FILE = OUTPUT_DIR / "carteira_diversificada.csv"
AUDITORIA_FILE = OUTPUT_DIR / "auditoria_ia.txt"

GRAFICO_SETOR = OUTPUT_DIR / "grafico_setor.png"
GRAFICO_PESOS = OUTPUT_DIR / "grafico_pesos.png"
GRAFICO_DECISAO = OUTPUT_DIR / "grafico_decisao.png"
GRAFICO_SCORE = OUTPUT_DIR / "grafico_score.png"


# ============================================================
# CORES
# ============================================================

COR_PRIMARIA = colors.HexColor("#0f172a")
COR_SECUNDARIA = colors.HexColor("#1e293b")
COR_AZUL = colors.HexColor("#2563eb")
COR_VERDE = colors.HexColor("#16a34a")
COR_AMARELO = colors.HexColor("#ca8a04")
COR_VERMELHO = colors.HexColor("#dc2626")
COR_CINZA = colors.HexColor("#f3f4f6")
COR_CINZA_2 = colors.HexColor("#e5e7eb")
COR_TEXTO = colors.HexColor("#111827")


# ============================================================
# UTILITÁRIOS
# ============================================================

def carregar_csv(caminho):
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()

    return pd.read_csv(caminho, encoding="utf-8-sig")


def ler_texto(caminho):
    if not caminho.exists():
        return "Arquivo não encontrado."

    return caminho.read_text(encoding="utf-8", errors="ignore")


def numero_seguro(valor, default=0.0):
    try:
        return float(valor)
    except Exception:
        return default


def texto_seguro(valor):
    if pd.isna(valor):
        return ""
    return str(valor)


def limpar_texto_para_pdf(texto):
    texto = str(texto or "")
    texto = texto.replace("&", "&amp;")
    texto = texto.replace("<", "&lt;")
    texto = texto.replace(">", "&gt;")
    return texto


def pct(valor):
    return f"{numero_seguro(valor):.2f}%"


def fmt(valor):
    return f"{numero_seguro(valor):.2f}"


# ============================================================
# MÉTRICAS
# ============================================================

def calcular_metricas(df):
    if df.empty:
        return {
            "qtd_ativos": 0,
            "peso_total": 0,
            "melhor_ativo": "N/A",
            "score_medio": 0,
            "peso_top5": 0,
            "qtd_setores": 0,
            "maior_setor": "N/A",
            "peso_maior_setor": 0,
            "decisao_top1": "N/A",
            "nota_visual": "N/A",
        }

    qtd_ativos = len(df)

    peso_total = (
        df["peso_sugerido_pct"].sum()
        if "peso_sugerido_pct" in df.columns
        else 0
    )

    melhor_ativo = (
        str(df.iloc[0]["ticker"])
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

    maior_setor = "N/A"
    peso_maior_setor = 0

    if "setor" in df.columns and "peso_sugerido_pct" in df.columns:
        setor = (
            df.groupby("setor")["peso_sugerido_pct"]
            .sum()
            .sort_values(ascending=False)
        )

        if not setor.empty:
            maior_setor = str(setor.index[0])
            peso_maior_setor = float(setor.iloc[0])

    decisao_top1 = (
        str(df.iloc[0]["decisao"])
        if "decisao" in df.columns and not df.empty
        else "N/A"
    )

    # Nota visual simples, só para dashboard. A auditoria IA continua sendo a fonte qualitativa.
    nota_visual = min(max(score_medio / 10, 0), 10)

    return {
        "qtd_ativos": qtd_ativos,
        "peso_total": peso_total,
        "melhor_ativo": melhor_ativo,
        "score_medio": score_medio,
        "peso_top5": peso_top5,
        "qtd_setores": qtd_setores,
        "maior_setor": maior_setor,
        "peso_maior_setor": peso_maior_setor,
        "decisao_top1": decisao_top1,
        "nota_visual": nota_visual,
    }


# ============================================================
# GRÁFICOS
# ============================================================

def salvar_grafico(path):
    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()


def criar_grafico_setor(df):
    if df.empty or "setor" not in df.columns or "peso_sugerido_pct" not in df.columns:
        return None

    dados = (
        df.groupby("setor")["peso_sugerido_pct"]
        .sum()
        .sort_values(ascending=False)
    )

    top = dados.head(7).copy()
    outros = dados.iloc[7:].sum()

    if outros > 0:
        top.loc["Outros"] = outros

    top = top.sort_values(ascending=True)

    plt.figure(figsize=(10, 6))
    bars = plt.barh(top.index, top.values)

    plt.title("Exposição Setorial da Carteira", fontsize=14, fontweight="bold")
    plt.xlabel("Peso na carteira (%)", fontsize=11)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=9)
    plt.grid(axis="x", alpha=0.25)

    for bar in bars:
        largura = bar.get_width()
        plt.text(
            largura + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{largura:.1f}%",
            va="center",
            fontsize=9,
        )

    salvar_grafico(GRAFICO_SETOR)
    return GRAFICO_SETOR


def criar_grafico_pesos(df):
    if df.empty or "ticker" not in df.columns or "peso_sugerido_pct" not in df.columns:
        return None

    dados = (
        df.sort_values("peso_sugerido_pct", ascending=False)
        .head(10)
        .sort_values("peso_sugerido_pct", ascending=True)
    )

    plt.figure(figsize=(10, 6))
    bars = plt.barh(dados["ticker"], dados["peso_sugerido_pct"])

    plt.title("Top 10 Pesos por Ativo", fontsize=14, fontweight="bold")
    plt.xlabel("Peso na carteira (%)", fontsize=11)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis="x", alpha=0.25)

    for bar in bars:
        largura = bar.get_width()
        plt.text(
            largura + 0.2,
            bar.get_y() + bar.get_height() / 2,
            f"{largura:.1f}%",
            va="center",
            fontsize=9,
        )

    salvar_grafico(GRAFICO_PESOS)
    return GRAFICO_PESOS


def criar_grafico_decisao(df):
    if df.empty or "decisao" not in df.columns:
        return None

    dados = df["decisao"].value_counts().sort_values(ascending=True)

    plt.figure(figsize=(10, 5))
    bars = plt.barh(dados.index, dados.values)

    plt.title("Distribuição por Decisão", fontsize=14, fontweight="bold")
    plt.xlabel("Quantidade de ativos", fontsize=11)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=9)
    plt.grid(axis="x", alpha=0.25)

    for bar in bars:
        largura = bar.get_width()
        plt.text(
            largura + 0.05,
            bar.get_y() + bar.get_height() / 2,
            f"{int(largura)}",
            va="center",
            fontsize=9,
        )

    salvar_grafico(GRAFICO_DECISAO)
    return GRAFICO_DECISAO


def criar_grafico_score(df):
    if df.empty or "ticker" not in df.columns or "score_final_carteira" not in df.columns:
        return None

    dados = (
        df.sort_values("score_final_carteira", ascending=False)
        .head(10)
        .sort_values("score_final_carteira", ascending=True)
    )

    plt.figure(figsize=(10, 6))
    bars = plt.barh(dados["ticker"], dados["score_final_carteira"])

    plt.title("Top 10 Scores da Carteira", fontsize=14, fontweight="bold")
    plt.xlabel("Score final", fontsize=11)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.grid(axis="x", alpha=0.25)

    for bar in bars:
        largura = bar.get_width()
        plt.text(
            largura + 0.5,
            bar.get_y() + bar.get_height() / 2,
            f"{largura:.1f}",
            va="center",
            fontsize=9,
        )

    salvar_grafico(GRAFICO_SCORE)
    return GRAFICO_SCORE


# ============================================================
# TABELAS
# ============================================================

def montar_tabela_top5(df):
    if df.empty:
        return [["Ticker", "Score", "Peso na Carteira", "Decisão"], ["-", "-", "-", "-"]]

    colunas = ["ticker", "score_final_carteira", "peso_sugerido_pct", "decisao"]
    colunas = [c for c in colunas if c in df.columns]

    tabela = [["Ticker", "Score", "Peso na Carteira", "Decisão"]]

    for _, row in df.head(5).iterrows():
        tabela.append([
            texto_seguro(row.get("ticker", "")),
            fmt(row.get("score_final_carteira", 0)),
            pct(row.get("peso_sugerido_pct", 0)),
            texto_seguro(row.get("decisao", "")),
        ])

    return tabela


def montar_tabela_carteira(df):
    if df.empty:
        return [["Sem dados disponíveis"]]

    colunas = [
        "ranking_carteira",
        "ticker",
        "setor",
        "rating_carteira",
        "conviccao",
        "score_final_carteira",
        "peso_sugerido_pct",
        "decisao",
    ]

    colunas = [c for c in colunas if c in df.columns]

    nomes = {
        "ranking_carteira": "Rank",
        "ticker": "Ticker",
        "setor": "Setor",
        "rating_carteira": "Rating",
        "conviccao": "Convicção",
        "score_final_carteira": "Score",
        "peso_sugerido_pct": "Peso na Carteira",
        "decisao": "Decisão",
    }

    tabela = [[nomes.get(c, c) for c in colunas]]

    for _, row in df[colunas].head(20).iterrows():
        linha = []

        for col in colunas:
            valor = row.get(col, "")

            if col == "score_final_carteira":
                valor = fmt(valor)

            if col == "peso_sugerido_pct":
                valor = pct(valor)

            linha.append(texto_seguro(valor))

        tabela.append(linha)

    return tabela


# ============================================================
# DASHBOARD
# ============================================================

def criar_card(titulo, valor, descricao=""):
    style_t = ParagraphStyle(
        "card_title",
        fontSize=8,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=10,
    )

    style_v = ParagraphStyle(
        "card_value",
        fontSize=16,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=20,
    )

    style_d = ParagraphStyle(
        "card_desc",
        fontSize=7,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=9,
    )

    return [
        Paragraph(f"<b>{titulo}</b>", style_t),
        Paragraph(str(valor), style_v),
        Paragraph(descricao, style_d),
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

    tabela = Table(dados, colWidths=[5.6 * cm, 5.6 * cm, 5.6 * cm])

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COR_SECUNDARIA),
        ("BOX", (0, 0), (-1, -1), 0.5, COR_PRIMARIA),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    return tabela


# ============================================================
# RODAPÉ
# ============================================================

def rodape(canvas, doc):
    canvas.saveState()
    largura, _ = A4
    data = datetime.now().strftime("%d/%m/%Y")

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#6b7280"))

    canvas.drawString(1.4 * cm, 0.8 * cm, "B3 Fundamentalista Engine")
    canvas.drawCentredString(largura / 2, 0.8 * cm, f"Relatório institucional | {data}")
    canvas.drawRightString(largura - 1.4 * cm, 0.8 * cm, f"Página {doc.page}")

    canvas.restoreState()


# ============================================================
# PDF
# ============================================================

def gerar_pdf_institucional():
    OUTPUT_DIR.mkdir(exist_ok=True)

    carteira = carregar_csv(CARTEIRA_FILE)
    diversificada = carregar_csv(DIVERSIFICADA_FILE)

    base_relatorio = diversificada if not diversificada.empty else carteira
    auditoria = ler_texto(AUDITORIA_FILE)

    metricas = calcular_metricas(base_relatorio)

    grafico_setor = criar_grafico_setor(base_relatorio)
    grafico_pesos = criar_grafico_pesos(base_relatorio)
    grafico_decisao = criar_grafico_decisao(base_relatorio)
    grafico_score = criar_grafico_score(base_relatorio)

    doc = SimpleDocTemplate(
        str(PDF_FILE),
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
    )

    styles = getSampleStyleSheet()

    titulo_capa = ParagraphStyle(
        "TituloCapa",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=24,
        leading=30,
        textColor=COR_PRIMARIA,
        spaceAfter=18,
    )

    subtitulo_capa = ParagraphStyle(
        "SubtituloCapa",
        parent=styles["Heading2"],
        alignment=TA_CENTER,
        fontSize=15,
        leading=20,
        textColor=COR_SECUNDARIA,
        spaceAfter=12,
    )

    secao = ParagraphStyle(
        "Secao",
        parent=styles["Heading2"],
        alignment=TA_LEFT,
        fontSize=15,
        leading=20,
        textColor=COR_PRIMARIA,
        spaceBefore=10,
        spaceAfter=8,
    )

    texto = ParagraphStyle(
        "Texto",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        alignment=TA_LEFT,
        textColor=COR_TEXTO,
    )

    texto_pequeno = ParagraphStyle(
        "TextoPequeno",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        alignment=TA_LEFT,
        textColor=COR_TEXTO,
    )

    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["BodyText"],
        fontSize=7,
        leading=10,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#374151"),
    )

    elementos = []

    # CAPA
    elementos.append(Spacer(1, 3.4 * cm))
    elementos.append(Paragraph("B3 FUNDAMENTALISTA ENGINE", titulo_capa))
    elementos.append(Paragraph("RELATÓRIO INSTITUCIONAL DE CARTEIRA", subtitulo_capa))
    elementos.append(Spacer(1, 0.5 * cm))

    capa_info = f"""
    Carteira Quantitativa Brasileira<br/>
    Data de geração: <b>{datetime.now().strftime('%d/%m/%Y %H:%M')}</b><br/>
    Execução automática via GitHub Actions<br/>
    Auditoria assistida por Inteligência Artificial
    """

    elementos.append(Paragraph(capa_info, texto))
    elementos.append(Spacer(1, 1 * cm))

    capa_box = Table(
        [[
            Paragraph("<b>Processo</b><br/>Fundamentalista + Técnico + Diversificação + IA", texto_pequeno),
            Paragraph("<b>Entrega</b><br/>Relatório PDF institucional", texto_pequeno),
            Paragraph("<b>Uso</b><br/>Apoio à análise e priorização", texto_pequeno),
        ]],
        colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm],
    )

    capa_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COR_CINZA),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    elementos.append(capa_box)
    elementos.append(Spacer(1, 1.5 * cm))
    elementos.append(Paragraph("Documento gerado automaticamente. Uso educacional e analítico.", disclaimer_style))
    elementos.append(PageBreak())

    # ÍNDICE
    elementos.append(Paragraph("Índice", secao))

    indice = [
        ["1", "Resumo Executivo"],
        ["2", "Dashboard da Carteira"],
        ["3", "Carteira Sugerida"],
        ["4", "Gráficos Institucionais"],
        ["5", "Auditoria Institucional com IA"],
        ["6", "Metodologia"],
        ["7", "Conclusão e Disclaimer"],
    ]

    tabela_indice = Table(indice, colWidths=[1 * cm, 15 * cm])
    tabela_indice.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(tabela_indice)
    elementos.append(PageBreak())

    # RESUMO
    elementos.append(Paragraph("1. Resumo Executivo", secao))

    resumo = f"""
    Este relatório consolida a execução automática do <b>B3 Fundamentalista Engine</b>.
    O motor seleciona empresas com base em fundamentos, avalia o momento técnico,
    monta a carteira institucional, aplica diversificação e gera auditoria com IA.
    <br/><br/>
    A carteira final contém <b>{metricas['qtd_ativos']}</b> ativos,
    distribuídos em <b>{metricas['qtd_setores']}</b> setores,
    com peso total alocado de <b>{metricas['peso_total']:.2f}%</b>.
    O principal ativo ranqueado no processo atual é <b>{metricas['melhor_ativo']}</b>.
    <br/><br/>
    A coluna <b>Peso na Carteira</b> representa o percentual sugerido de alocação
    de cada ativo dentro da carteira final. Exemplo: um peso de 9,85% indica que,
    a cada R$ 100.000 alocados na carteira, aproximadamente R$ 9.850 seriam destinados
    ao respectivo ativo.
    """

    elementos.append(Paragraph(resumo, texto))
    elementos.append(Spacer(1, 0.4 * cm))

    elementos.append(Paragraph("Top 5 Ativos da Carteira", secao))

    top5 = Table(montar_tabela_top5(base_relatorio), repeatRows=1)
    top5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_CINZA]),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    elementos.append(top5)
    elementos.append(PageBreak())

    # DASHBOARD
    elementos.append(Paragraph("2. Dashboard da Carteira", secao))
    elementos.append(montar_dashboard(metricas))
    elementos.append(Spacer(1, 0.5 * cm))

    leitura_dashboard = f"""
    Maior setor: <b>{metricas['maior_setor']}</b> com <b>{metricas['peso_maior_setor']:.2f}%</b> de peso.
    Peso consolidado dos 5 maiores ativos: <b>{metricas['peso_top5']:.2f}%</b>.
    Decisão do ativo principal: <b>{metricas['decisao_top1']}</b>.
    """

    elementos.append(Paragraph(leitura_dashboard, texto))
    elementos.append(PageBreak())

    # CARTEIRA
    elementos.append(Paragraph("3. Carteira Sugerida", secao))

    tabela_dados = montar_tabela_carteira(base_relatorio)

    tabela = Table(
        tabela_dados,
        repeatRows=1,
        colWidths=[1 * cm, 1.5 * cm, 3.1 * cm, 1.3 * cm, 1.8 * cm, 1.5 * cm, 2.3 * cm, 3.5 * cm],
    )

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6.2),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_CINZA]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    elementos.append(tabela)
    elementos.append(PageBreak())

    # GRÁFICOS
    elementos.append(Paragraph("4. Gráficos Institucionais", secao))

    if grafico_setor:
        elementos.append(Paragraph("<b>Exposição por setor</b><br/>Mostra a participação de cada setor no peso total da carteira.", texto))
        elementos.append(Image(str(grafico_setor), width=16 * cm, height=9 * cm))
        elementos.append(Spacer(1, 0.4 * cm))

    if grafico_pesos:
        elementos.append(Paragraph("<b>Peso sugerido por ativo</b><br/>Mostra os 10 maiores pesos individuais dentro da carteira final.", texto))
        elementos.append(Image(str(grafico_pesos), width=16 * cm, height=9 * cm))
        elementos.append(PageBreak())

    if grafico_score:
        elementos.append(Paragraph("<b>Score final por ativo</b><br/>Mostra os 10 maiores scores combinados entre fundamentos e análise técnica.", texto))
        elementos.append(Image(str(grafico_score), width=16 * cm, height=9 * cm))
        elementos.append(Spacer(1, 0.4 * cm))

    if grafico_decisao:
        elementos.append(Paragraph("<b>Distribuição por decisão</b><br/>Mostra quantos ativos estão classificados em cada decisão operacional.", texto))
        elementos.append(Image(str(grafico_decisao), width=16 * cm, height=8 * cm))
        elementos.append(PageBreak())

    # AUDITORIA
    elementos.append(Paragraph("5. Auditoria Institucional com IA", secao))

    auditoria_limpa = limpar_texto_para_pdf(auditoria)

    for bloco in auditoria_limpa.split("\n"):
        bloco = bloco.strip()

        if not bloco:
            continue

        if bloco.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.")):
            elementos.append(Spacer(1, 0.15 * cm))
            elementos.append(Paragraph(f"<b>{bloco}</b>", texto))
        elif bloco.startswith("-") or bloco.startswith("•"):
            bloco = bloco.replace("•", "").replace("-", "").strip()
            elementos.append(Paragraph(f"• {bloco}", texto))
        else:
            elementos.append(Paragraph(bloco, texto))

        elementos.append(Spacer(1, 0.08 * cm))

    elementos.append(PageBreak())

    # METODOLOGIA
    elementos.append(Paragraph("6. Metodologia", secao))

    metodologia = """
    O B3 Fundamentalista Engine utiliza uma arquitetura quantitativa em camadas.
    A primeira camada coleta e estrutura dados de empresas listadas na B3.
    A segunda camada calcula indicadores fundamentalistas, como rentabilidade,
    crescimento, valuation, alavancagem e moat. A terceira camada seleciona
    empresas com maior qualidade fundamentalista. Em seguida, o motor técnico
    avalia o momento de entrada com base em tendência, médias móveis, momentum,
    volatilidade e força relativa.
    <br/><br/>
    O score final da carteira combina predominantemente fundamentos com uma camada
    técnica de timing. A diversificação busca reduzir concentração setorial.
    Por fim, a auditoria com IA revisa a coerência do processo, os principais
    riscos e os pontos de atenção.
    """

    elementos.append(Paragraph(metodologia, texto))
    elementos.append(PageBreak())

    # CONCLUSÃO
    elementos.append(Paragraph("7. Conclusão e Disclaimer", secao))

    conclusao = """
    O relatório apresenta uma carteira construída por processo quantitativo,
    com combinação entre análise fundamentalista, análise técnica, controle
    de diversificação e auditoria por inteligência artificial.
    <br/><br/>
    Este documento não representa recomendação absoluta de compra ou venda.
    Ele serve como apoio institucional à análise, priorização e acompanhamento
    de oportunidades na B3.
    <br/><br/>
    Rentabilidade passada não garante rentabilidade futura.
    A decisão final de investimento deve considerar perfil de risco,
    horizonte de investimento, liquidez, tributação e objetivos individuais.
    """

    elementos.append(Paragraph(conclusao, texto))
    elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(Paragraph("Fim do relatório.", texto_pequeno))

    doc.build(
        elementos,
        onFirstPage=rodape,
        onLaterPages=rodape,
    )

    print("=" * 70)
    print("PDF INSTITUCIONAL GERADO")
    print("=" * 70)
    print(PDF_FILE)

    return PDF_FILE


if __name__ == "__main__":
    gerar_pdf_institucional()
