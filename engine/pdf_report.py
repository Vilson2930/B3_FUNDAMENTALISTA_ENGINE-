# ============================================================
# pdf_report.py
# B3 FUNDAMENTALISTA ENGINE
# Relatório Institucional em PDF — Versão Visual V3
# ============================================================

from pathlib import Path
from datetime import datetime
import re
import textwrap

import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
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
    KeepTogether,
)

# ============================================================
# CONFIG
# ============================================================

OUTPUT_DIR = Path("output")
PDF_FILE = OUTPUT_DIR / "relatorio_institucional_b3.pdf"

CARTEIRA_FILE = OUTPUT_DIR / "carteira_institucional.csv"
DIVERSIFICADA_FILE = OUTPUT_DIR / "carteira_diversificada.csv"
AUDITORIA_FILE = OUTPUT_DIR / "auditoria_ia.txt"

GRAFICO_SETOR = OUTPUT_DIR / "grafico_setor.png"
GRAFICO_PESOS = OUTPUT_DIR / "grafico_pesos.png"
GRAFICO_DECISAO = OUTPUT_DIR / "grafico_decisao.png"

COR_NAVY = colors.HexColor("#0f172a")
COR_AZUL = colors.HexColor("#1d4ed8")
COR_CINZA = colors.HexColor("#f1f5f9")
COR_CINZA2 = colors.HexColor("#e5e7eb")
COR_VERDE = colors.HexColor("#15803d")
COR_AMARELO = colors.HexColor("#92400e")
COR_VERMELHO = colors.HexColor("#991b1b")
COR_TEXTO = colors.HexColor("#111827")

# ============================================================
# UTILITÁRIOS
# ============================================================


def carregar_csv(caminho):
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()

    df = pd.read_csv(caminho, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def ler_texto(caminho):
    if not caminho.exists():
        return "Auditoria IA não encontrada."
    return caminho.read_text(encoding="utf-8", errors="ignore")


def n(valor, default=0.0):
    try:
        return float(valor)
    except Exception:
        return default


def fmt_num(valor, casas=2):
    return f"{n(valor):.{casas}f}"


def fmt_pct(valor, casas=2):
    return f"{n(valor):.{casas}f}%"


def limpar_html(texto):
    texto = str(texto or "")
    texto = texto.replace("&", "&amp;")
    texto = texto.replace("<", "&lt;")
    texto = texto.replace(">", "&gt;")
    return texto


def limitar_texto(texto, limite=900):
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if len(texto) <= limite:
        return texto
    return texto[:limite].rsplit(" ", 1)[0] + "..."


def extrair_nota(auditoria):
    m = re.search(r"NOTA\s+GERAL\s*:\s*([0-9]+(?:[\.,][0-9]+)?)", auditoria, re.I)
    if not m:
        m = re.search(r"Nota\s+Geral[^0-9]*([0-9]+(?:[\.,][0-9]+)?)", auditoria, re.I)
    if not m:
        return "N/A"
    return m.group(1).replace(",", ".") + "/10"


def calcular_metricas(df, auditoria=""):
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
            "nota_ia": extrair_nota(auditoria),
            "comprar_parcial": 0,
            "aguardar": 0,
            "nao_priorizar": 0,
        }

    peso_col = "peso_sugerido_pct"
    score_col = "score_final_carteira"

    maior_setor = "N/A"
    peso_maior_setor = 0
    if "setor" in df.columns and peso_col in df.columns:
        setores = df.groupby("setor")[peso_col].sum().sort_values(ascending=False)
        if not setores.empty:
            maior_setor = str(setores.index[0])
            peso_maior_setor = float(setores.iloc[0])

    decisoes = df["decisao"].value_counts() if "decisao" in df.columns else pd.Series(dtype=int)

    return {
        "qtd_ativos": len(df),
        "peso_total": df[peso_col].sum() if peso_col in df.columns else 0,
        "melhor_ativo": str(df.iloc[0]["ticker"]) if "ticker" in df.columns and not df.empty else "N/A",
        "score_medio": df[score_col].mean() if score_col in df.columns else 0,
        "peso_top5": df.head(5)[peso_col].sum() if peso_col in df.columns else 0,
        "qtd_setores": df["setor"].nunique() if "setor" in df.columns else 0,
        "maior_setor": maior_setor,
        "peso_maior_setor": peso_maior_setor,
        "nota_ia": extrair_nota(auditoria),
        "comprar_parcial": int(decisoes.get("COMPRAR PARCIAL", 0) + decisoes.get("COMPRAR AGORA", 0)),
        "aguardar": int(decisoes.get("AGUARDAR MELHOR ENTRADA", 0)),
        "nao_priorizar": int(decisoes.get("NÃO PRIORIZAR AGORA", 0) + decisoes.get("NAO PRIORIZAR AGORA", 0)),
    }

# ============================================================
# GRÁFICOS — LEGÍVEIS
# ============================================================


def salvar_grafico_setor(df):
    if df.empty or "setor" not in df.columns or "peso_sugerido_pct" not in df.columns:
        return None

    dados = df.groupby("setor")["peso_sugerido_pct"].sum().sort_values(ascending=False)
    top = dados.head(7).copy()
    outros = dados.iloc[7:].sum()
    if outros > 0:
        top.loc["Outros"] = outros
    top = top.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    bars = ax.barh(top.index, top.values)
    ax.set_title("Exposição setorial", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Peso na carteira (%)", fontsize=10)
    ax.tick_params(axis="both", labelsize=9)
    ax.grid(axis="x", alpha=0.25)
    ax.spines[["top", "right", "left"]].set_visible(False)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.25, bar.get_y() + bar.get_height() / 2, f"{width:.1f}%", va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(GRAFICO_SETOR, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return GRAFICO_SETOR


def salvar_grafico_pesos(df):
    if df.empty or "ticker" not in df.columns or "peso_sugerido_pct" not in df.columns:
        return None

    dados = df.sort_values("peso_sugerido_pct", ascending=False).head(10)
    dados = dados.sort_values("peso_sugerido_pct", ascending=True)

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    bars = ax.barh(dados["ticker"], dados["peso_sugerido_pct"])
    ax.set_title("Top 10 pesos por ativo", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Peso na carteira (%)", fontsize=10)
    ax.tick_params(axis="both", labelsize=9)
    ax.grid(axis="x", alpha=0.25)
    ax.spines[["top", "right", "left"]].set_visible(False)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.15, bar.get_y() + bar.get_height() / 2, f"{width:.1f}%", va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(GRAFICO_PESOS, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return GRAFICO_PESOS


def salvar_grafico_decisao(df):
    if df.empty or "decisao" not in df.columns:
        return None

    dados = df["decisao"].value_counts().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    bars = ax.barh(dados.index, dados.values)
    ax.set_title("Distribuição por decisão", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Quantidade de ativos", fontsize=10)
    ax.tick_params(axis="both", labelsize=9)
    ax.grid(axis="x", alpha=0.25)
    ax.spines[["top", "right", "left"]].set_visible(False)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height() / 2, f"{int(width)}", va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(GRAFICO_DECISAO, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return GRAFICO_DECISAO

# ============================================================
# COMPONENTES DO PDF
# ============================================================


def estilo_base():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("TituloGrande", parent=styles["Title"], alignment=TA_CENTER, fontSize=23, leading=29, textColor=COR_NAVY, spaceAfter=12))
    styles.add(ParagraphStyle("Subtitulo", parent=styles["Heading2"], alignment=TA_CENTER, fontSize=13, leading=17, textColor=COR_AZUL, spaceAfter=12))
    styles.add(ParagraphStyle("Secao", parent=styles["Heading2"], alignment=TA_LEFT, fontSize=14, leading=18, textColor=COR_NAVY, spaceBefore=8, spaceAfter=8))
    styles.add(ParagraphStyle("Texto", parent=styles["BodyText"], fontSize=8.8, leading=12, alignment=TA_LEFT, textColor=COR_TEXTO))
    styles.add(ParagraphStyle("TextoCentro", parent=styles["BodyText"], fontSize=8.8, leading=12, alignment=TA_CENTER, textColor=COR_TEXTO))
    styles.add(ParagraphStyle("Pequeno", parent=styles["BodyText"], fontSize=7.2, leading=9, alignment=TA_LEFT, textColor=colors.HexColor("#475569")))
    styles.add(ParagraphStyle("CardLabel", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=7, leading=8, textColor=colors.white))
    styles.add(ParagraphStyle("CardValor", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=15, leading=18, textColor=colors.white))
    styles.add(ParagraphStyle("CardDesc", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=6.5, leading=8, textColor=colors.white))
    return styles


def card(styles, label, valor, desc=""):
    return [
        Paragraph(f"<b>{limpar_html(label)}</b>", styles["CardLabel"]),
        Paragraph(f"<b>{limpar_html(valor)}</b>", styles["CardValor"]),
        Paragraph(limpar_html(desc), styles["CardDesc"]),
    ]


def dashboard(styles, m):
    dados = [[
        card(styles, "NOTA IA", str(m["nota_ia"]), "Auditoria"),
        card(styles, "ATIVOS", str(m["qtd_ativos"]), "Carteira final"),
        card(styles, "SCORE MÉDIO", f"{m['score_medio']:.1f}", "Qualidade"),
        card(styles, "TOP 5", f"{m['peso_top5']:.1f}%", "Concentração"),
    ], [
        card(styles, "SETORES", str(m["qtd_setores"]), "Diversificação"),
        card(styles, "MAIOR SETOR", m["maior_setor"][:14], f"{m['peso_maior_setor']:.1f}%"),
        card(styles, "COMPRAR", str(m["comprar_parcial"]), "Prioridade"),
        card(styles, "AGUARDAR", str(m["aguardar"]), "Timing"),
    ]]

    t = Table(dados, colWidths=[6.4 * cm, 6.4 * cm, 6.4 * cm, 6.4 * cm], rowHeights=[2.1 * cm, 2.1 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COR_NAVY),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.white),
        ("BOX", (0, 0), (-1, -1), 0.8, COR_NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def tabela_top5(df):
    if df.empty:
        return [["Sem dados"]]

    cols = [c for c in ["ticker", "rating_carteira", "conviccao", "score_final_carteira", "peso_sugerido_pct", "decisao"] if c in df.columns]
    nomes = {
        "ticker": "Ticker",
        "rating_carteira": "Rating",
        "conviccao": "Convicção",
        "score_final_carteira": "Score",
        "peso_sugerido_pct": "Peso na Carteira",
        "decisao": "Decisão",
    }
    tabela = [[nomes.get(c, c) for c in cols]]
    for _, r in df[cols].head(5).iterrows():
        linha = []
        for c in cols:
            v = r.get(c, "")
            if c == "score_final_carteira":
                v = fmt_num(v)
            if c == "peso_sugerido_pct":
                v = fmt_pct(v)
            linha.append(str(v))
        tabela.append(linha)
    return tabela


def tabela_carteira(df):
    if df.empty:
        return [["Sem dados"]]

    cols = [c for c in ["ranking_carteira", "ticker", "setor", "rating_carteira", "conviccao", "score_final_carteira", "peso_sugerido_pct", "decisao"] if c in df.columns]
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
    tabela = [[nomes.get(c, c) for c in cols]]
    for _, r in df[cols].head(20).iterrows():
        linha = []
        for c in cols:
            v = r.get(c, "")
            if c == "score_final_carteira":
                v = fmt_num(v)
            if c == "peso_sugerido_pct":
                v = fmt_pct(v)
            linha.append(str(v))
        tabela.append(linha)
    return tabela


def aplicar_estilo_tabela(tabela, header_bg=COR_NAVY, font_size=7):
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_CINZA]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabela


def dividir_auditoria(texto):
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    if not linhas:
        return []
    blocos = []
    atual = []
    for l in linhas:
        if re.match(r"^(NOTA GERAL|DIAGNÓSTICO EXECUTIVO|QUALIDADE|DIVERSIFICAÇÃO|PESOS|PONTOS|ATIVOS|PARECER)", l, re.I):
            if atual:
                blocos.append(atual)
            atual = [l]
        else:
            atual.append(l)
    if atual:
        blocos.append(atual)
    return blocos


def desenhar_rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#64748b"))
    data = datetime.now().strftime("%d/%m/%Y")
    canvas.drawString(1.4 * cm, 0.8 * cm, f"B3 Fundamentalista Engine | Relatório institucional | {data}")
    canvas.drawRightString(28.3 * cm, 0.8 * cm, f"Página {doc.page}")
    canvas.restoreState()

# ============================================================
# PDF PRINCIPAL
# ============================================================


def gerar_pdf_institucional():
    OUTPUT_DIR.mkdir(exist_ok=True)

    carteira = carregar_csv(CARTEIRA_FILE)
    diversificada = carregar_csv(DIVERSIFICADA_FILE)
    base = diversificada if not diversificada.empty else carteira
    auditoria = ler_texto(AUDITORIA_FILE)

    metricas = calcular_metricas(base, auditoria)

    grafico_setor = salvar_grafico_setor(base)
    grafico_pesos = salvar_grafico_pesos(base)
    grafico_decisao = salvar_grafico_decisao(base)

    doc = SimpleDocTemplate(
        str(PDF_FILE),
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    styles = estilo_base()
    elementos = []

    # CAPA
    elementos.append(Spacer(1, 1.2 * cm))
    elementos.append(Paragraph("B3 FUNDAMENTALISTA ENGINE", styles["TituloGrande"]))
    elementos.append(Paragraph("RELATÓRIO INSTITUCIONAL DE CARTEIRA", styles["Subtitulo"]))
    elementos.append(Spacer(1, 0.4 * cm))

    capa_info = Table(
        [[
            Paragraph("<b>Carteira Quantitativa Brasileira</b><br/>Execução automática via GitHub Actions", styles["TextoCentro"]),
            Paragraph(f"<b>Data</b><br/>{datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["TextoCentro"]),
            Paragraph("<b>Auditoria</b><br/>Assistida por Inteligência Artificial", styles["TextoCentro"]),
        ]],
        colWidths=[8.5 * cm, 8.5 * cm, 8.5 * cm],
    )
    capa_info.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COR_CINZA),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    elementos.append(capa_info)
    elementos.append(Spacer(1, 0.7 * cm))
    elementos.append(dashboard(styles, metricas))
    elementos.append(Spacer(1, 0.4 * cm))
    elementos.append(Paragraph("Documento gerado automaticamente. Uso educacional e analítico. Não representa recomendação absoluta de compra ou venda.", styles["Pequeno"]))
    elementos.append(PageBreak())

    # RESUMO EXECUTIVO
    elementos.append(Paragraph("1. Resumo Executivo", styles["Secao"]))
    resumo = (
        f"A carteira final contém <b>{metricas['qtd_ativos']}</b> ativos, "
        f"distribuídos em <b>{metricas['qtd_setores']}</b> setores, com peso total de "
        f"<b>{metricas['peso_total']:.2f}%</b>. O ativo líder é <b>{metricas['melhor_ativo']}</b>. "
        f"O maior setor é <b>{metricas['maior_setor']}</b>, com <b>{metricas['peso_maior_setor']:.2f}%</b> da carteira. "
        "A coluna <b>Peso na Carteira</b> representa a alocação sugerida de cada ativo dentro da carteira final."
    )
    elementos.append(Paragraph(resumo, styles["Texto"]))
    elementos.append(Spacer(1, 0.25 * cm))

    t_top5 = Table(tabela_top5(base), colWidths=[3 * cm, 3 * cm, 3.5 * cm, 3 * cm, 4 * cm, 7 * cm])
    elementos.append(Paragraph("Top 5 ativos", styles["Secao"]))
    elementos.append(aplicar_estilo_tabela(t_top5, font_size=7.4))
    elementos.append(PageBreak())

    # CARTEIRA
    elementos.append(Paragraph("2. Carteira Sugerida", styles["Secao"]))
    t_cart = Table(tabela_carteira(base), repeatRows=1, colWidths=[1.4 * cm, 2.1 * cm, 5 * cm, 2.4 * cm, 3 * cm, 2.4 * cm, 4.2 * cm, 6 * cm])
    elementos.append(aplicar_estilo_tabela(t_cart, font_size=6.8))
    elementos.append(PageBreak())

    # GRÁFICOS
    elementos.append(Paragraph("3. Gráficos Institucionais", styles["Secao"]))
    graf_tabela = []
    linha = []
    if grafico_setor:
        linha.append(Image(str(grafico_setor), width=12.4 * cm, height=7.2 * cm))
    if grafico_pesos:
        linha.append(Image(str(grafico_pesos), width=12.4 * cm, height=7.2 * cm))
    if linha:
        graf_tabela.append(linha)
    if grafico_decisao:
        graf_tabela.append([Image(str(grafico_decisao), width=12.4 * cm, height=6.2 * cm), Paragraph("<b>Leitura executiva:</b><br/>Os gráficos mostram a concentração setorial, os maiores pesos individuais e a distribuição das decisões operacionais. O objetivo é facilitar a leitura rápida do risco de concentração e do timing da carteira.", styles["Texto"])])

    if graf_tabela:
        tg = Table(graf_tabela, colWidths=[13 * cm, 13 * cm])
        tg.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elementos.append(tg)
    elementos.append(PageBreak())

    # AUDITORIA IA
    elementos.append(Paragraph("4. Auditoria Institucional com IA", styles["Secao"]))
    blocos = dividir_auditoria(auditoria)
    for bloco in blocos:
        titulo = limpar_html(bloco[0])
        corpo = limpar_html(limitar_texto(" ".join(bloco[1:]), 750))
        box = Table([[Paragraph(f"<b>{titulo}</b><br/>{corpo}", styles["Texto"])]], colWidths=[25.5 * cm])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COR_CINZA),
            ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elementos.append(KeepTogether([box, Spacer(1, 0.14 * cm)]))

    elementos.append(PageBreak())

    # METODOLOGIA E DISCLAIMER
    elementos.append(Paragraph("5. Metodologia", styles["Secao"]))
    metodologia = """
    O motor utiliza uma arquitetura em camadas: coleta de dados, análise fundamentalista, análise técnica, montagem da carteira, diversificação setorial, auditoria com IA e geração de relatório. O score final combina principalmente fundamentos com uma camada técnica de timing, buscando preservar explicabilidade e disciplina.
    """
    elementos.append(Paragraph(metodologia, styles["Texto"]))
    elementos.append(Spacer(1, 0.4 * cm))

    fluxo = Table(
        [["CVM / B3", "Fundamentalista", "Técnico", "Portfolio", "Diversificação", "IA", "PDF"]],
        colWidths=[3.6 * cm] * 7,
    )
    fluxo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COR_NAVY),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elementos.append(fluxo)
    elementos.append(Spacer(1, 0.5 * cm))

    elementos.append(Paragraph("6. Conclusão e Disclaimer", styles["Secao"]))
    conclusao = """
    Este relatório consolida uma carteira construída por processo quantitativo, com análise fundamentalista, análise técnica, diversificação e auditoria por inteligência artificial. O documento serve como apoio analítico e educacional. Não representa recomendação absoluta de compra ou venda. Rentabilidade passada não garante rentabilidade futura. A decisão final deve considerar perfil de risco, horizonte, liquidez, tributação e objetivos individuais.
    """
    elementos.append(Paragraph(conclusao, styles["Texto"]))

    doc.build(elementos, onFirstPage=desenhar_rodape, onLaterPages=desenhar_rodape)

    print("=" * 70)
    print("PDF INSTITUCIONAL GERADO")
    print("=" * 70)
    print(PDF_FILE)

    return PDF_FILE


if __name__ == "__main__":
    gerar_pdf_institucional()
