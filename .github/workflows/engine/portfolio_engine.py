from pathlib import Path
import pandas as pd

OUTPUT_DIR = Path("output")
INPUT_FILE = OUTPUT_DIR / "top20_tecnico.csv"

OUTPUT_FILE = OUTPUT_DIR / "carteira_institucional.csv"
REPORT_FILE = OUTPUT_DIR / "portfolio_report.txt"

MAX_EMPRESAS_CARTEIRA = 15
MAX_EMPRESAS_POR_SETOR = 2

PESO_FUNDAMENTALISTA = 0.50
PESO_TECNICO = 0.35
PESO_MOAT = 0.15


def carregar_base():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def numero(df, coluna, padrao=0):
    if coluna not in df.columns:
        df[coluna] = padrao

    df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(padrao)
    return df


def penalidade_tecnica(sinal):
    sinal = str(sinal).upper().strip()

    if "COMPRA FORTE" in sinal:
        return 5

    if sinal == "COMPRA":
        return 2

    if "AGUARDAR" in sinal:
        return -3

    if "FRACO" in sinal:
        return -12

    if "EVITAR" in sinal:
        return -20

    return 0


def calcular_score_gestor(df):
    df = numero(df, "score_balanceado", 0)
    df = numero(df, "score_tecnico", 0)
    df = numero(df, "moat_score", 50)

    if "sinal_tecnico" not in df.columns:
        df["sinal_tecnico"] = "NEUTRO"

    df["ajuste_tecnico"] = df["sinal_tecnico"].apply(penalidade_tecnica)

    df["score_gestor"] = (
        df["score_balanceado"] * PESO_FUNDAMENTALISTA
        + df["score_tecnico"] * PESO_TECNICO
        + df["moat_score"] * PESO_MOAT
        + df["ajuste_tecnico"]
    )

    df["score_gestor"] = df["score_gestor"].clip(lower=0, upper=100)

    return df


def aplicar_diversificacao(df):
    carteira = []
    setores = {}

    df = df.sort_values("score_gestor", ascending=False)

    for _, row in df.iterrows():
        setor = str(row.get("setor", "SEM_SETOR"))

        if setores.get(setor, 0) >= MAX_EMPRESAS_POR_SETOR:
            continue

        carteira.append(row)
        setores[setor] = setores.get(setor, 0) + 1

        if len(carteira) >= MAX_EMPRESAS_CARTEIRA:
            break

    return pd.DataFrame(carteira)


def calcular_pesos(carteira):
    carteira = carteira.copy()

    soma = carteira["score_gestor"].sum()

    if soma <= 0 or len(carteira) == 0:
        carteira["peso_sugerido"] = 0
    else:
        carteira["peso_sugerido"] = carteira["score_gestor"] / soma

    carteira["peso_sugerido_pct"] = carteira["peso_sugerido"] * 100

    return carteira


def definir_decisao(row):
    score = row["score_gestor"]
    sinal = str(row.get("sinal_tecnico", "")).upper()

    if score >= 80 and "COMPRA" in sinal:
        return "COMPRAR AGORA"

    if score >= 70 and "FRACO" not in sinal and "EVITAR" not in sinal:
        return "COMPRAR PARCIAL"

    if score >= 60:
        return "AGUARDAR"

    return "NÃO PRIORIZAR"


def gerar_motivo(row):
    motivos = []

    if row["score_balanceado"] >= 75:
        motivos.append("fundamentos fortes")
    else:
        motivos.append("fundamentos moderados")

    if row["score_tecnico"] >= 75:
        motivos.append("técnico favorável")
    elif row["score_tecnico"] < 50:
        motivos.append("técnico fraco reduziu prioridade")

    if row["moat_score"] >= 75:
        motivos.append("moat relevante")

    if row["ajuste_tecnico"] < 0:
        motivos.append("penalização técnica aplicada")

    return "; ".join(motivos)


def montar_carteira():
    OUTPUT_DIR.mkdir(exist_ok=True)

    df = carregar_base()
    df = calcular_score_gestor(df)

    carteira = aplicar_diversificacao(df)

    if carteira.empty:
        raise ValueError("Carteira vazia após aplicação da diversificação.")

    carteira = calcular_pesos(carteira)

    carteira["decisao"] = carteira.apply(definir_decisao, axis=1)
    carteira["motivo_decisao"] = carteira.apply(gerar_motivo, axis=1)

    carteira = carteira.sort_values("score_gestor", ascending=False).reset_index(drop=True)
    carteira.insert(0, "ranking", carteira.index + 1)

    colunas = [
        "ranking",
        "ticker",
        "empresa",
        "setor",
        "rating",
        "moat_classificacao",
        "score_balanceado",
        "score_tecnico",
        "moat_score",
        "sinal_tecnico",
        "ajuste_tecnico",
        "score_gestor",
        "peso_sugerido_pct",
        "decisao",
        "motivo_decisao",
    ]

    colunas = [c for c in colunas if c in carteira.columns]

    carteira[colunas].to_csv(OUTPUT_FILE, index=False)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("B3 FUNDAMENTALISTA ENGINE — PORTFOLIO REPORT\n\n")
        f.write(f"Empresas analisadas: {len(df)}\n")
        f.write(f"Empresas selecionadas: {len(carteira)}\n")
        f.write(f"Limite por setor: {MAX_EMPRESAS_POR_SETOR}\n\n")
        f.write("Fórmula do Score Gestor:\n")
        f.write("50% Fundamentalista + 35% Técnico + 15% Moat + Ajuste Técnico\n\n")
        f.write(carteira[colunas].to_string(index=False))

    print("PORTFOLIO ENGINE FINALIZADO")
    print(f"Arquivo salvo: {OUTPUT_FILE}")
    print(f"Relatório salvo: {REPORT_FILE}")


if __name__ == "__main__":
    montar_carteira()
