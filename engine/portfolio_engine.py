# ============================================================
# portfolio_engine.py
# B3 FUNDAMENTALISTA ENGINE
# Carteira Institucional Final
#
# Filosofia:
# O Fundamentalista escolhe as 20 melhores empresas.
# O Técnico calcula o momento de entrada.
# O Portfolio usa o top20_tecnico.csv para montar a carteira.
# Score Final = 70% Fundamentalista + 30% Técnico
# ============================================================

from pathlib import Path
import pandas as pd


INPUT_TECNICO = Path("output/top20_tecnico.csv")
OUTPUT_FILE = Path("output/carteira_institucional.csv")


PESO_FUNDAMENTAL = 0.70
PESO_TECNICO = 0.30

PESO_MAXIMO_ATIVO = 0.10
PESO_MINIMO_ATIVO = 0.02


def carregar_csv(caminho):
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(caminho, encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(caminho)

    df.columns = [str(c).strip() for c in df.columns]
    return df


def classificar_decisao(score):
    if score >= 80:
        return "COMPRAR AGORA"

    if score >= 70:
        return "COMPRAR PARCIAL"

    if score >= 60:
        return "AGUARDAR MELHOR ENTRADA"

    return "NÃO PRIORIZAR AGORA"


def classificar_conviccao(score):
    if score >= 80:
        return "MUITO ALTA"

    if score >= 70:
        return "ALTA"

    if score >= 60:
        return "MÉDIA"

    if score >= 50:
        return "BAIXA"

    return "MUITO BAIXA"


def classificar_prioridade(score):
    if score >= 80:
        return "PRIORIDADE 1"

    if score >= 70:
        return "PRIORIDADE 2"

    if score >= 60:
        return "PRIORIDADE 3"

    return "OBSERVAÇÃO"


def rating_institucional(score):
    if score >= 90:
        return "AAA"

    if score >= 85:
        return "AA+"

    if score >= 80:
        return "AA"

    if score >= 75:
        return "A+"

    if score >= 70:
        return "A"

    if score >= 65:
        return "BBB+"

    if score >= 60:
        return "BBB"

    if score >= 55:
        return "BB"

    return "B"


def calcular_score_final(base):
    base = base.copy()

    base["score_final_carteira"] = (
        base["score_fundamental"] * PESO_FUNDAMENTAL +
        base["score_tecnico"] * PESO_TECNICO
    )

    return base


def calcular_peso_inteligente(df):
    df = df.copy()

    # Pontuação de alocação mais concentrada nas melhores oportunidades
    df["allocation_score"] = df["score_final_carteira"].clip(lower=0) ** 2

    total = df["allocation_score"].sum()

    if total <= 0:
        df["peso_sugerido"] = 1 / len(df)
    else:
        df["peso_sugerido"] = df["allocation_score"] / total

    # Limite máximo por ativo
    df["peso_sugerido"] = df["peso_sugerido"].clip(upper=PESO_MAXIMO_ATIVO)

    total = df["peso_sugerido"].sum()

    if total > 0:
        df["peso_sugerido"] = df["peso_sugerido"] / total

    # Limite mínimo visual para ativos aprovados
    df.loc[
        df["score_final_carteira"] >= 60,
        "peso_sugerido"
    ] = df.loc[
        df["score_final_carteira"] >= 60,
        "peso_sugerido"
    ].clip(lower=PESO_MINIMO_ATIVO)

    total = df["peso_sugerido"].sum()

    if total > 0:
        df["peso_sugerido"] = df["peso_sugerido"] / total

    df["peso_sugerido_pct"] = df["peso_sugerido"] * 100

    return df


def gerar_motivo(row):
    motivos = []

    if row.get("score_fundamental", 0) >= 75:
        motivos.append("fundamentos fortes")
    elif row.get("score_fundamental", 0) >= 65:
        motivos.append("fundamentos bons")
    else:
        motivos.append("fundamentos moderados")

    if row.get("score_tecnico", 0) >= 80:
        motivos.append("momento técnico muito favorável")
    elif row.get("score_tecnico", 0) >= 65:
        motivos.append("momento técnico favorável")
    elif row.get("score_tecnico", 0) >= 50:
        motivos.append("momento técnico neutro")
    else:
        motivos.append("momento técnico fraco")

    if row.get("moat_score", 0) >= 75:
        motivos.append("moat relevante")

    if row.get("sinal_tecnico", "") in ["EVITAR", "FRACO"]:
        motivos.append("entrada exige cautela")

    return "; ".join(motivos)


def montar_carteira():
    base = carregar_csv(INPUT_TECNICO)

    if base.empty:
        print("Arquivo top20_tecnico.csv vazio ou não encontrado.")
        return pd.DataFrame()

    print("=" * 70)
    print("AUDITORIA — TOP20 TÉCNICO CARREGADO")
    print("=" * 70)
    print("Linhas:", len(base))
    print("Colunas:", list(base.columns))

    if "ticker" in base.columns:
        base["ticker"] = base["ticker"].astype(str).str.strip().str.upper()

    if "score_fundamental" not in base.columns:
        print("ATENÇÃO: coluna score_fundamental não encontrada. Usando 50.")
        base["score_fundamental"] = 50

    if "score_tecnico" not in base.columns:
        print("ATENÇÃO: coluna score_tecnico não encontrada. Usando 50.")
        base["score_tecnico"] = 50

    if "moat_score" not in base.columns:
        base["moat_score"] = 50

    if "sinal_tecnico" not in base.columns:
        base["sinal_tecnico"] = "NEUTRO"

    base["score_fundamental"] = pd.to_numeric(
        base["score_fundamental"],
        errors="coerce"
    ).fillna(50)

    base["score_tecnico"] = pd.to_numeric(
        base["score_tecnico"],
        errors="coerce"
    ).fillna(50)

    base["moat_score"] = pd.to_numeric(
        base["moat_score"],
        errors="coerce"
    ).fillna(50)

    print()
    print("Amostra antes do cálculo:")
    colunas_debug = [
        "ticker",
        "score_fundamental",
        "score_tecnico",
        "sinal_tecnico"
    ]
    colunas_debug = [c for c in colunas_debug if c in base.columns]
    print(base[colunas_debug].head(20))

    base = calcular_score_final(base)

    base["decisao"] = base["score_final_carteira"].apply(classificar_decisao)
    base["conviccao"] = base["score_final_carteira"].apply(classificar_conviccao)
    base["prioridade"] = base["score_final_carteira"].apply(classificar_prioridade)
    base["rating_carteira"] = base["score_final_carteira"].apply(rating_institucional)
    base["motivo_decisao"] = base.apply(gerar_motivo, axis=1)

    base = base.sort_values(
        ["score_final_carteira", "score_tecnico"],
        ascending=False
    ).reset_index(drop=True)

    base.insert(0, "ranking_carteira", base.index + 1)

    base = calcular_peso_inteligente(base)

    Path("output").mkdir(exist_ok=True)

    base.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("=" * 70)
    print("CARTEIRA INSTITUCIONAL")
    print("=" * 70)

    colunas = [
        "ranking_carteira",
        "ticker",
        "empresa",
        "setor",
        "score_fundamental",
        "score_tecnico",
        "score_final_carteira",
        "rating_carteira",
        "conviccao",
        "prioridade",
        "peso_sugerido_pct",
        "sinal_tecnico",
        "decisao",
        "motivo_decisao",
    ]

    colunas = [c for c in colunas if c in base.columns]

    print(base[colunas])

    print("\nCarteira institucional salva em:")
    print(OUTPUT_FILE)

    return base


if __name__ == "__main__":
    montar_carteira()
