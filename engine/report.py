# ============================================================
# report.py
# B3 FUNDAMENTALISTA ENGINE
# Relatório Executivo
# ============================================================

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

    if not motivos:
        motivos.append("bom equilíbrio fundamentalista")

    return ", ".join(motivos)


def imprimir_ranking(titulo, df, coluna_score):

    print()
    print("=" * 80)
    print(titulo)
    print("=" * 80)

    for i, (_, row) in enumerate(df.head(10).iterrows(), start=1):

        print(
            f"{i:02d} | {row['ticker']} | "
            f"{row['empresa'][:45]} | "
            f"Score: {row[coluna_score]:.2f}"
        )

        print(f"     Motivos: {explicar_empresa(row)}")
        print()


def gerar_relatorio(rankings):

    print()
    print("=" * 80)
    print("RELATÓRIO EXECUTIVO — B3 FUNDAMENTALISTA ENGINE")
    print("=" * 80)

    ranking_qualidade = rankings["qualidade"]
    ranking_crescimento = rankings["crescimento"]
    ranking_balanceado = rankings["balanceado"]

    imprimir_ranking(
        "TOP 10 — QUALIDADE ESTRUTURAL",
        ranking_qualidade,
        "score_qualidade"
    )

    imprimir_ranking(
        "TOP 10 — CRESCIMENTO",
        ranking_crescimento,
        "score_crescimento"
    )

    imprimir_ranking(
        "TOP 10 — BALANCEADO",
        ranking_balanceado,
        "score_balanceado"
    )

    print()
    print("=" * 80)
    print("RESUMO EXECUTIVO")
    print("=" * 80)

    print(f"Empresas na base final: {len(rankings['base'])}")
    print(f"Melhor qualidade: {ranking_qualidade.iloc[0]['ticker']}")
    print(f"Melhor crescimento: {ranking_crescimento.iloc[0]['ticker']}")
    print(f"Melhor balanceado: {ranking_balanceado.iloc[0]['ticker']}")

    print("=" * 80)
