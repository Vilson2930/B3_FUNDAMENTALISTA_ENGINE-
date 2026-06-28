# ============================================================
# pdf_report.py
# B3 FUNDAMENTALISTA ENGINE
# Relatório Institucional em PDF — V4 Integrado
#
# Objetivo:
# - Usar toda a inteligência nova do motor:
#   carteira_diversificada.csv
#   portfolio_metrics.csv
#   diversification_metrics.csv
#   top20_tecnico.csv
#   auditoria_ia.txt
# - Mostrar diagnóstico técnico, risco, diversificação, HHI,
#   validação de limites e leitura institucional.
# ============================================================

from pathlib import Path
from datetime import datetime
import re

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
TECNICO_FILE = OUTPUT_DIR / "top20_tecnico.csv"
AUDITORIA_FILE = OUTPUT_DIR / "auditoria_ia.txt"
PORTFOLIO_METRICS_FILE = OUTPUT_DIR / "portfolio_metrics.csv"
DIVERSIFICATION_METRICS_FILE = OUTPUT_DIR / "diversification_metrics.csv"

GRAFICO_SETOR = OUTPUT_DIR / "grafico_setor.png"
GRAFICO_PESOS = OUTPUT_DIR / "grafico_pesos.png"
GRAFICO_DECISAO = OUTPUT_DIR / "grafico_decisao.png"
GRAFICO_RISCO_TECNICO = OUTPUT_DIR / "grafico_risco_tecnico.png"
GRAFICO_CONVICCAO_TECNICA = OUTPUT_DIR / "grafico_conviccao_tecnica.png"
GRAFICO_SCORE = OUTPUT_DIR / "grafico_score_fund_tecnico.png"

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
    caminho = Path(caminho)
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
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
        return "Auditoria IA não encontrada."
    return caminho.read_text(encoding="utf-8", errors="ignore")


def n(valor, default=0.0):
    try:
        if pd.isna(valor):
            return default
        return float(valor)
    except Exception:
        return default


def texto(valor, default="N/A"):
    if valor is None:
        return default
    valor = str(valor).strip()
    if valor == "" or valor.lower() == "nan":
        return default
    return valor


def fmt_num(valor, casas=2):
    return f"{n(valor):.{casas}f}"


def fmt_pct(valor, casas=2):
    return f"{n(valor):.{casas}f}%"


def limpar_html(valor):
    valor = str(valor or "")
    valor = valor.replace("&", "&amp;")
    valor = valor.replace("<", "&lt;")
    valor = valor.replace(">", "&gt;")
    return valor


def limitar_texto(valor, limite=700):
    valor = re.sub(r"\s+", " ", str(valor or "")).strip()
    if len(valor) <= limite:
        return valor
    return valor[:limite].rsplit(" ", 1)[0] + "..."


def extrair_nota(auditoria):
    m = re.search(r"NOTA\s+GERAL\s*:\s*([0-9]+(?:[\.,][0-9]+)?)", auditoria, re.I)
    if not m:
        m = re.search(r"Nota\s+Geral[^0-9]*([0-9]+(?:[\.,][0-9]+)?)", auditoria, re.I)
    if not m:
        return "N/A"
    return m.group(1).replace(",", ".") + "/10"


def primeira_linha(df, coluna, default=0):
    if df is None or df.empty or coluna not in df.columns:
        return default
    return df.iloc[0].get(coluna, default)


def merge_tecnico(base, tecnico):
    if base.empty or tecnico.empty or "ticker" not in base.columns or "ticker" not in tecnico.columns:
        return base

    base = base.copy()
    tecnico = tecnico.copy()
    base["ticker"] = base["ticker"].astype(str).str.upper().str.strip()
    tecnico["ticker"] = tecnico["ticker"].astype(str).str.upper().str.strip()

    cols_tecnicos = [
        "ticker",
        "tendencia_resumo",
        "mm200_status",
        "rsi_status",
        "momentum_status",
        "volume_status",
        "volatilidade_status",
        "conviccao_tecnica",
        "risco_tecnico",
        "contribuicao_tecnica",
        "diagnostico_tecnico",
    ]
    cols_tecnicos = [c for c in cols_tecnicos if c in tecnico.columns]

    ja_existe = [c for c in cols_tecnicos if c != "ticker" and c in base.columns]
    if ja_existe:
        return base

    return base.merge(tecnico[cols_tecnicos], on="ticker", how="left")


# ============================================================
# MÉTRICAS CONSOLIDADAS
# ============================================================


def calcular_metricas(base, auditoria, portfolio_metrics, diversification_metrics):
    peso_col = "peso_sugerido_pct"
    score_col = "score_final_carteira"

    if base.empty:
        return {
            "nota_ia": extrair_nota(auditoria),
            "qtd_ativos": 0,
            "qtd_setores": 0,
            "peso_total": 0,
            "score_medio": 0,
            "peso_top5": 0,
            "melhor_ativo": "N/A",
            "maior_setor": "N/A",
            "peso_maior_setor": 0,
            "comprar": 0,
            "aguardar": 0,
            "nao_priorizar": 0,
            "score_diversificacao": 0,
            "risco_diversificacao": "N/A",
            "hhi": 0,
            "numero_efetivo_ativos": 0,
            "validacao_limites": "N/A",
            "peso_maximo_ativo": 0,
        }

    setores = pd.Series(dtype=float)
    maior_setor = "N/A"
    peso_maior_setor = 0
    if "setor" in base.columns and peso_col in base.columns:
        setores = base.groupby("setor")[peso_col].sum().sort_values(ascending=False)
        if not setores.empty:
            maior_setor = str(setores.index[0])
            peso_maior_setor = float(setores.iloc[0])

    decisoes = base["decisao"].value_counts() if "decisao" in base.columns else pd.Series(dtype=int)

    score_div = primeira_linha(diversification_metrics, "score_diversificacao", 0)
    status_div = primeira_linha(diversification_metrics, "status_diversificacao", "N/A")
    risco_div = primeira_linha(diversification_metrics, "risco_diversificacao", "N/A")
    hhi = primeira_linha(diversification_metrics, "hhi", 0)
    nea = primeira_linha(diversification_metrics, "numero_efetivo_ativos", 0)
    soma_pesos = primeira_linha(diversification_metrics, "soma_pesos_pct", base[peso_col].sum() if peso_col in base.columns else 0)
    peso_max = base[peso_col].max() if peso_col in base.columns else 0

    validacao_limites = "OK"
    if "validacao_peso_ativo" in base.columns and (base["validacao_peso_ativo"].astype(str) != "OK").any():
        validacao_limites = "ATENÇÃO"
    if "validacao_peso_setor" in base.columns and (base["validacao_peso_setor"].astype(str) != "OK").any():
        validacao_limites = "ATENÇÃO"

    return {
        "nota_ia": extrair_nota(auditoria),
        "qtd_ativos": len(base),
        "qtd_setores": base["setor"].nunique() if "setor" in base.columns else 0,
        "peso_total": soma_pesos,
        "score_medio": base[score_col].mean() if score_col in base.columns else 0,
        "peso_top5": base.head(5)[peso_col].sum() if peso_col in base.columns else 0,
        "melhor_ativo": str(base.iloc[0]["ticker"]) if "ticker" in base.columns else "N/A",
        "maior_setor": maior_setor,
        "peso_maior_setor": peso_maior_setor,
        "comprar": int(decisoes.get("COMPRAR PARCIAL", 0) + decisoes.get("COMPRAR AGORA", 0)),
        "aguardar": int(decisoes.get("AGUARDAR MELHOR ENTRADA", 0)),
        "nao_priorizar": int(decisoes.get("NÃO PRIORIZAR AGORA", 0) + decisoes.get("NAO PRIORIZAR AGORA", 0)),
        "score_diversificacao": n(score_div),
        "status_diversificacao": texto(status_div),
        "risco_diversificacao": texto(risco_div),
        "hhi": n(hhi),
        "numero_efetivo_ativos": n(nea),
        "validacao_limites": validacao_limites,
        "peso_maximo_ativo": peso_max,
    }


# ============================================================
# GRÁFICOS
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
    ax.grid(axis="x", alpha=0.25)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="both", labelsize=9)

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

    dados = df.sort_values("peso_sugerido_pct", ascending=False).head(10).sort_values("peso_sugerido_pct", ascending=True)

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    bars = ax.barh(dados["ticker"], dados["peso_sugerido_pct"])
    ax.set_title("Top 10 pesos por ativo", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Peso na carteira (%)", fontsize=10)
    ax.grid(axis="x", alpha=0.25)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="both", labelsize=9)

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

    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    bars = ax.barh(dados.index, dados.values)
    ax.set_title("Distribuição por decisão", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Quantidade de ativos", fontsize=10)
    ax.grid(axis="x", alpha=0.25)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="both", labelsize=9)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height() / 2, f"{int(width)}", va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(GRAFICO_DECISAO, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return GRAFICO_DECISAO


def salvar_grafico_categoria(df, coluna, titulo, arquivo):
    if df.empty or coluna not in df.columns:
        return None

    dados = df[coluna].fillna("N/A").astype(str).value_counts().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(9.5, 4.4))
    bars = ax.barh(dados.index, dados.values)
    ax.set_title(titulo, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Quantidade de ativos", fontsize=10)
    ax.grid(axis="x", alpha=0.25)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="both", labelsize=9)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height() / 2, f"{int(width)}", va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(arquivo, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return arquivo


def salvar_grafico_score(df):
    if df.empty or "ticker" not in df.columns:
        return None
    if "score_fundamental" not in df.columns or "score_tecnico" not in df.columns:
        return None

    dados = df.head(10).copy()
    x = range(len(dados))

    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.scatter(x, dados["score_fundamental"], label="Fundamental")
    ax.scatter(x, dados["score_tecnico"], label="Técnico")
    ax.set_xticks(list(x))
    ax.set_xticklabels(dados["ticker"], rotation=35, ha="right", fontsize=8)
    ax.set_title("Fundamental x Técnico — Top 10", fontsize=14, fontweight="bold", pad=12)
    ax.set_ylabel("Score")
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(GRAFICO_SCORE, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return GRAFICO_SCORE


# ============================================================
# ESTILOS E COMPONENTES
# ============================================================


def estilo_base():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("TituloGrande", parent=styles["Title"], alignment=TA_CENTER, fontSize=23, leading=29, textColor=COR_NAVY, spaceAfter=12))
    styles.add(ParagraphStyle("Subtitulo", parent=styles["Heading2"], alignment=TA_CENTER, fontSize=13, leading=17, textColor=COR_AZUL, spaceAfter=12))
    styles.add(ParagraphStyle("Secao", parent=styles["Heading2"], alignment=TA_LEFT, fontSize=14, leading=18, textColor=COR_NAVY, spaceBefore=8, spaceAfter=8))
    styles.add(ParagraphStyle("Texto", parent=styles["BodyText"], fontSize=8.4, leading=11.5, alignment=TA_LEFT, textColor=COR_TEXTO))
    styles.add(ParagraphStyle("TextoCentro", parent=styles["BodyText"], fontSize=8.4, leading=11.5, alignment=TA_CENTER, textColor=COR_TEXTO))
    styles.add(ParagraphStyle("Pequeno", parent=styles["BodyText"], fontSize=7.0, leading=9, alignment=TA_LEFT, textColor=colors.HexColor("#475569")))
    styles.add(ParagraphStyle("CardLabel", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=6.7, leading=8, textColor=colors.white))
    styles.add(ParagraphStyle("CardValor", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=14, leading=17, textColor=colors.white))
    styles.add(ParagraphStyle("CardDesc", parent=styles["BodyText"], alignment=TA_CENTER, fontSize=6.2, leading=8, textColor=colors.white))
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
        card(styles, "SCORE", f"{m['score_medio']:.1f}", "Médio"),
        card(styles, "TOP 5", f"{m['peso_top5']:.1f}%", "Concentração"),
    ], [
        card(styles, "DIVERSIF.", f"{m['score_diversificacao']:.0f}/100", m["risco_diversificacao"]),
        card(styles, "HHI", f"{m['hhi']:.3f}", "Concentração"),
        card(styles, "Nº EFETIVO", f"{m['numero_efetivo_ativos']:.1f}", "Ativos"),
        card(styles, "LIMITES", m["validacao_limites"], "Peso/Setor"),
    ], [
        card(styles, "MAIOR SETOR", m["maior_setor"][:13], f"{m['peso_maior_setor']:.1f}%"),
        card(styles, "PESO MÁX.", f"{m['peso_maximo_ativo']:.1f}%", "Ativo"),
        card(styles, "COMPRAR", str(m["comprar"]), "Prioridade"),
        card(styles, "AGUARDAR", str(m["aguardar"]), "Timing"),
    ]]

    t = Table(dados, colWidths=[6.4 * cm, 6.4 * cm, 6.4 * cm, 6.4 * cm], rowHeights=[1.55 * cm, 1.55 * cm, 1.55 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), COR_NAVY),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.white),
        ("BOX", (0, 0), (-1, -1), 0.8, COR_NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def aplicar_estilo_tabela(tabela, header_bg=COR_NAVY, font_size=6.7):
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


def tabela_top5(df):
    if df.empty:
        return [["Sem dados"]]

    cols = [c for c in ["ticker", "rating_carteira", "conviccao", "conviccao_tecnica", "risco_tecnico", "score_final_carteira", "peso_sugerido_pct", "decisao"] if c in df.columns]
    nomes = {
        "ticker": "Ticker",
        "rating_carteira": "Rating",
        "conviccao": "Convicção",
        "conviccao_tecnica": "Conv. Técnica",
        "risco_tecnico": "Risco Técnico",
        "score_final_carteira": "Score",
        "peso_sugerido_pct": "Peso",
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

    cols = [c for c in ["ranking_carteira", "ticker", "setor", "rating_carteira", "conviccao", "score_final_carteira", "peso_sugerido_pct", "conviccao_tecnica", "risco_tecnico", "decisao"] if c in df.columns]
    nomes = {
        "ranking_carteira": "Rank",
        "ticker": "Ticker",
        "setor": "Setor",
        "rating_carteira": "Rating",
        "conviccao": "Conv.",
        "score_final_carteira": "Score",
        "peso_sugerido_pct": "Peso",
        "conviccao_tecnica": "Conv. Téc.",
        "risco_tecnico": "Risco Téc.",
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


def tabela_validacao(m):
    return [
        ["Métrica", "Valor", "Leitura"],
        ["Score de Diversificação", f"{m['score_diversificacao']:.0f}/100", m["risco_diversificacao"]],
        ["HHI", f"{m['hhi']:.4f}", "menor = mais diversificado"],
        ["Número efetivo de ativos", f"{m['numero_efetivo_ativos']:.1f}", "diversificação real"],
        ["Peso máximo por ativo", f"{m['peso_maximo_ativo']:.2f}%", "limite validado"],
        ["Maior setor", f"{m['maior_setor']} ({m['peso_maior_setor']:.2f}%)", "exposição setorial"],
        ["Validação de limites", m["validacao_limites"], "ativo e setor"],
    ]


def tabela_diagnostico_tecnico(df):
    if df.empty:
        return [["Sem dados"]]

    cols = [c for c in ["ticker", "tendencia_resumo", "mm200_status", "rsi_status", "momentum_status", "volume_status", "conviccao_tecnica", "risco_tecnico"] if c in df.columns]
    nomes = {
        "ticker": "Ticker",
        "tendencia_resumo": "Tendência",
        "mm200_status": "MM200",
        "rsi_status": "RSI",
        "momentum_status": "Momentum",
        "volume_status": "Volume",
        "conviccao_tecnica": "Convicção",
        "risco_tecnico": "Risco",
    }
    tabela = [[nomes.get(c, c) for c in cols]]
    for _, r in df[cols].head(10).iterrows():
        linha = []
        for c in cols:
            linha.append(limitar_texto(str(r.get(c, "")), 38))
        tabela.append(linha)
    return tabela


def dividir_auditoria(texto_auditoria):
    linhas = [l.strip() for l in texto_auditoria.splitlines() if l.strip()]
    if not linhas:
        return []

    padrao = r"^(NOTA GERAL|COMPOSIÇÃO|COMPOSICAO|DIAGNÓSTICO|DIAGNOSTICO|PONTOS|RISCOS|INTERPRETAÇÃO|INTERPRETACAO|ATIVOS|CHECKLIST|PARECER)"
    blocos = []
    atual = []

    for linha in linhas:
        if re.match(padrao, linha, re.I):
            if atual:
                blocos.append(atual)
            atual = [linha]
        else:
            atual.append(linha)

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
    tecnico = carregar_csv(TECNICO_FILE)
    portfolio_metrics = carregar_csv(PORTFOLIO_METRICS_FILE)
    diversification_metrics = carregar_csv(DIVERSIFICATION_METRICS_FILE)
    auditoria = ler_texto(AUDITORIA_FILE)

    base = diversificada if not diversificada.empty else carteira
    base = merge_tecnico(base, tecnico)

    metricas = calcular_metricas(base, auditoria, portfolio_metrics, diversification_metrics)

    grafico_setor = salvar_grafico_setor(base)
    grafico_pesos = salvar_grafico_pesos(base)
    grafico_decisao = salvar_grafico_decisao(base)
    grafico_risco = salvar_grafico_categoria(base, "risco_tecnico", "Risco técnico", GRAFICO_RISCO_TECNICO)
    grafico_conviccao = salvar_grafico_categoria(base, "conviccao_tecnica", "Convicção técnica", GRAFICO_CONVICCAO_TECNICA)
    grafico_score = salvar_grafico_score(base)

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
    elementos.append(Spacer(1, 0.9 * cm))
    elementos.append(Paragraph("B3 FUNDAMENTALISTA ENGINE", styles["TituloGrande"]))
    elementos.append(Paragraph("RELATÓRIO INSTITUCIONAL DE CARTEIRA", styles["Subtitulo"]))
    elementos.append(Spacer(1, 0.25 * cm))

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
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elementos.append(capa_info)
    elementos.append(Spacer(1, 0.45 * cm))
    elementos.append(dashboard(styles, metricas))
    elementos.append(Spacer(1, 0.25 * cm))
    elementos.append(Paragraph("Documento gerado automaticamente. Uso educacional e analítico. Não representa recomendação absoluta de compra ou venda.", styles["Pequeno"]))
    elementos.append(PageBreak())

    # RESUMO EXECUTIVO
    elementos.append(Paragraph("1. Resumo Executivo", styles["Secao"]))
    resumo = (
        f"A carteira final contém <b>{metricas['qtd_ativos']}</b> ativos, distribuídos em "
        f"<b>{metricas['qtd_setores']}</b> setores, com peso total de "
        f"<b>{metricas['peso_total']:.2f}%</b>. O ativo líder é <b>{metricas['melhor_ativo']}</b>. "
        f"O maior setor é <b>{metricas['maior_setor']}</b>, com <b>{metricas['peso_maior_setor']:.2f}%</b>. "
        f"O score de diversificação é <b>{metricas['score_diversificacao']:.0f}/100</b>, "
        f"com risco classificado como <b>{metricas['risco_diversificacao']}</b>. "
        f"A validação de limites por ativo e setor está em status <b>{metricas['validacao_limites']}</b>."
    )
    elementos.append(Paragraph(resumo, styles["Texto"]))
    elementos.append(Spacer(1, 0.25 * cm))

    t_val = Table(tabela_validacao(metricas), colWidths=[7 * cm, 6 * cm, 12 * cm])
    elementos.append(aplicar_estilo_tabela(t_val, font_size=7.2))
    elementos.append(Spacer(1, 0.25 * cm))

    elementos.append(Paragraph("Top 5 ativos", styles["Secao"]))
    t_top5 = Table(tabela_top5(base), colWidths=[2 * cm, 2.2 * cm, 2.7 * cm, 3 * cm, 3.2 * cm, 2 * cm, 2.8 * cm, 6.5 * cm])
    elementos.append(aplicar_estilo_tabela(t_top5, font_size=6.6))
    elementos.append(PageBreak())

    # CARTEIRA
    elementos.append(Paragraph("2. Carteira Sugerida", styles["Secao"]))
    t_cart = Table(tabela_carteira(base), repeatRows=1, colWidths=[1.1 * cm, 1.7 * cm, 4.1 * cm, 1.7 * cm, 2.2 * cm, 1.8 * cm, 2.2 * cm, 2.4 * cm, 2.8 * cm, 5.2 * cm])
    elementos.append(aplicar_estilo_tabela(t_cart, font_size=6.1))
    elementos.append(PageBreak())

    # DIAGNÓSTICO TÉCNICO
    elementos.append(Paragraph("3. Diagnóstico Técnico dos Principais Ativos", styles["Secao"]))
    elementos.append(Paragraph("Esta página traduz os indicadores técnicos em linguagem executiva: tendência, MM200, RSI, momentum, volume, convicção e risco técnico.", styles["Texto"]))
    elementos.append(Spacer(1, 0.2 * cm))
    t_diag = Table(tabela_diagnostico_tecnico(base), repeatRows=1, colWidths=[1.7 * cm, 3.1 * cm, 3.4 * cm, 2.5 * cm, 5.0 * cm, 3.2 * cm, 2.5 * cm, 3.0 * cm])
    elementos.append(aplicar_estilo_tabela(t_diag, font_size=5.8))
    elementos.append(PageBreak())

    # GRÁFICOS 1
    elementos.append(Paragraph("4. Gráficos Institucionais", styles["Secao"]))
    linha1 = []
    if grafico_setor:
        linha1.append(Image(str(grafico_setor), width=12.4 * cm, height=7.0 * cm))
    if grafico_pesos:
        linha1.append(Image(str(grafico_pesos), width=12.4 * cm, height=7.0 * cm))
    if linha1:
        tg1 = Table([linha1], colWidths=[13 * cm, 13 * cm])
        tg1.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elementos.append(tg1)
    elementos.append(PageBreak())

    # GRÁFICOS 2
    elementos.append(Paragraph("5. Risco, Convicção e Decisão", styles["Secao"]))
    graf_tabela = []
    if grafico_decisao and grafico_risco:
        graf_tabela.append([Image(str(grafico_decisao), width=12.4 * cm, height=6.3 * cm), Image(str(grafico_risco), width=12.4 * cm, height=6.3 * cm)])
    if grafico_conviccao and grafico_score:
        graf_tabela.append([Image(str(grafico_conviccao), width=12.4 * cm, height=6.3 * cm), Image(str(grafico_score), width=12.4 * cm, height=6.3 * cm)])
    if graf_tabela:
        tg2 = Table(graf_tabela, colWidths=[13 * cm, 13 * cm])
        tg2.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elementos.append(tg2)
    elementos.append(PageBreak())

    # AUDITORIA IA
    elementos.append(Paragraph("6. Auditoria Institucional com IA", styles["Secao"]))
    blocos = dividir_auditoria(auditoria)
    for bloco in blocos:
        titulo = limpar_html(bloco[0])
        corpo = limpar_html(limitar_texto(" ".join(bloco[1:]), 620))
        box = Table([[Paragraph(f"<b>{titulo}</b><br/>{corpo}", styles["Texto"])]], colWidths=[25.5 * cm])
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COR_CINZA),
            ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(KeepTogether([box, Spacer(1, 0.11 * cm)]))
    elementos.append(PageBreak())

    # METODOLOGIA E DISCLAIMER
    elementos.append(Paragraph("7. Metodologia", styles["Secao"]))
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

    elementos.append(Paragraph("8. Conclusão e Disclaimer", styles["Secao"]))
    conclusao = """
    Este relatório consolida uma carteira construída por processo quantitativo, com análise fundamentalista, análise técnica, diversificação e auditoria por inteligência artificial. O documento serve como apoio analítico e educacional. Não representa recomendação absoluta de compra ou venda. Rentabilidade passada não garante rentabilidade futura. A decisão final deve considerar perfil de risco, horizonte, liquidez, tributação e objetivos individuais.
    """
    elementos.append(Paragraph(conclusao, styles["Texto"]))

    doc.build(elementos, onFirstPage=desenhar_rodape, onLaterPages=desenhar_rodape)

    print("=" * 70)
    print("PDF INSTITUCIONAL GERADO — V4 INTEGRADO")
    print("=" * 70)
    print(PDF_FILE)

    return PDF_FILE


if __name__ == "__main__":
    gerar_pdf_institucional()
