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


def calcular_peso_por_score(df, score_col="score_final_carteira"):
    df = df.copy()

    total_score = df[score_col].sum()

    if total_score <= 0:
        df["peso_sugerido"] = 1 / len(df)
    else:
        df["peso_sugerido"] = df[score_col] / total_score

    df["peso_sugerido_pct"] = df["peso_sugerido"] * 100

    return df


def limitar_peso_maximo(df, peso_maximo=0.10):
    df = df.copy()

    df["peso_sugerido"] = df["peso_sugerido"].clip(upper=peso_maximo)

    total = df["peso_sugerido"].sum()

    if total > 0:
        df["peso_sugerido"] = df["peso_sugerido"] / total

    df["peso_sugerido_pct"] = df["peso_sugerido"] * 100

    return df


def classificar_decisao(score):
    if score >= 80:
        return "COMPRAR AGORA"

    if score >= 70:
        return "COMPRAR PARCIAL"

    if score >= 60:
        return "AGUARDAR MELHOR ENTRADA"

    return "NÃO PRIORIZAR AGORA"


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

    base["score_fundamental"] = pd.to_numeric(
        base["score_fundamental"],
        errors="coerce"
    ).fillna(50)

    base["score_tecnico"] = pd.to_numeric(
        base["score_tecnico"],
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

    base["score_final_carteira"] = (
        base["score_fundamental"] * 0.70 +
        base["score_tecnico"] * 0.30
    )

    base["decisao"] = base["score_final_carteira"].apply(classificar_decisao)

    base = base.sort_values(
        ["score_final_carteira", "score_tecnico"],
        ascending=False
    ).reset_index(drop=True)

    base.insert(0, "ranking_carteira", base.index + 1)

    base = calcular_peso_por_score(base)
    base = limitar_peso_maximo(base, peso_maximo=0.10)

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
        "peso_sugerido_pct",
        "sinal_tecnico",
        "decisao",
    ]

    colunas = [c for c in colunas if c in base.columns]

    print(base[colunas])

    print("\nCarteira institucional salva em:")
    print(OUTPUT_FILE)

    return base


if __name__ == "__main__":
    montar_carteira()
