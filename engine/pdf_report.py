# ============================================================
# pdf_report.py
# B3 FUNDAMENTALISTA ENGINE
# Relatorio Institucional em PDF — Versao Profissional
# ============================================================

from pathlib import Path
from datetime import datetime
import re

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
GRAFICO_SCORE = OUTPUT_DIR / "grafico_score.png"
GRAFICO_DECISAO = OUTPUT_DIR / "grafico_decisao.png"


# ============================================================
# CORES
# ============================================================

COR_PRIMARIA = colors.HexColor("#111827")
COR_SECUNDARIA = colors.HexColor("#1f2937")
COR_AZUL = colors.HexColor("#2563eb")
COR_CINZA = colors.HexColor("#f3f4f6")
COR_CINZA_BORDA = colors.HexColor("#d1d5db")
COR_VERDE = colors.HexColor("#16a34a")
COR_TEXTO = colors.HexColor("#111827")


# ============================================================
# UTILITARIOS
# ============================================================

def carregar_csv(caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        print(f"Arquivo nao encontrado: {caminho}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(caminho, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(caminho)

    df.columns = [str(c).strip() for c in df.columns]
    return df


def ler_texto(caminho):
    caminho = Path(caminho)

    if not caminho.exists():
        return "Arquivo de auditoria nao encontrado."

    return caminho.read_text(encoding="utf-8", errors="ignore")


def numero_seguro(valor, default=0.0):
    try:
        return float(valor)
    except Exception:
        return default


def limpar_texto_para_pdf(texto):
    texto = str(texto or "")
    texto = texto.replace("&", "&amp;")
    texto = texto.replace("<", "&lt;")
    texto = texto.replace(">", "&gt;")
    return texto


def normalizar_texto(texto):
    texto = str(texto or "")
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


# ============================================================
# METRICAS
# ============================================================

def calcular_metricas(df):
    if df.empty:
        return {
            "qtd_ativos": 0,
            "peso_total": 0.0,
            "melhor_ativo": "N/A",
            "score_medio": 0.0,
            "peso_top5": 0.0,
            "qtd_setores": 0,
            "decisao_principal": "N/A",
            "maior_setor": "N/A",
            "peso_maior_setor": 0.0,
        }

    qtd_ativos = len(df)

    peso_total = 0.0
    if "peso_sugerido_pct" in df.columns:
        peso_total = numero_seguro(df["peso_sugerido_pct"].sum())

    melhor_ativo = "N/A"
    if "ticker" in df.columns and len(df) > 0:
        melhor_ativo = str(df.iloc[0].get("ticker", "N/A"))

    score_medio = 0.0
    if "score_final_carteira" in df.columns:
        score_medio = numero_seguro(df["score_final_carteira"].mean())

    peso_top5 = 0.0
    if "peso_sugerido_pct" in df.columns:
        peso_top5 = numero_seguro(df.head(5)["peso_sugerido_pct"].sum())

    qtd_setores = 0
    maior_setor = "N/A"
    peso_maior_setor = 0.0

    if "setor" in df.columns:
        qtd_setores = int(df["setor"].nunique())

        if "peso_sugerido_pct" in df.columns:
            setores = df.groupby("setor")["peso_sugerido_pct"].sum().sort_values(ascending=False)
            if not setores.empty:
                maior_setor = str(setores.index[0])
                peso_maior_setor = numero_seguro(setores.iloc[0])

    decisao_principal = "N/A"
    if "decisao" in df.columns and len(df) > 0:
        decisao_principal = str(df.iloc[0].get("decisao", "N/A"))

    return {
        "qtd_ativos": qtd_ativos,
        "peso_total": peso_total,
        "melhor_ativo": melhor_ativo,
        "score_medio": score_medio,
        "peso_top5": peso_top5,
        "qtd_setores": qtd_setores,
        "decisao_principal": decisao_principal,
        "maior_setor": maior_setor,
        "peso_maior_setor": peso_maior_setor,
    }


# ============================================================
# GRAFICOS
# ============================================================

def criar_grafico_setor(df):
    if df.empty or "setor" not in df.columns or "peso_sugerido_pct" not in df.columns:
        return None

    dados = df.groupby("setor")["peso_sugerido_pct"].sum().sort_values(ascending=True)

    if dados.empty:
        return None

    plt.figure(figsize=(8.5, 5.2))
    plt.barh(dados.index, dados.values)
    plt.title("Exposicao por Setor")
    plt.xlabel("Peso (%)")
    plt.tight_layout()
    plt.savefig(GRAFICO_SETOR, dpi=180)
    plt.close()

    return GRAFICO_SETOR


def criar_grafico_pesos(df):
    if df.empty or "ticker" not in df.columns or "peso_sugerido_pct" not in df.columns:
        return None

    dados = df.sort_values("peso_sugerido_pct", ascending=True).tail(15)

    if dados.empty:
        return None

    plt.figure(figsize=(8.5, 5.2))
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

    if dados.empty:
        return None

    plt.figure(figsize=(8.5, 5.2))
    plt.barh(dados["ticker"], dados["score_final_carteira"])
    plt.title("Score Final por Ativo")
    plt.xlabel("Score")
    plt.tight_layout()
    plt.savefig(GRAFICO_SCORE, dpi=180)
    plt.close()

    return GRAFICO_SCORE


def criar_grafico_decisao(df):
    if df.empty or "decisao" not in df.columns:
        return None

    dados = df["decisao"].fillna("N/A").value_counts().sort_values(ascending=True)

    if dados.empty:
        return None

    plt.figure(figsize=(8.5, 5.2))
    plt.barh(dados.index, dados.values)
    plt.title("Distribuicao por Decisao")
    plt.xlabel("Quantidade de ativos")
    plt.tight_layout()
    plt.savefig(GRAFICO_DECISAO, dpi=180)
    plt.close()

    return GRAFICO_DECISAO


# ============================================================
# TABELAS
# ============================================================

def montar_tabela_carteira(df):
    if df.empty:
        return [["Sem dados disponiveis"]]

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
        "decisao": "Decisao",
    }

    tabela = [[nomes.get(c, c) for c in colunas]]

    for _, row in df[colunas].head(20).iterrows():
        linha = []

        for col in colunas:
            valor = row.get(col, "")

            if col in ["score_final_carteira", "peso_sugerido_pct"]:
                valor = f"{numero_seguro(valor):.2f}"

            linha.append(normalizar_texto(valor))

        tabela.append(linha)

    return tabela


def montar_top5(df):
    if df.empty:
        return [["Ticker", "Score", "Peso %", "Decisao"], ["N/A", "0", "0", "N/A"]]

    linhas = [["Ticker", "Score", "Peso %", "Decisao"]]

    for _, row in df.head(5).iterrows():
        linhas.append([
            str(row.get("ticker", "N/A")),
            f"{numero_seguro(row.get('score_final_carteira', 0)):.2f}",
            f"{numero_seguro(row.get('peso_sugerido_pct', 0)):.2f}",
            normalizar_texto(row.get("decisao", "N/A")),
        ])

    return linhas


# ============================================================
# COMPONENTES VISUAIS
# ============================================================

def criar_card(titulo, valor, descricao=""):
    style_titulo = ParagraphStyle(
        "CardTitulo",
        fontSize=8,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=10,
    )

    style_valor = ParagraphStyle(
        "CardValor",
        fontSize=16,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=20,
    )

    style_desc = ParagraphStyle(
        "CardDesc",
        fontSize=7,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=9,
    )

    return [
        Paragraph(f"<b>{limpar_texto_para_pdf(titulo)}</b>", style_titulo),
        Paragraph(limpar_texto_para_pdf(valor), style_valor),
        Paragraph(limpar_texto_para_pdf(descricao), style_desc),
    ]


def montar_dashboard(metricas):
    dados = [
        [
            criar_card("ATIVOS", metricas["qtd_ativos"], "Carteira final"),
            criar_card("PESO TOTAL", f"{metricas['peso_total']:.1f}%", "Alocacao"),
            criar_card("TOP 1", metricas["melhor_ativo"], "Principal ativo"),
        ],
        [
            criar_card("SCORE MEDIO", f"{metricas['score_medio']:.1f}", "Qualidade geral"),
            criar_card("TOP 5", f"{metricas['peso_top5']:.1f}%", "Concentracao"),
            criar_card("SETORES", metricas["qtd_setores"], "Diversificacao"),
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


# ============================================================
# PDF PRINCIPAL
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
    grafico_score = criar_grafico_score(base_relatorio)
    grafico_decisao = criar_grafico_decisao(base_relatorio)

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
    elementos.append(Paragraph("RELATORIO INSTITUCIONAL DE CARTEIRA", subtitulo_capa))
    elementos.append(Spacer(1, 0.5 * cm))

    capa_info = f"""
    Carteira Quantitativa Brasileira<br/>
    Data de geracao: <b>{datetime.now().strftime('%d/%m/%Y %H:%M')}</b><br/>
    Execucao automatica via GitHub Actions<br/>
    Auditoria assistida por Inteligencia Artificial
    """

    elementos.append(Paragraph(capa_info, texto))
    elementos.append(Spacer(1, 1 * cm))

    capa_box = Table(
        [[
            Paragraph("<b>Processo</b><br/>Fundamentalista + Tecnico + Diversificacao + IA", texto_pequeno),
            Paragraph("<b>Entrega</b><br/>Relatorio PDF institucional", texto_pequeno),
            Paragraph("<b>Uso</b><br/>Apoio a analise e priorizacao", texto_pequeno),
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
    elementos.append(Spacer(1, 1.4 * cm))
    elementos.append(Paragraph("Documento gerado automaticamente. Uso educacional e analitico.", disclaimer_style))
    elementos.append(PageBreak())

    # INDICE
    elementos.append(Paragraph("Indice", secao))

    indice = [
        ["1", "Resumo Executivo"],
        ["2", "Dashboard da Carteira"],
        ["3", "Carteira Sugerida"],
        ["4", "Graficos Institucionais"],
        ["5", "Auditoria Institucional com IA"],
        ["6", "Metodologia"],
        ["7", "Conclusao e Disclaimer"],
    ]

    tabela_indice = Table(indice, colWidths=[1 * cm, 15 * cm])
    tabela_indice.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, COR_CINZA_BORDA),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(tabela_indice)
    elementos.append(PageBreak())

    # RESUMO
    elementos.append(Paragraph("1. Resumo Executivo", secao))

    resumo = f"""
    Este relatorio consolida a execucao automatica do <b>B3 Fundamentalista Engine</b>.
    O motor seleciona empresas com base em fundamentos, avalia o momento tecnico,
    monta a carteira institucional, aplica diversificacao e gera auditoria com IA.
    <br/><br/>
    A carteira final contem <b>{metricas['qtd_ativos']}</b> ativos,
    distribuidos em <b>{metricas['qtd_setores']}</b> setores,
    com peso total alocado de <b>{metricas['peso_total']:.2f}%</b>.
    O principal ativo ranqueado no processo atual e <b>{metricas['melhor_ativo']}</b>.
    """

    elementos.append(Paragraph(resumo, texto))
    elementos.append(Spacer(1, 0.4 * cm))

    # TOP 5
    elementos.append(Paragraph("Top 5 Ativos da Carteira", secao))
    tabela_top5 = Table(montar_top5(base_relatorio), colWidths=[3 * cm, 3 * cm, 3 * cm, 7 * cm])
    tabela_top5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, COR_CINZA_BORDA),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_CINZA]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabela_top5)
    elementos.append(PageBreak())

    # DASHBOARD
    elementos.append(Paragraph("2. Dashboard da Carteira", secao))
    elementos.append(montar_dashboard(metricas))
    elementos.append(Spacer(1, 0.6 * cm))

    resumo_risco = f"""
    Maior setor: <b>{limpar_texto_para_pdf(metricas['maior_setor'])}</b>
    com <b>{metricas['peso_maior_setor']:.2f}%</b> de peso.
    Peso consolidado dos 5 maiores ativos: <b>{metricas['peso_top5']:.2f}%</b>.
    Decisao do ativo principal: <b>{limpar_texto_para_pdf(metricas['decisao_principal'])}</b>.
    """

    elementos.append(Paragraph(resumo_risco, texto))
    elementos.append(PageBreak())

    # CARTEIRA
    elementos.append(Paragraph("3. Carteira Sugerida", secao))

    tabela_dados = montar_tabela_carteira(base_relatorio)

    tabela = Table(
        tabela_dados,
        repeatRows=1,
        colWidths=[1.2 * cm, 1.8 * cm, 4 * cm, 2 * cm, 2 * cm, 5.3 * cm],
    )

    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COR_PRIMARIA),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, COR_CINZA_BORDA),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_CINZA]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    elementos.append(tabela)
    elementos.append(PageBreak())

    # GRAFICOS
    elementos.append(Paragraph("4. Graficos Institucionais", secao))

    if grafico_setor:
        elementos.append(Paragraph("<b>Exposicao por setor</b>", texto))
        elementos.append(Image(str(grafico_setor), width=16 * cm, height=9 * cm))
        elementos.append(Spacer(1, 0.5 * cm))

    if grafico_pesos:
        elementos.append(Paragraph("<b>Peso sugerido por ativo</b>", texto))
        elementos.append(Image(str(grafico_pesos), width=16 * cm, height=9 * cm))
        elementos.append(PageBreak())

    if grafico_score:
        elementos.append(Paragraph("<b>Score final por ativo</b>", texto))
        elementos.append(Image(str(grafico_score), width=16 * cm, height=9 * cm))
        elementos.append(Spacer(1, 0.5 * cm))

    if grafico_decisao:
        elementos.append(Paragraph("<b>Distribuicao por decisao</b>", texto))
        elementos.append(Image(str(grafico_decisao), width=16 * cm, height=9 * cm))

    elementos.append(PageBreak())

    # AUDITORIA IA
    elementos.append(Paragraph("5. Auditoria Institucional com IA", secao))

    auditoria_limpa = limpar_texto_para_pdf(auditoria)

    for bloco in auditoria_limpa.split("\n"):
        bloco = bloco.strip()

        if not bloco:
            continue

        if bloco.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.", "10.")):
            elementos.append(Spacer(1, 0.14 * cm))
            elementos.append(Paragraph(f"<b>{bloco}</b>", texto))
        elif bloco.startswith("-"):
            elementos.append(Paragraph(f"• {bloco[1:].strip()}", texto))
        else:
            elementos.append(Paragraph(bloco, texto))

        elementos.append(Spacer(1, 0.06 * cm))

    elementos.append(PageBreak())

    # METODOLOGIA
    elementos.append(Paragraph("6. Metodologia", secao))

    metodologia = """
    O B3 Fundamentalista Engine utiliza uma arquitetura quantitativa em camadas.
    A primeira camada coleta e estrutura dados de empresas listadas na B3.
    A segunda camada calcula indicadores fundamentalistas, como rentabilidade,
    crescimento, valuation, alavancagem e moat. A terceira camada seleciona
    empresas com maior qualidade fundamentalista. Em seguida, o motor tecnico
    avalia o momento de entrada com base em tendencia, medias moveis, momentum,
    volatilidade e forca relativa.
    <br/><br/>
    O score final da carteira combina predominantemente fundamentos com uma camada
    tecnica de timing. A diversificacao busca reduzir concentracao setorial.
    Por fim, a auditoria com IA revisa a coerencia do processo, os principais
    riscos e os pontos de atencao.
    """

    elementos.append(Paragraph(metodologia, texto))
    elementos.append(PageBreak())

    # CONCLUSAO
    elementos.append(Paragraph("7. Conclusao e Disclaimer", secao))

    conclusao = """
    O relatorio apresenta uma carteira construida por processo quantitativo,
    com combinacao entre analise fundamentalista, analise tecnica, controle
    de diversificacao e auditoria por inteligencia artificial.
    <br/><br/>
    Este documento nao representa recomendacao absoluta de compra ou venda.
    Ele serve como apoio institucional a analise, priorizacao e acompanhamento
    de oportunidades na B3.
    <br/><br/>
    Rentabilidade passada nao garante rentabilidade futura.
    A decisao final de investimento deve considerar perfil de risco,
    horizonte de investimento, liquidez, tributacao e objetivos individuais.
    """

    elementos.append(Paragraph(conclusao, texto))
    elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(Paragraph("Fim do relatorio.", texto_pequeno))

    doc.build(elementos)

    print("=" * 70)
    print("PDF INSTITUCIONAL GERADO")
    print("=" * 70)
    print(PDF_FILE)

    return PDF_FILE


if __name__ == "__main__":
    gerar_pdf_institucional()
