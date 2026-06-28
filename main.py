# ============================================================
# B3 FUNDAMENTALISTA ENGINE
# MAIN.PY — DEBUG
# ============================================================

print("DEBUG 0 — main.py iniciado", flush=True)

print("DEBUG 1 — importando cvm_data", flush=True)
from engine.cvm_data import carregar_dados_cvm
print("DEBUG 2 — cvm_data importado", flush=True)

print("DEBUG 3 — importando b3_data", flush=True)
from engine.b3_data import carregar_empresas_b3
print("DEBUG 4 — b3_data importado", flush=True)

print("DEBUG 5 — importando indicators", flush=True)
from engine.indicators import construir_base_fundamentalista
print("DEBUG 6 — indicators importado", flush=True)

print("DEBUG 7 — importando scoring", flush=True)
from engine.scoring import gerar_rankings
print("DEBUG 8 — scoring importado", flush=True)

print("DEBUG 9 — importando report", flush=True)
from engine.report import gerar_relatorio
print("DEBUG 10 — report importado", flush=True)


def main():
    print("=" * 80, flush=True)
    print("B3 FUNDAMENTALISTA ENGINE", flush=True)
    print("=" * 80, flush=True)

    print("\n[1/5] Carregando empresas da B3...", flush=True)
    df_b3 = carregar_empresas_b3()
    print(f"Empresas B3 carregadas: {len(df_b3)}", flush=True)

    print("\n[2/5] Carregando dados da CVM...", flush=True)
    dados_cvm = carregar_dados_cvm()
    print("Dados CVM carregados.", flush=True)

    print("\n[3/5] Calculando fundamentos...", flush=True)
    base = construir_base_fundamentalista(df_b3=df_b3, dados_cvm=dados_cvm)
    print(f"Empresas analisadas: {len(base)}", flush=True)

    print("\n[4/5] Gerando rankings...", flush=True)
    rankings = gerar_rankings(base)
    print("Rankings gerados.", flush=True)

    print("\n[5/5] Gerando relatório...", flush=True)
    gerar_relatorio(rankings)
    print("Relatório gerado.", flush=True)

    print("=" * 80, flush=True)
    print("EXECUÇÃO FINALIZADA", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
