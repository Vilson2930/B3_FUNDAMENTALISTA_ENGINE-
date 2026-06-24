# ============================================================
# B3 FUNDAMENTALISTA ENGINE
# MAIN.PY
# ============================================================

from engine.cvm_data import (
    carregar_dados_cvm
)

from engine.b3_data import (
    carregar_empresas_b3
)

from engine.indicators import (
    construir_base_fundamentalista
)

from engine.scoring import (
    gerar_rankings
)

from engine.report import (
    gerar_relatorio
)

# ============================================================
# EXECUÇÃO
# ============================================================

def main():

    print("=" * 80)
    print("B3 FUNDAMENTALISTA ENGINE")
    print("=" * 80)

    # --------------------------------------------------------
    # B3
    # --------------------------------------------------------

    print("\n[1/5] Carregando empresas da B3...")

    df_b3 = carregar_empresas_b3()

    print(
        f"Empresas B3 carregadas: {len(df_b3)}"
    )

    # --------------------------------------------------------
    # CVM
    # --------------------------------------------------------

    print("\n[2/5] Carregando dados da CVM...")

    dados_cvm = carregar_dados_cvm()

    print("Dados CVM carregados.")

    # --------------------------------------------------------
    # FUNDAMENTOS
    # --------------------------------------------------------

    print("\n[3/5] Calculando fundamentos...")

    base_fundamentalista = (
        construir_base_fundamentalista(
            df_b3=df_b3,
            dados_cvm=dados_cvm
        )
    )

    print(
        f"Empresas analisadas: "
        f"{len(base_fundamentalista)}"
    )

    # --------------------------------------------------------
    # RANKINGS
    # --------------------------------------------------------

    print("\n[4/5] Gerando rankings...")

    rankings = gerar_rankings(
        base_fundamentalista
    )

    print("Rankings gerados.")

    # --------------------------------------------------------
    # RELATÓRIO
    # --------------------------------------------------------

    print("\n[5/5] Gerando relatório...")

    gerar_relatorio(rankings)

    print("\n")
    print("=" * 80)
    print("EXECUÇÃO FINALIZADA")
    print("=" * 80)

# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
