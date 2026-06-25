# ============================================================
# report.py
# B3 FUNDAMENTALISTA ENGINE
# Relatório Executivo + Arquivos
# ============================================================

from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def explicar_empresa(row):
    motivos = []

    if row.get("roe", 0) >= 0.20:
        motivos.append("ROE elevado")

    if row.get("roa", 0) >= 0.08:
        motivos.append("ROA elevado")

    if row.get("margem_liquida", 0) >= 0.15:
        motivos.append("margem líquida forte")

    if row.get("divida_patrimonio", 99) <= 1:
        motivos.append("baixa alavancagem")

    if row.get("crescimento_receita", 0) >= 0.10:
        motivos.append("crescimento de receita")

    if row.get("crescimento_lucro", 0) >= 0.10:
        motivos.append("crescimento de lucro")

    if row.get("ev_ebit", 999) <= 10:
        motivos.append("EV/EBIT atrativo")

    if row.get("pl_ratio", 999) <= 12:
        motivos.append("P/L atrativo")

    if row.get("pvp_ratio", 999) <= 2:
        motivos.append("P/VP atrativo")

    if row.get("moat_score", 0) >= 80:
        motivos.append("moat forte")

    if not motivos:
        motivos.append("bom equilíbrio fundamentalista")

    return ", ".join(motivos)


def montar_bloco_ranking(titulo, df, coluna_score):
    linhas = []
    linhas.append("")
    linhas.append("=" * 80)
    linhas.append(titulo)
    linhas.append("=" * 80)

    if df.empty:
        linhas.append("Sem empresas suficientes para este ranking.")
        return "\n".join(linhas)

    for i, (_, row) in enumerate(df.head(10).iterrows(), start=1):
        linhas.append(
            f"{i:02d} | {row.get('ticker', 'N/A')} | "
            f"{str(row.get('empresa', 'N/A'))[:45]} | "
            f"Score: {row.get(coluna_score, 0):.2f}"
        )

        if "rating" in row:
            linhas.append(
                f"     Rating: {row.get('rating', 'N/A')} | "
                f"{row.get('descricao_rating', 'N/A')}"
            )

        if "moat_score" in row:
            linhas.append(
                f"     Moat: {row.get('moat_score', 0):.2f} | "
                f"{row.get('moat_classificacao', 'N/A')}"
            )

        linhas.append(f"     Motivos: {explicar_empresa(row)}")

        if "pl_ratio" in row:
            linhas.append(
                f"     P/L: {row.get('pl_ratio', 0):.2f} | "
                f"P/VP: {row.get('pvp_ratio', 0):.2f} | "
                f"EV/EBIT: {row.get('ev_ebit', 0):.2f}"
            )

        linhas.append("")

    return "\n".join(linhas)


def pegar_ranking(rankings, chave):
    return rankings.get(chave, rankings["base"].head(0))


def gerar_relatorio(rankings):
    base = rankings["base"]

    ranking_qualidade = pegar_ranking(rankings, "qualidade")
    ranking_crescimento = pegar_ranking(rankings, "crescimento")
    ranking_valuation = pegar_ranking(rankings, "valuation")
    ranking_balanceado = pegar_ranking(rankings, "balanceado")
    ranking_moat = pegar_ranking(rankings, "moat")

    texto = []
    texto.append("=" * 80)
    texto.append("RELATÓRIO EXECUTIVO — B3 FUNDAMENTALISTA ENGINE")
    texto.append("=" * 80)

    texto.append(
        montar_bloco_ranking(
            "TOP 10 — RENTABILIDADE / QUALIDADE",
            ranking_qualidade,
            "score_profitability"
        )
    )

    texto.append(
        montar_bloco_ranking(
            "TOP 10 — CRESCIMENTO",
            ranking_crescimento,
            "score_growth"
        )
    )

    texto.append(
        montar_bloco_ranking(
            "TOP 10 — VALUATION",
            ranking_valuation,
            "score_valuation"
        )
    )

    texto.append(
        montar_bloco_ranking(
            "TOP 10 — MOAT SCORE",
            ranking_moat,
            "moat_score"
        )
    )

    texto.append(
        montar_bloco_ranking(
            "TOP 10 — BALANCEADO INSTITUCIONAL",
            ranking_balanceado,
            "score_balanceado"
        )
    )

    texto.append("")
    texto.append("=" * 80)
    texto.append("RESUMO EXECUTIVO")
    texto.append("=" * 80)
    texto.append(f"Empresas na base final: {len(base)}")

    if not ranking_qualidade.empty:
        texto.append(f"Melhor qualidade: {ranking_qualidade.iloc[0].get('ticker', 'N/A')}")
    if not ranking_crescimento.empty:
        texto.append(f"Melhor crescimento: {ranking_crescimento.iloc[0].get('ticker', 'N/A')}")
    if not ranking_valuation.empty:
        texto.append(f"Melhor valuation: {ranking_valuation.iloc[0].get('ticker', 'N/A')}")
    if not ranking_moat.empty:
        texto.append(f"Melhor moat: {ranking_moat.iloc[0].get('ticker', 'N/A')}")
    if not ranking_balanceado.empty:
        texto.append(f"Melhor balanceado: {ranking_balanceado.iloc[0].get('ticker', 'N/A')}")

    texto.append("=" * 80)

    relatorio = "\n".join(texto)

    print(relatorio)

    (OUTPUT_DIR / "report.txt").write_text(relatorio, encoding="utf-8")

    base.to_csv(OUTPUT_DIR / "base_final.csv", index=False)
    ranking_qualidade.to_csv(OUTPUT_DIR / "ranking_qualidade.csv", index=False)
    ranking_crescimento.to_csv(OUTPUT_DIR / "ranking_crescimento.csv", index=False)
    ranking_valuation.to_csv(OUTPUT_DIR / "ranking_valuation.csv", index=False)
    ranking_moat.to_csv(OUTPUT_DIR / "ranking_moat.csv", index=False)
    ranking_balanceado.to_csv(OUTPUT_DIR / "ranking_balanceado.csv", index=False)

    print("\nArquivos salvos em /output:")
    print("- report.txt")
    print("- base_final.csv")
    print("- ranking_qualidade.csv")
    print("- ranking_crescimento.csv")
    print("- ranking_valuation.csv")
    print("- ranking_moat.csv")
    print("- ranking_balanceado.csv")
